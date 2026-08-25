# Uma versão do "botão de ligar" que conversa por voz em vez de
# texto: grava sua fala, transcreve, manda pro agente, e fala a
# resposta em voz alta. Ainda por tempo fixo de gravação — "escutar
# até você parar de falar" e interrupção em tempo real vêm na
# Fase 8 (Realtime).

import logging

from backend.core.agent import Agent
from backend.core.config import settings
from backend.voice.recorder import record_audio
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
        filepath = record_audio(duration_seconds=settings.voice_record_seconds)

        print("Transcrevendo...")
        texto = transcribe_audio(filepath)
        print(f"Você disse: {texto}")

        if not texto.strip():
            print("Não entendi nada, tente de novo.\n")
            continue

        resposta = agent.respond(texto)
        print(f"{settings.agent_name}: {resposta}\n")
        speak(resposta)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEncerrado.")