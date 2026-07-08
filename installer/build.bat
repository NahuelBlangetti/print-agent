@echo off
REM Compila Print Agent como ejecutable de Windows.
REM Ejecutar desde la raiz del proyecto: installer\build.bat

echo Instalando dependencias...
pip install -r requirements.txt

echo Compilando con PyInstaller...
pyinstaller installer\print-agent.spec --distpath dist --workpath build --clean

echo.
echo Listo. Ejecutable generado en dist\print-agent.exe
pause
