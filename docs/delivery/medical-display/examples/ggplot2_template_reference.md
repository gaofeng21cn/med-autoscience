# MAS Display Pack Gallery

Owner: `MedAutoScience`
Purpose: `human_readable_gallery_for_builtin_mas_display_templates`
State: `active_support`
Machine boundary: 人读示例文档。机器真相继续归 display-pack template descriptor、renderer source、`paper/publication_style_profile.json`、layout sidecar、display lock、publication manifest、tests 和真实论文 artifacts。

- [PDF Gallery](./ggplot2_template_gallery.pdf)
- [Quality Audit](./display_pack_gallery_quality_audit.md)

全量 HTML、manifest、payload、layout sidecar、PNG/SVG/PDF 单图导出属于可再生成的本地输出，默认写入仓库忽略的 `outputs/display-pack-gallery/`。需要重建时运行：

```bash
./scripts/run-python-clean.sh scripts/build-display-pack-gallery.py --publish-docs
```

## 索引

| Category | Templates |
| --- | ---: |
| Prediction Performance | 1 |
| Clinical Utility | 1 |
| Time-to-Event | 2 |
| Effect Estimate | 2 |
| Generalizability | 1 |
| Data Geometry | 2 |
| Matrix Pattern | 3 |
| Model Explanation | 3 |
| Model Audit | 1 |
| Publication Shells and Tables | 2 |

## 当前默认风格

- `style_profile_id`: `paper_neutral_clinical_v1`
- `journal_palette_ref`: `nature_informed_clinical_publication_v1`
- canonical renderer inventory: `r_ggplot2=16`, `python=2`, `n/a=0`
- default R/ggplot2 evidence templates: `16`
- default Python evidence templates: `0`
- default Python design / flow shells: `2`
- canonical rendered image templates: `18`
- Python comparisons rendered: `9`
- excluded Python comparisons: `celltype_signature_heatmap`, `model_complexity_audit_panel`, `time_to_event_decision_curve`, `time_to_event_discrimination_calibration_panel`, `time_to_event_risk_group_summary`
- visual canonical gallery families: `18`
- core medical figure families: sourced from `contracts/medical-figure-family-catalog/`
- figure family policy: `core_catalog_bound_metadata_only`
- AI adaptation policy: `canonical_family_baseline_then_paper_local_adaptation`
- upstream nature-skills fresh HEAD checked on `2026-06-19`: `54eadc65d1c0535e90d792a87ab718d848ccbb7a`

## 风格口径

MAS 默认不是 Nature 官方模板复刻，也不是 Lancet 专用模板。当前内置默认是 `nature_informed_clinical_publication_v1`：白底、左下轴线、小字号、细轴线、弱网格、统一 clinical palette、sequential/diverging heatmap palette 和水平短 colorbar。数据分析产生的 evidence figure 默认以 R/ggplot2 为第一公民；Python evidence 模板只有在有明确优势证明或显式纸稿需求时才作为非默认迁移输入。设计、流程和 graphical abstract shell 可以用 SVG、Python composition 或 imagegen-assisted art direction，但不承担统计证据权威。旧模板 ID 作为 migration aliases 保留在 manifest 中，不作为用户默认候选。Gallery manifest 的医学图型 ontology 来自 `contracts/medical-figure-family-catalog/`，当前模板展示面由 pack-local canonical template catalog 提供代表模板和 migration aliases。
