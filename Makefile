.PHONY: test

test:
	@PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 uv run --frozen python -m pytest tests -q
