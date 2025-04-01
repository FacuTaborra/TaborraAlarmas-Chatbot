from fastapi import APIRouter, Request
from src.chains.intent_classifier import IntentClassifier
from src.graphs.main_graph import create_conversation_graph
from src.tools.whatsapp import WhatsAppService
from src.core.memory import RedisManager
from src.core.database import Database
from src.config.settings import settings
from langchain_core.messages import HumanMessage, AIMessage
import json

router = APIRouter()

# Inicializar servicios
intent_classifier = IntentClassifier(api_key=settings.OPENAI_API_KEY)
whatsapp_service = WhatsAppService(
    phone_id=settings.WHATSAPP_PHONE_ID,
    access_token=settings.WHATSAPP_ACCESS_TOKEN
)
redis_manager = RedisManager()
database = Database()
conversation_graph = create_conversation_graph()


@router.get("/whatsapp")
async def validate_webhook(request: Request):
    """Endpoint para validar webhook de WhatsApp"""
    print("🔐 Verificación de WhatsApp")
    params = request.query_params
    mode = params.get("hub.mode")
    challenge = params.get("hub.challenge")
    token = params.get("hub.verify_token")

    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        return int(challenge)  # Meta espera recibir este número
    return {"error": "Verificación fallida"}


@router.post("/whatsapp")
async def process_whatsapp_message(request: Request):
    """Endpoint para procesar mensajes de WhatsApp"""
    try:
        data = await request.json()
        print(f"📥 Nuevo mensaje recibido: {data}")

        # 1. Validar y extraer información del payload
        entry = data.get("entry", [])
        if not entry:
            return {"status": "No hay entry en el payload"}

        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "No hay changes en el payload"}

        value = changes[0].get("value", {})
        if "statuses" in value:
            return {"status": "Evento de estado ignorado"}

        messages = value.get("messages", [])
        if not messages:
            return {"status": "No hay mensajes"}

        # Extraer información del mensaje
        message_data = messages[0]
        message_id = message_data.get("id", "")

        # Verificar duplicados
        if await redis_manager.exists(f"message:{message_id}"):
            return {"status": "Mensaje duplicado ignorado"}
        await redis_manager.set_value(f"message:{message_id}", "1", 86400)

        # Obtener texto del mensaje
        text_body = ""
        if message_data.get("type") == "text":
            text_body = message_data.get("text", {}).get("body", "")
        elif message_data.get("type") == "interactive":
            # Manejar respuestas de botones interactivos
            interactive = message_data.get("interactive", {})
            if interactive.get("type") == "button_reply":
                text_body = interactive.get(
                    "button_reply", {}).get("title", "")

        if not text_body:
            return {"status": "Mensaje sin texto ignorado"}

        # Obtener teléfono del remitente
        phone_user = message_data["from"]
        # Asegurar formato correcto (quitar "549" si existe)
        if phone_user.startswith("549"):
            phone_user = "54" + phone_user[3:]

        # 2. Obtener datos del usuario
        user_data = await redis_manager.get_value(phone_user)
        context = ""

        if not user_data:
            # Usuario no existe en Redis, buscar en BD
            user_data = await database.get_user_by_phone(phone_user)

            if not user_data:
                # Usuario nuevo, registrar
                try:
                    full_name = value.get("contacts", [{}])[
                        0]["profile"]["name"]
                    names = full_name.split(" ", 1)
                    first_name = names[0]
                    last_name = names[1] if len(names) > 1 else ""
                except (IndexError, KeyError):
                    first_name = "Usuario"
                    last_name = ""

                await database.register_user(first_name, last_name, phone_user)
                user_data = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": phone_user,
                    "level": 1,
                }
                context = f"'NUEVO', nombre: {first_name}"
            else:
                # Usuario existente pero no en Redis
                context = f"'INACTIVO', nombre: {user_data['first_name']}"

            # Guardar en Redis
            await redis_manager.set_value(phone_user, user_data)
        else:
            # Usuario existente y en Redis
            await redis_manager.update_expiry(phone_user, 3600)
            if isinstance(user_data, str):
                user_data = json.loads(user_data)
            context = f"'SEGUIMIENTO', nombre: {user_data['first_name']}"

        # 3. Clasificar intenciones
        intents = await intent_classifier.predict(text_body)
        print(f"🧠 Intenciones detectadas: {intents}")

        # 4. Obtener historial de mensajes
        chat_id = await redis_manager.get_or_create_chat_id(phone_user)
        history = await redis_manager.get_message_history(f"chat:{phone_user}")

        # Crear lista de mensajes para LangChain
        messages_history = []
        for msg in history:
            if msg.get("role") == "user":
                messages_history.append(HumanMessage(
                    content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                messages_history.append(
                    AIMessage(content=msg.get("content", "")))

        # 5. Obtener estado de la conversación (para troubleshooting)
        conversation_state = await redis_manager.get_value(f"taborra:chat:{phone_user}:{chat_id}:state")
        troubleshooting_active = False
        troubleshooting_state = None

        if conversation_state:
            troubleshooting_active = True
            troubleshooting_state = conversation_state

        # 6. Obtener información del negocio
        business_info = await database.load_business_info()

        # 7. Preparar estado para el grafo
        # Añadir el mensaje actual al historial
        messages_history.append(HumanMessage(content=text_body))

        state = {
            "messages": messages_history,
            "user_data": user_data,
            "user_level": user_data.get("level", 1),
            "intents": intents,
            "context": context,
            "business_info": business_info,
            "troubleshooting_active": troubleshooting_active,
            "troubleshooting_state": troubleshooting_state
        }

        # 8. Procesar con el grafo
        result = conversation_graph.invoke(state)

        # 9. Extraer respuesta
        final_messages = result["messages"]
        if final_messages and isinstance(final_messages[-1], AIMessage):
            response_message = final_messages[-1]

            # 10. Guardar en el historial
            await redis_manager.add_message_to_history(
                f"chat:{phone_user}",
                "user",
                text_body
            )
            await redis_manager.add_message_to_history(
                f"chat:{phone_user}",
                "assistant",
                response_message.content
            )

            # 11. Actualizar estado de la conversación si hay troubleshooting
            if result.get("troubleshooting_active", False) and result.get("troubleshooting_state"):
                await redis_manager.set_value(
                    f"taborra:chat:{phone_user}:{chat_id}:state",
                    result["troubleshooting_state"],
                    1800  # 30 minutos
                )
            elif troubleshooting_active and not result.get("troubleshooting_active", False):
                # Si estaba activo pero ya no, eliminarlo
                await redis_manager.delete_key(f"taborra:chat:{phone_user}:{chat_id}:state")

            # 12. Enviar respuesta con WhatsApp
            await whatsapp_service.split_and_send_message(phone_user, response_message.content)

            return {"status": "Mensaje procesado y respuesta enviada"}
        else:
            return {"status": "No se generó respuesta"}

    except Exception as e:
        import traceback
        print(f"❌ Error al procesar mensaje: {str(e)}")
        traceback.print_exc()
        return {"status": "Error procesando mensaje", "error": str(e)}
