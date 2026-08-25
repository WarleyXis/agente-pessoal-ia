# Grava áudio do microfone por um tempo fixo e salva num arquivo
# .wav — o formato que o Whisper (nosso transcritor) espera receber.

from pathlib import Path

import numpy as np
import sounddevice as sd
import wave

SAMPLE_RATE = 16000  # 16kHz é o que o Whisper espera como entrada
RECORDING_PATH = Path("data") / "gravacao.wav"


def record_audio(duration_seconds: int) -> str:
    """Grava do microfone por 'duration_seconds' e devolve o caminho do arquivo salvo."""
    RECORDING_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"🎙️  Gravando por {duration_seconds}s — fale agora!")
    audio = sd.rec(
        int(duration_seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    sd.wait()  # espera a gravação terminar antes de continuar
    print("Gravação concluída.")

    # O microfone grava em float32 (-1.0 a 1.0), mas o formato WAV
    # padrão usa inteiros de 16 bits — convertemos aqui.
    audio_int16 = (audio * 32767).astype(np.int16)

    with wave.open(str(RECORDING_PATH), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 2 bytes = 16 bits
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(audio_int16.tobytes())

    return str(RECORDING_PATH)
