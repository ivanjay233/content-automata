.PHONY: install test example clean lint

# Installation
install:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

# Run tests
test:
	python -m pytest tests/ -v --tb=short

# Run the basic pipeline example
example:
	python examples/basic_pipeline.py

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf content_automata.egg-info/
	rm -rf __pycache__/
	rm -rf content_automata/__pycache__/
	rm -rf content_automata/stages/__pycache__/
	rm -rf tests/__pycache__/
	rm -rf examples/__pycache__/
	rm -rf .pytest_cache/
	rm -rf output/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Lint the code
lint:
	python -m pip install ruff --quiet 2>/dev/null || true
	python -m ruff check content_automata/ examples/ tests/
