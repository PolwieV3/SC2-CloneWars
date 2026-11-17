@echo off
setlocal
set "SC2_DEV_EXE=%~dp0local\dev-game\bin\SupremeCommander2.exe"
if not exist "%SC2_DEV_EXE%" (
    echo The development copy is missing. See README.md to refresh the baseline.
    pause
    exit /b 1
)
if not exist "%~dp0local\dev-game\bin\GARDevModeInit.lua" (
    echo V3 Dev Mode is missing. Use Launch-Skirmish-Without-Dev.cmd for a normal test.
    pause
    exit /b 1
)
echo Launching the Clone Wars reskin test copy with V3 Dev Mode available on F8.
echo Keep Steam running and confirm the game process uses this copy.
if not exist "%~dp0local\logs" mkdir "%~dp0local\logs"
cd /d "%~dp0local\dev-game\bin"
start "" /wait "%SC2_DEV_EXE%" /gar-dev-mode /init "%~dp0local\dev-game\bin\GARDevModeInit.lua" /log "%~dp0local\logs\clonewars-game.log"
set "SC2_EXIT=%ERRORLEVEL%"
if not "%SC2_EXIT%"=="0" (
    echo Supreme Commander 2 exited with status %SC2_EXIT%.
    echo Startup log: "%~dp0local\logs\clonewars-game.log"
    pause
)
exit /b %SC2_EXIT%
