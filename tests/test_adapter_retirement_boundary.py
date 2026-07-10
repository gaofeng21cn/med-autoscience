from __future__ import annotations

from pathlib import Path

from tests.test_adapter_retirement_boundary_cases.owner_callable_adapter_wire import (
    test_owner_callable_dispatch_residue_cleanup_surface_is_physically_retired,
    test_open_runtime_surfaces_cannot_use_active_callers_as_retention_reason,
    test_owner_callable_receipt_latest_reader_ignores_legacy_latest_wire,
    test_retired_legacy_stage_run_abi_scan_remains_provenance_not_delete_blocker,
    test_domain_owner_dispatch_execution_latest_payload_ignores_legacy_opt_in,
    test_current_owner_callable_readers_do_not_consume_legacy_latest_wire,
    test_legacy_latest_readers_consume_canonical_owner_callable_receipt_first,
)
from tests.test_adapter_retirement_boundary_cases.owner_callable_projection import (
    test_materializer_local_carrier_persistence_api_is_physically_retired,
    test_owner_callable_projection_does_not_accept_legacy_dispatch_alias,
    test_transition_request_counts_are_canonical_not_legacy_adapter_counts,
    test_owner_callable_projection_requires_canonical_transition_request_surface,
    test_public_owner_callable_adapter_reader_is_not_active_carrier,
    test_materializer_canonical_projection_preserves_strong_identity_without_legacy_body,
    test_domain_diagnostic_same_tick_admission_consumes_only_canonical_transition_requests,
    test_owner_action_execution_payloads_do_not_recommend_retired_private_cli_aliases,
    test_domain_owner_controller_refresh_public_wrapper_is_retired,
    test_retired_domain_owner_refresh_controller_command_is_not_active_cli_surface,
    test_current_controller_decision_refresh_does_not_emit_legacy_domain_owner_action_surface,
)
from tests.test_adapter_retirement_boundary_cases.runtime_inventory_contract import (
    assert_runtime_like_surfaces_have_machine_readable_opl_migration_inventory as _assert_runtime_like_surfaces_have_machine_readable_opl_migration_inventory,
    test_runtime_retirement_inventory_schema_is_closed_and_machine_readable,
)
from tests.test_adapter_retirement_boundary_cases.runtime_surface_no_authority_audit import (
    test_runtime_surface_retirement_guard_rejects_missing_retired_surface,
    test_runtime_surface_retirement_guard_rejects_resurrection_and_authority,
    test_runtime_surface_retirement_guard_rejects_retired_tombstone_rewrite,
    test_runtime_surface_retirement_no_authority_audit_blocks_active_caller_regression,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "med_autoscience"
ADAPTER_ROOT = SRC_ROOT / "adapters" / "deepscientist"
RUNTIME_TRANSPORT_ROOT = SRC_ROOT / "runtime_transport"


def test_production_code_does_not_import_deepscientist_adapters() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if path.is_relative_to(ADAPTER_ROOT):
            continue
        text = path.read_text(encoding="utf-8")
        if "med_autoscience.adapters.deepscientist" not in text and "adapters.deepscientist" not in text:
            continue
        violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_legacy_deepscientist_adapter_modules_are_removed() -> None:
    assert not (ADAPTER_ROOT / "__init__.py").exists()
    assert not (ADAPTER_ROOT / "daemon_api.py").exists()
    assert not (ADAPTER_ROOT / "mailbox.py").exists()
    assert not (ADAPTER_ROOT / "runtime.py").exists()
    assert not (ADAPTER_ROOT / "paper_bundle.py").exists()


def test_legacy_manual_finishing_projection_field_is_not_resurrected() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "legacy_current_stage" in text:
            violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_mas_private_runtime_transport_modules_are_physically_retired() -> None:
    assert not RUNTIME_TRANSPORT_ROOT.exists()


def test_production_code_does_not_import_retired_mas_runtime_transport_modules() -> None:
    forbidden_tokens = (
        "med_autoscience.runtime_transport.mas_runtime_core",
        "from med_autoscience.runtime_transport import mas_runtime_core",
        "from med_autoscience.runtime_transport import mas_runtime_core_",
        "med_autoscience.runtime_transport import mas_runtime_core",
    )
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if path.is_relative_to(RUNTIME_TRANSPORT_ROOT):
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden_tokens):
            violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_retired_runtime_supervisor_dispatch_executor_test_helper_is_removed() -> None:
    assert not (REPO_ROOT / "tests" / "runtime_supervisor_dispatch_executor_helpers.py").exists()


def test_runtime_like_surfaces_have_machine_readable_opl_migration_inventory() -> None:
    _assert_runtime_like_surfaces_have_machine_readable_opl_migration_inventory()
