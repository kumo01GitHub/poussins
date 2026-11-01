# poussins

A Python proof assistant with a small kernel and ergonomic proof DSL.

[![PyPI Version](https://img.shields.io/pypi/v/poussins)](https://pypi.org/project/poussins)
[![PyPI License](https://img.shields.io/pypi/l/poussins)](https://pypi.org/project/poussins)
[![Downloads](https://static.pepy.tech/badge/poussins/month)](https://pepy.tech/project/poussins)
[![Python package](https://github.com/kumo01GitHub/poussins/actions/workflows/python-package.yml/badge.svg)](https://github.com/kumo01GitHub/poussins/actions/workflows/python-package.yml)
[![Pylint](https://github.com/kumo01GitHub/poussins/actions/workflows/pylint.yml/badge.svg)](https://github.com/kumo01GitHub/poussins/actions/workflows/pylint.yml)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/78a507954076477a9b234e1f8234e572)](https://app.codacy.com/gh/kumo01GitHub/poussins/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

## Documentation Map

- Proof authors: [Proof Author Guide](docs/proof-author-guide.md)
- Contributors and maintainers: [Developer Guide](docs/developer-guide.md)
- Distributed execution users: [Integration Docs](docs/integration/README.md)
- Spark users: [Spark Integration Guide](docs/integration/spark.md)

## Quick Start

### Installation

Install `poussins` from PyPI:

```bash
pip install poussins
```

Try the official example (`example/hilbert_s.py`) by downloading and running it:

```bash
curl -L -o hilbert_s.py \
  https://raw.githubusercontent.com/kumo01GitHub/poussins/main/example/hilbert_s.py
python hilbert_s.py
```

Then create your own proof script and run it:

```bash
python path/to/proof.py
```

### From Source / Development

If you clone the repository or want to run examples directly with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/kumo01GitHub/poussins.git
cd poussins

uv sync
uv run example/hilbert_s.py
```
