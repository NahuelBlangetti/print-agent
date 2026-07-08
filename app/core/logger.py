"""
Configuracion de logging del Print Agent.

Escribe logs tanto a consola como a un archivo rotativo en logs/.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler

from app.core.config import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def setup_logging() -> None:
    """Configura el logger raiz una unica vez para toda la aplicacion."""
    global _configured
    if _configured:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    log_path = settings.log_dir / settings.log_filename
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger con el nombre indicado, garantizando configuracion previa."""
    setup_logging()
    return logging.getLogger(name)
