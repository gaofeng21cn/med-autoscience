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
    assert payload["style_corpus"]["style_version"] == "medical_journal_prose_style_v3"
    assert payload["style_corpus"]["style_digest"].startswith("sha256:")
    assert payload["style_currentness"]["status"] == "current"
    assert payload["style_currentness"]["style_version"] == "medical_journal_prose_style_v3"
    assert payload["style_currentness"]["style_digest"] == payload["style_corpus"]["style_digest"]
    assert payload["request_digest"].startswith("sha256:")
    assert payload["request_currentness"] == {
        "status": "current",
        "currentness_policy_id": "medical_prose_review_request_currentness_v1",
        "request_digest": payload["request_digest"],
        "style_version": "medical_journal_prose_style_v3",
        "style_digest": payload["style_corpus"]["style_digest"],
    }
    assert payload["structured_response_contract"]["mechanical_flags_role"] == "evidence_snippets_only"
    assert payload["mechanical_safety_flags"][0]["flag_id"] == "figure_table_subject_results_sentence"
    assert "Figure 1 shows" in payload["manuscript"]["text"]


def test_review_request_uses_stage_native_blueprint_when_legacy_paper_ref_is_absent(
    tmp_path: Path,
) -> None:
    from med_autoscience.medical_prose_review_request import (
        materialize_medical_prose_review_request,
        read_medical_prose_review_request,
    )

    study_root = tmp_path / "study"
    _write_review_request_inputs(study_root)
    legacy_blueprint_path = study_root / "paper" / "medical_manuscript_blueprint.json"
    stage_native_blueprint_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
        / "medical_manuscript_blueprint.json"
    )
    stage_native_blueprint_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_blueprint_path.replace(stage_native_blueprint_path)

    materialize_medical_prose_review_request(study_root=study_root)
    payload = read_medical_prose_review_request(study_root=study_root)

    assert payload["required_inputs"]["medical_manuscript_blueprint_ref"] == str(
        stage_native_blueprint_path.resolve()
    )
    assert not legacy_blueprint_path.exists()


def test_review_request_uses_stage_native_current_body_paper_root_when_legacy_paper_is_absent(
    tmp_path: Path,
) -> None:
    from med_autoscience.medical_prose_review_request import (
        materialize_medical_prose_review_request,
        read_medical_prose_review_request,
    )

    study_root = tmp_path / "study"
    _write_review_request_inputs(study_root)
    legacy_paper_root = study_root / "paper"
    stage_native_paper_root = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )
    stage_native_paper_root.parent.mkdir(parents=True, exist_ok=True)
    legacy_paper_root.replace(stage_native_paper_root)

    materialize_medical_prose_review_request(study_root=study_root)
    payload = read_medical_prose_review_request(study_root=study_root)

    assert payload["required_inputs"]["manuscript_ref"] == str((stage_native_paper_root / "draft.md").resolve())
    assert payload["required_inputs"]["claim_evidence_map_ref"] == str(
        (stage_native_paper_root / "claim_evidence_map.json").resolve()
    )
    assert payload["required_inputs"]["review_ledger_ref"] == str(
        (stage_native_paper_root / "review" / "review_ledger.json").resolve()
    )
    assert payload["manuscript"]["path"] == str((stage_native_paper_root / "draft.md").resolve())
    assert "Figure 1 shows" in payload["manuscript"]["text"]
    assert not (legacy_paper_root / "draft.md").exists()
    assert not (legacy_paper_root / "claim_evidence_map.json").exists()


def test_review_request_uses_stage_native_body_when_legacy_paper_shell_lacks_draft(
    tmp_path: Path,
) -> None:
    from med_autoscience.medical_prose_review_request import (
        materialize_medical_prose_review_request,
        read_medical_prose_review_request,
    )

    study_root = tmp_path / "study"
    _write_review_request_inputs(study_root)
    legacy_paper_root = study_root / "paper"
    stage_native_paper_root = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )
    stage_native_paper_root.parent.mkdir(parents=True, exist_ok=True)
    legacy_paper_root.replace(stage_native_paper_root)
    legacy_paper_root.mkdir(parents=True)
    _write_json(legacy_paper_root / "medical_journal_style_corpus.json", {"surface": "style_shell"})

    materialize_medical_prose_review_request(study_root=study_root)
    payload = read_medical_prose_review_request(study_root=study_root)

    assert payload["required_inputs"]["manuscript_ref"] == str((stage_native_paper_root / "draft.md").resolve())
    assert payload["manuscript"]["path"] == str((stage_native_paper_root / "draft.md").resolve())
    assert not (legacy_paper_root / "draft.md").exists()


