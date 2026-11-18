import ipaddress
import socket
from html.parser import HTMLParser
from time import monotonic
from urllib.parse import urlencode, urlsplit

import requests
from playwright.sync_api import sync_playwright

from backend.core.config import settings
from backend.tools.base import RiskLevel, Tool

MAX_PAGE_BYTES = 512 * 1024
MAX_TEXT_LENGTH = 6000


class PageText(HTMLParser):
    ignored = {"script", "style", "noscript", "template"}

    def __init__(self):
        super().__init__()
        self.skip = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.ignored:
            self.skip.append(tag)

    def handle_endtag(self, tag):
        if self.skip and self.skip[-1] == tag:
            self.skip.pop()

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())


class OpenUrlTool(Tool):
    name = "open_url"
    description = "Consulta texto de uma página HTTPS pública em um domínio autorizado e informa a fonte."
    risk_level = RiskLevel.MEDIUM
    domain = "browser"

    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {"url": {"type": "string", "maxLength": 2048}},
            "required": ["url"],
        }

    @staticmethod
    def checked_url(url: str) -> tuple[str, str]:
        url = url.strip()
        if "://" not in url:
            url = "https://" + url
        if any(character.isspace() or ord(character) < 32 for character in url) or "\\" in url:
            raise ValueError("Informe uma URL HTTPS válida.")
        parsed = urlsplit(url)
        allowed = {host.strip().lower() for host in settings.web_hosts.split(",")}
        hostname = parsed.hostname
        if (
            parsed.scheme != "https" or not hostname or hostname not in allowed
            or parsed.username is not None or parsed.password is not None
            or parsed.port not in (None, 443) or "." not in hostname
        ):
            raise ValueError("Use HTTPS em um domínio cadastrado em WEB_HOSTS.")
        try:
            ipaddress.ip_address(hostname)
        except ValueError:
            return url, hostname
        raise ValueError("Use o nome de um domínio cadastrado, sem endereço IP.")

    def approval_details(self, arguments: dict) -> dict:
        url, _ = self.checked_url(arguments["url"])
        return {"url": url}

    def execute(self, url: str) -> str:
        try:
            url, host = self.checked_url(url)
            addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
                return "A página não está em um endereço público."
            return self.read_page(url)
        except (requests.RequestException, OSError, ValueError) as error:
            if isinstance(error, ValueError):
                return str(error)
            return "Não foi possível consultar a página. Confira a conexão e o endereço."

    @staticmethod
    def read_page(url: str) -> str:
        deadline = monotonic() + 12
        with requests.Session() as session:
            session.trust_env = False
            with session.get(url, allow_redirects=False, stream=True, timeout=(4, 4)) as response:
                if 300 <= response.status_code < 400:
                    return "A página redirecionou. Informe diretamente o endereço final autorizado."
                response.raise_for_status()
                media_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
                if media_type not in {"text/html", "text/plain"}:
                    return "A consulta aceita somente páginas HTML ou texto."
                raw = bytearray()
                for chunk in response.iter_content(chunk_size=4096):
                    if monotonic() >= deadline:
                        return "A página demorou demais para enviar o conteúdo."
                    remaining = MAX_PAGE_BYTES - len(raw)
                    raw.extend(chunk[:remaining])
                    if len(raw) == MAX_PAGE_BYTES:
                        break
                try:
                    text = raw.decode(response.encoding or "utf-8", errors="replace")
                except LookupError:
                    text = raw.decode("utf-8", errors="replace")
        if media_type == "text/html":
            parser = PageText()
            parser.feed(text)
            text = " ".join(parser.parts)
        text = " ".join(text.split())[:MAX_TEXT_LENGTH]
        return f"Fonte: {url}\n\n{text}" if text else f"A página não forneceu texto. Fonte: {url}"


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
            context = browser.new_context()
            page = context.new_page()
            try:
                page.goto(f"https://html.duckduckgo.com/html/?{urlencode({'q': query})}", timeout=15000)
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
