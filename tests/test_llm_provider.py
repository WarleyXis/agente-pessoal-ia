# Testamos só se o OllamaProvider guarda corretamente as
# configurações recebidas — sem precisar do Ollama de verdade
# rodando, então o teste é rápido e não depende de rede.

from backend.core.llm_provider import OllamaProvider


def test_ollama_provider_stores_config():
    provider = OllamaProvider(model="llama3.2", base_url="http://localhost:11434")
    assert provider.model == "llama3.2"
    assert provider.base_url == "http://localhost:11434"


def test_qwen3_chat_sends_tools_without_extended_thinking(monkeypatch):
    from unittest.mock import Mock

    response = Mock()
    response.json.return_value = {"message": {"content": "Oi!"}}
    post = Mock(return_value=response)
    monkeypatch.setattr("backend.core.llm_provider.requests.post", post)
    provider = OllamaProvider("qwen3:4b", "http://localhost:11434")
    tools = [{"type": "function", "function": {"name": "consultar_hora"}}]
    assert provider.chat([{"role": "user", "content": "Oi!"}], tools)["content"] == "Oi!"
    assert post.call_args.kwargs["json"]["think"] is False
    assert post.call_args.kwargs["json"]["tools"] == tools
