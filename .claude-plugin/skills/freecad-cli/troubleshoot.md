# Troubleshooting

## Setup Issues

### `freecad-cli: command not found`

uv tool path is not in PATH.

```sh
uv tool dir
# Usually: ~/.local/bin

# Add to .zshrc / .bashrc
export PATH="$HOME/.local/bin:$PATH"
source ~/.zshrc
```

### `freecad-cli ping` returns `connection_refused`

Check in order:
1. Is FreeCAD running?
2. Did you run `freecad-cli install-addon`?
3. Did you restart FreeCAD **after** installing the addon?
4. Is the addon in the correct location?
   - macOS: `~/Library/Application Support/FreeCAD/Mod/FreecadCli/`
   - Linux: `~/.local/share/FreeCAD/Mod/FreecadCli/`

### `install-addon` shows `Path already exists`

Remove existing install and retry:
```sh
# macOS
rm ~/Library/Application\ Support/FreeCAD/Mod/FreecadCli
# Linux
rm ~/.local/share/FreeCAD/Mod/FreecadCli
```

### `uv tool install -e .` fails

```sh
python3 --version  # Must be 3.12+
uv tool install -e . --python 3.12
```

---

## Runtime Issues

### `rpc_fault` error

Python error inside FreeCAD. Read the traceback.

Common causes:
- `FreeCAD.ActiveDocument` is `None` → `freecad-cli create-document <name>` first
- Missing import → add `import FreeCAD` etc. at the top
- Forgot `doc.recompute()` → always call after modifying objects

### `timeout` error

Default is 5 seconds. Increase for heavy operations:
```sh
freecad-cli --timeout 60 execute-code '...'
```

### Screenshot is black or empty

```sh
# Reset the 3D view
freecad-cli execute-code '
import FreeCADGui
v = FreeCADGui.ActiveDocument.ActiveView
v.viewIsometric()
v.fitAll()
print("ok")
'
freecad-cli screenshot
```

### `connection_refused` during operation

FreeCAD may have crashed. Restart it — the addon auto-starts.