def test_review_request_includes_completed_unit_harmonized_rerun_evidence(tmp_path: Path) -> None:
    from med_autoscience.medical_prose_review_request import (
        materialize_medical_prose_review_request,
        read_medical_prose_review_request,
    )

    study_root = tmp_path / "study"
    _write_review_request_inputs(study_root)
    analysis_root = study_root / "artifacts" / "controller" / "analysis_harmonization"
    rerun_path = analysis_root / "unit_harmonized_external_validation_rerun.json"
    _write_json(
        analysis_root / "latest.json",
        {
            "surface": "analysis_harmonization_owner_result",
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "completed",
            "unit_harmonized_rerun_completed": True,
            "rerun_evidence_ref": str(rerun_path),
        },
    )
    _write_json(
        rerun_path,
        {
            "surface": "unit_harmonized_external_validation_rerun_evidence",
            "status": "completed",
            "old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion": True,
        },
    )

    materialize_medical_prose_review_request(study_root=study_root)
    payload = read_medical_prose_review_request(study_root=study_root)

    assert payload["required_inputs"]["analysis_harmonization_result_ref"] == str((analysis_root / "latest.json").resolve())
    assert payload["required_inputs"]["unit_harmonized_rerun_evidence_ref"] == str(rerun_path.resolve())
    assert payload["analysis_harmonization"]["unit_harmonized_rerun_completed"] is True
    assert payload["analysis_harmonization"]["old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion"] is True


def test_review_request_blocks_clear_verdict_when_methodology_repair_enters_story_sections(
    tmp_path: Path,
) -> None:
    from med_autoscience.medical_prose_review_request import (
        materialize_ai_medical_prose_review_from_response,
        materialize_medical_prose_review_request,
        read_medical_prose_review_request,
    )

    study_root = tmp_path / "study"
    _write_review_request_inputs(study_root)
    (study_root / "paper" / "draft.md").write_text(
        "\n".join(
            [
                "# Title",
                "",
                "## Abstract",
                "After unit-harmonized predictor preprocessing, the model retained external ordering.",
                "",
                "## Methods",
                "HDL cholesterol was represented in a common analytic unit before score application.",
                "",
                "## Results",
                "After unit-harmonized predictor preprocessing, the NHANES c-index was 0.7339.",
                "",
                "## Discussion",
                "The main contribution is the unit-harmonized external-validation story.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    analysis_root = study_root / "artifacts" / "controller" / "analysis_harmonization"
    rerun_path = analysis_root / "unit_harmonized_external_validation_rerun.json"
    _write_json(
        analysis_root / "latest.json",
        {
            "surface": "analysis_harmonization_owner_result",
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "completed",
            "unit_harmonized_rerun_completed": True,
            "rerun_evidence_ref": str(rerun_path),
        },
    )
    _write_json(
        rerun_path,
        {
            "surface": "unit_harmonized_external_validation_rerun_evidence",
            "status": "completed",
            "old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion": True,
        },
    )

    materialize_medical_prose_review_request(study_root=study_root)
    request = read_medical_prose_review_request(study_root=study_root)

    flag_ids = {flag["flag_id"] for flag in request["mechanical_safety_flags"]}
    assert "internal_methodology_repair_story_leakage" in flag_ids

    with pytest.raises(ValueError, match="blocking mechanical safety flags"):
        materialize_ai_medical_prose_review_from_response(
            study_root=study_root,
            response_payload={
                "overall_style_verdict": "clear",
                "summary": "The manuscript reads as a conventional external-validation article.",
                "section_level_diagnosis": {
                    "introduction": "The clinical problem and evidence gap are clear.",
                    "methods": "Methods are transparent.",
                    "results": "Results are quantitative.",
                    "discussion": "Discussion is restrained.",
                },
                "representative_bad_sentences": [
                    "After unit-harmonized predictor preprocessing, the NHANES c-index was 0.7339."
                ],
                "representative_rewrites": [
                    {
                        "before": "After unit-harmonized predictor preprocessing, the NHANES c-index was 0.7339.",
                        "after": "The transported score retained discrimination in NHANES, with a c-index of 0.7339.",
                    }
                ],
                "route_back_recommendation": {
                    "route_target": "none",
                    "reason": "The reviewer judged the manuscript clear.",
                },
            },
        )


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
                "introduction": "Clinical problem and evidence gap are readable.",
                "methods": "Methods wording is sufficiently reader-facing for this route-back.",
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
    assert review["assessment_provenance"]["request_digest"].startswith("sha256:")
    assert review["assessment_provenance"]["manuscript_ref"].endswith("paper/draft.md")
    assert review["assessment_provenance"]["manuscript_digest"].startswith("sha256:")
    assert review["style_currentness"]["status"] == "current"
    assert review["style_currentness"]["style_version"] == "medical_journal_prose_style_v3"
    assert review["style_currentness"]["style_digest"].startswith("sha256:")
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


def test_clear_ai_response_requires_substantive_journal_quality_evidence(tmp_path: Path) -> None:
    from med_autoscience.medical_prose_review_request import (
        materialize_ai_medical_prose_review_from_response,
        materialize_medical_prose_review_request,
    )

    study_root = tmp_path / "study"
    _write_review_request_inputs(study_root)
    materialize_medical_prose_review_request(study_root=study_root)

    with pytest.raises(ValueError, match="clear AI prose response"):
        materialize_ai_medical_prose_review_from_response(
            study_root=study_root,
            response_payload={
                "overall_style_verdict": "clear",
                "summary": "The manuscript is formal enough.",
                "section_level_diagnosis": {
                    "introduction": "Looks acceptable.",
                    "methods": "Looks acceptable.",
                    "results": "Looks acceptable.",
                    "discussion": "Looks acceptable.",
                },
                "representative_bad_sentences": [],
                "representative_rewrites": [],
                "route_back_recommendation": {"route_target": "none", "reason": "none"},
            },
        )
