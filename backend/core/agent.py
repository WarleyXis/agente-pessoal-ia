# O Agent é o "cérebro" do sistema: por enquanto ele só recebe uma
# mensagem do usuário e devolve a resposta do modelo de linguagem.
# Nas próximas fases, ele vai ganhar acesso a ferramentas e memória
# — mas a ideia central (receber, processar, responder) já nasce
# aqui.

from backend.core.config import settings
from backend.core.llm_provider import LLMProvider, get_llm_provider


class Agent:
    """Orquestrador central do agente pessoal."""

    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        # Se ninguém passar um provider específico, usa o padrão
        # definido na configuração, através da fábrica get_llm_provider().
        self.llm_provider = llm_provider or get_llm_provider()

    def respond(self, user_message: str) -> str:
        """
        Monta o prompt final (com uma instrução simples de
        personalidade) e pede ao provedor de LLM para gerar a resposta.
        """
        prompt = (
            f"Você é {settings.agent_name}, um assistente pessoal "
            f"direto e prestativo. Responda em português.\n\n"
            f"Usuário: {user_message}\n{settings.agent_name}:"
        )
        return self.llm_provider.generate(prompt)