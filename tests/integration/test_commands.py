import pytest
from typer.testing import CliRunner
from openseo.cli import _app

runner = CliRunner()

def test_cli_version():
    result = runner.invoke(_app, ["version"])
    assert result.exit_code == 0
    assert "OpenSEO" in result.stdout

def test_cli_doctor():
    result = runner.invoke(_app, ["doctor"])
    assert result.exit_code == 0
    assert "OpenSEO Doctor" in result.stdout

def test_cli_provider_list():
    result = runner.invoke(_app, ["provider", "list"])
    assert result.exit_code == 0
    assert "Available LLM Providers" in result.stdout
