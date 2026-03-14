import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from freecad_cli.cli import cli


def _mock_client():
    return patch("freecad_cli.client.xmlrpc.client.ServerProxy")


def test_create_document():
    runner = CliRunner()
    with _mock_client() as mock_cls:
        mock = MagicMock()
        mock.create_document.return_value = "MyDoc"
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["create-document", "MyDoc"])
        output = json.loads(result.output)
        assert output["status"] == "ok"


def test_list_documents():
    runner = CliRunner()
    with _mock_client() as mock_cls:
        mock = MagicMock()
        mock.list_documents.return_value = ["Doc1", "Doc2"]
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["list-documents"])
        output = json.loads(result.output)
        assert output["data"] == ["Doc1", "Doc2"]


def test_create_object_with_properties():
    runner = CliRunner()
    with _mock_client() as mock_cls:
        mock = MagicMock()
        mock.create_object.return_value = "Box"
        mock_cls.return_value = mock
        result = runner.invoke(cli, [
            "create-object", "MyDoc", "Box", "MyBox",
            "--properties", '{"Length": 10}'
        ])
        output = json.loads(result.output)
        assert output["status"] == "ok"


def test_create_object_without_properties():
    runner = CliRunner()
    with _mock_client() as mock_cls:
        mock = MagicMock()
        mock.create_object.return_value = "Box"
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["create-object", "MyDoc", "Box", "MyBox"])
        output = json.loads(result.output)
        assert output["status"] == "ok"


def test_edit_object():
    runner = CliRunner()
    with _mock_client() as mock_cls:
        mock = MagicMock()
        mock.edit_object.return_value = True
        mock_cls.return_value = mock
        result = runner.invoke(cli, [
            "edit-object", "MyDoc", "MyBox",
            "--properties", '{"Length": 20}'
        ])
        output = json.loads(result.output)
        assert output["status"] == "ok"


def test_delete_object():
    runner = CliRunner()
    with _mock_client() as mock_cls:
        mock = MagicMock()
        mock.delete_object.return_value = True
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["delete-object", "MyDoc", "MyBox"])
        output = json.loads(result.output)
        assert output["status"] == "ok"


def test_get_objects():
    runner = CliRunner()
    with _mock_client() as mock_cls:
        mock = MagicMock()
        mock.get_objects.return_value = [{"name": "MyBox"}]
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["get-objects", "MyDoc"])
        output = json.loads(result.output)
        assert output["status"] == "ok"


def test_get_object():
    runner = CliRunner()
    with _mock_client() as mock_cls:
        mock = MagicMock()
        mock.get_object.return_value = {"name": "MyBox", "type": "Box"}
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["get-object", "MyDoc", "MyBox"])
        output = json.loads(result.output)
        assert output["data"]["name"] == "MyBox"


def test_execute_code():
    runner = CliRunner()
    with _mock_client() as mock_cls:
        mock = MagicMock()
        mock.execute_code.return_value = "hello"
        mock_cls.return_value = mock
        result = runner.invoke(cli, ["execute-code", 'print("hello")'])
        output = json.loads(result.output)
        assert output["status"] == "ok"


def test_invalid_properties_json():
    runner = CliRunner()
    with _mock_client() as mock_cls:
        mock = MagicMock()
        mock_cls.return_value = mock
        result = runner.invoke(cli, [
            "create-object", "MyDoc", "Box", "MyBox",
            "--properties", "not-json"
        ])
        assert result.exit_code != 0
