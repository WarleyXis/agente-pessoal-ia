# STT = Speech-To-Text (fala para texto). Usa o Whisper rodando
# localmente através do faster-whisper, sem depender de API paga.

from faster_whisper import WhisperModel

_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    """
    Carrega o modelo uma única vez (é pesado) e reaproveita depois.

    'base' é um bom equilíbrio entre velocidade e precisão para
    começar. 'device=cpu' e 'compute_type=int8' deixam ele leve o
    suficiente para rodar sem placa de vídeo dedicada.
    """
    global _model
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model


def transcribe_audio(filepath: str) -> str:
    """Transcreve um arquivo de áudio para texto em português."""
    model = _get_model()
    segments, _ = model.transcribe(filepath, language="pt")
    return " ".join(segment.text for segment in segments).strip()
