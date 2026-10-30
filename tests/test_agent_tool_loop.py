# Testamos o loop de ferramentas do Agent com um LLMProvider "falso"
# (fake), sem precisar do Ollama de verdade — isso torna o teste
# rápido, determinístico, e independente de rede.

from backend.core.agent import Agent
from backend.core.llm_provider import LLMProvider
from backend.memory import store as memory_store
from backend.tools.registry import build_default_registry


class FakeLLMProvider(LLMProvider):
    """Devolve respostas pré-programadas em sequência, uma por chamada."""

    def __init__(self, respostas: list[dict]) -> None:
        self.respostas = respostas
        self.chamadas = 0

    def chat(self, messages, tools=None):
        resposta = self.respostas[self.chamadas]
        self.chamadas += 1
        return resposta

    def chat_stream(self, messages):
        yield "não usado neste teste"


def test_agent_calls_tool_then_answers(tmp_path, monkeypatch):
    monkeypatch.setattr(memory_store, "DB_PATH", tmp_path / "test_memory.db")

    fake_provider = FakeLLMProvider([
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"function": {"name": "get_current_time", "arguments": {}}}
            ],
        },
        {"role": "assistant", "content": "Já sei que horas são!"},
    ])

    agent = Agent(llm_provider=fake_provider, tool_registry=build_default_registry())
    resposta = agent.respond("que horas são?")

    assert resposta == "Já sei que horas são!"
    assert fake_provider.chamadas == 2


def test_agent_tool_loop_has_safety_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(memory_store, "DB_PATH", tmp_path / "test_memory.db")

    # Sempre pede a mesma ferramenta, nunca "se dá por satisfeito" —
    # simula um modelo preso em loop.
    sempre_pede_ferramenta = {
        "role": "assistant",
        "content": "",
        "tool_calls": [{"function": {"name": "get_current_time", "arguments": {}}}],
    }
    resposta_final = {"role": "assistant", "content": "Ok, parei por aqui."}

    respostas = [sempre_pede_ferramenta] * Agent.MAX_TOOL_ITERATIONS + [resposta_final]
    fake_provider = FakeLLMProvider(respostas)

    agent = Agent(llm_provider=fake_provider, tool_registry=build_default_registry())
    resposta = agent.respond("faça algo repetidamente")

    assert resposta == "Ok, parei por aqui."
    assert fake_provider.chamadas == Agent.MAX_TOOL_ITERATIONS + 1
    