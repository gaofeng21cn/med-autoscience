from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "contracts" / "schemas" / "evidence-gap-decision.schema.json"
POLICY_PATH = REPO_ROOT / "contracts" / "evidence-gap-decision-policy.json"


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_schema_shape(payload: dict[str, object]) -> None:
    schema = _json(SCHEMA_PATH)
    required = schema["required"]
    properties = schema["properties"]
    assert isinstance(required, list)
    assert isinstance(properties, dict)
    assert set(payload) <= set(properties)
    for field in required:
        assert field in payload, field


def test_authority_gate_payload_matches_contract_and_materializes_typed_blocker() -> None:
    from med_autoscience.evidence_gap_decision import (
        can_continue_current_action,
        classify_evidence_gap,
        is_hard_gate,
        materialize_typed_blocker_if_required,
    )

    decision = classify_evidence_gap(
        surface_kind="opl_stage_run_currentness",
        missing_ref_family="StageRun currentness provider authorization",
        identity={
            "study_id": "DM003",
            "quest_id": "quest-1",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        },
        evidence_refs=["runtime/status.json"],
        diagnostic_refs=["artifacts/diagnostics/currentness.json"],
    )
    payload = decision.to_payload()

    _assert_schema_shape(payload)
    assert payload["surface_kind"] == "mas_evidence_gap_decision"
    assert payload["owner"] == "MedAutoScience"
    assert payload["gap_class"] == "authority_gate"
    assert payload["decision"] == "materialize_typed_blocker"
    assert payload["typed_blocker_eligibility"] is True
    assert payload["typed_blocker_policy"] == {
        "typed_blocker_countable": True,
        "materialization_allowed": True,
        "materialization_reason": "authority_gate",
        "typed_blocker_ref": payload["typed_blocker_policy"]["typed_blocker_ref"],
    }
    assert payload["current_owner_delta_identity"] == {
        "study_id": "DM003",
        "quest_id": "quest-1",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
    }
    assert payload["evidence_refs"] == ["runtime/status.json"]
    assert "severity" not in payload
    assert "current_action_can_continue" not in payload
    assert "allowed_next_actions" not in payload
    assert is_hard_gate(decision) is True
    assert can_continue_current_action(payload) is False

    blocker = materialize_typed_blocker_if_required(decision)
    assert blocker is not None
    assert blocker["surface_kind"] == "mas_evidence_gap_typed_blocker"
    assert blocker["gap_class"] == "authority_gate"
    assert blocker["write_permitted"] is False
    assert blocker["required_owner_surface"] == "mas_authority_surface"
    assert blocker["typed_blocker_policy"]["materialization_reason"] == "authority_gate"


def test_soft_quality_gap_can_continue_without_typed_blocker() -> None:
    from med_autoscience.evidence_gap_decision import (
        can_continue_current_action,
        classify_evidence_gap,
        is_hard_gate,
        materialize_typed_blocker_if_required,
    )

    decision = classify_evidence_gap(
        surface_kind="reviewer_polish",
        missing_ref_family="reviewer polish structure non-hard concern",
        identity={
            "study_id": "DM003",
            "work_unit_id": "review_round",
            "work_unit_fingerprint": "review::round-2",
        },
    )
    payload = decision.to_payload()

    _assert_schema_shape(payload)
    assert payload["gap_class"] == "soft_quality_gap"
    assert payload["decision"] == "continue_with_quality_followup"
    assert payload["typed_blocker_eligibility"] is False
    assert payload["typed_blocker_policy"] == {
        "typed_blocker_countable": False,
        "materialization_allowed": False,
        "materialization_reason": "not_allowed",
        "typed_blocker_ref": None,
    }
    assert payload["followup_work_order_ref"].startswith("work_order_ref:")
    assert decision.current_action_can_continue is True
    assert "continue_current_action" in decision.allowed_next_actions
    assert is_hard_gate(payload) is False
    assert can_continue_current_action(decision) is True
    assert materialize_typed_blocker_if_required(payload) is None


def test_safe_missing_ref_proceeds_with_recorded_assumption() -> None:
    from med_autoscience.evidence_gap_decision import classify_missing_ref_family

    decision = classify_missing_ref_family(
        "safe non-critical bibliography helper ref",
        surface_kind="source_reference_note",
        identity={
            "study_id": "DM003",
            "work_unit_id": "bibliography_check",
            "work_unit_fingerprint": "source-reference::safe-helper",
        },
    )
    payload = decision.to_payload()

    _assert_schema_shape(payload)
    assert payload["gap_class"] == "proceed_with_assumption"
    assert payload["decision"] == "proceed_with_recorded_assumption"
    assert payload["assumption_ref"].startswith("assumption_ref:")
    assert payload["typed_blocker_eligibility"] is False
    assert decision.severity == "assumption"
    assert decision.current_action_can_continue is True


