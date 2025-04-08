# src/tools/home_assistant.py
from typing import Dict, Any, Optional
import aiohttp
import json
import uuid
from src.config.settings import settings


class HomeAssistantTools:
    def __init__(self, webhook_url: Optional[str] = None, token: Optional[str] = None):
        """
        Inicializa la herramienta para comunicarse con Home Assistant vía webhook.

        Args:
            webhook_url: URL del webhook configurado en Home Assistant del cliente
            token: Token de autenticación para el webhook
        """
        self.webhook_url = webhook_url
        self.token = token

        if not self.webhook_url:
            print("⚠️ No se ha configurado un webhook para Home Assistant")
            self.enabled = False
        else:
            self.enabled = True

    async def call_webhook(self, method: str, phone: str, conversation_id: str = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Llama al webhook de Home Assistant y procesa la respuesta.

        Args:
            method: Método o acción a ejecutar en Home Assistant
            phone: Número de teléfono del usuario para respuesta
            conversation_id: ID de la conversación para seguimiento
            params: Parámetros adicionales para el método

        Returns:
            Resultado de la llamada al webhook
        """
        if not self.enabled:
            return {"error": "No se ha configurado un webhook para Home Assistant"}

        # Generar ID de conversación si no se proporcionó
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # Preparar el payload para el webhook
        payload = {
            "method": method,
            "auth_token": self.token,
            "phone": phone,
            "conversation_id": conversation_id,
            "callback_url": f"{settings.URL_SERVIDOR}/webhook/home_assistant_response"
        }

        # Añadir parámetros adicionales si existen
        if params:
            payload["params"] = params

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                ) as response:
                    print(
                        f"🔄 Llamando al webhook de Home Assistant: {self.webhook_url}, response: {response}")
                    if response.status == 200:
                        # Intentar obtener respuesta inmediata
                        try:
                            response_data = await response.json()

                            # Verificar si hay resultados inmediatos
                            if "results" in response_data or "text_message" in response_data or "image_url" in response_data:
                                return {
                                    "success": True,
                                    "immediate_response": True,
                                    "data": response_data
                                }
                            else:
                                # No hay resultados inmediatos, esperar respuesta asíncrona
                                return {
                                    "success": True,
                                    "immediate_response": False,
                                    "message": "Solicitud enviada a Home Assistant, esperando respuesta asíncrona"
                                }
                        except Exception:
                            # No se pudo parsear como JSON, asumimos que es sólo confirmación
                            return {
                                "success": True,
                                "immediate_response": False,
                                "message": "Solicitud enviada a Home Assistant"
                            }
                    else:
                        error_text = await response.text()
                        return {"error": f"Error en la llamada al webhook (código {response.status}): {error_text}"}
        except Exception as e:
            return {"error": f"Error de conexión con Home Assistant: {str(e)}"}
