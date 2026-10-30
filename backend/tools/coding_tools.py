# Ferramentas para o agente trabalhar com código: ler arquivos,
# rodar os testes do projeto, e consultar o estado do Git (somente
# leitura). Ações que modificam código ou o repositório (escrever
# arquivos, fazer commit) ficam para uma fase futura de polimento —
# aqui o foco é o agente conseguir "entender" um projeto.
import sys
import subprocess

from pathlib import Path

from backend.tools.base import RiskLevel, Tool

MAX_CONTENT_LENGTH = 5000

ALLOWED_GIT_SUBCOMMANDS = {"status", "diff", "log", "branch"}


class ReadFileTool(Tool):
    name = "read_file"
    description = (
        "Lê o conteúdo de um arquivo de texto/código. O caminho é "
        "relativo à RAIZ do projeto (onde fica requirements.txt), "
        "não à pasta backend — ex: use 'requirements.txt', não "
        "'backend/requirements.txt'; use 'backend/main.py' para "
        "arquivos dentro de backend."
    )
    risk_level = RiskLevel.LOW
    domain = "coding"
    
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Caminho relativo do arquivo, ex: 'backend/main.py'.",
                }
            },
            "required": ["path"],
        }

    def execute(self, path: str = "", **kwargs) -> str:
        file_path = Path(path)

        # Impede acessar arquivos fora da pasta do projeto — sem isso,
        # um caminho como "../../../../dados_pessoais.txt" poderia
        # escapar da pasta do projeto e ler qualquer arquivo do PC.
        try:
            file_path.resolve().relative_to(Path.cwd().resolve())
        except ValueError:
            return "Acesso negado: só é permitido ler arquivos dentro da pasta do projeto."

        if not file_path.is_file():
            return f"Arquivo não encontrado: {path}"

        try:
            conteudo = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as erro:
            return f"Não foi possível ler o arquivo: {erro}"

        if len(conteudo) > MAX_CONTENT_LENGTH:
            conteudo = conteudo[:MAX_CONTENT_LENGTH] + "\n\n[...conteúdo truncado...]"

        return conteudo


class RunTestsTool(Tool):
    name = "run_tests"
    description = (
        "Executa a suíte de testes automatizados do projeto (pytest) e "
        "devolve o resultado. Use SOMENTE quando o usuário pedir "
        "explicitamente para rodar ou executar os testes. Para ver o "
        "que está escrito dentro de um arquivo, use read_file."
    )
    risk_level = RiskLevel.MEDIUM
    domain = "coding"
    
    def parameters_schema(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> str:
        resultado = subprocess.run(
            [sys.executable, "-m", "pytest", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        saida = (resultado.stdout + resultado.stderr).strip()
        if len(saida) > MAX_CONTENT_LENGTH:
            saida = saida[-MAX_CONTENT_LENGTH:]
        return saida or "Testes executados, nenhuma saída capturada."


class GitInfoTool(Tool):
    name = "git_info"
    description = (
        "Consulta informações do Git (somente leitura). Subcomandos "
        f"permitidos: {', '.join(sorted(ALLOWED_GIT_SUBCOMMANDS))}."
    )
    risk_level = RiskLevel.LOW
    domain = "coding"
    
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "subcommand": {
                    "type": "string",
                    "description": f"Um de: {', '.join(sorted(ALLOWED_GIT_SUBCOMMANDS))}.",
                }
            },
            "required": ["subcommand"],
        }

    def execute(self, subcommand: str = "", **kwargs) -> str:
        subcommand = subcommand.strip().lower()
        if subcommand not in ALLOWED_GIT_SUBCOMMANDS:
            permitidos = ", ".join(sorted(ALLOWED_GIT_SUBCOMMANDS))
            return f"Subcomando não permitido: '{subcommand}'. Permitidos: {permitidos}."

        resultado = subprocess.run(
            ["git", subcommand],
            capture_output=True,
            text=True,
            timeout=30,
        )
        saida = (resultado.stdout + resultado.stderr).strip()
        if len(saida) > MAX_CONTENT_LENGTH:
            saida = saida[:MAX_CONTENT_LENGTH] + "\n\n[...saída truncada...]"
        return saida or "Nenhuma saída."