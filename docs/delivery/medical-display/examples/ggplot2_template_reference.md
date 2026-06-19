# MAS Display Pack Gallery

Owner: `MedAutoScience`
Purpose: `human_readable_gallery_for_builtin_mas_display_templates`
State: `active_support`
Machine boundary: 人读示例文档。机器真相继续归 display-pack template descriptor、renderer source、`paper/publication_style_profile.json`、layout sidecar、display lock、publication manifest、tests 和真实论文 artifacts。

- [PDF Gallery](./ggplot2_template_gallery.pdf)

全量 HTML、manifest、payload、layout sidecar、PNG/SVG/PDF 单图导出属于可再生成的本地输出，默认写入仓库忽略的 `outputs/display-pack-gallery/`，不作为 repository canonical evidence 提交。需要重建时运行：

```bash
./scripts/run-python-clean.sh scripts/build-display-pack-gallery.py --publish-docs
```

## 索引

| Category | Templates |
| --- | ---: |
| Prediction Performance | 3 |
| Clinical Utility | 5 |
| Time-to-Event | 10 |
| Effect Estimate | 7 |
| Generalizability | 3 |
| Data Geometry | 15 |
| Matrix Pattern | 15 |
| Model Explanation | 19 |
| Model Audit | 1 |
| Publication Shells and Tables | 20 |

## 当前默认风格

- `style_profile_id`: `paper_neutral_clinical_v1`
- `journal_palette_ref`: `nature_informed_clinical_publication_v1`
- renderer inventory: `r_ggplot2=55`, `python=36`, `n/a=7`
- rendered image templates: `91`
- legacy Python comparisons rendered: `28`
- excluded legacy Python baselines: `celltype_signature_heatmap`, `model_complexity_audit_panel`, `time_to_event_decision_curve`, `time_to_event_discrimination_calibration_panel`, `time_to_event_risk_group_summary`
- upstream nature-skills fresh HEAD checked on `2026-06-18`: `1cb9070fdd94929d5f267ce6585ac87e2cba60b3`

## 风格口径

MAS 默认不是 Nature 官方模板复刻，也不是 Lancet 专用模板。当前内置默认是 `nature_informed_clinical_publication_v1`：白底、`theme_classic` / 左下轴线、小字号、细轴线、弱网格、蓝/青/红/橙/紫/中性语义色板。它吸收了 nature-skills 的 R/ggplot2 workflow、语义 palette、backend-exclusive 和 publication export discipline，但不引入外部 runner 或 publication authority。
