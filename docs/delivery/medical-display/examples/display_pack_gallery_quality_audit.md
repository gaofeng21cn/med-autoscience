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
- lower-bound review required: `28`
- blocked templates: `0`
- publication polish policy: `mas_publication_polish_policy.v1`
- figure workflow policy: `mas_nature_skills_figure_workflow_lifecycle.v1`
- composition recipe policy: `mas_medical_figure_composition_recipes.v1`
- composition recipes: `6`

## Paper-use 前置检查

- `core_conclusion_and_evidence_chain_locked`
- `paper_local_data_and_statistics_refs_present`
- `semantic_palette_roles_resolved_from_article_style_profile`
- `guide_legend_colorbar_overlap_checked_after_render`
- `final_physical_size_readability_checked`
- `multipanel_hierarchy_and_shared_guides_checked`
- `vector_or_high_resolution_export_recorded`
- `visual_audit_receipt_or_residual_item_recorded`

## Figure Workflow 前置检查

- `core_conclusion_and_evidence_chain_locked`
- `storyboard_panel_hierarchy_declared`
- `paper_local_data_and_statistics_refs_present`
- `semantic_palette_roles_resolved_from_article_style_profile`
- `rendered_artifact_inspected_at_final_size`
- `guide_legend_colorbar_overlap_checked_after_render`
- `revision_delta_or_residual_item_recorded`
- `visual_audit_receipt_or_residual_item_recorded`
- `owner_or_publication_gate_receipt_present_for_claim_bearing_figures`

## Composition Recipe 前置检查

- `composition_recipe_selected_or_explicitly_declined`
- `hero_panel_role_declared`
- `shared_legend_or_direct_label_strategy_declared`
- `programmatic_evidence_primitives_preserve_data_statistics_refs`

## 页面级 Composition Recipes

| Recipe | Title | Hero panel |
| --- | --- | --- |
| `clinical_triptych_prediction` | Clinical Prediction Triptych | primary_model_performance_summary |
| `model_validation_dashboard` | Model Validation Dashboard | validation_summary_or_generalizability |
| `schematic_led_composite` | Schematic-led Composite | schematic_or_process_hero |
| `image_plate_plus_quantification` | Image Plate plus Quantification | representative_image_plate |
| `asymmetric_genomics_figure` | Asymmetric Genomics Figure | dominant_molecular_pattern |
| `single_cell_atlas_storyboard` | Single-cell or Spatial Atlas Storyboard | cell_state_geometry_or_spatial_context |

## 高风险图族复核项

| Family | Checks |
| --- | --- |
| `kaplan_meier_with_risk_table` | `risk_table`, `censor_marks`, `time_scale`, `event_definition`, `strata_order` |
| `genomic_landscape_or_oncoprint` | `sample_order`, `annotation_tracks`, `alteration_semantics`, `shared_heatmap_palette` |
| `matrix_heatmap` | `fixed_scale_mapping`, `sequential_vs_diverging_semantics`, `colorbar_tick_density` |
| `shap_and_model_explanation` | `feature_order`, `direction_encoding`, `legend_density`, `panel_claim_mapping` |
| `coefficient_path_or_high_density_lines` | `label_strategy`, `direct_label_or_shared_legend`, `line_density`, `semantic_fit` |
| `multipanel_storyboard` | `hero_panel`, `panel_labels`, `shared_guides`, `remove_non_claim_panels` |

## 主要阻断项

| Blocker | Templates |
| --- | ---: |
| none | 0 |

## 主要风险项

| Warning | Templates |
| --- | ---: |
| `coefficient_path_semantic_fit_review` | 1 |
| `composition_density_risk` | 1 |
| `km_risk_table_and_censor_mark_review` | 1 |
| `legend_or_colorbar_overlap_risk` | 5 |
| `multi_panel_readability_review` | 2 |
| `oncoprint_annotation_track_review` | 1 |

## 模板审计

| Template | Category | Renderer | Status | Blockers |
| --- | --- | --- | --- | --- |
| `calibration_curve_binary` | Prediction Performance | r_ggplot2 | `lower_bound_review_required` | none |
| `celltype_marker_dotplot_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `cnv_recurrence_summary_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `coefficient_path_panel` | Effect Estimate | r_ggplot2 | `lower_bound_review_required` | none |
| `confusion_matrix_heatmap_binary` | Matrix Pattern | r_ggplot2 | `lower_bound_review_required` | none |
| `cumulative_incidence_grouped` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `decision_curve_binary` | Clinical Utility | r_ggplot2 | `lower_bound_review_required` | none |
| `forest_effect_main` | Effect Estimate | r_ggplot2 | `lower_bound_review_required` | none |
| `generalizability_subgroup_composite_panel` | Generalizability | r_ggplot2 | `lower_bound_review_required` | none |
| `genomic_alteration_consequence_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `genomic_alteration_landscape_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `heatmap_group_comparison` | Matrix Pattern | r_ggplot2 | `lower_bound_review_required` | none |
| `kaplan_meier_grouped` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `model_complexity_audit_panel` | Model Audit | r_ggplot2 | `lower_bound_review_required` | none |
| `omics_volcano_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `pathway_enrichment_dotplot_panel` | Genomic and Omics | r_ggplot2 | `lower_bound_review_required` | none |
| `pca_scatter_grouped` | Data Geometry | r_ggplot2 | `lower_bound_review_required` | none |
| `pr_curve_binary` | Prediction Performance | r_ggplot2 | `lower_bound_review_required` | none |
| `risk_layering_monotonic_bars` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `roc_curve_binary` | Prediction Performance | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_dependence_panel` | Model Explanation | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_summary_beeswarm` | Model Explanation | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_waterfall_local_explanation_panel` | Model Explanation | r_ggplot2 | `lower_bound_review_required` | none |
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
- [nature_skills_figure_contract](https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-figure): Figure work should start from core conclusion, evidence chain, panel hierarchy, backend-exclusive export, and final visual QA; MAS adapts this into a nonblocking R-first agent contract.
