# src/routes/home_assistant_routes.py
from fastapi import APIRouter, Request, HTTPException, Depends, Body
import json
import traceback
from typing import Dict, Any
from src.controllers.home_assistant_controller import HomeAssistantController
from src.core.database import Database

router = APIRouter()

# Dependencia para obtener el controlador


async def get_controller():
    controller = HomeAssistantController()
    await controller.initialize()
    try:
        yield controller
    finally:
        await controller.close()


async def get_database():
    database = Database()
    await database.connect()
    try:
        yield database
    finally:
        await database.close()


@router.post("/home_assistant_response")
async def process_home_assistant_response(
    request: Request,
    controller: HomeAssistantController = Depends(get_controller),
    database: Database = Depends(get_database)
):
    """
    Procesa la respuesta de Home Assistant con verificación de token temporal
    """
    try:
        data = await request.json()
        print(f"📥 Recibiendo respuesta de Home Assistant: {data}")

        # Verificar datos básicos necesarios
        callback_token = data.get('callback_token')
        conversation_id = data.get('conversation_id')
        phone = data.get('phone')

        if not callback_token or not conversation_id or not phone:
            error_msg = "Faltan datos requeridos (token, ID de conversación o teléfono)"
            print(f"⚠️ {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        if not database.verify_and_use_temp_ha_token(callback_token, conversation_id):
            # Si el token no es válido, retornar error
            error_msg = "Token de callback inválido"
            print(f"⚠️ {error_msg}")
            raise HTTPException(status_code=403, detail=error_msg)

        # Procesar la respuesta
        result = await controller.process_response(data)

        return result

    except json.JSONDecodeError:
        error_msg = "Error al decodificar JSON de la solicitud"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"Error al procesar respuesta: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/trigger_home_assistant")
async def trigger_home_assistant(
    request_data: Dict[str, Any] = Body(...),
    controller: HomeAssistantController = Depends(get_controller)
):
    """
    Endpoint para disparar acciones en Home Assistant manualmente.
    Este endpoint puede ser usado por otras partes de la aplicación
    o para pruebas desde herramientas como Postman.

    Ejemplo de body:
    {
        "user_id": 1111,
        "phone": "1111111",
        "method": "estado_alarma",
        "params": {}
    }
    """
    try:
        # Validar datos necesarios
        required_fields = ["user_id", "phone", "method"]
        missing_fields = [
            field for field in required_fields if field not in request_data]

        if missing_fields:
            return {"success": False, "message": f"Faltan campos requeridos: {', '.join(missing_fields)}"}

        # Extraer datos
        user_id = request_data["user_id"]
        phone = request_data["phone"]
        method = request_data["method"]
        params = request_data.get("params", {})

        # Llamar al controlador
        result = await controller.trigger_home_assistant(user_id, phone, method, params)

        return result

    except Exception as e:
        print(f"❌ Error al disparar acción en Home Assistant: {e}")
        raise HTTPException(status_code=500, detail=str(e))
