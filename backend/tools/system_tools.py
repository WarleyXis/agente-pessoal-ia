# Duas ferramentas simples, de baixo risco, só para provar que o
# mecanismo funciona de ponta a ponta. Ferramentas mais poderosas
# (arquivos, navegador, computador) vêm em fases futuras, já usando
# essa mesma base.

import os
from datetime import datetime

from backend.tools.base import RiskLevel, Tool


class GetCurrentTimeTool(Tool):
    name = "get_current_time"
    description = "Retorna a data e hora atuais do sistema."
    risk_level = RiskLevel.LOW

    def parameters_schema(self) -> dict:
        # Essa ferramenta não precisa de nenhum argumento.
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> str:
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return f"A data e hora atuais são: {agora}"


class ListFilesTool(Tool):
    name = "list_files"
    description = "Lista os arquivos de uma pasta específica."
    risk_level = RiskLevel.LOW

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Caminho da pasta a ser listada. Use '.' para a pasta atual.",
                }
            },
            "required": ["directory"],
        }

    def execute(self, directory: str = ".", **kwargs) -> str:
        try:
            arquivos = os.listdir(directory)
        except FileNotFoundError:
            return f"Pasta não encontrada: {directory}"
        except PermissionError:
            return f"Sem permissão para acessar: {directory}"

        if not arquivos:
            return f"A pasta '{directory}' está vazia."
        return f"Arquivos em '{directory}': " + ", ".join(arquivos)