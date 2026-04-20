from __future__ import annotations

import importlib

import pytest


MODULE_NAME = "med_autoscience.publication_eval_record"


def _load_module() -> object:
    return importlib.import_module(MODULE_NAME)


def _minimal_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": "/tmp/workspace/studies/001-risk/artifacts/controller/study_charter.json",
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
            "main_result_ref": "/tmp/runtime/quests/quest-001/artifacts/results/main_result.json",
        },
        "delivery_context_refs": {
            "paper_root_ref": "/tmp/workspace/studies/001-risk/paper",
            "submission_minimal_ref": "/tmp/workspace/studies/001-risk/paper/submission_minimal/submission_manifest.json",
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Primary claim still lacks external validation support.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "evidence",
                "severity": "must_fix",
                "summary": "External validation cohort is still missing.",
                "evidence_refs": [
                    "/tmp/runtime/quests/quest-001/artifacts/results/main_result.json"
                ],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "action-001",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "Controller must decide whether to invest in external validation.",
                "evidence_refs": [
                    "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json"
                ],
                "requires_controller_decision": True,
            }
        ],
    }


def test_publication_eval_record_from_payload_round_trips_minimal_shape() -> None:
    module = _load_module()
    payload = _minimal_payload()

    record = module.PublicationEvalRecord.from_payload(payload)

    assert record == module.PublicationEvalRecord(
        schema_version=1,
        eval_id="publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-04-05T06:00:00+00:00",
        evaluation_scope="publication",
        charter_context_ref=module.PublicationEvalCharterContextRef(
            ref="/tmp/workspace/studies/001-risk/artifacts/controller/study_charter.json",
            charter_id="charter::001-risk::v1",
            publication_objective="risk stratification external validation",
        ),
        runtime_context_refs={
            "runtime_escalation_ref": "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
            "main_result_ref": "/tmp/runtime/quests/quest-001/artifacts/results/main_result.json",
        },
        delivery_context_refs={
            "paper_root_ref": "/tmp/workspace/studies/001-risk/paper",
            "submission_minimal_ref": "/tmp/workspace/studies/001-risk/paper/submission_minimal/submission_manifest.json",
        },
        verdict=module.PublicationEvalVerdict(
            overall_verdict="blocked",
            primary_claim_status="partial",
            summary="Primary claim still lacks external validation support.",
            stop_loss_pressure="watch",
        ),
        gaps=(
            module.PublicationEvalGap(
                gap_id="gap-001",
                gap_type="evidence",
                severity="must_fix",
                summary="External validation cohort is still missing.",
                evidence_refs=(
                    "/tmp/runtime/quests/quest-001/artifacts/results/main_result.json",
                ),
            ),
        ),
        recommended_actions=(
            module.PublicationEvalRecommendedAction(
                action_id="action-001",
                action_type="return_to_controller",
                priority="now",
                reason="Controller must decide whether to invest in external validation.",
                evidence_refs=(
                    "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
                ),
                requires_controller_decision=True,
            ),
        ),
    )
    assert record.to_dict() == payload


@pytest.mark.parametrize("missing_field", ["verdict", "gaps", "recommended_actions"])
def test_publication_eval_record_rejects_missing_required_fields(missing_field: str) -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload.pop(missing_field)

    with pytest.raises(ValueError, match=f"publication eval record payload missing {missing_field}"):
        module.PublicationEvalRecord.from_payload(payload)


@pytest.mark.parametrize(
    "missing_field",
    ["schema_version", "eval_id", "study_id", "quest_id", "emitted_at", "evaluation_scope"],
)
def test_publication_eval_record_rejects_missing_required_metadata(missing_field: str) -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload.pop(missing_field)

    with pytest.raises(ValueError, match=f"publication eval record payload missing {missing_field}"):
        module.PublicationEvalRecord.from_payload(payload)


def test_publication_eval_record_requires_controller_decision_true() -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload["recommended_actions"][0]["requires_controller_decision"] = False

    with pytest.raises(ValueError, match="publication eval recommended action requires_controller_decision must be true"):
        module.PublicationEvalRecord.from_payload(payload)


def test_publication_eval_record_allows_route_back_same_line_recommended_action() -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload["recommended_actions"][0]["action_type"] = "route_back_same_line"
    payload["recommended_actions"][0]["reason"] = (
        "Route back to the same core study line to repair ordinary publication quality gaps."
    )

    record = module.PublicationEvalRecord.from_payload(payload)

    assert record.recommended_actions[0].action_type == "route_back_same_line"
    assert record.to_dict()["recommended_actions"][0]["action_type"] == "route_back_same_line"


def test_publication_eval_record_rejects_promotion_in_overall_verdict() -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload["verdict"]["overall_verdict"] = "ready_for_promotion"

    with pytest.raises(ValueError, match="publication eval verdict overall_verdict must be one of"):
        module.PublicationEvalRecord.from_payload(payload)


