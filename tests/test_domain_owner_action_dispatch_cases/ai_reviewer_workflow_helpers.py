from __future__ import annotations

from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import write_json as _write_json


def _complete_ai_reviewer_input_refs(
    study_root: Path,
    *,
    publication_gate_projection: Path | None = None,
    extra_refs: dict[str, Path] | None = None,
) -> dict[str, dict[str, object]]:
    refs = {
        "manuscript": {"path": str(study_root / "paper" / "draft.md"), "present": True, "valid": True},
        "evidence_ledger": {"path": str(study_root / "paper" / "evidence_ledger.json"), "present": True, "valid": True},
        "review_ledger": {
            "path": str(study_root / "paper" / "review" / "review_ledger.json"),
            "present": True,
            "valid": True,
        },
        "study_charter": {
            "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "present": True,
            "valid": True,
        },
        "medical_manuscript_blueprint": {
            "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
            "present": True,
            "valid": True,
        },
        "claim_evidence_map": {
            "path": str(study_root / "paper" / "claim_evidence_map.json"),
            "present": True,
            "valid": True,
        },
        "medical_prose_review": {
            "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
            "present": True,
            "valid": True,
        },
        "publication_gate_projection": {
            "path": str(publication_gate_projection or study_root / "artifacts" / "publication_eval" / "latest.json"),
            "present": True,
            "valid": True,
        },
    }
    for ref_name, ref_path in (extra_refs or {}).items():
        refs[ref_name] = {"path": str(ref_path), "present": True, "valid": True}
    return refs


def _write_medical_prose_review_request_inputs(study_root: Path, *, study_id: str) -> None:
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
            "study_id": study_id,
            "clinical_problem": "Primary care diabetes management needs reproducible treatment-gap measurement.",
            "evidence_gap": "Prior regional reports do not separate recorded coverage gaps from causal treatment effects.",
            "study_objective": "To describe DPCC diabetes phenotypes and recorded treatment-review gaps.",
            "target_population": "Adults with diabetes in the DPCC primary-care network.",
            "study_design": "Retrospective descriptive clinical epidemiology study.",
            "main_findings_by_clinical_importance": [
                {"rank": 1, "clinical_finding": "Recorded medication-coverage gaps vary by phenotype."}
            ],
            "clinical_interpretation": "Interpret treatment gaps as documentation-aware review targets.",
            "claim_evidence_map": [{"claim_id": "C1", "statement": "Recorded gaps differ across phenotypes."}],
            "figure_table_rhetorical_roles": [
                {"display_id": "T1", "rhetorical_role": "Defines baseline characteristics."}
            ],
            "discussion_claim_boundary": "Do not infer treatment effects or national representativeness.",
            "limitations": ["Medication data may miss outside prescriptions."],
            "journal_voice_target": {"voice": "neutral_clinical_original_research"},
            "source_refs": [str(study_root / "paper" / "claim_evidence_map.json")],
        },
    )
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claims": [{"claim_id": "C1"}]})
    _write_json(
        study_root / "paper" / "results_narrative_map.json",
        {"sections": [{"section_id": "results", "direct_answer": "Recorded gaps varied across phenotypes."}]},
    )
    _write_json(
        study_root / "paper" / "figure_semantics_manifest.json",
        {"figures": [{"figure_id": "T1", "direct_message": "Baseline characteristics by phenotype."}]},
    )
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"items": []})
    draft = study_root / "paper" / "draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(
        "# Draft\n\n## Methods\n\nWe defined the DPCC cohort, phenotypes, and recorded treatment-review gaps.\n",
        encoding="utf-8",
    )
