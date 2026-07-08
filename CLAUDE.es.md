# CLAUDE.md (Español)

Este archivo brinda contexto a Claude Code (claude.ai/code) para trabajar en este repositorio. Es la version en español de [CLAUDE.md](CLAUDE.md); ante cualquier discrepancia, ese archivo es la referencia principal.

## Que es esto

Print Agent es un servicio local FastAPI que actua como intermediario entre
una app Laravel alojada en la nube y las impresoras instaladas fisicamente en
la computadora (Windows o Ubuntu) de un cliente. Laravel nunca habla
directamente con una impresora: envia contenido ya generado (ZPL para
etiquetas Zebra, ESC/POS para impresoras de tickets) por HTTPS a este agente,
que lo reenvia tal cual al spooler de impresion del sistema operativo.

```
Laravel (Cloud)  --HTTPS-->  Print Agent (FastAPI)  --USB/LAN-->  Impresoras
```

**El agente no contiene logica de negocio.** No genera ZPL/ESC-POS, no toca
ninguna base de datos y no conoce productos ni pedidos. Hay que mantenerlo
asi: si un cambio requiere que el agente entienda que esta imprimiendo, esa
logica pertenece a Laravel, no a este repositorio.

## Comandos

```bash
python -m venv .venv
.venv\Scripts\activate                       # Windows
pip install -r requirements.txt
copy config\.env.example config\.env         # opcional, para sobreescribir host/puerto/etc.

uvicorn app.main:app --reload --port 58432    # correr en desarrollo
python -m app.main                           # correr como en produccion

installer\build.bat                          # Windows: PyInstaller -> dist\print-agent.exe
installer\install_autostart.bat              # Windows: registrar autoarranque via Programador de Tareas
sudo installer/install_autostart.sh          # Ubuntu: registrar + iniciar print-agent.service (systemd)
```

Actualmente no hay suite de tests, linter ni configuracion de CI en este repositorio.

## Soporte de plataforma: Windows y Ubuntu 22.04

La impresion real esta soportada en dos plataformas, cada una via su
subsistema nativo de impresion:
- **Windows**: `pywin32` (`win32print`), instalado solo cuando
  `sys_platform == "win32"` (ver [requirements.txt](requirements.txt)).
- **Ubuntu/Linux**: CUPS via `pycups`, instalado solo cuando
  `sys_platform == "linux"`. Requiere el paquete de sistema
  `libcups2-dev` para compilar (ver los pasos de instalacion en Ubuntu
  en [README.md](README.md)) y las impresoras dadas de alta en CUPS
  (idealmente como cola RAW).

`app/drivers/raw.py` es el dispatcher que usan tanto `zebra.py` como
`escpos.py` — elige entre `_windows_raw.py` o `_linux_raw.py` segun
`platform.system()` en el momento de la llamada, para que los drivers
en si se mantengan agnosticos a la plataforma.
`app/services/printer_manager.py` tiene la misma division para listar
impresoras (`_list_windows_printers` / `_list_linux_printers`).

En cualquier otra plataforma (macOS, o Windows/Ubuntu sin la
dependencia nativa instalada), el servidor igual levanta para
desarrollo, pero:
- `GET /printers` devuelve una lista vacia (`_list_dev_fallback_printers`
  en `printer_manager.py`)
- `POST /print/label` y `POST /print/ticket` lanzan `PrinterDriverError`
  explicando que la plataforma actual no esta soportada (el dispatcher
  de `raw.py`, o el modulo especifico si falta la dependencia nativa)

Al agregar una tercera plataforma, crear su propio `_<so>_raw.py` y
`_list_<so>_printers`, y conectarlos en sus respectivos dispatchers —
no agregar casos especiales para un SO nuevo dentro de los modulos de
plataforma existentes.

## Arquitectura

Capas estrictas, con una sola direccion de dependencia:
`api` → `services` → `drivers`.

- **`app/api/`** — solo routers de FastAPI. Valida la forma del request via
  schemas Pydantic y delega inmediatamente; aqui no vive logica de
  impresion.
