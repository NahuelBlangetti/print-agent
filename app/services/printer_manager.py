"""
PrinterManager: se encarga unicamente de listar las impresoras
instaladas en el sistema operativo. No sabe nada de ZPL, ESC/POS ni
de logica de negocio.
"""
import platform

from app.core.logger import get_logger
from app.schemas.print_schemas import PrinterInfo
from app.services.printer_classifier import guess_printer_type

logger = get_logger(__name__)

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"


class PrinterManager:
    """Lista impresoras disponibles en el sistema operativo actual."""

    def list_printers(self) -> list[PrinterInfo]:
        if IS_WINDOWS:
            return self._list_windows_printers()
        if IS_LINUX:
            return self._list_linux_printers()
        return self._list_dev_fallback_printers()

    # -- Windows -----------------------------------------------------
    def _list_windows_printers(self) -> list[PrinterInfo]:
        try:
            import win32print  # type: ignore
        except ImportError:
            logger.error("pywin32 no esta instalado, no se pueden listar impresoras")
            return []

        printers: list[PrinterInfo] = []
        default_printer = None
        try:
            default_printer = win32print.GetDefaultPrinter()
        except Exception:
            logger.warning("No se pudo determinar la impresora predeterminada")

        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        for printer in win32print.EnumPrinters(flags):
            # printer es una tupla: (flags, description, name, comment)
            name = printer[2]
            printers.append(
                PrinterInfo(
                    name=name,
                    is_default=(name == default_printer),
                    status="ready",
                    guessed_type=guess_printer_type(name),
                )
            )
        return printers

    # -- Linux (Ubuntu) via CUPS --------------------------------------
    def _list_linux_printers(self) -> list[PrinterInfo]:
        try:
            import cups  # type: ignore
        except ImportError:
            logger.error("pycups no esta instalado, no se pueden listar impresoras")
            return []

        # Estados IPP/CUPS: 3 = idle (lista), 4 = imprimiendo, 5 = detenida
        state_map = {3: "ready", 4: "printing", 5: "stopped"}

        try:
            conn = cups.Connection()
            default_printer = conn.getDefault()
            return [
                PrinterInfo(
                    name=name,
                    is_default=(name == default_printer),
                    status=state_map.get(info.get("printer-state"), "unknown"),
                    guessed_type=guess_printer_type(name),
                )
                for name, info in conn.getPrinters().items()
            ]
        except Exception:
            logger.exception("No se pudieron listar las impresoras via CUPS")
            return []

    # -- Fallback (otras plataformas, solo para desarrollo/testing) --
    def _list_dev_fallback_printers(self) -> list[PrinterInfo]:
        logger.warning(
            "Enumeracion de impresoras solo soportada en Windows y Linux (CUPS) "
            "en esta version. Devolviendo lista vacia (plataforma actual: %s)",
            platform.system(),
        )
        return []


printer_manager = PrinterManager()
