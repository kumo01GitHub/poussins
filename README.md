# poussins

A Python proof assistant with a small kernel, tactic layer, and ergonomic proof DSL.

## Documentation Map

- Proof authors: [Proof Author Guide](docs/proof-author-guide.md)
- Contributors and maintainers: [Developer Guide](docs/developer-guide.md)

## Quick Start

```bash
uv sync
uv run -m poussins --help
```

Run an example proof:

```bash
uv run python example/example1.py
```

## Common Commands

```bash
# CLI
uv run -m poussins prove path/to/proofs.py

# Tests and lint
uv run pytest
uv run ruff check .

# Package
uv build
uv publish
```
