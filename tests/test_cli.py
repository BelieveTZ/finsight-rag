from typer.testing import CliRunner

from finsight.cli import app


def test_doctor_reports_ready() -> None:
    result = CliRunner().invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Status: ready" in result.stdout

    assert "Python:" in result.stdout