import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from freecad_cli.cli import cli


@pytest.fixture(params=["Darwin", "Linux", "Windows"])
def installation(request, tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    appdata = tmp_path / "appdata"
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setattr("freecad_cli.cli.platform.system", lambda: request.param)
    data_home = {
        "Darwin": home / "Library" / "Application Support",
        "Linux": home / ".local" / "share",
        "Windows": appdata,
    }[request.param]

    # Back mocked Windows junctions with real links so destination checks do I/O.
    junctions = set()

    def create_junction(source, destination):
        os.symlink(source, destination, target_is_directory=True)
        junctions.add(Path(destination))

    create_junction = Mock(side_effect=create_junction)
    monkeypatch.setitem(sys.modules, "_winapi", SimpleNamespace(CreateJunction=create_junction))
    is_symlink = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path not in junctions and is_symlink(path))
    monkeypatch.setattr(Path, "is_junction", lambda path: path in junctions)
    return SimpleNamespace(
        system=request.param,
        data_home=data_home,
        junctions=junctions,
        create_junction=create_junction,
    )


def assert_installed(result, link, installation):
    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    output = json.loads(result.stdout)
    assert output["status"] == "ok"
    assert output["data"]["path"] == str(link)
    source = Path(output["data"]["source"])
    assert link.resolve() == source.resolve()
    assert (link / "InitGui.py").is_file()
    if installation.system == "Windows":
        assert link.is_junction()
        assert not link.is_symlink()
        installation.create_junction.assert_called_once_with(str(source), str(link))
    else:
        assert link.is_symlink()
        installation.create_junction.assert_not_called()


def assert_json_error(result, code):
    assert result.exit_code == 1
    assert result.stdout == ""
    output = json.loads(result.stderr)
    assert output["status"] == "error"
    assert output["code"] == code
    return output


@pytest.mark.parametrize(("versions", "version"), [
    (["v1-1"], "v1-1"),
    (["v1-9", "v1-10"], "v1-10"),
    (["v1-10", "v2-0"], "v2-0"),
])
def test_install_addon_uses_newest_version(installation, versions, version):
    base = installation.data_home / "FreeCAD"
    for name in ["v0-21", *versions, "v99", "v9-9-9", "v3-x", "Macro"]:
        (base / name).mkdir(parents=True, exist_ok=True)
    (base / "v99-99").touch()

    result = CliRunner().invoke(cli, ["install-addon"])

    assert_installed(result, base / version / "Mod" / "FreecadCli", installation)
    assert not (base / "Mod").exists()


@pytest.mark.parametrize("existing_base", [False, True])
def test_install_addon_without_version(installation, existing_base):
    base = installation.data_home / "FreeCAD"
    if existing_base:
        (base / "Macro").mkdir(parents=True)

    result = CliRunner().invoke(cli, ["install-addon"])

    assert_installed(result, base / "Mod" / "FreecadCli", installation)


@pytest.mark.parametrize("installation", ["Linux"], indirect=True)
def test_install_addon_respects_xdg_data_home(installation, tmp_path, monkeypatch):
    data_home = tmp_path / "xdg-data"
    (data_home / "FreeCAD" / "v1-1").mkdir(parents=True)
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))

    result = CliRunner().invoke(cli, ["install-addon"])

    assert_installed(result, data_home / "FreeCAD" / "v1-1" / "Mod" / "FreecadCli", installation)
    assert not (installation.data_home / "FreeCAD").exists()


def test_install_addon_mod_dir_override(installation, tmp_path, monkeypatch):
    base = installation.data_home / "FreeCAD"
    (base / "v1-2").mkdir(parents=True)
    mod_dir = tmp_path / "older-freecad" / "Mod"
    # An explicit destination does not need the platform's default data location.
    monkeypatch.delenv("APPDATA", raising=False)

    result = CliRunner().invoke(cli, ["install-addon", "--mod-dir", str(mod_dir)])

    assert_installed(result, mod_dir / "FreecadCli", installation)
    assert not (base / "v1-2" / "Mod").exists()


def test_install_addon_already_installed(installation):
    runner = CliRunner()
    first = runner.invoke(cli, ["install-addon"])
    link = installation.data_home / "FreeCAD" / "Mod" / "FreecadCli"
    assert_installed(first, link, installation)

    result = runner.invoke(cli, ["install-addon"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {
        "status": "ok",
        "data": {"path": str(link), "message": "Already installed"},
    }
    if installation.system == "Windows":
        assert installation.create_junction.call_count == 1


@pytest.mark.parametrize("existing", ["link", "directory"])
def test_install_addon_rejects_existing_destination(installation, tmp_path, existing):
    link = installation.data_home / "FreeCAD" / "Mod" / "FreecadCli"
    link.parent.mkdir(parents=True)
    other = tmp_path / "other-addon"
    other.mkdir()
    if existing == "directory":
        link.mkdir()
    elif installation.system == "Windows":
        installation.create_junction(str(other), str(link))
    else:
        link.symlink_to(other, target_is_directory=True)

    result = CliRunner().invoke(cli, ["install-addon"])

    output = assert_json_error(result, "invalid_input")
    assert str(link) in output["error"]
    assert link.resolve() == (other if existing == "link" else link)


@pytest.mark.parametrize("operation", ["mkdir", "link"])
def test_install_addon_oserror_is_json(installation, monkeypatch, operation):
    mod_dir = installation.data_home / "FreeCAD" / "Mod"
    if operation == "mkdir":
        mkdir = Path.mkdir

        def denied_mkdir(path, *args, **kwargs):
            if path == mod_dir:
                raise PermissionError("permission denied for Mod")
            return mkdir(path, *args, **kwargs)

        monkeypatch.setattr(Path, "mkdir", denied_mkdir)
    elif installation.system == "Windows":
        installation.create_junction.side_effect = PermissionError("permission denied for Mod")
    else:
        monkeypatch.setattr("freecad_cli.cli.os.symlink", Mock(
            side_effect=PermissionError("permission denied for Mod"),
        ))

    result = CliRunner().invoke(cli, ["install-addon"])

    output = assert_json_error(result, "installation_error")
    assert "permission denied for Mod" in output["error"]
    assert not (mod_dir / "FreecadCli").exists()
