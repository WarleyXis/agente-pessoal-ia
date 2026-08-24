# O Agent agora sabe usar ferramentas: ele manda a conversa pro
# modelo, e se o modelo pedir para executar uma ferramenta, o Agent
# verifica o risco, pede sua aprovação se necessário, executa, e
# devolve o resultado pro modelo — que só então formula a resposta
# final em texto.

import json

from backend.core.config import settings
from backend.core.llm_provider import LLMProvider, get_llm_provider
from backend.core.security import ask_approval, requires_approval
from backend.tools.registry import ToolRegistry, build_default_registry


class Agent:
    """Orquestrador central do agente pessoal."""

    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.llm_provider = llm_provider or get_llm_provider()
        self.tool_registry = tool_registry or build_default_registry()

    def respond(self, user_message: str) -> str:
        system_prompt = (
            f"Você é {settings.agent_name}, um assistente pessoal direto "
            f"e prestativo. Responda sempre em português. Use as "
            f"ferramentas disponíveis quando forem úteis para responder "
            f"com precisão."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # Primeira chamada: o modelo decide se responde direto ou
        # pede para usar uma ferramenta.
        message = self.llm_provider.chat(
            messages, tools=self.tool_registry.schemas_for_llm()
        )

        tool_calls = message.get("tool_calls")

        if not tool_calls:
            # Nenhuma ferramenta necessária — resposta direta.
            return message.get("content", "")

        # Guarda a resposta do modelo (pedindo a ferramenta) no
        # histórico, e adiciona o resultado de cada ferramenta chamada.
        messages.append(message)

        for call in tool_calls:
            tool_name = call["function"]["name"]
            arguments = call["function"]["arguments"]

            # Alguns modelos devolvem os argumentos como texto JSON
            # em vez de já vir como dicionário — tratamos os dois casos.
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            tool = self.tool_registry.get(tool_name)
            if tool is None:
                result = f"Ferramenta desconhecida: {tool_name}"
            elif requires_approval(tool.risk_level) and not ask_approval(
                tool_name, arguments
            ):
                result = "Ação não autorizada pelo usuário."
            else:
                result = tool.execute(**arguments)

            messages.append({"role": "tool", "content": result})

        # Segunda chamada: agora o modelo já tem o resultado da
        # ferramenta e pode formular a resposta final em texto.
        final_message = self.llm_provider.chat(messages)
        return final_message.get("content", "")