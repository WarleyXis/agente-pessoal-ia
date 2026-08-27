# Modo de voz com escuta automática (para sozinha quando você para
# de falar) e resposta em streaming (o texto aparece progressivamente
# enquanto é gerado, antes de ser falado em voz alta).

import logging

from backend.core.agent import Agent
from backend.core.config import settings
from backend.voice.recorder import record_until_silence
from backend.voice.stt import transcribe_audio
from backend.voice.tts import speak


def setup_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


def main() -> None:
    setup_logging()
    agent = Agent()

    print(f"\n{settings.agent_name} está online (modo voz). Ctrl+C para encerrar.\n")

    while True:
        input("Pressione Enter para falar...")
        filepath = record_until_silence()

        print("Transcrevendo...")
        texto = transcribe_audio(filepath)
        print(f"Você disse: {texto}")

        if not texto.strip():
            print("Não entendi nada, tente de novo.\n")
            continue

        print(f"{settings.agent_name}: ", end="", flush=True)
        full_text = ""
        for chunk in agent.respond_stream(texto):
            print(chunk, end="", flush=True)
            full_text += chunk
        print("\n")

        speak(full_text)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEncerrado.")