- **`app/services/`** — logica de aplicacion que no conoce marcas ni
  protocolos especificos de impresora:
  - `queue.py` — `PrintQueue`, una cola FIFO en memoria (`asyncio.Queue`)
    con un unico worker en background. Todos los trabajos de impresion
    pasan por aqui para que dos trabajos nunca escriban al mismo tiempo
    sobre el spooler de una impresora. El estado de cada job
    (`queued`/`printing`/`done`/`failed`) se guarda en un diccionario en
    memoria indexado por `job_id` (un UUID) — los jobs se pierden al
    reiniciar, no hay persistencia. El worker ejecuta `driver.print_raw`
    (bloqueante, via win32) en un thread executor para no bloquear el
    event loop de asyncio.
  - `printer_manager.py` — solo lista las impresoras instaladas en el
    sistema operativo; no sabe nada de ZPL/ESC-POS.
- **`app/drivers/`** — un archivo por marca/protocolo de impresora, cada
  uno una subclase de la clase abstracta `PrinterDriver` en `base.py` que
  implementa `print_raw(printer_name, content)`. Los drivers reenvian el
  contenido tal cual: nunca lo transforman ni validan, y llaman al
  `send_raw_bytes` de `raw.py`, nunca directamente a un modulo especifico
  de plataforma. `raw.py` despacha a `_windows_raw.py` (via `win32print`)
  o `_linux_raw.py` (via `pycups`, que requiere escribir el contenido a
  un archivo temporal ya que la API de CUPS trabaja con paths, no con
  bytes en memoria).
- **`app/schemas/print_schemas.py`** — todos los DTOs Pydantic (requests,
  responses, enum `JobStatus`) en un solo archivo.
- **`app/core/`** — `config.py` (`Settings` de pydantic-settings, cargado
  desde `config/.env`, ver `config/.env.example` para todas las claves) y
  `logger.py` (configura el logger raiz una unica vez, escribiendo tanto a
  stdout como a un archivo rotativo en `logs/`).

## CORS y la integracion con Laravel

Laravel corre en la nube; el agente corre en `127.0.0.1` de la maquina
del cliente, asi que el backend de Laravel nunca puede alcanzarlo
directamente — solo el navegador del cliente puede, via JS del lado
del cliente. Eso hace que cualquier request cross-origin desde una
pagina servida por el dominio de Laravel hacia el agente sea una
request CORS. `CORSMiddleware` esta conectado en
[app/main.py](app/main.py) usando `settings.cors_origins`, que por
defecto es `[]` (ningun origen permitido) — hay que configurarlo en
`config/.env` (`CORS_ORIGINS=["https://app.ejemplo.com"]`, array JSON)
para que la integracion basada en navegador funcione. Ver
[docs/LARAVEL_INTEGRATION.md](docs/LARAVEL_INTEGRATION.md) para el
flujo completo del request y un ejemplo.

### Agregar una nueva marca de impresora

Crear `app/drivers/<marca>.py` con una clase que extienda `PrinterDriver`
implementando `print_raw`, y luego conectarla desde el endpoint
correspondiente en `app/api/print.py`. No hace falta tocar la cola, el
logging, ni los drivers existentes (principio Open/Closed).

### Endpoints (v1.0.0)

- `GET /status` — chequeo de salud/version
- `GET /printers` — lista impresoras instaladas (Windows o Ubuntu/CUPS;
  vacio en otros sistemas)
- `POST /print/label` — encola ZPL crudo para una impresora Zebra o
  compatible, `202`
- `POST /print/ticket` — encola ESC/POS crudo para una impresora de
  tickets, `202`
- `GET /print/job/{job_id}` — consulta el estado de un job previamente
  encolado

### Planeado pero aun no implementado

`Settings.api_key` ya existe en la configuracion pero todavia no se aplica
en ningun lado: hoy no hay autenticacion entre Laravel y el agente. Ver la
seccion Roadmap de [README.md](README.md) para otros items planeados
(interfaz web de configuracion, auto-deteccion de impresoras, un servicio
real de Windows en vez de Programador de Tareas, y una posible
renombracion a un alcance mas amplio tipo "Local Device Agent" cubriendo
balanzas/cajones monederos/terminales de pago).
