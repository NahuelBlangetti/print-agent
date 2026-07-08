"""
Print Agent - punto de entrada.

Levanta un servidor HTTP local que actua como intermediario entre
Laravel (Cloud) y las impresoras instaladas en la PC del cliente.

Ejecutar en desarrollo:
    uvicorn app.main:app --reload --port 58432

Ejecutar en produccion (Windows):
    python -m app.main
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import printers, print as print_router, status
from app.core.config import settings
from app.core.logger import get_logger, setup_logging
from app.services.queue import print_queue

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando %s v%s en http://%s:%s", settings.app_name, settings.version, settings.host, settings.port)
    print_queue.start()
    yield
    await print_queue.stop()
    logger.info("Print Agent detenido")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Agente local de impresion: puente entre Laravel (Cloud) y las impresoras del cliente.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(status.router)
app.include_router(printers.router)
app.include_router(print_router.router)


def run() -> None:
    """Permite ejecutar el agente con `python -m app.main`."""
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    run()
