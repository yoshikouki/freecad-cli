import json
import os
import platform
import sys
from pathlib import Path

import click

from freecad_cli.client import FreeCADClient
from freecad_cli.output import error, success

COMMAND_SECTIONS = {
    "Core": ["execute-code", "ping", "screenshot"],
    "Documents": ["active-document", "create-document", "list-documents", "set-active-document"],
    "Objects": ["create-object", "edit-object", "delete-object", "get-object", "get-objects"],
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


@cli.command("create-object")
@click.argument("document")
@click.argument("type_name")
@click.argument("name")
@click.option("--properties", default=None, help="JSON string of properties")
@click.pass_context
def create_object(ctx, document, type_name, name, properties):
    """Create an object in a document."""
    props = _parse_properties(properties)
    result = ctx.obj["client"].create_object(document, type_name, name, props)
    success(result)


@cli.command("edit-object")
@click.argument("document")
@click.argument("name")
@click.option("--properties", required=True, help="JSON string of properties")
@click.pass_context
def edit_object(ctx, document, name, properties):
    """Edit an object's properties."""
    props = _parse_properties(properties)
    if props is None:
        error("--properties is required", "invalid_input")
    result = ctx.obj["client"].edit_object(document, name, props)
    success(result)


@cli.command("delete-object")
@click.argument("document")
@click.argument("name")
@click.pass_context
def delete_object(ctx, document, name):
    """Delete an object from a document."""
    result = ctx.obj["client"].delete_object(document, name)
    success(result)


@cli.command("get-objects")
@click.argument("document")
@click.pass_context
def get_objects(ctx, document):
    """List all objects in a document."""
    result = ctx.obj["client"].get_objects(document)
    success(result)


@cli.command("get-object")
@click.argument("document")
@click.argument("name")
@click.pass_context
def get_object(ctx, document, name):
    """Get details of a specific object."""
    result = ctx.obj["client"].get_object(document, name)
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


@cli.command("install-addon")
def install_addon():
    """Install the RPC server addon into FreeCAD."""
    addon_src = Path(__file__).resolve().parent.parent.parent / "addon" / "FreecadCli"
    if not addon_src.is_dir():
        error(f"Addon source not found: {addon_src}", "invalid_input")

    system = platform.system()
    if system == "Darwin":
        mod_dir = Path.home() / "Library" / "Application Support" / "FreeCAD" / "Mod"
    elif system == "Linux":
        mod_dir = Path.home() / ".local" / "share" / "FreeCAD" / "Mod"
    else:
        error(f"Unsupported platform: {system}", "invalid_input")

    mod_dir.mkdir(parents=True, exist_ok=True)
    link_path = mod_dir / "FreecadCli"

    if link_path.is_symlink() or link_path.exists():
        if link_path.is_symlink() and link_path.resolve() == addon_src.resolve():
            success({"path": str(link_path), "message": "Already installed"})
            return
        error(f"Path already exists: {link_path}. Remove it first.", "invalid_input")

    os.symlink(addon_src, link_path)
    success({"path": str(link_path), "source": str(addon_src)})


def _parse_properties(properties_json: str | None) -> dict | None:
    if properties_json is None:
        return None
    try:
        return json.loads(properties_json)
    except json.JSONDecodeError as e:
        error(f"Invalid JSON for properties: {e}", "invalid_input")
