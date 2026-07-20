"""
Driver para impresoras de tickets que usan el estandar ESC/POS
(Epson, XPrinter y compatibles).

El agente NO genera los comandos ESC/POS: solo reenvia el contenido tal
cual llega desde Laravel, en modo RAW.
"""
import base64

from app.core.logger import get_logger
from app.drivers.base import PrinterDriver
from app.drivers.raw import send_raw_bytes

logger = get_logger(__name__)

_BASE64_PREFIX = "base64:"


class EscPosDriver(PrinterDriver):
    """Envia contenido ESC/POS crudo a una impresora de tickets vía modo RAW."""

    def print_raw(self, printer_name: str, content: str) -> None:
        # Los bitmaps de codigo de barras traen bytes > 127 que JSON/UTF-8
        # corromperian en crudo: Laravel los manda como "base64:<payload>"
        # para viajar intactos. El contenido de texto plano (tickets sin
        # bitmaps) sigue llegando sin prefijo, como siempre.
        if content.startswith(_BASE64_PREFIX):
            data = base64.b64decode(content[len(_BASE64_PREFIX):])
        else:
            data = content.encode("utf-8", errors="replace")

        logger.info("Enviando ticket ESC/POS a '%s' (%d bytes)", printer_name, len(data))
        send_raw_bytes(printer_name, data, job_name="ESCPOS-Ticket")
