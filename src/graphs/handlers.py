"""
Handlers para cada nodo del grafo de conversación principal.
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from src.graphs.troubleshooting import create_troubleshooting_graph
from src.config.settings import settings
import src.template.prompts as prompts


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
        "despedida": "👋 ¡Gracias por contactar a Taborra Alarmas SRL! Estamos para ayudarte cuando lo necesites."
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


def handle_alarm_status(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo para manejar consultas de estado de alarma (nivel 3)

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado con la respuesta generada
    """
    messages = state["messages"]

    # Simulación:
    alarm_status = {
        "Partición 1": "activada",
        "Partición 2": "desactivada"
    }

    # Formatear respuesta
    response = "📊 *Estado actual de la alarma:*\n\n"
    for partition, status in alarm_status.items():
        response += f"• {partition}: {status.upper()}\n"

    # Añadir respuesta al historial
    messages.append(AIMessage(content=response))

    return {**state, "messages": messages}


def handle_camera_scan(state: Dict[str, Any]) -> Dict[str, Any]:
    messages = state["messages"]
    user_level = state.get("user_level", 1)
    business_info = state.get("business_info", {})

    # Verificar si el usuario tiene nivel suficiente
    if user_level < 3:
        response = "⚠️ Lo siento, el escaneo de cámaras solo está disponible para usuarios de nivel VIP (Nivel 3).\n\n"
        response += "Para obtener acceso a esta función, por favor contacta con nuestro servicio de ventas:\n"
        response += f"📞 WhatsApp Ventas: {business_info.get('whatsapp_ventas', 'No disponible')}"
    else:
        # Lógica para obtener datos de cámaras (por ejemplo, desde Home Assistant)
        camera_data = [
            {"id": "camera.entrada_principal",
                "name": "Entrada Principal", "state": "Grabando"},
            {"id": "camera.patio_trasero",
                "name": "Patio Trasero", "state": "Grabando"},
            {"id": "camera.cocina", "name": "Cocina", "state": "Inactiva"}
        ]

        response = "📷 *Estado de las cámaras:*\n\n"
        for camera in camera_data:
            response += f"• {camera['name']}: {camera['state']}\n"

        response += "\nEnviando imágenes de las cámaras activas..."

    # Añadir respuesta al historial
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
        "business_info": state["business_info"]
    }

    return {
        **state,
        "troubleshooting_active": True,
        "troubleshooting_state": troubleshooting_state
    }


def process_troubleshooting(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo para procesar el flujo de resolución de problemas

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado con resultados del proceso de troubleshooting
    """
    # Obtener grafo de troubleshooting
    troubleshooting_graph = create_troubleshooting_graph()

    # Procesar estado con el grafo
    result = troubleshooting_graph.invoke(state["troubleshooting_state"])

    # Verificar si hemos terminado
    if result["current_step"] == 0 and len(result["messages"]) > 1:
        return {
            **state,
            "messages": result["messages"],
            "troubleshooting_active": False,
            "troubleshooting_state": None
        }

    # Continuar el flujo
    return {
        **state,
        "messages": result["messages"],
        "troubleshooting_state": result
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


def finalize_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo final que marca el término del procesamiento

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado sin modificaciones
    """
    return state
