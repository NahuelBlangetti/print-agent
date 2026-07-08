# -*- mode: python ; coding: utf-8 -*-
# Build spec de PyInstaller para Print Agent (Windows).
#
# Uso:
#   pyinstaller installer/print-agent.spec
#
# Genera un unico ejecutable en dist/print-agent.exe que corre el
# servidor FastAPI/uvicorn embebido, sin requerir Python instalado
# en la PC del cliente.

import sys
from pathlib import Path

block_cipher = None
PROJECT_ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(PROJECT_ROOT / "app" / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "win32timezone",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="print-agent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=None,
)
