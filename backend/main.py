# Este é o "botão de ligar" do agente.
# Por enquanto ele só confirma que a configuração está funcionando —
# nas próximas fases, é aqui que o agente vai começar a de fato
# processar mensagens.

import logging

# Importa a configuração já carregada do config.py
from backend.core.config import settings


def setup_logging() -> None:
    """
    Configura como as mensagens de log vão aparecer no terminal.

    logging.basicConfig prepara o sistema de logs padrão do Python
    para usar o nível (INFO, DEBUG, etc) definido em settings.log_level
    e um formato que mostra data/hora, nível, nome do logger e mensagem.
    """
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


def main() -> None:
    """Ponto de entrada: roda quando executamos `python -m backend.main`."""
    setup_logging()

    # Cria um "logger" com o nome do agente — assim, se no futuro
    # tivermos vários módulos logando coisas, dá pra saber de onde
    # cada mensagem veio.
    logger = logging.getLogger(settings.agent_name)

    logger.info("Inicializando %s...", settings.agent_name)
    print(f"\n{settings.agent_name} está online.\n")


# Esse "if" é um padrão do Python: o código dentro dele só roda
# quando este arquivo é executado diretamente (não quando é
# importado por outro arquivo).
if __name__ == "__main__":
    main()