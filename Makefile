.PHONY: test test-smoke test-regression test-ci-preflight test-fast test-meta test-display test-submission test-full test-family line-budget line-budget-strict test-structure test-structure-strict test-control-plane test-medical-paper-ops test-medical-quality-regression

MAS_PYTEST_WORKERS ?= auto
MAS_PYTEST_DIST ?= loadscope
MAS_PYTEST_XDIST_ARGS := -n $(MAS_PYTEST_WORKERS) --dist=$(MAS_PYTEST_DIST)

CONTROL_PLANE_TESTS := \
	tests/test_control_plane_regression.py \
	tests/test_control_plane_structure.py \
	tests/test_domain_authority_snapshot.py \
	tests/test_autonomy_state_surface.py \
	tests/test_study_runtime_typed_surface_cases/status_type_cases.py \
	tests/test_authority_route_gate.py \
	tests/test_artifact_lifecycle_inventory.py \
	tests/test_artifact_retention_operations_plan.py \
	tests/test_storage_governance_policy_kernel.py \
	tests/test_artifact_lifecycle_operations_report.py \
	tests/test_runtime_protocol_paper_artifacts.py \
	tests/test_study_delivery_sync.py \
	tests/test_runtime_storage_maintenance.py \
	tests/test_workspace_authority_migration_audit.py \
	tests/test_delivery_authority_backfill_apply.py \
	tests/test_cli_cases/public_entry_commands.py::test_workspace_authority_migration_audit_command_dispatches_read_only_controller \
	tests/test_cli_cases/public_entry_commands.py::test_control_plane_cleanup_apply_is_not_public \
	tests/test_cli_cases/public_entry_commands.py::test_lifecycle_report_command_dispatches_read_only_controller_options \
	tests/test_cli_cases/authority_operation_commands.py \
	tests/test_mcp_server.py::test_mcp_authority_operations_description_documents_authority_operation_surfaces \
	tests/test_mcp_server.py::test_mcp_authority_operations_schema_accepts_authority_operation_options \
	tests/test_mcp_server.py::test_mcp_authority_operations_can_call_workspace_authority_migration_audit \
	tests/test_mcp_server.py::test_mcp_authority_operations_rejects_cleanup_apply_mode \
	tests/test_mcp_server.py::test_mcp_authority_operations_can_call_lifecycle_report_with_scan_options \
	tests/test_test_command_surfaces.py::test_authority_operation_command_catalog_guards_cli_mcp_manifest_and_schema_surfaces \
	tests/test_installed_mcp_smoke.py::test_installed_medautosci_mcp_lists_authority_operation_modes \
	tests/test_installed_mcp_smoke.py::test_installed_medautosci_cli_lists_authority_operation_group_commands \
	tests/test_installed_mcp_smoke.py::test_installed_medautosci_mcp_calls_artifact_lifecycle_continuous_soak_summary \
	tests/test_installed_mcp_smoke.py::test_installed_medautosci_cli_calls_artifact_lifecycle_continuous_soak_summary \
	tests/test_truth_projection_surfaces.py \
	tests/test_runtime_health_projection_surfaces.py \
	tests/test_study_progress.py \
	tests/test_product_entry.py \
	tests/test_domain_health_diagnostic.py

test: test-smoke

test-smoke:
	scripts/run-pytest-clean.sh tests/test_smoke_entrypoints.py tests/test_line_budget.py -q

test-regression:
	scripts/run-pytest-clean.sh -q $(MAS_PYTEST_XDIST_ARGS) -m "not meta and not display_heavy and not submission_heavy and not materialization_heavy and not family"

test-ci-preflight:
	@if [ -z "$${BASE_REF:-}" ]; then echo "BASE_REF is required, for example: BASE_REF=HEAD~1 make test-ci-preflight" >&2; exit 2; fi
	scripts/run-python-clean.sh -m med_autoscience.cli doctor preflight --base-ref "$${BASE_REF}"

test-fast: test-regression

test-meta:
	scripts/run-pytest-clean.sh -q -m meta

test-display:
	scripts/run-pytest-clean.sh -q $(MAS_PYTEST_XDIST_ARGS) -m display_heavy

test-submission:
	scripts/run-pytest-clean.sh -q $(MAS_PYTEST_XDIST_ARGS) -m "submission_heavy or materialization_heavy"

test-family:
	scripts/run-pytest-clean.sh tests/test_family_shared_release.py tests/test_editable_shared_bootstrap.py tests/test_dev_preflight_contract.py tests/test_dev_preflight.py -q
	scripts/run-pytest-clean.sh tests/test_opl_agent_lab_longline_migration.py -q

line-budget:
	scripts/run-python-clean.sh scripts/line_budget.py

line-budget-strict: line-budget

test-control-plane:
	scripts/run-pytest-clean.sh -q $(CONTROL_PLANE_TESTS)

test-medical-paper-ops:
	scripts/run-pytest-clean.sh -q tests/test_medical_paper_ops_health.py tests/study_progress_cases/medical_paper_ops_health_projection.py tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_medical_paper_ops_health.py

test-medical-quality-regression:
	scripts/run-pytest-clean.sh -q tests/test_medical_quality_regression_lane.py tests/test_agent_lab_medical_manuscript_quality.py tests/test_agent_lab_medical_manuscript_quality_cases/owner_chain_regression_family.py tests/test_paper_progress_state.py tests/test_paper_progress_reconciler.py tests/test_progress_first_global_contract.py

test-structure:
	scripts/run-python-clean.sh scripts/line_budget.py
	scripts/run-structure-quality-gate.sh

test-structure-strict:
	scripts/run-python-clean.sh scripts/line_budget.py
	scripts/run-structure-quality-gate.sh

test-full:
	./scripts/run-parallel-test-lanes.sh full
