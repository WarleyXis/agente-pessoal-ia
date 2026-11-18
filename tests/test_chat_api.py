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
