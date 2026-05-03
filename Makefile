.PHONY: test test-fast test-meta test-display test-submission test-full test-family test-structure test-control-plane

CONTROL_PLANE_TESTS := \
	tests/test_control_plane_regression.py \
	tests/test_control_plane_structure.py \
	tests/test_study_control_plane_kernel.py \
	tests/test_control_plane_state_machine.py \
	tests/test_study_runtime_typed_surface_cases/status_type_cases.py \
	tests/test_artifact_lifecycle_inventory.py \
	tests/test_runtime_protocol_paper_artifacts.py \
	tests/test_study_delivery_sync.py \
	tests/test_runtime_storage_maintenance.py \
	tests/test_control_plane_migration_audit.py \
	tests/test_truth_projection_surfaces.py \
	tests/test_runtime_health_projection_surfaces.py \
	tests/test_study_progress.py \
	tests/test_product_entry.py \
	tests/test_runtime_watch.py

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
	PYTHONPATH=src uv run pytest -q $(CONTROL_PLANE_TESTS)

test-structure:
	python scripts/line_budget.py
	sentrux gate
	if [ -f .sentrux/rules.toml ]; then sentrux check; fi

test-full:
	./scripts/run-parallel-test-lanes.sh full
