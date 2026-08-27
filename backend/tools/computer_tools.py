# Ferramentas de controle do computador: abrir programas, clicar e
# digitar. São as ferramentas de MAIOR RISCO do projeto até agora —
# todas exigem sua aprovação antes de rodar, sem exceção.
#
# Por segurança, "abrir programa" só aceita nomes de uma lista
# pré-aprovada — o modelo NUNCA decide sozinho qual comando/caminho
# executar no seu sistema.

import subprocess
import time
import pygetwindow
import pyautogui

from backend.tools.base import RiskLevel, Tool

ALLOWED_APPS = {
    "bloco de notas": "notepad.exe",
    "notepad": "notepad.exe",
    "calculadora": "calc.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
}


class OpenApplicationTool(Tool):
    name = "open_application"
    description = (
        "Abre um aplicativo do Windows por nome. Só funciona para "
        "aplicativos de uma lista pré-aprovada (ex: 'bloco de notas', "
        "'calculadora', 'paint')."
    )
    risk_level = RiskLevel.HIGH

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Nome do aplicativo a abrir (ex: 'bloco de notas').",
                }
            },
            "required": ["app_name"],
        }

    def execute(self, app_name: str = "", **kwargs) -> str:
        # Normaliza variações comuns que o modelo pode gerar
        # (underscores, hífens) antes de comparar com a lista permitida.
        normalized = app_name.strip().lower().replace("_", " ").replace("-", " ")
        executable = ALLOWED_APPS.get(normalized)

        if executable is None:
            permitidos = ", ".join(sorted(ALLOWED_APPS.keys()))
            return f"Aplicativo não permitido: '{app_name}'. Aplicativos permitidos: {permitidos}."

        subprocess.Popen([executable])
        time.sleep(1.5)  # dá tempo do aplicativo abrir antes da próxima ação
        return f"Aplicativo '{app_name}' aberto com sucesso."


class ClickAtTool(Tool):
    name = "click_at"
    description = (
        "Clica em uma posição específica da tela, em coordenadas de "
        "pixel (x, y). Use apenas quando o usuário informar ou "
        "confirmar as coordenadas exatas."
    )
    risk_level = RiskLevel.HIGH

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "Posição horizontal em pixels."},
                "y": {"type": "integer", "description": "Posição vertical em pixels."},
            },
            "required": ["x", "y"],
        }

    def execute(self, x: int = 0, y: int = 0, **kwargs) -> str:
        pyautogui.click(x, y)
        return f"Clique executado em ({x}, {y})."


class TypeTextTool(Tool):
    name = "type_text"
    description = (
        "Digita um texto em uma janela do Windows. Sempre que o "
        "usuário mencionar um aplicativo específico (ex: 'no bloco "
        "de notas'), preencha 'window_title' com o nome dele — sem "
        "isso, o texto pode ir para a janela errada, já que o "
        "terminal do agente costuma estar em foco quando esta "
        "ferramenta é chamada."
    )
    risk_level = RiskLevel.HIGH

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto a ser digitado."},
                "window_title": {
                    "type": "string",
                    "description": "Parte do título da janela onde digitar (ex: 'Bloco de Notas').",
                },
            },
            "required": ["text"],
        }

    def execute(self, text: str = "", window_title: str = "", **kwargs) -> str:
        if window_title:
            janelas = pygetwindow.getWindowsWithTitle(window_title)
            if not janelas:
                return f"Nenhuma janela encontrada com título contendo '{window_title}'."
            janelas[0].activate()
            time.sleep(0.5)  # dá tempo do Windows trazer a janela para frente

        pyautogui.write(text, interval=0.02)
        return f"Texto digitado: '{text}'."