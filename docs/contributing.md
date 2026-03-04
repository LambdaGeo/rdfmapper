# Contributing

## Setup

```bash
git clone https://github.com/lambdageo/rdfmapper.git
cd rdfmapper
pip install -e ".[dev]"
```

## Running tests

```bash
pytest tests/ -v
```

## Type checking

```bash
mypy src/
```

## Submitting changes

1. Fork the repository
2. Create a branch: `git checkout -b feat/my-feature`
3. Add tests for your changes
4. Open a Pull Request against `main`

## Reporting issues

Please open an issue at [github.com/lambdageo/rdfmapper/issues](https://github.com/lambdageo/rdfmapper/issues).
