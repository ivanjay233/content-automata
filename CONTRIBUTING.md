# Contributing to content-automata

First off, thank you for considering contributing to content-automata! We welcome contributions from everyone.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How Can I Contribute?

### Reporting Bugs

- Check if the bug has already been reported in [Issues](https://github.com/ivanjay233/content-automata/issues).
- Use the bug report template and include:
  - A clear description of the issue
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (OS, Python version, etc.)

### Suggesting Features

- Open a feature request issue describing what you'd like to see.
- Explain why the feature would be useful and how it should work.
- Be open to discussion and feedback.

### Pull Requests

1. **Fork** the repository.
2. **Create a branch** for your changes: `git checkout -b feature/my-feature`.
3. **Make your changes** following the coding conventions below.
4. **Add or update tests** as needed.
5. **Run the tests** to make sure nothing is broken.
6. **Commit** with a clear, descriptive message.
7. **Push** to your fork and open a Pull Request.

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/content-automata.git
cd content-automata

# Install in development mode
make install

# Run tests
make test

# Run the example
make example
```

## Coding Conventions

- **Python**: 3.10+ with type hints on all public functions and methods.
- **Style**: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/). We use `black` for formatting.
- **Imports**: Use `from __future__ import annotations`, then standard library, third-party, and local imports separated by blank lines.
- **Docstrings**: Use Google-style docstrings for all public modules, classes, and functions.
- **Testing**: Write pytest tests for all new functionality. Aim for at least 80% coverage.
- **Models**: Use Pydantic for all data models.

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for Instagram scheduling
fix: correct CSV export encoding
docs: update README with new examples
test: add pipeline edge case tests
chore: update dependencies
```

## Project Structure

```
content-automata/
├── content_automata/       # Main package
│   ├── __init__.py         # Package exports (Pipeline)
│   ├── pipeline.py         # ContentPipeline orchestrator
│   ├── models.py           # Pydantic data models
│   ├── cli.py              # Click CLI
│   └── stages/             # Pipeline stages
│       ├── __init__.py
│       ├── research.py     # TopicResearch
│       ├── copywriter.py   # CopyWriter
│       ├── image_gen.py    # ImageGenerator
│       └── scheduler.py    # ContentScheduler
├── examples/               # Usage examples
│   ├── basic_pipeline.py
│   └── config.yaml.example
├── tests/                  # Test suite
│   └── test_pipeline.py
├── pyproject.toml          # Package configuration
├── Makefile                # Development tasks
├── README.md               # Project documentation
├── CONTRIBUTING.md         # This file
└── LICENSE                 # MIT License
```

## Adding a New Stage

1. Create a new file in `content_automata/stages/`.
2. Implement the stage class with a `generate()` or similar method.
3. Add a corresponding model in `models.py` if needed.
4. Wire the stage into `ContentPipeline._run()` in `pipeline.py`.
5. Add tests in `tests/`.

## Testing

```bash
# Run all tests
make test

# Run with verbose output
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_pipeline.py -v

# Run with coverage
python -m pytest tests/ --cov=content_automata
```

## Release Process

1. Update version in `content_automata/__init__.py` and `pyproject.toml`.
2. Update `CHANGELOG.md` (if we add one).
3. Tag the release: `git tag v0.1.0 && git push --tags`.
4. Build and publish: `python -m build && twine upload dist/*`.

---

Thank you for contributing! 🚀
