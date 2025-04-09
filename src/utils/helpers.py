# src/utils/helpers.py
import unicodedata
from typing import Dict, Any


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
