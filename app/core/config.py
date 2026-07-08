"""
Configuracion central del Print Agent.

Toda la configuracion se puede sobreescribir mediante variables de entorno
o un archivo .env ubicado en config/.env
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(CONFIG_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Identidad de la app
    app_name: str = "Print Agent"
    version: str = "1.0.0"

    # Servidor
    host: str = "127.0.0.1"
    port: int = 58432

    # Logging
    log_level: str = "INFO"
    log_dir: Path = LOG_DIR
    log_filename: str = "print-agent.log"
    log_max_bytes: int = 5 * 1024 * 1024  # 5 MB
    log_backup_count: int = 5

    # Cola de impresion
    queue_max_size: int = 100

    # CORS: origenes permitidos para llamar al agente desde el navegador
    # (el dominio donde esta alojada la app Laravel). Ej en .env:
    # CORS_ORIGINS=["https://app.tuempresa.com"]
    cors_origins: list[str] = []

    # Seguridad (para futuras versiones: autenticacion por API Key)
    api_key: str | None = None


settings = Settings()

# Aseguramos que existan las carpetas necesarias
settings.log_dir.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
