# Definición de tipos de teclados y sus problemas comunes
from typing import Dict


KEYBOARD_TYPES = {
    "modelo_1555": {
        "name": "Modelo 1555",
        "image_url": "teclado_1555.jpg",
        "problems": {
            "no_puede_activar": {
                "title": "No puedo activar el sistema",
                "solution": "Existen varias razones por las que el sistema no se activa.",
                "video_url": "https://www.youtube.com/embed/XXXX1",
                "steps": [
                    "Verifica que no haya zonas abiertas (puertas o ventanas)",
                    "Comprueba que el teclado no muestre fallas",
                    "Asegúrate de ingresar correctamente tu código de usuario"
                ]
            },
            "muestra_falla": {
                "title": "Me muestra una falla",
                "solution": "Las fallas pueden ser por distintos motivos y es importante identificarlas correctamente.",
                "video_url": "https://www.youtube.com/embed/XXXX2",
                "steps": [
                    "Identifica el número o código de falla en el teclado",
                    "Consulta el manual para identificar el tipo de falla",
                    "Verifica la alimentación y conexiones del sistema"
                ]
            },
            "emite_sonido": {
                "title": "Me emite un sonido el teclado",
                "solution": "Los sonidos del teclado indican diferentes estados o alertas del sistema.",
                "video_url": "https://www.youtube.com/embed/XXXX3",
                "steps": [
                    "Identifica el tipo de sonido (continuo, intermitente, corto)",
                    "Verifica si hay alguna zona abierta o en falla",
                    "Consulta el manual para el significado específico del sonido"
                ]
            },
            "anular_zona": {
                "title": "Necesito anular una zona",
                "solution": "Puedes anular temporalmente una zona para activar el sistema sin que ésta genere alarmas.",
                "video_url": "https://www.youtube.com/embed/XXXX4",
                "steps": [
                    "Ingresa tu código de usuario",
                    "Presiona la tecla de anulación (generalmente [*])",
                    "Ingresa el número de zona que deseas anular"
                ]
            },
            "modificar_codigo": {
                "title": "Agregar, modificar o anular un código",
                "solution": "Es posible administrar los códigos de usuario desde el teclado principal.",
                "video_url": "https://www.youtube.com/embed/XXXX5",
                "steps": [
                    "Ingresa el código maestro (generalmente es el usuario 1)",
                    "Sigue la secuencia para programación de códigos",
                    "Asigna o modifica el código del usuario deseado"
                ]
            },
            "ampliar_sistema": {
                "title": "Necesito ampliar mi sistema",
                "solution": "Los sistemas de alarma se pueden expandir con sensores y dispositivos adicionales.",
                "video_url": "https://www.youtube.com/embed/XXXX6",
                "steps": [
                    "Identifica qué tipo de ampliación necesitas",
                    "Verifica la compatibilidad con tu panel actual",
                    "Contacta a soporte técnico para una evaluación profesional"
                ]
            },
            "activar_perimetral": {
                "title": "Necesito saber cómo activar mi sistema en forma perimetral o en forma total",
                "solution": "Existen diferentes modos de activación según tus necesidades de protección.",
                "video_url": "https://www.youtube.com/embed/XXXX7",
                "steps": [
                    "Para activación total: Ingresa tu código de usuario",
                    "Para activación perimetral: Presiona la tecla correspondiente (generalmente [Stay]) y luego tu código",
                    "Espera el tiempo de salida antes de que el sistema se active completamente"
                ]
            },
            "probar_funcionamiento": {
                "title": "Probar funcionamiento del sistema",
                "solution": "Es recomendable hacer pruebas periódicas para asegurar el correcto funcionamiento.",
                "video_url": "https://www.youtube.com/embed/XXXX8",
                "steps": [
                    "Notifica a la central de monitoreo que realizarás una prueba",
                    "Activa el sistema y genera una alarma controlada",
                    "Verifica que la señal se haya transmitido correctamente"
                ]
            },
            "prueba_transmision": {
                "title": "Realizar una prueba de transmisión a la central de monitoreo",
                "solution": "Puedes verificar la comunicación con la central de monitoreo mediante una prueba de transmisión.",
                "video_url": "https://www.youtube.com/embed/XXXX9",
                "steps": [
                    "Ingresa el código maestro",
                    "Accede al menú de prueba de comunicación",
                    "Espera la confirmación de transmisión exitosa"
                ]
            },
            "otros_problemas": {
                "title": "Otros problemas",
                "solution": "Existen situaciones específicas que pueden requerir asistencia personalizada.",
                "video_url": "https://www.youtube.com/embed/XXXX10",
                "steps": [
                    "Documenta detalladamente el problema que estás experimentando",
                    "Verifica si el problema persiste después de reiniciar el sistema",
                    "Contacta a soporte técnico para una evaluación profesional"
                ]
            }
        }
    },
    "modelo_5500": {
        "name": "Modelo 5500",
        "image_url":  "teclado_5500.jpg",
        "problems": {
            "no_puede_activar": {
                "title": "No puedo activar el sistema",
                "solution": "Existen varias razones por las que el sistema no se activa.",
                "video_url": "https://www.youtube.com/embed/XXXX1",
                "steps": [
                    "Verifica que no haya zonas abiertas (puertas o ventanas)",
                    "Comprueba que el teclado no muestre fallas",
                    "Asegúrate de ingresar correctamente tu código de usuario"
                ]
            },
            "muestra_falla": {
                "title": "Me muestra una falla",
                "solution": "Las fallas pueden ser por distintos motivos y es importante identificarlas correctamente.",
                "video_url": "https://www.youtube.com/embed/XXXX2",
                "steps": [
                    "Identifica el número o código de falla en el teclado",
                    "Consulta el manual para identificar el tipo de falla",
                    "Verifica la alimentación y conexiones del sistema"
                ]
            },
            "emite_sonido": {
                "title": "Me emite un sonido el teclado",
                "solution": "Los sonidos del teclado indican diferentes estados o alertas del sistema.",
                "video_url": "https://www.youtube.com/embed/XXXX3",
                "steps": [
                    "Identifica el tipo de sonido (continuo, intermitente, corto)",
                    "Verifica si hay alguna zona abierta o en falla",
                    "Consulta el manual para el significado específico del sonido"
                ]
            },
            "anular_zona": {
                "title": "Necesito anular una zona",
                "solution": "Puedes anular temporalmente una zona para activar el sistema sin que ésta genere alarmas.",
                "video_url": "https://www.youtube.com/embed/XXXX4",
                "steps": [
                    "Ingresa tu código de usuario",
                    "Presiona la tecla de anulación (generalmente [*])",
                    "Ingresa el número de zona que deseas anular"
                ]
            },
            "modificar_codigo": {
                "title": "Agregar, modificar o anular un código",
                "solution": "Es posible administrar los códigos de usuario desde el teclado principal.",
                "video_url": "https://www.youtube.com/embed/XXXX5",
                "steps": [
                    "Ingresa el código maestro (generalmente es el usuario 1)",
                    "Sigue la secuencia para programación de códigos",
                    "Asigna o modifica el código del usuario deseado"
                ]
            },
            "ampliar_sistema": {
                "title": "Necesito ampliar mi sistema",
                "solution": "Los sistemas de alarma se pueden expandir con sensores y dispositivos adicionales.",
                "video_url": "https://www.youtube.com/embed/XXXX6",
                "steps": [
                    "Identifica qué tipo de ampliación necesitas",
                    "Verifica la compatibilidad con tu panel actual",
                    "Contacta a soporte técnico para una evaluación profesional"
                ]
            },
            "activar_perimetral": {
                "title": "Necesito saber cómo activar mi sistema en forma perimetral o en forma total",
                "solution": "Existen diferentes modos de activación según tus necesidades de protección.",
                "video_url": "https://www.youtube.com/embed/XXXX7",
                "steps": [
                    "Para activación total: Ingresa tu código de usuario",
                    "Para activación perimetral: Presiona la tecla correspondiente (generalmente [Stay]) y luego tu código",
                    "Espera el tiempo de salida antes de que el sistema se active completamente"
                ]
            },
            "probar_funcionamiento": {
                "title": "Probar funcionamiento del sistema",
                "solution": "Es recomendable hacer pruebas periódicas para asegurar el correcto funcionamiento.",
                "video_url": "https://www.youtube.com/embed/XXXX8",
                "steps": [
                    "Notifica a la central de monitoreo que realizarás una prueba",
                    "Activa el sistema y genera una alarma controlada",
                    "Verifica que la señal se haya transmitido correctamente"
                ]
            },
            "prueba_transmision": {
                "title": "Realizar una prueba de transmisión a la central de monitoreo",
                "solution": "Puedes verificar la comunicación con la central de monitoreo mediante una prueba de transmisión.",
                "video_url": "https://www.youtube.com/embed/XXXX9",
                "steps": [
                    "Ingresa el código maestro",
                    "Accede al menú de prueba de comunicación",
                    "Espera la confirmación de transmisión exitosa"
                ]
            },
            "otros_problemas": {
                "title": "Otros problemas",
                "solution": "Existen situaciones específicas que pueden requerir asistencia personalizada.",
                "video_url": "https://www.youtube.com/embed/XXXX10",
                "steps": [
                    "Documenta detalladamente el problema que estás experimentando",
                    "Verifica si el problema persiste después de reiniciar el sistema",
                    "Contacta a soporte técnico para una evaluación profesional"
                ]
            }
        }
    },
    "modelo_neo_lcd": {
        "name": "Modelo NEO LCD",
        "image_url":  "teclado_neo_lcd.jpg",
        "problems": {
            "no_puede_activar": {
                "title": "No puedo activar el sistema",
                "solution": "Existen varias razones por las que el sistema no se activa.",
                "video_url": "https://www.youtube.com/embed/XXXX1",
                "steps": [
                    "Verifica que no haya zonas abiertas (puertas o ventanas)",
                    "Comprueba que el teclado no muestre fallas",
                    "Asegúrate de ingresar correctamente tu código de usuario"
                ]
            },
            "muestra_falla": {
                "title": "Me muestra una falla",
                "solution": "Las fallas pueden ser por distintos motivos y es importante identificarlas correctamente.",
                "video_url": "https://www.youtube.com/embed/XXXX2",
                "steps": [
                    "Identifica el número o código de falla en el teclado",
                    "Consulta el manual para identificar el tipo de falla",
                    "Verifica la alimentación y conexiones del sistema"
                ]
            },
            "emite_sonido": {
                "title": "Me emite un sonido el teclado",
                "solution": "Los sonidos del teclado indican diferentes estados o alertas del sistema.",
                "video_url": "https://www.youtube.com/embed/XXXX3",
                "steps": [
                    "Identifica el tipo de sonido (continuo, intermitente, corto)",
                    "Verifica si hay alguna zona abierta o en falla",
                    "Consulta el manual para el significado específico del sonido"
                ]
            },
            "anular_zona": {
                "title": "Necesito anular una zona",
                "solution": "Puedes anular temporalmente una zona para activar el sistema sin que ésta genere alarmas.",
                "video_url": "https://www.youtube.com/embed/XXXX4",
                "steps": [
                    "Ingresa tu código de usuario",
                    "Presiona la tecla de anulación (generalmente [*])",
                    "Ingresa el número de zona que deseas anular"
                ]
            },
            "modificar_codigo": {
                "title": "Agregar, modificar o anular un código",
                "solution": "Es posible administrar los códigos de usuario desde el teclado principal.",
                "video_url": "https://www.youtube.com/embed/XXXX5",
                "steps": [
                    "Ingresa el código maestro (generalmente es el usuario 1)",
                    "Sigue la secuencia para programación de códigos",
                    "Asigna o modifica el código del usuario deseado"
                ]
            },
            "ampliar_sistema": {
                "title": "Necesito ampliar mi sistema",
                "solution": "Los sistemas de alarma se pueden expandir con sensores y dispositivos adicionales.",
                "video_url": "https://www.youtube.com/embed/XXXX6",
                "steps": [
                    "Identifica qué tipo de ampliación necesitas",
                    "Verifica la compatibilidad con tu panel actual",
                    "Contacta a soporte técnico para una evaluación profesional"
                ]
            },
            "activar_perimetral": {
                "title": "Necesito saber cómo activar mi sistema en forma perimetral o en forma total",
                "solution": "Existen diferentes modos de activación según tus necesidades de protección.",
                "video_url": "https://www.youtube.com/embed/XXXX7",
                "steps": [
                    "Para activación total: Ingresa tu código de usuario",
                    "Para activación perimetral: Presiona la tecla correspondiente (generalmente [Stay]) y luego tu código",
                    "Espera el tiempo de salida antes de que el sistema se active completamente"
                ]
            },
            "probar_funcionamiento": {
                "title": "Probar funcionamiento del sistema",
                "solution": "Es recomendable hacer pruebas periódicas para asegurar el correcto funcionamiento.",
                "video_url": "https://www.youtube.com/embed/XXXX8",
                "steps": [
                    "Notifica a la central de monitoreo que realizarás una prueba",
                    "Activa el sistema y genera una alarma controlada",
                    "Verifica que la señal se haya transmitido correctamente"
                ]
            },
            "prueba_transmision": {
                "title": "Realizar una prueba de transmisión a la central de monitoreo",
                "solution": "Puedes verificar la comunicación con la central de monitoreo mediante una prueba de transmisión.",
                "video_url": "https://www.youtube.com/embed/XXXX9",
                "steps": [
                    "Ingresa el código maestro",
                    "Accede al menú de prueba de comunicación",
                    "Espera la confirmación de transmisión exitosa"
                ]
            },
            "otros_problemas": {
                "title": "Otros problemas",
                "solution": "Existen situaciones específicas que pueden requerir asistencia personalizada.",
                "video_url": "https://www.youtube.com/embed/XXXX10",
                "steps": [
                    "Documenta detalladamente el problema que estás experimentando",
                    "Verifica si el problema persiste después de reiniciar el sistema",
                    "Contacta a soporte técnico para una evaluación profesional"
                ]
            }
        }
    },
    # The rest of the KEYBOARD_TYPES dictionary follows the same pattern for Modelo 5500 and NEO LCD models
    # I'll omit those for brevity, but they would be updated in the same manner with proper capitalization
    "alax": {
        "name": "Ajax",
        "image_url": "teclado_ajax.jpg",
        "direct_support": True,
        "support_message": "Para el modelo Alax, es necesario contactar directamente con soporte técnico debido a su configuración especial. ¿Deseas que te facilite el número de contacto?"
    }
}


def get_keyboard_image_url(keyboard_type, base_url):
    """Genera URL completa usando la base proporcionada"""
    keyboard = KEYBOARD_TYPES.get(keyboard_type)
    if keyboard and "image_url" in keyboard:
        return f"{base_url}/teclados/{keyboard['image_url']}"
    return None


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