def test_evidence_tail_blocks_readiness_claim_but_not_current_action() -> None:
    from med_autoscience.evidence_gap_decision import classify_evidence_gap

    decision = classify_evidence_gap(
        surface_kind="production_soak",
        missing_ref_family="production soak direct-hosted parity live-readiness tail",
        identity={
            "study_id": "DM003",
            "work_unit_id": "runtime_tail",
            "work_unit_fingerprint": "tail::live-readiness",
        },
    )
    payload = decision.to_payload()

    _assert_schema_shape(payload)
    assert payload["gap_class"] == "evidence_tail"
    assert payload["decision"] == "record_evidence_tail"
    assert payload["typed_blocker_eligibility"] is False
    assert payload["completion_claim_allowed"] is False
    assert payload["claim_boundary"]["live_runtime_readiness_claim_allowed"] is False
    assert "live_runtime_ready" in payload["forbidden_claim_terms"]
    assert decision.current_action_can_continue is True


def test_merge_and_summarize_count_gap_classes_and_hard_gates() -> None:
    from med_autoscience.evidence_gap_decision import (
        classify_missing_ref_family,
        merge_gap_decisions,
        summarize_gap_decisions,
    )

    authority = classify_missing_ref_family(
        "forbidden-write owner route",
        surface_kind="authority",
        identity={
            "study_id": "DM003",
            "work_unit_id": "owner_route",
            "work_unit_fingerprint": "owner-route::forbidden-write",
        },
    )
    tail = classify_missing_ref_family(
        "live-readiness tail",
        surface_kind="runtime_tail",
        identity={
            "study_id": "DM003",
            "work_unit_id": "runtime_tail",
            "work_unit_fingerprint": "runtime-tail::live",
        },
    )
    soft = classify_missing_ref_family(
        "reviewer structure concern",
        surface_kind="review",
        identity={
            "study_id": "DM003",
            "work_unit_id": "review_round",
            "work_unit_fingerprint": "review::structure",
        },
    )

    merged = merge_gap_decisions([authority, tail], [soft.to_payload()])
    summary = summarize_gap_decisions(merged)

    assert len(merged) == 3
    assert summary["total_count"] == 3
    assert summary["hard_gate_count"] == 1
    assert summary["typed_blocker_countable_count"] == 1
    assert summary["current_action_can_continue"] is False
    assert summary["counts_by_gap_class"] == {
        "authority_gate": 1,
        "evidence_tail": 1,
        "soft_quality_gap": 1,
    }
    assert summary["counts_by_severity"] == {
        "hard_gate": 1,
        "soft": 1,
        "tail": 1,
    }
    assert "live_runtime_ready" in summary["forbidden_claim_terms"]


def test_gap_classes_match_policy_typed_blocker_rules() -> None:
    from med_autoscience.evidence_gap_decision import classify_missing_ref_family

    policy = _json(POLICY_PATH)
    materialization = policy["typed_blocker_materialization_policy"]
    assert isinstance(materialization, dict)
    hard_classes = set(materialization["typed_blocker_countable_gap_classes"])
    soft_classes = set(materialization["forbidden_gap_classes_for_typed_blocker_count"])

    examples = {
        "authority_gate": ("forbidden-write owner route", "authority"),
        "human_gate": ("human submission approval", "submission"),
        "proceed_with_assumption": ("safe non-critical helper ref", "source_reference_note"),
        "soft_quality_gap": ("reviewer polish structure non-hard concern", "review"),
        "observability_backlog": ("telemetry token cost trace", "telemetry"),
        "evidence_tail": ("live-readiness tail", "runtime_tail"),
    }
    for gap_class, (missing_ref_family, surface_kind) in examples.items():
        decision = classify_missing_ref_family(
            missing_ref_family,
            surface_kind=surface_kind,
            identity={
                "study_id": "DM003",
                "work_unit_id": f"{gap_class}_unit",
                "work_unit_fingerprint": f"{gap_class}::fingerprint",
            },
        )
        payload = decision.to_payload()
        assert payload["gap_class"] == gap_class
        if gap_class in hard_classes:
            assert payload["typed_blocker_eligibility"] is True
            assert payload["typed_blocker_policy"]["typed_blocker_countable"] is True
        if gap_class in soft_classes:
            assert payload["typed_blocker_eligibility"] is False
            assert payload["typed_blocker_policy"]["typed_blocker_countable"] is False
