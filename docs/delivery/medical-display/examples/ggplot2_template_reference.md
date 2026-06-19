# MAS Display Pack Gallery

Owner: `MedAutoScience`
Purpose: `human_readable_gallery_for_builtin_mas_display_templates`
State: `active_support`
Machine boundary: 人读示例文档。机器真相继续归 display-pack template descriptor、renderer source、`paper/publication_style_profile.json`、layout sidecar、display lock、publication manifest、tests 和真实论文 artifacts。

- [PDF Gallery](./ggplot2_template_gallery.pdf)

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
| Data Geometry | 3 |
| Matrix Pattern | 3 |
| Model Explanation | 3 |
| Model Audit | 1 |
| Publication Shells and Tables | 4 |

## 当前默认风格

- `style_profile_id`: `paper_neutral_clinical_v1`
- `journal_palette_ref`: `nature_informed_clinical_publication_v1`
- canonical renderer inventory: `r_ggplot2=13`, `python=7`, `n/a=1`
- canonical rendered image templates: `20`
- Python comparisons rendered: `6`
- excluded Python comparisons: `celltype_signature_heatmap`, `model_complexity_audit_panel`, `time_to_event_decision_curve`, `time_to_event_discrimination_calibration_panel`, `time_to_event_risk_group_summary`
- canonical families: `21`
- upstream nature-skills fresh HEAD checked on `2026-06-19`: `54eadc65d1c0535e90d792a87ab718d848ccbb7a`

## 风格口径

MAS 默认不是 Nature 官方模板复刻，也不是 Lancet 专用模板。当前内置默认是 `nature_informed_clinical_publication_v1`：白底、左下轴线、小字号、细轴线、弱网格、统一 clinical palette、sequential heatmap 和右侧短 colorbar。它吸收了 nature-skills 的 archetype-first、backend-exclusive、shared-legend / dedicated-guide 和 vector export discipline，但不引入外部 runner 或 publication authority。默认应用面只展示 canonical 图型家族；旧模板 ID 作为 migration aliases 保留在 manifest 中，不作为用户默认候选。
