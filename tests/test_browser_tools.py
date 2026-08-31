from backend.tools.base import RiskLevel
from backend.tools.browser_tools import OpenUrlTool, SearchWebTool


def test_open_url_tool_metadata():
    tool = OpenUrlTool()
    assert tool.name == "open_url"
    assert tool.risk_level == RiskLevel.MEDIUM


def test_search_web_tool_metadata():
    tool = SearchWebTool()
    assert tool.name == "search_web"
    assert tool.risk_level == RiskLevel.LOW