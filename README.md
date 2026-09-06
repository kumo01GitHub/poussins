# poussins

A Python proof assistant with a small kernel and ergonomic proof DSL.

[![PyPI Version](https://img.shields.io/pypi/v/poussins)](https://pypi.org/project/poussins)
[![PyPI License](https://img.shields.io/pypi/l/poussins)](https://pypi.org/project/poussins)
[![Downloads](https://static.pepy.tech/badge/poussins/month)](https://pepy.tech/project/poussins)
[![Pylint](https://github.com/kumo01GitHub/poussins/actions/workflows/pylint.yml/badge.svg)](https://github.com/kumo01GitHub/poussins/actions/workflows/pylint.yml)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/78a507954076477a9b234e1f8234e572)](https://app.codacy.com/gh/kumo01GitHub/poussins/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

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
