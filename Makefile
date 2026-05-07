.PHONY: test test-smoke test-regression test-ci-preflight test-fast test-meta test-display test-submission test-full test-family test-structure test-control-plane test-medical-paper-ops

MAS_PYTEST_WORKERS ?= auto
MAS_PYTEST_DIST ?= loadscope
MAS_PYTEST_XDIST_ARGS := -n $(MAS_PYTEST_WORKERS) --dist=$(MAS_PYTEST_DIST)
ARCH_OWNER_BOUNDARY_TEST := tests/test_architecture_owner_boundary.py

CONTROL_PLANE_TESTS := \
	tests/test_control_plane_regression.py \
	tests/test_control_plane_structure.py \
	tests/test_study_control_plane_kernel.py \
	tests/test_control_plane_state_machine.py \
	tests/test_study_runtime_typed_surface_cases/status_type_cases.py \
	tests/test_control_plane_route_gate.py \
	tests/test_artifact_lifecycle_inventory.py \
	tests/test_artifact_retention_operations_plan.py \
	tests/test_storage_governance_policy_kernel.py \
	tests/test_artifact_lifecycle_operations_report.py \
	tests/test_runtime_protocol_paper_artifacts.py \
	tests/test_study_delivery_sync.py \
	tests/test_runtime_storage_maintenance.py \
	tests/test_control_plane_cleanup_apply.py \
	tests/test_control_plane_migration_audit.py \
	tests/test_cli_cases/public_entry_commands.py::test_migration_audit_command_dispatches_read_only_controller \
	tests/test_cli_cases/public_entry_commands.py::test_cleanup_apply_command_dispatches_controller \
	tests/test_cli_cases/public_entry_commands.py::test_lifecycle_report_command_dispatches_read_only_controller_options \
	tests/test_cli_cases/control_plane_operation_commands.py \
	tests/test_mcp_server.py::test_mcp_product_entry_description_documents_control_plane_operations_surfaces \
	tests/test_mcp_server.py::test_mcp_product_entry_schema_accepts_control_plane_operations_options \
	tests/test_mcp_server.py::test_mcp_product_entry_can_call_migration_audit \
	tests/test_mcp_server.py::test_mcp_product_entry_can_call_cleanup_apply \
	tests/test_mcp_server.py::test_mcp_product_entry_can_call_lifecycle_report_with_scan_options \
	tests/test_test_command_surfaces.py::test_control_plane_operation_command_catalog_guards_cli_mcp_manifest_and_schema_surfaces \
	tests/test_installed_mcp_smoke.py::test_installed_medautosci_mcp_lists_control_plane_operation_modes \
	tests/test_installed_mcp_smoke.py::test_installed_medautosci_cli_lists_control_plane_operation_commands \
	tests/test_installed_mcp_smoke.py::test_installed_medautosci_mcp_calls_continuous_soak_summary \
	tests/test_installed_mcp_smoke.py::test_installed_medautosci_cli_calls_continuous_soak_summary \
	tests/test_truth_projection_surfaces.py \
	tests/test_runtime_health_projection_surfaces.py \
	tests/test_study_progress.py \
	tests/test_product_entry.py \
	tests/test_runtime_watch.py

test: test-smoke

test-smoke:
	uv run pytest tests/test_test_command_surfaces.py tests/test_line_budget.py -q

test-regression:
	uv run pytest -q $(MAS_PYTEST_XDIST_ARGS) -m "not meta and not display_heavy and not submission_heavy and not family"

test-ci-preflight:
	@if [ -z "$${BASE_REF:-}" ]; then echo "BASE_REF is required, for example: BASE_REF=HEAD~1 make test-ci-preflight" >&2; exit 2; fi
	uv run python -m med_autoscience.cli doctor preflight --base-ref "$${BASE_REF}"

test-fast: test-regression

test-meta:
	uv run pytest -q -m meta
	uv run pytest -q $(ARCH_OWNER_BOUNDARY_TEST)

test-display:
	uv run pytest -q $(MAS_PYTEST_XDIST_ARGS) -m display_heavy

test-submission:
	uv run pytest -q $(MAS_PYTEST_XDIST_ARGS) -m submission_heavy

test-family:
	uv run pytest tests/test_family_shared_release.py tests/test_editable_shared_bootstrap.py tests/test_dev_preflight_contract.py tests/test_dev_preflight.py -q

test-control-plane:
	PYTHONPATH=src uv run pytest -q $(CONTROL_PLANE_TESTS)

test-medical-paper-ops:
	PYTHONPATH=src uv run pytest -q tests/test_medical_paper_ops_health.py tests/study_progress_cases/medical_paper_ops_health_projection.py tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_medical_paper_ops_health.py

test-structure:
	uv run python scripts/line_budget.py
	scripts/run-structure-quality-gate.sh

test-full:
	./scripts/run-parallel-test-lanes.sh full
