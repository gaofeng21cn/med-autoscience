from __future__ import annotations

from . import shared_base as _shared_base
from . import genomic_payload_fixtures as _genomic_payload_fixtures

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared_base)
_module_reexport(_genomic_payload_fixtures)

def _make_partial_dependence_interaction_slice_panel_display(
    display_id: str = "Figure43",
) -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "partial_dependence_interaction_slice_panel",
        "title": "Partial dependence interaction slice panel for clinically bounded conditioning profiles",
        "caption": (
            "Bounded interaction slices summarize how clinically meaningful conditioning profiles reshape the "
            "partial-dependence trajectory for the audited model."
        ),
        "y_label": "Predicted response probability",
        "legend_title": "Conditioning profile",
        "panels": [
            {
                "panel_id": "age_by_albumin",
                "panel_label": "A",
                "title": "Age conditioned on albumin",
                "x_label": "Age (years)",
                "x_feature": "Age",
                "slice_feature": "Albumin",
                "reference_value": 60.0,
                "reference_label": "Median age",
                "slice_curves": [
                    {
                        "slice_id": "albumin_low",
                        "slice_label": "Low conditioning",
                        "conditioning_value": 3.2,
                        "x": [40.0, 50.0, 60.0, 70.0],
                        "y": [0.24, 0.28, 0.33, 0.39],
                    },
                    {
                        "slice_id": "albumin_high",
                        "slice_label": "High conditioning",
                        "conditioning_value": 4.4,
                        "x": [40.0, 50.0, 60.0, 70.0],
                        "y": [0.15, 0.19, 0.24, 0.30],
                    },
                ],
            },
            {
                "panel_id": "tumor_by_platelet",
                "panel_label": "B",
                "title": "Tumor size conditioned on platelets",
                "x_label": "Tumor size (cm)",
                "x_feature": "Tumor size",
                "slice_feature": "Platelet count",
                "reference_value": 6.0,
                "reference_label": "Reference tumor size",
                "slice_curves": [
                    {
                        "slice_id": "platelet_low",
                        "slice_label": "Low conditioning",
                        "conditioning_value": 110.0,
                        "x": [2.0, 4.0, 6.0, 8.0],
                        "y": [0.20, 0.27, 0.36, 0.47],
                    },
                    {
                        "slice_id": "platelet_high",
                        "slice_label": "High conditioning",
                        "conditioning_value": 210.0,
                        "x": [2.0, 4.0, 6.0, 8.0],
                        "y": [0.13, 0.19, 0.27, 0.35],
                    },
                ],
            },
        ],
    }

def _make_partial_dependence_subgroup_comparison_panel_display(
    display_id: str = "Figure44",
) -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "partial_dependence_subgroup_comparison_panel",
        "title": "Partial dependence subgroup comparison panel for audited sensitivity heterogeneity",
        "caption": (
            "Bounded subgroup comparison panels couple subgroup-specific PDP/ICE trajectories with a compact "
            "interval summary so the manuscript-facing explanation remains auditable."
        ),
        "y_label": "Predicted response probability",
        "subgroup_panel_label": "C",
        "subgroup_panel_title": "Subgroup-level absolute risk contrast",
        "subgroup_x_label": "Mean predicted risk difference",
        "panels": [
            {
                "panel_id": "immune_high",
                "panel_label": "A",
                "subgroup_label": "Immune-high",
                "title": "Immune-high subgroup",
                "x_label": "Age (years)",
                "feature": "Age",
                "reference_value": 60.0,
                "reference_label": "Median age",
                "pdp_curve": {"x": [40.0, 50.0, 60.0, 70.0], "y": [0.18, 0.24, 0.31, 0.39]},
                "ice_curves": [
                    {"curve_id": "immune_high_case_1", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.16, 0.22, 0.30, 0.40]},
                    {"curve_id": "immune_high_case_2", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.19, 0.25, 0.33, 0.41]},
                ],
            },
            {
                "panel_id": "immune_low",
                "panel_label": "B",
                "subgroup_label": "Immune-low",
                "title": "Immune-low subgroup",
                "x_label": "Age (years)",
                "feature": "Age",
                "reference_value": 60.0,
                "reference_label": "Median age",
                "pdp_curve": {"x": [40.0, 50.0, 60.0, 70.0], "y": [0.13, 0.17, 0.22, 0.28]},
                "ice_curves": [
                    {"curve_id": "immune_low_case_1", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.12, 0.16, 0.21, 0.27]},
                    {"curve_id": "immune_low_case_2", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.14, 0.18, 0.23, 0.29]},
                ],
            },
        ],
        "subgroup_rows": [
            {
                "row_id": "immune_high_row",
                "panel_id": "immune_high",
                "row_label": "Immune-high",
                "estimate": 0.31,
                "lower": 0.24,
                "upper": 0.38,
                "support_n": 142,
            },
            {
                "row_id": "immune_low_row",
                "panel_id": "immune_low",
                "row_label": "Immune-low",
                "estimate": 0.22,
                "lower": 0.16,
                "upper": 0.28,
                "support_n": 151,
            },
        ],
    }

