"""
Dispatcher de impresion RAW: delega en el helper especifico de cada
sistema operativo, para que los drivers (zebra.py, escpos.py) no
necesiten conocer la plataforma actual.

Agregar soporte para un nuevo sistema operativo consiste en crear su
propio _<so>_raw.py e incorporarlo aqui, sin tocar los drivers.
"""
import platform

from app.drivers.base import PrinterDriverError

_SYSTEM = platform.system()


def send_raw_bytes(printer_name: str, data: bytes, job_name: str = "PrintAgentJob") -> None:
    """Envia `data` en crudo a `printer_name` usando el helper de la plataforma actual."""
    if _SYSTEM == "Windows":
        from app.drivers._windows_raw import send_raw_bytes as _send
    elif _SYSTEM == "Linux":
        from app.drivers._linux_raw import send_raw_bytes as _send
    else:
        raise PrinterDriverError(
            f"Impresion RAW no soportada en esta plataforma ({_SYSTEM}). "
            "Soportado: Windows y Ubuntu/Linux (via CUPS)."
        )
    _send(printer_name, data, job_name)
