from __future__ import annotations

from pathlib import Path

from .shared_base import dump_json


def write_statistical_reviewer_audit_fixture(paper_root: Path) -> None:
    dump_json(
        paper_root / "review" / "statistical_reviewer_audit.json",
        {
            "schema_version": 1,
            "status": "resolved",
            "reviewer_role": "statistical_reviewer",
            "sections": {
                "statistical_plan": {
                    "status": "pass",
                    "assessment": "The statistical plan is prespecified and tied to the main claim.",
                    "evidence_refs": ["paper/methods_implementation_manifest.json"],
                    "manuscript_action": "Keep the methods text aligned with the prespecified plan.",
                },
                "model_or_test_selection": {
                    "status": "pass",
                    "assessment": "Model comparisons are justified by endpoint and validation design.",
                    "evidence_refs": ["paper/methods_implementation_manifest.json"],
                    "manuscript_action": "Report model choice with rationale and comparison boundary.",
                },
                "sample_size_or_precision": {
                    "status": "acceptable_with_boundary",
                    "assessment": "Available sample size and event support require precision-bounded interpretation.",
                    "evidence_refs": ["paper/evidence_ledger.json"],
                    "manuscript_action": "Report uncertainty and avoid unsupported subgroup precision claims.",
                },
                "missing_data": {
                    "status": "pass",
                    "assessment": "Missingness handling is aligned across methods, derived analyses, and reproducibility supplement.",
                    "evidence_refs": [
                        "paper/methods_implementation_manifest.json",
                        "paper/derived_analysis_manifest.json",
                    ],
                    "manuscript_action": "State the missing-data strategy and sensitivity boundary.",
                },
                "sensitivity_analyses": {
                    "status": "pass",
                    "assessment": "Sensitivity analyses address resampling, threshold, and missingness robustness.",
                    "evidence_refs": ["paper/derived_analysis_manifest.json"],
                    "manuscript_action": "Present sensitivity checks as robustness evidence.",
                },
                "subgroup_and_interaction": {
                    "status": "acceptable_with_boundary",
                    "assessment": "Subgroup findings are prespecified and interpreted with support thresholds.",
                    "evidence_refs": ["paper/results_narrative_map.json"],
                    "manuscript_action": "Treat subgroup contrasts as bounded and interaction-aware.",
                },
                "multiplicity": {
                    "status": "pass",
                    "assessment": "Primary and exploratory comparisons are separated with multiplicity guardrails.",
                    "evidence_refs": ["paper/methods_implementation_manifest.json"],
                    "manuscript_action": "Label exploratory contrasts and avoid nominal P-value promotion.",
                },
                "causal_language_boundary": {
                    "status": "pass",
                    "assessment": "The manuscript is bounded to associational prediction language.",
                    "evidence_refs": ["paper/methods_implementation_manifest.json"],
                    "manuscript_action": "Avoid causal effect and treatment-effect wording.",
                    "forbidden_language": ["causal effect", "treatment effect"],
                },
            },
        },
    )


def write_structured_disclosure_audit_fixture(paper_root: Path) -> None:
    dump_json(
        paper_root / "review" / "structured_disclosure_audit.json",
        {
            "schema_version": 1,
            "status": "resolved",
            "ethics": {
                "status": "pass",
                "statement": "IRB approval and consent waiver status are documented for manuscript closeout.",
                "evidence_refs": ["paper/methods_implementation_manifest.json#/study_design/ethics"],
                "manuscript_action": "Carry the ethics statement into the submission metadata surface.",
            },
            "privacy": {
                "status": "pass",
                "statement": "Only deidentified locked analysis outputs are used on paper-facing surfaces.",
                "evidence_refs": ["memory/portfolio/data_assets/private/registry.json"],
                "manuscript_action": "State privacy limits without promising unrestricted patient-level release.",
            },
            "data_availability": {
                "status": "acceptable_with_boundary",
                "statement": "Private clinical data are available subject to institutional and privacy approval.",
                "evidence_refs": ["memory/portfolio/data_assets/impact/latest_impact_report.json"],
                "manuscript_action": "Use bounded data-availability wording tied to registry evidence.",
            },
            "ai_disclosure": {
                "status": "pass",
                "statement": "AI assistance is disclosed as manuscript-support tooling without evidence authority.",
                "evidence_refs": ["paper/review/medical_prose_review.json"],
                "manuscript_action": "Keep AI disclosure separate from scientific evidence claims.",
            },
            "data_asset_evidence": {
                "registry_refs": ["memory/portfolio/data_assets/private/registry.json"],
                "access_evidence": ["access_tier: analysis_ready_standardized"],
                "privacy_evidence": ["deidentified analysis release"],
                "license_evidence": ["institutional clinical data; public reuse not unrestricted"],
            },
        },
    )