def _make_accumulated_local_effects_panel_display(
    display_id: str = "Figure45",
) -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "accumulated_local_effects_panel",
        "title": "Accumulated local effects panel for bounded feature-response accumulation",
        "caption": (
            "Bounded ALE panels summarize local-effect bins and the corresponding accumulated effect curves "
            "without opening an unconstrained explanation scene."
        ),
        "y_label": "Accumulated local effect",
        "panels": [
            {
                "panel_id": "age_ale",
                "panel_label": "A",
                "title": "Age",
                "x_label": "Age (years)",
                "feature": "Age",
                "reference_value": 60.0,
                "reference_label": "Median age",
                "ale_curve": {"x": [45.0, 55.0, 65.0, 75.0], "y": [0.02, 0.07, 0.11, 0.16]},
                "local_effect_bins": [
                    {"bin_id": "age_bin_1", "bin_left": 40.0, "bin_right": 50.0, "bin_center": 45.0, "local_effect": 0.02, "support_count": 84},
                    {"bin_id": "age_bin_2", "bin_left": 50.0, "bin_right": 60.0, "bin_center": 55.0, "local_effect": 0.05, "support_count": 91},
                    {"bin_id": "age_bin_3", "bin_left": 60.0, "bin_right": 70.0, "bin_center": 65.0, "local_effect": 0.04, "support_count": 88},
                    {"bin_id": "age_bin_4", "bin_left": 70.0, "bin_right": 80.0, "bin_center": 75.0, "local_effect": 0.05, "support_count": 73},
                ],
            },
            {
                "panel_id": "albumin_ale",
                "panel_label": "B",
                "title": "Albumin",
                "x_label": "Albumin (g/dL)",
                "feature": "Albumin",
                "reference_value": 3.8,
                "reference_label": "Median albumin",
                "ale_curve": {"x": [3.0, 3.4, 3.8, 4.2], "y": [-0.03, -0.07, -0.10, -0.12]},
                "local_effect_bins": [
                    {"bin_id": "alb_bin_1", "bin_left": 2.8, "bin_right": 3.2, "bin_center": 3.0, "local_effect": -0.03, "support_count": 81},
                    {"bin_id": "alb_bin_2", "bin_left": 3.2, "bin_right": 3.6, "bin_center": 3.4, "local_effect": -0.04, "support_count": 87},
                    {"bin_id": "alb_bin_3", "bin_left": 3.6, "bin_right": 4.0, "bin_center": 3.8, "local_effect": -0.03, "support_count": 96},
                    {"bin_id": "alb_bin_4", "bin_left": 4.0, "bin_right": 4.4, "bin_center": 4.2, "local_effect": -0.02, "support_count": 78},
                ],
            },
        ],
    }

