# src/controllers/home_assistant_controller.py
from typing import Dict, Any, Optional, List
import traceback
import json
import uuid
from src.tools.whatsapp import WhatsAppService
from src.core.memory import RedisManager
from src.core.database import Database
from src.tools.home_assistant import HomeAssistantTools
from src.config import settings
import time


class HomeAssistantController:
    def __init__(self):
        """
        Inicializa el controlador para procesamiento de respuestas de Home Assistant.
        """
        self.whatsapp_service = WhatsAppService()
        self.redis_manager = RedisManager()
        self.database = Database()

    async def initialize(self):
        """
        Inicializa las conexiones necesarias.
        """
        await self.database.connect()

    async def get_home_assistant_config(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene la configuración de Home Assistant para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Configuración de Home Assistant o diccionario vacío si no existe
        """
        # Buscar primero en caché
        ha_config = await self.redis_manager.get_value(f"ha_config:{user_id}")

        if not ha_config:
            # Si no está en caché, buscar en BD
            ha_config = await self.database.get_home_assistant_config(user_id)

            if ha_config:
                # Guardar en caché para futuras consultas
                await self.redis_manager.set_value(f"ha_config:{user_id}", ha_config, 3600)

        print(
            f"🔍 Configuración de Home Assistant para el usuario {user_id}: {ha_config}")
        return ha_config or {}

    async def trigger_home_assistant(self, user_id: int, phone: str, method: str, params=None) -> Dict[str, Any]:
        """
        Dispara una acción en Home Assistant.

        Args:
            user_id: ID del usuario
            phone: Número de teléfono del usuario
            method: Método a ejecutar
            params: Parámetros adicionales (opcional)

        Returns:
            Resultado de la operación
        """
        if params is None:
            params = {}

        # Obtener configuración de Home Assistant
        ha_config = await self.get_home_assistant_config(user_id)
        if not ha_config or not ha_config.get("webhook_url"):
            return {"success": False, "message": "No se ha configurado Home Assistant para tu cuenta. Por Favor, contactate con nuestro equipo de soporte tecnico para mas información"}

        # Verificar si el método está disponible
        # ha_config.get("available_methods", [])
        available_methods = list(ha_config['available_methods'].keys())
        if not available_methods:
            return {"success": False, "message": "No hay métodos disponibles en tu configuración de Home Assistant. Por Favor, contactate con nuestro equipo de soporte tecnico para mas información"}

        if method not in available_methods:
            return {"success": False, "message": f"El método '{method}' no esta disponible en la configuración de Home Assistant. Por Favor, contactate con nuestro equipo de soporte tecnico para mas información"}

        # Obtener chat_id y conversation_id existente para este usuario
        chat_id = await self.redis_manager.get_or_create_chat_id(phone)
        conversation_id = await self.database.find_active_conversation(user_id, chat_id)

        # Si no hay conversación activa, crear una
        if not conversation_id:
            conversation_id = await self.database.create_conversation(user_id, chat_id)
            if not conversation_id:
                return {"success": False, "message": "No se pudo crear una conversación para el usuario."}

        callback_token = await self.database.create_temp_ha_token(conversation_id)
        if not callback_token:
            return {"success": False, "message": "No se pudo generar un token temporal."}

        # Crear instancia de herramienta de Home Assistant
        url = f"{ha_config["webhook_url"]}/api/webhook/activar_{method}"
        ha_tools = HomeAssistantTools(
            webhook_url=url,
            token=ha_config["token"]
        )

        # Añadir el token temporal y URL de callback a los parámetros
        url = f"{settings.URL_SERVIDOR}/webhook/home_assistant_response"
        callback_params = {
            "callback_token": callback_token,
            "conversation_id": conversation_id,
            "callback_url": f"{settings.URL_SERVIDOR}/webhook/home_assistant_response",
            "phone": phone
        }
        # Combinar con los parámetros existentes
        if params:
            callback_params.update(params)

        # Llamar al webhook
        result = await ha_tools.call_webhook(
            method=method,
            params=callback_params
        )

        return result

    async def process_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa las respuestas recibidas desde Home Assistant y envía
        los resultados a través de WhatsApp.

        Args:
            data: Datos recibidos desde Home Assistant

        Returns:
            Estado del procesamiento
        """
        try:

            phone = data.get("phone")

            # Procesar el mensaje según su tipo
            if "text_message" in data:
                # Mensaje de texto simple
                await self.whatsapp_service.send_message(phone, data["text_message"])

                # Actualizar historial
                await self._update_conversation_history(phone, data["text_message"])

            if "images_url" in data:
                for image_url in data["images_url"]:
                    # Enviar imágenes
                    await self.whatsapp_service.send_image(phone, f"{image_url}?t={int(time.time())}")
                    # Actualizar historial
                    await self._update_conversation_history(phone, f"{image_url}?t={int(time.time())}")

            if "video_url" in data:
                # Enviar video, falta implementar
                await self.whatsapp_service.send_message(phone, data["video_url"])
                # Actualizar historial
                await self._update_conversation_history(phone, data["video_url"])

        except Exception as e:
            print(f"❌ Error al procesar respuesta de Home Assistant: {e}")
            return {"success": False, "message": f"Error al procesar respuesta: {str(e)}"}

    async def _update_conversation_history(self, phone: str, message: str):
        """
        Actualiza el historial de conversación en Redis y Base de Datos.

        Args:
            phone: Número de teléfono
            message: Mensaje a guardar
        """
        # Guardar en Redis
        await self.redis_manager.add_message_to_history(
            f"chat:{phone}",
            "assistant",
            message
        )

        try:
            # Obtener datos del usuario
            user_data = await self.database.get_user_by_phone(phone)

            if user_data and "id" in user_data:
                # Obtener chat_id
                chat_id = await self.redis_manager.get_or_create_chat_id(phone)

                # Buscar conversación activa
                conversation_id = await self.database.find_active_conversation(user_data["id"], chat_id)

                if conversation_id:
                    # Guardar mensaje en la BD
                    await self.database.save_conversation_message(
                        conversation_id,
                        "assistant",
                        message
                    )
        except Exception as e:
            print(f"❌ Error al actualizar historial en BD: {e}")

    def _format_results(self, results: Any, method: str) -> str:
        """
        Formatea los resultados según el método.

        Args:
            results: Resultados a formatear
            method: Método que generó los resultados

        Returns:
            Mensaje formateado
        """
        try:
            if isinstance(results, str):
                return results

            if isinstance(results, dict):
                if method == "get_alarm_status" and "partitions" in results:
                    # Formatear estado de alarma
                    partitions = results["partitions"]
                    message = "📊 *Estado actual de la alarma:*\n\n"

                    for name, status in partitions.items():
                        message += f"• {name}: {status.upper()}\n"

                    return message

                elif method == "scan_cameras" and "cameras" in results:
                    # Formatear lista de cámaras
                    cameras = results["cameras"]
                    message = "📷 *Estado de las cámaras:*\n\n"

                    for camera in cameras:
                        message += f"• {camera.get('name')}: {camera.get('state', 'Desconocido')}\n"

                    return message

            # Si no hay formato específico, convertir a JSON y devolver
            return f"Resultados de '{method}':\n\n{json.dumps(results, indent=2, ensure_ascii=False)}"
        except Exception as e:
            return f"Resultados recibidos para '{method}' (formato no reconocido): {str(e)}"

    async def determine_method(self, user_id: int, intents: List[str], last_message: str) -> Optional[str]:
        """
        Determina qué método de Home Assistant invocar basado en las intenciones
        y el último mensaje del usuario.

        Args:
            user_id: ID del usuario
            intents: Intenciones detectadas
            last_message: Último mensaje del usuario

        Returns:
            Nombre del método a invocar o None si no se puede determinar
        """
        # Obtener configuración de Home Assistant para este usuario
        ha_config = await self.get_home_assistant_config(user_id)

        if not ha_config or not ha_config.get("available_methods"):
            return None

        available_methods = ha_config.get("available_methods", [])

        if not available_methods:
            return None

        # Mapeo básico de intenciones comunes a métodos
        intent_to_method = {
            "estado_alarma": "get_alarm_status",
            "como_esta_alarma": "get_alarm_status",
            "revisar_alarma": "get_alarm_status",
            "escaneo_camaras": "scan_cameras",
            "ver_camaras": "scan_cameras",
            "camaras": "scan_cameras",
            "imagen_camara": "get_camera_image",
            "foto_camara": "get_camera_image",
            "captura_camara": "get_camera_image",
            "verificar_sensores": "check_sensors",
            "sensores": "check_sensors",
            "detectores": "check_sensors"
        }

        # Buscar un método basado en intenciones
        for intent in intents:
            if intent in intent_to_method:
                method = intent_to_method[intent]
                if method in available_methods:
                    return method

        # Si no se encontró por intenciones, buscar por palabras clave en el mensaje
        last_message = last_message.lower()

        keywords = {
            "get_alarm_status": ["alarma", "estado", "armada", "activada"],
            "scan_cameras": ["camaras", "cámaras", "video", "escanear"],
            "get_camera_image": ["foto", "imagen", "captura"],
            "check_sensors": ["sensor", "detector", "movimiento", "temperatura"]
        }

        for method, words in keywords.items():
            if method in available_methods and any(word in last_message for word in words):
                return method

        # Si no encontramos nada específico, devolver el primer método disponible
        return available_methods[0] if available_methods else None

    async def close(self):
        """
        Cierra las conexiones utilizadas.
        """
        await self.database.close()
