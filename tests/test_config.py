# Este arquivo contém testes automáticos: código que verifica se
# outro código está funcionando como esperado, sem você precisar
# testar manualmente toda vez.

from backend.core.config import Settings


def test_default_agent_name():
    """
    Confirma que, sem nenhuma variável de ambiente definida,
    o nome padrão do agente é 'JARVIS'.

    _env_file=None diz ao Pydantic: "não leia o .env real da
    minha máquina para este teste" — assim o teste sempre dá o
    mesmo resultado, não importa o que estiver no seu .env.
    """
    s = Settings(_env_file=None)
    assert s.agent_name == "JARVIS"


def test_agent_name_from_env(monkeypatch):
    """
    Confirma que, se a variável de ambiente AGENT_NAME existir,
    ela substitui o valor padrão.

    monkeypatch.setenv simula, só durante este teste, que existe
    uma variável AGENT_NAME com valor "ATLAS" — sem mexer no seu
    .env de verdade.
    """
    monkeypatch.setenv("AGENT_NAME", "ATLAS")
    s = Settings(_env_file=None)
    assert s.agent_name == "ATLAS"