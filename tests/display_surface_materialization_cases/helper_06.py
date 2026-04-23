from __future__ import annotations

from . import shared_base as _shared_base
from . import helper_05 as _helper_prev

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared_base)
_module_reexport(_helper_prev)

def _make_genomic_alteration_multiomic_consequence_panel_display(display_id: str = "Figure40") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": full_id("genomic_alteration_multiomic_consequence_panel"),
        "title": "Driver-linked genomic alteration landscape with multiomic downstream consequence panels",
        "caption": (
            "Shared landscape governance and fixed three-layer multiomic consequence evidence stay inside one "
            "audited broader genomic composite contract."
        ),
        "y_label": "Altered gene",
        "burden_axis_label": "Altered genes",
        "frequency_axis_label": "Altered samples (%)",
        "alteration_legend_title": "Genomic alteration",
        "gene_order": [
            {"label": "TP53"},
            {"label": "KRAS"},
            {"label": "EGFR"},
            {"label": "PIK3CA"},
        ],
        "sample_order": [
            {"sample_id": "D1"},
            {"sample_id": "D2"},
            {"sample_id": "V1"},
            {"sample_id": "V2"},
        ],
        "annotation_tracks": [
            {
                "track_id": "cohort",
                "track_label": "Cohort",
                "values": [
                    {"sample_id": "D1", "category_label": "Discovery"},
                    {"sample_id": "D2", "category_label": "Discovery"},
                    {"sample_id": "V1", "category_label": "Validation"},
                    {"sample_id": "V2", "category_label": "Validation"},
                ],
            },
            {
                "track_id": "response",
                "track_label": "Response",
                "values": [
                    {"sample_id": "D1", "category_label": "Responder"},
                    {"sample_id": "D2", "category_label": "Non-responder"},
                    {"sample_id": "V1", "category_label": "Responder"},
                    {"sample_id": "V2", "category_label": "Non-responder"},
                ],
            },
        ],
        "alteration_records": [
            {"sample_id": "D1", "gene_label": "TP53", "mutation_class": "missense", "cnv_state": "loss"},
            {"sample_id": "D2", "gene_label": "KRAS", "cnv_state": "amplification"},
            {"sample_id": "V1", "gene_label": "TP53", "mutation_class": "truncating"},
            {"sample_id": "V1", "gene_label": "PIK3CA", "cnv_state": "gain"},
            {"sample_id": "V2", "gene_label": "EGFR", "mutation_class": "fusion", "cnv_state": "amplification"},
        ],
        "consequence_x_label": "Effect size",
        "consequence_y_label": "-log10 adjusted P",
        "consequence_legend_title": "Consequence class",
        "effect_threshold": 1.0,
        "significance_threshold": 2.0,
        "driver_gene_order": [
            {"label": "TP53"},
            {"label": "EGFR"},
        ],
        "consequence_panel_order": [
            {"panel_id": "proteome", "panel_title": "Proteome consequence"},
            {"panel_id": "phosphoproteome", "panel_title": "Phosphoproteome consequence"},
            {"panel_id": "glycoproteome", "panel_title": "Glycoproteome consequence"},
        ],
        "consequence_points": [
            {
                "panel_id": "proteome",
                "gene_label": "TP53",
                "effect_value": 1.18,
                "significance_value": 3.28,
                "regulation_class": "upregulated",
            },
            {
                "panel_id": "proteome",
                "gene_label": "EGFR",
                "effect_value": -1.07,
                "significance_value": 2.84,
                "regulation_class": "downregulated",
            },
            {
                "panel_id": "phosphoproteome",
                "gene_label": "TP53",
                "effect_value": 1.42,
                "significance_value": 3.75,
                "regulation_class": "upregulated",
            },
            {
                "panel_id": "phosphoproteome",
                "gene_label": "EGFR",
                "effect_value": -1.24,
                "significance_value": 3.19,
                "regulation_class": "downregulated",
            },
            {
                "panel_id": "glycoproteome",
                "gene_label": "TP53",
                "effect_value": 1.06,
                "significance_value": 2.91,
                "regulation_class": "upregulated",
            },
            {
                "panel_id": "glycoproteome",
                "gene_label": "EGFR",
                "effect_value": -0.95,
                "significance_value": 2.43,
                "regulation_class": "background",
            },
        ],
    }

