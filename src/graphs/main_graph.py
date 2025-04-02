"""
Grafo principal para el sistema de conversación del chatbot.
"""
from typing import Dict, Any, List, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph
from src.graphs.handlers import (
    detect_intents,
    handle_general_inquiry,
    handle_alarm_status,
    handle_camera_scan,
    start_troubleshooting,
    process_troubleshooting,
    handle_general_response,
    finalize_response
)
from src.graphs.routers import route_main_conversation

# Definir el tipo del estado


class ConversationState(TypedDict):
    messages: List[BaseMessage]
    user_data: Dict[str, Any]
    user_level: int
    intents: List[str]
    context: str
    business_info: Dict[str, Any]
    troubleshooting_active: bool
    troubleshooting_state: Optional[Dict[str, Any]]


def create_conversation_graph():
    """
    Crea y retorna el grafo principal de conversación.

    Returns:
        Grafo compilado listo para ser invocado
    """
    # Construir el grafo
    conversation_graph = StateGraph(ConversationState)

    # Añadir nodos
    conversation_graph.add_node("DETECT_INTENTS", detect_intents)
    conversation_graph.add_node("GENERAL_INQUIRY", handle_general_inquiry)
    conversation_graph.add_node("ALARM_STATUS", handle_alarm_status)
    conversation_graph.add_node("CAMERA_SCAN", handle_camera_scan)
    conversation_graph.add_node("START_TROUBLESHOOTING", start_troubleshooting)
    conversation_graph.add_node("TROUBLESHOOTING", process_troubleshooting)
    conversation_graph.add_node("GENERAL_RESPONSE", handle_general_response)
    conversation_graph.add_node("FINAL", finalize_response)

    # Añadir enrutamiento condicional desde DETECT_INTENTS
    conversation_graph.add_conditional_edges(
        "DETECT_INTENTS",
        route_main_conversation,
        {
            "GENERAL_INQUIRY": "GENERAL_INQUIRY",
            "ALARM_STATUS": "ALARM_STATUS",
            "CAMERA_SCAN": "CAMERA_SCAN",
            "START_TROUBLESHOOTING": "START_TROUBLESHOOTING",
            "TROUBLESHOOTING": "TROUBLESHOOTING",
            "GENERAL_RESPONSE": "GENERAL_RESPONSE"
        }
    )

    # Añadir bordes directos
    conversation_graph.add_edge("START_TROUBLESHOOTING", "TROUBLESHOOTING")

    # Todos los nodos finalizan en el nodo FINAL
    conversation_graph.add_edge("GENERAL_INQUIRY", "FINAL")
    conversation_graph.add_edge("ALARM_STATUS", "FINAL")
    conversation_graph.add_edge("CAMERA_SCAN", "FINAL")
    conversation_graph.add_edge("TROUBLESHOOTING", "FINAL")
    conversation_graph.add_edge("GENERAL_RESPONSE", "FINAL")

    # Definir punto de entrada y salida
    conversation_graph.set_entry_point("DETECT_INTENTS")
    conversation_graph.set_finish_point("FINAL")

    # Compilar el grafo
    return conversation_graph.compile()
