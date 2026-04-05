from __future__ import annotations

import importlib

import pytest

from med_autoscience import display_registry


def test_registry_exposes_phase2_time_to_event_and_generalizability_surface() -> None:
    module = importlib.import_module("med_autoscience.display_registry")

    evidence_specs = module.list_evidence_figure_specs()
    illustration_specs = module.list_illustration_shell_specs()
    table_specs = module.list_table_shell_specs()

    assert {item.template_id for item in evidence_specs} >= {
        "roc_curve_binary",
        "pr_curve_binary",
        "calibration_curve_binary",
        "decision_curve_binary",
        "risk_layering_monotonic_bars",
        "binary_calibration_decision_curve_panel",
        "model_complexity_audit_panel",
        "time_dependent_roc_horizon",
        "kaplan_meier_grouped",
        "cumulative_incidence_grouped",
        "umap_scatter_grouped",
        "pca_scatter_grouped",
        "tsne_scatter_grouped",
        "heatmap_group_comparison",
        "correlation_heatmap",
        "clustered_heatmap",
        "forest_effect_main",
        "subgroup_forest",
        "shap_summary_beeswarm",
        "time_to_event_discrimination_calibration_panel",
        "time_to_event_risk_group_summary",
        "time_to_event_decision_curve",
        "multicenter_generalizability_overview",
    }
    assert {item.shell_id for item in illustration_specs} == {"cohort_flow_figure"}
    assert {item.shell_id for item in table_specs} >= {
        "table1_baseline_characteristics",
        "table2_time_to_event_performance_summary",
        "table3_clinical_interpretation_summary",
    }


def test_time_to_event_publication_surface_specs_are_registered() -> None:
    figure7 = display_registry.get_evidence_figure_spec("time_dependent_roc_horizon")
    figure9 = display_registry.get_evidence_figure_spec("tsne_scatter_grouped")
    figure10 = display_registry.get_evidence_figure_spec("clustered_heatmap")
    figure12 = display_registry.get_evidence_figure_spec("subgroup_forest")
    figure14 = display_registry.get_evidence_figure_spec("time_to_event_discrimination_calibration_panel")
    figure15 = display_registry.get_evidence_figure_spec("time_to_event_risk_group_summary")
    figure16 = display_registry.get_evidence_figure_spec("time_to_event_decision_curve")
    figure17 = display_registry.get_evidence_figure_spec("multicenter_generalizability_overview")
    figure22 = display_registry.get_evidence_figure_spec("risk_layering_monotonic_bars")
    figure3 = display_registry.get_evidence_figure_spec("binary_calibration_decision_curve_panel")
    figure4 = display_registry.get_evidence_figure_spec("model_complexity_audit_panel")
    table2 = display_registry.get_table_shell_spec("table2_time_to_event_performance_summary")
    table3 = display_registry.get_table_shell_spec("table3_clinical_interpretation_summary")

    assert figure7.input_schema_id == "binary_prediction_curve_inputs_v1"
    assert figure7.evidence_class == "time_to_event"
    assert figure9.layout_qc_profile == "publication_embedding_scatter"
    assert figure10.input_schema_id == "clustered_heatmap_inputs_v1"
    assert figure10.layout_qc_profile == "publication_heatmap"
    assert figure12.input_schema_id == "forest_effect_inputs_v1"
    assert figure12.layout_qc_profile == "publication_forest_plot"
    assert figure14.renderer_family == "python"
    assert figure14.required_exports == ("png", "pdf")
    assert figure14.input_schema_id == "time_to_event_discrimination_calibration_inputs_v1"
    assert figure15.input_schema_id == "time_to_event_grouped_inputs_v1"
    assert figure16.layout_qc_profile == "publication_decision_curve"
    assert figure17.allowed_paper_roles == ("main_text", "supplementary")
    assert figure17.evidence_class == "generalizability"
    assert figure22.renderer_family == "python"
    assert figure22.input_schema_id == "risk_layering_monotonic_inputs_v1"
    assert figure22.layout_qc_profile == "publication_risk_layering_bars"
    assert figure3.input_schema_id == "binary_calibration_decision_curve_panel_inputs_v1"
    assert figure3.layout_qc_profile == "publication_binary_calibration_decision_curve"
    assert figure3.renderer_family == "python"
    assert figure4.evidence_class == "model_audit"
    assert figure4.input_schema_id == "model_complexity_audit_panel_inputs_v1"
    assert figure4.layout_qc_profile == "publication_model_complexity_audit"
    assert table2.required_exports == ("md",)
    assert table3.input_schema_id == "clinical_interpretation_summary_v1"


def test_resolve_display_registry_rejects_unknown_template() -> None:
    module = importlib.import_module("med_autoscience.display_registry")

    with pytest.raises(ValueError, match="unknown evidence figure template"):
        module.get_evidence_figure_spec("unknown_template")
