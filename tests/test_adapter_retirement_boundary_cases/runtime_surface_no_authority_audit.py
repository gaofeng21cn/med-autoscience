from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = REPO_ROOT / "contracts/runtime/mas-runtime-surface-retirement-inventory.json"


def _inventory() -> dict:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def test_runtime_surface_retirement_no_authority_audit_blocks_active_caller_regression() -> None:
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    audit = retirement.audit_runtime_surface_retirement_inventory(_inventory())

    assert audit["surface_kind"] == "mas_runtime_surface_retirement_no_authority_audit"
    assert audit["status"] == "passed"
    assert audit["inventory_contract_valid"] is True
    assert audit["repo_no_authority_guard_satisfied"] is True
    assert audit["retired_surface_count"] == 12
    assert audit["retained_tail_count"] == 6
    assert audit["physical_delete_allowed"] is False
    assert audit["live_runtime_readiness_claim_allowed"] is False
    assert audit["completion_claim_allowed"] is False
    assert audit["violations"] == []


def test_runtime_surface_retirement_guard_rejects_resurrection_and_authority() -> None:
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    inventory = copy.deepcopy(_inventory())
    inventory["surfaces"].append(
        {
            "surface_id": "domain_diagnostic_obligation_actuator",
            "disposition": "retained_read_only_projection",
            "replacement_ref": "opl:recovery-obligation-store",
            "tombstone_ref": None,
            "retained_mas_role": "diagnostic_projection",
            "mas_runtime_authority": True,
        }
    )

    violations = retirement.validate_runtime_surface_retirement_inventory(inventory)
    reasons = {
        (item["surface_id"], item["reason"])
        for item in violations
    }
    assert (
        "domain_diagnostic_obligation_actuator",
        "forbidden_surface_resurrected",
    ) in reasons
    assert (
        "domain_diagnostic_obligation_actuator",
        "mas_runtime_authority_not_false",
    ) in reasons
