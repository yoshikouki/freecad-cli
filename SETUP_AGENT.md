# freecad-cli Setup Guide for AI Agents

You are setting up **freecad-cli**, a CLI tool that lets you control FreeCAD via shell commands.

## Prerequisites

Check that the following are available. If any are missing, ask the user for permission before installing them.

| Requirement | Check command | Install guide |
|---|---|---|
| Python 3.12+ | `python3 --version` | https://www.python.org/downloads/ |
| uv (Python package manager) | `uv --version` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| FreeCAD (GUI must be running) | FreeCAD should be open | https://www.freecad.org/downloads.php |

## Installation Steps

Run these commands in order:

```sh
# 1. Clone the repository
git clone https://github.com/yoshikouki/freecad-cli.git
cd freecad-cli

# 2. Install the CLI tool
uv tool install -e .

# 3. Install the addon (symlink on macOS/Linux, directory junction on Windows)
freecad-cli install-addon
```

The installer uses `Mod` inside the newest existing `vX-Y` directory under
`FreeCAD`, or inside the unversioned `FreeCAD` folder if none exists. The base
data directory is `~/Library/Application Support` on macOS, `$XDG_DATA_HOME`
(default `~/.local/share`) on Linux, or `%APPDATA%` on Windows. Check the installed
path in the JSON result. The CLI does not detect the running FreeCAD version;
if a newer development version has left an unused directory, pass the `Mod`
directory your FreeCAD actually uses:

```sh
freecad-cli install-addon --mod-dir /path/to/FreeCAD/v1-1/Mod
```

Filesystem failures return JSON on stderr with `"status": "error"` and
`"code": "installation_error"`, and a nonzero exit code.

After step 3, **restart FreeCAD**. The RPC server addon will auto-start on every launch.

## Verification

```sh
# Verify the connection to FreeCAD (FreeCAD must be running)
freecad-cli ping
```

Expected output:

```json
{"status": "ok", "data": true}
```

If `ping` fails with a connection error, ensure FreeCAD is running and was restarted after the addon was installed.

## Available Commands

Once installed, you can use these commands:

```sh
freecad-cli ping                          # Check connection
freecad-cli create-document <name>        # Create a new document
freecad-cli active-document               # Get the active document
freecad-cli execute-code '<python code>'  # Run Python code in FreeCAD
freecad-cli execute-code --file script.py # Run a Python script file
freecad-cli screenshot --width 800        # Take a screenshot
freecad-cli --help                        # See all commands
```

All commands return JSON: `{"status": "ok", "data": ...}` on success, `{"status": "error", ...}` on failure.