def _make_genomic_alteration_pathway_integrated_composite_panel_display(
    display_id: str = "Figure41",
) -> dict[str, object]:
    display = _make_genomic_alteration_multiomic_consequence_panel_display(display_id)
    display["template_id"] = full_id("genomic_alteration_pathway_integrated_composite_panel")
    display["title"] = "Driver-linked genomic alteration landscape with multiomic and pathway-integrated consequence panels"
    display["caption"] = (
        "One audited composite binds the alteration landscape to three-layer gene-level consequence and "
        "three-layer pathway-level enrichment evidence."
    )
    display["pathway_x_label"] = "Normalized enrichment score"
    display["pathway_y_label"] = "Pathway"
    display["pathway_effect_scale_label"] = "Enrichment direction"
    display["pathway_size_scale_label"] = "Hit count"
    display["pathway_order"] = [
        {"label": "PI3K-AKT signaling"},
        {"label": "Cell cycle"},
        {"label": "DNA damage response"},
        {"label": "Immune signaling"},
    ]
    display["pathway_panel_order"] = [
        {"panel_id": "proteome", "panel_title": "Proteome pathways"},
        {"panel_id": "phosphoproteome", "panel_title": "Phosphoproteome pathways"},
        {"panel_id": "glycoproteome", "panel_title": "Glycoproteome pathways"},
    ]
    display["pathway_points"] = [
        {"panel_id": "proteome", "pathway_label": "PI3K-AKT signaling", "x_value": 1.48, "effect_value": 1.48, "size_value": 36.0},
        {"panel_id": "proteome", "pathway_label": "Cell cycle", "x_value": 1.22, "effect_value": 1.22, "size_value": 30.0},
        {"panel_id": "proteome", "pathway_label": "DNA damage response", "x_value": -1.06, "effect_value": -1.06, "size_value": 24.0},
        {"panel_id": "proteome", "pathway_label": "Immune signaling", "x_value": 0.82, "effect_value": 0.82, "size_value": 20.0},
        {"panel_id": "phosphoproteome", "pathway_label": "PI3K-AKT signaling", "x_value": 1.61, "effect_value": 1.61, "size_value": 38.0},
        {"panel_id": "phosphoproteome", "pathway_label": "Cell cycle", "x_value": 1.34, "effect_value": 1.34, "size_value": 33.0},
        {"panel_id": "phosphoproteome", "pathway_label": "DNA damage response", "x_value": -0.94, "effect_value": -0.94, "size_value": 25.0},
        {"panel_id": "phosphoproteome", "pathway_label": "Immune signaling", "x_value": 0.71, "effect_value": 0.71, "size_value": 18.0},
        {"panel_id": "glycoproteome", "pathway_label": "PI3K-AKT signaling", "x_value": 1.18, "effect_value": 1.18, "size_value": 31.0},
        {"panel_id": "glycoproteome", "pathway_label": "Cell cycle", "x_value": 0.93, "effect_value": 0.93, "size_value": 27.0},
        {"panel_id": "glycoproteome", "pathway_label": "DNA damage response", "x_value": -0.76, "effect_value": -0.76, "size_value": 22.0},
        {"panel_id": "glycoproteome", "pathway_label": "Immune signaling", "x_value": 0.58, "effect_value": 0.58, "size_value": 16.0},
    ]
    return display

