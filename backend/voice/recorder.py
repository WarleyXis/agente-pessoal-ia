# Grava do microfone continuamente, mas para sozinho quando detecta
# silêncio — medindo o volume (RMS, "root mean square") de cada
# pedaço de áudio, em vez de usar uma biblioteca externa de detecção
# de fala. É uma técnica mais simples (não distingue fala de outros
# ruídos altos), mas não depende de nenhuma compilação C, o que a
# torna muito mais fácil de instalar.

from pathlib import Path

import numpy as np
import sounddevice as sd
import wave

SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_MS / 1000)

# Volume mínimo (escala 0.0 a 1.0) para considerar que há fala.
# Se o silêncio não for detectado, diminua este valor; se parar
# cedo demais, aumente.
SPEECH_THRESHOLD = 0.02

SILENCE_LIMIT_MS = 1200
MAX_RECORDING_MS = 30000

RECORDING_PATH = Path("data") / "gravacao.wav"


def _rms(frame: np.ndarray) -> float:
    """Calcula o volume médio de um pedaço de áudio (0.0 = silêncio total)."""
    return float(np.sqrt(np.mean(frame.astype(np.float64) ** 2)) / 32768)


def record_until_silence() -> str:
    """
    Grava do microfone até detectar silêncio contínuo (ou até o
    limite máximo de segurança) e devolve o caminho do arquivo salvo.
    """
    frames: list[np.ndarray] = []
    silent_ms = 0
    started_talking = False
    total_ms = 0

    print("🎙️  Ouvindo... fale quando quiser (para sozinho no silêncio).")

    with sd.InputStream(
        samplerate=SAMPLE_RATE, blocksize=FRAME_SAMPLES, dtype="int16", channels=1
    ) as stream:
        while total_ms < MAX_RECORDING_MS:
            frame, _ = stream.read(FRAME_SAMPLES)
            frames.append(frame.copy())
            total_ms += FRAME_MS

            volume = _rms(frame)

            if volume > SPEECH_THRESHOLD:
                started_talking = True
                silent_ms = 0
            elif started_talking:
                silent_ms += FRAME_MS
                if silent_ms >= SILENCE_LIMIT_MS:
                    break

    print("Gravação concluída.")

    audio = np.concatenate(frames)

    RECORDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(RECORDING_PATH), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(audio.tobytes())

    return str(RECORDING_PATH)