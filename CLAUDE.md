# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Print Agent is a local FastAPI service that acts as an intermediary between a
cloud-hosted Laravel app and printers physically installed on a client's
machine (Windows or Ubuntu). Laravel never talks to a printer directly — it sends
already-generated raw content (ZPL for Zebra labels, ESC/POS for ticket
printers) over HTTPS to this agent, which forwards it byte-for-byte to the OS
print spooler.

```
Laravel (Cloud)  --HTTPS-->  Print Agent (FastAPI)  --USB/LAN-->  Printers
```

**The agent contains no business logic.** It does not generate ZPL/ESC-POS,
does not touch a database, and does not know about products or orders. Keep
it that way — if a change requires the agent to understand what it's
printing, that logic belongs in Laravel, not here.

## Commands

```bash
python -m venv .venv
.venv\Scripts\activate                       # Windows
pip install -r requirements.txt
copy config\.env.example config\.env         # optional, to override host/port/etc.

uvicorn app.main:app --reload --port 58432    # run in dev
python -m app.main                           # run as it would in production

installer\build.bat                          # Windows: PyInstaller -> dist\print-agent.exe
installer\install_autostart.bat              # Windows: register autostart via Task Scheduler
sudo installer/install_autostart.sh          # Ubuntu: register + start print-agent.service (systemd)
```

There is no test suite, linter, or CI config in this repo currently.

## Platform support: Windows and Ubuntu 22.04

Real printing is supported on two platforms, each via its native printing
subsystem:
- **Windows**: `pywin32` (`win32print`), installed only when
  `sys_platform == "win32"` (see [requirements.txt](requirements.txt)).
- **Ubuntu/Linux**: CUPS via `pycups`, installed only when
  `sys_platform == "linux"`. Requires the `libcups2-dev` system package to
  build (see the Ubuntu install steps in [README.md](README.md)) and
  printers registered in CUPS (ideally as a RAW queue).

`app/drivers/raw.py` is the dispatcher both `zebra.py` and `escpos.py` call
through — it picks `_windows_raw.py` or `_linux_raw.py` based on
`platform.system()` at call time so the drivers themselves stay
platform-agnostic. `app/services/printer_manager.py` has the equivalent
split for listing printers (`_list_windows_printers` / `_list_linux_printers`).

On any other platform (macOS, or Windows/Ubuntu missing the native
dependency), the server still boots for development, but:
- `GET /printers` returns an empty list (`_list_dev_fallback_printers` in
  `printer_manager.py`)
- `POST /print/label` and `POST /print/ticket` raise `PrinterDriverError`
  explaining the current platform isn't supported (`raw.py`'s dispatcher, or
  the per-platform module if the native dependency is missing)

When adding a third platform, add its own `_<os>_raw.py` and
`_list_<os>_printers`, and wire both into their respective dispatchers —
don't special-case a new OS inline inside the existing platform modules.

## Architecture

Strict layering, one direction of dependency: `api` → `services` → `drivers`.

- **`app/api/`** — FastAPI routers only. Validates request shape via Pydantic
  schemas and delegates immediately; no printing logic lives here.
- **`app/services/`** — application logic that doesn't know about specific
  printer brands/protocols:
  - `queue.py` — `PrintQueue`, an in-memory FIFO (`asyncio.Queue`) with a
    single background worker task. All print jobs go through this so two
    jobs never write to a printer spooler concurrently. Job state
    (`queued`/`printing`/`done`/`failed`) is tracked in an in-memory dict
    keyed by `job_id` (a UUID) — jobs are lost on restart, there's no
    persistence. The worker runs the (blocking, win32) `driver.print_raw` in
    a thread executor so it doesn't block the asyncio event loop.
  - `printer_manager.py` — lists installed OS printers only; knows nothing
    about ZPL/ESC-POS.
- **`app/drivers/`** — one file per printer brand/protocol, each a subclass
  of the abstract `PrinterDriver` in `base.py` implementing
  `print_raw(printer_name, content)`. Drivers forward content as-is — they
  never transform or validate ZPL/ESC-POS, and they call `raw.py`'s
  `send_raw_bytes`, never a platform-specific module directly. `raw.py`
  dispatches to `_windows_raw.py` (via `win32print`) or `_linux_raw.py` (via
  `pycups`, which requires writing content to a temp file since the CUPS API
  takes file paths, not in-memory bytes).
- **`app/schemas/print_schemas.py`** — all Pydantic DTOs (requests,
  responses, `JobStatus` enum) in one file.
- **`app/core/`** — `config.py` (pydantic-settings `Settings`, loaded from
  `config/.env`, see `config/.env.example` for all keys) and `logger.py`
  (configures a root logger once, writing to both stdout and a rotating file
  in `logs/`).

## CORS and the Laravel integration

Laravel runs in the cloud; the agent runs on `127.0.0.1` on the client's
machine, so Laravel's backend can never reach it directly — only the
client's browser can, via client-side JS. That makes any cross-origin
request from a page served by Laravel's domain to the agent a CORS request.
`CORSMiddleware` is wired in [app/main.py](app/main.py) using
`settings.cors_origins`, which defaults to `[]` (no origins allowed) — it
must be set in `config/.env` (`CORS_ORIGINS=["https://app.example.com"]`,
JSON array) for the browser-based integration to work at all. See
[docs/LARAVEL_INTEGRATION.md](docs/LARAVEL_INTEGRATION.md) for the full
request flow and an example.

### Adding a new printer brand

Create `app/drivers/<brand>.py` with a class extending `PrinterDriver`
implementing `print_raw`, then wire it into the relevant endpoint in
`app/api/print.py`. No changes needed to the queue, logging, or existing
drivers (Open/Closed).

### Endpoints (v1.0.0)

- `GET /status` — health/version check
- `GET /printers` — list installed printers (Windows or Ubuntu/CUPS; empty elsewhere)
- `POST /print/label` — enqueue raw ZPL for a Zebra-compatible printer, `202`
- `POST /print/ticket` — enqueue raw ESC/POS for a ticket printer, `202`
- `GET /print/job/{job_id}` — poll status of a previously enqueued job

### Planned but not yet implemented

`Settings.api_key` exists in config but is not yet enforced anywhere — there
is currently no authentication between Laravel and the agent. See the
Roadmap section of [README.md](README.md) for other planned work (web config
UI, printer auto-detection, a real Windows service instead of Task Scheduler,
and a possible rename to a broader "Local Device Agent" scope covering
scales/cash drawers/payment terminals).
