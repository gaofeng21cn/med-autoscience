from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = REPO_ROOT / "contracts" / "paper_progress_transition_runtime_completion_audit.json"
REPLAY_STATUS_PATH = REPO_ROOT / "contracts" / "paper_progress_replay_live_evidence_status.json"
RETIREMENT_INVENTORY_PATH = (
    REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
)


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_completion_audit_limits_done_claim_to_repo_source_control_plane() -> None:
    audit = _load(AUDIT_PATH)

    assert audit["surface_kind"] == "paper_progress_transition_runtime_completion_audit"
    assert audit["version"] == "paper-progress-transition-runtime-completion-audit.v2"
    assert audit["state"] == "active_evidence_audit"
    assert audit["overall"] == {
        "status": "partial",
        "goal_complete": False,
        "completion_claim_allowed": False,
        "reason": "repo_source_control_plane_closed_live_runtime_and_paper_acceptance_open",
    }
    assert audit["blueprint_l0_l7_functional_acceptance"] == {
        "status": "done",
        "completion_percent": 100,
        "claim_scope": "repo_source_control_plane_only",
        "live_acceptance_status": "evidence_required",
        "overall_completion_claim_allowed": False,
    }
    assert audit["repo_source_retirement"]["status"] == "done"
    assert audit["repo_source_retirement"]["completion_claim_allowed"] is True
    assert audit["repo_source_retirement"]["local_state_index_persistence"] == "absent"


def test_completion_audit_preserves_domain_authority_and_opl_ownership() -> None:
    audit = _load(AUDIT_PATH)
    inventory = _load(RETIREMENT_INVENTORY_PATH)

    assert set(audit["authority_invariants"]["mas_retains"]) == set(
        inventory["authority_boundary"]["mas_retains"]
    )
    assert set(audit["authority_invariants"]["opl_owns"]) == set(
        inventory["authority_boundary"]["opl_owns"]
    )
    assert audit["authority_invariants"][
        "stage_outcome_requires_progress_receipt_owner_answer_or_hard_stop"
    ] is True
    assert audit["authority_invariants"][
        "owner_receipt_required_for_quality_publication_or_submission_claim"
    ] is True
    assert audit["authority_invariants"]["same_identity_runtime_readback_required"] is True
    assert audit["authority_invariants"]["request_only_projection_is_completion"] is False
    assert set(audit["repo_source_retirement"]["required_retained_surface_ids"]) == set(
        surface["surface_id"]
        for surface in inventory["surfaces"]
        if surface["disposition"] != "physically_retired"
    )


def test_completion_audit_keeps_replay_and_live_evidence_separate() -> None:
    audit = _load(AUDIT_PATH)
    replay_status = _load(REPLAY_STATUS_PATH)
    live = audit["live_runtime_readiness"]

    assert live["status"] == "evidence_required"
    assert live["completion_claim_allowed"] is False
    assert live["required_runtime_readback_sections"] == [
        "identity",
        "causality",
        "authority_boundary",
        "exactly_one_outcome",
        "projection_metadata",
    ]
    assert replay_status["replay_to_live_separation_gate"]["status"] == "evidence_tail_open"
    assert "fresh DM002/DM003 paper-line accepted outcome" in live["open_evidence_tails"]
    assert "source_adapter_manifest_as_live_state_index_readback" in audit[
        "forbidden_completion_interpretations"
    ]


def test_completion_audit_verification_refs_exist() -> None:
    audit = _load(AUDIT_PATH)

    missing = [
        ref
        for ref in audit["verification_refs"]
        if not (REPO_ROOT / ref).exists()
    ]

    assert missing == []
    assert not (
        REPO_ROOT
        / "src"
        / "med_autoscience"
        / "runtime_protocol"
        / "domain_authority_refs_index.py"
    ).exists()
