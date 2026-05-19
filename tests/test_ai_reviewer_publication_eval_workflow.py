from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _refs(study_root: Path) -> dict[str, str]:
    return {
        "manuscript": str(study_root / "paper" / "manuscript.md"),
        "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(study_root / "artifacts" / "publication_gate" / "latest.json"),
    }


def _relative_refs() -> dict[str, str]:
    return {
        "manuscript": "paper/manuscript.md",
        "study_charter": "artifacts/controller/study_charter.json",
        "evidence_ledger": "paper/evidence_ledger.json",
        "review_ledger": "paper/review/review_ledger.json",
        "medical_manuscript_blueprint": "paper/medical_manuscript_blueprint.json",
        "claim_evidence_map": "paper/claim_evidence_map.json",
        "medical_prose_review": "artifacts/publication_eval/medical_prose_review.json",
        "publication_gate_projection": "artifacts/publication_gate/latest.json",
    }


def _quality_assessment(study_root: Path) -> dict[str, Any]:
    refs = _refs(study_root)
    return {
        "clinical_significance": {
            "status": "ready",
            "summary": "Clinical question is manuscript-safe.",
            "evidence_refs": [refs["study_charter"], refs["manuscript"]],
        },
        "evidence_strength": {
            "status": "ready",
            "summary": "Claim evidence is closed.",
            "evidence_refs": [refs["evidence_ledger"]],
        },
        "novelty_positioning": {
            "status": "ready",
            "summary": "Novelty boundary is explicit.",
            "evidence_refs": [refs["study_charter"]],
        },
        "medical_journal_prose_quality": {
            "status": "ready",
            "summary": "Medical prose review is clear.",
            "evidence_refs": [refs["medical_prose_review"]],
        },
        "human_review_readiness": {
            "status": "ready",
            "summary": "Review ledger is closed.",
            "evidence_refs": [refs["review_ledger"]],
        },
    }


def _reviewer_operating_system(study_root: Path) -> dict[str, Any]:
    refs = _refs(study_root)
    dimensions = (
        "clinical_significance",
        "evidence_strength",
        "novelty_positioning",
        "medical_journal_prose_quality",
        "human_review_readiness",
    )
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": refs,
        "rubric_scores": {
            dimension: {
                "status": "ready",
                "rationale": f"{dimension} is closed.",
                "evidence_refs": [refs["manuscript"]],
            }
            for dimension in dimensions
        },
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": "ready",
                "rationale": f"{dimension} is closed.",
            }
            for dimension in dimensions
        ],
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_digest": "sha256:" + "a" * 64,
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": "sha256:" + "c" * 64,
            },
            "current_package_freshness": {
                "status": "fresh",
                "source_eval_id": "publication-eval::001-risk::quest-001::2026-05-04T00:00:00+00:00",
            },
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "Medication coverage is based on recorded medication fields.",
                "impact_on_claim": "Treatment-gap language must remain documentation-aware.",
                "required_future_analysis_data_or_design": "Link pharmacy or insurance dispensing data.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": {
            "recommended_action": "continue_same_line",
            "rationale": "Proceed to first full draft.",
        },
    }


