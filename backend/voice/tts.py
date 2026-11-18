"""Synthesize the configured local Piper voice."""

from io import BytesIO
from pathlib import Path
from threading import Lock
import wave

from backend.core.config import settings

_voice_lock = Lock()
_loaded_voice = None
_loaded_path: Path | None = None


def synthesize_wav(text: str) -> bytes:
    from piper import PiperVoice

    path = Path(settings.piper_voice).expanduser().resolve()
    if not path.is_file() or not path.with_suffix(".onnx.json").is_file():
        raise FileNotFoundError("Arquivos da voz Piper ausentes.")

    global _loaded_voice, _loaded_path
    with _voice_lock:
        if _loaded_voice is None or _loaded_path != path:
            _loaded_voice = PiperVoice.load(path)
            _loaded_path = path
        audio = BytesIO()
        with wave.open(audio, "wb") as output:
            _loaded_voice.synthesize_wav(text, output)
        return audio.getvalue()


def speak(text: str) -> None:
    import winsound

    winsound.PlaySound(synthesize_wav(text), winsound.SND_MEMORY)
