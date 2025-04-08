# src/config/test_ha_config.py
"""
Configuración de prueba para Home Assistant.
Este archivo contiene datos hardcodeados para simular la configuración
que vendría desde la base de datos configurada por el administrador.

En producción, esta configuración se cargaría desde la base de datos.
"""

# Ejemplo de configuración para un usuario nivel 3
TEST_USER_HA_CONFIG = {
    # Usuario con ID 1 (Facu Taborra en la BD)
    1: {
        "webhook_url": "http://192.168.1.123:8123/api/webhook/taborra_alarmas_webhook",
        "token": "token_secreto_123",
        "available_methods": {
            "get_alarm_status": {
                "display_name": "Consultando el estado de tu alarma",
                "intents": ["estado_alarma", "como_esta_alarma", "revisar_alarma"]
            },
            "scan_cameras": {
                "display_name": "Escaneando las cámaras disponibles",
                "intents": ["escaneo_camaras", "ver_camaras", "camaras"]
            },
            "get_camera_image": {
                "display_name": "Obteniendo imagen de la cámara",
                "intents": ["imagen_camara", "foto_camara", "captura_camara"],
                "requires_params": True,
                "param_pattern": "camara_{location}"
            },
            "check_sensors": {
                "display_name": "Verificando el estado de los sensores",
                "intents": ["verificar_sensores", "sensores", "detectores"]
            }
        }
    },
    # Usuario con ID 2
    2: {
        "webhook_url": "http://192.168.1.456:8123/api/webhook/otro_cliente_webhook",
        "token": "otro_token_secreto",
        "available_methods": {
            "get_alarm_status": {
                "display_name": "Consultando el estado de tu alarma",
                "intents": ["estado_alarma", "como_esta_alarma", "revisar_alarma"]
            },
            # Este usuario solo tiene configurado el método de estado de alarma
        }
    }
}

# Función para obtener la configuración de un usuario


def get_test_ha_config(user_id):
    """
    Obtiene la configuración de Home Assistant para un usuario de prueba.

    Args:
        user_id: ID del usuario

    Returns:
        Configuración de Home Assistant o None si no existe
    """
    return TEST_USER_HA_CONFIG.get(user_id)
