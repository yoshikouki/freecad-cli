# freecad-cli

## Environment

- Python 3.12+, managed by uv
- Run tests: `uv run pytest`
- Lint: ruff (pre-commit hook via `.githooks/`)
- Install CLI locally: `uv tool install -e .`

## Design Principles

- `execute-code` is the primary primitive — avoid adding thin wrapper commands
- Multi-step orchestration commands (screenshot, export) are justified; simple CRUD wrappers are not
- This project is new with no existing users — delete freely, no deprecation ceremony needed

## Documentation

- Documentation must be in English
- When adding/removing CLI commands, update: README.md, SKILL.md, freecad-operator.md, docs/architecture.md
- COMMAND_SECTIONS in cli.py controls `--help` grouping
