from __future__ import annotations


def evidence_renderer_display_to_claim_fields(
    *,
    figure_id: str,
    core_claim: str,
    panel_role: str,
    qa_risk: str,
) -> dict[str, object]:
    return {
        "core_claim": core_claim,
        "evidence_chain": [
            f"paper/results_narrative_map.json#{figure_id}",
            f"paper/figures/figure_catalog.json#{figure_id}",
        ],
        "panel_role": panel_role,
        "source_data_refs": [
            "paper/evidence_ledger.json#EXP-001",
        ],
        "statistics_refs": [
            "paper/statistical_analysis_plan.json#primary-analysis",
        ],
        "export_contract": {
            "required_formats": ["png", "pdf"],
            "archive_ref": f"paper/figures/generated/{figure_id}",
        },
        "qa_risks": [
            qa_risk,
        ],
    }


def default_threshold_renderer_contract() -> dict[str, object]:
    return {
        "figure_semantics": "evidence",
        "renderer_family": "r_ggplot2",
        "template_id": "roc_curve_binary",
        "selection_rationale": (
            "This result figure is regenerated from the locked R analysis stack so the plotted "
            "evidence remains coupled to the audited statistical outputs."
        ),
        "layout_qc_profile": "publication_evidence_curve",
        "required_exports": ["png", "pdf"],
        **evidence_renderer_display_to_claim_fields(
            figure_id="F4",
            core_claim="Threshold-level operating summaries support bounded clinical translation without establishing treatment cut-offs.",
            panel_role="threshold_interpretation",
            qa_risk="Threshold summaries could be mistaken for recommended intervention cut-offs.",
        ),
        "fallback_on_failure": False,
        "failure_action": "block_and_fix_environment",
    }
