from fastapi import APIRouter

from app.schemas.print_schemas import PrintersResponse
from app.services.printer_manager import printer_manager

router = APIRouter(tags=["printers"])


@router.get("/printers", response_model=PrintersResponse)
async def get_printers() -> PrintersResponse:
    printers = printer_manager.list_printers()
    return PrintersResponse(printers=printers)
