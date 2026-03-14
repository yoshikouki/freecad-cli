import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from freecad_cli.cli import cli


def test_ping_success():
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.ping.return_value = True
        mock_proxy_cls.return_value = mock_proxy

        result = runner.invoke(cli, ["ping"])
        output = json.loads(result.output)
        assert output == {"status": "ok", "data": True}
        assert result.exit_code == 0


def test_ping_connection_refused():
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.ping.side_effect = ConnectionRefusedError()
        mock_proxy_cls.return_value = mock_proxy

        result = runner.invoke(cli, ["ping"])
        assert result.exit_code != 0


def test_execute_code_delegates_to_rpc():
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.execute_code.return_value = {"output": "hello\n", "error": ""}
        mock_proxy_cls.return_value = mock_proxy

        result = runner.invoke(cli, ["execute-code", "print('hello')"])
        output = json.loads(result.output)
        assert output["status"] == "ok"
        assert output["data"]["output"] == "hello\n"
