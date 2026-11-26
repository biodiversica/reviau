# Development

*English · [Português (Brasil)](../pt-BR/development.md)*

```bash
git clone https://github.com/biodiversica/reviau
cd reviau
uv sync               # installs the project and the development tools
uv run ruff check .   # lint
uv run pytest         # tests
uv run reviau /path/to/segments
```

## Tests and CI

The test suite covers the naming rules, the filing of reviewed clips, the HTTP
API, the interface texts in both languages and a complete review carried out over
an in-process SFTP server. The client's DOM-independent helpers are tested with
Node.js, and those tests are skipped when Node.js is not installed. Continuous
integration runs the lint and the tests on Linux, macOS and Windows, and also
runs the installers on all three systems with the built package, followed by
`scripts/smoke_test.py`, which reviews a clip with the installed command.

Before pushing, the suite should also be run as the continuous integration runs
it:

```bash
GITHUB_ACTIONS=true uv run pytest
```

Rich colours the Typer help output whenever it detects a terminal, which it
always does on GitHub Actions. This changes the rendered output enough to break a
test that passes locally.

## Documentation

The documentation lives in [`docs/`](../README.md), one page per topic in
English and Portuguese under the same file name. A change to one language
should be made to the other in the same commit.
