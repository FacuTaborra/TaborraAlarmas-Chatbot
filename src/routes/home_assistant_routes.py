# src/routes/home_assistant_routes.py
from fastapi import APIRouter, Request, HTTPException, Depends, Body, Header
from typing import Dict, Any
from src.controllers.home_assistant_controller import HomeAssistantController

router = APIRouter()

# Dependencia para obtener el controlador


async def get_controller():
    controller = HomeAssistantController()
    await controller.initialize()
    try:
        yield controller
    finally:
        await controller.close()


@router.post("/home_assistant_response")
async def process_home_assistant_response(
    request: Request,
    controller: HomeAssistantController = Depends(get_controller)
):
    """
    Procesa la respuesta de Home Assistant con verificación de token
    """
    try:
        data = await request.json()

        # Verificar token
        user_id = data.get('user_id')
        token = data.get('token')

        if not user_id or not token:
            raise HTTPException(
                status_code=400, detail="Faltan datos de autenticación")

        # Verificar token usando el controlador
        is_valid = await controller.verify_webhook_token(user_id, token)

        if not is_valid:
            raise HTTPException(
                status_code=403, detail="Token inválido o expirado")

        # Procesar webhook normalmente
        result = await controller.process_response(data)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        "user_id": 1,
        "phone": "543471627777",
        "method": "get_alarm_status",
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
