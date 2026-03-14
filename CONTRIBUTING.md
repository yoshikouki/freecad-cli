# Contributing to freecad-cli

Thank you for your interest in contributing!

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with a descriptive message
6. Push and open a Pull Request

## Development Setup

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/yoshikouki/freecad-cli.git
cd freecad-cli
uv sync
```

## Running Tests

```bash
uv run pytest
```

## Linting

```bash
uv run ruff check .
```

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `chore:` maintenance tasks
- `refactor:` code refactoring
- `test:` adding or updating tests

## Pull Requests

- Keep PRs focused on a single change
- Add tests for new functionality
- Ensure all tests pass and linting is clean
- Describe what your PR does and why

## Project Structure

- `src/freecad_cli/` — CLI client (Python package)
- `addon/FreecadCli/` — FreeCAD addon (runs inside FreeCAD)
- `tests/` — Test suite

The addon is intentionally minimal. Most changes should be in the CLI client.

## Questions?

Open an issue if you have questions or need help getting started.
