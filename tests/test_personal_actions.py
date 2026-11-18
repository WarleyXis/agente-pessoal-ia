import socket
from unittest.mock import Mock

from fastapi.testclient import TestClient

from backend.api.app import app
from backend.core.config import settings
from backend.memory import store
from backend.tools.browser_tools import OpenUrlTool


def prepare(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "atlas.db")
    monkeypatch.setattr(settings, "notes_directory", str(tmp_path / "notes"))


def request_note(client, filename="Agenda.md", content="Primeira linha", mode="create"):
    response = client.post("/api/actions", json={
        "tool": "save_note",
        "arguments": {"filename": filename, "content": content, "mode": mode},
    })
    assert response.status_code == 200
    return response.json()


def decide(client, request, approved):
    return client.post(f"/api/approvals/{request['approval']['id']}", json={"approved": approved})


def test_note_requires_single_approval_and_preserves_existing_text(tmp_path, monkeypatch):
    prepare(tmp_path, monkeypatch)
    path = tmp_path / "notes" / "Agenda.md"
    with TestClient(app) as client:
        declined = request_note(client)
        assert declined["approval"]["arguments"]["path"] == str(path)
        assert not path.exists()
        assert decide(client, declined, False).status_code == 200
        assert not path.exists()

        new = request_note(client)
        assert decide(client, new, True).status_code == 200
        assert path.read_text(encoding="utf-8") == "Primeira linha"
        assert decide(client, new, True).status_code == 404

        assert "já existe" in decide(client, request_note(client, content="Substituição"), True).json()["response"]
        assert path.read_text(encoding="utf-8") == "Primeira linha"
        change = request_note(client, content="Segunda linha", mode="append")
        assert decide(client, change, True).status_code == 200
        assert path.read_text(encoding="utf-8") == "Primeira linha\nSegunda linha"


def test_note_rejects_invalid_paths_and_preserves_external_file(tmp_path, monkeypatch):
    prepare(tmp_path, monkeypatch)
    with TestClient(app) as client:
        assert "inválidos" in request_note(client, filename="../Externo.md")["response"]
        assert "nome simples" in request_note(client, filename="NUL.txt")["response"]
        assert not (tmp_path / "Externo.md").exists()


def test_web_access_starts_only_after_approval(tmp_path, monkeypatch):
    prepare(tmp_path, monkeypatch)
    monkeypatch.setattr(settings, "web_hosts", "docs.python.org")
    lookup = Mock(return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("151.101.0.223", 443))])
    read_page = Mock(return_value="Fonte: https://docs.python.org/3/")
    monkeypatch.setattr(socket, "getaddrinfo", lookup)
    monkeypatch.setattr(OpenUrlTool, "read_page", staticmethod(read_page))
    with TestClient(app) as client:
        def page(url):
            return client.post("/api/actions", json={"tool": "open_url", "arguments": {"url": url}}).json()

        assert "domínio cadastrado" in page("https://127.0.0.1")["response"]
        assert decide(client, page("docs.python.org/3/"), False).status_code == 200
        lookup.assert_not_called()
        assert "Fonte:" in decide(client, page("docs.python.org/3/"), True).json()["response"]
        read_page.assert_called_once_with("https://docs.python.org/3/")

        lookup.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        assert "endereço público" in decide(client, page("docs.python.org/3/"), True).json()["response"]
        read_page.assert_called_once()


def test_web_extracts_text_without_running_page_scripts(monkeypatch):
    response = Mock(status_code=200, headers={"Content-Type": "text/html"}, encoding="utf-8")
    response.iter_content.return_value = [b"<style>hidden</style><p>Texto da fonte</p><script>hidden</script>"]
    session = Mock()
    session.get.return_value.__enter__ = Mock(return_value=response)
    session.get.return_value.__exit__ = Mock()
    manager = Mock()
    manager.__enter__ = Mock(return_value=session)
    manager.__exit__ = Mock()
    monkeypatch.setattr("backend.tools.browser_tools.requests.Session", lambda: manager)

    result = OpenUrlTool.read_page("https://docs.python.org/3/")
    assert result == "Fonte: https://docs.python.org/3/\n\nTexto da fonte"
    assert session.get.call_args.kwargs["allow_redirects"] is False
