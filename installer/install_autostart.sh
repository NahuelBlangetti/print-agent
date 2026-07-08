#!/bin/bash
# Registra Print Agent como servicio systemd para que se ejecute
# automaticamente al iniciar Ubuntu 22.04.
#
# Requiere haber creado antes el entorno virtual e instalado las
# dependencias (ver README, seccion "Instalacion en Ubuntu").
# Ejecutar con sudo desde la raiz del proyecto:
#   sudo installer/install_autostart.sh

set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "Este script debe ejecutarse con sudo." >&2
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_USER="${SUDO_USER:-root}"
SERVICE_FILE="/etc/systemd/system/print-agent.service"

if [ ! -x "$PROJECT_ROOT/.venv/bin/python" ]; then
    echo "No se encontro $PROJECT_ROOT/.venv/bin/python." >&2
    echo "Cree el entorno virtual e instale las dependencias antes de continuar." >&2
    exit 1
fi

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Print Agent
After=network.target cups.service
Wants=cups.service

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$PROJECT_ROOT
ExecStart=$PROJECT_ROOT/.venv/bin/python -m app.main
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now print-agent.service

echo
echo "Servicio 'print-agent' registrado e iniciado."
echo "Ver estado:  systemctl status print-agent"
echo "Ver logs:    journalctl -u print-agent -f"