def _make_genomic_program_governance_summary_panel_display(
    display_id: str = "Figure51",
) -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": full_id("genomic_program_governance_summary_panel"),
        "title": "Genomic program governance summary for manuscript-facing driver-to-program synthesis",
        "caption": (
            "One bounded summary aligns alteration-linked multiomic support with row-level program priority, "
            "verdict, and manuscript action."
        ),
        "evidence_panel_title": "Cross-layer genomic evidence",
        "summary_panel_title": "Program governance summary",
        "effect_scale_label": "Direction and magnitude",
        "support_scale_label": "Support fraction",
        "layer_order": [
            {"layer_id": "alteration", "layer_label": "Alteration"},
            {"layer_id": "proteome", "layer_label": "Proteome"},
            {"layer_id": "phosphoproteome", "layer_label": "Phosphoproteome"},
            {"layer_id": "glycoproteome", "layer_label": "Glycoproteome"},
            {"layer_id": "pathway", "layer_label": "Pathway"},
        ],
        "programs": [
            {
                "program_id": "pi3k_growth",
                "program_label": "PI3K growth program",
                "lead_driver_label": "EGFR",
                "dominant_pathway_label": "PI3K-AKT signaling",
                "pathway_hit_count": 8,
                "priority_rank": 1,
                "priority_band": "high_priority",
                "verdict": "convergent",
                "action": "Promote to manuscript main-text synthesis",
                "detail": "Every declared layer supports the same activating direction.",
                "layer_supports": [
                    {"layer_id": "alteration", "effect_value": 0.88, "support_fraction": 0.82},
                    {"layer_id": "proteome", "effect_value": 1.21, "support_fraction": 0.74},
                    {"layer_id": "phosphoproteome", "effect_value": 1.48, "support_fraction": 0.86},
                    {"layer_id": "glycoproteome", "effect_value": 0.93, "support_fraction": 0.69},
                    {"layer_id": "pathway", "effect_value": 1.34, "support_fraction": 0.78},
                ],
            },
            {
                "program_id": "cell_cycle_stress",
                "program_label": "Cell-cycle stress program",
                "lead_driver_label": "TP53",
                "dominant_pathway_label": "Cell cycle",
                "pathway_hit_count": 6,
                "priority_rank": 2,
                "priority_band": "monitor",
                "verdict": "layer_specific",
                "action": "Keep as support-domain evidence",
                "detail": "Signal concentrates in proteome and pathway layers with weaker glycoproteome carry-through.",
                "layer_supports": [
                    {"layer_id": "alteration", "effect_value": 0.76, "support_fraction": 0.67},
                    {"layer_id": "proteome", "effect_value": 1.02, "support_fraction": 0.72},
                    {"layer_id": "phosphoproteome", "effect_value": 1.16, "support_fraction": 0.75},
                    {"layer_id": "glycoproteome", "effect_value": 0.41, "support_fraction": 0.44},
                    {"layer_id": "pathway", "effect_value": 1.08, "support_fraction": 0.71},
                ],
            },
            {
                "program_id": "immune_suppression",
                "program_label": "Immune suppression program",
                "lead_driver_label": "PIK3CA",
                "dominant_pathway_label": "Immune signaling",
                "pathway_hit_count": 4,
                "priority_rank": 3,
                "priority_band": "watchlist",
                "verdict": "context_dependent",
                "action": "Retain for supplementary context only",
                "detail": "Direction flips across layers and remains weaker than the top two programs.",
                "layer_supports": [
                    {"layer_id": "alteration", "effect_value": 0.22, "support_fraction": 0.36},
                    {"layer_id": "proteome", "effect_value": 0.58, "support_fraction": 0.49},
                    {"layer_id": "phosphoproteome", "effect_value": -0.34, "support_fraction": 0.41},
                    {"layer_id": "glycoproteome", "effect_value": -0.27, "support_fraction": 0.38},
                    {"layer_id": "pathway", "effect_value": 0.43, "support_fraction": 0.47},
                ],
            },
        ],
    }

