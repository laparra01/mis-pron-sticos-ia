@echo off
title Picks 90 GT - Servidor y Acceso Remoto
echo =======================================================
echo    PICKS 90 GT - ACCESO REMOTO PARA EL CELULAR
echo =======================================================
echo.

set "PY_CMD=python"
if exist "C:\Users\Jonathan Laparra\anaconda3\python.exe" (
    set "PY_CMD=C:\Users\Jonathan Laparra\anaconda3\python.exe"
) else if exist "C:\Users\Jonathan Laparra\miniconda3\python.exe" (
    set "PY_CMD=C:\Users\Jonathan Laparra\miniconda3\python.exe"
)

echo [1/2] Iniciando servidor Flask en segundo plano...
start /b "" "%PY_CMD%" app.py > nul 2>&1
timeout /t 3 > nul

echo [2/2] Generando enlace publico seguro con Cloudflare...
echo.
echo =======================================================
echo  INSTRUCCIONES PARA TU CELULAR:
echo  1. Busca abajo la linea con el enlace que termina en:
echo     https://[nombre-aleatorio].trycloudflare.com
echo  2. Abre ese enlace en tu celular.
echo  3. Deja esta ventana abierta en tu PC.
echo =======================================================
echo.
cloudflared.exe tunnel --url http://localhost:5000
pause
