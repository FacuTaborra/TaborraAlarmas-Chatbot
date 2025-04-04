"""
Grafo de resolución de problemas para la alarma.
"""
from typing import Dict, Any, List, TypedDict, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph
from src.template.keyboard_types import KEYBOARD_TYPES, get_keyboard_options_text, get_problems_options_text, generate_solution_response
from src.graphs.routers import route_troubleshooting
from src.core.database import Database

# Definición del tipo de estado
db = Database()


class TroubleshootingState(TypedDict):
    messages: List[BaseMessage]
    current_step: int
    keyboard_type: Optional[str]
    problem_type: Optional[str]
    solutions_shown: List[str]
    rating: Optional[int]
    business_info: Dict[str, Any]

# Handlers para cada paso del flujo


def confirmation_step(state: TroubleshootingState) -> TroubleshootingState:
    """
    Nodo para solicitar confirmación al usuario

    Args:
        state: Estado del flujo de troubleshooting

    Returns:
        Estado actualizado con la pregunta de confirmación
    """
    messages = state["messages"]

    # Añadir respuesta del sistema
    response = "Veo que tienes un problema con tu alarma. ¿Quieres que te ayude a resolverlo?"
    messages.append(AIMessage(content=response))

    return {
        **state,
        "messages": messages,
        "current_step": 1
    }


def keyboard_selection(state: TroubleshootingState) -> TroubleshootingState:
    """
    Nodo para seleccionar el tipo de teclado

    Args:
        state: Estado del flujo de troubleshooting

    Returns:
        Estado actualizado con las opciones de teclado
    """
    messages = state["messages"]

    # Preparar respuesta con opciones de teclados
    response = "Para ayudarte mejor, necesito saber qué modelo de teclado de alarma tienes.\n\n"
    response += get_keyboard_options_text()
    response += "\n_Puedes escribir 'salir' o 'cancelar' en cualquier momento para salir del asistente._"
    messages.append(AIMessage(content=response))

    return {
        **state,
        "messages": messages,
        "current_step": 2
    }


def process_keyboard_selection(state: TroubleshootingState) -> TroubleshootingState:
    """
    Nodo para procesar la selección de teclado del usuario

    Args:
        state: Estado del flujo de troubleshooting

    Returns:
        Estado actualizado con el teclado seleccionado
    """
    messages = state["messages"]
    user_message = ""

    # Obtener el último mensaje del usuario
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break

    selected_keyboard = None

    # Verificar selección por número
    if user_message.isdigit():
        idx = int(user_message) - 1
        keys = list(KEYBOARD_TYPES.keys())
        if 0 <= idx < len(keys):
            selected_keyboard = keys[idx]
    else:
        # Determinar qué teclado seleccionó por nombre
        for key, keyboard in KEYBOARD_TYPES.items():
            if keyboard["name"].lower() in user_message.lower() or key.lower() in user_message.lower():
                selected_keyboard = key
                break

    if not selected_keyboard:
        # No pudimos identificar el teclado
        response = "No pude identificar el modelo de teclado que mencionas. Por favor, selecciona uno de estos modelos:\n\n"
        response += get_keyboard_options_text()
        messages.append(AIMessage(content=response))
        return {**state, "messages": messages}

    # Verificar si es Alax (derivación directa a soporte)
    if KEYBOARD_TYPES[selected_keyboard].get("direct_support", False):
        support_message = KEYBOARD_TYPES[selected_keyboard].get(
            "support_message", "")
        support_number = state["business_info"].get(
            "whatsapp_servicio_tecnico", "nuestro número de soporte")
        response = f"{support_message}\nPuedes comunicarte al {support_number}."
        messages.append(AIMessage(content=response))
        return {**state, "messages": messages, "current_step": 0, "keyboard_type": selected_keyboard}

    # Continuar con los problemas específicos del teclado
    response = f"Perfecto. Para el {KEYBOARD_TYPES[selected_keyboard]['name']}, estos son los problemas más comunes:\n\n"
    response += get_problems_options_text(selected_keyboard)
    messages.append(AIMessage(content=response))

    return {
        **state,
        "messages": messages,
        "current_step": 3,
        "keyboard_type": selected_keyboard
    }


def process_problem_selection(state: TroubleshootingState) -> TroubleshootingState:
    """
    Nodo para procesar la selección de problema del usuario

    Args:
        state: Estado del flujo de troubleshooting

    Returns:
        Estado actualizado con el problema seleccionado y su solución
    """
    messages = state["messages"]
    user_message = ""

    # Obtener el último mensaje del usuario
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break

    keyboard_type = state["keyboard_type"]

    if not keyboard_type:
        # Error: No hay tipo de teclado seleccionado
        messages.append(
            AIMessage(content="Lo siento, ocurrió un error. Vamos a comenzar de nuevo."))
        return {**state, "messages": messages, "current_step": 1}

    keyboard = KEYBOARD_TYPES.get(keyboard_type, {})
    problems = keyboard.get("problems", {})

    selected_problem = None
    # Verificar selección por número
    if user_message.isdigit():
        idx = int(user_message) - 1
        keys = list(problems.keys())
        if 0 <= idx < len(keys):
            selected_problem = keys[idx]
    else:
        # Determinar qué problema seleccionó por nombre
        for key, problem in problems.items():
            if problem["title"].lower() in user_message.lower() or key.lower() in user_message.lower():
                selected_problem = key
                break

    if not selected_problem:
        # No pudimos identificar el problema
        response = "No pude identificar el problema que mencionas. Por favor, selecciona uno de estos problemas comunes:\n\n"
        response += get_problems_options_text(keyboard_type)
        response += "\n_Puedes escribir 'salir' o 'cancelar' en cualquier momento para salir del asistente._"
        messages.append(AIMessage(content=response))
        return {**state, "messages": messages}

    problem_data = problems[selected_problem]

    # Generar respuesta con solución, video y calificación
    response = generate_solution_response(problem_data)
    messages.append(AIMessage(content=response))

    return {
        **state,
        "messages": messages,
        "current_step": 4,
        "problem_type": selected_problem,
        "solutions_shown": state.get("solutions_shown", []) + [selected_problem]
    }


