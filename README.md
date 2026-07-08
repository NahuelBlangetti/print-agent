# Print Agent

Agente local de impresión desarrollado con **FastAPI**, que actúa como
intermediario entre una aplicación Laravel alojada en la nube y las
impresoras instaladas en la computadora del cliente (Windows o Ubuntu).

```
Laravel (Cloud)  --HTTPS-->  Print Agent (FastAPI)  --USB/LAN-->  Impresoras
```

Laravel nunca habla directamente con la impresora: siempre habla con
este agente, que reenvía el contenido ya generado (ZPL / ESC-POS) tal
cual, sin lógica de negocio.

## Estructura del proyecto

```
print-agent/
├── app/
│   ├── api/                 # Routers FastAPI (capa HTTP)
│   │   ├── status.py
│   │   ├── printers.py
│   │   └── print.py
│   ├── core/                 # Configuración y logging
│   │   ├── config.py
│   │   └── logger.py
│   ├── services/              # Lógica de aplicación
│   │   ├── queue.py           # Cola de impresión (evita concurrencia)
│   │   └── printer_manager.py # Enumeración de impresoras del SO
│   ├── drivers/                # Un driver por marca/protocolo
│   │   ├── base.py            # Clase abstracta PrinterDriver
│   │   ├── zebra.py           # ZPL
│   │   ├── escpos.py          # ESC/POS
│   │   ├── raw.py             # Dispatcher RAW segun sistema operativo
│   │   ├── _windows_raw.py    # Helper interno Windows (win32print)
│   │   └── _linux_raw.py      # Helper interno Ubuntu/Linux (CUPS)
│   ├── schemas/                # DTOs Pydantic
│   └── main.py                 # Entry point FastAPI
├── config/                     # .env de configuración
├── logs/                       # Logs rotativos
├── installer/                  # Empaquetado PyInstaller + autostart (Windows/Ubuntu)
├── docs/
│   └── LARAVEL_INTEGRATION.md  # Guia de integracion para el equipo de Laravel
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.12+
- **Windows 10 o superior, 64-bit** (impresión real vía `pywin32`).
  Python 3.9+ ya no soporta Windows 7/8, y el ejecutable compilado con
  PyInstaller se genera para la arquitectura de la máquina donde se
  compila (normalmente x64).
- **Ubuntu 22.04** (impresión real vía CUPS/`pycups`). Requiere CUPS
  instalado y corriendo (viene por defecto en Ubuntu Desktop; en
  Ubuntu Server: `sudo apt install cups`), y las impresoras dadas de
  alta en CUPS (idealmente como cola RAW, para que no transforme el
  ZPL/ESC-POS).

En cualquier otro sistema operativo (macOS, Windows/Ubuntu sin las
dependencias nativas) el servidor levanta igual para desarrollo, pero
los endpoints de impresión devolverán un error explicando que la
plataforma actual no está soportada.

## Instalación

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config\.env.example config\.env   # opcional, para configurar host/puerto
```

### Ubuntu 22.04

`pycups` necesita compilarse contra la librería de CUPS, así que hacen
falta las cabeceras de sistema antes de instalar los paquetes de Python:

```bash
sudo apt update
sudo apt install -y cups libcups2-dev build-essential python3-dev python3-venv

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/.env.example config/.env   # opcional, para configurar host/puerto
```

## Ejecutar en desarrollo

```bash
uvicorn app.main:app --reload --port 58432
```

## Endpoints (v1.0.0)

### `GET /status`
```json
{ "status": "online", "version": "1.0.0" }
```

### `GET /printers`
Lista las impresoras instaladas en el sistema (Windows vía `pywin32`,
Ubuntu vía CUPS).
```json
{
  "printers": [
    { "name": "Zebra ZD220", "is_default": true, "status": "ready" }
  ]
}
```

### `POST /print/label`
Envía ZPL crudo a una impresora Zebra (o compatible). Responde `202`
y el trabajo se procesa en la cola en background.
```json
{ "printer": "Zebra ZD220", "content": "^XA ... ^XZ" }
```

### `POST /print/ticket`
Envía texto/comandos ESC/POS crudos a una impresora de tickets.
```json
{ "printer": "XPrinter", "content": "Texto ESCPOS" }
```

### `GET /print/job/{job_id}`
Consulta el estado (`queued` / `printing` / `done` / `failed`) de un
trabajo previamente encolado.

## CORS (integración con Laravel)

Como Laravel corre en la nube y el agente en `127.0.0.1` de la PC del
cliente, quien llama al agente es el **navegador** (JS), no el backend
de Laravel — ver [docs/LARAVEL_INTEGRATION.md](docs/LARAVEL_INTEGRATION.md)
para el detalle completo de esta arquitectura.

Por defecto no se permite ningún origen (`cors_origins: []`). Para que
el navegador pueda llamar al agente desde la webapp, hay que declarar
el dominio de Laravel en `config/.env`:

```bash
CORS_ORIGINS=["https://app.tuempresa.com"]
```

## Cola de impresión

Todas las impresiones pasan por una cola FIFO en memoria (`app/services/queue.py`)
procesada por un único worker en background, para evitar que dos
trabajos escriban simultáneamente sobre el mismo spooler.

## Agregar una nueva marca de impresora

1. Crear `app/drivers/mi_marca.py` con una clase que extienda `PrinterDriver`
   (`app/drivers/base.py`) e implemente `print_raw(printer_name, content)`.
2. Usarla desde el endpoint correspondiente en `app/api/print.py`.

No es necesario tocar la cola, el logging, ni el resto de los drivers
existentes (Open/Closed Principle).

## Compilar como ejecutable de Windows

```bash
installer\build.bat
```
Genera `dist\print-agent.exe`, que no requiere Python instalado en la
PC del cliente. Ver `installer/print-agent.spec`.

## Autoarranque con Windows

```bash
installer\install_autostart.bat
```
Registra el ejecutable en el Programador de Tareas de Windows para
iniciar en cada inicio de sesión. En una futura versión se migrará a
un Servicio de Windows real (`pywin32` `win32serviceutil`), para poder
arrancar antes del login del usuario.

## Autoarranque con Ubuntu (systemd)

```bash
sudo installer/install_autostart.sh
```
Requiere haber creado antes el entorno virtual e instalado las
dependencias (ver "Instalación > Ubuntu 22.04"). Registra y arranca un
servicio systemd (`print-agent.service`) que corre
`.venv/bin/python -m app.main` con reinicio automático ante fallos.

```bash
systemctl status print-agent      # ver estado
journalctl -u print-agent -f      # ver logs en vivo
```

## Roadmap (futuras versiones)

- [ ] Autenticación mediante API Key entre Laravel y el agente.
- [ ] Configuración desde una interfaz web local.
- [ ] Descubrimiento automático de impresoras / auto-detección de tipo.
- [ ] Actualización automática del agente.
- [ ] Servicio real de Windows (en vez de tarea programada).
- [x] Soporte Ubuntu vía CUPS (`pycups`) y servicio `systemd`.
- [ ] Nuevos tipos de dispositivo: balanzas, cajones monederos,
      terminales de pago, visores de cliente — bajo el mismo agente,
      renombrado eventualmente a algo más amplio (ej. `Local Device Agent`).

## Principios de diseño

- El agente **no contiene lógica de negocio**: no genera ZPL, no
  accede a bases de datos, no conoce productos. Solo recibe contenido
  ya listo para imprimir y lo reenvía a la impresora indicada.
- Arquitectura en capas (`api` → `services` → `drivers`), con
  interfaces abstractas para poder extender sin modificar código
  existente (Clean Architecture / SOLID).
