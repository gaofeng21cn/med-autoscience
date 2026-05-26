from __future__ import annotations
import hashlib
import importlib
from pathlib import Path
from typing import Any

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_quality_repair_batch_cases.upstream_paper_owner_surface import (
    _paper_write_supervisor_route_context,
    _write_blocked_publication_eval,
    _write_json,
    _write_quality_summary,
)


def _fingerprint(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"size": len(data), "content_sha256": hashlib.sha256(data).hexdigest()}


def test_medical_prose_write_repair_updates_canonical_story_surface(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_gap",
    )
    quest_id = "quest-003"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    paper_root = study_root / "paper"
    (paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text("# Draft\n\nPrimary-care treatment-gap draft surface.\n", encoding="utf-8")
    _write_json(paper_root / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "evidence_ledger.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "medical_prose_review.json", {"schema_version": 1, "findings": []})
    _write_json(paper_root / "results_narrative_map.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "figure_semantics_manifest.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _write_json(
        paper_root / "dpcc_treatment_gap_alignment.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "treatment_gap_alignment",
                    "rows": [
                        {
                            "phenotype_label": "Adiposity-linked multimorbidity",
                            "index_patients": 181306,
                            "severe_glycemia_low_intensity_gap_patients": 0,
                            "uncontrolled_glycemia_no_drug_gap_patients": 71370,
                            "hypertension_no_antihypertensive_gap_patients": 104900,
                            "dyslipidemia_no_lipid_lowering_gap_patients": 151579,
                        },
                        {
                            "phenotype_label": "Glycemic-dominant diabetes",
                            "index_patients": 104029,
                            "severe_glycemia_low_intensity_gap_patients": 89578,
                            "uncontrolled_glycemia_no_drug_gap_patients": 52071,
                            "hypertension_no_antihypertensive_gap_patients": 74416,
                            "dyslipidemia_no_lipid_lowering_gap_patients": 88999,
                        },
                        {
                            "phenotype_label": "Severe glycemic multimorbidity",
                            "index_patients": 73203,
                            "severe_glycemia_low_intensity_gap_patients": 55480,
                            "uncontrolled_glycemia_no_drug_gap_patients": 24532,
                            "hypertension_no_antihypertensive_gap_patients": 53950,
                            "dyslipidemia_no_lipid_lowering_gap_patients": 55607,
                        },
                    ],
                }
            ],
        },
    )
    (paper_root / "tables").mkdir(parents=True, exist_ok=True)
    (paper_root / "tables" / "T2_phenotype_gap_summary.md").write_text(
        "\n".join(
            [
                "# T2",
                "",
                "| Phenotype | Index patients | Share of index cohort | Mean age, y | Mean BMI | Mean HbA1c | Severe glycemia low-intensity gap | Uncontrolled glycemia with no diabetes drug | Hypertension with no antihypertensive | Dyslipidemia with no lipid-lowering |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| Adiposity-linked multimorbidity | 181306 | 26.17% | 64.99 | 26.69 | 6.59 | NA | 39.36% | 57.86% | 83.60% |",
                "| Glycemic-dominant diabetes | 104029 | 15.02% | 64.44 | 23.05 | 8.04 | 86.11% | 50.05% | 71.52% | 85.55% |",
                "| Severe glycemic multimorbidity | 73203 | 10.57% | 61.21 | 24.91 | 10.69 | 75.79% | 33.51% | 73.68% | 75.96% |",
            ]
        ),
        encoding="utf-8",
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0].update(
        {
            "action_type": "route_back_same_line",
            "route_target": "write",
            "route_key_question": "Repair current AI reviewer medical-prose findings.",
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
                "summary": "Repair the manuscript body against current AI reviewer prose findings.",
            },
        }
    )
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_quality_summary(study_root)

    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": ["medical_publication_surface_blocked", "reviewer_first_concerns_unresolved"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["medical_prose_quality_blocked"],
            "current_required_action": "return_to_publishability_gate",
            "gate_fingerprint": "publication-gate::medical-prose",
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
            "selected_publication_work_unit": {"unit_id": "medical_prose_write_repair"},
            "gate_replay": {
                "status": "blocked",
                "report_json": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
            "unit_results": [],
        },
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context=_paper_write_supervisor_route_context(),
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert "writer_worker_handoff" not in result
    evidence = result["repair_execution_evidence"]
    assert evidence["status"] == "progress_delta_candidate"
    assert evidence["progress_delta_candidate"] is True
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_required"] is True
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_present"] is True
    changed_paths = {
        Path(ref["path"]).relative_to(study_root).as_posix()
        for ref in evidence["canonical_artifact_delta"]["artifact_refs"]
    }
    assert "paper/claim_evidence_map.json" in changed_paths
    assert "paper/evidence_ledger.json" in changed_paths
    assert "paper/review/review_ledger.json" in changed_paths
    assert "paper/draft.md" in changed_paths
    assert "paper/build/review_manuscript.md" in changed_paths
    story_text = (paper_root / "draft.md").read_text(encoding="utf-8")
    assert "Phenotype derivation and assignment" in story_text
    assert "recorded treatment-review gap" in story_text
    assert "Data quality assessment" in story_text
    assert "Baseline characteristics" in story_text
    assert "first qualifying diabetes-coded visit" in story_text
    assert "reproducible without model fitting" in story_text
    assert "severe-glycemia patients as the eligible denominator" in story_text
    assert "uncontrolled-glycemia patients as the eligible denominator" in story_text
    assert "A Not assessed cell means the indicator was outside the phenotype-specific eligible denominator" in story_text
    assert "Medication exposure was limited to medication classes recorded in the DPCC primary-care release" in story_text
    assert "Missing values were not imputed" in story_text
    assert "row-level, variable-level, or eligibility-level consequences" in story_text
    assert "first and last phenotype-ready visits" in story_text
    assert "dominant-site deterministic partition" in story_text
    assert "Study design and cohort" in story_text
    assert "Variable definition and measurement" in story_text
    assert "Model or grouping framework" in story_text
    assert "Validation framework" in story_text
    assert "Table 1 is the cohort-assembly and data-quality table" in story_text
    assert "Table 2 is the phenotype-level baseline-characteristics table" in story_text
    assert "No sampling-based 95% confidence intervals were calculated" in story_text
    assert "Python" in story_text
    assert "71,370 of 181,306" in story_text
    assert "104,900 of 181,306" in story_text
    assert "151,579 of 181,306" in story_text
    forbidden_runtime_terms = (
        "MAS",
        "AI reviewer",
        "verified outputs",
        "accepted records",
        "source gaps",
        "submission readiness",
        "repair note",
        "before manuscript repair",
        "quality repair",
        "publication gate",
    )
    assert not any(term in story_text for term in forbidden_runtime_terms)
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == story_text
    assert not (study_root / "manuscript" / "current_package").exists()
    assert not (paper_root / "submission_minimal").exists()


