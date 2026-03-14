import json

import click

from freecad_cli.client import FreeCADClient
from freecad_cli.output import error, success


@click.group()
@click.option("--host", default="localhost", help="FreeCAD RPC server host")
@click.option("--port", default=9875, type=int, help="FreeCAD RPC server port")
@click.option("--timeout", default=5.0, type=float, help="RPC timeout in seconds")
@click.pass_context
def cli(ctx, host, port, timeout):
    """CLI tool for controlling FreeCAD via XML-RPC."""
    ctx.ensure_object(dict)
    ctx.obj["client"] = FreeCADClient(host=host, port=port, timeout=timeout)


@cli.command()
@click.pass_context
def ping(ctx):
    """Check if FreeCAD RPC server is running."""
    result = ctx.obj["client"].ping()
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
@click.argument("code")
@click.pass_context
def execute_code(ctx, code):
    """Execute Python code in FreeCAD."""
    result = ctx.obj["client"].execute_code(code)
    success(result)


@cli.command()
@click.option("--width", default=800, type=int, help="Screenshot width in pixels")
@click.pass_context
def screenshot(ctx, width):
    """Take a screenshot of the active view."""
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


def _parse_properties(properties_json: str | None) -> dict | None:
    if properties_json is None:
        return None
    try:
        return json.loads(properties_json)
    except json.JSONDecodeError as e:
        error(f"Invalid JSON for properties: {e}", "invalid_input")
