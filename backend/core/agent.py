# O Agent sabe usar ferramentas e tem memória. A partir desta fase,
# ganha também uma versão "streaming" da resposta — útil para o modo
# de voz, onde queremos mostrar o texto aparecendo progressivamente.

import json
from typing import Iterator

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
        self.history: list[dict] = memory_store.load_recent_history()

    def _build_base_messages(self, user_message: str) -> list[dict]:
        """Monta o histórico + mensagem atual, prontos para mandar ao modelo."""
        system_prompt = (
            f"Você é {settings.agent_name}, um assistente pessoal direto "
            f"e prestativo. Responda sempre em português. Use as "
            f"ferramentas disponíveis quando forem úteis para responder "
            f"com precisão. Você tem acesso ao histórico da conversa "
            f"abaixo — use-o para lembrar do que já foi dito.\n\n"
            f"Quando uma ferramenta devolver um resultado (incluindo "
            f"descrições visuais da tela do usuário), trate essa "
            f"informação como algo que você observou diretamente e "
            f"responda com base nela. Nunca negue ter acesso a uma "
            f"informação depois que uma ferramenta já a forneceu."
        )
        
        return (
            [{"role": "system", "content": system_prompt}]
            + self.history
            + [{"role": "user", "content": user_message}]
        )

    def _resolve_tool_calls(
        self, messages: list[dict], initial_message: dict
    ) -> tuple[list[dict], bool]:
        """
        Recebe a primeira resposta do modelo. Se ela pedir ferramentas,
        executa cada uma (respeitando aprovação de risco) e adiciona
        os resultados ao histórico de mensagens.

        Devolve as mensagens atualizadas e um booleano indicando se
        ainda é necessária uma chamada final ao modelo (True quando
        ferramentas foram usadas).
        """
        tool_calls = initial_message.get("tool_calls")
        if not tool_calls:
            return messages, False

        messages.append(initial_message)

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
            messages.append({"role": "tool", "name": tool_name, "content": result})

        return messages, True

    def _save_turn(self, user_message: str, final_text: str) -> None:
        """Salva a troca (pergunta + resposta) na memória de curto e longo prazo."""
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": final_text})
        self.history = self.history[-memory_store.MAX_HISTORY_MESSAGES:]

        memory_store.save_message("user", user_message)
        memory_store.save_message("assistant", final_text)

    def respond(self, user_message: str) -> str:
        """Resposta completa de uma vez (usada pelo terminal em texto e pela API)."""
        messages = self._build_base_messages(user_message)
        initial_message = self.llm_provider.chat(
            messages, tools=self.tool_registry.schemas_for_llm()
        )
        messages, needs_final_call = self._resolve_tool_calls(messages, initial_message)

        if needs_final_call:
            final_message = self.llm_provider.chat(messages)
            final_text = final_message.get("content", "")
        else:
            final_text = initial_message.get("content", "")

        self._save_turn(user_message, final_text)
        return final_text

    def respond_stream(self, user_message: str) -> Iterator[str]:
        """Mesma lógica, mas devolve a resposta final em pedaços (usada pelo modo de voz)."""
        messages = self._build_base_messages(user_message)
        initial_message = self.llm_provider.chat(
            messages, tools=self.tool_registry.schemas_for_llm()
        )
        messages, needs_final_call = self._resolve_tool_calls(messages, initial_message)

        full_text = ""
        if needs_final_call:
            for chunk in self.llm_provider.chat_stream(messages):
                full_text += chunk
                yield chunk
        else:
            full_text = initial_message.get("content", "")
            yield full_text

        self._save_turn(user_message, full_text)