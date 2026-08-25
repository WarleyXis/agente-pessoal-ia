# TTS = Text-To-Speech (texto para fala). Usa o motor de voz já
# embutido no Windows (via pyttsx3) — grátis e offline, mas com
# qualidade mais robótica que serviços pagos. Dá pra trocar por algo
# melhor depois, sem mudar quem usa essa função.

import pyttsx3


def speak(text: str) -> None:
    """Fala o texto em voz alta usando o motor de voz do sistema."""
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()