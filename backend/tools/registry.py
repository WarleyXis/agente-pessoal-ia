# O registro é onde todas as ferramentas disponíveis ficam
# cadastradas. O Agent não conhece as ferramentas diretamente — ele
# pergunta ao registro "quais ferramentas existem?" e "execute a
# ferramenta X com esses argumentos".

from backend.tools.base import Tool
from backend.tools.system_tools import GetCurrentTimeTool, ListFilesTool
from backend.tools.vision_tools import DescribeScreenTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def schemas_for_llm(self) -> list[dict]:
        """
        Monta a lista de ferramentas no formato que os modelos de IA
        esperam para 'function calling' — um padrão usado tanto pelo
        Ollama quanto pela OpenAI, o que facilita trocar de provedor
        depois.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters_schema(),
                },
            }
            for tool in self._tools.values()
        ]


def build_default_registry() -> ToolRegistry:
    """Cria um registro já com as ferramentas padrão cadastradas."""
    registry = ToolRegistry()
    registry.register(GetCurrentTimeTool())
    registry.register(ListFilesTool())
    registry.register(DescribeScreenTool())
    
    return registry