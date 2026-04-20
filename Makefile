.PHONY: test test-fast test-meta test-display test-full test-family

test: test-fast

test-fast:
	uv run pytest -q -m "not meta and not display_heavy and not family"

test-meta:
	uv run pytest -q -m meta

test-display:
	uv run pytest -q -m display_heavy

test-family:
	uv run pytest tests/test_family_shared_release.py tests/test_editable_shared_bootstrap.py tests/test_dev_preflight_contract.py tests/test_dev_preflight.py -q

test-full:
	uv run pytest -q
