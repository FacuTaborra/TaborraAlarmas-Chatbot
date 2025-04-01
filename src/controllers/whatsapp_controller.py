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

        # Clasificar intenciones
        intents = await self.intent_classifier.predict(text_body)
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

        # Procesar con el grafo de conversación
        result = self.conversation_graph.invoke(state)

        # Extraer y enviar respuesta
        return await self._process_graph_result(result, phone_user, chat_id)

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

                await self.database.register_user(first_name, last_name, phone)
                user_data = {
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

    async def _process_graph_result(self, result: Dict[str, Any], phone: str, chat_id: str) -> Dict[str, Any]:
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

        if not final_messages or not isinstance(final_messages[-1], AIMessage):
            return {"status": "No se generó respuesta"}

        response_message = final_messages[-1]

        # Guardar en historial de mensajes
        await self.redis_manager.add_message_to_history(
            f"chat:{phone}",
            "user",
            final_messages[-2].content  # El último mensaje de usuario
        )
        await self.redis_manager.add_message_to_history(
            f"chat:{phone}",
            "assistant",
            response_message.content
        )

        # Manejar estado de troubleshooting
        if result.get("troubleshooting_active", False) and result.get("troubleshooting_state"):
            await self.redis_manager.set_value(
                f"taborra:chat:{phone}:{chat_id}:state",
                result["troubleshooting_state"],
                1800  # 30 minutos
            )
        else:
            # Si estaba activo pero ya no, eliminarlo
            await self.redis_manager.delete_key(f"taborra:chat:{phone}:{chat_id}:state")

        # Enviar respuesta por WhatsApp
        await self.whatsapp_service.split_and_send_message(
            phone,
            response_message.content
        )

        return {"status": "Mensaje procesado y respuesta enviada"}

    async def close(self):
        """
        Cierra los servicios utilizados.
        """
        await self.database.close()
