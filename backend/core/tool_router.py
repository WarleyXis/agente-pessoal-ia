# Filtro leve de ferramentas por palavra-chave: reduz quantas
# ferramentas mandamos ao modelo a cada mensagem, sem precisar de
# uma segunda chamada de IA para "rotear" — o que adicionaria mais
# uma chance de erro, já que vimos modelos pequenos errarem decisões
# mais simples que essa ao longo do projeto.
#
# Isso é uma heurística determinística, não um agente. Nunca esconde
# uma ferramenta por engano: se nenhuma palavra-chave bater, devolve
# None, e o chamador deve usar TODAS as ferramentas disponíveis.

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "vision": ["tela", "screenshot", "vendo", "vê", "imagem", "visual"],
    "computer": [
        "abra", "abrir", "clique", "clic", "digite", "digitar",
        "aplicativo", "programa", "janela",
    ],
    "browser": [
        "site", "navegador", "pesquis", "busca", "internet", "url",
        "página", "web",
    ],
    "coding": ["arquivo", "código", "teste", "git", "pytest", "commit"],
}

# Ferramentas de sistema (hora, listar arquivos) são de baixo risco
# e genuinamente úteis em qualquer contexto — sempre incluídas.
ALWAYS_INCLUDED_DOMAINS = {"system"}


def relevant_domains(user_message: str) -> set[str] | None:
    """
    Decide quais domínios de ferramenta são relevantes para a
    mensagem. Devolve None se nada específico foi detectado — nesse
    caso, o chamador deve usar todas as ferramentas, sem filtrar.
    """
    mensagem = user_message.lower()
    domains = set(ALWAYS_INCLUDED_DOMAINS)

    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in mensagem for keyword in keywords):
            domains.add(domain)

    if domains == set(ALWAYS_INCLUDED_DOMAINS):
        return None

    return domains