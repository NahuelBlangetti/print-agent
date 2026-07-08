"""
Helper interno, compartido por los drivers, para enviar bytes RAW a una
impresora instalada en el sistema operativo.

En Windows usa pywin32 (win32print) para hablar directamente con el
spooler en modo RAW. En otros sistemas operativos (usado hoy solo para
desarrollo/testing de este agente, ya que la version 1 es Windows-only)
lanza un error explicativo en vez de fallar silenciosamente.
"""
import platform

from app.core.logger import get_logger
from app.drivers.base import PrinterDriverError

logger = get_logger(__name__)

IS_WINDOWS = platform.system() == "Windows"


def send_raw_bytes(printer_name: str, data: bytes, job_name: str = "PrintAgentJob") -> None:
    """Envia `data` en crudo (modo RAW) a la impresora `printer_name`."""
    if not IS_WINDOWS:
        raise PrinterDriverError(
            f"Impresion RAW solo soportada en Windows en esta version. "
            f"(printer={printer_name!r}, plataforma actual={platform.system()})"
        )

    try:
        import win32print  # type: ignore
    except ImportError as exc:  # pragma: no cover - solo ocurre si falta pywin32
        raise PrinterDriverError(
            "pywin32 no esta instalado. Ejecuta: pip install pywin32"
        ) from exc

    handle = None
    try:
        handle = win32print.OpenPrinter(printer_name)
        job_info = ("PrintAgent - " + job_name, None, "RAW")
        win32print.StartDocPrinter(handle, 1, job_info)
        try:
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, data)
            win32print.EndPagePrinter(handle)
        finally:
            win32print.EndDocPrinter(handle)
    except Exception as exc:
        logger.exception("Fallo al imprimir en %s", printer_name)
        raise PrinterDriverError(f"No se pudo imprimir en '{printer_name}': {exc}") from exc
    finally:
        if handle is not None:
            win32print.ClosePrinter(handle)
