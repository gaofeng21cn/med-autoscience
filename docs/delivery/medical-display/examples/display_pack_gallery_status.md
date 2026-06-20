# MAS Display Pack Gallery Status

Owner: `MedAutoScience`
Purpose: `generated_display_pack_gallery_status`
State: `generated_active_support`
Machine boundary: 本文由 `scripts/build-display-pack-gallery.py --publish-docs` 从 Gallery manifest / canonical catalog 生成。机器真相继续归 template descriptor、canonical catalog、Gallery manifest、layout sidecar、renderer source、tests、真实论文 artifact、visual-audit receipt、owner receipt 和 publication gate。

## 当前数量口径

| Metric | Count |
| --- | ---: |
| Gallery evidence figures | 28 |
| Current canonical templates | 31 |
| Current non-visual canonical inventory | 3 |
| Retired alias / duplicate ids | 35 |
| Migration index entries | 66 |
| Current Python evidence templates | 0 |

`Gallery evidence figures` 是 PDF Gallery 中展示的 R/ggplot2 数据证据图数量。`Current canonical templates` 是当前可推荐 canonical surface，包含不进入 ggplot2 evidence Gallery 的非视觉库存。`Retired alias / duplicate ids` 只用于显式旧 ID 迁移，不是 current template，也不是 Gallery 卡片。

## Renderer 与质量口径

- gallery default surface: `canonical_current_r_ggplot2_evidence_templates`
- evidence figures default to R/ggplot2: `true`
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

## Analysis Responsibility

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

## Gallery 分类

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

## 非视觉库存

| Template | Category | Kind |
| --- | --- | --- |
| `cohort_flow_figure` | Publication Shells and Tables | illustration_shell |
| `submission_graphical_abstract` | Publication Shells and Tables | illustration_shell |
| `table1_baseline_characteristics` | Publication Shells and Tables | table_shell |