def test_medical_prose_write_repair_preserves_current_writer_story_delta(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_gap",
    )
    quest_id = "quest-003"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    paper_root = study_root / "paper"
    old_text = "# Draft\n\nPrimary-care treatment-gap draft surface before the writer revision.\n"
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        path = paper_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(old_text, encoding="utf-8")
    old_refs = [
        {
            "path": str((paper_root / relative_path).resolve()),
            "artifact_role": "canonical_manuscript_story_surface",
            "fingerprint": _fingerprint(paper_root / relative_path),
        }
        for relative_path in ("draft.md", "build/review_manuscript.md")
    ]
    writer_story = "\n\n".join(
        [
            "# Clinically interpretable diabetes phenotypes and recorded treatment-review gaps in Hunan primary care",
            "## Abstract",
            "**Background:** Primary-care diabetes services need reproducible phenotype summaries that connect clinical burden with documented medication coverage.",
            "**Methods:** The study used 1,779,360 DPCC records and 692,702 adult index patients. Phenotypes were assigned with a deterministic rule hierarchy, not a fitted clustering or prediction model.",
            "**Results:** Six phenotypes were retained; severe glycemic multimorbidity and glycemic-dominant diabetes had the largest glycemic burden. Regional treatment review should begin with the phenotype-specific denominator, because each recorded treatment-review gap used its own eligible denominator.",
            "**Conclusions:** The findings support regional service review and prospective validation.",
            "## Introduction",
            "The clinical problem is the heterogeneity of diabetes management needs in primary care. Prior subclassification literature shows that diabetes is not a single clinical pattern, but routine-care networks also need transparent service-review groupings.",
            "This study addressed the evidence gap by asking whether DPCC records could define reproducible phenotypes and phenotype-specific recorded treatment-review gaps without converting the analysis into individualized treatment advice.",
            "## Methods",
            "### Study design and cohort",
            "We conducted a retrospective descriptive study of deidentified DPCC primary-care records from May 2020 through December 2025. The index encounter was the first qualifying diabetes-coded visit after semantic-audit plausibility filtering.",
            "### Variable definition and measurement",
            "Candidate domains included age, sex, BMI, waist circumference, HbA1c, fasting glucose, lipid measures, eGFR, diagnoses, medication records, visit structure, and site identifiers. Missing values were not imputed.",
            "### Phenotype derivation and assignment",
            "Phenotype derivation used a prespecified deterministic hierarchy: severe glycemic multimorbidity, adiposity-linked multimorbidity, glycemic-dominant diabetes, adiposity-dominant diabetes, cardiometabolic-risk dominant diabetes, and lower-burden diabetes. The assignment is reproducible for a new patient by applying the same index-visit rules.",
            "### Model or grouping framework",
            "No clustering model, latent-class model, treatment-effect model, or individualized prediction model was fitted. The grouping framework was a clinical rule hierarchy.",
            "### Validation framework",
            "First-to-last repeated-visit transitions and deterministic dominant-site support were used as within-network support checks, not external validation.",
            "### Data quality assessment",
            "Blood-pressure semantic inversion was handled as a data-quality boundary, so blood-pressure control status was excluded while hypertension context was interpreted cautiously.",
            "### Statistical analysis",
            "Analyses were descriptive and used counts, percentages, and phenotype-level means. No model-based confidence intervals were introduced for the release-level descriptive counts.",
            "## Results",
            "The index cohort included 692,702 adults with diabetes. Six phenotype groups accounted for the full index cohort, and recorded treatment-review gap rates varied by phenotype and eligible denominator.",
            "## Discussion",
            "The principal finding is that a reproducible clinical hierarchy separated different service-review problems inside one regional diabetes network. This interpretation is useful for local review and prospective evaluation.",
            "## Limitations",
            "Medication capture was limited to recorded primary-care medication fields, and blood-pressure target attainment was not assessed because of the semantic-field issue.",
            "## Conclusion",
            "A deterministic DPCC phenotype hierarchy identified clinically interpretable groups with distinct recorded medication-coverage patterns.",
        ]
    ) + "\n"
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        (paper_root / relative_path).write_text(writer_story, encoding="utf-8")
    _write_json(paper_root / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "evidence_ledger.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "medical_prose_review.json", {"schema_version": 1, "findings": []})
    _write_json(paper_root / "results_narrative_map.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "figure_semantics_manifest.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0].update(
        {
            "action_type": "route_back_same_line",
            "route_target": "write",
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
                "summary": "Repair the manuscript body against current medical-prose findings.",
            },
        }
    )
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_quality_summary(study_root)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": publication_eval_payload["eval_id"],
            "status": "handoff_ready",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "repair_execution_evidence": {
                "status": "blocked",
                "blockers": ["manuscript_story_surface_delta_missing"],
                "manuscript_surface_hygiene": {
                    "status": "blocked",
                    "surface_refs": old_refs,
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                    "story_surface_delta_refs": [],
                },
            },
        },
    )

    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": ["medical_publication_surface_blocked", "reviewer_first_concerns_unresolved"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["medical_prose_quality_blocked"],
            "current_required_action": "return_to_publishability_gate",
            "gate_fingerprint": "publication-gate::medical-prose",
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
            "selected_publication_work_unit": {"unit_id": "medical_prose_write_repair"},
            "gate_replay": {
                "status": "blocked",
                "report_json": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
            "unit_results": [],
        },
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context=_paper_write_supervisor_route_context(),
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert (paper_root / "draft.md").read_text(encoding="utf-8") == writer_story
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == writer_story
    story_refs = result["repair_execution_evidence"]["manuscript_surface_hygiene"]["story_surface_delta_refs"]
    assert {
        Path(ref["path"]).relative_to(study_root).as_posix()
        for ref in story_refs
    } == {"paper/draft.md", "paper/build/review_manuscript.md"}
    assert {ref["fingerprint"]["content_sha256"] for ref in story_refs} == {
        _fingerprint(paper_root / "draft.md")["content_sha256"]
    }