def _make_stratified_cumulative_incidence_display(display_id: str = "Figure24") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "time_to_event_stratified_cumulative_incidence_panel",
        "title": "HTN-AI cumulative incidence of all-cause mortality across risk strata",
        "caption": (
            "Cumulative incidence curves stratified by baseline hypertension status, age band, and HTN-AI quintile."
        ),
        "x_label": "Years from index ECG",
        "y_label": "Cumulative incidence of all-cause mortality",
        "panels": [
            {
                "panel_id": "baseline_htn",
                "panel_label": "A",
                "title": "Baseline hypertension status",
                "annotation": "Gray test P < .001",
                "groups": [
                    {
                        "label": "HTN-AI+",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.04, 0.08, 0.13, 0.18],
                    },
                    {
                        "label": "HTN-AI−",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.02, 0.04, 0.06, 0.09],
                    },
                ],
            },
            {
                "panel_id": "age_band",
                "panel_label": "B",
                "title": "Age band",
                "annotation": "Gray test P < .001",
                "groups": [
                    {
                        "label": "Older",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.05, 0.10, 0.16, 0.22],
                    },
                    {
                        "label": "Younger",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.01, 0.03, 0.05, 0.07],
                    },
                ],
            },
            {
                "panel_id": "htn_ai_quintile",
                "panel_label": "C",
                "title": "HTN-AI quintile",
                "annotation": "Gray test P < .001",
                "groups": [
                    {
                        "label": "Q1",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.01, 0.02, 0.03, 0.05],
                    },
                    {
                        "label": "Q2",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.015, 0.03, 0.045, 0.06],
                    },
                    {
                        "label": "Q3",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.02, 0.04, 0.06, 0.09],
                    },
                    {
                        "label": "Q4",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.03, 0.06, 0.10, 0.14],
                    },
                    {
                        "label": "Q5",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.05, 0.10, 0.16, 0.23],
                    },
                ],
            },
        ],
    }

def _make_time_dependent_roc_comparison_panel_display(display_id: str = "Figure25") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "time_dependent_roc_comparison_panel",
        "title": "Time-dependent ROC analyses for dementia risk across follow-up windows",
        "caption": (
            "Panelized time-dependent ROC analyses comparing overall follow-up with the first 15 years of follow-up."
        ),
        "x_label": "False-positive rate",
        "y_label": "True-positive rate",
        "panels": [
            {
                "panel_id": "overall_followup",
                "panel_label": "A",
                "title": "Overall follow-up",
                "analysis_window_label": "Overall follow-up",
                "annotation": "AUC = 0.84",
                "series": [
                    {
                        "label": "Locked dementia-risk model",
                        "x": [0.0, 0.08, 0.18, 0.33, 1.0],
                        "y": [0.0, 0.56, 0.72, 0.86, 1.0],
                    },
                    {
                        "label": "Clinical baseline",
                        "x": [0.0, 0.10, 0.24, 0.40, 1.0],
                        "y": [0.0, 0.48, 0.65, 0.79, 1.0],
                    },
                ],
                "reference_line": {
                    "label": "Chance",
                    "x": [0.0, 1.0],
                    "y": [0.0, 1.0],
                },
            },
            {
                "panel_id": "first_15_years",
                "panel_label": "B",
                "title": "First 15 years of follow-up",
                "analysis_window_label": "First 15 years of follow-up",
                "time_horizon_months": 180,
                "annotation": "AUC = 0.88",
                "series": [
                    {
                        "label": "Locked dementia-risk model",
                        "x": [0.0, 0.05, 0.14, 0.30, 1.0],
                        "y": [0.0, 0.60, 0.79, 0.90, 1.0],
                    },
                    {
                        "label": "Clinical baseline",
                        "x": [0.0, 0.09, 0.22, 0.39, 1.0],
                        "y": [0.0, 0.50, 0.68, 0.80, 1.0],
                    },
                ],
                "reference_line": {
                    "label": "Chance",
                    "x": [0.0, 1.0],
                    "y": [0.0, 1.0],
                },
            },
        ],
    }

