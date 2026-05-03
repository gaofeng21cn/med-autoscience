from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_minimal_section_authority(study_root: Path) -> None:
    paper_root = study_root / "paper"
    _write_json(
        paper_root / "claim_evidence_map.json",
        {
            "claims": [
                {
                    "claim_id": "primary-result",
                    "statement": "The primary result is supported by auditable evidence.",
                    "status": "supported",
                    "paper_role": "main_text",
                    "display_bindings": ["Figure1", "Table1"],
                    "sections": ["introduction", "methods", "results", "discussion"],
                    "evidence_items": [
                        {
                            "item_id": "primary-result-evidence",
                            "support_level": "direct",
                            "source_paths": ["paper/derived_analysis_manifest.json"],
                        }
                    ],
                }
            ]
        },
    )
    (paper_root / "evidence_ledger.md").write_text(
        "# Evidence ledger\n\n- primary-result-evidence: primary numeric and display evidence.\n",
        encoding="utf-8",
    )
    _write_json(
        paper_root / "methods_implementation_manifest.json",
        {
            "study_design": {
                "cohort_definition": "Defined analytic cohort.",
                "endpoint_definition": "Defined endpoint.",
            },
            "statistical_analysis": {
                "primary_metrics": ["risk_difference"],
                "summary_format": "median and interquartile range.",
            },
        },
    )
    _write_json(
        paper_root / "results_narrative_map.json",
        {
            "sections": [
                {
                    "section_id": "results",
                    "section_title": "Results",
                    "research_question": "What did the analysis find?",
                    "direct_answer": "The primary analysis supports the bounded result.",
                    "supporting_display_items": ["Figure1", "Table1"],
                    "key_quantitative_findings": ["The primary metric is grounded in the analysis manifest."],
                    "clinical_meaning": "The result is clinically interpretable.",
                    "boundary": "No causal claim is made.",
                }
            ]
        },
    )
    _write_json(
        paper_root / "figure_semantics_manifest.json",
        {
            "figures": [
                {
                    "figure_id": "Figure1",
                    "story_role": "result_evidence",
                    "research_question": "What display grounds the result?",
                    "direct_message": "The figure presents the primary result.",
                    "clinical_implication": "The result is bounded.",
                    "interpretation_boundary": "No treatment recommendation is made.",
                    "panel_messages": [{"panel_id": "A", "message": "Primary result."}],
                    "legend_glossary": [{"term": "primary", "explanation": "Main analysis."}],
                    "threshold_semantics": "No threshold is introduced.",
                    "stratification_basis": "None.",
                    "recommendation_boundary": "No recommendation.",
                }
            ]
        },
    )
    _write_json(
        paper_root / "derived_analysis_manifest.json",
        {
            "numeric_results": [
                {
                    "result_id": "primary_metric",
                    "source_path": "paper/analysis/primary_metric.csv",
                    "claim_refs": ["primary-result"],
                    "display_refs": ["Figure1", "Table1"],
                }
            ]
        },
    )


def test_section_authoring_work_units_are_read_only_and_ground_all_core_sections(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.section_authoring_work_units")
    study_root = tmp_path / "study"
    _write_minimal_section_authority(study_root)

    result = module.build_section_authoring_work_units(study_root=study_root)

    assert result["surface"] == "section_authoring_work_units"
    assert result["schema_version"] == 1
    assert result["status"] == "ready"
    assert result["can_mutate_package"] is False
    assert result["blockers"] == []
    assert [unit["section"] for unit in result["units"]] == [
        "introduction",
        "methods",
        "results",
        "discussion",
    ]
    for unit in result["units"]:
        assert unit["unit_id"] == f"section_authoring::{unit['section']}"
        assert unit["can_mutate_package"] is False
        assert unit["blockers"] == []
        assert unit["route_back_hint"] == "clear"
        assert "paper/claim_evidence_map.json" in unit["required_refs"]
        assert "paper/evidence_ledger.md" in unit["required_refs"]
        assert "paper/figure_semantics_manifest.json" in unit["grounding"]["display_refs"]
        assert "paper/derived_analysis_manifest.json" in unit["grounding"]["numeric_refs"]

    results_unit = result["units"][2]
    assert "paper/results_narrative_map.json" in results_unit["required_refs"]
    assert "paper/figure_semantics_manifest.json" in results_unit["required_refs"]
    assert "paper/derived_analysis_manifest.json" in results_unit["required_refs"]


def test_section_authoring_work_units_fail_closed_when_required_authority_refs_are_missing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.section_authoring_work_units")
    study_root = tmp_path / "study"
    _write_minimal_section_authority(study_root)
    (study_root / "paper" / "evidence_ledger.md").unlink()
    (study_root / "paper" / "derived_analysis_manifest.json").unlink()

    result = module.build_section_authoring_work_units(study_root=study_root)

    assert result["status"] == "blocked"
    assert result["can_mutate_package"] is False
    assert "missing_ref:paper/evidence_ledger.md" in result["blockers"]
    assert "missing_ref:paper/derived_analysis_manifest.json" in result["blockers"]
    introduction_unit = result["units"][0]
    results_unit = result["units"][2]
    assert introduction_unit["route_back_hint"] == "restore_required_authority_refs"
    assert "missing_ref:paper/evidence_ledger.md" in introduction_unit["blockers"]
    assert "missing_ref:paper/derived_analysis_manifest.json" in results_unit["blockers"]
