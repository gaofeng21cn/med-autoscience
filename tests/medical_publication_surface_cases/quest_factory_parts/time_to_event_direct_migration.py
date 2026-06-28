from pathlib import Path

from ..figure_contract_fixtures import evidence_renderer_display_to_claim_fields
from ..shared_base import TIME_TO_EVENT_DIRECT_MIGRATION_DISPLAY_PLAN, dump_json


def _write_time_to_event_direct_migration_surface(quest_root: Path, *, include_f5: bool) -> None:
    paper_root = quest_root / "paper"
    dump_json(
        paper_root / "medical_reporting_contract.json",
        {
            "status": "resolved",
            "display_shell_plan": TIME_TO_EVENT_DIRECT_MIGRATION_DISPLAY_PLAN,
        },
    )
    figure_entries = [
        {
            "figure_id": "F1",
            "template_id": "cohort_flow_figure",
            "renderer_family": "python",
            "input_schema_id": "cohort_flow_shell_inputs_v1",
            "qc_profile": "publication_illustration_flow",
            "qc_result": {
                "status": "pass",
                "checked_at": "2026-04-03T10:00:00+00:00",
                "engine_id": "display_layout_qc_v1",
                "qc_profile": "publication_illustration_flow",
                "layout_sidecar_path": "paper/figures/generated/F1.layout.json",
                "issues": [],
            },
            "title": "Cohort derivation and endpoint inventory",
            "caption": "Cohort flow and endpoint inventory for the formal analysis cohort.",
            "paper_role": "main_text",
            "export_paths": [
                "paper/figures/F1_cohort_flow.png",
                "paper/figures/F1_cohort_flow.svg",
                "paper/figures/F1_cohort_flow.pdf",
            ],
        },
        {
            "figure_id": "F2",
            "template_id": "time_to_event_discrimination_calibration_panel",
            "renderer_family": "r_ggplot2",
            "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
            "qc_profile": "publication_evidence_curve",
            "qc_result": {
                "status": "pass",
                "checked_at": "2026-04-03T10:00:00+00:00",
                "engine_id": "display_layout_qc_v1",
                "qc_profile": "publication_evidence_curve",
                "layout_sidecar_path": "paper/figures/generated/F2.layout.json",
                "issues": [],
            },
            "title": "Discrimination and grouped calibration",
            "caption": "Primary endpoint discrimination and grouped calibration.",
            "paper_role": "main_text",
            "export_paths": ["paper/figures/F2_validation.png", "paper/figures/F2_validation.pdf"],
        },
        {
            "figure_id": "F3",
            "template_id": "time_to_event_risk_group_summary",
            "renderer_family": "r_ggplot2",
            "input_schema_id": "time_to_event_grouped_inputs_v1",
            "qc_profile": "publication_survival_curve",
            "qc_result": {
                "status": "pass",
                "checked_at": "2026-04-03T10:00:00+00:00",
                "engine_id": "display_layout_qc_v1",
                "qc_profile": "publication_survival_curve",
                "layout_sidecar_path": "paper/figures/generated/F3.layout.json",
                "issues": [],
            },
            "title": "Primary risk-group summary",
            "caption": "Predicted versus observed five-year risk and observed event concentration across prespecified tertiles.",
            "paper_role": "main_text",
            "export_paths": ["paper/figures/F3_risk_group_summary.png", "paper/figures/F3_risk_group_summary.pdf"],
        },
        {
            "figure_id": "F4",
            "template_id": "time_to_event_decision_curve",
            "renderer_family": "r_ggplot2",
            "input_schema_id": "time_to_event_decision_curve_inputs_v1",
            "qc_profile": "publication_decision_curve",
            "qc_result": {
                "status": "pass",
                "checked_at": "2026-04-03T10:00:00+00:00",
                "engine_id": "display_layout_qc_v1",
                "qc_profile": "publication_decision_curve",
                "layout_sidecar_path": "paper/figures/generated/F4.layout.json",
                "issues": [],
            },
            "title": "Time-to-event decision curve",
            "caption": "Clinical utility at the prespecified five-year horizon.",
            "paper_role": "main_text",
            "export_paths": ["paper/figures/F4_dca.png", "paper/figures/F4_dca.pdf"],
        },
    ]
    if include_f5:
        figure_entries.append(
            {
                "figure_id": "F5",
                "template_id": "generalizability_subgroup_composite_panel",
                "renderer_family": "r_ggplot2",
                "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
                "qc_profile": "publication_generalizability_subgroup_composite_panel",
                "qc_result": {
                    "status": "pass",
                    "checked_at": "2026-04-03T10:00:00+00:00",
                    "engine_id": "display_layout_qc_v1",
                    "qc_profile": "publication_generalizability_subgroup_composite_panel",
                    "layout_sidecar_path": "paper/figures/generated/F5.layout.json",
                    "issues": [],
                },
                "title": "Internal multicenter generalizability",
                "caption": "Center-level generalizability summary for the internal multicenter evaluation.",
                "paper_role": "main_text",
                "export_paths": ["paper/figures/F5_generalizability.png", "paper/figures/F5_generalizability.pdf"],
            }
        )
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": figure_entries,
        },
    )
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "T1",
                    "table_shell_id": "table1_baseline_characteristics",
                    "input_schema_id": "baseline_characteristics_schema_v1",
                    "qc_profile": "publication_table_baseline",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Patient characteristics",
                    "caption": "Baseline characteristics of the modeling cohort.",
                    "paper_role": "main_text",
                    "asset_paths": ["paper/tables/T1.csv", "paper/tables/T1.md"],
                },
                {
                    "table_id": "T2",
                    "table_shell_id": "table2_time_to_event_performance_summary",
                    "input_schema_id": "time_to_event_performance_summary_v1",
                    "qc_profile": "publication_table_performance",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Time-to-event performance summary",
                    "caption": "Performance summary across primary and supportive endpoints.",
                    "paper_role": "main_text",
                    "asset_paths": ["paper/tables/T2.md"],
                },
            ],
        },
    )
    semantics_entries = [
        {
            "figure_id": "F1",
            "story_role": "study_setup",
            "research_question": "How was the analysis cohort derived and how were the primary endpoints inventoried?",
            "direct_message": "The analytic cohort and endpoint inventory were prespecified before model evaluation.",
            "clinical_implication": "Defines the denominator and endpoint framing for all downstream performance claims.",
            "interpretation_boundary": "Describes cohort derivation and endpoint accounting only.",
            "panel_messages": [{"panel_id": "A", "message": "The cohort derivation is numerically explicit."}],
            "legend_glossary": [{"term": "endpoint inventory", "explanation": "Lists the paper-facing endpoints carried into evaluation."}],
            "threshold_semantics": "No decision threshold is encoded in this illustration.",
            "stratification_basis": "No risk stratification is implied by the cohort flow shell.",
            "recommendation_boundary": "No clinical recommendation is proposed from the cohort flow shell.",
            "renderer_contract": {
                "figure_semantics": "illustration",
                "renderer_family": "python",
                "template_id": "cohort_flow_figure",
                "selection_rationale": "The cohort flow shell is rendered from the audited illustration pipeline.",
                "layout_qc_profile": "publication_illustration_flow",
                "required_exports": ["png", "svg", "pdf"],
                "fallback_on_failure": False,
                "failure_action": "block_and_fix_environment",
            },
        },
        {
            "figure_id": "F2",
            "story_role": "performance_validation",
            "research_question": "Did the primary endpoint show aligned discrimination and grouped calibration?",
            "direct_message": "The primary endpoint showed concordant discrimination and grouped calibration support.",
            "clinical_implication": "Supports calibrated time-to-event risk communication in the main manuscript.",
            "interpretation_boundary": "Internal validation only; no transport claim.",
            "panel_messages": [{"panel_id": "A", "message": "Discrimination and grouped calibration are shown together."}],
            "legend_glossary": [{"term": "grouped calibration", "explanation": "Observed event-free probability across prespecified risk groups."}],
            "threshold_semantics": "No treatment threshold is proposed by the validation panel.",
            "stratification_basis": "Risk groups were prespecified for paper-facing calibration display.",
            "recommendation_boundary": "The panel supports validation, not a clinical intervention threshold.",
            "renderer_contract": {
                "figure_semantics": "evidence",
                "renderer_family": "r_ggplot2",
                "template_id": "time_to_event_discrimination_calibration_panel",
                "selection_rationale": "The validation panel stays on the audited direct-migration template.",
                "layout_qc_profile": "publication_evidence_curve",
                "required_exports": ["png", "pdf"],
                **evidence_renderer_display_to_claim_fields(
                    figure_id="F2",
                    core_claim="Primary endpoint discrimination and grouped calibration support the manuscript validation claim.",
                    panel_role="performance_validation",
                    qa_risk="Discrimination and calibration could be read as transport evidence without the stated boundary.",
                ),
                "fallback_on_failure": False,
                "failure_action": "block_and_fix_environment",
            },
        },
        {
            "figure_id": "F3",
            "story_role": "risk_stratification",
            "research_question": "Did tertile-based grouping concentrate observed events and separate five-year risk?",
            "direct_message": "Observed five-year events concentrated in the highest tertile and were absent in the low-risk tertile.",
            "clinical_implication": "Supports clinically interpretable risk layering in the main manuscript.",
            "interpretation_boundary": "Shows tertile-based five-year risk separation rather than a full survival-curve reconstruction.",
            "panel_messages": [{"panel_id": "A", "message": "Predicted and observed five-year risks rise stepwise from low to high tertiles."}],
            "legend_glossary": [{"term": "risk tertile", "explanation": "Ordered groups formed from predicted five-year risk."}],
            "threshold_semantics": "No intervention threshold is encoded in the tertile summary.",
            "stratification_basis": "Groups are derived from the prespecified manuscript five-year risk stratification.",
            "recommendation_boundary": "Risk-group separation does not by itself define a treatment rule.",
            "renderer_contract": {
                "figure_semantics": "evidence",
                "renderer_family": "r_ggplot2",
                "template_id": "time_to_event_risk_group_summary",
                "selection_rationale": "The manuscript requires the audited two-panel tertile summary rather than a grouped KM default.",
                "layout_qc_profile": "publication_survival_curve",
                "required_exports": ["png", "pdf"],
                **evidence_renderer_display_to_claim_fields(
                    figure_id="F3",
                    core_claim="Risk tertile summaries support the bounded risk-layering interpretation.",
                    panel_role="risk_stratification",
                    qa_risk="Risk-group separation could be mistaken for a treatment rule.",
                ),
                "fallback_on_failure": False,
                "failure_action": "block_and_fix_environment",
            },
        },
        {
            "figure_id": "F4",
            "story_role": "clinical_utility",
            "research_question": "Did the model preserve clinical utility across the prespecified horizon?",
            "direct_message": "Net benefit remained positive across the prespecified threshold range.",
            "clinical_implication": "Supports horizon-aware clinical utility interpretation without overclaiming treatment cut-offs.",
            "interpretation_boundary": "The curve is horizon-specific and does not establish a universal threshold.",
            "panel_messages": [{"panel_id": "A", "message": "Net benefit is summarized over the prespecified threshold range."}],
            "legend_glossary": [{"term": "net benefit", "explanation": "Clinical utility relative to treat-all and treat-none references."}],
            "threshold_semantics": "Thresholds are illustrative operating points, not recommended cut-offs.",
            "stratification_basis": "The decision-curve display is threshold-based rather than group-based.",
            "recommendation_boundary": "No single intervention threshold is recommended from this figure.",
            "renderer_contract": {
                "figure_semantics": "evidence",
                "renderer_family": "r_ggplot2",
                "template_id": "time_to_event_decision_curve",
                "selection_rationale": "The horizon-aware decision curve stays on the audited direct-migration template.",
                "layout_qc_profile": "publication_decision_curve",
                "required_exports": ["png", "pdf"],
                **evidence_renderer_display_to_claim_fields(
                    figure_id="F4",
                    core_claim="Decision-curve evidence supports threshold-aware clinical utility interpretation.",
                    panel_role="clinical_utility",
                    qa_risk="Net benefit curves could be overread as recommending a single operating threshold.",
                ),
                "fallback_on_failure": False,
                "failure_action": "block_and_fix_environment",
            },
        },
    ]
    if include_f5:
        semantics_entries.append(
            {
                "figure_id": "F5",
                "story_role": "generalizability",
                "research_question": "Did the internal multicenter assessment preserve support across centers?",
                "direct_message": "Center-level estimates remained directionally aligned with the overall performance signal.",
                "clinical_implication": "Supports cautious internal generalizability framing in the manuscript discussion.",
                "interpretation_boundary": "Internal center-level support only; not external transport validation.",
                "panel_messages": [{"panel_id": "A", "message": "Center-level interval support is summarized explicitly."}],
                "legend_glossary": [{"term": "center support", "explanation": "Center-level estimate with uncertainty interval."}],
                "threshold_semantics": "No treatment threshold is encoded in the generalizability composite.",
                "stratification_basis": "Centers are displayed as prespecified data-partition units rather than risk strata.",
                "recommendation_boundary": "The overview does not establish external transportability on its own.",
                "renderer_contract": {
                    "figure_semantics": "evidence",
                    "renderer_family": "r_ggplot2",
                    "template_id": "generalizability_subgroup_composite_panel",
                    "selection_rationale": "The subgroup generalizability composite remains on the audited R/ggplot2 template.",
                    "layout_qc_profile": "publication_generalizability_subgroup_composite_panel",
                    "required_exports": ["png", "pdf"],
                    **evidence_renderer_display_to_claim_fields(
                        figure_id="F5",
                        core_claim="Center-level summaries support cautious internal generalizability framing.",
                        panel_role="generalizability",
                        qa_risk="Internal center alignment could be overread as external transport validation.",
                    ),
                    "fallback_on_failure": False,
                    "failure_action": "block_and_fix_environment",
                },
            }
        )
    dump_json(
        paper_root / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": semantics_entries,
        },
    )
    narrative_sections = [
        {
            "section_id": "R1",
            "section_title": "Cohort derivation and baseline definition",
            "research_question": "How was the formal analysis cohort defined?",
            "direct_answer": "The cohort derivation and endpoint inventory were prespecified before evaluation.",
            "supporting_display_items": ["F1", "T1"],
            "key_quantitative_findings": ["Cohort flow and baseline structure were fixed before model evaluation."],
            "clinical_meaning": "Defines the clinical denominator for the current analysis.",
            "boundary": "Descriptive cohort accounting only.",
        },
        {
            "section_id": "R2",
            "section_title": "Primary validation and risk stratification",
            "research_question": "Did the primary endpoint support performance and risk separation?",
            "direct_answer": "Yes. Discrimination, grouped calibration, and grouped survival separation were directionally consistent.",
            "supporting_display_items": ["F2", "F3"],
            "key_quantitative_findings": ["Performance and survival separation remained aligned across the prespecified displays."],
            "clinical_meaning": "Supports the manuscript's risk-stratification framing.",
            "boundary": "Internal validation only.",
        },
        {
            "section_id": "R3",
            "section_title": "Clinical utility",
            "research_question": "Did the model preserve clinical utility at the main horizon?",
            "direct_answer": "Yes. Net benefit remained favorable across the prespecified threshold range.",
            "supporting_display_items": ["F4", "T2"],
            "key_quantitative_findings": ["Clinical utility remained favorable at the manuscript horizon."],
            "clinical_meaning": "Supports threshold-aware clinical interpretation without overclaiming a treatment rule.",
            "boundary": "No universal threshold recommendation is proposed.",
        },
    ]
    if include_f5:
        narrative_sections.append(
            {
                "section_id": "R4",
                "section_title": "Internal multicenter generalizability",
                "research_question": "Was the internal multicenter signal directionally preserved?",
                "direct_answer": "Yes. Center-level support remained directionally aligned with the overall estimate.",
                "supporting_display_items": ["F5"],
                "key_quantitative_findings": ["Center-level support remained within a clinically interpretable range."],
                "clinical_meaning": "Supports cautious generalizability framing within the internal multicenter setting.",
                "boundary": "Internal center-level support only; not external transport validation.",
            }
        )
    dump_json(
        paper_root / "results_narrative_map.json",
        {
            "schema_version": 1,
            "sections": narrative_sections,
        },
    )
