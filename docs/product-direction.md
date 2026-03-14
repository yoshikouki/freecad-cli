# Product Direction

## Two-Layer Command Philosophy

freecad-cli provides two layers of interaction:

### Low-level: `execute-code`

The `execute-code` command is the universal primitive. It sends arbitrary Python code to FreeCAD's eval proxy and covers 100% of FreeCAD's API surface. Any operation possible in FreeCAD's Python console can be performed through this command.

From real-world usage (building a parametric ring stand model with PartDesign), `execute-code` alone was sufficient for all modeling operations — sketches, constraints, pads, pockets, fillets, STL export, and more. The individual CRUD commands (`create-object`, `edit-object`, etc.) were never used.

### High-level: Integrated Commands

Integrated commands sit on top of `execute-code` and earn their place by providing value beyond raw code execution. A dedicated CLI command is justified when it provides at least one of:

- **AI agent discoverability** — `--help` text teaches an agent what is possible without prior FreeCAD knowledge
- **Auditability** — structured JSON output that can be parsed, logged, and tracked
- **Shell pipeline integration** — commands that compose well with Unix tools (stdin, pipes, files)
- **Multi-step orchestration** — operations requiring coordination that would be tedious to repeat (e.g., `screenshot` involves temp file creation, base64 encoding, and cleanup)

### Commands Worth Keeping

| Command | Justification |
|---------|--------------|
| `ping` | Health check — trivial but essential |
| `execute-code` | Core primitive — supports inline, file, and stdin input |
| `screenshot` | Multi-step orchestration (temp file + base64 + cleanup) |
| `install-addon` | System setup — not a FreeCAD API operation |
| `create-document` | High discoverability, common first action |
| `list-documents` | High discoverability, quick status check |
| `active-document` | Diagnostics — helps debug view/screenshot issues |
| `set-active-document` | Diagnostics — switches context for screenshot |

### Middle-Layer Commands (Candidates for Deprecation)

The following commands are thin wrappers around operations trivially done via `execute-code`. They add friction (rigid argument shapes, JSON property quoting) without meaningful value:

- `create-object` — `execute-code` is more flexible for PartDesign workflows
- `edit-object` — properties are easier to set in Python directly
- `delete-object` — one-liner in `execute-code`
- `get-object` / `get-objects` — `execute-code` can return exactly the data needed

These may be deprecated in a future release. Users should prefer `execute-code` for object manipulation.

## Design Principles

1. **`execute-code` is the escape hatch** — any FreeCAD operation must be possible through it, even if no dedicated command exists
2. **Don't wrap for the sake of wrapping** — a command must add value beyond what `execute-code` provides
3. **AI agent ergonomics matter** — `--help` descriptions, structured JSON output, and clear error messages help AI agents use the CLI effectively
4. **Shell-native** — support stdin pipes, file input, and composable output for integration with shell workflows
