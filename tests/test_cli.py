import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from freecad_cli.cli import cli


def _mock_proxy():
    return patch("freecad_cli.client.xmlrpc.client.ServerProxy")


def test_create_document():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = {"output": "MyDoc\n", "error": ""}
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["create-document", "MyDoc"])
        output = json.loads(result.output)
        assert output == {"status": "ok", "data": "MyDoc"}


def test_list_documents():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = {"output": '["Doc1", "Doc2"]\n', "error": ""}
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["list-documents"])
        output = json.loads(result.output)
        assert output["data"] == ["Doc1", "Doc2"]


def test_create_object_with_properties():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = {"output": "MyBox\n", "error": ""}
        mock_cls.return_value = mock
        result = runner.invoke(cli, [
            "create-object", "MyDoc", "Part::Box", "MyBox",
            "--properties", '{"Length": 10}'
        ])
        output = json.loads(result.output)
        assert output == {"status": "ok", "data": "MyBox"}


def test_create_object_without_properties():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = {"output": "MyBox\n", "error": ""}
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["create-object", "MyDoc", "Part::Box", "MyBox"])
        output = json.loads(result.output)
        assert output == {"status": "ok", "data": "MyBox"}


def test_edit_object():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = {"output": "MyBox\n", "error": ""}
        mock_cls.return_value = mock
        result = runner.invoke(cli, [
            "edit-object", "MyDoc", "MyBox",
            "--properties", '{"Length": 20}'
        ])
        output = json.loads(result.output)
        assert output == {"status": "ok", "data": "MyBox"}


def test_delete_object():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = {"output": "", "error": ""}
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["delete-object", "MyDoc", "MyBox"])
        output = json.loads(result.output)
        assert output == {"status": "ok", "data": True}


def test_get_objects():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = {
            "output": '[{"name": "MyBox", "type": "Part::Box", "label": "MyBox"}]\n',
            "error": "",
        }
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["get-objects", "MyDoc"])
        output = json.loads(result.output)
        assert output["data"][0]["name"] == "MyBox"


def test_get_object():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = {
            "output": '{"name": "MyBox", "type": "Part::Box", "label": "MyBox", "properties": {}}\n',
            "error": "",
        }
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["get-object", "MyDoc", "MyBox"])
        output = json.loads(result.output)
        assert output["data"]["name"] == "MyBox"


def test_execute_code():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = {"output": "hello\n", "error": ""}
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["execute-code", 'print("hello")'])
        output = json.loads(result.output)
        assert output["status"] == "ok"


def test_invalid_properties_json():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock_cls.return_value = mock
        result = runner.invoke(cli, [
            "create-object", "MyDoc", "Part::Box", "MyBox",
            "--properties", "not-json"
        ])
        assert result.exit_code != 0


def test_execute_code_from_stdin():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = {"output": "hello\n", "error": ""}
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["execute-code", "-"], input="print('hello')")
        output = json.loads(result.output)
        assert output["status"] == "ok"
        mock.execute_code.assert_called_once()
        call_code = mock.execute_code.call_args[0][0]
        assert "print('hello')" in call_code


def test_execute_code_from_file():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = {"output": "42\n", "error": ""}
        mock_cls.return_value = mock
        with runner.isolated_filesystem():
            Path("script.py").write_text("print(42)")
            result = runner.invoke(cli, ["execute-code", "--file", "script.py"])
            output = json.loads(result.output)
            assert output["status"] == "ok"
            call_code = mock.execute_code.call_args[0][0]
            assert "print(42)" in call_code


def test_execute_code_file_and_code_conflict():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock_cls.return_value = mock
        with runner.isolated_filesystem():
            Path("script.py").write_text("print(1)")
            result = runner.invoke(cli, ["execute-code", "--file", "script.py", "inline_code"])
            assert result.exit_code != 0


def test_execute_code_no_input_error():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["execute-code"])
        assert result.exit_code != 0


def test_rpc_error_propagated():
    runner = CliRunner()
    with _mock_proxy() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = {
            "output": "",
            "error": "Traceback: NameError: name 'foo' is not defined",
        }
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["create-document", "Test"])
        assert result.exit_code != 0
