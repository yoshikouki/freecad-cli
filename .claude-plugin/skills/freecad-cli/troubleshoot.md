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
freecad-cli screenshot --width 800 --height 600
```
