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
    """
    Nodo para manejar consultas generales (nivel 1)
    Args:
        state: Estado actual de la conversación
    Returns:
        Estado con la respuesta generada
    """
    messages = state["messages"]
    user_level = state["user_level"]
    intents = state["intents"]
    business_info = state["business_info"]

    # Intenciones específicas para información de negocio
    specific_intents = [
        "saludo", "despedida", "direccion", "horario", "email", "telefono",
        "whatsapp", "whatsapp_servicio_tecnico", "whatsapp_ventas",
        "whatsapp_administracion", "whatsapp_cobranza", "security", "control_alarma"
    ]

    # Verificar si hay intenciones específicas
    if any(i in intents for i in specific_intents) or not intents:
        # Crear un template para el prompt
        prompt_template = prompts.GENERAL_RESPONSE_TEMPLATE

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
            "intents": ", ".join(intents) if intents else "Ninguna",
            "user_message": user_message,
            "context": "Consulta sin intención específica",
            "direccion": business_info.get("direccion", "No disponible"),
            "horario": business_info.get("horario", "No disponible"),
            "email": business_info.get("email", "No disponible"),
            "telefono1": business_info.get("telefono1", "No disponible"),
            "telefono2": business_info.get("telefono2", "No disponible"),
            "telefono3": business_info.get("telefono3", "No disponible"),
            "whatsapp": business_info.get("whatsapp", "No disponible"),
            "whatsapp_servicio_tecnico": business_info.get("whatsapp_servicio_tecnico", "No disponible"),
            "whatsapp_ventas": business_info.get("whatsapp_ventas", "No disponible"),
            "whatsapp_administracion": business_info.get("whatsapp_administracion", "No disponible"),
            "whatsapp_cobranza": business_info.get("whatsapp_cobranza", "No disponible"),
            "telefono_security": business_info.get("telefono_security", "No disponible")
        }).content
        print(response)
    else:
        # Si no hay intenciones específicas, mantener lógica anterior
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


def handle_llm_response(state: Dict[str, Any]) -> Dict[str, Any]:
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


def finalize_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo final que marca el término del procesamiento

    Args:
        state: Estado actual de la conversación

    Returns:
        Estado sin modificaciones
    """
    return state
