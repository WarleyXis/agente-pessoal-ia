@echo off
setlocal
pushd "%~dp0" || exit /b 1
set "AtlasStartupAction=%~1"
if not defined AtlasStartupAction set "AtlasStartupAction=ativar"
if not exist ".venv\Scripts\python.exe" (
    echo Instale o Atlas primeiro conforme o README.
    popd
    exit /b 1
)
".venv\Scripts\python.exe" -m backend.windows_startup "%AtlasStartupAction%"
set "AtlasStartupResult=%ERRORLEVEL%"
popd
exit /b %AtlasStartupResult%
