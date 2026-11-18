from unittest.mock import Mock

import requests
from fastapi.testclient import TestClient

from backend.api.app import app
from backend.memory import store


def test_chat_approval_is_single_use(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "atlas.db")
    with TestClient(app) as client:
        model = Mock()
        model.chat.side_effect = [
            {"role": "assistant", "tool_calls": [
                {"function": {"name": "open_application", "arguments": {"app_name": "calculadora"}}}
            ]},
            {"content": "A ação foi recusada."},
        ]
        app.state.agent.llm_provider = model
        execute = Mock()
        monkeypatch.setattr(app.state.agent.tool_registry.get("open_application"), "execute", execute)

        response = client.post("/api/chat", json={"message": "Abra a calculadora"})
        assert response.status_code == 200
        approval = response.json()["approval"]
        assert approval["arguments"] == {"app_name": "calculadora"}
        assert client.post(f"/api/approvals/{approval['id']}", json={"approved": False}).status_code == 200
        assert client.post(f"/api/approvals/{approval['id']}", json={"approved": True}).status_code == 404
        execute.assert_not_called()


def test_chat_reports_unavailable_model(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "atlas.db")
    with TestClient(app) as client:
        monkeypatch.setattr(app.state.agent.llm_provider, "chat", Mock(side_effect=requests.ConnectionError))
        response = client.post("/api/chat", json={"message": "Olá"})
    assert response.status_code == 502
    assert "Ollama" in response.json()["detail"]


def test_invalid_tool_arguments_do_not_execute(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "atlas.db")
    with TestClient(app) as client:
        model = Mock()
        model.chat.side_effect = [
            {"role": "assistant", "tool_calls": [
                {"function": {"name": "get_current_time", "arguments": "incompleto"}}
            ]},
            {"content": "Argumentos inválidos."},
        ]
        app.state.agent.llm_provider = model
        tool = app.state.agent.tool_registry.get("get_current_time")
        execute = Mock()
        monkeypatch.setattr(tool, "execute", execute)
        assert client.post("/api/chat", json={"message": "Que horas são?"}).status_code == 200
        assert "inválidos" in model.chat.call_args.args[0][-1]["content"]
        execute.assert_not_called()


def test_chat_shows_original_ollama_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "atlas.db")
    ollama = requests.Response()
    ollama.status_code = 500
    ollama._content = b'{"error":"model requires more system memory than is available"}'
    monkeypatch.setattr("backend.core.llm_provider.requests.post", Mock(return_value=ollama))
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "Oi"})
    assert response.status_code == 502
    assert "HTTP 500" in response.json()["detail"]
    assert "more system memory" in response.json()["detail"]


def test_chat_reports_missing_configured_model(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "atlas.db")
    monkeypatch.setattr("backend.core.config.settings.ollama_model", "qwen3:4b")
    ollama = requests.Response()
    ollama.status_code = 404
    ollama._content = b'{"error":"model qwen3:4b not found"}'
    monkeypatch.setattr("backend.core.llm_provider.requests.post", Mock(return_value=ollama))
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "Oi"})
    assert response.status_code == 502
    assert "ollama pull qwen3:4b" in response.json()["detail"]


def test_chat_does_not_mislabel_atlas_failure_as_missing_model(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "atlas.db")
    with TestClient(app) as client:
        monkeypatch.setattr(app.state.agent.llm_provider, "chat", Mock(side_effect=TypeError))
        response = client.post("/api/chat", json={"message": "Oi"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Erro interno no Atlas (TypeError)."


def test_spoken_chat_requests_shorter_answers_and_uses_recent_context(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "atlas.db")
    with TestClient(app) as client:
        for number in range(6):
            store.save_turn(f"Pergunta {number}", f"Resposta {number}")
        model = Mock()
        model.chat.return_value = {"content": "Tudo pronto."}
        app.state.agent.llm_provider = model

        result = client.post("/api/chat", json={"message": "Oi", "spoken": True})
        assert result.json() == {"response": "Tudo pronto."}
        messages = model.chat.call_args.args[0]
        assert "uma ou duas frases curtas" in messages[0]["content"]
        assert len(messages) == 10
        assert messages[1]["content"] == "Pergunta 2"

        client.post("/api/chat", json={"message": "Oi novamente"})
        messages = model.chat.call_args.args[0]
        assert "uma ou duas frases curtas" not in messages[0]["content"]
        assert messages[1]["content"] == "Pergunta 0"
