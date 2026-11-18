"""Local Portuguese speech recognition."""

import av
import numpy as np
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model


def decode_recording(filepath: str) -> np.ndarray:
    resampler = av.AudioResampler(format="fltp", layout="mono", rate=SAMPLE_RATE)
    chunks = []
    try:
        # Decode explicitly because faster-whisper passes a keyword that some
        # PyAV builds do not accept. Whisper also accepts PCM samples directly.
        with av.open(filepath, mode="r") as container:
            if not container.streams.audio:
                raise ValueError("A gravação não tem uma faixa de áudio.")
            for frame in container.decode(audio=0):
                chunks.extend(part.to_ndarray().reshape(-1) for part in resampler.resample(frame))
            if chunks:
                chunks.extend(part.to_ndarray().reshape(-1) for part in resampler.resample(None))
    except av.FFmpegError as error:
        raise ValueError("A gravação não pôde ser decodificada.") from error
    return np.concatenate(chunks) if chunks else np.empty(0, dtype=np.float32)


def transcribe_audio(filepath: str) -> str:
    samples = decode_recording(filepath)
    if not samples.size:
        return ""
    segments, _ = _get_model().transcribe(samples, language="pt", vad_filter=True)
    return " ".join(segment.text for segment in segments).strip()
