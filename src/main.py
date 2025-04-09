# src/main.py
import uvicorn
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Importar componentes
from src.core.database import Database
from src.core.memory import RedisManager
from src.routes import whatsapp_routes, home_assistant_routes
from pathlib import Path


# Cargar variables de entorno
os.environ.clear()
load_dotenv(override=True)
# Inicializar servicios
database = Database()
redis_manager = RedisManager()

BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = BASE_DIR / "public"


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

# En main.py
teclados_dir = BASE_DIR / "public" / "imagenes_teclados"
app.mount("/teclados", StaticFiles(directory=teclados_dir), name="teclados")


app.include_router(whatsapp_routes.router,
                   prefix="/webhook", tags=["WhatsApp"])
app.include_router(home_assistant_routes.router,
                   prefix="/webhook", tags=["Home Assistant"])


@app.get("/")
async def index():
    return {"status": "API funcionando correctamente"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
