# src/main.py
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Importar componentes
from src.core.database import Database
from src.core.memory import RedisManager
from src.routes import whatsapp_routes, image_routes

# Cargar variables de entorno
load_dotenv()

# Inicializar servicios
database = Database()
redis_manager = RedisManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar servicios
    print("🚀 Iniciando servicios...")
    await database.connect()

    # Cargar información del negocio en Redis
    business_info = await database.load_business_info()
    await redis_manager.set_value("info_business", business_info)

    yield  # FastAPI ejecuta la app

    # Cerrar servicios al finalizar
    print("🔴 Cerrando servicios...")
    await database.close()

# Crear la aplicación FastAPI
app = FastAPI(lifespan=lifespan)

# Incluir rutas
app.include_router(whatsapp_routes.router,
                   prefix="/webhook", tags=["WhatsApp"])
app.include_router(image_routes.router, prefix="/webhook", tags=["Images"])


@app.get("/")
async def index():
    return {"status": "API funcionando correctamente"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