def _make_time_to_event_landmark_performance_panel_display(display_id: str = "Figure27") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "time_to_event_landmark_performance_panel",
        "title": "Landmark survival performance summary across recurrence prediction windows",
        "caption": (
            "Discrimination, prediction error, and calibration slope were locked across forward landmark windows "
            "for dynamic recurrence-risk evaluation."
        ),
        "discrimination_panel_title": "Discrimination",
        "discrimination_x_label": "Validation C-index",
        "error_panel_title": "Prediction error",
        "error_x_label": "Brier score",
        "calibration_panel_title": "Calibration",
        "calibration_x_label": "Calibration slope",
        "landmark_summaries": [
            {
                "window_label": "3→12 months",
                "analysis_window_label": "3-month landmark predicting 12-month recurrence",
                "landmark_months": 3,
                "prediction_months": 12,
                "c_index": 0.78,
                "brier_score": 0.18,
                "calibration_slope": 1.06,
                "annotation": "Baseline postoperative window",
            },
            {
                "window_label": "6→15 months",
                "analysis_window_label": "6-month landmark predicting 15-month recurrence",
                "landmark_months": 6,
                "prediction_months": 15,
                "c_index": 0.81,
                "brier_score": 0.15,
                "calibration_slope": 0.98,
            },
            {
                "window_label": "9→18 months",
                "analysis_window_label": "9-month landmark predicting 18-month recurrence",
                "landmark_months": 9,
                "prediction_months": 18,
                "c_index": 0.84,
                "brier_score": 0.12,
                "calibration_slope": 0.93,
            },
        ],
    }

def _make_shap_dependence_panel_display(display_id: str = "Figure28") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_dependence_panel",
        "title": "SHAP dependence panel for representative nonlinear feature effects",
        "caption": (
            "Feature-level SHAP dependence plots highlight nonlinear contribution structure and interaction patterns "
            "across the audited explanation surface."
        ),
        "y_label": "SHAP value",
        "colorbar_label": "Interaction feature value",
        "panels": [
            {
                "panel_id": "age_panel",
                "panel_label": "A",
                "title": "Age",
                "x_label": "Age (years)",
                "feature": "Age",
                "interaction_feature": "Albumin",
                "points": [
                    {"feature_value": 38.0, "shap_value": -0.22, "interaction_value": 3.1},
                    {"feature_value": 55.0, "shap_value": 0.04, "interaction_value": 4.2},
                    {"feature_value": 71.0, "shap_value": 0.31, "interaction_value": 4.8},
                ],
            },
            {
                "panel_id": "platelet_panel",
                "panel_label": "B",
                "title": "Platelet count",
                "x_label": "Platelets (10^9/L)",
                "feature": "Platelet count",
                "interaction_feature": "Age",
                "points": [
                    {"feature_value": 85.0, "shap_value": 0.28, "interaction_value": 72.0},
                    {"feature_value": 142.0, "shap_value": 0.02, "interaction_value": 59.0},
                    {"feature_value": 210.0, "shap_value": -0.19, "interaction_value": 44.0},
                ],
            },
        ],
    }

def _make_shap_waterfall_local_explanation_panel_display(display_id: str = "Figure33") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_waterfall_local_explanation_panel",
        "title": "SHAP waterfall local explanation panel for representative patient-level risk calls",
        "caption": (
            "Ordered case-level SHAP contributions show how the audited model output moves from baseline "
            "expectation to the final patient-level prediction."
        ),
        "x_label": "Predicted 1-year mortality probability",
        "panels": [
            {
                "panel_id": "case_a",
                "panel_label": "A",
                "title": "Representative high-risk case",
                "case_label": "Case 1 · 1-year mortality",
                "baseline_value": 0.18,
                "predicted_value": 0.39,
                "contributions": [
                    {"feature": "Age", "feature_value_text": "74 years", "shap_value": 0.12},
                    {"feature": "Albumin", "feature_value_text": "3.1 g/dL", "shap_value": 0.08},
                    {"feature": "Platelets", "feature_value_text": "210 ×10^9/L", "shap_value": -0.03},
                    {"feature": "Tumor size", "feature_value_text": "9.4 cm", "shap_value": 0.04},
                ],
            },
            {
                "panel_id": "case_b",
                "panel_label": "B",
                "title": "Representative lower-risk case",
                "case_label": "Case 2 · 1-year mortality",
                "baseline_value": 0.42,
                "predicted_value": 0.28,
                "contributions": [
                    {"feature": "Age", "feature_value_text": "49 years", "shap_value": -0.11},
                    {"feature": "Albumin", "feature_value_text": "4.5 g/dL", "shap_value": -0.07},
                    {"feature": "Tumor stage", "feature_value_text": "Stage II", "shap_value": 0.04},
                ],
            },
        ],
    }

