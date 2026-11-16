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
   Check the `data.path` reported by `install-addon`. On all platforms, the installer
   selects `Mod` under the newest existing `FreeCAD/vX-Y` directory, or under the
   unversioned `FreeCAD` folder if none exists. The base data directory is
   `~/Library/Application Support` on macOS, `$XDG_DATA_HOME` (default
   `~/.local/share`) on Linux, or `%APPDATA%` on Windows. If the running FreeCAD
   uses an older version's directory, install into its actual `Mod` directory:

   ```sh
   freecad-cli install-addon --mod-dir /path/to/FreeCAD/v1-1/Mod
   ```

### `install-addon` shows `Path already exists`

For a conflicting symlink or directory junction, remove the link at the exact
path reported in the JSON error, then retry the same installation command
(including `--mod-dir` if used):

```sh
# macOS/Linux: replace with the path from the error
rm "/exact/path/from/error/FreecadCli"
```

```bat
:: Windows Command Prompt: remove the junction, using the path from the error
rmdir "C:\exact\path\from\error\FreecadCli"
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

### Edge/Face numbers don't match after adding features

Edge and Face indices (`Edge1`, `Face3`, etc.) are renumbered after every boolean operation (Pocket, Fillet, etc.). Never hardcode indices across features. Instead, re-enumerate by iterating `feature.Shape.Edges` or `feature.Shape.Faces` and filtering by coordinates:

```python
# Find the top face by Z coordinate
for i, face in enumerate(feature.Shape.Faces):
    if abs(face.CenterOfMass.z - expected_z) < 0.01:
        face_name = f"Face{i+1}"
```

### Fillet fails with "Edge does not belong to the shape"

The edge list references a previous feature's numbering. Always use the **latest feature** in the tree (the one just before the Fillet) as the base, and enumerate its edges fresh.

### Screenshot image is too large

If the screenshot causes issues (e.g., MCP response size limits), reduce dimensions:
```sh
freecad-cli screenshot --width 600
```
