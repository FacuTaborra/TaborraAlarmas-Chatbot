"""
Funciones de enrutamiento para los grafos de conversación.
"""
from typing import Dict, Any
from langchain_core.messages import HumanMessage


def route_main_conversation(state: Dict[str, Any]) -> str:
    """
    Enrutador principal del grafo de conversación.
    Determina qué nodo debe procesar el mensaje basado en intenciones y nivel de usuario.

    Args:
        state: Estado actual de la conversación

    Returns:
        Nombre del nodo al que dirigir el flujo
    """
    intents = state["intents"]
    user_level = state["user_level"]

    # Si hay un estado de troubleshooting activo, continuar con él
    if state.get("troubleshooting_active", False):
        return "TROUBLESHOOTING"

    # Intención de problema de alarma para nivel 2+
    if "problema_alarma" in intents and user_level >= 2:
        return "START_TROUBLESHOOTING"
    elif "problema_alarma" in intents:
        # Si no tiene nivel 2+, podría redirigir a una respuesta general
        return "ACCESS_DENIED"

    # Estado de alarma para nivel 3
    if "estado_alarma" in intents and user_level >= 3:
        return "ALARM_STATUS"
    elif "estado_alarma" in intents:
        # Si no tiene nivel 3, podría redirigir a una respuesta general
        return "ACCESS_DENIED"

    # Escaneo de cámaras para nivel 3
    if "escaneo_camaras" in intents and user_level >= 3:
        return "CAMERA_SCAN"
    elif "escaneo_camaras" in intents:
        # Si no tiene nivel 3, podría redirigir a una respuesta general
        return "ACCESS_DENIED"

    # Control de alarma, no permitido para ningun nivel
    if "control_alarma" in intents:
        return "ACCESS_DENIED"

    # Intenciones generales de información para cualquier nivel
    general_intents = ["direccion", "horario", "email", "telefono1", "telefono2", "telefono3", "whatsapp",
                       "whatsapp_servicio_tecnico", "whatsapp_ventas",
                       "whatsapp_administracion", "whatsapp_cobranza",
                       "security", "saludo", "despedida", "control_alarma"]

    if any(intent in intents for intent in general_intents):
        return "GENERAL_INQUIRY"

    # Default: manejo cuando no se detecta intencion
    return "GENERAL_RESPONSE"


def route_troubleshooting(state: Dict[str, Any]) -> str:
    """
    Enrutador para el grafo de troubleshooting.
    Determina el siguiente paso en el flujo de resolución de problemas.

    Args:
        state: Estado actual del proceso de troubleshooting

    Returns:
        Nombre del siguiente nodo en el flujo
    """
    current_step = state["current_step"]

    # Verificar si el usuario quiere salir
    if len(state["messages"]) > 0 and isinstance(state["messages"][-1], HumanMessage):
        last_msg = state["messages"][-1].content.lower()
        exit_phrases = ["salir", "cancelar", "terminar", "no quiero seguir", "quiero hablar de otra cosa",
                        "volver", "atrás", "atras", "menu", "menú", "menu principal"]
        if any(phrase in last_msg for phrase in exit_phrases):
            return "EXIT"

    # Enrutar basado en el paso actual
    if current_step == 0:
        return "CONFIRMATION"
    elif current_step == 1:
        if len(state["messages"]) > 0 and isinstance(state["messages"][-1], HumanMessage):
            last_msg = state["messages"][-1].content.lower()
            confirmation_phrases = ["si", "sí", "yes", "Si", "SI", "SÍ", "quiero", "quiero seguir",
                                    "quiero continuar", "quiero seguir con esto", "quiero continuar con esto",
                                    "quiero", "dale", "ok", "1", "aceptar"]
            if any(phrase == last_msg or phrase in last_msg.split() for phrase in confirmation_phrases):
                return "KEYBOARD_SELECTION"
            else:
                return "EXIT"
        return "CONFIRMATION"
    elif current_step == 2:
        return "PROCESS_KEYBOARD"
    elif current_step == 3:
        return "PROCESS_PROBLEM"
    elif current_step == 4:
        return "PROCESS_RATING"

    return "EXIT"
