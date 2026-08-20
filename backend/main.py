# Este é o "botão de ligar" do agente — agora com um loop de chat
# de verdade: você digita, o agente responde, repete até você sair.

import logging

from backend.core.agent import Agent
from backend.core.config import settings


def setup_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger(settings.agent_name)
    logger.info("Inicializando %s...", settings.agent_name)

    agent = Agent()

    print(f"\n{settings.agent_name} está online. Digite 'sair' para encerrar.\n")

    # Loop infinito: só termina quando o usuário digitar "sair"
    while True:
        user_message = input("Você: ").strip()

        if user_message.lower() in {"sair", "exit", "quit"}:
            print(f"{settings.agent_name}: Até logo!")
            break

        if not user_message:
            continue

        resposta = agent.respond(user_message)
        print(f"{settings.agent_name}: {resposta}\n")


if __name__ == "__main__":
    main()