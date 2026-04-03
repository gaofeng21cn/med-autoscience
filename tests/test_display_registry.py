from __future__ import annotations

import importlib

import pytest


def test_phase1_registry_exposes_official_templates_and_shells() -> None:
    module = importlib.import_module("med_autoscience.display_registry")

    evidence_specs = module.list_evidence_figure_specs()
    illustration_specs = module.list_illustration_shell_specs()
    table_specs = module.list_table_shell_specs()

    assert {item.template_id for item in evidence_specs} >= {
        "roc_curve_binary",
        "pr_curve_binary",
        "calibration_curve_binary",
        "decision_curve_binary",
        "kaplan_meier_grouped",
        "cumulative_incidence_grouped",
        "umap_scatter_grouped",
        "pca_scatter_grouped",
        "heatmap_group_comparison",
        "correlation_heatmap",
        "forest_effect_main",
        "shap_summary_beeswarm",
    }
    assert {item.shell_id for item in illustration_specs} == {"cohort_flow_figure"}
    assert {item.shell_id for item in table_specs} == {"table1_baseline_characteristics"}


def test_resolve_display_registry_rejects_unknown_template() -> None:
    module = importlib.import_module("med_autoscience.display_registry")

    with pytest.raises(ValueError, match="unknown evidence figure template"):
        module.get_evidence_figure_spec("unknown_template")
