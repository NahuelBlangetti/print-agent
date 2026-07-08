"""
Helper interno, compartido por los drivers, para enviar bytes RAW a una
impresora instalada en Ubuntu/Linux via CUPS (pycups).

Es el equivalente a _windows_raw.py pero para Linux. La API de CUPS
trabaja con archivos (no con bytes en memoria como win32print), asi que
el contenido se vuelca primero a un archivo temporal y se elimina al
finalizar.
"""
import os
import platform
import tempfile

from app.core.logger import get_logger
from app.drivers.base import PrinterDriverError

logger = get_logger(__name__)

IS_LINUX = platform.system() == "Linux"


def send_raw_bytes(printer_name: str, data: bytes, job_name: str = "PrintAgentJob") -> None:
    """Envia `data` en crudo (modo RAW) a la impresora `printer_name` via CUPS."""
    if not IS_LINUX:
        raise PrinterDriverError(
            f"Impresion RAW via CUPS solo soportada en Linux en esta version. "
            f"(printer={printer_name!r}, plataforma actual={platform.system()})"
        )

    try:
        import cups  # type: ignore
    except ImportError as exc:  # pragma: no cover - solo ocurre si falta pycups
        raise PrinterDriverError(
            "pycups no esta instalado. Ejecuta: pip install pycups "
            "(requiere el paquete de sistema libcups2-dev)"
        ) from exc

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(data)
            tmp_path = tmp_file.name

        conn = cups.Connection()
        # options={"raw": "True"} evita que CUPS filtre/transforme el
        # contenido, sea o no una cola configurada como RAW.
        conn.printFile(printer_name, tmp_path, "PrintAgent - " + job_name, {"raw": "True"})
    except Exception as exc:
        logger.exception("Fallo al imprimir en %s", printer_name)
        raise PrinterDriverError(f"No se pudo imprimir en '{printer_name}': {exc}") from exc
    finally:
        if tmp_path is not None:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
