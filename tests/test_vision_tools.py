from backend.tools.base import RiskLevel
from backend.tools.vision_tools import DescribeScreenTool


def test_describe_screen_tool_metadata():
    tool = DescribeScreenTool()
    assert tool.name == "describe_screen"
    assert tool.risk_level == RiskLevel.MEDIUM
    assert "question" in tool.parameters_schema()["properties"]