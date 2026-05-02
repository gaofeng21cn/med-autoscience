from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_valid_blueprint(study_root: Path) -> None:
    _write_json(
        study_root / "paper" / "medical_manuscript_blueprint.json",
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
            "clinical_problem": "Patients need a clinically interpretable risk frame.",
            "evidence_gap": "Prior evidence does not define the bounded interpretation.",
            "study_objective": "To evaluate the model in a retrospective cohort.",
            "target_population": "Adults in the study cohort.",
            "study_design": "Retrospective cohort study.",
            "main_findings_by_clinical_importance": [{"rank": 1, "clinical_finding": "The model improved risk stratification."}],
            "clinical_interpretation": "Interpret as bounded prediction evidence.",
            "claim_evidence_map": [{"claim_id": "C1", "statement": "Primary claim."}],
            "figure_table_rhetorical_roles": [{"display_id": "F1", "rhetorical_role": "Supports the primary finding."}],
            "discussion_claim_boundary": "Do not claim practice change.",
            "limitations": ["External validation is not established."],
            "journal_voice_target": {"voice": "neutral_clinical_original_research"},
            "source_refs": [str(study_root / "paper" / "claim_evidence_map.json")],
        },
    )


def test_materialize_medical_prose_review_requires_ai_reviewer_owned_structured_judgment(tmp_path: Path) -> None:
    from med_autoscience.medical_prose_review import materialize_medical_prose_review, read_medical_prose_review

    study_root = tmp_path / "study"
    _write_valid_blueprint(study_root)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_path.write_text("## Results\n\nFigure 1 shows the model worked well.\n", encoding="utf-8")

    result = materialize_medical_prose_review(
        study_root=study_root,
        manuscript_path=manuscript_path,
        verdict="revise",
        style_diagnosis="AI reviewer found figure-led Results prose.",
        representative_bad_sentences=["Figure 1 shows the model worked well."],
        representative_rewrites=[
            {
                "before": "Figure 1 shows the model worked well.",
                "after": "The model improved risk stratification across the prespecified threshold range.",
            }
        ],
        route_back_target="write",
    )
    payload = read_medical_prose_review(study_root=study_root)

    assert result["artifact_path"] == str(
        study_root.resolve() / "artifacts" / "publication_eval" / "medical_prose_review.json"
    )
    assert payload["assessment_provenance"]["owner"] == "ai_reviewer"
    assert payload["medical_journal_prose_quality"]["overall_style_verdict"] == "revise"
    assert payload["medical_journal_prose_quality"]["representative_rewrites"][0]["after"].startswith(
        "The model improved"
    )


def test_medical_prose_review_rejects_mechanical_projection_owner(tmp_path: Path) -> None:
    from med_autoscience.medical_prose_review import materialize_medical_prose_review

    study_root = tmp_path / "study"
    payload = {
        "schema_version": 1,
        "surface": "medical_prose_review",
        "assessment_provenance": {
            "owner": "mechanical_projection",
            "source_kind": "medical_prose_review",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        },
        "medical_journal_prose_quality": {
            "status": "ready",
            "overall_style_verdict": "clear",
            "summary": "Pattern scan did not find work-report residue.",
            "route_back_recommendation": {"required": False, "route_target": "none", "reason": "none"},
        },
        "mechanical_safety_flags": [],
        "source_refs": [str(study_root)],
    }

    with pytest.raises(ValueError, match="owner must be ai_reviewer"):
        materialize_medical_prose_review(study_root=study_root, payload=payload)