@pytest.mark.parametrize("extra_field", ["mutation", "runtime_side_effect_result"])
def test_publication_eval_record_rejects_mutation_shaped_recommended_action_fields(extra_field: str) -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload["recommended_actions"][0][extra_field] = {"op": "mutate", "target": "runtime"}

    with pytest.raises(
        ValueError,
        match=f"publication eval recommended action payload contains unknown fields: {extra_field}",
    ):
        module.PublicationEvalRecord.from_payload(payload)


@pytest.mark.parametrize(
    ("field_name", "field_value", "message"),
    [
        (
            "charter_context_ref",
            {
                "ref": "/tmp/workspace/studies/001-risk/artifacts/controller/study_charter.json",
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "risk stratification external validation",
                "study_id": "001-risk",
            },
            "publication eval charter context ref payload contains unknown fields: study_id",
        ),
        (
            "runtime_context_refs",
            {
                "runtime_escalation_ref": {
                    "record_id": "runtime-escalation::001-risk::quest-001",
                    "artifact_path": "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
                    "summary_ref": "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record_summary.json",
                }
            },
            "publication eval record runtime_context_refs value must be a ref string",
        ),
        (
            "delivery_context_refs",
            {
                "submission_minimal_ref": {
                    "artifact_path": "/tmp/workspace/studies/001-risk/paper/submission_minimal/submission_manifest.json",
                    "status": "draft",
                }
            },
            "publication eval record delivery_context_refs value must be a ref string",
        ),
    ],
)
def test_publication_eval_record_rejects_full_authority_payloads(
    field_name: str,
    field_value: object,
    message: str,
) -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload[field_name] = field_value

    with pytest.raises((TypeError, ValueError), match=message):
        module.PublicationEvalRecord.from_payload(payload)


@pytest.mark.parametrize(
    ("field_name", "replacement", "message"),
    [
        (
            "runtime_context_refs",
            {
                "unexpected_runtime_ref": "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
                "main_result_ref": "/tmp/runtime/quests/quest-001/artifacts/results/main_result.json",
            },
            "publication eval record runtime_context_refs must include runtime_escalation_ref",
        ),
        (
            "runtime_context_refs",
            {
                "runtime_escalation_ref": "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
                "unexpected_runtime_ref": "/tmp/runtime/quests/quest-001/artifacts/results/main_result.json",
            },
            "publication eval record runtime_context_refs must include main_result_ref",
        ),
        (
            "delivery_context_refs",
            {
                "unexpected_delivery_ref": "/tmp/workspace/studies/001-risk/paper",
                "submission_minimal_ref": "/tmp/workspace/studies/001-risk/paper/submission_minimal/submission_manifest.json",
            },
            "publication eval record delivery_context_refs must include paper_root_ref",
        ),
        (
            "delivery_context_refs",
            {
                "paper_root_ref": "/tmp/workspace/studies/001-risk/paper",
                "unexpected_delivery_ref": "/tmp/workspace/studies/001-risk/paper/submission_minimal/submission_manifest.json",
            },
            "publication eval record delivery_context_refs must include submission_minimal_ref",
        ),
    ],
)
def test_publication_eval_record_requires_minimal_runtime_and_delivery_ref_keys(
    field_name: str,
    replacement: dict[str, str],
    message: str,
) -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload[field_name] = replacement

    with pytest.raises(ValueError, match=message):
        module.PublicationEvalRecord.from_payload(payload)


@pytest.mark.parametrize(
    ("field_name", "replacement", "message"),
    [
        (
            "runtime_context_refs",
            {
                "runtime_escalation_ref": "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
                "main_result_ref": "/tmp/runtime/quests/quest-001/artifacts/results/main_result.json",
                "controller_override_ref": "/tmp/workspace/studies/001-risk/artifacts/controller/override.json",
            },
            "publication eval record runtime_context_refs contains unexpected ref key controller_override_ref",
        ),
        (
            "delivery_context_refs",
            {
                "paper_root_ref": "/tmp/workspace/studies/001-risk/paper",
                "submission_minimal_ref": "/tmp/workspace/studies/001-risk/paper/submission_minimal/submission_manifest.json",
                "promotion_decision_ref": "/tmp/workspace/studies/001-risk/artifacts/controller/promotion_decision.json",
            },
            "publication eval record delivery_context_refs contains unexpected ref key promotion_decision_ref",
        ),
    ],
)
def test_publication_eval_record_rejects_extra_runtime_and_delivery_ref_keys(
    field_name: str,
    replacement: dict[str, str],
    message: str,
) -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload[field_name] = replacement

    with pytest.raises(ValueError, match=message):
        module.PublicationEvalRecord.from_payload(payload)
