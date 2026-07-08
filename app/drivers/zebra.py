"""
Driver para impresoras Zebra (o compatibles) que reciben comandos ZPL.

El agente NO genera ni valida el ZPL: solo lo reenvia tal cual a la
impresora en modo RAW, tal como llega desde Laravel.
"""
from app.core.logger import get_logger
from app.drivers.base import PrinterDriver
from app.drivers.raw import send_raw_bytes

logger = get_logger(__name__)


class ZebraDriver(PrinterDriver):
    """Envia contenido ZPL crudo a una impresora Zebra vía modo RAW."""

    def print_raw(self, printer_name: str, content: str) -> None:
        logger.info("Enviando etiqueta ZPL a '%s' (%d bytes)", printer_name, len(content))
        data = content.encode("utf-8", errors="replace")
        send_raw_bytes(printer_name, data, job_name="ZPL-Label")
