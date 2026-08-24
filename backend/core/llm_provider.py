# Esta camada existe para que o resto do agente NUNCA precise saber
# se está conversando com o Ollama (local, grátis) ou com a OpenAI
# (paga, na nuvem) ou qualquer outro provedor no futuro.
#
# Nesta fase, adicionamos suporte a "tools" (function calling): o
# modelo pode responder pedindo para executar uma ferramenta, em vez
# de só devolver texto. O formato é parecido entre Ollama e OpenAI,
# o que facilita trocar de provedor depois.

from abc import ABC, abstractmethod

import requests

from backend.core.config import settings


class LLMProvider(ABC):
    """Interface que todo provedor de modelo de linguagem precisa seguir."""

    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """
        Manda uma lista de mensagens (histórico da conversa) para o
        modelo e devolve a resposta dele. Se 'tools' for passado, o
        modelo pode escolher chamar uma ferramenta em vez de responder
        direto com texto.
        """
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    """Provedor que conversa com um modelo rodando localmente via Ollama."""

    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["message"]


def get_llm_provider() -> LLMProvider:
    """'Fábrica' que decide qual provedor usar, baseado na configuração."""
    if settings.llm_provider == "ollama":
        return OllamaProvider(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )

    raise ValueError(f"Provedor de LLM desconhecido: {settings.llm_provider}")