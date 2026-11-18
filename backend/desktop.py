"""Open Atlas in a Windows desktop window with a loopback server."""

import os
import socket
import sys
from contextlib import contextmanager
from threading import Thread
from time import monotonic, sleep

import uvicorn

from backend.core.config import settings
from backend.windows_startup import ROOT, HOST, check_panel

DESKTOP_PORT = 8765


@contextmanager
def local_server(port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        if sys.platform == "win32":
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            listener.bind((HOST, port))
        except OSError as error:
            raise RuntimeError(f"A porta {port} está em uso. Confira se a janela do Atlas já está aberta.") from error
        bound_port = listener.getsockname()[1]
        config = uvicorn.Config(
            "backend.api.app:app", host=HOST, port=bound_port,
            access_log=False, log_config=None, proxy_headers=False,
            timeout_graceful_shutdown=3,
        )
        server = uvicorn.Server(config)
        worker = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        worker.start()
        try:
            deadline = monotonic() + 10
            while not server.started and worker.is_alive() and monotonic() < deadline:
                sleep(0.05)
            if not server.started:
                raise RuntimeError("O servidor do Atlas não iniciou. Confira a instalação e o arquivo .env.")
            yield f"http://{HOST}:{bound_port}"
        finally:
            server.should_exit = True
            worker.join(timeout=5)


def run_window() -> None:
    check_panel()
    import webview
    from webview.platforms.winforms import is_chromium

    if not is_chromium:
        raise RuntimeError("Instale o Microsoft Edge WebView2 Runtime para abrir o Atlas e usar o microfone.")
    with local_server(DESKTOP_PORT) as url:
        webview.create_window(
            settings.agent_name, url, width=1200, height=800, min_size=(360, 520),
            background_color="#080e19",
        )
        webview.start(
            gui="edgechromium", debug=False, private_mode=False,
            storage_path=str(ROOT / "data" / "desktop"),
        )


def main() -> int:
    if sys.platform != "win32":
        print("A janela desktop do Atlas está disponível no Windows.", file=sys.stderr)
        return 1

    from ctypes import windll

    os.chdir(ROOT)
    try:
        run_window()
    except Exception as error:
        windll.user32.MessageBoxW(None, str(error), "Atlas — falha na inicialização", 0x10)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
