from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_ai_reviewer_publication_eval_workflow import (
    _publication_eval_record,
    _refs,
    _write_ai_reviewer_alignment_inputs,
    _write_json,
    _write_text,
)


def _write_medical_manuscript_blueprint(study_root: Path, *, study_id: str = "001-risk") -> None:
    refs = _refs(study_root)
    _write_json(
        Path(refs["medical_manuscript_blueprint"]),
        {
            "schema_version": 1,
            "surface": "medical_manuscript_blueprint",
            "authoring_provenance": {
                "owner": "ai_author",
                "source_kind": "medical_manuscript_blueprint",
                "policy_id": "medical_manuscript_blueprint_v1",
                "ai_reviewer_required": False,
            },
            "argument_sequence": [
                "clinical_problem",
                "evidence_gap",
                "study_objective",
                "target_population",
                "study_design",
                "main_findings_by_clinical_importance",
                "clinical_interpretation",
                "discussion_claim_boundary",
                "limitations",
            ],
            "study_id": study_id,
            "clinical_problem": "Patients need clinically interpretable risk information.",
            "evidence_gap": "Prior reports do not define the claim boundary.",
            "study_objective": "To evaluate a restrained risk model.",
            "target_population": "Adults in the cohort.",
            "study_design": "Retrospective cohort study.",
            "main_findings_by_clinical_importance": [
                {"rank": 1, "clinical_finding": "The score stratified risk."}
            ],
            "clinical_interpretation": "Interpret as bounded risk stratification.",
            "claim_evidence_map": [{"claim_id": "C1", "statement": "Primary claim."}],
            "figure_table_rhetorical_roles": [
                {"display_id": "F1", "rhetorical_role": "Supports the main finding."}
            ],
            "discussion_claim_boundary": "Do not claim practice change.",
            "limitations": ["External validation is not established."],
            "journal_voice_target": {"voice": "neutral_clinical_original_research"},
            "source_refs": [refs["claim_evidence_map"]],
        },
    )


def test_ai_reviewer_publication_eval_workflow_clean_migration_uses_record_route_target(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    manuscript_ref = str(study_root / "paper" / "draft.md")
    record = _publication_eval_record(study_root)
    record["verdict"] = {
        "overall_verdict": "mixed",
        "primary_claim_status": "partial",
        "summary": "Clean migration requires write-owner manuscript repair before closure.",
        "stop_loss_pressure": "watch",
    }
    record["quality_assessment"]["medical_journal_prose_quality"] = {
        "status": "partial",
        "summary": "The current manuscript needs write-owner repair before journal submission.",
        "evidence_refs": [manuscript_ref],
        "reviewer_reason": "Methods reproducibility and result-driven prose remain incomplete.",
    }
    record["recommended_actions"] = [
        {
            "action_id": "clean-migration-route-to-write",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Route the clean-migration reviewer record back to write.",
            "route_target": "write",
            "route_key_question": "Can write repair close the current clean-migration reviewer record?",
            "route_rationale": "The AI reviewer record is current but needs manuscript repair.",
            "evidence_refs": [manuscript_ref],
            "requires_controller_decision": True,
        }
    ]
    _write_ai_reviewer_alignment_inputs(study_root)
    _write_medical_manuscript_blueprint(study_root)
    manuscript_text = "# Current manuscript\n\nClean migration reviewer record is bound to this manuscript.\n"
    _write_text(Path(manuscript_ref), manuscript_text)
    _write_json(
        study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json",
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": "001-risk",
        },
    )

    record_with_trace = module.build_ai_reviewer_publication_eval_record_with_workflow_trace(
        study_root=study_root,
        manuscript_ref=manuscript_ref,
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

    reviewer_os = record_with_trace["reviewer_operating_system"]
    prose_currentness = reviewer_os["currentness_checks"]["medical_prose_review"]
    assert prose_currentness["status"] == "requested"
    assert prose_currentness["authority_source_signature"] == "paper_authority_clean_migration"
    assert prose_currentness["route_back_required"] is True
    assert prose_currentness["route_target"] == "write"
    assert reviewer_os["route_back_decision"]["recommended_action"] == "route_back_same_line"
    assert reviewer_os["route_back_decision"]["route_target"] == "write"
