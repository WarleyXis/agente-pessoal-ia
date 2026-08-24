# Aqui definimos o "molde" que toda ferramenta do agente precisa
# seguir, e os níveis de risco que decidem se uma ação precisa de
# aprovação sua antes de rodar.

from abc import ABC, abstractmethod
from enum import Enum


class RiskLevel(str, Enum):
    """
    Nível de risco de uma ferramenta.

    LOW: sem consequência relevante (ex: ler a hora).
    MEDIUM: mudança reversível (ex: criar um arquivo).
    HIGH: ação potencialmente destrutiva (ex: apagar arquivos).
    CRITICAL: dinheiro, credenciais, dados sensíveis, irreversível.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Tool(ABC):
    """
    Toda ferramenta do agente precisa ter nome, descrição, nível de
    risco, e saber executar a própria ação.
    """

    name: str
    description: str
    risk_level: RiskLevel

    @abstractmethod
    def parameters_schema(self) -> dict:
        """
        Descreve, em formato JSON Schema, quais argumentos essa
        ferramenta espera. É isso que "explicamos" pro modelo de IA
        entender como chamar a ferramenta corretamente.
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Executa a ação de verdade e devolve o resultado em texto."""
        raise NotImplementedError
    