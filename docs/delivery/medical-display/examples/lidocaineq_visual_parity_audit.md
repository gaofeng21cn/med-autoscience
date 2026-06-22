# LidocaineQ 33 项逐图视觉审计

本文件是 MAS 绘图模板质量审计面，不作为 Gallery 永久章节。审计目的，是把学生手工确认过的发表级参考图与 MAS 当前模板输出逐一对应，发现图型语法、排版、配色和信息密度偏差。

- 参考项目：`LidocaineQ/Figure_Template`
- 参考根目录：`/private/tmp/lidocaineq_figure_template`
- 参考模板数：`33`
- 状态计数：`{"mas_computed_workflow_intentionally_extended": 1, "reference_style_matched": 32}`
- Contact sheet：`outputs/display-pack-gallery/lidocaineq_visual_parity_contact_sheet.png`

| Reference | MAS template | Status | Required action |
| --- | --- | --- | --- |
| `survival_km` | `kaplan_meier_grouped` | reference_style_matched | Use as MAS lower-bound start; paper-specific review should only tune censor marks, time scale, and final risk-table labels. |
| `cumulative_incidence_grouped` | `cumulative_incidence_grouped` | reference_style_matched | Use as MAS lower-bound start; paper-specific review should tune competing-risk labels and horizon ticks. |
| `roc_auc` | `roc_curve_binary` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `time_dependent_roc_horizon` | `time_dependent_roc_horizon` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `calibration_curve_binary` | `calibration_curve_binary` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `pr_curve_binary` | `pr_curve_binary` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `decision_curve_binary` | `decision_curve_binary` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `time_to_event_decision_curve` | `time_to_event_decision_curve` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `time_to_event_multihorizon_calibration_panel` | `time_to_event_multihorizon_calibration_panel` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `forest_cox` | `forest_effect_main` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `coefficient_path_panel` | `coefficient_path_panel` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `generalizability_subgroup_composite_panel` | `generalizability_subgroup_composite_panel` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `violin_box` | `distribution_violin_box` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `bar_stacked` | `composition_stacked_bar` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `risk_layering_monotonic_bars` | `risk_layering_monotonic_bars` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `scatter_correlation` | `correlation_scatter` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `embedding_umap_tsne` | `pca_scatter_grouped, tsne_scatter_grouped, umap_scatter_grouped` | mas_computed_workflow_intentionally_extended | Use as computed MAS workflows; do not force PCA/t-SNE/UMAP to share the same point geometry. |
| `heatmap` | `heatmap_group_comparison` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `confusion_matrix_heatmap_binary` | `confusion_matrix_heatmap_binary` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `volcano_deg` | `omics_volcano_panel` | reference_style_matched | Use as MAS lower-bound start; paper-specific review should tune differential-testing thresholds and label policy. |
| `gsea_enrichment` | `pathway_enrichment_dotplot_panel` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `oncoplot_mutation` | `genomic_alteration_landscape_panel` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `genomic_alteration_consequence_panel` | `genomic_alteration_consequence_panel` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `cnv_recurrence_summary_panel` | `cnv_recurrence_summary_panel` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `waterfall` | `waterfall_response` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `shap_dependence_panel` | `shap_dependence_panel` | reference_style_matched | Use as MAS lower-bound start; paper-specific review should tune interaction variable and axis units. |
| `shap_summary_beeswarm` | `shap_summary_beeswarm` | reference_style_matched | Use as MAS lower-bound start; paper-specific review should tune feature ordering and colour-bar label. |
| `shap_waterfall_local_explanation_panel` | `shap_waterfall_local_explanation_panel` | reference_style_matched | Use as MAS lower-bound start; paper-specific review should tune patient label and contribution units. |
| `model_complexity_audit_panel` | `model_complexity_audit_panel` | reference_style_matched | Use as MAS lower-bound start; paper-specific review should tune selected feature count and metric naming. |
| `celltype_marker_dotplot_panel` | `celltype_marker_dotplot_panel` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `sankey_alluvial` | `alluvial_transition` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `radar` | `radar_profile` | reference_style_matched | Use as MAS lower-bound start; run paper-specific visual audit before claiming final publication-ready output. |
| `baseline_table` | `table1_baseline_characteristics` | reference_style_matched | Use as Gallery preview only; table_shell remains the authoritative data/table surface. |
