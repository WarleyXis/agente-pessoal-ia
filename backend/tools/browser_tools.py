# Ferramentas de navegação web usando Playwright — um navegador real
# (headless, sem interface visível) controlado por código. Toda vez
# que uma ferramenta é chamada, abrimos e fechamos o navegador: mais
# simples de manter, ao custo de alguns segundos extras por chamada.
#
# Atenção de segurança: o texto de uma página da web é conteúdo NÃO
# confiável — uma página maliciosa poderia tentar incluir instruções
# disfarçadas de texto normal, na esperança de manipular o agente.
# Por isso 'open_url' pede aprovação antes de rodar.

from playwright.sync_api import sync_playwright

from backend.tools.base import RiskLevel, Tool

MAX_TEXT_LENGTH = 3000  # limite para não sobrecarregar o contexto do modelo


class OpenUrlTool(Tool):
    name = "open_url"
    description = (
        "Abre uma página da web pela URL e devolve o título e o "
        "texto visível dela. Use quando o usuário pedir para "
        "acessar um site específico."
    )
    risk_level = RiskLevel.MEDIUM
    domain = "browser"

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL completa da página, incluindo https://",
                }
            },
            "required": ["url"],
        }

    def execute(self, url: str = "", **kwargs) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, timeout=15000)
                titulo = page.title()
                texto = page.inner_text("body")
            except Exception as erro:
                return f"Não foi possível abrir a página: {erro}"
            finally:
                browser.close()

        texto = texto.strip()[:MAX_TEXT_LENGTH]
        return f"Título: {titulo}\n\nConteúdo:\n{texto}"


class SearchWebTool(Tool):
    name = "search_web"
    description = "Pesquisa um termo na web e devolve os principais resultados (título e link)."
    risk_level = RiskLevel.LOW
    domain = "browser"

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "O que pesquisar."}
            },
            "required": ["query"],
        }

    def execute(self, query: str = "", **kwargs) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Um navegador automatizado "padrão" costuma se denunciar por
            # não ter identificação de navegador real nem tamanho de tela
            # — isso ajuda a evitar ser barrado como robô.
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            try:
                page.goto(f"https://html.duckduckgo.com/html/?q={query}", timeout=15000)
                titulos = page.locator(".result__title").all_inner_texts()[:5]
                links = page.locator(".result__url").all_inner_texts()[:5]
            except Exception as erro:
                return f"Não foi possível pesquisar: {erro}"
            finally:
                browser.close()

        if not titulos:
            return "Nenhum resultado encontrado."

        linhas = [f"- {titulo} ({link.strip()})" for titulo, link in zip(titulos, links)]
        return "Resultados da pesquisa:\n" + "\n".join(linhas)