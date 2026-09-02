from backend.tools.base import RiskLevel
from backend.tools.coding_tools import GitInfoTool, ReadFileTool, RunTestsTool


def test_read_file_tool_metadata():
    tool = ReadFileTool()
    assert tool.name == "read_file"
    assert tool.risk_level == RiskLevel.LOW


def test_read_file_reads_existing_file():
    tool = ReadFileTool()
    result = tool.execute(path="requirements.txt")
    assert "pytest" in result


def test_read_file_blocks_path_traversal():
    tool = ReadFileTool()
    result = tool.execute(path="../../../../Windows/System32/drivers/etc/hosts")
    assert "Acesso negado" in result


def test_run_tests_tool_metadata():
    tool = RunTestsTool()
    assert tool.name == "run_tests"
    assert tool.risk_level == RiskLevel.MEDIUM


def test_git_info_tool_metadata():
    tool = GitInfoTool()
    assert tool.name == "git_info"
    assert tool.risk_level == RiskLevel.LOW


def test_git_info_rejects_unknown_subcommand():
    tool = GitInfoTool()
    result = tool.execute(subcommand="push --force")
    assert "não permitido" in result