.PHONY: test

test:
	@sdk_src=""; \
		if python3 -c "import opl_client" >/dev/null 2>&1; then \
			sdk_src=""; \
		elif [ -n "$${OPL_PYTHON_CLIENT_DIR:-}" ] && [ -d "$${OPL_PYTHON_CLIENT_DIR}/src/opl_client" ]; then \
			sdk_src="$${OPL_PYTHON_CLIENT_DIR}/src"; \
		elif [ -n "$${OPL_FRAMEWORK_ROOT:-}" ] && [ -d "$${OPL_FRAMEWORK_ROOT}/sdks/python-client/src/opl_client" ]; then \
			sdk_src="$${OPL_FRAMEWORK_ROOT}/sdks/python-client/src"; \
		elif [ -d "../one-person-lab/sdks/python-client/src/opl_client" ]; then \
			sdk_src="../one-person-lab/sdks/python-client/src"; \
		elif [ -d "../.worktrees/opl-v2/sdks/python-client/src/opl_client" ]; then \
			sdk_src="../.worktrees/opl-v2/sdks/python-client/src"; \
		fi; \
		requirements_file="$$(mktemp "$${TMPDIR:-/tmp}/mas-dev-requirements.XXXXXX")"; \
		trap 'rm -f "$$requirements_file"' EXIT; \
		uv export --quiet --frozen --group dev --no-emit-project --no-header --no-annotate --output-file "$$requirements_file"; \
		PYTHONPATH="src$${sdk_src:+:$$sdk_src}$${PYTHONPATH:+:$$PYTHONPATH}" PYTHONDONTWRITEBYTECODE=1 uv run --isolated --no-project --with-requirements "$$requirements_file" python -m pytest tests -q
