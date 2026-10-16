@echo off
title 8 Ball Pool - Lancement du Jeu
cd /d "%~dp0"

echo ========================================================
echo           LANCEMENT DE 8 BALL POOL
echo ========================================================
echo.

if exist "C:\Users\jpm\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\jpm\AppData\Local\Programs\Python\Python312\python.exe" main.py
    goto end
)

py -3.12 main.py 2>nul
if %errorlevel% equ 0 goto end

python main.py 2>nul
if %errorlevel% equ 0 goto end

py main.py 2>nul
if %errorlevel% equ 0 goto end

echo Erreur : Python n'a pas pu etre execute automatiquement.
pause

:end
