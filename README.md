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
uv run -m poussins prove example/hilbert_s.py
```
