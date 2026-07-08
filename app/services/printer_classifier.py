"""
Heuristica para adivinar el tipo de una impresora instalada en el SO a
partir de su nombre (Windows) o nombre de cola (CUPS), ya que ni Windows
ni CUPS exponen un campo estandar de "tipo de impresora".

No es 100% infalible: se basa en patrones de nombre de marcas conocidas.
Sigue sin conocer productos, ordenes ni logica de negocio - solo reconoce
familias de hardware de impresion, igual que ya hacen los drivers.
"""
import re

_LABEL_PATTERN = re.compile(
    r"zebra|zpl|zdesigner|\bzd\d|\bzt\d|\bgc4|\bgk4|\bgx4|godex|\btsc\b|ttp-|sato|intermec",
    re.IGNORECASE,
)

_TICKET_PATTERN = re.compile(
    r"epson|escpos|esc/pos|tm-t|tm-m|tm-u|star\s?tsp|bixolon|xprinter|citizen|"
    r"rongta|pos-?58|pos-?80|receipt|ticket",
    re.IGNORECASE,
)


def guess_printer_type(name: str) -> str:
    """Devuelve 'label', 'ticket' u 'unknown' segun el nombre de la impresora."""
    if _LABEL_PATTERN.search(name):
        return "label"
    if _TICKET_PATTERN.search(name):
        return "ticket"
    return "unknown"
