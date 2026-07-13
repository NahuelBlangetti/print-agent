@echo off
REM Instalador para la PC del cliente final (no tecnico).
REM
REM Uso: colocar este archivo en la MISMA carpeta que print-agent.exe
REM y config\.env, y hacer click derecho -> "Ejecutar como administrador".
REM
REM Registra el arranque automatico en el Programador de Tareas de
REM Windows y arranca el agente ahora mismo, para no tener que
REM reiniciar la PC para probarlo.

set EXE_PATH=%~dp0print-agent.exe

if not exist "%EXE_PATH%" (
    echo No se encontro print-agent.exe en esta carpeta.
    echo Asegurate de que instalar_cliente.bat este en la misma carpeta
    echo que print-agent.exe antes de ejecutarlo.
    pause
    exit /b 1
)

schtasks /create ^
    /tn "PrintAgent" ^
    /tr "\"%EXE_PATH%\"" ^
    /sc onlogon ^
    /rl highest ^
    /f

if %errorlevel% neq 0 (
    echo.
    echo No se pudo registrar el arranque automatico.
    echo Verifica que hayas ejecutado este archivo como Administrador
    echo ^(click derecho -^> "Ejecutar como administrador"^).
    pause
    exit /b 1
)

start "" "%EXE_PATH%"

echo.
echo Listo. Print Agent quedo instalado y esta funcionando.
echo Se iniciara automaticamente cada vez que se inicie sesion en Windows.
pause
