"""
Contrato base para cualquier driver de impresora.

Agregar una nueva marca en el futuro consiste unicamente en crear una
subclase de PrinterDriver e implementar `print_raw`, sin tocar el resto
del sistema (Open/Closed Principle).
"""
from abc import ABC, abstractmethod


class PrinterDriverError(Exception):
    """Error generico al imprimir."""


class PrinterDriver(ABC):
    """Interfaz que deben cumplir todos los drivers de impresoras."""

    @abstractmethod
    def print_raw(self, printer_name: str, content: str) -> None:
        """
        Envia contenido crudo (ZPL, ESC/POS, etc.) directamente a la
        impresora indicada, sin ningun tipo de transformacion.

        Debe lanzar PrinterDriverError si la impresion falla.
        """
        raise NotImplementedError
