@echo off
setlocal
pushd "%~dp0" || exit /b 1
if not exist ".venv\Scripts\pythonw.exe" (
    echo Execute InstalarAtlasDesktop.cmd antes de abrir o Atlas.
    pause
    popd
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" -m backend.desktop
popd
