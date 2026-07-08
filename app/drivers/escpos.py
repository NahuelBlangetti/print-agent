"""
Driver para impresoras de tickets que usan el estandar ESC/POS
(Epson, XPrinter y compatibles).

El agente NO genera los comandos ESC/POS: solo reenvia el contenido tal
cual llega desde Laravel, en modo RAW.
"""
from app.core.logger import get_logger
from app.drivers.base import PrinterDriver
from app.drivers.raw import send_raw_bytes

logger = get_logger(__name__)


class EscPosDriver(PrinterDriver):
    """Envia contenido ESC/POS crudo a una impresora de tickets vía modo RAW."""

    def print_raw(self, printer_name: str, content: str) -> None:
        logger.info("Enviando ticket ESC/POS a '%s' (%d bytes)", printer_name, len(content))
        data = content.encode("utf-8", errors="replace")
        send_raw_bytes(printer_name, data, job_name="ESCPOS-Ticket")
