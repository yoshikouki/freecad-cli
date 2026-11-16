import os
import platform
import re
import sys
from pathlib import Path

import click

from freecad_cli.client import FreeCADClient
from freecad_cli.output import error, success

COMMAND_SECTIONS = {
    "Core": ["execute-code", "export", "ping", "screenshot"],
    "Documents": ["active-document", "create-document", "list-documents", "set-active-document"],
    "Parts Library": ["list-parts", "insert-part"],
    "Setup": ["install-addon"],
}


class SectionedGroup(click.Group):
    def format_commands(self, ctx, formatter):
        commands = {}
        for name in self.list_commands(ctx):
            cmd = self.get_command(ctx, name)
            if cmd is not None:
                commands[name] = cmd

        for section, names in COMMAND_SECTIONS.items():
            rows = []
            for name in names:
                if name in commands:
                    cmd = commands[name]
                    help_text = cmd.get_short_help_str(limit=formatter.width)
                    rows.append((name, help_text))
            if rows:
                with formatter.section(section):
                    formatter.write_dl(rows)


@click.group(cls=SectionedGroup)
@click.option("--host", default="localhost", help="FreeCAD RPC server host")
@click.option("--port", default=9875, type=int, help="FreeCAD RPC server port")
@click.option("--timeout", default=5.0, type=float, help="RPC timeout in seconds")
@click.pass_context
def cli(ctx, host, port, timeout):
    """Control a running FreeCAD instance via shell.

    The primary command is execute-code, which runs arbitrary Python inside
    FreeCAD. It accepts inline code, a file (--file), or stdin (use '-').

    \b
    Quick start:
      freecad-cli ping
      freecad-cli execute-code 'print(FreeCAD.ActiveDocument.Name)'
      freecad-cli execute-code --file script.py
      cat script.py | freecad-cli execute-code -

    All commands return JSON: {"status": "ok", "data": ...}
    """
    ctx.ensure_object(dict)
    ctx.obj["client"] = FreeCADClient(host=host, port=port, timeout=timeout)


@cli.command()
@click.pass_context
def ping(ctx):
    """Check if FreeCAD RPC server is running."""
    result = ctx.obj["client"].ping()
    success(result)


@cli.command("active-document")
@click.pass_context
def active_document(ctx):
    """Show the active document and GUI state."""
    result = ctx.obj["client"].get_active_document()
    success(result)


@cli.command("set-active-document")
@click.argument("name")
@click.pass_context
def set_active_document(ctx, name):
    """Switch the active document and fit the view."""
    result = ctx.obj["client"].set_active_document(name)
    success(result)


@cli.command("create-document")
@click.argument("name")
@click.pass_context
def create_document(ctx, name):
    """Create a new document."""
    result = ctx.obj["client"].create_document(name)
    success(result)


@cli.command("list-documents")
@click.pass_context
def list_documents(ctx):
    """List all open documents."""
    result = ctx.obj["client"].list_documents()
    success(result)


@cli.command("execute-code")
@click.argument("code", required=False, default=None)
@click.option("--file", "file_path", default=None, type=click.Path(exists=True),
              help="Read code from a file")
@click.pass_context
def execute_code(ctx, code, file_path):
    """Execute Python code in FreeCAD (inline, file, or stdin).

    \b
    Three input modes:
      freecad-cli execute-code 'import FreeCAD; print(FreeCAD.listDocuments())'
      freecad-cli execute-code --file script.py
      cat script.py | freecad-cli execute-code -

    \b
    The code runs inside the FreeCAD process with full access to:
      FreeCAD, FreeCADGui, Part, PartDesign, Sketcher, Mesh, etc.

    \b
    Output is captured from stdout. Use print() to return results:
      freecad-cli execute-code 'import json; print(json.dumps({"key": "value"}))'
    """
    if file_path and code:
        error("Cannot specify both --file and a code argument", "invalid_input")

    if file_path:
        code = Path(file_path).read_text()
    elif code == "-" or (code is None and not sys.stdin.isatty()):
        code = sys.stdin.read()
    elif code is None:
        error("No code provided. Pass inline code, use --file, or pipe to stdin with '-'", "invalid_input")

    result = ctx.obj["client"].execute_code(code)
    success(result)


