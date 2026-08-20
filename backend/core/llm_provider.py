# Esta camada existe para que o resto do agente NUNCA precise saber
# se está conversando com o Ollama (local, grátis) ou com a OpenAI
# (paga, na nuvem) ou qualquer outro provedor no futuro.
#
# Todo provedor de LLM (Large Language Model) implementa a mesma
# "promessa": um método generate(prompt) que devolve uma resposta
# em texto. O resto do código só conhece essa promessa, não o
# provedor específico por trás dela.

from abc import ABC, abstractmethod

import requests

from backend.core.config import settings


class LLMProvider(ABC):
    """
    Interface (contrato) que todo provedor de modelo de linguagem
    precisa seguir. ABC = Abstract Base Class: uma classe que não
    pode ser usada diretamente, só serve de "molde" para outras.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Recebe um texto de entrada e devolve a resposta do modelo."""
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    """
    Provedor que conversa com um modelo rodando localmente via Ollama.

    O Ollama, depois de instalado, fica rodando em segundo plano
    como um servidor na sua própria máquina, escutando em
    http://localhost:11434. Nós apenas mandamos uma requisição HTTP
    pra ele, como se fosse um site.
    """

    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,  # queremos a resposta inteira de uma vez, não em pedaços
            },
            timeout=120,  # modelos locais podem demorar, principalmente na primeira chamada
        )
        response.raise_for_status()  # lança erro se o Ollama respondeu com problema
        return response.json()["response"]


def get_llm_provider() -> LLMProvider:
    """
    'Fábrica' que decide qual provedor usar, baseado na configuração.

    Hoje só existe Ollama. Quando adicionarmos OpenAI (fase futura),
    o único lugar que muda é aqui dentro — o resto do agente
    continua exatamente igual.
    """
    if settings.llm_provider == "ollama":
        return OllamaProvider(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )

    raise ValueError(f"Provedor de LLM desconhecido: {settings.llm_provider}")