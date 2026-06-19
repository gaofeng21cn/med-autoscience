from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_TAIL_OWNERS = {
    "agent_tool_arsenal_scientific_capability_registry": "one-person-lab Capability Runtime owner",
    "domain_health_diagnostic_obligation_actuator": (
        "one-person-lab RecoveryObligationStore / SupervisorDecisionEngine owner"
    ),
    "domain_owner_action_dispatch": "one-person-lab StageRun / execution authorization owner",
    "progress_portal_study_workbench_overview_action_projection": (
        "one-person-lab Workbench Shell owner"
    ),
    "runtime_health_kernel": "one-person-lab Observability / RouteReconciler owner",
    "runtime_lifecycle_payload_retention": "one-person-lab runtime lifecycle / retention owner",
    "runtime_storage_maintenance": "one-person-lab runtime storage / restore-retention owner",
}


def _inventory() -> dict:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    return json.loads(inventory_path.read_text(encoding="utf-8"))


def test_live_tail_evidence_gate_names_owner_and_does_not_block_repo_source_retirement() -> None:
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )

    audit = retirement.audit_runtime_surface_retirement_inventory(_inventory())
    tails = {
        item["surface_id"]: item
        for item in audit["completion_evidence_layers"]["live_soak_or_no_active_caller"][
            "open_surface_tails"
        ]
    }

    assert set(tails) == set(EXPECTED_TAIL_OWNERS)
    assert audit["repo_source_retirement_completion"]["completion_claim_allowed"] is True
    assert audit["live_runtime_readiness_completion"]["completion_claim_allowed"] is False

    for surface_id, expected_owner in EXPECTED_TAIL_OWNERS.items():
        tail = tails[surface_id]
        gate = tail["evidence_gate"]

        assert gate["gate_kind"] == "live_runtime_readiness_tail"
        assert gate["next_owner"] == expected_owner
        assert gate["repo_source_retirement_blocked"] is False
        assert gate["live_runtime_readiness_claim_allowed"] is False
        assert gate["missing_evidence_status"] == "evidence_required"
        assert gate["acceptable_evidence_ref_families"] == tail["required_ref_families"]
        assert gate["forbidden_evidence_substitutes"] == tail[
            "forbidden_completion_interpretations"
        ]
        assert gate["acceptable_evidence_ref_families"]
        assert gate["forbidden_evidence_substitutes"]

