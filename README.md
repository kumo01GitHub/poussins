# poussins

A proof assistant running on Python.

## Develop

```bash
# Run
uv run -m poussins

# Unit Test
uv run pytest

# Lint
uv run ruff check .
```

## Release

```bash
# Build
uv run -m build

# Upload
uv run -m twine upload dist/*
```
