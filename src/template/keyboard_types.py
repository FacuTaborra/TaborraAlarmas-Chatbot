# Definición de tipos de teclados y sus problemas comunes
from typing import Dict

KEYBOARD_TYPES = {
    "touch": {
        "name": "Teclado Touch",
        "image_url": "/imagenes/touch_keyboard.jpg",
        "problems": {
            "beep_continuo": {
                "title": "Pitido continuo o beep",
                "solution": "1. Asegúrate de que todas las puertas y ventanas estén cerradas.\n2. Verifica el panel para ver si hay alguna zona abierta.\n3. Intenta reiniciar el sistema desconectando la alimentación por 30 segundos.",
                "video_url": None
            },
            "no_enciende": {
                "title": "No enciende el teclado",
                "solution": "1. Verifica que el sistema tenga energía.\n2. Revisa los cables de conexión entre el teclado y el panel.\n3. Intenta reiniciar el sistema.",
                "video_url": None
            }
        }
    },
    "lcd": {
        "name": "Teclado LCD",
        "image_url": "/imagenes/lcd_keyboard.jpg",
        "problems": {
            "error_comunicacion": {
                "title": "Error de comunicación",
                "solution": "1. Verifica la conexión a internet.\n2. Reinicia el router.\n3. Reinicia el panel de alarma desconectando la alimentación por 30 segundos.",
                "video_url": None
            },
            "pantalla_blanco": {
                "title": "Pantalla en blanco",
                "solution": "1. Comprueba la alimentación del teclado.\n2. Revisa los cables de conexión.\n3. Verifica el brillo del LCD, tal vez esté al mínimo.",
                "video_url": None
            }
        }
    },
    "alax": {
        "name": "Teclado Alax",
        "image_url": "/imagenes/alax_keyboard.jpg",
        "direct_support": True,
        "support_message": "Los teclados Alax requieren soporte técnico especializado debido a su configuración avanzada."
    }
}


def get_keyboard_options_text() -> str:
    """
    Genera texto con opciones de teclados.

    Returns:
        Texto formateado con opciones
    """
    options_text = ""
    for i, (key, keyboard) in enumerate(KEYBOARD_TYPES.items(), 1):
        options_text += f"{i}. {keyboard['name']}\n"
    return options_text


def get_problems_options_text(keyboard_type: str) -> str:
    """
    Genera texto con opciones de problemas para un tipo de teclado.

    Args:
        keyboard_type: Tipo de teclado

    Returns:
        Texto formateado con opciones
    """
    keyboard = KEYBOARD_TYPES.get(keyboard_type)
    if not keyboard or not keyboard.get("problems"):
        return "No hay problemas definidos para este teclado."

    options_text = ""
    for i, (key, problem) in enumerate(keyboard["problems"].items(), 1):
        options_text += f"{i}. {problem['title']}\n"
    return options_text


def generate_solution_response(problem_data: Dict) -> str:
    """
    Genera una respuesta con la solución para un problema.

    Args:
        problem_data: Datos del problema

    Returns:
        Texto de respuesta formateado
    """
    solution = problem_data.get(
        "solution", "No hay solución disponible para este problema.")
    video_url = problem_data.get("video_url")

    response = f"*{problem_data['title']}*\n\n"
    response += f"{solution}\n\n"

    if video_url:
        response += f"📹 *Video tutorial*: {video_url}\n\n"

    response += "¿Fue útil esta solución? Califica del 1 al 5 (donde 5 es muy útil)."

    return response
