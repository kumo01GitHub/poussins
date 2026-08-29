# poussins

A Python proof assistant with a small kernel and ergonomic proof DSL.

<p align="center">
<a href="https://pypi.org/project/poussins">
    <img alt="PyPI Version" src="https://img.shields.io/pypi/v/poussins">
</a>
<a href="https://pypi.org/project/poussins">
    <img alt="PyPI License" src="https://img.shields.io/pypi/l/poussins">
</a>
<a href="https://app.codacy.com/gh/kumo01GitHub/poussins/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade">
    <img src="https://app.codacy.com/project/badge/Grade/78a507954076477a9b234e1f8234e572"/>
</a>
</p>

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
