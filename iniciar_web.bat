@echo off
title Picks 90 GT - Servidor Web Local
echo =======================================================
echo            INICIANDO PICKS 90 GT (WEB)
echo =======================================================
echo.

set "PY_CMD=python"
if exist "C:\Users\Jonathan Laparra\miniconda3\python.exe" (
    set "PY_CMD=C:\Users\Jonathan Laparra\miniconda3\python.exe"
)

echo [1/2] Levantando servidor local en http://localhost:5000 ...
echo Abriendo navegador en 3 segundos...
start /b cmd /c "timeout /t 3 /nobreak > nul & start http://localhost:5000"

"%PY_CMD%" app.py
pause
