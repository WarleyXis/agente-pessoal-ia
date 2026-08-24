# O Policy Engine é a camada que decide se uma ação precisa da sua
# aprovação antes de rodar. Nenhuma ferramenta de risco médio pra
# cima executa sem passar por aqui — nem o modelo de IA pode pular
# essa etapa, porque a decisão não depende dele.

from backend.tools.base import RiskLevel

# Ferramentas LOW rodam direto. As demais pedem confirmação no
# terminal por enquanto (em fases futuras isso vira uma UI de
# verdade, com botão de aprovar/rejeitar).
RISK_REQUIRES_APPROVAL = {
    RiskLevel.LOW: False,
    RiskLevel.MEDIUM: True,
    RiskLevel.HIGH: True,
    RiskLevel.CRITICAL: True,
}


def requires_approval(risk_level: RiskLevel) -> bool:
    return RISK_REQUIRES_APPROVAL[risk_level]


def ask_approval(tool_name: str, arguments: dict) -> bool:
    """Pergunta ao usuário, no terminal, se a ação pode ser executada."""
    print(f"\n⚠ {tool_name} quer executar com argumentos: {arguments}")
    resposta = input("Permitir? (s/n): ").strip().lower()
    return resposta == "s"