# MAS Display Pack Gallery Quality Audit

Owner: `MedAutoScience`
Purpose: `human_readable_quality_audit_for_display_pack_gallery`
State: `active_support`
Machine boundary: 人读质量审计。机器真相继续归 Gallery manifest、template descriptor、renderer source、layout sidecar、display lock、publication manifest、真实论文 artifact 和 owner receipt。

## 结论

当前 Gallery 是 `lower_bound_reference_templates_only`，不能声明为 publication-ready。模板提供质量下限和图型结构参考；AI 被授权按论文具体主张自由修改结构、排版、标签、配色和组合方式来拔高上限。

- overall_status: `not_publication_ready`
- publication_ready_claim_authorized: `false`
- visual template count: `20`
- non-visual inventory count: `1`
- lower-bound review required: `13`
- blocked templates: `7`

## 主要阻断项

| Blocker | Templates |
| --- | ---: |
| `composition_density_risk` | 1 |
| `illustration_shell_style_gap` | 2 |
| `low_information_density` | 1 |
| `multi_panel_readability_risk` | 2 |
| `python_current_style_gap` | 2 |

## 主要风险项

| Warning | Templates |
| --- | ---: |
| `composition_density_risk` | 4 |
| `legacy_python_comparison_available` | 6 |
| `legacy_python_comparison_excluded_after_failed_render` | 2 |
| `legend_or_colorbar_overlap_risk` | 6 |
| `python_renderer_style_alignment_required` | 7 |

## 模板审计

| Template | Category | Renderer | Status | Blockers |
| --- | --- | --- | --- | --- |
| `binary_calibration_decision_curve_panel` | Clinical Utility | r_ggplot2 | `lower_bound_review_required` | none |
| `coefficient_path_panel` | Effect Estimate | r_ggplot2 | `lower_bound_review_required` | none |
| `cohort_flow_figure` | Publication Shells and Tables | python | `not_publication_ready` | `illustration_shell_style_gap` |
| `forest_effect_main` | Effect Estimate | r_ggplot2 | `lower_bound_review_required` | none |
| `genomic_alteration_landscape_panel` | Matrix Pattern | r_ggplot2 | `not_publication_ready` | `low_information_density` |
| `heatmap_group_comparison` | Matrix Pattern | r_ggplot2 | `lower_bound_review_required` | none |
| `kaplan_meier_grouped` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `model_complexity_audit_panel` | Model Audit | r_ggplot2 | `not_publication_ready` | `multi_panel_readability_risk` |
| `multicenter_generalizability_overview` | Generalizability | python | `lower_bound_review_required` | none |
| `omics_volcano_panel` | Data Geometry | r_ggplot2 | `lower_bound_review_required` | none |
| `partial_dependence_ice_panel` | Model Explanation | python | `not_publication_ready` | `python_current_style_gap` |
| `pathway_enrichment_dotplot_panel` | Matrix Pattern | r_ggplot2 | `lower_bound_review_required` | none |
| `phenotype_gap_structure_figure` | Publication Shells and Tables | python | `lower_bound_review_required` | none |
| `roc_curve_binary` | Prediction Performance | r_ggplot2 | `lower_bound_review_required` | none |
| `shap_grouped_local_support_domain_panel` | Model Explanation | python | `not_publication_ready` | `multi_panel_readability_risk` |
| `shap_summary_beeswarm` | Model Explanation | r_ggplot2 | `lower_bound_review_required` | none |
| `single_cell_atlas_overview_panel` | Data Geometry | python | `not_publication_ready` | `composition_density_risk`, `python_current_style_gap` |
| `submission_graphical_abstract` | Publication Shells and Tables | python | `not_publication_ready` | `illustration_shell_style_gap` |
| `time_to_event_discrimination_calibration_panel` | Time-to-Event | r_ggplot2 | `lower_bound_review_required` | none |
| `umap_scatter_grouped` | Data Geometry | r_ggplot2 | `lower_bound_review_required` | none |

## 外部准则

- [nature_final_submission_artwork](https://www.nature.com/nature/for-authors/final-submission): Use consistent sans-serif figure lettering, readable reduced-size labels, vector line art when possible, 0.25-1 pt final line weights, RGB color, and production-quality figure files.
- [plos_figure_guidelines](https://journals.plos.org/plosone/s/figures): Keep figures at intended dimensions, 300-600 dpi, fonts in the 8-12 pt range for submitted artwork, and avoid low-resolution or upsampled elements.
- [ggsci](https://github.com/nanxstats/ggsci): Scientific-journal-inspired palettes are useful references, but MAS keeps one semantic clinical palette instead of exposing many style presets.
- [ggpubfigs](https://github.com/JLSteenwyk/ggpubfigs): Publication themes should be restrained and colorblind friendly; palette accessibility is part of the template quality floor.
