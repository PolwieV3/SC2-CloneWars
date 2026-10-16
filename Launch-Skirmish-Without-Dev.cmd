@echo off
setlocal
set "SC2_DEV_EXE=%~dp0local\dev-game\bin\SupremeCommander2.exe"
if not exist "%SC2_DEV_EXE%" (
    echo The development copy is missing. See README.md to refresh the baseline.
    pause
    exit /b 1
)
echo Launching the separate Supreme Commander 2 development copy.
echo Keep Steam running and confirm the game process uses this copy.
if not exist "%~dp0local\logs" mkdir "%~dp0local\logs"
cd /d "%~dp0local\dev-game\bin"
start "" "%SC2_DEV_EXE%" /log "%~dp0local\logs\clonewars-game.log"