def _make_feature_response_support_domain_panel_display(
    display_id: str = "Figure47",
) -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "feature_response_support_domain_panel",
        "title": "Feature response support domain panel for audited support-aware explanation bounds",
        "caption": (
            "Bounded support-domain panels make explicit which response-curve intervals are backed by observed, "
            "subgroup, or bin support and which intervals must stay annotated as extrapolation reminders."
        ),
        "y_label": "Predicted response probability",
        "panels": [
            {
                "panel_id": "age_support",
                "panel_label": "A",
                "title": "Age support domain",
                "x_label": "Age (years)",
                "feature": "Age",
                "reference_value": 60.0,
                "reference_label": "Median age",
                "response_curve": {"x": [40.0, 50.0, 60.0, 70.0, 80.0], "y": [0.18, 0.22, 0.29, 0.35, 0.41]},
                "support_segments": [
                    {"segment_id": "age_observed", "segment_label": "Observed", "support_kind": "observed_support", "domain_start": 40.0, "domain_end": 50.0},
                    {"segment_id": "age_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "domain_start": 50.0, "domain_end": 62.0},
                    {"segment_id": "age_bin", "segment_label": "Bin", "support_kind": "bin_support", "domain_start": 62.0, "domain_end": 72.0},
                    {"segment_id": "age_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "domain_start": 72.0, "domain_end": 80.0},
                ],
            },
            {
                "panel_id": "albumin_support",
                "panel_label": "B",
                "title": "Albumin support domain",
                "x_label": "Albumin (g/dL)",
                "feature": "Albumin",
                "reference_value": 3.8,
                "reference_label": "Median albumin",
                "response_curve": {
                    "x": [2.8, 3.2, 3.6, 4.0, 4.4, 4.6],
                    "y": [0.39, 0.33, 0.28, 0.23, 0.19, 0.17],
                },
                "support_segments": [
                    {"segment_id": "alb_observed", "segment_label": "Observed", "support_kind": "observed_support", "domain_start": 2.8, "domain_end": 3.2},
                    {"segment_id": "alb_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "domain_start": 3.2, "domain_end": 3.8},
                    {"segment_id": "alb_bin", "segment_label": "Bin", "support_kind": "bin_support", "domain_start": 3.8, "domain_end": 4.2},
                    {"segment_id": "alb_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "domain_start": 4.2, "domain_end": 4.6},
                ],
            },
        ],
    }

def _make_shap_multigroup_decision_path_support_domain_panel_display(
    display_id: str = "Figure51",
) -> dict[str, object]:
    decision_panel = _make_shap_multigroup_decision_path_panel_display(display_id)
    support_panel = _make_feature_response_support_domain_panel_display(display_id)
    return {
        "display_id": display_id,
        "template_id": "shap_multigroup_decision_path_support_domain_panel",
        "title": "Multigroup decision path with support-domain follow-on for manuscript-facing explanation scenes",
        "caption": (
            "A single multigroup decision-path panel summarizes how phenotype-level SHAP trajectories diverge, "
            "and matched support-domain panels expose which feature-response regions remain backed by observed support."
        ),
        "decision_panel_title": decision_panel["panel_title"],
        "decision_x_label": decision_panel["x_label"],
        "decision_y_label": decision_panel["y_label"],
        "decision_legend_title": decision_panel["legend_title"],
        "support_y_label": support_panel["y_label"],
        "support_legend_title": "Support domain",
        "baseline_value": decision_panel["baseline_value"],
        "groups": decision_panel["groups"],
        "support_panels": support_panel["panels"],
    }

def _make_shap_signed_importance_local_support_domain_panel_display(
    display_id: str = "Figure52",
) -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_signed_importance_local_support_domain_panel",
        "title": "Global signed importance with local waterfall and support-domain follow-on for manuscript-facing explanation scenes",
        "caption": (
            "A signed-importance anchor defines the global polarity of the explanation scene, "
            "a representative local waterfall preserves the patient-level additive path, "
            "and matched support-domain panels keep the same narrative bounded by observed evidence."
        ),
        "support_y_label": "Predicted response probability",
        "support_legend_title": "Support domain",
        "importance_panel": {
            "panel_id": "global_signed_importance",
            "panel_label": "A",
            "title": "Directional global importance",
            "x_label": "Mean signed SHAP value",
            "negative_label": "Protective direction",
            "positive_label": "Risk direction",
            "bars": [
                {"rank": 1, "feature": "Albumin", "signed_importance_value": -0.118},
                {"rank": 2, "feature": "Age", "signed_importance_value": 0.104},
                {"rank": 3, "feature": "Tumor size", "signed_importance_value": 0.081},
                {"rank": 4, "feature": "Platelet count", "signed_importance_value": -0.064},
            ],
        },
        "local_panel": {
            "panel_id": "representative_case",
            "panel_label": "B",
            "title": "Representative high-risk case",
            "case_label": "Case 1 · 1-year mortality",
            "x_label": "Predicted 1-year mortality probability",
            "baseline_value": 0.18,
            "predicted_value": 0.39,
            "contributions": [
                {"feature": "Albumin", "feature_value_text": "3.1 g/dL", "shap_value": 0.08},
                {"feature": "Age", "feature_value_text": "74 years", "shap_value": 0.12},
                {"feature": "Tumor size", "feature_value_text": "9.4 cm", "shap_value": 0.04},
                {"feature": "Platelet count", "feature_value_text": "210 ×10^9/L", "shap_value": -0.03},
            ],
        },
        "support_panels": [
            {
                "panel_id": "albumin_support",
                "panel_label": "C",
                "title": "Albumin response support",
                "x_label": "Albumin (g/dL)",
                "feature": "Albumin",
                "reference_value": 3.8,
                "reference_label": "Median albumin",
                "response_curve": {
                    "x": [2.8, 3.2, 3.6, 4.0, 4.4, 4.6],
                    "y": [0.39, 0.33, 0.28, 0.23, 0.19, 0.17],
                },
                "support_segments": [
                    {"segment_id": "alb_observed", "segment_label": "Observed", "support_kind": "observed_support", "domain_start": 2.8, "domain_end": 3.2},
                    {"segment_id": "alb_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "domain_start": 3.2, "domain_end": 3.8},
                    {"segment_id": "alb_bin", "segment_label": "Bin", "support_kind": "bin_support", "domain_start": 3.8, "domain_end": 4.2},
                    {"segment_id": "alb_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "domain_start": 4.2, "domain_end": 4.6},
                ],
            },
            {
                "panel_id": "age_support",
                "panel_label": "D",
                "title": "Age response support",
                "x_label": "Age (years)",
                "feature": "Age",
                "reference_value": 60.0,
                "reference_label": "Median age",
                "response_curve": {"x": [40.0, 50.0, 60.0, 70.0, 80.0], "y": [0.18, 0.22, 0.29, 0.35, 0.41]},
                "support_segments": [
                    {"segment_id": "age_observed", "segment_label": "Observed", "support_kind": "observed_support", "domain_start": 40.0, "domain_end": 50.0},
                    {"segment_id": "age_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "domain_start": 50.0, "domain_end": 62.0},
                    {"segment_id": "age_bin", "segment_label": "Bin", "support_kind": "bin_support", "domain_start": 62.0, "domain_end": 72.0},
                    {"segment_id": "age_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "domain_start": 72.0, "domain_end": 80.0},
                ],
            },
        ],
    }

def _make_shap_bar_importance_display(display_id: str = "Figure37") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_bar_importance",
        "title": "SHAP bar importance panel for audited global feature ranking",
        "caption": (
            "Bounded SHAP importance bars summarize the top global drivers of the audited model prediction "
            "surface using a stable ranked-importance contract."
        ),
        "x_label": "Mean absolute SHAP value",
        "bars": [
            {"rank": 1, "feature": "Age", "importance_value": 0.184},
            {"rank": 2, "feature": "Albumin", "importance_value": 0.133},
            {"rank": 3, "feature": "Tumor size", "importance_value": 0.096},
            {"rank": 4, "feature": "Platelet count", "importance_value": 0.071},
        ],
    }

def _make_shap_signed_importance_panel_display(display_id: str = "Figure38") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_signed_importance_panel",
        "title": "SHAP signed importance panel for audited directional feature influence",
        "caption": (
            "Bounded signed-importance bars summarize the net directional contribution of the top global drivers "
            "while keeping zero-centered geometry and polarity semantics manuscript-facing and auditable."
        ),
        "x_label": "Mean signed SHAP value",
        "negative_label": "Protective direction",
        "positive_label": "Risk direction",
        "bars": [
            {"rank": 1, "feature": "Albumin", "signed_importance_value": -0.118},
            {"rank": 2, "feature": "Age", "signed_importance_value": 0.104},
            {"rank": 3, "feature": "Tumor size", "signed_importance_value": 0.081},
            {"rank": 4, "feature": "Platelet count", "signed_importance_value": -0.064},
        ],
    }

def _make_shap_multicohort_importance_panel_display(display_id: str = "Figure39") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_multicohort_importance_panel",
        "title": "SHAP multicohort importance panel for audited cross-cohort feature ranking",
        "caption": (
            "Bounded multi-panel SHAP importance views compare stable ranked feature drivers across audited cohorts "
            "without giving up deterministic panel contracts or manuscript-facing readability."
        ),
        "x_label": "Mean absolute SHAP value",
        "panels": [
            {
                "panel_id": "derivation",
                "panel_label": "A",
                "title": "Derivation cohort",
                "cohort_label": "Derivation",
                "bars": [
                    {"rank": 1, "feature": "Age", "importance_value": 0.184},
                    {"rank": 2, "feature": "Albumin", "importance_value": 0.133},
                    {"rank": 3, "feature": "Tumor size", "importance_value": 0.096},
                    {"rank": 4, "feature": "Platelet count", "importance_value": 0.071},
                ],
            },
            {
                "panel_id": "validation",
                "panel_label": "B",
                "title": "External validation cohort",
                "cohort_label": "Validation",
                "bars": [
                    {"rank": 1, "feature": "Age", "importance_value": 0.171},
                    {"rank": 2, "feature": "Albumin", "importance_value": 0.121},
                    {"rank": 3, "feature": "Tumor size", "importance_value": 0.089},
                    {"rank": 4, "feature": "Platelet count", "importance_value": 0.067},
                ],
            },
        ],
    }

def _make_generalizability_subgroup_composite_panel_display(display_id: str = "Figure34") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "generalizability_subgroup_composite_panel",
        "title": "Generalizability and subgroup discrimination composite for external validation",
        "caption": (
            "Bounded composite lock for overall external generalizability and prespecified subgroup discrimination "
            "stability."
        ),
        "metric_family": "discrimination",
        "primary_label": "Locked model",
        "comparator_label": "Derivation cohort",
        "overview_panel_title": "External cohort discrimination overview",
        "overview_x_label": "AUROC",
        "overview_rows": [
            {
                "cohort_id": "external_a",
                "cohort_label": "External A",
                "support_count": 184,
                "event_count": 29,
                "metric_value": 0.82,
                "comparator_metric_value": 0.79,
            },
            {
                "cohort_id": "external_b",
                "cohort_label": "External B",
                "support_count": 163,
                "event_count": 21,
                "metric_value": 0.78,
                "comparator_metric_value": 0.79,
            },
            {
                "cohort_id": "temporal",
                "cohort_label": "Temporal",
                "support_count": 142,
                "event_count": 18,
                "metric_value": 0.80,
                "comparator_metric_value": 0.79,
            },
        ],
        "subgroup_panel_title": "Prespecified subgroup discrimination stability",
        "subgroup_x_label": "AUROC",
        "subgroup_reference_value": 0.80,
        "subgroup_rows": [
            {
                "subgroup_id": "age_ge_65",
                "subgroup_label": "Age ≥65 years",
                "group_n": 201,
                "estimate": 0.82,
                "lower": 0.78,
                "upper": 0.86,
            },
            {
                "subgroup_id": "female",
                "subgroup_label": "Female",
                "group_n": 173,
                "estimate": 0.79,
                "lower": 0.75,
                "upper": 0.83,
            },
            {
                "subgroup_id": "high_risk",
                "subgroup_label": "High-risk surgery",
                "group_n": 96,
                "estimate": 0.84,
                "lower": 0.79,
                "upper": 0.89,
            },
        ],
    }

def _make_compact_effect_estimate_panel_display(display_id: str = "Figure46") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "compact_effect_estimate_panel",
        "title": "Compact effect estimate panel for pre-specified heterogeneity review",
        "caption": (
            "Bounded multi-panel effect estimates preserve a shared row order and shared null reference while "
            "keeping the C/H follow-on contract manuscript-facing and auditable."
        ),
        "x_label": "Hazard ratio",
        "reference_value": 1.0,
        "panels": [
            {
                "panel_id": "overall",
                "panel_label": "A",
                "title": "Overall cohort",
                "rows": [
                    {
                        "row_id": "age_ge_65",
                        "row_label": "Age ≥65 years",
                        "support_n": 184,
                        "estimate": 1.18,
                        "lower": 1.04,
                        "upper": 1.34,
                    },
                    {
                        "row_id": "female",
                        "row_label": "Female",
                        "support_n": 201,
                        "estimate": 1.26,
                        "lower": 1.10,
                        "upper": 1.44,
                    },
                    {
                        "row_id": "high_risk",
                        "row_label": "High risk",
                        "support_n": 96,
                        "estimate": 1.42,
                        "lower": 1.17,
                        "upper": 1.72,
                    },
                ],
            },
            {
                "panel_id": "adjusted",
                "panel_label": "B",
                "title": "Covariate-adjusted model",
                "rows": [
                    {
                        "row_id": "age_ge_65",
                        "row_label": "Age ≥65 years",
                        "support_n": 184,
                        "estimate": 1.11,
                        "lower": 0.98,
                        "upper": 1.28,
                    },
                    {
                        "row_id": "female",
                        "row_label": "Female",
                        "support_n": 201,
                        "estimate": 1.22,
                        "lower": 1.05,
                        "upper": 1.40,
                    },
                    {
                        "row_id": "high_risk",
                        "row_label": "High risk",
                        "support_n": 96,
                        "estimate": 1.35,
                        "lower": 1.11,
                        "upper": 1.64,
                    },
                ],
            },
            {
                "panel_id": "sensitivity",
                "panel_label": "C",
                "title": "Sensitivity analysis",
                "rows": [
                    {
                        "row_id": "age_ge_65",
                        "row_label": "Age ≥65 years",
                        "support_n": 184,
                        "estimate": 1.09,
                        "lower": 0.95,
                        "upper": 1.25,
                    },
                    {
                        "row_id": "female",
                        "row_label": "Female",
                        "support_n": 201,
                        "estimate": 1.18,
                        "lower": 1.01,
                        "upper": 1.37,
                    },
                    {
                        "row_id": "high_risk",
                        "row_label": "High risk",
                        "support_n": 96,
                        "estimate": 1.29,
                        "lower": 1.05,
                        "upper": 1.58,
                    },
                ],
            },
        ],
    }

def _make_coefficient_path_panel_display(display_id: str = "Figure48") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "coefficient_path_panel",
        "title": "Coefficient path panel for prespecified heterogeneity stability review",
        "caption": (
            "Bounded coefficient-path evidence locks directional stability across prespecified adjustment steps "
            "while keeping the manuscript-facing heterogeneity summary auditable."
        ),
        "path_panel_title": "Coefficient path across model steps",
        "x_label": "Log hazard ratio",
        "reference_value": 0.0,
        "step_legend_title": "Model step",
        "steps": [
            {"step_id": "unadjusted", "step_label": "Unadjusted", "step_order": 1},
            {"step_id": "adjusted", "step_label": "Adjusted", "step_order": 2},
            {"step_id": "sensitivity", "step_label": "Sensitivity", "step_order": 3},
        ],
        "coefficient_rows": [
            {
                "row_id": "age_ge_65",
                "row_label": "Age ≥65 years",
                "points": [
                    {"step_id": "unadjusted", "estimate": 0.18, "lower": 0.04, "upper": 0.32, "support_n": 184},
                    {"step_id": "adjusted", "estimate": 0.11, "lower": -0.01, "upper": 0.24, "support_n": 184},
                    {"step_id": "sensitivity", "estimate": 0.08, "lower": -0.05, "upper": 0.20, "support_n": 184},
                ],
            },
            {
                "row_id": "female",
                "row_label": "Female",
                "points": [
                    {"step_id": "unadjusted", "estimate": 0.34, "lower": 0.19, "upper": 0.49, "support_n": 201},
                    {"step_id": "adjusted", "estimate": 0.27, "lower": 0.12, "upper": 0.41, "support_n": 201},
                    {"step_id": "sensitivity", "estimate": 0.22, "lower": 0.08, "upper": 0.36, "support_n": 201},
                ],
            },
            {
                "row_id": "high_risk",
                "row_label": "High-risk subgroup",
                "points": [
                    {"step_id": "unadjusted", "estimate": 0.41, "lower": 0.24, "upper": 0.58, "support_n": 96},
                    {"step_id": "adjusted", "estimate": 0.33, "lower": 0.16, "upper": 0.49, "support_n": 96},
                    {"step_id": "sensitivity", "estimate": 0.29, "lower": 0.11, "upper": 0.46, "support_n": 96},
                ],
            },
        ],
        "summary_panel_title": "Stability summary",
        "summary_cards": [
            {
                "card_id": "age",
                "label": "Age ≥65 years",
                "value": "Stable positive",
                "detail": "Direction stays positive across all 3 model steps.",
            },
            {
                "card_id": "female",
                "label": "Female",
                "value": "Attenuated after adjustment",
                "detail": "Magnitude shrinks after covariate adjustment but remains positive.",
            },
            {
                "card_id": "high_risk",
                "label": "High-risk subgroup",
                "value": "Largest retained signal",
                "detail": "The widest positive effect survives all prespecified sensitivity steps.",
            },
        ],
    }

