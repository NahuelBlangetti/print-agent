"""
Schemas (DTOs) de entrada/salida de la API.

El agente nunca conoce productos ni logica de negocio: solo recibe
contenido ya listo para imprimir (ZPL o texto ESC/POS).
"""
from enum import Enum

from pydantic import BaseModel, Field


class StatusResponse(BaseModel):
    status: str = "online"
    version: str


class PrinterInfo(BaseModel):
    name: str
    driver_name: str | None = None
    is_default: bool = False
    status: str = "unknown"
    guessed_type: str = "unknown"  # "label" | "ticket" | "unknown", ver printer_classifier.py


class PrintersResponse(BaseModel):
    printers: list[PrinterInfo]


class PrintLabelRequest(BaseModel):
    printer: str = Field(..., description="Nombre exacto de la impresora instalada")
    content: str = Field(..., description="Contenido ZPL crudo, ej: ^XA ... ^XZ")


class PrintTicketRequest(BaseModel):
    printer: str = Field(..., description="Nombre exacto de la impresora instalada")
    content: str = Field(..., description="Texto / comandos ESC/POS crudos")


class JobStatus(str, Enum):
    QUEUED = "queued"
    PRINTING = "printing"
    DONE = "done"
    FAILED = "failed"


class PrintJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    printer: str
    detail: str | None = None
