# O Agent agora tem memória: lembra das mensagens anteriores dentro
# da mesma execução (memória de curto prazo) e também carrega o
# histórico salvo em disco ao iniciar, então a conversa continua de
# onde parou mesmo depois de fechar e abrir o programa de novo
# (memória entre sessões).

import json

from backend.core.config import settings
from backend.core.llm_provider import LLMProvider, get_llm_provider
from backend.core.security import ask_approval, requires_approval
from backend.memory import store as memory_store
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

        memory_store.init_db()
        # Carrega as últimas mensagens salvas como ponto de partida
        # da conversa — é assim que o agente "lembra" de sessões
        # anteriores.
        self.history: list[dict] = memory_store.load_recent_history()

    def respond(self, user_message: str) -> str:
        system_prompt = (
            f"Você é {settings.agent_name}, um assistente pessoal direto "
            f"e prestativo. Responda sempre em português. Use as "
            f"ferramentas disponíveis quando forem úteis para responder "
            f"com precisão. Você tem acesso ao histórico da conversa "
            f"abaixo — use-o para lembrar do que já foi dito."
        )

        messages = (
            [{"role": "system", "content": system_prompt}]
            + self.history
            + [{"role": "user", "content": user_message}]
        )

        message = self.llm_provider.chat(
            messages, tools=self.tool_registry.schemas_for_llm()
        )

        tool_calls = message.get("tool_calls")

        if not tool_calls:
            final_text = message.get("content", "")
        else:
            messages.append(message)

            for call in tool_calls:
                tool_name = call["function"]["name"]
                arguments = call["function"]["arguments"]

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

            final_message = self.llm_provider.chat(messages)
            final_text = final_message.get("content", "")

        # Guarda só a pergunta e a resposta final no histórico — não
        # os detalhes intermediários de chamada de ferramenta, que
        # não interessam para a continuidade da conversa.
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": final_text})

        # Mantém o histórico em memória de um tamanho razoável, para
        # não estourar o limite de contexto do modelo numa sessão
        # muito longa.
        self.history = self.history[-memory_store.MAX_HISTORY_MESSAGES :]

        memory_store.save_message("user", user_message)
        memory_store.save_message("assistant", final_text)

        return final_text