@cli.command()
@click.option("--width", default=800, type=int, help="Screenshot width in pixels")
@click.pass_context
def screenshot(ctx, width):
    """Take a screenshot of the active view (returns base64 PNG)."""
    result = ctx.obj["client"].get_active_screenshot(width)
    success(result)


@cli.command()
@click.argument("format", type=click.Choice(["stl", "step", "fcstd"]))
@click.option("--output", "-o", required=True, help="Output file path")
@click.option("--object", "object_name", default=None, help="Object name to export (default: Body or first object)")
@click.pass_context
def export(ctx, format, output, object_name):
    """Export an object to STL, STEP, or FCStd format."""
    result = ctx.obj["client"].export_object(format, output, object_name)
    success(result)


@cli.command("list-parts")
@click.pass_context
def list_parts(ctx):
    """List available parts from the library."""
    result = ctx.obj["client"].get_parts_list()
    success(result)


@cli.command("insert-part")
@click.argument("path")
@click.pass_context
def insert_part(ctx, path):
    """Insert a part from the library."""
    result = ctx.obj["client"].insert_part_from_library(path)
    success(result)


def _select_mod_dir(base: Path, directory_names: list[str]) -> Path:
    """Select the newest vX-Y directory, or the unversioned base, without I/O."""
    versioned = []
    for name in directory_names:
        match = re.fullmatch(r"v([0-9]+)-([0-9]+)", name)
        if match:
            versioned.append((tuple(int(p) for p in match.groups()), name))
    if versioned:
        return base / max(versioned)[1] / "Mod"
    return base / "Mod"


@cli.command("install-addon")
@click.option("--mod-dir", type=click.Path(path_type=Path),
              help="Install into this Mod directory instead of selecting one automatically")
def install_addon(mod_dir):
    """Install the RPC server addon into FreeCAD."""
    addon_src = Path(__file__).resolve().parent.parent.parent / "addon" / "FreecadCli"
    if not addon_src.is_dir():
        error(f"Addon source not found: {addon_src}", "invalid_input")

    system = platform.system()
    if system not in ("Darwin", "Linux", "Windows"):
        error(f"Unsupported platform: {system}", "invalid_input")

    try:
        if mod_dir is None:
            if system == "Darwin":
                data_home = Path.home() / "Library" / "Application Support"
            elif system == "Linux":
                data_home = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
            else:
                appdata = os.environ.get("APPDATA")
                if not appdata:
                    error("APPDATA environment variable is not set", "invalid_input")
                data_home = Path(appdata)
            base = data_home / "FreeCAD"
            directory_names = [child.name for child in base.iterdir() if child.is_dir()] if base.is_dir() else []
            mod_dir = _select_mod_dir(base, directory_names)

        mod_dir.mkdir(parents=True, exist_ok=True)
        link_path = mod_dir / "FreecadCli"

        is_link = link_path.is_symlink() or link_path.is_junction()
        if is_link or link_path.exists():
            if is_link and link_path.resolve() == addon_src.resolve():
                success({"path": str(link_path), "message": "Already installed"})
                return
            error(f"Path already exists: {link_path}. Remove it first.", "invalid_input")

        if system == "Windows":
            # Symlinks need admin or Developer Mode on Windows; directory junctions do not.
            import _winapi

            _winapi.CreateJunction(str(addon_src), str(link_path))
        else:
            os.symlink(addon_src, link_path)
    except OSError as exc:
        error(f"Could not install addon: {exc}", "installation_error")
    success({"path": str(link_path), "source": str(addon_src)})