def process_rating(state: TroubleshootingState) -> TroubleshootingState:
    """
    Nodo para procesar la calificación del usuario

    Args:
        state: Estado del flujo de troubleshooting

    Returns:
        Estado actualizado con la calificación o preparado para una nueva consulta
    """
    messages = state["messages"]
    user_message = ""

    # Obtener el último mensaje del usuario
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break

    # Comprobar si es una calificación
    if user_message.isdigit() and 1 <= int(user_message) <= 5:
        rating = int(user_message)
        print(
            f"💯 Rating recibido: {rating} para problema {state.get('problem_type')} en teclado {state.get('keyboard_type')}")
        response = f"¡Gracias por tu calificación de {rating}/5! ¿Hay algo más en lo que pueda ayudarte con tu alarma?\n\n_Puedes escribir 'salir' o 'cancelar' para terminar el asistente._"
        messages.append(AIMessage(content=response))

        return {
            **state,
            "messages": messages,
            "current_step": 0,  # Terminar el flujo
            "rating": rating
        }

    # El usuario probablemente está haciendo otra pregunta o necesita más ayuda
    response = "¿Quieres que te ayude con otro problema de tu alarma?\n\n_Puedes escribir 'salir' o 'cancelar' para terminar el asistente._"
    messages.append(AIMessage(content=response))

    return {
        **state,
        "messages": messages,
        "current_step": 1  # Volver al paso de confirmación
    }


def exit_flow(state: TroubleshootingState) -> TroubleshootingState:
    """
    Nodo para salir del flujo de resolución de problemas

    Args:
        state: Estado del flujo de troubleshooting

    Returns:
        Estado con mensaje de salida y paso reseteado
    """
    messages = state["messages"]
    messages.append(AIMessage(
        content="Has salido del asistente de resolución de problemas. ¿En qué más puedo ayudarte?"))
    return {**state, "messages": messages, "current_step": 0}


def create_troubleshooting_graph():
    """
    Crea y retorna el grafo de resolución de problemas

    Returns:
        Grafo compilado listo para ser invocado
    """
    # Construir el grafo
    troubleshooting_graph = StateGraph(TroubleshootingState)

    # Añadir nodos
    troubleshooting_graph.add_node("CONFIRMATION", confirmation_step)
    troubleshooting_graph.add_node("KEYBOARD_SELECTION", keyboard_selection)
    troubleshooting_graph.add_node(
        "PROCESS_KEYBOARD", process_keyboard_selection)
    troubleshooting_graph.add_node(
        "PROCESS_PROBLEM", process_problem_selection)
    troubleshooting_graph.add_node("PROCESS_RATING", process_rating)
    troubleshooting_graph.add_node("EXIT", exit_flow)

    # Añadir enrutador condicional
    troubleshooting_graph.add_conditional_edges(
        "CONFIRMATION",
        route_troubleshooting,
        {
            "KEYBOARD_SELECTION": "KEYBOARD_SELECTION",
            "EXIT": "EXIT",
        }
    )

    troubleshooting_graph.add_conditional_edges(
        "KEYBOARD_SELECTION",
        route_troubleshooting,
        {
            "PROCESS_KEYBOARD": "PROCESS_KEYBOARD",
            "EXIT": "EXIT"
        }
    )

    troubleshooting_graph.add_conditional_edges(
        "PROCESS_KEYBOARD",
        route_troubleshooting,
        {
            "PROCESS_PROBLEM": "PROCESS_PROBLEM",
            "EXIT": "EXIT"
        }
    )

    troubleshooting_graph.add_conditional_edges(
        "PROCESS_PROBLEM",
        route_troubleshooting,
        {
            "PROCESS_RATING": "PROCESS_RATING",
            "EXIT": "EXIT"
        }
    )

    troubleshooting_graph.add_conditional_edges(
        "PROCESS_RATING",
        route_troubleshooting,
        {
            "CONFIRMATION": "CONFIRMATION",
            "EXIT": "EXIT"
        }
    )

    # Define el punto de entrada
    troubleshooting_graph.set_entry_point("CONFIRMATION")

    # Define el punto de terminación
    troubleshooting_graph.set_finish_point("EXIT")

    # Compilar el grafo
    return troubleshooting_graph.compile()