def _publication_eval_record(study_root: Path) -> dict[str, Any]:
    refs = _refs(study_root)
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-05-04T00:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-05-04T00:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": refs["study_charter"],
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "Submit a clinically restrained manuscript.",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "runtime" / "runtime_escalation_record.json"),
            "main_result_ref": str(study_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [refs["manuscript"], refs["evidence_ledger"], refs["review_ledger"]],
            "ai_reviewer_required": False,
        },
        "verdict": {
            "overall_verdict": "promising",
            "primary_claim_status": "supported",
            "summary": "AI reviewer closed publication-facing quality.",
            "stop_loss_pressure": "none",
        },
        "quality_assessment": _quality_assessment(study_root),
        "gaps": [
            {
                "gap_id": "gap-closed-001",
                "gap_type": "evidence",
                "severity": "optional",
                "summary": "No blocking evidence gap remains after AI reviewer closure.",
                "evidence_refs": [refs["evidence_ledger"]],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "continue-first-draft",
                "action_type": "continue_same_line",
                "priority": "next",
                "reason": "Proceed to first full draft.",
                "route_target": "write",
                "route_key_question": "Write the first full draft.",
                "route_rationale": "Reviewer OS trace is complete.",
                "evidence_refs": [refs["review_ledger"]],
                "requires_controller_decision": True,
            }
        ],
        "future_facing_limitations_plan": [
            {
                "limitation": "Medication coverage is based on recorded medication fields.",
                "impact_on_claim": "Treatment-gap language must remain documentation-aware.",
                "required_future_analysis_data_or_design": "Link pharmacy or insurance dispensing data.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
    }


def _write_ai_reviewer_currentness_inputs(
    study_root: Path,
    *,
    source_eval_id: str | None = None,
    prose_status: str = "ready",
    style_verdict: str = "clear",
    route_back_required: bool = False,
) -> None:
    refs = _refs(study_root)
    request_digest = "sha256:" + "a" * 64
    manuscript_digest = "sha256:" + "c" * 64
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    _write_json(
        request_path,
        {
            "surface": "medical_prose_review_request",
            "request_digest": request_digest,
            "manuscript": {"path": refs["manuscript"], "digest": manuscript_digest},
        },
    )
    _write_json(
        review_path,
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_ref": str(request_path),
                "request_digest": request_digest,
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": manuscript_digest,
            },
            "medical_journal_prose_quality": {
                "status": prose_status,
                "overall_style_verdict": style_verdict,
                "route_back_recommendation": {
                    "required": route_back_required,
                    "route_target": "write" if route_back_required else "none",
                    "reason": "Rewrite manuscript prose against the current evidence." if route_back_required else "",
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {
            "schema_version": 1,
            "status": "fresh",
            "source_eval_id": source_eval_id
            or "publication-eval::001-risk::quest-001::2026-05-04T00:00:00+00:00",
            "current_package_root": str(study_root / "manuscript" / "current_package"),
            "current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
        },
    )


def _write_relative_ai_reviewer_currentness_inputs(
    study_root: Path,
    *,
    source_eval_id: str | None = None,
) -> None:
    refs = _relative_refs()
    request_digest = "sha256:" + "a" * 64
    manuscript_digest = "sha256:" + "c" * 64
    request_ref = "artifacts/publication_eval/medical_prose_review_request.json"
    _write_json(
        study_root / request_ref,
        {
            "surface": "medical_prose_review_request",
            "request_digest": request_digest,
            "manuscript": {"path": refs["manuscript"], "digest": manuscript_digest},
        },
    )
    _write_json(
        study_root / refs["medical_prose_review"],
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_ref": request_ref,
                "request_digest": request_digest,
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": manuscript_digest,
            },
            "medical_journal_prose_quality": {
                "status": "ready",
                "overall_style_verdict": "clear",
                "route_back_recommendation": {"required": False, "route_target": "none"},
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {
            "schema_version": 1,
            "status": "fresh",
            "source_eval_id": source_eval_id
            or "publication-eval::001-risk::quest-001::2026-05-04T00:00:00+00:00",
            "current_package_root": "manuscript/current_package",
            "current_package_zip": "manuscript/current_package.zip",
        },
    )


def test_ai_reviewer_publication_eval_workflow_materializes_latest_with_reviewer_os_trace(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    _write_ai_reviewer_currentness_inputs(study_root)

    result = module.run_ai_reviewer_publication_eval_workflow(
        study_root=study_root,
        manuscript_ref=refs["manuscript"],
        evidence_ref=refs["evidence_ledger"],
        review_ref=refs["review_ledger"],
        charter_ref=refs["study_charter"],
        additional_refs={
            "medical_manuscript_blueprint": refs["medical_manuscript_blueprint"],
            "claim_evidence_map": refs["claim_evidence_map"],
            "medical_prose_review": refs["medical_prose_review"],
            "publication_gate_projection": refs["publication_gate_projection"],
        },
        record=_publication_eval_record(study_root),
    )

    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    latest = json.loads(latest_path.read_text(encoding="utf-8"))

    assert result["surface"] == "ai_reviewer_publication_eval_workflow"
    assert result["status"] == "materialized"
    assert result["artifact_path"] == str(latest_path.resolve())
    assert latest["assessment_provenance"]["owner"] == "ai_reviewer"
    assert latest["assessment_provenance"]["source_kind"] == "publication_eval_ai_reviewer"
    assert latest["assessment_provenance"]["ai_reviewer_required"] is False
    assert latest["emitted_at"] > "2026-05-04T00:00:00+00:00"
    assert latest["reviewer_operating_system"]["input_bundle"]["manuscript"] == refs["manuscript"]
    assert latest["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]["request_digest"] == (
        "sha256:" + "a" * 64
    )
    assert latest["reviewer_operating_system"]["currentness_checks"]["current_package_freshness"][
        "source_eval_id"
    ] == latest["eval_id"]
    assert latest["reviewer_operating_system"]["route_back_decision"] == {
        "recommended_action": "continue_same_line",
        "rationale": "Proceed to first full draft.",
    }
    assert latest["reviewer_operating_system"]["future_facing_limitations_plan"] == [
        {
            "limitation": "Medication coverage is based on recorded medication fields.",
            "impact_on_claim": "Treatment-gap language must remain documentation-aware.",
            "required_future_analysis_data_or_design": "Link pharmacy or insurance dispensing data.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]
    assert latest["future_facing_limitations_plan"] == [
        {
            "limitation": "Medication coverage is based on recorded medication fields.",
            "impact_on_claim": "Treatment-gap language must remain documentation-aware.",
            "required_future_analysis_data_or_design": "Link pharmacy or insurance dispensing data.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]


def test_ai_reviewer_publication_eval_workflow_accepts_study_relative_currentness_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _relative_refs()
    record = _publication_eval_record(study_root)
    record["quality_assessment"]["medical_journal_prose_quality"]["evidence_refs"] = [
        refs["medical_prose_review"]
    ]
    _write_relative_ai_reviewer_currentness_inputs(study_root)

    result = module.run_ai_reviewer_publication_eval_workflow(
        study_root=study_root,
        manuscript_ref=refs["manuscript"],
        evidence_ref=refs["evidence_ledger"],
        review_ref=refs["review_ledger"],
        charter_ref=refs["study_charter"],
        additional_refs={
            "medical_manuscript_blueprint": refs["medical_manuscript_blueprint"],
            "claim_evidence_map": refs["claim_evidence_map"],
            "medical_prose_review": refs["medical_prose_review"],
            "publication_gate_projection": refs["publication_gate_projection"],
        },
        record=record,
    )

    latest = json.loads((study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8"))

    assert result["status"] == "materialized"
    assert latest["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"][
        "manuscript_ref"
    ] == refs["manuscript"]


def test_ai_reviewer_publication_eval_workflow_materializes_current_route_back_prose_review(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    record = _publication_eval_record(study_root)
    record["verdict"] = {
        "overall_verdict": "mixed",
        "primary_claim_status": "partial",
        "summary": "AI reviewer requires manuscript write repair before publication readiness.",
        "stop_loss_pressure": "watch",
    }
    record["quality_assessment"]["medical_journal_prose_quality"] = {
        "status": "partial",
        "summary": "Medical prose is current but not clear for submission.",
        "evidence_refs": [refs["medical_prose_review"], refs["manuscript"]],
        "reviewer_reason": "Methods and Results need write-owner repair against existing evidence.",
    }
    record["gaps"] = [
        {
            "gap_id": "medical-prose-write-repair",
            "gap_type": "reporting",
            "severity": "must_fix",
            "summary": "The manuscript body is not yet reproducible or result-driven enough for a medical journal.",
            "evidence_refs": [refs["medical_prose_review"], refs["manuscript"]],
        }
    ]
    record["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::route-back-write::medical-prose",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Route the same paper line back to write for medical-journal prose repair.",
            "route_target": "write",
            "route_key_question": "What is the narrowest manuscript repair needed to make the current evidence read as a medical original research article?",
            "route_rationale": "The reviewer judgment is current and evidence-bound; the next owner is write, not a new analysis lane.",
            "evidence_refs": [refs["medical_prose_review"], refs["manuscript"]],
            "requires_controller_decision": True,
            "work_unit_fingerprint": "medical-prose-route-back::write",
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
                "summary": "Repair the manuscript body against current AI reviewer prose findings.",
            },
        }
    ]
    _write_ai_reviewer_currentness_inputs(
        study_root,
        prose_status="partial",
        style_verdict="revise",
        route_back_required=True,
    )

    result = module.run_ai_reviewer_publication_eval_workflow(
        study_root=study_root,
        manuscript_ref=refs["manuscript"],
        evidence_ref=refs["evidence_ledger"],
        review_ref=refs["review_ledger"],
        charter_ref=refs["study_charter"],
        additional_refs={
            "medical_manuscript_blueprint": refs["medical_manuscript_blueprint"],
            "claim_evidence_map": refs["claim_evidence_map"],
            "medical_prose_review": refs["medical_prose_review"],
            "publication_gate_projection": refs["publication_gate_projection"],
        },
        record=record,
    )

    latest = json.loads((study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8"))
    prose_currentness = latest["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]

    assert result["status"] == "materialized"
    assert latest["quality_assessment"]["medical_journal_prose_quality"]["status"] == "partial"
    assert latest["recommended_actions"][0]["action_type"] == "route_back_same_line"
    assert latest["recommended_actions"][0]["route_target"] == "write"
    assert prose_currentness["status"] == "current"
    assert prose_currentness["prose_status"] == "partial"
    assert prose_currentness["overall_style_verdict"] == "revise"
    assert prose_currentness["route_back_required"] is True
    assert prose_currentness["route_target"] == "write"
    assert latest["reviewer_operating_system"]["route_back_decision"]["recommended_action"] == "route_back_same_line"
    assert latest["reviewer_operating_system"]["currentness_checks"]["current_package_freshness"] == {
        "status": "downstream_pending",
        "ref": str((study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json").resolve()),
        "source_eval_id": latest["eval_id"],
        "current_package_root": None,
        "current_package_zip": None,
        "source_signature": None,
        "authority_source_signature": "ai_reviewer_route_back_delivery_downstream_only",
    }


def test_ai_reviewer_publication_eval_workflow_fails_closed_when_required_ref_missing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    _write_ai_reviewer_currentness_inputs(study_root)

    try:
        module.run_ai_reviewer_publication_eval_workflow(
            study_root=study_root,
            manuscript_ref=refs["manuscript"],
            evidence_ref=refs["evidence_ledger"],
            review_ref=refs["review_ledger"],
            charter_ref=refs["study_charter"],
            additional_refs={
                "medical_manuscript_blueprint": refs["medical_manuscript_blueprint"],
                "claim_evidence_map": refs["claim_evidence_map"],
                "medical_prose_review": refs["medical_prose_review"],
            },
            record=_publication_eval_record(study_root),
        )
    except ValueError as exc:
        assert "missing input ref for publication_gate_projection" in str(exc)
    else:
        raise AssertionError("workflow accepted incomplete reviewer OS input refs")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_ai_reviewer_publication_eval_workflow_fails_closed_without_future_facing_limitations_plan(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    record = _publication_eval_record(study_root)
    record.pop("future_facing_limitations_plan")
    _write_ai_reviewer_currentness_inputs(study_root)

    try:
        module.run_ai_reviewer_publication_eval_workflow(
            study_root=study_root,
            manuscript_ref=refs["manuscript"],
            evidence_ref=refs["evidence_ledger"],
            review_ref=refs["review_ledger"],
            charter_ref=refs["study_charter"],
            additional_refs={
                "medical_manuscript_blueprint": refs["medical_manuscript_blueprint"],
                "claim_evidence_map": refs["claim_evidence_map"],
                "medical_prose_review": refs["medical_prose_review"],
                "publication_gate_projection": refs["publication_gate_projection"],
            },
            record=record,
        )
    except ValueError as exc:
        assert "future_facing_limitations_plan" in str(exc)
    else:
        raise AssertionError("workflow accepted AI reviewer trace without future-facing limitations plan")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_ai_reviewer_publication_eval_workflow_rejects_disclosure_only_limitations(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    record = _publication_eval_record(study_root)
    _write_ai_reviewer_currentness_inputs(study_root)
    record["future_facing_limitations_plan"] = [
        {
            "limitation": "Blood pressure fields are semantically unstable.",
            "impact_on_claim": "Blood-pressure-control claims must be withheld.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]

    try:
        module.run_ai_reviewer_publication_eval_workflow(
            study_root=study_root,
            manuscript_ref=refs["manuscript"],
            evidence_ref=refs["evidence_ledger"],
            review_ref=refs["review_ledger"],
            charter_ref=refs["study_charter"],
            additional_refs={
                "medical_manuscript_blueprint": refs["medical_manuscript_blueprint"],
                "claim_evidence_map": refs["claim_evidence_map"],
                "medical_prose_review": refs["medical_prose_review"],
                "publication_gate_projection": refs["publication_gate_projection"],
            },
            record=record,
        )
    except ValueError as exc:
        assert "required_future_analysis_data_or_design" in str(exc)
    else:
        raise AssertionError("workflow accepted disclosure-only limitation without future analysis or design")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_ai_reviewer_publication_eval_workflow_rejects_manuscript_story_provenance_leakage(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    record = _publication_eval_record(study_root)
    _write_ai_reviewer_currentness_inputs(study_root)
    record["quality_assessment"]["novelty_positioning"][
        "reviewer_reason"
    ] = "The novelty remains useful only if the manuscript foregrounds the data-harmonization lesson."
    record["future_facing_limitations_plan"] = [
        {
            "limitation": "HDL unit harmonization changed the central interpretation of the transported score.",
            "impact_on_claim": "The manuscript must treat the raw-HDL run as a harmonization failure signal.",
            "required_future_analysis_data_or_design": "Regenerate tables from current harmonized evidence.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]

    try:
        module.run_ai_reviewer_publication_eval_workflow(
            study_root=study_root,
            manuscript_ref=refs["manuscript"],
            evidence_ref=refs["evidence_ledger"],
            review_ref=refs["review_ledger"],
            charter_ref=refs["study_charter"],
            additional_refs={
                "medical_manuscript_blueprint": refs["medical_manuscript_blueprint"],
                "claim_evidence_map": refs["claim_evidence_map"],
                "medical_prose_review": refs["medical_prose_review"],
                "publication_gate_projection": refs["publication_gate_projection"],
            },
            record=record,
        )
    except ValueError as exc:
        assert "manuscript_story_provenance_leakage" in str(exc)
    else:
        raise AssertionError("workflow accepted AI reviewer record that turned correction provenance into paper story")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_ai_reviewer_publication_eval_workflow_fails_closed_when_prose_review_predates_request(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    record = _publication_eval_record(study_root)
    record["quality_assessment"]["medical_journal_prose_quality"]["evidence_refs"] = [refs["medical_prose_review"]]

    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    _write_json(
        request_path,
        {
            "surface": "medical_prose_review_request",
            "request_digest": "sha256:" + "b" * 64,
            "manuscript": {"path": refs["manuscript"], "digest": "sha256:" + "c" * 64},
        },
    )
    _write_json(
        review_path,
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_ref": str(request_path),
                "request_digest": "sha256:" + "a" * 64,
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": "sha256:" + "c" * 64,
            },
            "medical_journal_prose_quality": {
                "status": "ready",
                "overall_style_verdict": "clear",
                "route_back_recommendation": {"required": False, "route_target": "none"},
            },
        },
    )

    try:
        module.run_ai_reviewer_publication_eval_workflow(
            study_root=study_root,
            manuscript_ref=refs["manuscript"],
            evidence_ref=refs["evidence_ledger"],
            review_ref=refs["review_ledger"],
            charter_ref=refs["study_charter"],
            additional_refs={
                "medical_manuscript_blueprint": refs["medical_manuscript_blueprint"],
                "claim_evidence_map": refs["claim_evidence_map"],
                "medical_prose_review": refs["medical_prose_review"],
                "publication_gate_projection": refs["publication_gate_projection"],
            },
            record=record,
        )
    except ValueError as exc:
        assert "medical_prose_review_request_digest_mismatch" in str(exc)
    else:
        raise AssertionError("workflow accepted stale AI prose review against newer request")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_ai_reviewer_publication_eval_workflow_fails_closed_when_package_freshness_is_for_old_eval(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    record = _publication_eval_record(study_root)
    _write_ai_reviewer_currentness_inputs(study_root, source_eval_id="publication-eval::old")

    try:
        module.run_ai_reviewer_publication_eval_workflow(
            study_root=study_root,
            manuscript_ref=refs["manuscript"],
            evidence_ref=refs["evidence_ledger"],
            review_ref=refs["review_ledger"],
            charter_ref=refs["study_charter"],
            additional_refs={
                "medical_manuscript_blueprint": refs["medical_manuscript_blueprint"],
                "claim_evidence_map": refs["claim_evidence_map"],
                "medical_prose_review": refs["medical_prose_review"],
                "publication_gate_projection": refs["publication_gate_projection"],
            },
            record=record,
        )
    except ValueError as exc:
        assert "current_package_freshness_source_eval_id_mismatch" in str(exc)
    else:
        raise AssertionError("workflow accepted package freshness from an older publication eval")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_ai_reviewer_publication_eval_latest_rejects_trace_without_currentness_checks(
    tmp_path: Path,
) -> None:
    from med_autoscience.publication_eval_latest import materialize_ai_reviewer_publication_eval_latest

    study_root = tmp_path / "study"
    record = _publication_eval_record(study_root)
    record.pop("future_facing_limitations_plan")
    trace = _reviewer_operating_system(study_root)
    trace.pop("currentness_checks", None)
    record["reviewer_operating_system"] = trace

    try:
        materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=record)
    except ValueError as exc:
        assert "currentness_checks" in str(exc)
    else:
        raise AssertionError("publication eval latest accepted AI reviewer trace without currentness checks")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_ai_reviewer_publication_eval_latest_rejects_requested_prose_currentness_without_clean_migration(
    tmp_path: Path,
) -> None:
    from med_autoscience.publication_eval_latest import materialize_ai_reviewer_publication_eval_latest

    study_root = tmp_path / "study"
    record = _publication_eval_record(study_root)
    trace = _reviewer_operating_system(study_root)
    trace["currentness_checks"]["medical_prose_review"] = {
        "status": "requested",
        "request_ref": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"),
        "request_digest": "sha256:" + "a" * 64,
        "manuscript_ref": str(study_root / "paper" / "manuscript.md"),
        "manuscript_digest": "sha256:" + "c" * 64,
        "route_back_required": True,
    }
    record["reviewer_operating_system"] = trace

    try:
        materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=record)
    except ValueError as exc:
        assert "paper_authority_clean_migration" in str(exc)
    else:
        raise AssertionError("publication eval latest accepted requested prose currentness without clean migration")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
