from backend.tools.system_tools import GetCurrentTimeTool, ListFilesTool


def test_get_current_time_returns_text():
    tool = GetCurrentTimeTool()
    result = tool.execute()
    assert "A data e hora atuais são" in result


def test_list_files_current_directory():
    tool = ListFilesTool()
    result = tool.execute(directory=".")
    assert "backend" in result  # sabemos que essa pasta existe no projeto