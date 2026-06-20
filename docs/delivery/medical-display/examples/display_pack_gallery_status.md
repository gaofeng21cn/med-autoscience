# MAS 医学论文配图 Gallery 生成状态

Owner: `MedAutoScience`
Purpose: `generated_display_pack_gallery_status`
State: `generated_active_support`
Machine boundary: 本文由 `scripts/build-display-pack-gallery.py --publish-docs` 从 Gallery manifest / canonical catalog 生成。机器真相继续归 template descriptor、canonical catalog、Gallery manifest、layout sidecar、renderer source、tests、真实论文 artifact、visual-audit receipt、owner receipt 和 publication gate。

## 当前数量口径

| 指标 | 数量 |
| --- | ---: |
| Gallery evidence figures | 28 |
| Gallery design / flow figures | 2 |
| Gallery visual templates | 30 |
| Current canonical templates | 31 |
| Current non-visual canonical inventory | 3 |
| Retired alias / duplicate ids | 35 |
| Migration index entries | 66 |
| Current Python evidence templates | 0 |
| Page-level composition recipes | 6 |
| Composition storyboard gallery pages | 6 |

`Gallery evidence figures` 是 PDF 画册中展示的 R/ggplot2 数据证据图数量。`Gallery design / flow figures` 是 PDF/HTML 中真实渲染的 cohort flow、graphical abstract 等非数据设计图起点。`Composition storyboard gallery pages` 是 PDF/HTML 前段展示的图页级方案数量。`Page-level composition recipes` 是组织多个数据证据面板的图页方案，不是更多单图模板。`Current canonical templates` 是当前可推荐 canonical surface。`Retired alias / duplicate ids` 只用于显式旧 ID 迁移，不是 current template，也不是画册卡片。

## 渲染器与质量口径

- gallery default surface: `canonical_current_visual_gallery_templates`
- evidence gallery default surface: `canonical_current_r_ggplot2_evidence_templates`
- design gallery default surface: `canonical_current_illustration_shell_templates`
- evidence figures default to R/ggplot2: `true`
- Python illustration shells visible as design cards: `true`
- Python evidence retained without advantage proof: `false`
- style profile: `paper_neutral_clinical_v1`
- journal palette: `nature_informed_clinical_publication_v1`
- quality overall status: `not_publication_ready`
- publication-ready claim authorized: `false`
- blocked templates after current render: `0`
- lower-bound review required: `28`
- gallery lower-bound admission: `gallery_lower_bound_passed_requires_paper_audit`
- publication quality profile coverage: `31/31` (100%)
- publication polish policy: `mas_publication_polish_policy.v1`
- figure workflow policy: `mas_nature_skills_figure_workflow_lifecycle.v1`
- composition recipe policy: `mas_medical_figure_composition_recipes.v1`

## 数据处理责任

| Responsibility | Current templates |
| --- | ---: |
| `computed_in_template` | 3 |
| `illustration_shell` | 2 |
| `table_shell` | 1 |
| `validated_summary_required` | 25 |

- raw analysis requests fail closed unless the selected template declares `computed_in_template`
- `validated_summary_required` templates render upstream analysis outputs; they do not fit models, recompute curves, run differential testing, infer SHAP values, or call variants

## Paper-use 前置检查

- `core_conclusion_and_evidence_chain_locked`
- `paper_local_data_and_statistics_refs_present`
- `semantic_palette_roles_resolved_from_article_style_profile`
- `guide_legend_colorbar_overlap_checked_after_render`
- `final_physical_size_readability_checked`
- `multipanel_hierarchy_and_shared_guides_checked`
- `vector_or_high_resolution_export_recorded`
- `visual_audit_receipt_or_residual_item_recorded`

## 图件工作流前置检查

- `core_conclusion_and_evidence_chain_locked`
- `storyboard_panel_hierarchy_declared`
- `paper_local_data_and_statistics_refs_present`
- `semantic_palette_roles_resolved_from_article_style_profile`
- `rendered_artifact_inspected_at_final_size`
- `guide_legend_colorbar_overlap_checked_after_render`
- `revision_delta_or_residual_item_recorded`
- `visual_audit_receipt_or_residual_item_recorded`
- `owner_or_publication_gate_receipt_present_for_claim_bearing_figures`

## 页面级图页方案

| Recipe | Title | Hero panel | Supporting | Primitive families | Default layout |
| --- | --- | --- | ---: | ---: | --- |
| `clinical_triptych_prediction` | Clinical Prediction Triptych | primary_model_performance_summary | 3 | 5 | one_large_left_panel_with_two_or_three_right_support_panels |
| `model_validation_dashboard` | Model Validation Dashboard | validation_summary_or_generalizability | 3 | 7 | performance_or_generalizability_hero_with_explanation_and_governance_support |
| `schematic_led_composite` | Schematic-led Composite | schematic_or_process_hero | 3 | 6 | schematic_hero_above_or_left_with_small_programmatic_evidence_panels |
| `image_plate_plus_quantification` | Image Plate plus Quantification | representative_image_plate | 3 | 5 | dark_or_neutral_image_plate_with_adjacent_white_background_quantification |
| `asymmetric_genomics_figure` | Asymmetric Genomics Figure | dominant_molecular_pattern | 3 | 6 | wide_pattern_hero_with_narrow_right_or_bottom_consequence_panels |
| `single_cell_atlas_storyboard` | Single-cell or Spatial Atlas Storyboard | cell_state_geometry_or_spatial_context | 3 | 7 | atlas_embedding_or_spatial_hero_with_marker_composition_and_trajectory_support |

## 非数据设计/流程图 Gallery

| Template | Display name | Renderer | Render status |
| --- | --- | --- | --- |
| `cohort_flow_figure` | Cohort Flow Figure | python | rendered |
| `submission_graphical_abstract` | Submission Graphical Abstract | python | rendered |

## 画册分类

| Category | Gallery evidence figures |
| --- | ---: |
| Clinical Utility | 2 |
| Data Geometry | 3 |
| Effect Estimate | 2 |
| Generalizability | 1 |
| Genomic and Omics | 6 |
| Matrix Pattern | 2 |
| Model Audit | 1 |
| Model Explanation | 3 |
| Prediction Performance | 3 |
| Time-to-Event | 5 |

## 表格/非图像库存

| Template | Category | Kind |
| --- | --- | --- |
| `cohort_flow_figure` | Publication Shells and Tables | illustration_shell |
| `submission_graphical_abstract` | Publication Shells and Tables | illustration_shell |
| `table1_baseline_characteristics` | Publication Shells and Tables | table_shell |
