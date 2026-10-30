# O Agent sabe usar ferramentas, tem memória, e agora consegue
# encadear VÁRIAS rodadas de ferramenta numa mesma tarefa (até um
# limite de segurança) — em vez de só uma decisão por mensagem.
# Isso é o que permite tarefas como "leia o arquivo X e depois rode
# os testes", sem precisar de um plano escrito antes.

import json
from typing import Iterator

from backend.core.config import settings
from backend.core.llm_provider import LLMProvider, get_llm_provider
from backend.core.security import ask_approval, requires_approval
from backend.core.tool_router import relevant_domains
from backend.memory import store as memory_store
from backend.tools.registry import ToolRegistry, build_default_registry


class Agent:
    """Orquestrador central do agente pessoal."""

    # Quantas rodadas de "pedir ferramenta -> executar -> ver resultado"
    # o agente pode encadear numa mesma tarefa, antes de ser forçado a
    # responder de qualquer jeito. Evita loops infinitos.
    MAX_TOOL_ITERATIONS = 5

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

    def _execute_tool_call(self, call: dict) -> tuple[str, str]:
        """Executa uma única chamada de ferramenta e devolve (nome, resultado)."""
        tool_name = call["function"]["name"]
        arguments = call["function"]["arguments"]
        if isinstance(arguments, str):
            arguments = json.loads(arguments)

        print(f"🔧 Executando: {tool_name}({arguments})")

        tool = self.tool_registry.get(tool_name)
        if tool is None:
            return tool_name, f"Ferramenta desconhecida: {tool_name}"

        if requires_approval(tool.risk_level) and not ask_approval(tool_name, arguments):
            return tool_name, "Ação não autorizada pelo usuário."

        return tool_name, tool.execute(**arguments)

    def _run_tool_loop(
        self, messages: list[dict], domains: set[str] | None
    ) -> tuple[list[dict], dict | None]:
        """
        Executa rodadas de decisão de ferramenta enquanto o modelo
        continuar pedindo — até ele parar de pedir (retorno normal)
        ou até MAX_TOOL_ITERATIONS (retorno None, sinalizando que
        ainda falta uma chamada final para gerar a resposta).
        """
        tools_schema = self.tool_registry.schemas_for_llm(domains)

        for _ in range(self.MAX_TOOL_ITERATIONS):
            message = self.llm_provider.chat(messages, tools=tools_schema)
            tool_calls = message.get("tool_calls")

            if not tool_calls:
                return messages, message

            messages.append(message)
            for call in tool_calls:
                tool_name, result = self._execute_tool_call(call)
                messages.append({"role": "tool", "name": tool_name, "content": result})
        else:
            # Excedeu o limite de segurança sem o modelo se dar por
            # satisfeito — quem chamou este método precisa fazer uma
            # última chamada, sem ferramentas, para forçar uma resposta.
            return messages, None

    def _save_turn(self, user_message: str, final_text: str) -> None:
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": final_text})
        self.history = self.history[-memory_store.MAX_HISTORY_MESSAGES:]

        memory_store.save_message("user", user_message)
        memory_store.save_message("assistant", final_text)

    def respond(self, user_message: str) -> str:
        """Resposta completa de uma vez (usada pelo terminal em texto e pela API)."""
        messages = self._build_base_messages(user_message)
        domains = relevant_domains(user_message)
        messages, last_message = self._run_tool_loop(messages, domains)

        if last_message is not None:
            final_text = last_message.get("content", "")
        else:
            final_message = self.llm_provider.chat(messages)
            final_text = final_message.get("content", "")

        self._save_turn(user_message, final_text)
        return final_text

    def respond_stream(self, user_message: str) -> Iterator[str]:
        """Mesma lógica, mas devolve a resposta final em pedaços (usada pelo modo de voz)."""
        messages = self._build_base_messages(user_message)
        domains = relevant_domains(user_message)
        messages, last_message = self._run_tool_loop(messages, domains)

        full_text = ""
        if last_message is not None:
            full_text = last_message.get("content", "")
            yield full_text
        else:
            for chunk in self.llm_provider.chat_stream(messages):
                full_text += chunk
                yield chunk

        self._save_turn(user_message, full_text)