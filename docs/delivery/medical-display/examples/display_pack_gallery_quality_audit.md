# MAS Display Pack Gallery Quality Audit

Owner: `MedAutoScience`
Purpose: `human_readable_quality_audit_for_display_pack_gallery`
State: `active_support`
Machine boundary: 人读质量审计。机器真相继续归 Gallery manifest、template descriptor、renderer source、layout sidecar、display lock、publication manifest、真实论文 artifact 和 owner receipt。

## 结论

当前 Gallery 是 `lower_bound_reference_templates_only`，不能声明为 publication-ready。模板提供质量下限和图型结构参考；AI 被授权按论文具体主张自由修改结构、排版、标签、配色和组合方式来拔高上限。

- overall_status: `not_publication_ready`
- publication_ready_claim_authorized: `false`
- visual template count: `28`
- non-visual inventory count: `3`
- lower-bound review required: `23`
- blocked templates: `5`

## 主要阻断项

| Blocker | Templates |
| --- | ---: |
| `coefficient_path_renderer_gap` | 1 |
| `km_risk_table_and_censor_mark_gap` | 1 |
| `multi_panel_readability_risk` | 2 |
| `oncoprint_annotation_track_gap` | 1 |

## 主要风险项

| Warning | Templates |
| --- | ---: |
| `composition_density_risk` | 1 |
| `legend_or_colorbar_overlap_risk` | 5 |

## 模板审计

| Template | Category | Renderer | Status | Blockers |
| --- | --- | --- | --- | --- |
| `calibration_curve_binary` | Prediction Performance | r_ggplot2 | `lower_bound_review_required` | none |
| `celltype_marker_dotplot_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `cnv_recurrence_summary_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `coefficient_path_panel` | Effect Estimate | r_ggplot2 | `not_publication_ready` | `coefficient_path_renderer_gap` |
| `confusion_matrix_heatmap_binary` | Matrix Pattern | r_ggplot2 | `lower_bound_review_required` | none |
| `cumulative_incidence_grouped` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `decision_curve_binary` | Clinical Utility | r_ggplot2 | `lower_bound_review_required` | none |
| `forest_effect_main` | Effect Estimate | r_ggplot2 | `lower_bound_review_required` | none |
| `generalizability_subgroup_composite_panel` | Generalizability | r_ggplot2 | `lower_bound_review_required` | none |
| `genomic_alteration_consequence_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `genomic_alteration_landscape_panel` | Genomic and Omics | r_ggplot2 | `not_publication_ready` | `oncoprint_annotation_track_gap` |
| `heatmap_group_comparison` | Matrix Pattern | r_ggplot2 | `lower_bound_review_required` | none |
| `kaplan_meier_grouped` | Time-to-Event | r_ggplot2 | `not_publication_ready` | `km_risk_table_and_censor_mark_gap` |
| `model_complexity_audit_panel` | Model Audit | r_ggplot2 | `not_publication_ready` | `multi_panel_readability_risk` |
| `omics_volcano_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `pathway_enrichment_dotplot_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `pca_scatter_grouped` | Data Geometry | r_ggplot2 | `lower_bound_review_required` | none |
| `pr_curve_binary` | Prediction Performance | r_ggplot2 | `lower_bound_review_required` | none |
| `risk_layering_monotonic_bars` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `roc_curve_binary` | Prediction Performance | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_dependence_panel` | Model Explanation | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_summary_beeswarm` | Model Explanation | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_waterfall_local_explanation_panel` | Model Explanation | r_ggplot2 | `not_publication_ready` | `multi_panel_readability_risk` |
| `time_dependent_roc_horizon` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `time_to_event_decision_curve` | Clinical Utility | r_ggplot2 | `lower_bound_review_required` | none |
| `time_to_event_multihorizon_calibration_panel` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `tsne_scatter_grouped` | Data Geometry | r_ggplot2 | `lower_bound_review_required` | none |
| `umap_scatter_grouped` | Data Geometry | r_ggplot2 | `lower_bound_review_required` | none |

## 分类完成度

| Category | Status | Completion | Gallery visual | R/ggplot2 evidence | Current Python evidence |
| --- | --- | ---: | ---: | ---: | ---: |
| Clinical Utility | `done` | 100% | 2 | 2 | 0 |
| Data Geometry | `done` | 100% | 3 | 3 | 0 |
| Effect Estimate | `done` | 100% | 2 | 2 | 0 |
| Generalizability | `done` | 100% | 1 | 1 | 0 |
| Genomic and Omics | `done` | 100% | 6 | 6 | 0 |
| Matrix Pattern | `done` | 100% | 2 | 2 | 0 |
| Model Audit | `done` | 100% | 1 | 1 | 0 |
| Model Explanation | `done` | 100% | 3 | 3 | 0 |
| Prediction Performance | `done` | 100% | 3 | 3 | 0 |
| Publication Shells and Tables | `done` | 100% | 0 | 0 | 0 |
| Time-to-Event | `done` | 100% | 5 | 5 | 0 |

## 当前 Python Evidence

| Template | Category | Kind | Renderer | Reason |
| --- | --- | --- | --- | --- |
| none | none | evidence_figure | python | current_pack_retains_no_python_evidence_templates |

## 默认面排除的非视觉库存

| Template | Category | Kind | Renderer | Reason |
| --- | --- | --- | --- | --- |
| none | none | none | none | none |

## 外部准则

- [nature_final_submission_artwork](https://www.nature.com/nature/for-authors/final-submission): Use consistent figure lettering, readable reduced-size labels, vector line art when possible, RGB color, and production-quality figure files.
- [ggplot2_theme_system](https://ggplot2.tidyverse.org/reference/theme.html): Use a single theme system for titles, labels, fonts, backgrounds, gridlines, and legends so all evidence figures share one article-level visual grammar.
- [ggsci_npg_palette](https://nanx.me/ggsci/reference/scale_npg.html): Nature Publishing Group inspired discrete palettes are mature ggplot2-compatible references for publication-style categorical roles.
- [colorspace_hcl_palettes](https://colorspace.r-forge.r-project.org/): HCL-based qualitative, sequential and diverging palettes are a stable basis for article-level semantic color roles.
- [viridis_perceptual_palette](https://sjmgarnier.github.io/viridis/): Perceptually uniform and color-vision-friendly sequential palettes are preferred for continuous matrix and density-like encodings.
- [complexheatmap_color_mapping](https://jokergoo.github.io/ComplexHeatmap-reference/book/a-single-heatmap.html): Matrix heatmaps need fixed value-to-color mapping rather than per-plot drift; shared sequential and diverging mappings preserve cross-figure comparability.
