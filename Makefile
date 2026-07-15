.PHONY: test test-smoke test-meta test-regression test-full test-structure

define run_python
tmp=$$(mktemp -d "$${TMPDIR:-/tmp}/mas-python.XXXXXX"); \
trap 'rm -rf "$$tmp"' EXIT; \
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$$tmp/pycache" \
PYTEST_ADDOPTS="-p no:cacheprovider -o cache_dir=$$tmp/pytest-cache" \
uv run --frozen python $(1)
endef

test: test-full

test-smoke:
	@$(call run_python,-m pytest tests/test_smoke_entrypoints.py -q)

test-meta:
	@$(call run_python,-m pytest -q -m meta)

test-regression:
	@$(call run_python,-m pytest -q -m "not meta")

test-full:
	@$(call run_python,-m pytest tests -q)

test-structure:
	scripts/run-structure-quality-gate.sh
