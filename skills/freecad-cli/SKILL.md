---
name: freecad-cli
description: Install, update, and operate freecad-cli — a CLI tool that controls FreeCAD via XML-RPC. Use when the user asks to set up freecad-cli, create 3D models, run Python code in FreeCAD, take screenshots, or troubleshoot freecad-cli commands.
---

# freecad-cli Agent Skill

## Core Model

`freecad-cli` is a shell bridge into a running FreeCAD GUI process.

- The FreeCAD addon is a thin localhost XML-RPC eval proxy.
- `execute-code` is the primary primitive and can reach the full FreeCAD Python API.
- Other commands are convenience wrappers for setup, diagnostics, screenshots, document state, exports, and parts-library lookup.
- The addon runs inside FreeCAD, so connection issues usually require checking both CLI installation and whether FreeCAD was restarted after addon installation.

## Setup

Follow this playbook in order.

### 1. Check Prerequisites

| Requirement | Command | Pass criteria |
|---|---|---|
| Python 3.12+ | `python3 --version` | Version 3.12 or higher |
| uv | `uv --version` | Command exists |
| FreeCAD | Ask user | FreeCAD app is running |

If uv is missing (install after user permission):

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Get Repository

If the user provides a repository path, use it. Otherwise clone:

```sh
git clone https://github.com/yoshikouki/freecad-cli.git
cd freecad-cli
```

### 3. Install CLI

```sh
uv tool install -e .
```

Verify: `freecad-cli --help` runs without error.

### 4. Install Addon

```sh
freecad-cli install-addon
```

Expected: JSON with `"status": "ok"`. `Already installed` is normal.

### 5. Restart FreeCAD

The addon initializes at FreeCAD startup. Ask the user to restart FreeCAD and confirm before proceeding.

### 6. Verify Connection

```sh
freecad-cli ping
```

Expected: `{"status": "ok", "data": true}`

If this fails, see [troubleshoot.md](troubleshoot.md).

---

## Update

```sh
cd <freecad-cli repo directory>
git pull
uv tool install -e . --force
```

The FreeCAD addon is symlinked to the repository. File changes from `git pull` are reflected on disk immediately, but FreeCAD must be restarted to reload the addon into its Python runtime. In practice, addon changes are rare — the design keeps the addon minimal.

---

## Verify

Run these checks before modeling and when commands fail unexpectedly:

```sh
freecad-cli --help              # CLI installed?
freecad-cli ping                # RPC connection?
freecad-cli active-document     # Document available?
```

- `command not found` → re-run Setup
- `connection_refused` → FreeCAD not running, or addon not installed / FreeCAD not restarted
- `timeout` → FreeCAD running but unresponsive, try restarting
- `active-document` returns `null` → create a document first: `freecad-cli create-document <name>`

## Operation Loop

1. Start with `freecad-cli ping` and `freecad-cli active-document`.
2. Create or select a document before modifying geometry.
3. Use `execute-code` for FreeCAD API work. Keep scripts small enough to diagnose failures.
4. Call `doc.recompute()` after every geometry or constraint change.
5. Use JSON or clear `print()` output for state checks.
6. Take a screenshot when visual confirmation is useful.
7. Export with the dedicated `export` command when producing STL, STEP, or FCStd files.

For common modeling snippets, read [execute-code-patterns.md](execute-code-patterns.md). For failures, read [troubleshoot.md](troubleshoot.md).

---

## Command Reference

### execute-code (core)

```sh
# Inline
freecad-cli execute-code 'print(FreeCAD.ActiveDocument.Name)'

# From file
freecad-cli execute-code --file script.py

# Pipe from stdin
cat script.py | freecad-cli execute-code -
echo 'print(1+1)' | freecad-cli execute-code -
```

Available modules: `FreeCAD`, `FreeCADGui`, `Part`, `PartDesign`, `Sketcher`, `Mesh`, `Draft`

Use `print()` for output. For structured data: `import json; print(json.dumps(data))`.

### Document Management

```sh
freecad-cli create-document MyPart
freecad-cli list-documents
freecad-cli active-document
freecad-cli set-active-document MyPart
```

### export

```sh
freecad-cli export stl -o output.stl
freecad-cli export step -o output.step --object MyBody
freecad-cli export fcstd -o model.FCStd
```

### Screenshot

```sh
freecad-cli screenshot              # 800px default
freecad-cli screenshot --width 1920 # custom width
```

Output is a base64-encoded square PNG.

### Global Options

```sh
freecad-cli --host localhost --port 9875 --timeout 30 execute-code '...'
```

Increase `--timeout` for heavy operations (STL export, complex booleans).

## Output Format

All commands return JSON:
- Success: `{"status": "ok", "data": <value>}`
- Failure: `{"status": "error", "error": "<message>", "code": "<error_code>"}`

Error codes: `connection_refused`, `timeout`, `rpc_fault`, `invalid_input`

---

## execute-code Patterns

See [execute-code-patterns.md](execute-code-patterns.md) for common FreeCAD Python snippets.

## Troubleshooting

See [troubleshoot.md](troubleshoot.md) for setup and runtime error solutions.
