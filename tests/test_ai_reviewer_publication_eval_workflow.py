from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_ai_reviewer_publication_eval_workflow_cases.shared import (
    _canonical_publication_eval_record,
    _publication_eval_record,
    _reviewer_operating_system,
    _refs,
    _relative_refs,
    _sha256_text,
    _sci_clinical_registry_review,
    _write_ai_reviewer_alignment_inputs,
    _write_ai_reviewer_currentness_inputs,
    _write_json,
    _write_relative_ai_reviewer_currentness_inputs,
    _write_text,
)

__all__ = [
    "_canonical_publication_eval_record",
    "_publication_eval_record",
    "_reviewer_operating_system",
    "_refs",
    "_relative_refs",
    "_sha256_text",
    "_sci_clinical_registry_review",
    "_write_ai_reviewer_alignment_inputs",
    "_write_ai_reviewer_currentness_inputs",
    "_write_json",
    "_write_relative_ai_reviewer_currentness_inputs",
    "_write_text",
]

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
    evidence_currentness = latest["reviewer_operating_system"]["currentness_checks"]["evidence_ledger"]
    claim_map_currentness = latest["reviewer_operating_system"]["currentness_checks"]["claim_evidence_map"]
    assert evidence_currentness == {
        "status": "current",
        "ref": refs["evidence_ledger"],
        "digest": module._sha256_file(Path(refs["evidence_ledger"])),
        "authority_source_signature": "ai_reviewer_workflow_live_input",
    }
    assert claim_map_currentness == {
        "status": "current",
        "ref": refs["claim_evidence_map"],
        "digest": module._sha256_file(Path(refs["claim_evidence_map"])),
        "authority_source_signature": "ai_reviewer_workflow_live_input",
    }
    quality_readiness = latest["reviewer_operating_system"]["publication_quality_readiness"]
    prose_currentness = latest["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]
    alignment_gate = latest["reviewer_operating_system"]["claim_evidence_alignment"]
    assert alignment_gate["status"] == "ready"
    assert alignment_gate["claim_count"] == 1
    assert alignment_gate["aligned_claim_count"] == 1
    assert alignment_gate["may_authorize_quality_verdict"] is False
    assert quality_readiness == {
        "surface_kind": "publication_quality_authority_kernel_v1",
        "status": "ready",
        "current_manuscript_digest": prose_currentness["manuscript_digest"],
        "review_request_digest": prose_currentness["request_digest"],
        "evidence_ledger_digest": quality_readiness["evidence_ledger_digest"],
        "claim_evidence_alignment_digest": quality_readiness["claim_evidence_alignment_digest"],
        "rubric_version": "medical_publication_critique_v1",
        "owner_attempt_id": quality_readiness["owner_attempt_id"],
        "fail_closed_when_missing": True,
        "missing_required_fields": [],
    }
    assert quality_readiness["evidence_ledger_digest"].startswith("sha256:")
    assert quality_readiness["claim_evidence_alignment_digest"].startswith("sha256:")
    assert quality_readiness["owner_attempt_id"].startswith("ai-reviewer-publication-eval::")
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
    current_manuscript = latest["reviewer_operating_system"]["currentness_checks"]["current_manuscript"]
    assert current_manuscript == {
        "status": "current",
        "manuscript_ref": refs["manuscript"],
        "manuscript_digest": prose_currentness["manuscript_digest"],
        "authority_source_signature": "ai_reviewer_workflow_live_manuscript",
    }
    assert latest["future_facing_limitations_plan"] == [
        {
            "limitation": "Medication coverage is based on recorded medication fields.",
            "impact_on_claim": "Treatment-gap language must remain documentation-aware.",
            "required_future_analysis_data_or_design": "Link pharmacy or insurance dispensing data.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]


def test_ai_reviewer_publication_eval_workflow_preserves_owner_route_identity(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    _write_ai_reviewer_currentness_inputs(study_root)
    owner_route_currentness_basis = {
        "truth_epoch": "truth-event-current",
        "runtime_health_epoch": "runtime-health-current",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        "work_unit_fingerprint": "domain-transition::review::current-manuscript",
        "source_eval_id": "publication-eval::previous",
    }

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
            "owner_route_currentness_basis": owner_route_currentness_basis,
        },
        record=_publication_eval_record(study_root),
    )

    latest = json.loads((study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8"))
    provenance = latest["assessment_provenance"]
    assert provenance["owner_route_currentness_basis"] == owner_route_currentness_basis
    assert provenance["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    assert provenance["work_unit_fingerprint"] == "domain-transition::review::current-manuscript"


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


def test_ai_reviewer_publication_eval_workflow_requires_sci_registry_review_matrix(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    record = _publication_eval_record(study_root)
    record.pop("sci_clinical_registry_review")
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
        assert "sci_clinical_registry_review" in str(exc)
    else:
        raise AssertionError("workflow accepted publication eval without SCI clinical registry review matrix")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_ai_reviewer_publication_eval_workflow_blocks_major_sci_registry_concern(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    record = _publication_eval_record(study_root)
    record["sci_clinical_registry_review"][2] = {
        "concern_id": "adult-child-bmi-classification-risk",
        "domain": "population_applicability",
        "status": "major_concern",
        "severity": "major",
        "finding": "Median age near 18 requires adult-only or pediatric classification handling before BMI class claims can be paper-ready.",
        "evidence_refs": [refs["manuscript"], refs["evidence_ledger"]],
        "required_disposition": "route_back_analysis",
    }
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
        record=record,
    )

    latest = json.loads(Path(result["artifact_path"]).read_text(encoding="utf-8"))
    readiness = latest["reviewer_operating_system"]["publication_quality_readiness"]
    assert readiness["status"] == "blocked"
    assert "sci_clinical_registry_review::adult-child-bmi-classification-risk" in readiness["missing_required_fields"]


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


def test_ai_reviewer_publication_eval_workflow_fails_closed_when_live_manuscript_changed_after_review(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    record = _publication_eval_record(study_root)
    record["quality_assessment"]["medical_journal_prose_quality"]["evidence_refs"] = [refs["medical_prose_review"]]
    _write_ai_reviewer_currentness_inputs(study_root)
    _write_text(
        Path(refs["manuscript"]),
        "# Revised manuscript\n\nThis text changed after the AI prose review was produced.\n",
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
        assert "medical_prose_review_live_manuscript_digest_mismatch" in str(exc)
    else:
        raise AssertionError("workflow accepted stale AI prose review after live manuscript changed")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_request_bound_ai_reviewer_workflow_fails_closed_when_live_manuscript_changed_after_review(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    record = _publication_eval_record(study_root)
    record["quality_assessment"]["medical_journal_prose_quality"]["evidence_refs"] = [refs["medical_prose_review"]]
    _write_ai_reviewer_currentness_inputs(
        study_root,
        prose_status="partial",
        style_verdict="revise",
        route_back_required=True,
    )
    _write_text(
        Path(refs["manuscript"]),
        "# Revised manuscript\n\nThis text changed after the AI prose review was produced.\n",
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
            workflow_currentness_mode="request_bound_ai_reviewer_record",
        )
    except ValueError as exc:
        assert "medical_prose_review_live_manuscript_digest_mismatch" in str(exc)
    else:
        raise AssertionError("request-bound workflow accepted stale AI prose review after live manuscript changed")

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


from tests.test_ai_reviewer_publication_eval_workflow_cases.latest_authority_validation import *  # noqa: E402,F403,F401