def _make_broader_heterogeneity_summary_panel_display(display_id: str = "Figure49") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "broader_heterogeneity_summary_panel",
        "title": "Broader heterogeneity summary panel for manuscript-facing comparative review",
        "caption": (
            "Bounded heterogeneity evidence aligns prespecified cohort, subgroup, and adjustment slices with a "
            "row-level manuscript verdict so the comparative summary stays auditable and reusable."
        ),
        "matrix_panel_title": "Prespecified heterogeneity slices",
        "x_label": "Hazard ratio",
        "reference_value": 1.0,
        "slice_legend_title": "Evidence slice",
        "slices": [
            {
                "slice_id": "overall",
                "slice_label": "Overall cohort",
                "slice_kind": "cohort",
                "slice_order": 1,
            },
            {
                "slice_id": "subgroup",
                "slice_label": "Prespecified subgroup",
                "slice_kind": "subgroup",
                "slice_order": 2,
            },
            {
                "slice_id": "adjusted",
                "slice_label": "Adjusted model",
                "slice_kind": "adjustment",
                "slice_order": 3,
            },
        ],
        "effect_rows": [
            {
                "row_id": "age_ge_65",
                "row_label": "Age ≥65 years",
                "verdict": "stable",
                "detail": "Positive direction stays preserved across every declared slice.",
                "slice_estimates": [
                    {"slice_id": "overall", "estimate": 1.18, "lower": 1.04, "upper": 1.34, "support_n": 184},
                    {"slice_id": "subgroup", "estimate": 1.16, "lower": 1.01, "upper": 1.33, "support_n": 121},
                    {"slice_id": "adjusted", "estimate": 1.11, "lower": 0.98, "upper": 1.28, "support_n": 184},
                ],
            },
            {
                "row_id": "female",
                "row_label": "Female",
                "verdict": "attenuated",
                "detail": "Magnitude shrinks after adjustment while retaining a positive point estimate.",
                "slice_estimates": [
                    {"slice_id": "overall", "estimate": 1.26, "lower": 1.10, "upper": 1.44, "support_n": 201},
                    {"slice_id": "subgroup", "estimate": 1.22, "lower": 1.05, "upper": 1.41, "support_n": 173},
                    {"slice_id": "adjusted", "estimate": 1.08, "lower": 0.94, "upper": 1.24, "support_n": 201},
                ],
            },
            {
                "row_id": "high_risk",
                "row_label": "High-risk subgroup",
                "verdict": "context_dependent",
                "detail": "The strongest signal concentrates in the high-risk slice and softens outside it.",
                "slice_estimates": [
                    {"slice_id": "overall", "estimate": 1.19, "lower": 1.01, "upper": 1.39, "support_n": 96},
                    {"slice_id": "subgroup", "estimate": 1.42, "lower": 1.17, "upper": 1.72, "support_n": 96},
                    {"slice_id": "adjusted", "estimate": 1.05, "lower": 0.89, "upper": 1.24, "support_n": 96},
                ],
            },
        ],
        "summary_panel_title": "Manuscript verdict summary",
    }

