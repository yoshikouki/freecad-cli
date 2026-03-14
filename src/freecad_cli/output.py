import json
import sys

import click


def success(data):
    click.echo(json.dumps({"status": "ok", "data": data}))


def error(message: str, code: str):
    click.echo(json.dumps({"status": "error", "error": message, "code": code}), err=True)
    sys.exit(1)
