# freecad-cli

A Python CLI tool for controlling FreeCAD from AI Agents via shell. Communicates with FreeCAD over XML-RPC (port 9875).

## Architecture

```
AI Agent → shell → freecad-cli (Python CLI)
                        ↓ XML-RPC (localhost:9875)
                    FreeCAD + Addon (thin eval proxy)
```

The addon is a minimal XML-RPC server that runs inside FreeCAD. It only exposes `ping` and `execute_code` — all business logic lives in the CLI client. Once installed, the addon never needs to be updated. See [docs/architecture.md](docs/architecture.md) for design rationale and security considerations.

## Setup

### 1. Install the CLI

```sh
uv tool install -e .
```

### 2. Install the FreeCAD addon

```sh
freecad-cli install-addon
```

This creates a symlink from FreeCAD's Mod directory to the addon source. Restart FreeCAD after the first install — the RPC server will auto-start on every launch.

### 3. Verify

```sh
freecad-cli ping
```

## Usage

```sh
freecad-cli create-document MyDoc
freecad-cli create-object MyDoc Part::Box MyBox --properties '{"Length": 10}'
freecad-cli get-objects MyDoc
freecad-cli execute-code 'print(FreeCAD.ActiveDocument.Name)'
freecad-cli screenshot --width 800
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
