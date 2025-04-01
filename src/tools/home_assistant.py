from typing import Dict, Any, Optional
import aiohttp
import json
from src.config.settings import settings


class HomeAssistantTools:
    def __init__(self, url: Optional[str] = None, token: Optional[str] = None):
        """
        Inicializa las herramientas para Home Assistant.

        Args:
            url: URL base de Home Assistant
            token: Token de acceso
        """
        self.url = url or settings.HOME_ASSISTANT_URL
        self.token = token or settings.HOME_ASSISTANT_TOKEN

        if not self.url or not self.token:
            print("⚠️ La integración con Home Assistant está deshabilitada")
            self.enabled = False
        else:
            self.enabled = True
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

    async def get_alarm_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de todas las particiones de alarma.

        Returns:
            Diccionario con el estado de cada partición o error
        """
        if not self.enabled:
            return {"error": "La integración con Home Assistant está deshabilitada"}

        template_url = f"{self.url}/api/template"
        payload = {
            "template": """
            {% set entidades = states.binary_sensor | selectattr('entity_id', 'search', 'alarma_dsc_neo_casa_estado_armado_particion_') | list %}
            {
              {% for entidad in entidades %}
                "{{ entidad.entity_id }}": "{{ entidad.state }}"{{ "," if not loop.last else "" }}
              {% endfor %}
            }
            """
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(template_url, headers=self.headers, json=payload) as response:
                    text_response = await response.text()

                    if response.status == 200:
                        try:
                            data = json.loads(text_response)
                            estados = {
                                entidad.split(
                                    '.')[-1]: "activada" if estado == "off" else "desactivada"
                                for entidad, estado in data.items()
                            }
                            return estados
                        except json.JSONDecodeError:
                            return {
                                "error": "La respuesta de Home Assistant no es un JSON válido",
                                "detalle": text_response
                            }
                    else:
                        return {
                            "error": f"Error en la petición a Home Assistant (código {response.status})",
                            "detalle": text_response
                        }
        except Exception as e:
            return {"error": f"Error en la conexión con Home Assistant: {str(e)}"}

    async def scan_cameras(self) -> Dict[str, Any]:
        """
        Obtiene información de todas las cámaras.

        Returns:
            Información de las cámaras o error
        """
        if not self.enabled:
            return {"error": "La integración con Home Assistant está deshabilitada"}

        template_url = f"{self.url}/api/template"
        payload = {
            "template": """
            {% set camaras = states.camera | list %}
            {
              "camaras": [
                {% for camara in camaras %}
                  {
                    "id": "{{ camara.entity_id }}",
                    "name": "{{ camara.name }}",
                    "state": "{{ camara.state }}"
                  }{{ "," if not loop.last else "" }}
                {% endfor %}
              ]
            }
            """
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(template_url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        return {"error": f"Error en la petición a Home Assistant (código {response.status})"}
        except Exception as e:
            return {"error": f"Error al escanear cámaras: {str(e)}"}

    async def get_camera_image(self, camera_entity_id: str) -> Optional[str]:
        """
        Obtiene la URL de la imagen de una cámara.

        Args:
            camera_entity_id: ID de la entidad de la cámara

        Returns:
            URL de la imagen o None si hay error
        """
        if not self.enabled:
            return None

        # Verificar si la cámara existe
        state_url = f"{self.url}/api/states/{camera_entity_id}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(state_url, headers=self.headers) as response:
                    if response.status == 200:
                        # La cámara existe, retornar URL con timestamp para evitar cache
                        import time
                        camera_url = f"{self.url}/api/camera_proxy/{camera_entity_id}?t={int(time.time())}"
                        return camera_url
                    else:
                        print(f"Error al verificar cámara: {response.status}")
                        return None
        except Exception as e:
            print(f"Error al obtener imagen de cámara: {str(e)}")
            return None
