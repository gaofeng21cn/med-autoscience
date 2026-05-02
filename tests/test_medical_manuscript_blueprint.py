from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_blueprint_inputs(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "controller" / "study_charter.json",
        {
            "study_id": "001-risk",
            "paper_quality_contract": {
                "reporting_expectations": {
                    "paper_framing_summary": "Patients with postoperative NF-PitNET need clinically interpretable risk stratification."
                },
                "medical_prose_style_contract": {
                    "target_voice": "neutral_clinical_original_research",
                    "source_basis": [
                        "Zeiger biomedical research paper clear-writing and paper-text model",
                        "Gopen and Swan reader-expectation information flow",
                        "JAMA Network Open original investigation prose exemplars",
                    ],
                },
            },
            "publication_objective": "To evaluate a restrained postoperative risk model.",
            "scientific_followup_questions": [
                "Prior descriptive reports do not define how preoperative features should shape follow-up."
            ],
            "manuscript_conclusion_redlines": ["Do not claim treatment escalation from internal validation."],
        },
    )
    paper_root = study_root / "paper"
    _write_json(
        paper_root / "results_narrative_map.json",
        {
            "sections": [
                {
                    "section_id": "primary-risk",
                    "direct_answer": "The extended model improved risk stratification.",
                    "key_quantitative_findings": ["Calibration and decision utility favored the extended model."],
                    "clinical_meaning": "The finding supports follow-up stratification language.",
                    "boundary": "Internal validation only.",
                    "supporting_display_items": ["F1", "T1"],
                }
            ]
        },
    )
    _write_json(
        paper_root / "claim_evidence_map.json",
        {
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "The model supports bounded risk stratification.",
                    "status": "supported_main_text",
                    "paper_role": "main_text",
                    "evidence_items": [{"evidence_id": "E1"}],
                    "display_bindings": ["F1"],
                    "limitations": ["External validation is not established."],
                }
            ]
        },
    )
    _write_json(
        paper_root / "figure_semantics_manifest.json",
        {
            "figures": [
                {
                    "figure_id": "F1",
                    "story_role": "primary_result",
                    "direct_message": "Shows calibration and clinical utility support.",
                    "interpretation_boundary": "No treatment threshold is proposed.",
                }
            ]
        },
    )
    _write_json(
        paper_root / "methods_implementation_manifest.json",
        {
            "study_design": {
                "study_design": "Retrospective cohort study.",
                "cohort_definition": "Adults undergoing surgery for NF-PitNET.",
            }
        },
    )
    _write_json(paper_root / "evidence_ledger.json", {"items": [{"evidence_id": "E1"}]})
    _write_json(paper_root / "review" / "review_ledger.json", {"items": []})


def test_materialize_medical_manuscript_blueprint_uses_clinical_argument_order(tmp_path: Path) -> None:
    from med_autoscience.medical_manuscript_blueprint import (
        materialize_medical_manuscript_blueprint,
        read_medical_manuscript_blueprint,
    )

    study_root = tmp_path / "study"
    _write_blueprint_inputs(study_root)

    result = materialize_medical_manuscript_blueprint(study_root=study_root)
    payload = read_medical_manuscript_blueprint(study_root=study_root)

    assert result["artifact_path"] == str(study_root.resolve() / "paper" / "medical_manuscript_blueprint.json")
    assert payload["argument_sequence"] == [
        "clinical_problem",
        "evidence_gap",
        "study_objective",
        "target_population",
        "study_design",
        "main_findings_by_clinical_importance",
        "clinical_interpretation",
        "discussion_claim_boundary",
        "limitations",
    ]
    assert payload["clinical_problem"].startswith("Patients with postoperative NF-PitNET")
    assert payload["main_findings_by_clinical_importance"][0]["clinical_finding"] == (
        "The extended model improved risk stratification."
    )
    assert payload["figure_table_rhetorical_roles"][0]["rhetorical_role"] == (
        "Shows calibration and clinical utility support."
    )
    assert payload["journal_voice_target"]["voice"] == "neutral_clinical_original_research"
    assert payload["journal_voice_target"]["style_corpus_id"] == "general_medical_journal_style_corpus_v1"
    assert payload["journal_voice_target"]["style_corpus_ref"].endswith("paper/medical_journal_style_corpus.json")
    assert (study_root / "paper" / "medical_journal_style_corpus.json").exists()


def test_blueprint_reader_rejects_non_authority_path(tmp_path: Path) -> None:
    from med_autoscience.medical_manuscript_blueprint import resolve_medical_manuscript_blueprint_ref

    study_root = tmp_path / "study"

    with pytest.raises(ValueError, match="study paper authority"):
        resolve_medical_manuscript_blueprint_ref(
            study_root=study_root,
            ref=study_root / "paper" / "draft_blueprint.json",
        )
