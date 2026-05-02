from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_review_request_inputs(study_root: Path) -> None:
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
            "study_id": "001-risk",
            "clinical_problem": "Patients need clinically interpretable risk information.",
            "evidence_gap": "Prior reports do not define the claim boundary.",
            "study_objective": "To evaluate a restrained risk model.",
            "target_population": "Adults in the cohort.",
            "study_design": "Retrospective cohort study.",
            "main_findings_by_clinical_importance": [{"rank": 1, "clinical_finding": "The score stratified risk."}],
            "clinical_interpretation": "Interpret as bounded risk stratification.",
            "claim_evidence_map": [{"claim_id": "C1", "statement": "Primary claim."}],
            "figure_table_rhetorical_roles": [{"display_id": "F1", "rhetorical_role": "Supports the main finding."}],
            "discussion_claim_boundary": "Do not claim practice change.",
            "limitations": ["External validation is not established."],
            "journal_voice_target": {"voice": "neutral_clinical_original_research"},
            "source_refs": [str(study_root / "paper" / "claim_evidence_map.json")],
        },
    )
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claims": [{"claim_id": "C1"}]})
    _write_json(study_root / "paper" / "results_narrative_map.json", {"sections": [{"section_id": "results"}]})
    _write_json(study_root / "paper" / "figure_semantics_manifest.json", {"figures": [{"figure_id": "F1"}]})
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"items": []})
    (study_root / "paper" / "draft.md").write_text(
        "## Results\n\nFigure 1 shows that the model worked well.\n",
        encoding="utf-8",
    )


def test_review_request_bundles_blueprint_corpus_and_mechanical_evidence_without_authorizing_style(
    tmp_path: Path,
) -> None:
    from med_autoscience.medical_prose_review_request import (
        materialize_medical_prose_review_request,
        read_medical_prose_review_request,
    )

    study_root = tmp_path / "study"
    _write_review_request_inputs(study_root)

    result = materialize_medical_prose_review_request(
        study_root=study_root,
        mechanical_safety_flags=[
            {
                "flag_id": "figure_table_subject_results_sentence",
                "evidence_snippet": "Figure 1 shows that the model worked well.",
            }
        ],
    )
    payload = read_medical_prose_review_request(study_root=study_root)

    assert result["artifact_path"] == str(
        study_root.resolve() / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    )
    assert payload["review_owner"] == "ai_reviewer"
    assert payload["style_corpus"]["corpus_id"] == "general_medical_journal_style_corpus_v1"
    assert payload["structured_response_contract"]["mechanical_flags_role"] == "evidence_snippets_only"
    assert payload["mechanical_safety_flags"][0]["flag_id"] == "figure_table_subject_results_sentence"
    assert "Figure 1 shows" in payload["manuscript"]["text"]


def test_ai_response_materializes_ai_owned_prose_review(tmp_path: Path) -> None:
    from med_autoscience.medical_prose_review import read_medical_prose_review
    from med_autoscience.medical_prose_review_request import (
        materialize_ai_medical_prose_review_from_response,
        materialize_medical_prose_review_request,
    )

    study_root = tmp_path / "study"
    _write_review_request_inputs(study_root)
    materialize_medical_prose_review_request(study_root=study_root)

    result = materialize_ai_medical_prose_review_from_response(
        study_root=study_root,
        response_payload={
            "overall_style_verdict": "revise",
            "summary": "Results are still display-led and sound like a work report.",
            "section_level_diagnosis": {
                "results": "Clinical findings should lead before display citations.",
                "discussion": "Discussion should open with the principal finding.",
            },
            "representative_bad_sentences": ["Figure 1 shows that the model worked well."],
            "representative_rewrites": [
                {
                    "before": "Figure 1 shows that the model worked well.",
                    "after": "The score separated clinically relevant risk groups across the prespecified follow-up horizon.",
                }
            ],
            "route_back_recommendation": {
                "route_target": "write",
                "reason": "Rewrite Results paragraphs from the AI prose review.",
            },
        },
    )
    review = read_medical_prose_review(study_root=study_root)

    assert result["artifact_path"].endswith("medical_prose_review.json")
    assert review["assessment_provenance"]["owner"] == "ai_reviewer"
    assert review["assessment_provenance"]["request_ref"].endswith("medical_prose_review_request.json")
    assert review["medical_journal_prose_quality"]["overall_style_verdict"] == "revise"
    assert review["medical_journal_prose_quality"]["route_back_recommendation"]["route_target"] == "write"


def test_ai_response_rejects_non_clear_without_route_back(tmp_path: Path) -> None:
    from med_autoscience.medical_prose_review_request import (
        materialize_ai_medical_prose_review_from_response,
        materialize_medical_prose_review_request,
    )

    study_root = tmp_path / "study"
    _write_review_request_inputs(study_root)
    materialize_medical_prose_review_request(study_root=study_root)

    with pytest.raises(ValueError, match="non-clear AI prose response"):
        materialize_ai_medical_prose_review_from_response(
            study_root=study_root,
            response_payload={
                "overall_style_verdict": "revise",
                "summary": "Needs revision.",
                "section_level_diagnosis": {"results": "Needs revision."},
                "representative_bad_sentences": [],
                "representative_rewrites": [],
                "route_back_recommendation": {"route_target": "none", "reason": "none"},
            },
        )
