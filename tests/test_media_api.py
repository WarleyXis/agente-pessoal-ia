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


def test_speech_returns_audio_and_reports_unavailable_voice(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "atlas.db")
    synthesize = Mock(side_effect=[b"RIFFsampleWAVE", FileNotFoundError("voice unavailable")])
    monkeypatch.setattr(media, "synthesize_wav", synthesize)
    with TestClient(app) as client:
        response = client.post("/api/speak", json={"text": "Olá, Warley"})
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert response.headers["cache-control"] == "no-store"
        assert response.content == b"RIFFsampleWAVE"
        assert client.post("/api/speak", json={"text": "Atlas"}).status_code == 503
        assert client.post("/api/speak", json={"text": ""}).status_code == 422
    assert synthesize.call_count == 2


def test_transcription_decodes_real_recording_before_calling_whisper(tmp_path, monkeypatch):
    import wave
    from types import SimpleNamespace

    import numpy as np

    from backend.voice import stt

    recording = BytesIO()
    waveform = np.tile(np.array([1000, 2000], dtype="<i2"), (4800, 1))
    with wave.open(recording, "wb") as output:
        output.setparams((2, 2, 48000, 0, "NONE", "not compressed"))
        output.writeframes(waveform.tobytes())

    model = Mock()
    model.transcribe.return_value = ([SimpleNamespace(text=" Teste de voz.")], None)
    monkeypatch.setattr(stt, "_get_model", lambda: model)
    path = tmp_path / "recording.wav"
    path.write_bytes(recording.getvalue())
    assert stt.transcribe_audio(str(path)) == "Teste de voz."
    args, kwargs = model.transcribe.call_args
    assert args[0].dtype == np.float32
    assert args[0].shape == (1600,)
    assert np.max(np.abs(args[0])) > 0.01
    assert kwargs == {"language": "pt", "vad_filter": True}


def test_speech_keeps_technical_material_in_the_panel(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "test.db")
    synthesize = Mock(return_value=b"RIFFsampleWAVE")
    monkeypatch.setattr(media, "synthesize_wav", synthesize)
    with TestClient(app) as client:
        response = client.post("/api/speak", json={"text": (
            "<analysis>I should consider the options carefully.</analysis>"
            "### Posso explicar essa parte.\n\n"
            "This paragraph is written entirely in English and can be read on the page.\n\n"
            "```python\nprint('hello')\n```\n\nFonte: https://example.test"
        )})
        assert response.status_code == 200
    synthesize.assert_called_once_with("Posso explicar essa parte.")
