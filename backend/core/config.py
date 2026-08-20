# Este arquivo é o "painel de controle" do projeto.
# Toda configuração do agente (nome, nível de log, ambiente, qual
# provedor de IA usar) é lida aqui, a partir do arquivo .env —
# nunca digitada direto nos outros arquivos do código.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuração central do agente.

    Essa classe herda de BaseSettings (do Pydantic), que sabe ler
    automaticamente valores de variáveis de ambiente ou de um
    arquivo .env e transformá-los em atributos Python com tipo
    definido (str, int, etc).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- identidade e comportamento geral ---
    agent_name: str = "JARVIS"
    log_level: str = "INFO"
    environment: str = "development"

    # --- provedor de modelo de linguagem (LLM) ---
    # "ollama" hoje; no futuro pode virar "openai" sem mudar
    # nenhum outro arquivo além deste e do llm_provider.py.
    llm_provider: str = "ollama"
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"


settings = Settings()