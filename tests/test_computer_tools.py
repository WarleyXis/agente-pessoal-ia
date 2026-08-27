from backend.tools.base import RiskLevel
from backend.tools.computer_tools import ClickAtTool, OpenApplicationTool, TypeTextTool


def test_open_application_tool_metadata():
    tool = OpenApplicationTool()
    assert tool.name == "open_application"
    assert tool.risk_level == RiskLevel.HIGH


def test_open_application_rejects_unknown_app():
    tool = OpenApplicationTool()
    result = tool.execute(app_name="algo-nao-permitido.exe")
    assert "não permitido" in result


def test_click_at_tool_metadata():
    tool = ClickAtTool()
    assert tool.name == "click_at"
    assert tool.risk_level == RiskLevel.HIGH


def test_type_text_tool_metadata():
    tool = TypeTextTool()
    assert tool.name == "type_text"
    assert tool.risk_level == RiskLevel.HIGH