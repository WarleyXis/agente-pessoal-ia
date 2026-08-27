# Esta camada existe para que o resto do agente NUNCA precise saber
# se está conversando com o Ollama (local, grátis) ou com a OpenAI
# (paga, na nuvem) ou qualquer outro provedor no futuro.
#
# Agora com duas formas de conversar: chat() devolve a resposta
# inteira de uma vez (útil quando o modelo pode pedir uma ferramenta,
# o que precisa da resposta completa para funcionar direito), e
# chat_stream() devolve pedaços de texto conforme são gerados —
# o mesmo efeito visual do ChatGPT "digitando" a resposta.

import json
from abc import ABC, abstractmethod
from typing import Iterator

import requests

from backend.core.config import settings


class LLMProvider(ABC):
    """Interface que todo provedor de modelo de linguagem precisa seguir."""

    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Manda a conversa e devolve a resposta completa de uma vez."""
        raise NotImplementedError

    @abstractmethod
    def chat_stream(self, messages: list[dict]) -> Iterator[str]:
        """
        Manda a conversa e devolve pedaços de texto conforme são
        gerados. Não aceita 'tools' — streaming com chamada de
        ferramenta ao mesmo tempo é mais complexo e fica para uma
        fase futura de polimento.
        """
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    """Provedor que conversa com um modelo rodando localmente via Ollama."""

    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        payload = {"model": self.model, "messages": messages, "stream": False}
        if tools:
            payload["tools"] = tools

        response = requests.post(
            f"{self.base_url}/api/chat", json=payload, timeout=120
        )
        response.raise_for_status()
        return response.json()["message"]

    def chat_stream(self, messages: list[dict]) -> Iterator[str]:
        payload = {"model": self.model, "messages": messages, "stream": True}

        with requests.post(
            f"{self.base_url}/api/chat", json=payload, stream=True, timeout=120
        ) as response:
            response.raise_for_status()
            # Cada linha da resposta é um pedaço de JSON separado —
            # o Ollama manda um objeto por linha em vez de um só no final.
            for line in response.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content


def get_llm_provider() -> LLMProvider:
    """'Fábrica' que decide qual provedor usar, baseado na configuração."""
    if settings.llm_provider == "ollama":
        return OllamaProvider(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )

    raise ValueError(f"Provedor de LLM desconhecido: {settings.llm_provider}")