def _make_shap_force_like_summary_panel_display(display_id: str = "Figure35") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_force_like_summary_panel",
        "title": "SHAP force-like summary panel for representative response phenotypes",
        "caption": (
            "Force-like local explanation lanes summarize which features push each representative case toward "
            "higher or lower predicted response probability."
        ),
        "x_label": "Predicted response probability",
        "panels": [
            {
                "panel_id": "case_a",
                "panel_label": "A",
                "title": "Representative responder",
                "case_label": "Case 1 · durable response",
                "baseline_value": 0.22,
                "predicted_value": 0.31,
                "contributions": [
                    {"feature": "Age", "feature_value_text": "74 years", "shap_value": 0.13},
                    {"feature": "Albumin", "feature_value_text": "3.1 g/dL", "shap_value": -0.04},
                ],
            },
            {
                "panel_id": "case_b",
                "panel_label": "B",
                "title": "Representative non-responder",
                "case_label": "Case 2 · early progression",
                "baseline_value": 0.57,
                "predicted_value": 0.48,
                "contributions": [
                    {"feature": "Tumor stage", "feature_value_text": "Stage III", "shap_value": -0.18},
                    {"feature": "Albumin", "feature_value_text": "4.6 g/dL", "shap_value": 0.09},
                ],
            },
        ],
    }

def _make_shap_grouped_local_explanation_panel_display(display_id: str = "Figure40") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_grouped_local_explanation_panel",
        "title": "SHAP grouped local explanation panel for representative phenotype comparison",
        "caption": (
            "Bounded grouped local explanation panels compare signed local feature contributions across "
            "representative phenotypes while preserving shared feature-order governance."
        ),
        "x_label": "Local SHAP contribution to predicted risk",
        "panels": [
            {
                "panel_id": "high_risk",
                "panel_label": "A",
                "title": "High-risk phenotype",
                "group_label": "Phenotype 1 · immune-inflamed",
                "baseline_value": 0.22,
                "predicted_value": 0.34,
                "contributions": [
                    {"rank": 1, "feature": "Age", "shap_value": 0.14},
                    {"rank": 2, "feature": "Albumin", "shap_value": -0.05},
                    {"rank": 3, "feature": "Tumor size", "shap_value": 0.03},
                ],
            },
            {
                "panel_id": "low_risk",
                "panel_label": "B",
                "title": "Lower-risk phenotype",
                "group_label": "Phenotype 2 · stromal-low",
                "baseline_value": 0.18,
                "predicted_value": 0.12,
                "contributions": [
                    {"rank": 1, "feature": "Age", "shap_value": -0.07},
                    {"rank": 2, "feature": "Albumin", "shap_value": 0.02},
                    {"rank": 3, "feature": "Tumor size", "shap_value": -0.01},
                ],
            },
        ],
    }

