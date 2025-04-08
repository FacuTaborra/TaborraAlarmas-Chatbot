# src/routes/whatsapp_routes.py
from fastapi import APIRouter, Request, HTTPException
from src.controllers.whatsapp_controller import WhatsAppController

router = APIRouter()
whatsapp_controller = WhatsAppController()


@router.get("/whatsapp")
async def validate_webhook(request: Request):
    """
    Endpoint para validar webhook de WhatsApp
    """
    print("🔐 Verificación de WhatsApp")

    try:
        # Validar webhook
        is_valid = await whatsapp_controller.validate_webhook(dict(request.query_params))

        if is_valid:
            # Meta espera recibir el challenge como número entero
            return int(request.query_params.get("hub.challenge", 0))

        raise HTTPException(status_code=403, detail="Verificación fallida")

    except Exception as e:
        print(f"❌ Error en validación de webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/whatsapp")
async def process_whatsapp_message(request: Request):
    """
    Endpoint para procesar mensajes de WhatsApp
    """
    try:
        # Inicializar servicios si es necesario
        await whatsapp_controller.initialize()

        # Obtener payload
        data = await request.json()
        print(f"📥 Nuevo mensaje recibido: {data}")

        # Procesar mensaje
        response = await whatsapp_controller.process_message(data)

        return response

    except Exception as e:
        print(f"❌ Error al procesar mensaje: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Asegurarse de cerrar conexiones
        await whatsapp_controller.close()