def test_medical_prose_write_repair_preserves_medication_coverage_writer_story_delta(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_gap",
    )
    quest_id = "quest-003"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    paper_root = study_root / "paper"
    old_text = "# Draft\n\nPrimary-care treatment-gap draft surface before the writer revision.\n"
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        path = paper_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(old_text, encoding="utf-8")
    old_refs = [
        {
            "path": str((paper_root / relative_path).resolve()),
            "artifact_role": "canonical_manuscript_story_surface",
            "fingerprint": _fingerprint(paper_root / relative_path),
        }
        for relative_path in ("draft.md", "build/review_manuscript.md")
    ]
    writer_story = "\n\n".join(
        [
            "# Clinically interpretable diabetes phenotypes and recorded medication-coverage gaps in Hunan primary care",
            "## Abstract",
            "**Background:** Primary-care diabetes services need reproducible phenotype summaries that connect clinical burden with documented medication coverage.",
            "**Methods:** The study used 1,779,360 DPCC records and 692,702 adult index patients. Phenotype derivation used a deterministic clinical hierarchy rather than fitted clustering.",
            "**Results:** Six phenotypes were retained. Recorded medication-coverage gaps were reported with phenotype-specific eligible denominators.",
            "**Conclusions:** The findings support regional service review and prospective validation.",
            "## Introduction",
            "The clinical problem is the heterogeneity of diabetes management needs in primary care.",
            "## Methods",
            "### Study design and cohort",
            "We conducted a retrospective descriptive study of deidentified DPCC primary-care records.",
            "### Variable definition and measurement",
            "Candidate domains included age, BMI, HbA1c, fasting glucose, cardiometabolic context, and medication records.",
            "### Phenotype derivation and assignment",
            "Phenotype derivation used a prespecified deterministic hierarchy that can be reproduced for a new index patient.",
            "### Model or grouping framework",
            "No clustering model, treatment-effect model, or individualized prediction model was fitted.",
            "### Validation framework",
            "Repeated-visit transitions and site support were used as descriptive within-network support checks.",
            "### Data quality assessment",
            "Data quality checks defined the blood-pressure boundary before interpreting hypertension context.",
            "### Statistical analysis",
            "Statistical analysis used counts, percentages, denominators, and descriptive summaries.",
            "## Results",
            "The index cohort included 692,702 adults with diabetes. Recorded medication-coverage gap rates varied by phenotype and eligible denominator.",
            "## Discussion",
            "The principal finding is that a reproducible clinical hierarchy separated different service-review problems inside one regional diabetes network.",
            "## Limitations",
            "Medication capture was limited to recorded primary-care medication fields.",
            "## Conclusion",
            "A deterministic DPCC phenotype hierarchy identified clinically interpretable groups with distinct recorded medication-coverage gap profiles.",
        ]
    ) + "\n"
    for relative_path in ("draft.md", "build/review_manuscript.md"):
        (paper_root / relative_path).write_text(writer_story, encoding="utf-8")
    _write_json(paper_root / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "evidence_ledger.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "medical_prose_review.json", {"schema_version": 1, "findings": []})
    _write_json(paper_root / "results_narrative_map.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "figure_semantics_manifest.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    publication_eval_payload["recommended_actions"][0].update(
        {
            "action_type": "route_back_same_line",
            "route_target": "write",
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
                "summary": "Repair the manuscript body against current medical-prose findings.",
            },
        }
    )
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    _write_quality_summary(study_root)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": publication_eval_payload["eval_id"],
            "status": "handoff_ready",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "repair_execution_evidence": {
                "status": "blocked",
                "blockers": ["manuscript_story_surface_delta_missing"],
                "manuscript_surface_hygiene": {
                    "status": "blocked",
                    "surface_refs": old_refs,
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": False,
                    "story_surface_delta_refs": [],
                },
            },
        },
    )

    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": ["medical_publication_surface_blocked", "reviewer_first_concerns_unresolved"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["medical_prose_quality_blocked"],
            "current_required_action": "return_to_publishability_gate",
            "gate_fingerprint": "publication-gate::medical-prose",
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
            "selected_publication_work_unit": {"unit_id": "medical_prose_write_repair"},
            "gate_replay": {
                "status": "blocked",
                "report_json": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
            "unit_results": [],
        },
    )

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context=_paper_write_supervisor_route_context(),
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert (paper_root / "draft.md").read_text(encoding="utf-8") == writer_story
    assert (paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8") == writer_story
    story_refs = result["repair_execution_evidence"]["manuscript_surface_hygiene"]["story_surface_delta_refs"]
    assert {
        Path(ref["path"]).relative_to(study_root).as_posix()
        for ref in story_refs
    } == {"paper/draft.md", "paper/build/review_manuscript.md"}
    assert {ref["fingerprint"]["content_sha256"] for ref in story_refs} == {
        _fingerprint(paper_root / "draft.md")["content_sha256"]
    }
    assert "recorded treatment-review gap" not in (paper_root / "draft.md").read_text(encoding="utf-8")


def test_medical_prose_write_repair_uses_explicit_route_context_when_gate_result_lacks_selection(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="primary_care_gap",
    )
    quest_id = "quest-003"
    quest_root = profile.managed_runtime_quests_root / quest_id
    _write_json(quest_root / "runtime_state.json", {"quest_id": quest_id, "status": "waiting_for_user"})
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\nstudy_id: {study_root.name}\n", encoding="utf-8")
    paper_root = study_root / "paper"
    (paper_root / "draft.md").parent.mkdir(parents=True, exist_ok=True)
    (paper_root / "draft.md").write_text("# Draft\n\nPrimary-care treatment-gap draft surface.\n", encoding="utf-8")
    _write_json(paper_root / "claim_evidence_map.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "evidence_ledger.json", {"schema_version": 1, "claims": []})
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "medical_prose_review.json", {"schema_version": 1, "findings": []})
    _write_json(paper_root / "results_narrative_map.json", {"schema_version": 1, "sections": []})
    _write_json(paper_root / "figure_semantics_manifest.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _write_json(
        paper_root / "dpcc_treatment_gap_alignment.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "treatment_gap_alignment",
                    "rows": [
                        {
                            "phenotype_label": "Adiposity-linked multimorbidity",
                            "index_patients": 181306,
                            "severe_glycemia_low_intensity_gap_patients": 0,
                            "uncontrolled_glycemia_no_drug_gap_patients": 71370,
                            "hypertension_no_antihypertensive_gap_patients": 104900,
                            "dyslipidemia_no_lipid_lowering_gap_patients": 151579,
                        },
                        {
                            "phenotype_label": "Glycemic-dominant diabetes",
                            "index_patients": 104029,
                            "severe_glycemia_low_intensity_gap_patients": 89578,
                            "uncontrolled_glycemia_no_drug_gap_patients": 52071,
                            "hypertension_no_antihypertensive_gap_patients": 74416,
                            "dyslipidemia_no_lipid_lowering_gap_patients": 88999,
                        },
                        {
                            "phenotype_label": "Severe glycemic multimorbidity",
                            "index_patients": 73203,
                            "severe_glycemia_low_intensity_gap_patients": 55480,
                            "uncontrolled_glycemia_no_drug_gap_patients": 24532,
                            "hypertension_no_antihypertensive_gap_patients": 53950,
                            "dyslipidemia_no_lipid_lowering_gap_patients": 55607,
                        },
                    ],
                }
            ],
        },
    )
    (paper_root / "tables").mkdir(parents=True, exist_ok=True)
    (paper_root / "tables" / "T2_phenotype_gap_summary.md").write_text(
        "\n".join(
            [
                "# T2",
                "",
                "| Phenotype | Index patients | Share of index cohort | Mean age, y | Mean BMI | Mean HbA1c | Severe glycemia low-intensity gap | Uncontrolled glycemia with no diabetes drug | Hypertension with no antihypertensive | Dyslipidemia with no lipid-lowering |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| Adiposity-linked multimorbidity | 181306 | 26.17% | 64.99 | 26.69 | 6.59 | NA | 39.36% | 57.86% | 83.60% |",
                "| Glycemic-dominant diabetes | 104029 | 15.02% | 64.44 | 23.05 | 8.04 | 86.11% | 50.05% | 71.52% | 85.55% |",
                "| Severe glycemic multimorbidity | 73203 | 10.57% | 61.21 | 24.91 | 10.69 | 75.79% | 33.51% | 73.68% | 75.96% |",
            ]
        ),
        encoding="utf-8",
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id=quest_id)
    _write_quality_summary(study_root)

    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch.publication_gate,
        "build_gate_report",
        lambda _state: {
            "status": "blocked",
            "blockers": ["medical_publication_surface_blocked", "reviewer_first_concerns_unresolved"],
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["medical_prose_quality_blocked"],
            "current_required_action": "return_to_publishability_gate",
            "gate_fingerprint": "publication-gate::medical-prose",
        },
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "run_gate_clearing_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
            "gate_replay": {
                "status": "blocked",
                "report_json": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
            "unit_results": [],
        },
    )
    route_context = {
        **_paper_write_supervisor_route_context(),
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "requires_human_confirmation": False,
            "source_eval_id": publication_eval_payload["eval_id"],
            "work_unit_fingerprint": "medical-prose-routeback::write::current",
        },
    }

    result = module.run_quality_repair_batch(
        profile=profile,
        study_id=study_root.name,
        study_root=study_root,
        quest_id=quest_id,
        source="test-source",
        authority_route_context=route_context,
    )

    assert result["ok"] is True
    assert result["status"] == "executed"
    assert "writer_worker_handoff" not in result
    evidence = result["repair_execution_evidence"]
    assert evidence["repair_work_unit"]["unit_id"] == "medical_prose_write_repair"
    assert evidence["manuscript_surface_hygiene"]["story_surface_delta_present"] is True
    changed_paths = {
        Path(ref["path"]).relative_to(study_root).as_posix()
        for ref in evidence["canonical_artifact_delta"]["artifact_refs"]
    }
    assert "paper/draft.md" in changed_paths
    assert "paper/build/review_manuscript.md" in changed_paths
    story_text = (paper_root / "draft.md").read_text(encoding="utf-8")
    assert "Phenotype derivation and assignment" in story_text
    assert "recorded treatment-review gap" in story_text
