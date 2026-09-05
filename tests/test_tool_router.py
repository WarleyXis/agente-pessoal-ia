from backend.core.tool_router import relevant_domains


def test_no_keywords_returns_none():
    assert relevant_domains("oi, tudo bem?") is None


def test_vision_keyword_detected():
    domains = relevant_domains("o que você vê na minha tela?")
    assert domains is not None
    assert "vision" in domains
    assert "system" in domains


def test_computer_keyword_detected():
    domains = relevant_domains("abra o bloco de notas")
    assert "computer" in domains


def test_browser_keyword_detected():
    domains = relevant_domains("pesquise sobre python na web")
    assert "browser" in domains


def test_coding_keyword_detected():
    domains = relevant_domains("rode os testes do projeto")
    assert "coding" in domains