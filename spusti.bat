@echo off
title Python Script Launcher

echo ============================
echo   PYTHON SCRIPT LAUNCHER
echo ============================
echo.

set /p scriptname=Zadej nazev Python souboru bez .py : 

echo.
echo Spoustim: %scriptname%.py
echo.

python "%scriptname%.py"

echo.
echo ============================
echo Script byl ukoncen.
echo ============================
pause