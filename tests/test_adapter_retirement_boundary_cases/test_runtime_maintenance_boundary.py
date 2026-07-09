from __future__ import annotations

import importlib
import json
from collections.abc import Callable
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = (
    REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
)


def _inventory() -> dict:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def _surface(inventory: dict, surface_id: str) -> dict:
    return {item["surface_id"]: item for item in inventory["surfaces"]}[surface_id]


@pytest.mark.parametrize(
    (
        "surface_id",
        "disposition",
        "mutation_flag",
        "required_gate",
        "required_forbidden_claim",
    ),
    [
        (
            "runtime_lifecycle_payload_retention",
            "opl_authorized_maintenance_callable_adapter_live_takeover_tail_open",
            "mutates_derived_runtime_lifecycle_payload_only_when_opl_authorized",
            "live_opl_cleanup_policy_takeover_required",
            "runtime_storage_apply_as_paper_progress",
        ),
        (
            "runtime_storage_maintenance",
            "opl_authorized_storage_maintenance_callable_adapter_live_takeover_tail_open",
            "mutates_runtime_storage_payload_only_when_opl_authorized",
            "live_opl_storage_policy_takeover_required",
            "runtime_storage_apply_as_provider_admission",
        ),
    ],
)
def test_runtime_maintenance_surfaces_require_bound_opl_authorization(
    surface_id: str,
    disposition: str,
    mutation_flag: str,
    required_gate: str,
    required_forbidden_claim: str,
) -> None:
    surface = _surface(_inventory(), surface_id)

    assert surface["current_disposition"] == disposition
    assert surface["authority_boundary"]["can_create_opl_command"] is False
    assert surface["authority_boundary"]["can_create_opl_stage_run"] is False
    assert surface["authority_boundary"]["can_authorize_generic_cleanup_policy"] is False
    assert surface["authority_boundary"]["can_write_domain_truth"] is False
    assert surface["authority_boundary"][mutation_flag] is True
    assert surface["apply_gate"]["required_authorization_surface"].startswith("opl_runtime_")
    assert "authorization_ref" in surface["apply_gate"]["must_bind"]
    assert required_forbidden_claim in surface["forbidden_claims"]
    assert surface["retirement_gate"][required_gate] is True


@pytest.mark.parametrize(
    ("surface_id", "mutate", "expected_reasons"),
    [
        (
            "runtime_lifecycle_payload_retention",
            lambda surface: _break_lifecycle(surface),
            {
                "truthy_authority_flag:authority_boundary.can_authorize_generic_cleanup_policy",
                "lifecycle_retention_missing_opl_authorized_mutation_flag",
                "lifecycle_retention_apply_gate_bindings_incomplete",
                "lifecycle_retention_tail_status_not_open",
                "lifecycle_retention_tail_missing_false_completion_guards",
                "lifecycle_retention_missing_live_opl_takeover_gate",
            },
        ),
        (
            "runtime_storage_maintenance",
            lambda surface: _break_storage(surface),
            {
                "truthy_authority_flag:authority_boundary.can_claim_paper_progress",
                "storage_maintenance_missing_dry_run_projection_boundary",
                "storage_maintenance_missing_opl_authorized_mutation_flag",
                "storage_maintenance_apply_gate_bindings_incomplete",
                "storage_maintenance_tail_status_not_open",
                "storage_maintenance_tail_missing_false_completion_guards",
                "storage_maintenance_missing_live_opl_takeover_gate",
            },
        ),
    ],
)
def test_runtime_maintenance_surfaces_reject_mas_authority_regressions(
    surface_id: str,
    mutate: Callable[[dict], None],
    expected_reasons: set[str],
) -> None:
    inventory = _inventory()
    mutate(_surface(inventory, surface_id))

    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    violations = retirement.validate_runtime_surface_retirement_inventory(inventory)

    observed_reasons = {
        item["reason"] for item in violations if item["surface_id"] == surface_id
    }
    assert expected_reasons <= observed_reasons


def _break_lifecycle(surface: dict) -> None:
    tail = surface["opl_runtime_lifecycle_maintenance_tail_readback"]
    tail["status"] = "satisfied_with_apply_gate"
    tail["required_before_physical_delete"] = "runtime_lifecycle_apply_gate_ref"
    tail["sqlite_sidecar_repair_receipt_can_satisfy_live_takeover"] = True
    tail["forbidden_completion_claims"].remove("payload_retention_plan_as_live_takeover")
    surface["authority_boundary"]["can_authorize_generic_cleanup_policy"] = True
    surface["authority_boundary"][
        "mutates_derived_runtime_lifecycle_payload_only_when_opl_authorized"
    ] = False
    surface["apply_gate"]["required_for_apply"] = False
    surface["apply_gate"]["must_bind"].remove("authorization_ref")
    surface["retirement_gate"]["live_opl_cleanup_policy_takeover_required"] = False


def _break_storage(surface: dict) -> None:
    tail = surface["opl_runtime_storage_maintenance_tail_readback"]
    tail["status"] = "satisfied_with_restore_canary"
    tail["required_before_physical_delete"] = "runtime_storage_restore_canary_ref"
    tail["archive_report_retention_plan_can_satisfy_live_takeover"] = True
    tail["forbidden_completion_claims"].remove("archive_retention_plan_as_live_takeover")
    surface["authority_boundary"]["can_claim_paper_progress"] = True
    surface["authority_boundary"]["dry_run_projection_only"] = False
    surface["authority_boundary"][
        "mutates_runtime_storage_payload_only_when_opl_authorized"
    ] = False
    surface["apply_gate"]["required_for_workspace_apply"] = False
    surface["apply_gate"]["must_bind"].remove("workspace_root_or_quest_root")
    surface["retirement_gate"]["live_opl_storage_policy_takeover_required"] = False
