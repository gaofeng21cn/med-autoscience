.PHONY: test

test:
	@requirements_file="$$(mktemp "$${TMPDIR:-/tmp}/mas-dev-requirements.XXXXXX")"; \
		trap 'rm -f "$$requirements_file"' EXIT; \
		uv export --quiet --frozen --only-group dev --no-emit-project --no-header --no-annotate --output-file "$$requirements_file"; \
		PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 uv run --isolated --no-project --with-requirements "$$requirements_file" python -m pytest tests -q
