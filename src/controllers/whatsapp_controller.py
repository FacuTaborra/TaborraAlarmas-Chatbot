# src/controllers/whatsapp_controller.py
from typing import Dict, Any, Optional
from src.chains.intent_classifier import IntentClassifier
from src.graphs.main_graph import create_conversation_graph
from src.tools.whatsapp import WhatsAppService
from src.core.memory import RedisManager
from src.core.database import Database
from src.utils.helpers import parse_whatsapp_payload
from src.config.settings import settings
from langchain_core.messages import HumanMessage, AIMessage
from src.template.keyboard_types import KEYBOARD_TYPES, get_keyboard_image_url
# Importar controlador de Home Assistant
from src.controllers.home_assistant_controller import HomeAssistantController


class WhatsAppController:
    def __init__(
        self,
        intent_classifier: Optional[IntentClassifier] = None,
        whatsapp_service: Optional[WhatsAppService] = None,
        redis_manager: Optional[RedisManager] = None,
        database: Optional[Database] = None
    ):
        """
        Inicializa el controlador de WhatsApp con servicios inyectables.

        Args:
            intent_classifier: Clasificador de intenciones (opcional)
            whatsapp_service: Servicio de WhatsApp (opcional)
            redis_manager: Gestor de Redis (opcional)
            database: Servicio de base de datos (opcional)
        """
        self.intent_classifier = intent_classifier or IntentClassifier(
            api_key=settings.OPENAI_API_KEY
        )
        self.whatsapp_service = whatsapp_service or WhatsAppService()
        self.redis_manager = redis_manager or RedisManager()
        self.database = database or Database()

        # Crear grafo de conversación
        self.conversation_graph = create_conversation_graph()

    async def initialize(self):
        """
        Inicializa servicios necesarios.
        """
        await self.database.connect()

    async def validate_webhook(self, params: Dict[str, str]) -> bool:
        """
        Valida el webhook de WhatsApp.

        Args:
            params: Parámetros de la solicitud

        Returns:
            True si la validación es exitosa, False en caso contrario
        """
        mode = params.get("hub.mode")
        challenge = params.get("hub.challenge")
        token = params.get("hub.verify_token")

        return (
            mode == "subscribe" and
            token == settings.VERIFY_TOKEN and
            challenge is not None
        )

    async def process_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje de WhatsApp entrante.

        Args:
            payload: Datos del mensaje de WhatsApp

        Returns:
            Diccionario con el estado del procesamiento
        """
        # Parsear payload
        parsed_data = parse_whatsapp_payload(payload)

        if not parsed_data["success"]:
            return {"status": "Error al parsear payload"}

        # Extraer información
        message_id = parsed_data["message_id"]
        text_body = parsed_data["text"]
        phone_user = parsed_data["phone"]
        user_name = parsed_data["name"]

        # Verificar mensaje duplicado
        if await self.redis_manager.exists(f"message:{message_id}"):
            return {"status": "Mensaje duplicado ignorado"}
        await self.redis_manager.set_value(f"message:{message_id}", "1", 86400)

        # Obtener datos del usuario
        user_data = await self._get_or_create_user(phone_user, user_name)

        ha_methods = {}
        if user_data.get("level", 1) >= 3:
            try:
                # Obtener configuración de HA de la BD
                ha_methods = await self.database.get_home_assistant_methods(user_data["id"])
            except Exception as e:
                print(f"❌ Error al cargar métodos de Home Assistant: {e}")

        intent_classifier = IntentClassifier(
            api_key=settings.OPENAI_API_KEY,
            ha_methods=ha_methods
        )

        # Clasificar intenciones
        intents = await intent_classifier.predict(text_body)
        print(f"🧠 Intenciones detectadas: {intents}")

        # Obtener historial de mensajes
        chat_id = await self.redis_manager.get_or_create_chat_id(phone_user)
        history = await self.redis_manager.get_message_history(f"chat:{phone_user}")

        # Crear lista de mensajes para LangChain
        messages_history = self._convert_history_to_messages(history)
        messages_history.append(HumanMessage(content=text_body))

        # Obtener información del negocio
        business_info = await self.redis_manager.get_value("info_business")
        print(business_info)
        # Si no está en Redis, cargar de la base de datos y guardar en Redis
        if not business_info:
            business_info = await self.database.load_business_info()
            await self.redis_manager.set_value("info_business", business_info, 86400)

        # Preparar estado para el grafo
        state = {
            "messages": messages_history,
            "user_data": user_data,
            "user_level": user_data.get("level", 1),
            "intents": intents,
            "context": f"Chat con {user_data.get('first_name', 'Usuario')}",
            "business_info": business_info,
            "troubleshooting_active": False,
            "troubleshooting_state": None
        }

        # Verifica si hay un estado de troubleshooting activo
        troubleshooting_state = await self.redis_manager.get_value(f"taborra:chat:{phone_user}:{chat_id}:state")
        if troubleshooting_state:
            # Recuperar el estado y convertir los mensajes
            troubleshooting_state = self._recover_state_from_storage(
                troubleshooting_state)
            state["troubleshooting_active"] = True
            state["troubleshooting_state"] = troubleshooting_state

        # Procesar con el grafo de conversación
        result = self.conversation_graph.invoke(state)
        # Extraer y enviar respuesta
        return await self._process_graph_result(result, user_data, chat_id)

    async def _get_or_create_user(self, phone: str, name: str) -> Dict[str, Any]:
        """
        Obtiene o crea un usuario.

        Args:
            phone: Número de teléfono
            name: Nombre del usuario

        Returns:
            Datos del usuario
        """
        # Intentar obtener de Redis
        user_data = await self.redis_manager.get_value(phone)

        if not user_data:
            # Buscar en base de datos
            user_data = await self.database.get_user_by_phone(phone)

            if not user_data:
             # Crear nuevo usuario
                names = name.split(" ", 1)
                first_name = names[0]
                last_name = names[1] if len(names) > 1 else ""

                user_id = await self.database.register_user(first_name, last_name, phone)
                user_data = {
                    "id": user_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": phone,
                    "level": 1,
                }

            # Guardar en Redis
            await self.redis_manager.set_value(phone, user_data)

        return user_data

    def _convert_history_to_messages(self, history: list) -> list:
        """
        Convierte el historial de mensajes al formato de LangChain.

        Args:
            history: Historial de mensajes de Redis

        Returns:
            Lista de mensajes de LangChain
        """
        messages_history = []
        for msg in history:
            if msg.get("role") == "user":
                messages_history.append(HumanMessage(
                    content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                messages_history.append(
                    AIMessage(content=msg.get("content", "")))
        return messages_history

    def _convert_stored_state_to_messages(self, state):
        """Convierte mensajes almacenados de vuelta a objetos Message"""
        if "messages" in state:
            messages = []
            for msg in state["messages"]:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(
                        content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg.get("content", "")))
            state["messages"] = messages
        return state

    async def _process_graph_result(self, result: Dict[str, Any], user_data: Dict[str, Any], chat_id: str) -> Dict[str, Any]:
        """
        Procesa el resultado del grafo de conversación.

        Args:
            result: Resultado del grafo
            phone: Número de teléfono del usuario
            chat_id: ID del chat

        Returns:
            Diccionario con estado del procesamiento
        """
        final_messages = result.get("messages", [])
        rating_info = result.get("rating_info", None)

        # Verificar si es necesario procesar una solicitud de Home Assistant
        requires_ha = result.get("requires_home_assistant", False)
        ha_request = result.get("ha_request", {})

        if not final_messages or not isinstance(final_messages[-1], AIMessage):
            return {"status": "No se generó respuesta"}

        response_message = final_messages[-1]

        # Obtener usuario_id
        user_id = user_data.get("id")

        if user_id:
            # Buscar conversación activa o crear una nueva
            conversation_id = await self.database.find_active_conversation(user_id, chat_id)

            if not conversation_id:
                conversation_id = await self.database.create_conversation(user_id, chat_id)

            if conversation_id:
                # Si hay mensajes nuevos, guardarlos en la base de datos
                if len(final_messages) >= 2:
                    # Guardar el último mensaje del usuario
                    await self.database.save_conversation_message(
                        conversation_id,
                        "user",
                        # El último mensaje de usuario
                        final_messages[-2].content
                    )

                    # Guardar la respuesta del asistente
                    await self.database.save_conversation_message(
                        conversation_id,
                        "assistant",
                        response_message.content
                    )

        # Guardar en historial de mensajes (Redis - temporal)
        await self.redis_manager.add_message_to_history(
            f"chat:{user_data.get('phone')}",
            "user",
            final_messages[-2].content if len(final_messages) >= 2 else ""
        )
        await self.redis_manager.add_message_to_history(
            f"chat:{user_data.get('phone')}",
            "assistant",
            response_message.content
        )

        # Detectar si estamos en el paso de selección de teclado
        is_keyboard_selection = False
        if result.get("troubleshooting_active") and result.get("troubleshooting_state"):
            ts_state = result["troubleshooting_state"]
            if ts_state.get("current_step") == 2:  # Paso de selección de teclado
                is_keyboard_selection = True

        # Si es selección de teclado, enviar imágenes
        if is_keyboard_selection:
            # Primero enviar el mensaje con las opciones
            await self.whatsapp_service.send_message(user_data.get("phone"), response_message.content)

            # Luego enviar cada imagen de teclado
            # Luego enviar cada imagen de teclado
            for i, (key, keyboard) in enumerate(KEYBOARD_TYPES.items(), 1):
                caption = f"Digite el número {i} para seleccionar el teclado {keyboard['name']}"
                # Obtener URL actual
                current_url = settings.URL_SERVIDOR
                image_url = get_keyboard_image_url(key, current_url)
                print(f"🔗 URL de la imagen del teclado: {image_url}")
                await self.whatsapp_service.send_image(user_data.get("phone"), image_url, caption)
        else:
            # Envío normal de texto
            await self.whatsapp_service.split_and_send_message(user_data.get("phone"), response_message.content)

        # Si se requiere Home Assistant, llamar al webhook
        if requires_ha and ha_request:
            try:
                # Inicializar controlador
                ha_controller = HomeAssistantController()
                await ha_controller.initialize()

                # Procesar solicitud
                user_id = ha_request.get("user_id")
                phone = ha_request.get("phone")
                intents = ha_request.get("intents", [])

                # Ver si las intenciones que tiene estan en la lista de Home Assistant

                for intent in intents:
                    # Enviar mensaje a Home Assistant
                    response = await ha_controller.trigger_home_assistant(user_id, phone, intent)

                    if response.get("success"):
                        success_msg = f"✅ Método {intent} ejecutado correctamente en Home Assistant."
                        print(success_msg)
                        return {"status": success_msg}
                    elif not response.get("success"):
                        error_msg = f"⚠️ No tienes implementado el metodo {intent} en Home Assistant. Por Favor, comunicate con nuestro servicio técnico si quieres mas infomación."
                        print(f"❌ Error: {response.get('message')}")
                        await self.whatsapp_service.send_message(phone, response.get('message'))

            except Exception as e:
                print(f"❌ Error al procesar solicitud de Home Assistant: {e}")
                error_msg = "⚠️ Ocurrió un error al procesar tu solicitud a Home Assistant. Por favor, intenta más tarde."
                raise ValueError(error_msg)

        # Verificar si hay una calificación para guardar
        if rating_info and rating_info.get("rating") is not None:
            rating = rating_info.get("rating")
            keyboard_type = rating_info.get("keyboard_type", "desconocido")
            problem_type = rating_info.get("problem_type", "desconocido")

            if user_data and "id" in user_data:
                user_id = user_data.get('id')

                # Guardar en base de datos
                try:
                    await self.database.save_rating(
                        user_id=user_id,
                        rating=rating,
                        keyboard_type=keyboard_type,
                        problem_type=problem_type
                    )
                    print(
                        f"✅ Calificación {rating} guardada para usuario {user_id}, problema {problem_type}, teclado {keyboard_type}")
                except Exception as e:
                    print(f"❌ Error al guardar calificación: {e}")
            else:
                print(
                    f"⚠️ No se pudo encontrar el ID del usuario para el teléfono {user_data.get("phone")}")

        # Al guardar el estado de troubleshooting, convertirlo a formato serializable
        if result.get("troubleshooting_active", False) and result.get("troubleshooting_state"):
            # Convertir los mensajes a formato serializable
            serializable_state = self._prepare_state_for_storage(
                result["troubleshooting_state"])
            await self.redis_manager.set_value(
                f"taborra:chat:{user_data.get("phone")}:{chat_id}:state",
                serializable_state,
                1800  # 30 minutos
            )
        else:
            # Si estaba activo pero ya no, eliminarlo
            await self.redis_manager.delete_key(f"taborra:chat:{user_data.get("phone")}:{chat_id}:state")

        return {"status": "Mensaje procesado y respuesta enviada"}

    def _prepare_state_for_storage(self, state):
        """Prepara el estado para almacenamiento en Redis convirtiendo objetos no serializables"""
        serializable_state = {}

        for key, value in state.items():
            if key == "messages":
                # Convertir mensajes a formato serializable
                serializable_state[key] = []
                for msg in value:
                    if isinstance(msg, HumanMessage):
                        serializable_state[key].append({
                            "role": "user",
                            "content": msg.content
                        })
                    elif isinstance(msg, AIMessage):
                        serializable_state[key].append({
                            "role": "assistant",
                            "content": msg.content
                        })
            else:
                # Copiar otros valores como están
                serializable_state[key] = value

        return serializable_state

    def _recover_state_from_storage(self, state):
        """Recupera el estado de almacenamiento convirtiendo a objetos LangChain"""
        if "messages" in state and isinstance(state["messages"], list):
            state["messages"] = self._convert_history_to_messages(
                state["messages"])
        return state

    async def close(self):
        """
        Cierra los servicios utilizados.
        """
        await self.database.close()
