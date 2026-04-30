.PHONY: test test-fast test-meta test-display test-submission test-full test-family test-structure test-control-plane

test: test-fast

test-fast:
	uv run pytest -q -m "not meta and not display_heavy and not submission_heavy and not family"

test-meta:
	uv run pytest -q -m meta

test-display:
	uv run pytest -q -m display_heavy

test-submission:
	uv run pytest -q -m submission_heavy

test-family:
	uv run pytest tests/test_family_shared_release.py tests/test_editable_shared_bootstrap.py tests/test_dev_preflight_contract.py tests/test_dev_preflight.py -q

test-control-plane:
	PYTHONPATH=src uv run pytest -q tests/test_control_plane_regression.py tests/test_control_plane_structure.py

test-structure:
	python scripts/line_budget.py
	sentrux gate
	if [ -f .sentrux/rules.toml ]; then sentrux check; fi

test-full:
	./scripts/run-parallel-test-lanes.sh full
