import json

from click.testing import CliRunner

from freecad_cli.output import success


def test_success_outputs_json():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(_success_command, ["hello"])
        output = json.loads(result.output)
        assert output == {"status": "ok", "data": "hello"}


import click


@click.command()
@click.argument("data")
def _success_command(data):
    success(data)
