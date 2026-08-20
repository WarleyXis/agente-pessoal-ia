# Testamos só se o OllamaProvider guarda corretamente as
# configurações recebidas — sem precisar do Ollama de verdade
# rodando, então o teste é rápido e não depende de rede.

from backend.core.llm_provider import OllamaProvider


def test_ollama_provider_stores_config():
    provider = OllamaProvider(model="llama3.2", base_url="http://localhost:11434")
    assert provider.model == "llama3.2"
    assert provider.base_url == "http://localhost:11434"
    