@echo off
REM Registra print-agent.exe para que se ejecute automaticamente al
REM iniciar sesion en Windows, usando el Programador de Tareas.
REM
REM Requiere haber compilado antes con build.bat (dist\print-agent.exe)
REM Ejecutar como Administrador.
REM Requiere Windows 10 o superior (64-bit).

set EXE_PATH=%~dp0..\dist\print-agent.exe

schtasks /create ^
    /tn "PrintAgent" ^
    /tr "\"%EXE_PATH%\"" ^
    /sc onlogon ^
    /rl highest ^
    /f

echo.
echo Tarea "PrintAgent" registrada. Se iniciara automaticamente en cada
echo inicio de sesion de Windows.
echo (Nota: en una version futura se migrara a un Servicio de Windows
echo real para poder iniciar antes del login del usuario.)
pause
