"""Register the local Atlas panel for the current Windows user's login."""

import argparse
import os
import socket
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
from traceback import print_exc

ROOT = Path(__file__).resolve().parent.parent
STARTUP_ARGUMENTS = "-m backend.windows_startup iniciar"
DESKTOP_ARGUMENTS = "-m backend.desktop"
HOST = "127.0.0.1"
PORT = 8000

SHORTCUT_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$folder = [Environment]::GetFolderPath('Startup')
if (-not $folder -or -not (Test-Path -LiteralPath $folder -PathType Container)) {
    throw 'Pasta de inicializacao do usuario indisponivel.'
}
$path = Join-Path $folder 'Atlas.lnk'
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut($path)
$exists = Test-Path -LiteralPath $path
if ($exists -and $link.Arguments -notin @('-m backend.windows_startup iniciar', '-m backend.desktop')) {
    throw 'Ja existe um atalho Atlas.lnk que pertence a outro aplicativo.'
}
if ($env:ATLAS_STARTUP_ACTION -eq 'desativar') {
    if ($exists) { Remove-Item -LiteralPath $path }
} else {
    $link.TargetPath = $env:ATLAS_STARTUP_TARGET
    $link.Arguments = $env:ATLAS_STARTUP_ARGUMENTS
    $link.WorkingDirectory = $env:ATLAS_STARTUP_DIRECTORY
    $link.Description = 'Iniciar o assistente Atlas ao entrar no Windows'
    $link.Save()
}
"""


def check_panel() -> None:
    if not (ROOT / "frontend" / "dist" / "index.html").is_file():
        raise RuntimeError("Painel ausente. Execute npm --prefix frontend run build na pasta do Atlas.")


def configure(action: str) -> None:
    if sys.platform != "win32":
        raise RuntimeError("A configuração da inicialização automática está disponível no Windows.")
    target = Path(sys.executable).with_name("pythonw.exe")
    if action != "desativar":
        check_panel()
        if not target.is_file():
            raise RuntimeError("Python do ambiente virtual indisponível. Confira o guia de instalação.")
        import uvicorn  # noqa: F401
        if action == "ativar-janela":
            import webview  # noqa: F401

    powershell = Path(os.environ["SystemRoot"]) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    result = subprocess.run(
        [str(powershell), "-NoProfile", "-NonInteractive", "-Command", SHORTCUT_SCRIPT],
        env={
            **os.environ,
            "ATLAS_STARTUP_ACTION": action,
            "ATLAS_STARTUP_TARGET": str(target),
            "ATLAS_STARTUP_ARGUMENTS": DESKTOP_ARGUMENTS if action == "ativar-janela" else STARTUP_ARGUMENTS,
            "ATLAS_STARTUP_DIRECTORY": str(ROOT),
        },
        capture_output=True,
        text=True,
        errors="replace",
        timeout=30,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "O Windows não conseguiu atualizar o atalho Atlas.")
    if action != "desativar":
        print("Atlas ativado na inicialização da sua conta do Windows.")
        if action == "ativar-janela":
            print("A janela do Atlas abrirá quando você entrar no Windows.")
        else:
            print("Após entrar no Windows, abra http://localhost:8000.")
    else:
        print("Atlas desativado na inicialização da sua conta do Windows.")


def launch() -> int:
    os.chdir(ROOT)
    log_path = ROOT / "data" / "inicializacao.log"
    log_path.parent.mkdir(exist_ok=True)
    with log_path.open("a", encoding="utf-8", buffering=1) as log, redirect_stdout(log), redirect_stderr(log):
        print(f"\n{datetime.now():%Y-%m-%d %H:%M:%S} | Iniciando Atlas.")
        try:
            check_panel()
            import uvicorn

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                if sys.platform == "win32":
                    listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                try:
                    listener.bind((HOST, PORT))
                except OSError as error:
                    print(f"Não foi possível usar {HOST}:{PORT}. Confira se o Atlas já está aberto. {error}")
                    return 1
                server = uvicorn.Server(uvicorn.Config(
                    "backend.api.app:app", host=HOST, port=PORT, access_log=False,
                ))
                server.run(sockets=[listener])
                return 0 if server.started else 1
        except Exception:
            print_exc()
            return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=("ativar", "ativar-janela", "desativar", "iniciar"))
    action = parser.parse_args().acao
    if action == "iniciar":
        return launch()
    try:
        configure(action)
    except (RuntimeError, ImportError, OSError, subprocess.TimeoutExpired) as error:
        print(f"Erro ao configurar o Atlas: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
