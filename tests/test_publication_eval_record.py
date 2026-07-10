from __future__ import annotations

from copy import deepcopy

import pytest

from med_autoscience.publication_eval_record import PublicationEvalRecord


def _payload() -> dict:
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::study::quest::2026-04-05T06:00:00+00:00",
        "study_id": "study",
        "quest_id": "quest",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": "/study/charter.json",
            "charter_id": "charter::study::v1",
            "publication_objective": "bounded clinical claim",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": "/runtime/escalation.json",
            "main_result_ref": "/runtime/main_result.json",
        },
        "delivery_context_refs": {
            "paper_root_ref": "/study/paper",
            "submission_minimal_ref": "/study/paper/submission_manifest.json",
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "One bounded repair remains.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-1",
                "gap_type": "evidence",
                "severity": "must_fix",
                "summary": "Evidence is incomplete.",
                "evidence_refs": ["/runtime/main_result.json"],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "action-1",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "Owner decision is required.",
                "evidence_refs": ["/runtime/escalation.json"],
                "requires_controller_decision": True,
            }
        ],
    }


def test_publication_eval_record_round_trips_sparse_canonical_payload() -> None:
    payload = _payload()

    serialized = PublicationEvalRecord.from_payload(payload).to_dict()

    assert {key: serialized[key] for key in payload} == payload
    assert serialized["assessment_provenance"]["owner"] == "mechanical_projection"
    assert serialized["assessment_provenance"]["ai_reviewer_required"] is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "authority_boundary",
            {
                "mutated_current_package": False,
                "mutated_submission_minimal": False,
                "mutated_publication_gate_conclusion": False,
                "mutated_medical_result_values": False,
                "quality_gate_relaxation": False,
                "publication_gate_allow_write_respected": True,
            },
        ),
        (
            "assessment_provenance",
            {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "source_refs": ["/study/paper/manuscript.md"],
                "ai_reviewer_required": False,
                "mechanical_projection_used_as_quality_authority": False,
            },
        ),
        (
            "reviewer_operating_system",
            {
                "contract_id": "medical_publication_ai_reviewer_os_v1",
                "input_bundle": {"manuscript": "/study/paper/manuscript.md"},
                "rubric_scores": {},
                "decision_matrix": [],
                "provenance_checks": {"assessment_owner": "ai_reviewer"},
                "route_back_decision": {"recommended_action": "route_back_same_line"},
            },
        ),
    ],
)
def test_publication_eval_record_round_trips_authority_fields(field: str, value: object) -> None:
    payload = _payload()
    payload[field] = value

    assert PublicationEvalRecord.from_payload(payload).to_dict()[field] == value


def test_publication_eval_record_preserves_human_gate_without_mutation_authority() -> None:
    payload = _payload()
    payload["gaps"][0]["gate_kind"] = "human_or_expert_gate"

    record = PublicationEvalRecord.from_payload(payload)

    assert record.gaps[0].gate_kind == "human_or_expert_gate"
    assert record.authority_boundary is None


def test_publication_eval_record_accepts_explicit_routeback_contract() -> None:
    payload = _payload()
    payload["recommended_actions"][0].update(
        action_type="route_back_same_line",
        route_target="write",
        route_key_question="Which claim needs repair?",
        route_rationale="Repair the same paper line.",
    )

    action = PublicationEvalRecord.from_payload(payload).recommended_actions[0]

    assert (action.action_type, action.route_target) == ("route_back_same_line", "write")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda payload: payload.pop("verdict"),
            "publication eval record payload missing verdict",
        ),
        (
            lambda payload: payload["recommended_actions"][0].update(requires_controller_decision=False),
            "requires_controller_decision must be true",
        ),
        (
            lambda payload: payload["recommended_actions"][0].update(action_type="route_back_same_line"),
            "route_target must be non-empty",
        ),
        (
            lambda payload: payload["recommended_actions"][0].update(
                mutation={"op": "write", "target": "runtime"}
            ),
            "payload contains unknown fields: mutation",
        ),
        (
            lambda payload: payload["verdict"].update(overall_verdict="ready_for_promotion"),
            "overall_verdict must be one of",
        ),
        (
            lambda payload: payload["charter_context_ref"].update(study_id="study"),
            "charter context ref payload contains unknown fields: study_id",
        ),
        (
            lambda payload: payload["runtime_context_refs"].update(
                runtime_escalation_ref={"artifact_path": "/runtime/escalation.json"}
            ),
            "runtime_context_refs value must be a ref string",
        ),
        (
            lambda payload: payload["runtime_context_refs"].update(
                unexpected_authority_ref="/runtime/unexpected-authority.json"
            ),
            "runtime_context_refs contains unexpected ref key unexpected_authority_ref",
        ),
        (
            lambda payload: payload.update(
                authority_boundary={"mutated_current_package": 1}
            ),
            "authority_boundary mutated_current_package must be bool",
        ),
    ],
)
def test_publication_eval_record_fails_closed_on_authority_leaks(mutation, message: str) -> None:
    payload = deepcopy(_payload())
    mutation(payload)

    with pytest.raises((TypeError, ValueError), match=message):
        PublicationEvalRecord.from_payload(payload)


def test_publication_eval_record_normalizes_ref_whitespace_without_expanding_authority() -> None:
    payload = _payload()
    payload["runtime_context_refs"] = {
        " runtime_escalation_ref ": " /runtime/escalation.json ",
        "main_result_ref": " /runtime/main_result.json ",
    }
    payload["delivery_context_refs"] = {
        "paper_root_ref": " /study/paper ",
        " submission_minimal_ref ": " /study/paper/submission_manifest.json ",
    }

    record = PublicationEvalRecord.from_payload(payload)

    assert record.runtime_context_refs == {
        "runtime_escalation_ref": "/runtime/escalation.json",
        "main_result_ref": "/runtime/main_result.json",
    }
    assert record.delivery_context_refs == {
        "paper_root_ref": "/study/paper",
        "submission_minimal_ref": "/study/paper/submission_manifest.json",
    }
    assert record.authority_boundary is None


@pytest.mark.parametrize(
    ("field", "missing_key"),
    [
        ("runtime_context_refs", "runtime_escalation_ref"),
        ("runtime_context_refs", "main_result_ref"),
        ("delivery_context_refs", "paper_root_ref"),
        ("delivery_context_refs", "submission_minimal_ref"),
    ],
)
def test_publication_eval_record_requires_exact_runtime_and_delivery_refs(
    field: str,
    missing_key: str,
) -> None:
    payload = _payload()
    payload[field].pop(missing_key)

    with pytest.raises(ValueError, match=f"{field} must include {missing_key}"):
        PublicationEvalRecord.from_payload(payload)