def _make_shap_grouped_decision_path_panel_display(display_id: str = "Figure42") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_grouped_decision_path_panel",
        "title": "SHAP grouped decision path panel for phenotype-level local explanation contrast",
        "caption": (
            "Bounded grouped decision paths summarize how a shared ordered feature set moves the audited "
            "model output from the common baseline toward phenotype-specific predictions."
        ),
        "panel_title": "Decision-path comparison across representative phenotypes",
        "x_label": "Cumulative model output",
        "y_label": "Ordered feature contributions",
        "legend_title": "Phenotype",
        "baseline_value": 0.19,
        "groups": [
            {
                "group_id": "immune_inflamed",
                "group_label": "Phenotype 1 · immune-inflamed",
                "predicted_value": 0.34,
                "contributions": [
                    {"rank": 1, "feature": "Age", "shap_value": 0.10},
                    {"rank": 2, "feature": "Albumin", "shap_value": -0.03},
                    {"rank": 3, "feature": "Tumor size", "shap_value": 0.08},
                ],
            },
            {
                "group_id": "stromal_low",
                "group_label": "Phenotype 2 · stromal-low",
                "predicted_value": 0.08,
                "contributions": [
                    {"rank": 1, "feature": "Age", "shap_value": -0.04},
                    {"rank": 2, "feature": "Albumin", "shap_value": -0.02},
                    {"rank": 3, "feature": "Tumor size", "shap_value": -0.05},
                ],
            },
        ],
    }

def _make_shap_multigroup_decision_path_panel_display(display_id: str = "Figure49") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_multigroup_decision_path_panel",
        "title": "SHAP multigroup decision path panel for phenotype-level local explanation contrast",
        "caption": (
            "Bounded multigroup decision paths summarize how a shared ordered feature set moves the audited "
            "model output from the common baseline toward phenotype-specific predictions."
        ),
        "panel_title": "Decision-path comparison across representative phenotypes",
        "x_label": "Cumulative model output",
        "y_label": "Ordered feature contributions",
        "legend_title": "Phenotype",
        "baseline_value": 0.19,
        "groups": [
            {
                "group_id": "immune_inflamed",
                "group_label": "Phenotype 1 · immune-inflamed",
                "predicted_value": 0.34,
                "contributions": [
                    {"rank": 1, "feature": "Age", "shap_value": 0.10},
                    {"rank": 2, "feature": "Albumin", "shap_value": -0.03},
                    {"rank": 3, "feature": "Tumor size", "shap_value": 0.08},
                ],
            },
            {
                "group_id": "stromal_low",
                "group_label": "Phenotype 2 · stromal-low",
                "predicted_value": 0.08,
                "contributions": [
                    {"rank": 1, "feature": "Age", "shap_value": -0.04},
                    {"rank": 2, "feature": "Albumin", "shap_value": -0.02},
                    {"rank": 3, "feature": "Tumor size", "shap_value": -0.05},
                ],
            },
            {
                "group_id": "immune_excluded",
                "group_label": "Phenotype 3 · immune-excluded",
                "predicted_value": 0.21,
                "contributions": [
                    {"rank": 1, "feature": "Age", "shap_value": 0.02},
                    {"rank": 2, "feature": "Albumin", "shap_value": -0.01},
                    {"rank": 3, "feature": "Tumor size", "shap_value": 0.01},
                ],
            },
        ],
    }

