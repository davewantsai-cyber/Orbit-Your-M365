from click.testing import CliRunner

from orbit.cli import main
from orbit.config import VERSION


def test_list_tools_prints_table_and_exits_zero():
    result = CliRunner().invoke(main, ["--list-tools"])
    assert result.exit_code == 0, result.output
    assert f"ORBIT v{VERSION} — Tool Status" in result.output
    for header in ("Tool", "Installed", "Compatible", "Version"):
        assert header in result.output
    for name in ("ScubaGear", "Maester", "Monkey365", "ROADtools", "Hawk"):
        assert name in result.output
