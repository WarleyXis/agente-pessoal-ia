# Este arquivo é o "painel de controle" do projeto.
# Toda configuração do agente (nome, nível de log, ambiente) é lida
# aqui, a partir do arquivo .env — nunca digitada direto nos outros
# arquivos do código.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuração central do agente.

    Essa classe herda de BaseSettings (do Pydantic), que sabe ler
    automaticamente valores de variáveis de ambiente ou de um
    arquivo .env e transformá-los em atributos Python com tipo
    definido (str, int, etc).
    """

    # model_config diz ao Pydantic ONDE procurar as variáveis:
    # aqui, no arquivo .env, na mesma pasta do projeto.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignora variáveis extras que ainda não usamos
    )

    # Cada linha abaixo é uma configuração.
    # O valor depois do "=" é só um valor padrão — se existir a
    # variável correspondente no .env, ela sempre tem prioridade.
    agent_name: str = "JARVIS"          # nome do agente (vem de AGENT_NAME no .env)
    log_level: str = "INFO"             # nível de detalhe dos logs
    environment: str = "development"    # em qual ambiente está rodando


# Essa linha cria UMA instância pronta da configuração, já carregada
# a partir do .env. É essa variável "settings" que o resto do
# projeto vai importar e usar.
settings = Settings()