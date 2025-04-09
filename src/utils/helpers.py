# src/utils/helpers.py
import unicodedata
from typing import Dict, Any
from fastapi import Request, HTTPException
from src.core.database import Database
from src.core.memory import RedisManager


def normalize_phone(phone: str) -> str:
    """
    Normaliza un número de teléfono para asegurar un formato consistente.

    Args:
        phone: Número de teléfono

    Returns:
        Número normalizado
    """
    # Quitar espacios y caracteres no numéricos
    phone = ''.join(filter(str.isdigit, phone))

    # Asegurar que tiene formato internacional
    if phone.startswith("549"):
        phone = "54" + phone[3:]
    elif not phone.startswith("54"):
        phone = "54" + phone

    return phone


def remove_accents(text: str) -> str:
    """
    Elimina acentos de un texto.

    Args:
        text: Texto a normalizar

    Returns:
        Texto sin acentos
    """
    text = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in text if not unicodedata.combining(c)])


def parse_whatsapp_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa el payload de WhatsApp para extraer información relevante.

    Args:
        data: Payload de WhatsApp

    Returns:
        Diccionario con datos extraídos
    """
    try:
        result = {
            "success": False,
            "message_id": None,
            "text": None,
            "phone": None,
            "name": None
        }

        entry = data.get("entry", [])
        if not entry:
            return result

        changes = entry[0].get("changes", [])
        if not changes:
            return result

        value = changes[0].get("value", {})
        if "statuses" in value:
            return result

        messages = value.get("messages", [])
        if not messages:
            return result

        message_data = messages[0]
        result["message_id"] = message_data.get("id", "")

        # Extraer texto
        if message_data.get("type") == "text":
            result["text"] = message_data.get("text", {}).get("body", "")
        elif message_data.get("type") == "interactive":
            interactive = message_data.get("interactive", {})
            if interactive.get("type") == "button_reply":
                result["text"] = interactive.get(
                    "button_reply", {}).get("title", "")

        # Extraer teléfono
        result["phone"] = normalize_phone(message_data.get("from", ""))

        # Extraer nombre
        try:
            result["name"] = value.get("contacts", [{}])[0]["profile"]["name"]
        except (IndexError, KeyError):
            result["name"] = "Usuario"

        if result["message_id"] and result["text"] and result["phone"]:
            result["success"] = True

        return result

    except Exception as e:
        print(f"❌ Error al procesar payload de WhatsApp: {e}")
        return {"success": False}


async def get_current_user(request: Request) -> dict:
    """
    Obtiene el usuario actual basado en el token de autenticación.

    Args:
        request: Solicitud HTTP actual

    Returns:
        Diccionario con información del usuario
    """
    # Extraer token del encabezado de autorización
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=401, detail="Token de autenticación no proporcionado")

    token = auth_header.split(' ')[1]

    # Inicializar servicios
    redis_manager = RedisManager()
    database = Database()

    try:
        # Verificar el token en Redis
        user_data = await redis_manager.get_value(f"auth_token:{token}")

        if not user_data:
            # Si no está en Redis, buscar en base de datos
            # Implementa tu lógica de verificación de token
            # Por ejemplo, buscar en una tabla de tokens de usuario
            user_data = await database.verify_auth_token(token)

        if not user_data:
            raise HTTPException(status_code=401, detail="Token inválido")

        return user_data

    except Exception as e:
        raise HTTPException(status_code=401, detail="Error de autenticación")
