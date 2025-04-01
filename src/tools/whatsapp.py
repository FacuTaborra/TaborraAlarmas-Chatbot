from typing import Dict, Any, List, Optional
import aiohttp
from src.config.settings import settings


class WhatsAppService:
    def __init__(self, phone_id: Optional[str] = None, access_token: Optional[str] = None):
        """
        Inicializa el servicio de WhatsApp.

        Args:
            phone_id: ID del teléfono en WhatsApp Business API
            access_token: Token de acceso
        """
        self.phone_id = phone_id or settings.WHATSAPP_PHONE_ID
        self.access_token = access_token or settings.WHATSAPP_ACCESS_TOKEN

        if not self.phone_id or not self.access_token:
            print("⚠️ El servicio de WhatsApp está deshabilitado")
            self.enabled = False
        else:
            self.enabled = True
            self.api_url = f"https://graph.facebook.com/v22.0/{self.phone_id}/messages"
            self.headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

    async def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Envía un mensaje de texto.

        Args:
            to: Número de teléfono destino
            message: Texto del mensaje

        Returns:
            Respuesta de la API
        """
        if not self.enabled:
            return {"error": "El servicio de WhatsApp está deshabilitado"}

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }

        return await self._send_request(payload, f"mensaje a {to}")

    async def send_image(self, to: str, image_url: str, caption: str = "") -> Dict[str, Any]:
        """
        Envía una imagen.

        Args:
            to: Número de teléfono destino
            image_url: URL de la imagen
            caption: Pie de foto opcional

        Returns:
            Respuesta de la API
        """
        if not self.enabled:
            return {"error": "El servicio de WhatsApp está deshabilitado"}

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"link": image_url, "caption": caption}
        }

        return await self._send_request(payload, f"imagen a {to}")

    async def send_interactive_buttons(self, to: str, message: str, buttons: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Envía un mensaje con botones interactivos.

        Args:
            to: Número de teléfono destino
            message: Texto del mensaje
            buttons: Lista de botones (cada uno con id y title)

        Returns:
            Respuesta de la API
        """
        if not self.enabled:
            return {"error": "El servicio de WhatsApp está deshabilitado"}

        button_items = [
            {
                "type": "reply",
                "reply": {
                    "id": button["id"],
                    "title": button["title"]
                }
            } for button in buttons
        ]

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": message
                },
                "action": {
                    "buttons": button_items
                }
            }
        }

        return await self._send_request(payload, f"botones a {to}")

    async def _send_request(self, payload: Dict[str, Any], action_desc: str) -> Dict[str, Any]:
        """
        Envía una solicitud a la API de WhatsApp.

        Args:
            payload: Datos a enviar
            action_desc: Descripción para logs

        Returns:
            Respuesta de la API
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10
                ) as response:
                    response_data = await response.json()

                    if response.status == 200:
                        print(
                            f"✅ Éxito enviando {action_desc}: {response_data}")
                    else:
                        print(
                            f"⚠️ Error enviando {action_desc}: {response_data}")

                    return response_data
        except Exception as e:
            error_data = {"error": f"Error al enviar {action_desc}: {str(e)}"}
            print(f"❌ {error_data['error']}")
            return error_data

    async def split_and_send_message(self, to: str, message: str, max_length: int = 4000) -> List[Dict[str, Any]]:
        """
        Divide un mensaje largo y envía cada parte.

        Args:
            to: Número de teléfono destino
            message: Mensaje a enviar
            max_length: Longitud máxima de cada parte

        Returns:
            Lista de respuestas de la API
        """
        if len(message) <= max_length:
            return [await self.send_message(to, message)]

        parts = []
        current_pos = 0
        responses = []

        while current_pos < len(message):
            end_pos = min(current_pos + max_length, len(message))

            # Buscar un buen punto de corte
            if end_pos < len(message):
                paragraph_end = message.rfind("\n\n", current_pos, end_pos)
                if paragraph_end > current_pos + 100:
                    end_pos = paragraph_end + 2
                else:
                    sentence_end = message.rfind(". ", current_pos, end_pos)
                    if sentence_end > current_pos + 50:
                        end_pos = sentence_end + 2

            part = message[current_pos:end_pos]
            parts.append(part)
            current_pos = end_pos

        # Enviar cada parte
        for part in parts:
            response = await self.send_message(to, part)
            responses.append(response)

        return responses
