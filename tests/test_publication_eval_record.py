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
    expected_payload = {
        **payload,
        "assessment_provenance": {
            "owner": "mechanical_projection",
            "source_kind": "legacy_publication_eval_projection",
            "policy_id": "publication_gate_projection_v1",
            "source_refs": [
                payload["charter_context_ref"]["ref"],
                payload["runtime_context_refs"]["runtime_escalation_ref"],
                payload["runtime_context_refs"]["main_result_ref"],
                payload["delivery_context_refs"]["paper_root_ref"],
                payload["delivery_context_refs"]["submission_minimal_ref"],
            ],
            "ai_reviewer_required": True,
        },
    }
    assert record.to_dict() == expected_payload


def test_publication_eval_record_quality_dimension_guidance_round_trips() -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload["quality_assessment"] = {
        "clinical_significance": {
            "status": "partial",
            "summary": "临床问题已冻结，但结果叙事还不够稳。",
            "evidence_refs": ["/tmp/workspace/studies/001-risk/artifacts/controller/study_charter.json"],
            "reviewer_reason": "当前结果表面还不足以支撑稳定临床结论。",
            "reviewer_revision_advice": "补齐临床解释段与结果对应关系，避免泛化结论。",
            "reviewer_next_round_focus": "检查临床 framing 与结果摘要是否逐条对齐。",
        },
        "evidence_strength": {
            "status": "blocked",
            "summary": "主证据链未放行。",
            "evidence_refs": ["/tmp/runtime/quests/quest-001/artifacts/results/main_result.json"],
            "reviewer_reason": "缺少可发布主锚点，证据链当前不完整。",
            "reviewer_revision_advice": "先修复主锚点缺失，再做 claim-to-evidence 对齐审阅。",
            "reviewer_next_round_focus": "优先确认主锚点与关键效应指标的可追溯性。",
        },
        "novelty_positioning": {
            "status": "underdefined",
            "summary": "创新性边界尚未结构化。",
            "evidence_refs": ["/tmp/workspace/studies/001-risk/artifacts/controller/study_charter.json"],
            "reviewer_reason": "charter 里缺少显式 follow-up questions 与解释目标锚点。",
            "reviewer_revision_advice": "明确科学问题边界并补齐解释目标合同。",
            "reviewer_next_round_focus": "检查 novelty framing 与稿件主结论是否一一对应。",
        },
        "human_review_readiness": {
            "status": "ready",
            "summary": "人工审阅包已就绪。",
            "evidence_refs": ["/tmp/workspace/studies/001-risk/paper/submission_minimal/submission_manifest.json"],
            "reviewer_reason": "给人读的 current package 与 submission_minimal 已对齐。",
            "reviewer_revision_advice": "保持当前结构并仅处理事实性勘误。",
            "reviewer_next_round_focus": "重点复核术语一致性与证据引用完整性。",
        },
    }

    record = module.PublicationEvalRecord.from_payload(payload)

    clinical = record.quality_assessment.clinical_significance
    assert clinical.reviewer_reason == "当前结果表面还不足以支撑稳定临床结论。"
    assert clinical.reviewer_revision_advice == "补齐临床解释段与结果对应关系，避免泛化结论。"
    assert clinical.reviewer_next_round_focus == "检查临床 framing 与结果摘要是否逐条对齐。"
    assert record.to_dict()["quality_assessment"] == payload["quality_assessment"]


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
    payload["recommended_actions"][0]["route_target"] = "write"
    payload["recommended_actions"][0]["route_key_question"] = "What is the narrowest manuscript repair needed to keep the current paper line honest?"
    payload["recommended_actions"][0]["route_rationale"] = (
        "The main claim line stays fixed; the next honest move is to repair the current paper-writing route."
    )

    record = module.PublicationEvalRecord.from_payload(payload)

    assert record.recommended_actions[0].action_type == "route_back_same_line"
    assert record.recommended_actions[0].route_target == "write"
    assert (
        record.recommended_actions[0].route_key_question
        == "What is the narrowest manuscript repair needed to keep the current paper line honest?"
    )
    assert record.to_dict()["recommended_actions"][0]["action_type"] == "route_back_same_line"
    assert record.to_dict()["recommended_actions"][0]["route_target"] == "write"


@pytest.mark.parametrize("action_type", ["continue_same_line", "route_back_same_line", "bounded_analysis"])
def test_publication_eval_record_requires_route_contract_for_same_line_actions(action_type: str) -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload["recommended_actions"][0]["action_type"] = action_type
    payload["recommended_actions"][0]["reason"] = "Same-line actions must say where they route and why."

    with pytest.raises(ValueError, match="publication eval recommended action route_target must be non-empty"):
        module.PublicationEvalRecord.from_payload(payload)


def test_publication_eval_record_rejects_route_contract_on_controller_return_action() -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload["recommended_actions"][0]["route_target"] = "write"
    payload["recommended_actions"][0]["route_key_question"] = "Should we keep writing?"
    payload["recommended_actions"][0]["route_rationale"] = "Extra route data is not allowed on controller-return actions."

    with pytest.raises(
        ValueError,
        match="publication eval recommended action route_target is only allowed for same-line actions",
    ):
        module.PublicationEvalRecord.from_payload(payload)


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
