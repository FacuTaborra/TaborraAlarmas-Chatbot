"""
Handlers para cada nodo del grafo de conversación principal.
"""
import traceback
import uuid
from typing import Dict, Any

from langchain_core.messages import AIMessage, HumanMessage

from src.graphs.troubleshooting import (
    confirmation_step,
    keyboard_selection,
    process_keyboard_selection,
    process_problem_selection,
    process_rating,
    exit_flow
)

from src.tools.home_assistant import HomeAssistantTools
from src.core.database import Database
from src.core.memory import RedisManager

# Inicializar servicios
db = Database()
redis = RedisManager()


def detect_intents(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo para verificar las intenciones detectadas

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado actualizado
    """
    print(f"🧠 Intenciones detectadas: {state['intents']}")
    return state


def handle_general_inquiry(state: Dict[str, Any]) -> Dict[str, Any]:
    messages = state["messages"]
    intents = state["intents"]
    business_info = state["business_info"]

    # Mapeo de intenciones a respuestas predefinidas
    intent_responses = {
        "direccion": f"🏢 Nuestra dirección es: {business_info.get('direccion', 'No disponible')}",
        "horario": f"🕒 Nuestro horario de atención es: {business_info.get('horario', 'No disponible')}",
        "email": f"📧 Puedes contactarnos por email a: {business_info.get('email', 'No disponible')}",
        "telefono1": f"📞 Nuestro teléfono principal es: {business_info.get('telefono_1', 'No disponible')}",
        "telefono2": f"📞 Teléfono alternativo: {business_info.get('telefono_2', 'No disponible')}",
        "telefono3": f"📞 Otro teléfono: {business_info.get('telefono_3', 'No disponible')}",
        "whatsapp_servicio_tecnico": f"🔧 WhatsApp del servicio técnico: {business_info.get('whatsapp_servicio_tecnico', 'No disponible')}",
        "whatsapp_ventas": f"📞 WhatsApp de ventas: {business_info.get('whatsapp_ventas', 'No disponible')}",
        "whatsapp_administracion": f"📞 WhatsApp de administración: {business_info.get('whatsapp_administracion', 'No disponible')}",
        "whatsapp_cobranza": f"📞 WhatsApp de cobranza: {business_info.get('whatsapp_cobranza', 'No disponible')}",
        "security": f"🚨 Teléfono de Security 24: {business_info.get('security', 'No disponible')}",
        "saludo": "👋 ¡Hola! Soy el asistente virtual de Taborra Alarmas SRL. ¿En qué puedo ayudarte hoy?",
        "despedida": "👋 ¡Gracias por contactar a Taborra Alarmas SRL! Estamos para ayudarte cuando lo necesites.",
        "agradecimiento": "🙏 De nada! Aqui estoy para lo que necesites de nuestros servicios! No dudes en preguntar si necesitas otra cosa."
    }

    # Si hay una intención específica detectada, usar respuesta predefinida
    detected_intents = [i for i in intents if i in intent_responses]

    if detected_intents:
        # Si hay múltiples intenciones, combinar las respuestas
        if len(detected_intents) > 1:
            response = "\n\n".join([intent_responses[intent]
                                   for intent in detected_intents])
        else:
            response = intent_responses[detected_intents[0]]

        messages.append(AIMessage(content=response))
        return {**state, "messages": messages}


def start_troubleshooting(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo para iniciar el flujo de resolución de problemas

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado con el flujo de troubleshooting iniciado
    """
    # Preparar estado para el flujo de troubleshooting

    troubleshooting_state = {
        "messages": state["messages"],
        "current_step": 0,
        "keyboard_type": None,
        "problem_type": None,
        "solutions_shown": [],
        "rating": None,
        "business_info": state["business_info"],
        "user_data": state.get("user_data", None)
    }

    return {
        **state,
        "troubleshooting_active": True,
        "troubleshooting_state": troubleshooting_state
    }


def process_troubleshooting(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo para procesar el flujo de resolución de problemas
    """
    try:
        # Obtener estado actual
        troubleshooting_state = state["troubleshooting_state"]
        current_step = troubleshooting_state.get("current_step", 0)

        # IMPORTANTE: Actualizar los mensajes del troubleshooting_state con los mensajes actuales
        troubleshooting_state["messages"] = state["messages"]

        # Verificar primero si el usuario quiere salir (antes de cualquier otro procesamiento)
        last_user_message = None
        for msg in reversed(troubleshooting_state["messages"]):
            if isinstance(msg, HumanMessage):
                last_user_message = msg.content.lower()
                break

        # Lista ampliada de frases para salir
        exit_phrases = [
            "salir", "cancelar", "terminar", "no quiero seguir", "quiero hablar de otra cosa",
            "volver", "atrás", "atras", "menu", "menú", "menu principal", "exit", "no", "chau",
            "ya no", "stop", "parar", "no me interesa", "otro tema", "no gracias", "salida"
        ]

        # Si el usuario quiere salir, hacerlo inmediatamente
        if last_user_message and any(phrase in last_user_message for phrase in exit_phrases):
            print(f"Usuario solicitó salir con: '{last_user_message}'")
            result = exit_flow(troubleshooting_state)
            return {
                **state,
                "messages": result["messages"],
                "troubleshooting_active": False,
                "troubleshooting_state": None
            }

        # Si no quiere salir, continuar con el flujo normal
        print(f"Paso actual: {current_step}")

        if current_step == 0:
            # Paso inicial de confirmación
            result = confirmation_step(troubleshooting_state)
            print("Confirmación mostrada, pasando a paso 1")
        elif current_step == 1:
            # Verificar si el usuario quiere continuar
            print("Procesando respuesta de confirmación")
            user_confirmed = False

            if last_user_message:
                confirmation_phrases = ["si", "sí", "yes",
                                        "quiero", "dale", "ok", "1", "aceptar"]
                user_confirmed = any(phrase == last_user_message or phrase in last_user_message.split(
                ) for phrase in confirmation_phrases)
                print(f"¿Usuario confirmó?: {user_confirmed}")

            if user_confirmed:
                print("Usuario confirmó, mostrando opciones de teclado")
                result = keyboard_selection(troubleshooting_state)
            else:
                print("Usuario no confirmó, saliendo del flujo")
                result = exit_flow(troubleshooting_state)
        elif current_step == 2:
            # Procesar selección de teclado
            print("Procesando selección de teclado")
            result = process_keyboard_selection(troubleshooting_state)
        elif current_step == 3:
            # Procesar selección de problema
            print("Procesando selección de problema")
            result = process_problem_selection(troubleshooting_state)
        elif current_step == 4:
            # Procesar calificación
            print("Procesando calificación")
            result = process_rating(troubleshooting_state)
        else:
            # Paso no reconocido, salir del flujo
            print(f"Paso no reconocido: {current_step}, saliendo")
            result = exit_flow(troubleshooting_state)

        # Verificar si hemos terminado
        if result.get("current_step", -1) == 0:
            print("Flujo de troubleshooting terminado")
            return {
                **state,
                "messages": result["messages"],
                "troubleshooting_active": False,
                "troubleshooting_state": None,
                "rating_info": {
                    "rating": result.get("rating"),
                    "keyboard_type": result.get("keyboard_type"),
                    "problem_type": result.get("problem_type")
                }
            }

        print(f"Continuando flujo, próximo paso: {result.get('current_step')}")
        # Continuar el flujo
        return {
            **state,
            "messages": result["messages"],
            "troubleshooting_state": result
        }
    except Exception as e:
        print(f"Error en process_troubleshooting: {e}")
        traceback.print_exc()
        # Para cualquier error, salir del flujo con mensaje de error
        messages = state["messages"]
        messages.append(AIMessage(
            content="Lo siento, hubo un problema con el asistente de resolución. Por favor, contacta directamente con nuestro servicio técnico."))
        return {
            **state,
            "messages": messages,
            "troubleshooting_active": False,
            "troubleshooting_state": None
        }


def handle_general_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo para responder cuando no se detectan intenciones

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado con la respuesta generica
    """
    messages = state["messages"]
    # Ejecutar la cadena
    response = "No he podido entender tu consulta. ¿Puedes especificar qué información necesitas sobre nuestros servicios?"

    # Añadir respuesta al historial
    messages.append(AIMessage(content=response))

    return {**state, "messages": messages}


def handle_access_denied(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo para manejar solicitudes de acceso denegado por nivel insuficiente

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado con mensaje de acceso denegado
    """
    messages = state["messages"]
    intents = state["intents"]
    business_info = state["business_info"]

    # Determinar qué tipo de acceso fue denegado
    denied_feature = ""
    print("Control de alarma no permitido")

    if "estado_alarma" in intents:
        denied_feature = "consultar el estado de tu alarma"
    elif "escaneo_camaras" in intents:
        denied_feature = "escanear las cámaras"
    elif "problema_alarma" in intents:
        denied_feature = "usar el asistente de resolución de problemas"
    elif "control_alarma" in intents:
        denied_feature = "controlar la alarma"

    # Crear mensaje personalizado
    response = f"⚠️ Lo siento, no tengo permitido {denied_feature}. Para mas información recomiendo que te contactes con nuestro equipo de ventas.\n\n"

    # Agregar información de contacto para upgrades
    if "whatsapp_ventas" in business_info:
        response += f"📞 Departamento de ventas: {business_info.get('whatsapp_ventas', 'No disponible')}"

    # Añadir respuesta al historial
    messages.append(AIMessage(content=response))

    return {**state, "messages": messages}


# En src/graphs/handlers.py

def handle_home_assistant_request(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo para marcar que se necesita una acción de Home Assistant.
    Este nodo no realiza operaciones asíncronas, solo prepara el estado.

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado actualizado con información para Home Assistant
    """
    messages = state["messages"]
    user_data = state.get("user_data", {})
    intents = state.get("intents", [])

    print(f"Intenciones para Home Assistant: {intents} usuario: {user_data}")

    # Verificar nivel de usuario
    if user_data.get("level", 1) < 3:
        response = "⚠️ Lo siento, esta función solo está disponible para usuarios de nivel VIP (Nivel 3)."
        messages.append(AIMessage(content=response))
        return {**state, "messages": messages}

    phone = user_data.get("phone")
    user_id = user_data.get("id")

    if not phone or not user_id:
        messages.append(
            AIMessage(content="⚠️ No se pudo identificar tu información de usuario."))
        return {**state, "messages": messages}

    # Agregar un mensaje genérico mientras procesamos
    messages.append(
        AIMessage(content="🔄 Procesando tu solicitud con Home Assistant, dame un momento..."))

    # Marcar en el estado que se necesita una acción de Home Assistant
    # Esto será procesado por el controlador después de que el grafo termine
    return {
        **state,
        "messages": messages,
        "requires_home_assistant": True,
        "ha_request": {
            "user_id": user_id,
            "phone": phone,
            "intents": intents,
            "last_message": state["messages"][-2].content if len(state["messages"]) >= 2 else ""
        }
    }


def finalize_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo final que marca el término del procesamiento

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado sin modificaciones
    """
    return state
