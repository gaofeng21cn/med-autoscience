.PHONY: test test-smoke test-regression test-ci-preflight test-fast test-meta test-display test-submission test-full test-family test-structure test-control-plane

CONTROL_PLANE_TESTS := \
	tests/test_control_plane_regression.py \
	tests/test_control_plane_structure.py \
	tests/test_study_control_plane_kernel.py \
	tests/test_control_plane_state_machine.py \
	tests/test_study_runtime_typed_surface_cases/status_type_cases.py \
	tests/test_control_plane_route_gate.py \
	tests/test_artifact_lifecycle_inventory.py \
	tests/test_artifact_lifecycle_operations_report.py \
	tests/test_runtime_protocol_paper_artifacts.py \
	tests/test_study_delivery_sync.py \
	tests/test_runtime_storage_maintenance.py \
	tests/test_control_plane_cleanup_apply.py \
	tests/test_control_plane_migration_audit.py \
	tests/test_cli_cases/public_entry_commands.py::test_migration_audit_command_dispatches_read_only_controller \
	tests/test_cli_cases/public_entry_commands.py::test_cleanup_apply_command_dispatches_controller \
	tests/test_cli_cases/public_entry_commands.py::test_lifecycle_report_command_dispatches_read_only_controller \
	tests/test_mcp_server.py::test_mcp_product_entry_description_documents_control_plane_operations_surfaces \
	tests/test_mcp_server.py::test_mcp_product_entry_schema_accepts_control_plane_operations_options \
	tests/test_mcp_server.py::test_mcp_product_entry_can_call_migration_audit \
	tests/test_mcp_server.py::test_mcp_product_entry_can_call_cleanup_apply \
	tests/test_mcp_server.py::test_mcp_product_entry_can_call_lifecycle_report \
	tests/test_truth_projection_surfaces.py \
	tests/test_runtime_health_projection_surfaces.py \
	tests/test_study_progress.py \
	tests/test_product_entry.py \
	tests/test_runtime_watch.py

test: test-smoke

test-smoke:
	uv run pytest tests/test_test_command_surfaces.py tests/test_line_budget.py -q

test-regression:
	uv run pytest -q -m "not meta and not display_heavy and not submission_heavy and not family"

test-ci-preflight:
	uv run pytest tests/test_release_workflow.py tests/test_python_environment_contract.py tests/test_codex_plugin.py tests/test_codex_plugin_installer.py -q

test-fast: test-regression

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
	uv run python scripts/line_budget.py
	sentrux gate
	if [ -f .sentrux/rules.toml ]; then sentrux check; fi

test-full:
	./scripts/run-parallel-test-lanes.sh full
