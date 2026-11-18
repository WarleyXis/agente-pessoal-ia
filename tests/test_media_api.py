from io import BytesIO
from unittest.mock import Mock

from fastapi.testclient import TestClient
from PIL import Image

from backend.api import media
from backend.api.app import app
from backend.memory import store


def test_transcription_uses_supported_audio_and_rejects_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "atlas.db")
    transcribe = Mock(return_value="Olá, Atlas")
    monkeypatch.setattr(media, "transcribe", transcribe)
    with TestClient(app) as client:
        headers = {"Content-Type": "audio/webm;codecs=opus"}
        response = client.post("/api/transcribe", content=b"sample", headers=headers)
        assert response.json() == {"text": "Olá, Atlas"}
        assert client.post("/api/transcribe", content=b"", headers=headers).status_code == 422
    transcribe.assert_called_once_with(b"sample", "webm")


def test_vision_validates_png_and_records_description(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "atlas.db")
    describe = Mock(return_value="Janela de teste")
    monkeypatch.setattr(media, "describe_image", describe)
    image = BytesIO()
    Image.new("RGB", (5, 5)).save(image, format="PNG")
    with TestClient(app) as client:
        headers = {"Content-Type": "image/png"}
        url = "/api/vision?question=O%20que%20aparece%3F"
        assert client.post(url, content=b"bad", headers=headers).status_code == 422
        assert client.post(url, content=image.getvalue(), headers=headers).json() == {"response": "Janela de teste"}
    describe.assert_called_once_with(image.getvalue(), "O que aparece?")
    assert store.load_recent_history()[-1]["content"] == "Janela de teste"
