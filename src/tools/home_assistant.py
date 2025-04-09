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

    async def call_webhook(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
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

        # Preparar el payload para el webhook
        payload = {
            "method": method,
            "phone": params.get("phone"),
            "conversation_id": params.get("conversation_id"),
            "callback_token": params.get("callback_token"),
            "callback_url": params.get("callback_url"),
        }

        # Añadir parámetros adicionales si existen
        if params:
            payload["params"] = params

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                ) as response:
                    text = await response.text()
                    print(f"Respuesta del webhook HA: {text}")
                    if response.status == 200:
                        try:
                            # Siempre intentar obtener el JSON
                            response_data = await response.json()
                            print(f"Respuesta del webhook HA: {response_data}")
                            return {
                                "success": True,
                                "data": response_data
                            }
                        except Exception:
                            # Si no hay JSON, devolver éxito sin datos
                            return {
                                "success": True,
                                "message": "Solicitud enviada exitosamente"
                            }
                    else:
                        error_text = await response.text()
                        return {
                            "error": f"Error en la llamada al webhook (código {response.status}): {error_text}"
                        }
        except Exception as e:
            return {"error": f"Error de conexión con Home Assistant: {str(e)}"}
