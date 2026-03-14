# freecad-cli

A Python CLI tool for controlling FreeCAD from AI Agents via shell. Communicates with FreeCAD over XML-RPC (port 9875).

## Architecture

```
AI Agent → shell → freecad-cli (Python CLI)
                        ↓ XML-RPC (localhost:9875)
                    FreeCAD + Addon (RPC Server)
```

## Usage

```sh
freecad-cli ping
freecad-cli create-document MyDoc
freecad-cli create-object MyDoc Box MyBox --properties '{"Length": 10}'
freecad-cli get-objects MyDoc
```

All commands return JSON output:

```json
{"status": "ok", "data": true}
```

## Development

### Setup

```sh
uv sync
```

### Install as a command

```sh
uv tool install -e .
```

Installed in editable mode — source code changes take effect immediately.

To uninstall:

```sh
uv tool uninstall freecad-cli
```

### Test

```sh
uv run pytest
```
