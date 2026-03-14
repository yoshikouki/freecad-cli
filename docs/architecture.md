# Architecture

## Why RPC?

To control a running FreeCAD instance with its GUI, we need to execute code inside FreeCAD's own process. FreeCAD does not provide any built-in mechanism for external processes to connect to it.

- **Importing FreeCAD as a Python library** (`import FreeCAD`) starts a separate engine process. It cannot access documents open in the user's GUI — it runs in a completely different memory space.
- **FreeCAD command-line mode** (`freecadcmd`) spawns a new process per invocation with no persistent state and no GUI access.

The only way to interact with the user's live FreeCAD session is to run a server inside FreeCAD's process. This project uses a lightweight XML-RPC server embedded as a FreeCAD addon.

## Thin server design

The addon (`addon/FreecadCli/`) exposes exactly two RPC methods:

- `ping()` — health check
- `execute_code(code)` — execute arbitrary Python code on FreeCAD's main thread

All business logic — document management, export, screenshot capture — lives in the CLI client (`src/freecad_cli/client.py`), which constructs Python code strings and sends them via `execute_code`.

This means:

- **The addon is stable.** Once installed, it should never need updating.
- **New CLI features don't require FreeCAD restarts.** The CLI is installed in editable mode, so code changes take effect immediately.
- **Contributors should add new functionality to the CLI client, not to the addon.**

## Main thread constraint

FreeCAD's GUI operations (creating documents, modifying objects, taking screenshots) must run on the Qt main thread. The RPC server runs in a daemon thread, so calling GUI operations directly from RPC handlers will crash FreeCAD.

The addon solves this by dispatching `execute_code` requests to the main thread via a `PySide2.QtCore.Signal`, with a `queue.Queue` for synchronous result passing back to the RPC thread. If you ever need to modify the addon, this pattern must be preserved.

## Security considerations

The RPC server is an eval proxy — it executes arbitrary Python code sent to it. This is an intentional design choice for maximum flexibility, but it carries inherent risk:

- The server binds to `127.0.0.1` only (not `0.0.0.0`), so it is not accessible from other machines on the network.
- There is no authentication. Any local process can send code to the server.
- The risk profile is equivalent to the user typing commands into FreeCAD's built-in Python console.

This is acceptable for a local development tool, but the server should never be exposed to untrusted networks.
