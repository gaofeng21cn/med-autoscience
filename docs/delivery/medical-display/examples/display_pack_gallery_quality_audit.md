# MAS Display Pack Gallery Quality Audit

Owner: `MedAutoScience`
Purpose: `human_readable_quality_audit_for_display_pack_gallery`
State: `active_support`
Machine boundary: 人读质量审计。机器真相继续归 Gallery manifest、template descriptor、renderer source、layout sidecar、display lock、publication manifest、真实论文 artifact 和 owner receipt。

## 结论

当前 Gallery 是 `lower_bound_reference_templates_only`，不能声明为 publication-ready。模板提供质量下限和图型结构参考；AI 被授权按论文具体主张自由修改结构、排版、标签、配色和组合方式来拔高上限。

- overall_status: `not_publication_ready`
- publication_ready_claim_authorized: `false`
- visual template count: `18`
- non-visual inventory count: `1`
- lower-bound review required: `13`
- blocked templates: `5`

## 主要阻断项

| Blocker | Templates |
| --- | ---: |
| `illustration_shell_style_gap` | 2 |
| `low_information_density` | 1 |
| `multi_panel_readability_risk` | 2 |

## 主要风险项

| Warning | Templates |
| --- | ---: |
| `composition_density_risk` | 3 |
| `legend_or_colorbar_overlap_risk` | 6 |
| `python_renderer_style_alignment_required` | 2 |

## 模板审计

| Template | Category | Renderer | Status | Blockers |
| --- | --- | --- | --- | --- |
| `binary_calibration_decision_curve_panel` | Clinical Utility | r_ggplot2 | `lower_bound_review_required` | none |
| `coefficient_path_panel` | Effect Estimate | r_ggplot2 | `lower_bound_review_required` | none |
| `cohort_flow_figure` | Publication Shells and Tables | python | `not_publication_ready` | `illustration_shell_style_gap` |
| `forest_effect_main` | Effect Estimate | r_ggplot2 | `lower_bound_review_required` | none |
| `generalizability_subgroup_composite_panel` | Generalizability | r_ggplot2 | `lower_bound_review_required` | none |
| `genomic_alteration_landscape_panel` | Matrix Pattern | r_ggplot2 | `not_publication_ready` | `low_information_density` |
| `heatmap_group_comparison` | Matrix Pattern | r_ggplot2 | `lower_bound_review_required` | none |
| `kaplan_meier_grouped` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `model_complexity_audit_panel` | Model Audit | r_ggplot2 | `not_publication_ready` | `multi_panel_readability_risk` |
| `omics_volcano_panel` | Data Geometry | r_ggplot2 | `lower_bound_review_required` | none |
| `pathway_enrichment_dotplot_panel` | Matrix Pattern | r_ggplot2 | `lower_bound_review_required` | none |
| `roc_curve_binary` | Prediction Performance | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_dependence_panel` | Model Explanation | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_summary_beeswarm` | Model Explanation | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_waterfall_local_explanation_panel` | Model Explanation | r_ggplot2 | `not_publication_ready` | `multi_panel_readability_risk` |
| `submission_graphical_abstract` | Publication Shells and Tables | python | `not_publication_ready` | `illustration_shell_style_gap` |
| `time_to_event_discrimination_calibration_panel` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `umap_scatter_grouped` | Data Geometry | r_ggplot2 | `lower_bound_review_required` | none |

## 分类完成度

| Category | Status | Completion | Default visual | R/ggplot2 evidence | Current Python evidence |
| --- | --- | ---: | ---: | ---: | ---: |
| Clinical Utility | `done` | 100% | 1 | 1 | 0 |
| Data Geometry | `done` | 100% | 2 | 2 | 0 |
| Effect Estimate | `done` | 100% | 2 | 2 | 0 |
| Generalizability | `done` | 100% | 1 | 1 | 0 |
| Matrix Pattern | `done` | 100% | 3 | 3 | 0 |
| Model Audit | `done` | 100% | 1 | 1 | 0 |
| Model Explanation | `done` | 100% | 3 | 3 | 0 |
| Prediction Performance | `done` | 100% | 1 | 1 | 0 |
| Publication Shells and Tables | `done` | 100% | 2 | 0 | 0 |
| Time-to-Event | `done` | 100% | 2 | 2 | 0 |

    ## 当前 Python Evidence

| Template | Category | Kind | Renderer | Reason |
| --- | --- | --- | --- | --- |
| none | none | evidence_figure | python | current_pack_retains_no_python_evidence_templates |

## 默认面排除的非视觉库存

| Template | Category | Kind | Renderer | Reason |
| --- | --- | --- | --- | --- |
| none | none | none | none | none |

## 外部准则

- [nature_final_submission_artwork](https://www.nature.com/nature/for-authors/final-submission): Use consistent sans-serif figure lettering, readable reduced-size labels, vector line art when possible, 0.25-1 pt final line weights, RGB color, and production-quality figure files.
- [ggplot2_theme_system](https://ggplot2.tidyverse.org/reference/theme.html): Use a single theme system for titles, labels, fonts, backgrounds, gridlines, and legends so all evidence figures share one article-level visual grammar.
- [ggsci](https://nanx.me/ggsci/): Scientific-journal-inspired ggplot2 palettes are useful references, but MAS keeps one semantic clinical palette instead of exposing many style presets.
- [complexheatmap_color_mapping](https://jokergoo.github.io/ComplexHeatmap-reference/book/a-single-heatmap.html): Matrix heatmaps need fixed value-to-color mapping rather than per-plot drift; shared sequential and diverging mappings preserve cross-figure comparability.
