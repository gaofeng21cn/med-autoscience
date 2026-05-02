from __future__ import annotations

from pathlib import Path

import pytest


def _audit_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "surface": "retrospective_medical_prose_audit",
        "audit_policy_id": "medical_journal_prose_retrospective_audit_v1",
        "style_corpus_ref": "/tmp/study/paper/medical_journal_style_corpus.json",
        "samples": [
            {
                "sample_id": "nf-pitnet-003",
                "study_label": "NF-PitNET 003 endocrine burden follow-up",
                "source_ref": "/Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup/paper/draft.md",
                "style_score": 42,
                "overall_style_verdict": "work_report_like",
                "work_report_residue": {
                    "diagnosis": "Internal manuscript-control language remains visible.",
                    "examples": ["Figure and Table Anchors", "paper protagonist"],
                },
                "results_subject_information_flow": {
                    "diagnosis": "Results sometimes make displays or model labels the subject.",
                    "route_back": "write",
                },
                "discussion_restraint": {
                    "diagnosis": "Discussion is mostly restrained but still self-describes the manuscript.",
                    "route_back": "write",
                },
                "top_three_paragraphs_to_rewrite": [
                    {"section": "Methods", "reason": "Internal claim-boundary wording leaks into the paper."},
                    {"section": "Results", "reason": "Model-role language should become clinical finding language."},
                    {"section": "Discussion", "reason": "Self-description should become restrained interpretation."},
                ],
                "route_back_recommendation": {
                    "route_target": "write",
                    "reason": "Rewrite from blueprint and AI prose review.",
                },
            },
            {
                "sample_id": "dpcc-003",
                "study_label": "DPCC 003 primary-care phenotype treatment gap",
                "source_ref": "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/003-dpcc-primary-care-phenotype-treatment-gap/manuscript/current_package/review_manuscript.md",
                "style_score": 58,
                "overall_style_verdict": "mixed",
                "work_report_residue": {"diagnosis": "Some delivery-package language remains.", "examples": []},
                "results_subject_information_flow": {"diagnosis": "Clinical groups usually lead.", "route_back": "write"},
                "discussion_restraint": {"diagnosis": "Claims remain mostly descriptive.", "route_back": "review"},
                "top_three_paragraphs_to_rewrite": [
                    {"section": "Introduction", "reason": "Sharpen evidence gap."},
                    {"section": "Results", "reason": "Order findings by clinical importance."},
                    {"section": "Discussion", "reason": "State limitations as boundaries."},
                ],
                "route_back_recommendation": {"route_target": "write", "reason": "Tighten medical prose."},
            },
            {
                "sample_id": "dpcc-004",
                "study_label": "DPCC 004 longitudinal care inertia intensification gap",
                "source_ref": "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/004-dpcc-longitudinal-care-inertia-intensification-gap/manuscript/current_package/manuscript_source.md",
                "style_score": 55,
                "overall_style_verdict": "mixed",
                "work_report_residue": {"diagnosis": "Evidence-led but package-QC language can leak.", "examples": []},
                "results_subject_information_flow": {"diagnosis": "Outcome findings should consistently lead.", "route_back": "write"},
                "discussion_restraint": {"diagnosis": "Treatment-change interpretation remains conservative.", "route_back": "review"},
                "top_three_paragraphs_to_rewrite": [
                    {"section": "Results", "reason": "Lead with care-gap finding."},
                    {"section": "Discussion", "reason": "Separate implication from causal language."},
                    {"section": "Limitations", "reason": "Integrate limitations with claim boundaries."},
                ],
                "route_back_recommendation": {"route_target": "write", "reason": "Use AI prose rewrite plan."},
            },
        ],
        "regression_fixture_contract": {
            "mode": "repo_level_pipeline_regression_fixture",
            "manual_study_patch_allowed": False,
            "used_for": ["medical prose review regression"],
        },
    }


def test_retrospective_request_names_existing_replay_samples(tmp_path: Path) -> None:
    from med_autoscience.retrospective_medical_prose_audit import (
        materialize_retrospective_medical_prose_audit_request,
    )

    study_root = tmp_path / "study"
    result = materialize_retrospective_medical_prose_audit_request(study_root=study_root)
    payload = (study_root / "artifacts" / "publication_eval" / "retrospective_medical_prose_audit_request.json").read_text(
        encoding="utf-8"
    )

    assert result["artifact_path"].endswith("retrospective_medical_prose_audit_request.json")
    assert "nf-pitnet-003" in payload
    assert "dpcc-003" in payload
    assert "dpcc-004" in payload
    assert "manual_study_patch_allowed" in payload
    assert "ai_reviewer" in payload


def test_retrospective_audit_materializes_ai_owned_fixture_baseline(tmp_path: Path) -> None:
    from med_autoscience.retrospective_medical_prose_audit import (
        materialize_retrospective_medical_prose_audit,
        read_retrospective_medical_prose_audit,
    )

    study_root = tmp_path / "study"
    result = materialize_retrospective_medical_prose_audit(study_root=study_root, payload=_audit_payload())
    payload = read_retrospective_medical_prose_audit(study_root=study_root)

    assert result["artifact_path"].endswith("retrospective_medical_prose_audit.json")
    assert payload["assessment_provenance"]["owner"] == "ai_reviewer"
    assert payload["regression_fixture_contract"]["manual_study_patch_allowed"] is False
    sample_by_id = {sample["sample_id"]: sample for sample in payload["samples"]}
    assert sample_by_id["nf-pitnet-003"]["overall_style_verdict"] == "work_report_like"
    assert len(sample_by_id["dpcc-004"]["top_three_paragraphs_to_rewrite"]) == 3


def test_retrospective_audit_requires_all_replay_samples(tmp_path: Path) -> None:
    from med_autoscience.retrospective_medical_prose_audit import materialize_retrospective_medical_prose_audit

    payload = _audit_payload()
    payload["samples"] = payload["samples"][:2]  # type: ignore[index]

    with pytest.raises(ValueError, match="dpcc-004"):
        materialize_retrospective_medical_prose_audit(study_root=tmp_path / "study", payload=payload)