def _make_partial_dependence_ice_panel_display(display_id: str = "Figure36") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "partial_dependence_ice_panel",
        "title": "Partial dependence and ICE panel for representative feature-response trajectories",
        "caption": (
            "Bounded PDP and ICE overlays summarize how key features move the audited model prediction "
            "across representative feature ranges."
        ),
        "y_label": "Predicted response probability",
        "panels": [
            {
                "panel_id": "age_panel",
                "panel_label": "A",
                "title": "Age",
                "x_label": "Age (years)",
                "feature": "Age",
                "reference_value": 60.0,
                "reference_label": "Median age",
                "pdp_curve": {"x": [40.0, 50.0, 60.0, 70.0], "y": [0.16, 0.21, 0.27, 0.34]},
                "ice_curves": [
                    {"curve_id": "age_case_1", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.14, 0.19, 0.25, 0.33]},
                    {"curve_id": "age_case_2", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.17, 0.22, 0.29, 0.36]},
                    {"curve_id": "age_case_3", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.18, 0.23, 0.28, 0.35]},
                ],
            },
            {
                "panel_id": "albumin_panel",
                "panel_label": "B",
                "title": "Albumin",
                "x_label": "Albumin (g/dL)",
                "feature": "Albumin",
                "reference_value": 3.8,
                "reference_label": "Median albumin",
                "pdp_curve": {"x": [2.8, 3.4, 4.0, 4.6], "y": [0.39, 0.31, 0.25, 0.20]},
                "ice_curves": [
                    {"curve_id": "alb_case_1", "x": [2.8, 3.4, 4.0, 4.6], "y": [0.41, 0.33, 0.26, 0.21]},
                    {"curve_id": "alb_case_2", "x": [2.8, 3.4, 4.0, 4.6], "y": [0.37, 0.30, 0.24, 0.18]},
                    {"curve_id": "alb_case_3", "x": [2.8, 3.4, 4.0, 4.6], "y": [0.40, 0.32, 0.27, 0.22]},
                ],
            },
        ],
    }

def _make_partial_dependence_interaction_contour_panel_display(
    display_id: str = "Figure41",
) -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "partial_dependence_interaction_contour_panel",
        "title": "Partial dependence interaction contour panel for joint feature-response surfaces",
        "caption": (
            "Bounded pairwise partial dependence contours summarize how coupled feature regimes move the audited "
            "model prediction across clinically plausible combinations."
        ),
        "colorbar_label": "Predicted response probability",
        "panels": [
            {
                "panel_id": "age_albumin",
                "panel_label": "A",
                "title": "Age x Albumin",
                "x_label": "Age (years)",
                "y_label": "Albumin (g/dL)",
                "x_feature": "Age",
                "y_feature": "Albumin",
                "reference_x_value": 60.0,
                "reference_y_value": 3.8,
                "reference_label": "Median profile",
                "x_grid": [40.0, 50.0, 60.0, 70.0],
                "y_grid": [2.8, 3.4, 4.0, 4.6],
                "response_grid": [
                    [0.44, 0.37, 0.31, 0.27],
                    [0.35, 0.29, 0.24, 0.20],
                    [0.28, 0.23, 0.19, 0.16],
                    [0.24, 0.20, 0.17, 0.14],
                ],
                "observed_points": [
                    {"point_id": "case_1", "x": 43.0, "y": 3.0},
                    {"point_id": "case_2", "x": 51.0, "y": 3.5},
                    {"point_id": "case_3", "x": 60.0, "y": 3.8},
                    {"point_id": "case_4", "x": 67.0, "y": 4.2},
                ],
            },
            {
                "panel_id": "tumor_platelet",
                "panel_label": "B",
                "title": "Tumor size x Platelets",
                "x_label": "Tumor size (cm)",
                "y_label": "Platelets (10^9/L)",
                "x_feature": "Tumor size",
                "y_feature": "Platelet count",
                "reference_x_value": 6.0,
                "reference_y_value": 160.0,
                "reference_label": "Reference profile",
                "x_grid": [2.0, 4.0, 6.0, 8.0],
                "y_grid": [80.0, 120.0, 160.0, 200.0],
                "response_grid": [
                    [0.18, 0.21, 0.25, 0.29],
                    [0.22, 0.27, 0.31, 0.36],
                    [0.27, 0.33, 0.39, 0.45],
                    [0.31, 0.38, 0.45, 0.52],
                ],
                "observed_points": [
                    {"point_id": "case_5", "x": 2.6, "y": 92.0},
                    {"point_id": "case_6", "x": 4.8, "y": 138.0},
                    {"point_id": "case_7", "x": 6.1, "y": 164.0},
                    {"point_id": "case_8", "x": 7.5, "y": 188.0},
                ],
            },
        ],
    }
