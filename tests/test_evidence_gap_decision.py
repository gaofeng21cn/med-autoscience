from __future__ import annotations

import json


def test_authority_gate_is_hard_and_materializes_typed_blocker() -> None:
    from med_autoscience.evidence_gap_decision import (
        can_continue_current_action,
        classify_evidence_gap,
        is_hard_gate,
        materialize_typed_blocker_if_required,
    )

    decision = classify_evidence_gap(
        surface_kind="opl_stage_run_currentness",
        missing_ref_family="StageRun currentness provider authorization",
        identity={"study_id": "DM003", "quest_id": "quest-1", "active_run_id": "run-1"},
        evidence_refs=["runtime/status.json"],
        diagnostic_refs=["artifacts/diagnostics/currentness.json"],
    )
    payload = decision.to_payload()

    assert payload["surface_kind"] == "mas_evidence_gap_decision"
    assert payload["source_surface_kind"] == "opl_stage_run_currentness"
    assert payload["gap_class"] == "authority_gate"
    assert payload["severity"] == "hard_gate"
    assert payload["current_action_can_continue"] is False
    assert is_hard_gate(decision) is True
    assert can_continue_current_action(payload) is False
    assert "continue_current_action" not in payload["allowed_next_actions"]
    assert "paper_progress" in payload["forbidden_claims"]
    assert payload["claim_boundary"]["paper_progress_claim_allowed"] is False
    assert payload["identity"]["study_id"] == "DM003"
    json.dumps(payload)

    blocker = materialize_typed_blocker_if_required(decision)
    assert blocker is not None
    assert blocker["surface_kind"] == "mas_evidence_gap_typed_blocker"
    assert blocker["gap_class"] == "authority_gate"
    assert blocker["write_permitted"] is False
    assert blocker["required_owner_surface"] == "mas_authority_surface"


def test_soft_quality_gap_can_continue_without_typed_blocker_but_cannot_claim_progress() -> None:
    from med_autoscience.evidence_gap_decision import (
        can_continue_current_action,
        classify_evidence_gap,
        is_hard_gate,
        materialize_typed_blocker_if_required,
    )

    decision = classify_evidence_gap(
        surface_kind="reviewer_polish",
        missing_ref_family="reviewer polish structure non-hard concern",
        identity={"study_id": "DM003"},
    )
    payload = decision.to_payload()

    assert payload["gap_class"] == "soft_quality_gap"
    assert payload["severity"] == "soft"
    assert payload["current_action_can_continue"] is True
    assert "continue_current_action" in payload["allowed_next_actions"]
    assert "paper_progress" in payload["forbidden_claims"]
    assert payload["claim_boundary"]["paper_progress_claim_allowed"] is False
    assert is_hard_gate(payload) is False
    assert can_continue_current_action(decision) is True
    assert materialize_typed_blocker_if_required(payload) is None


def test_all_nonblocking_gap_classes_continue_but_forbid_high_order_claims() -> None:
    from med_autoscience.evidence_gap_decision import classify_missing_ref_family

    cases = {
        "safe non-critical bibliography helper ref": "proceed_with_assumption",
        "telemetry token cost trace report freshness": "observability_backlog",
        "production soak direct-hosted parity live readiness tail": "evidence_tail",
    }

    for missing_ref_family, expected_class in cases.items():
        decision = classify_missing_ref_family(
            missing_ref_family,
            surface_kind="evidence_ref",
            identity={"study_id": "DM003"},
        )
        payload = decision.to_payload()
        assert payload["gap_class"] == expected_class
        assert payload["current_action_can_continue"] is True
        assert "continue_current_action" in payload["allowed_next_actions"]
        assert "paper_progress" in payload["forbidden_claims"]
        assert payload["claim_boundary"]["publication_readiness_claim_allowed"] is False


def test_merge_and_summarize_count_gap_classes_and_hard_gates() -> None:
    from med_autoscience.evidence_gap_decision import (
        classify_missing_ref_family,
        merge_gap_decisions,
        summarize_gap_decisions,
    )

    authority = classify_missing_ref_family("forbidden-write owner route", surface_kind="authority")
    tail = classify_missing_ref_family("live-readiness tail", surface_kind="runtime_tail")
    soft = classify_missing_ref_family("reviewer structure concern", surface_kind="review")

    merged = merge_gap_decisions([authority, tail], [soft.to_payload()])
    summary = summarize_gap_decisions(merged)

    assert len(merged) == 3
    assert summary["total_count"] == 3
    assert summary["hard_gate_count"] == 1
    assert summary["current_action_can_continue"] is False
    assert summary["counts_by_gap_class"] == {
        "authority_gate": 1,
        "evidence_tail": 1,
        "soft_quality_gap": 1,
    }
    assert "paper_progress" in summary["forbidden_claims"]
    assert summary["claim_boundary"]["paper_progress_claim_allowed"] is False
