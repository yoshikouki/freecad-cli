import io
import json
import sys
import types
from contextlib import redirect_stdout
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


def test_export_object_stl():
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.execute_code.return_value = {"output": "/tmp/out.stl\n", "error": ""}
        mock_proxy_cls.return_value = mock_proxy

        result = runner.invoke(cli, ["export", "stl", "-o", "/tmp/out.stl"])
        output = json.loads(result.output)
        assert output["data"] == "/tmp/out.stl"
        call_code = mock_proxy.execute_code.call_args[0][0]
        assert "Mesh.export" in call_code


def test_export_object_step():
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.execute_code.return_value = {"output": "/tmp/out.step\n", "error": ""}
        mock_proxy_cls.return_value = mock_proxy

        result = runner.invoke(cli, ["export", "step", "-o", "/tmp/out.step"])
        output = json.loads(result.output)
        assert output["data"] == "/tmp/out.step"
        call_code = mock_proxy.execute_code.call_args[0][0]
        assert "Part.export" in call_code


def test_export_object_fcstd():
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.execute_code.return_value = {"output": "/tmp/out.fcstd\n", "error": ""}
        mock_proxy_cls.return_value = mock_proxy

        result = runner.invoke(cli, ["export", "fcstd", "-o", "/tmp/out.fcstd"])
        output = json.loads(result.output)
        assert output["data"] == "/tmp/out.fcstd"
        call_code = mock_proxy.execute_code.call_args[0][0]
        assert "doc.saveAs" in call_code


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


def _run_in_fake_freecad(dirs):
    """Run code sent over RPC against a fake FreeCAD module exposing `dirs`."""
    fake_freecad = types.ModuleType("FreeCAD")
    for name, path in dirs.items():
        setattr(fake_freecad, name, lambda path=path: path)

    def execute_code(code):
        stdout = io.StringIO()
        with patch.dict(sys.modules, {"FreeCAD": fake_freecad}), redirect_stdout(stdout):
            exec(code, {})
        return {"output": stdout.getvalue(), "error": ""}

    return execute_code


def _list_parts(dirs):
    runner = CliRunner()
    with patch("freecad_cli.client.xmlrpc.client.ServerProxy") as mock_proxy_cls:
        mock_proxy = MagicMock()
        mock_proxy.execute_code.side_effect = _run_in_fake_freecad(dirs)
        mock_proxy_cls.return_value = mock_proxy
        result = runner.invoke(cli, ["list-parts"])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)["data"]


def _make_library(base, *files):
    library = base / "Mod" / "Parts_Library"
    for name in files:
        path = library / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    return library


def test_list_parts_returns_paths_insert_part_can_open(tmp_path):
    library = _make_library(tmp_path / "user", "Mechanical/bolt.step", "README.md")

    parts = _list_parts({"getUserAppDataDir": str(tmp_path / "user")})

    assert parts == [str(library / "Mechanical" / "bolt.step")]


def test_list_parts_prefers_user_library_over_install(tmp_path):
    user_library = _make_library(tmp_path / "user", "user.FCStd")
    _make_library(tmp_path / "home", "bundled.FCStd")

    parts = _list_parts({
        "getUserAppDataDir": str(tmp_path / "user"),
        "getHomePath": str(tmp_path / "home"),
    })

    assert parts == [str(user_library / "user.FCStd")]


def test_list_parts_falls_back_to_install_dir(tmp_path):
    home_library = _make_library(tmp_path / "home", "bundled.iges")

    parts = _list_parts({
        "getUserAppDataDir": str(tmp_path / "user"),
        "getHomePath": str(tmp_path / "home"),
    })

    assert parts == [str(home_library / "bundled.iges")]


def test_list_parts_without_library_is_empty(tmp_path):
    assert _list_parts({"getUserAppDataDir": str(tmp_path / "user")}) == []