def _make_interaction_effect_summary_panel_display(display_id: str = "Figure51") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "interaction_effect_summary_panel",
        "title": "Interaction effect summary panel for modifier-focused heterogeneity review",
        "caption": (
            "Bounded interaction-effect evidence formalizes modifier-level contrast estimates together with "
            "manuscript-facing verdicts, favored subgroup labels, and interaction P values."
        ),
        "estimate_panel_title": "Prespecified interaction effects",
        "x_label": "Interaction beta (log hazard ratio difference)",
        "reference_value": 0.0,
        "summary_panel_title": "Interaction verdict summary",
        "modifiers": [
            {
                "modifier_id": "age_ge_65",
                "modifier_label": "Age ≥65 years",
                "interaction_estimate": 0.18,
                "lower": 0.05,
                "upper": 0.31,
                "support_n": 184,
                "favored_group_label": "Stronger in age ≥65 years",
                "interaction_p_value": 0.014,
                "verdict": "credible",
            },
            {
                "modifier_id": "female",
                "modifier_label": "Female",
                "interaction_estimate": 0.09,
                "lower": -0.02,
                "upper": 0.20,
                "support_n": 201,
                "favored_group_label": "More pronounced in female patients",
                "interaction_p_value": 0.081,
                "verdict": "suggestive",
            },
            {
                "modifier_id": "high_risk",
                "modifier_label": "High-risk subgroup",
                "interaction_estimate": 0.27,
                "lower": 0.10,
                "upper": 0.44,
                "support_n": 96,
                "favored_group_label": "Largest signal in high-risk subgroup",
                "interaction_p_value": 0.006,
                "verdict": "credible",
            },
        ],
    }
