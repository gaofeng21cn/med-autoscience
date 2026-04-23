from __future__ import annotations


def _build_workspace_registry_displays(
    *,
    include_evidence: bool,
    include_extended_evidence: bool,
) -> list[dict[str, str]]:
    displays = [
        {
            "display_id": "Figure1",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "shell_path": "paper/figures/Figure1.shell.json",
        },
        {
            "display_id": "Table1",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "shell_path": "paper/tables/Table1.shell.json",
        },
    ]
    if include_evidence:
        displays.extend(
            [
                {
                    "display_id": "Figure2",
                    "display_kind": "figure",
                    "requirement_key": "roc_curve_binary",
                    "shell_path": "paper/figures/Figure2.shell.json",
                },
                {
                    "display_id": "Figure3",
                    "display_kind": "figure",
                    "requirement_key": "pr_curve_binary",
                    "shell_path": "paper/figures/Figure3.shell.json",
                },
                {
                    "display_id": "Figure4",
                    "display_kind": "figure",
                    "requirement_key": "calibration_curve_binary",
                    "shell_path": "paper/figures/Figure4.shell.json",
                },
                {
                    "display_id": "Figure5",
                    "display_kind": "figure",
                    "requirement_key": "decision_curve_binary",
                    "shell_path": "paper/figures/Figure5.shell.json",
                },
                {
                    "display_id": "Figure6",
                    "display_kind": "figure",
                    "requirement_key": "kaplan_meier_grouped",
                    "shell_path": "paper/figures/Figure6.shell.json",
                },
            ]
        )
    if include_extended_evidence:
        displays.extend(
            [
                {
                    "display_id": "Figure7",
                    "display_kind": "figure",
                    "requirement_key": "cumulative_incidence_grouped",
                    "shell_path": "paper/figures/Figure7.shell.json",
                },
                {
                    "display_id": "Figure8",
                    "display_kind": "figure",
                    "requirement_key": "umap_scatter_grouped",
                    "shell_path": "paper/figures/Figure8.shell.json",
                },
                {
                    "display_id": "Figure9",
                    "display_kind": "figure",
                    "requirement_key": "pca_scatter_grouped",
                    "shell_path": "paper/figures/Figure9.shell.json",
                },
                {
                    "display_id": "Figure10",
                    "display_kind": "figure",
                    "requirement_key": "heatmap_group_comparison",
                    "shell_path": "paper/figures/Figure10.shell.json",
                },
                {
                    "display_id": "Figure11",
                    "display_kind": "figure",
                    "requirement_key": "correlation_heatmap",
                    "shell_path": "paper/figures/Figure11.shell.json",
                },
                {
                    "display_id": "Figure12",
                    "display_kind": "figure",
                    "requirement_key": "forest_effect_main",
                    "shell_path": "paper/figures/Figure12.shell.json",
                },
                {
                    "display_id": "Figure13",
                    "display_kind": "figure",
                    "requirement_key": "shap_summary_beeswarm",
                    "shell_path": "paper/figures/Figure13.shell.json",
                },
                {
                    "display_id": "Figure14",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_discrimination_calibration_panel",
                    "shell_path": "paper/figures/Figure14.shell.json",
                },
                {
                    "display_id": "Figure15",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_risk_group_summary",
                    "shell_path": "paper/figures/Figure15.shell.json",
                },
                {
                    "display_id": "Figure16",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_decision_curve",
                    "shell_path": "paper/figures/Figure16.shell.json",
                },
                {
                    "display_id": "Figure17",
                    "display_kind": "figure",
                    "requirement_key": "multicenter_generalizability_overview",
                    "shell_path": "paper/figures/Figure17.shell.json",
                },
                {
                    "display_id": "Figure18",
                    "display_kind": "figure",
                    "requirement_key": "time_dependent_roc_horizon",
                    "shell_path": "paper/figures/Figure18.shell.json",
                },
                {
                    "display_id": "Figure19",
                    "display_kind": "figure",
                    "requirement_key": "tsne_scatter_grouped",
                    "shell_path": "paper/figures/Figure19.shell.json",
                },
                {
                    "display_id": "Figure20",
                    "display_kind": "figure",
                    "requirement_key": "subgroup_forest",
                    "shell_path": "paper/figures/Figure20.shell.json",
                },
                {
                    "display_id": "Figure21",
                    "display_kind": "figure",
                    "requirement_key": "clustered_heatmap",
                    "shell_path": "paper/figures/Figure21.shell.json",
                },
                {
                    "display_id": "Figure22",
                    "display_kind": "figure",
                    "requirement_key": "clinical_impact_curve_binary",
                    "shell_path": "paper/figures/Figure22.shell.json",
                },
                {
                    "display_id": "Figure23",
                    "display_kind": "figure",
                    "requirement_key": "multivariable_forest",
                    "shell_path": "paper/figures/Figure23.shell.json",
                },
                {
                    "display_id": "Figure24",
                    "display_kind": "figure",
                    "requirement_key": "phate_scatter_grouped",
                    "shell_path": "paper/figures/Figure24.shell.json",
                },
                {
                    "display_id": "Figure25",
                    "display_kind": "figure",
                    "requirement_key": "diffusion_map_scatter_grouped",
                    "shell_path": "paper/figures/Figure25.shell.json",
                },
                {
                    "display_id": "Table2",
                    "display_kind": "table",
                    "requirement_key": "table2_time_to_event_performance_summary",
                    "shell_path": "paper/tables/Table2.shell.json",
                },
                {
                    "display_id": "Table3",
                    "display_kind": "table",
                    "requirement_key": "table3_clinical_interpretation_summary",
                    "shell_path": "paper/tables/Table3.shell.json",
                },
            ]
        )
    return displays


def _workspace_template_bindings(include_extended_evidence: bool) -> list[tuple[int, str]]:
    template_bindings = [
        (2, "roc_curve_binary"),
        (3, "pr_curve_binary"),
        (4, "calibration_curve_binary"),
        (5, "decision_curve_binary"),
        (6, "kaplan_meier_grouped"),
    ]
    if include_extended_evidence:
        template_bindings.extend(
            [
                (7, "cumulative_incidence_grouped"),
                (8, "umap_scatter_grouped"),
                (9, "pca_scatter_grouped"),
                (10, "heatmap_group_comparison"),
                (11, "correlation_heatmap"),
                (12, "forest_effect_main"),
                (13, "shap_summary_beeswarm"),
                (14, "time_to_event_discrimination_calibration_panel"),
                (15, "time_to_event_risk_group_summary"),
                (16, "time_to_event_decision_curve"),
                (17, "multicenter_generalizability_overview"),
                (18, "time_dependent_roc_horizon"),
                (19, "tsne_scatter_grouped"),
                (20, "subgroup_forest"),
                (21, "clustered_heatmap"),
                (22, "clinical_impact_curve_binary"),
                (23, "multivariable_forest"),
                (24, "phate_scatter_grouped"),
                (25, "diffusion_map_scatter_grouped"),
            ]
        )
    return template_bindings
