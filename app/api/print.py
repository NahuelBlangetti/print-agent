from fastapi import APIRouter, HTTPException, status

from app.core.logger import get_logger
from app.drivers.escpos import EscPosDriver
from app.drivers.zebra import ZebraDriver
from app.schemas.print_schemas import (
    PrintJobResponse,
    PrintLabelRequest,
    PrintTicketRequest,
)
from app.services.queue import print_queue

logger = get_logger(__name__)

router = APIRouter(prefix="/print", tags=["print"])

_zebra_driver = ZebraDriver()
_escpos_driver = EscPosDriver()


@router.post("/label", response_model=PrintJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def print_label(payload: PrintLabelRequest) -> PrintJobResponse:
    """Encola una etiqueta ZPL para ser impresa en una impresora Zebra (o compatible)."""
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="El contenido ZPL no puede estar vacio")

    job = await print_queue.enqueue(payload.printer, payload.content, _zebra_driver)
    return PrintJobResponse(job_id=job.job_id, status=job.status, printer=job.printer)


@router.post("/ticket", response_model=PrintJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def print_ticket(payload: PrintTicketRequest) -> PrintJobResponse:
    """Encola un ticket ESC/POS para ser impreso en una impresora de tickets."""
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="El contenido ESC/POS no puede estar vacio")

    job = await print_queue.enqueue(payload.printer, payload.content, _escpos_driver)
    return PrintJobResponse(job_id=job.job_id, status=job.status, printer=job.printer)


@router.get("/job/{job_id}", response_model=PrintJobResponse)
async def get_job_status(job_id: str) -> PrintJobResponse:
    """Consulta el estado de un trabajo de impresion encolado previamente."""
    job = print_queue.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return PrintJobResponse(job_id=job.job_id, status=job.status, printer=job.printer, detail=job.detail)
