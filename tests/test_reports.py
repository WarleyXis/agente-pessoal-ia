import json
import sys
from unittest.mock import Mock

from fastapi.testclient import TestClient

from backend.api import reports
from backend.api.app import app
from backend.core.config import settings
from backend.memory import store


def configure(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "atlas.db")
    config = tmp_path / "projects.json"
    config.write_text(json.dumps({"Projeto de exemplo": {"path": str(tmp_path)}}), encoding="utf-8")
    monkeypatch.setattr(settings, "projects_file", str(config))


def test_report_persists_without_git_and_refusal_does_not_execute(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    command = Mock()
    monkeypatch.setattr(reports, "run_command", command)
    with TestClient(app) as client:
        report = client.post("/api/reports", json={"project": "Projeto de exemplo", "include_tests": True}).json()
        assert report["git"] == {"state": "no_git"}
        assert report["tests"]["state"] == "pending"
        report_url = f"/api/reports/{report['id']}/decision"
        assert client.post(report_url, json={"approved": False}).json()["tests"]["state"] == "declined"
        assert client.post(report_url, json={"approved": True}).status_code == 409
    with TestClient(app) as client:
        assert client.get("/api/reports").json()[0]["tests"]["state"] == "declined"
    command.assert_not_called()


def test_failed_tests_keep_exit_code_after_approval(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    command = Mock(return_value={"state": "failed", "exit_code": 1, "output": "1 failed"})
    monkeypatch.setattr(reports, "run_command", command)
    with TestClient(app) as client:
        report = client.post("/api/reports", json={"project": "Projeto de exemplo", "include_tests": True}).json()
        result = client.post(f"/api/reports/{report['id']}/decision", json={"approved": True}).json()
        assert result["tests"]["state"] == "failed"
        assert result["tests"]["exit_code"] == 1
    command.assert_called_once_with([sys.executable, "-m", "pytest", "-q"], tmp_path, 120)
