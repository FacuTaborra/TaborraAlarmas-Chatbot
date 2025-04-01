"""
Handlers para cada nodo del grafo de conversación principal.
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from src.graphs.troubleshooting import create_troubleshooting_graph
from src.config.settings import settings


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
    """
    Nodo para manejar consultas generales (nivel 1)

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado con la respuesta generada
    """
    messages = state["messages"]
    intents = state["intents"]
    business_info = state["business_info"]

    # Crear respuesta basada en intenciones detectadas
    response = ""

    # Procesar cada tipo de intención
    if "saludo" in intents:
        response += f"¡Hola! Soy el asistente virtual de Taborra Alarmas. ¿En qué puedo ayudarte hoy?\n\n"

    if "despedida" in intents:
        response += "¡Gracias por contactarnos! Que tengas un excelente día.\n\n"

    if "direccion" in intents:
        response += f"📍 Nuestra dirección es: {business_info.get('direccion', 'No disponible')}.\n\n"

    if "horario" in intents:
        response += f"🕒 Nuestro horario de atención es: {business_info.get('horario', 'No disponible')}.\n\n"

    if "email" in intents:
        response += f"📧 Nuestro email de contacto es: {business_info.get('email', 'No disponible')}.\n\n"

    if "telefono" in intents:
        response += f"📞 Nuestro teléfono de contacto es: {business_info.get('telefono', 'No disponible')}.\n\n"

    if "whatsapp" in intents:
        response += f"📱 Nuestro WhatsApp es: {business_info.get('whatsapp', 'No disponible')}.\n\n"

    if "whatsapp_servicio_tecnico" in intents:
        response += f"🔧 Nuestro WhatsApp para servicio técnico es: {business_info.get('whatsapp_servicio_tecnico', 'No disponible')}.\n\n"

    if "whatsapp_ventas" in intents:
        response += f"💼 Nuestro WhatsApp para ventas es: {business_info.get('whatsapp_ventas', 'No disponible')}.\n\n"

    if "whatsapp_administracion" in intents:
        response += f"📊 Nuestro WhatsApp para administración es: {business_info.get('whatsapp_administracion', 'No disponible')}.\n\n"

    if "whatsapp_cobranza" in intents:
        response += f"💰 Nuestro WhatsApp para cobranza es: {business_info.get('whatsapp_cobranza', 'No disponible')}.\n\n"

    if "security" in intents:
        response += f"🔐 Nuestro número de Security 24 es: {business_info.get('telefono_security', 'No disponible')}.\n\n"

    if "control_alarma" in intents:
        response += "⚠️ Lo siento, no puedo controlar la alarma por seguridad. Si necesitas ayuda con tu alarma, por favor contacta a nuestro servicio técnico.\n\n"

    # Si hay intención de estado_alarma o escaneo_camaras pero el usuario no tiene nivel 3, informar
    if ("estado_alarma" in intents or "escaneo_camaras" in intents) and state["user_level"] < 3:
        response += "⚠️ Para acceder a información sobre el estado de alarmas y cámaras, necesitas un nivel de acceso superior. Por favor, contacta a nuestro servicio técnico.\n\n"

    # Si no se detectó ninguna intención específica para información general
    if not any(i in intents for i in ["saludo", "despedida", "direccion", "horario", "email", "telefono",
                                      "whatsapp", "whatsapp_servicio_tecnico", "whatsapp_ventas",
                                      "whatsapp_administracion", "whatsapp_cobranza", "security", "control_alarma"]):
        response = "No he podido entender tu consulta. ¿Puedes especificar qué información necesitas sobre nuestros servicios?"

    # Añadir respuesta al historial
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
    """
    Nodo para manejar escaneo de cámaras (nivel 3)

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado con la respuesta generada
    """
    messages = state["messages"]

    # Simulación:
    camera_data = [
        {"id": "camera.entrada_principal",
            "name": "Entrada Principal", "state": "Grabando"},
        {"id": "camera.patio_trasero", "name": "Patio Trasero", "state": "Grabando"},
        {"id": "camera.cocina", "name": "Cocina", "state": "Inactiva"}
    ]

    # Formatear respuesta
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


def handle_llm_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo para generar respuestas usando LLM para casos no cubiertos por otros nodos

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado con la respuesta generada por el modelo
    """
    messages = state["messages"]
    user_level = state["user_level"]
    intents = state["intents"]

    # Crear un template para el prompt
    prompt_template = """
    Eres el asistente virtual de Taborra Alarmas, una empresa de seguridad y alarmas.
    
    Nivel de acceso del usuario: {user_level} (1=general, 2=técnico, 3=avanzado)
    
    Intenciones detectadas: {intents}
    
    Responde de manera amigable y profesional. Usa emojis ocasionalmente.
    
    Mensaje del usuario: {user_message}
    
    Tu respuesta:
    """

    # Crear el prompt
    prompt = ChatPromptTemplate.from_template(prompt_template)

    # Crear LLM
    llm = ChatOpenAI(
        model=settings.MODEL_NAME,
        temperature=0.7,
        openai_api_key=settings.OPENAI_API_KEY
    )

    # Crear la cadena
    chain = prompt | llm

    # Obtener último mensaje del usuario
    user_message = messages[-1].content if messages and hasattr(
        messages[-1], "content") else ""

    # Ejecutar la cadena
    response = chain.invoke({
        "user_level": user_level,
        "intents": ", ".join(intents),
        "user_message": user_message
    })

    # Añadir respuesta al historial
    messages.append(AIMessage(content=response.content))

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
