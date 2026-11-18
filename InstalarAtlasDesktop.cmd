@echo off
setlocal
pushd "%~dp0" || exit /b 1
if not exist ".venv\Scripts\python.exe" (
    py -3.12 -m venv .venv || goto falha
)
".venv\Scripts\python.exe" -m pip install -r requirements-desktop.txt || goto falha
if not exist "data\voices" mkdir "data\voices" || goto falha
".venv\Scripts\python.exe" -m piper.download_voices --download-dir data/voices pt_BR-faber-medium || goto falha
ollama pull qwen3:4b || goto falha
if not exist ".env" copy ".env.example" ".env" >nul || goto falha
".venv\Scripts\python.exe" -c "from dotenv import set_key; set_key('.env', 'OLLAMA_MODEL', 'qwen3:4b', quote_mode='never'); set_key('.env', 'PIPER_VOICE', 'data/voices/pt_BR-faber-medium.onnx', quote_mode='never')" || goto falha
call npm.cmd --prefix frontend ci || goto falha
call npm.cmd --prefix frontend run build || goto falha
echo Atlas pronto. Abra AbrirAtlas.cmd.
popd
exit /b 0

:falha
echo Falha na instalacao. Confira a mensagem acima e se o Ollama esta aberto.
popd
exit /b 1
