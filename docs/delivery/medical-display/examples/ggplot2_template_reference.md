# MAS Display Pack Gallery

Owner: `MedAutoScience`
Purpose: `human_readable_gallery_for_builtin_mas_display_templates`
State: `active_support`
Machine boundary: 人读示例文档。机器真相继续归 display-pack template descriptor、renderer source、`paper/publication_style_profile.json`、layout sidecar、display lock、publication manifest、tests 和真实论文 artifacts。

- [PDF Gallery](./ggplot2_template_gallery.pdf)
- [Generated Status](./display_pack_gallery_status.md)
- [Quality Audit](./display_pack_gallery_quality_audit.md)

HTML、manifest、payload、layout sidecar、PNG/SVG/PDF 单图导出属于可再生成的本地输出，默认写入仓库忽略的 `outputs/display-pack-gallery/`。需要重建时运行：

```bash
./scripts/run-python-clean.sh scripts/build-display-pack-gallery.py --publish-docs
```

## 索引

| Category | Templates |
| --- | ---: |
| Prediction Performance | 3 |
| Clinical Utility | 2 |
| Time-to-Event | 5 |
| Effect Estimate | 2 |
| Generalizability | 1 |
| Data Geometry | 3 |
| Matrix Pattern | 2 |
| Model Explanation | 3 |
| Model Audit | 1 |

## 当前默认风格

- `style_profile_id`: `paper_neutral_clinical_v1`
- `journal_palette_ref`: `nature_informed_clinical_publication_v1`
- canonical renderer inventory: `r_ggplot2=28`, `python=0`, `n/a=0`
- canonical current R/ggplot2 evidence gallery cards: `28`
- current Python evidence templates: `0`
- Python design / flow shells in ggplot2 evidence Gallery: `0`
- rendered evidence gallery cards: `28`
- visual canonical evidence families: `28`
- duplicate / legacy aliases are mapped in generated status / manifest but are not current template directories or Gallery cards.
- core medical figure families: sourced from `contracts/medical-figure-family-catalog/`
- figure family policy: `intent_first_current_template_surface`
- AI adaptation policy: `canonical_family_baseline_then_paper_local_adaptation`
- Nature-Skills figure learning head: `5d2ba1dee1c087be6de8f4a8aad4b27f04974be9`
- figure contract policy: `mas_nature_skills_informed_figure_contract.v1`

## 风格口径

MAS 默认不是 Nature 官方模板复刻，也不是 Lancet 专用模板。当前内置默认是 `nature_informed_clinical_publication_v1`：白底、左下轴线、小字号、细轴线、弱网格、统一 clinical palette、sequential/diverging heatmap palette 和横向 colorbar。数据分析产生的 evidence figure 以 R/ggplot2 为第一公民；未证明优于 R/ggplot2 的 Python evidence 模板不进入当前 pack、隐藏库存或 Gallery 对比图。设计、流程和 graphical abstract shell 可以用 SVG、Python composition 或 imagegen-assisted art direction，但不承担统计证据权威，也不混入这份 ggplot2 evidence Gallery。

Nature-Skills 的 `nature-figure` 已作为 clean-room 质量流程学习源吸收：MAS 现在要求图件先有 core conclusion、evidence chain、panel hierarchy、journal/export contract 和最终 visual QA receipt。与上游不同的是，MAS 不把 “Python or R?” 作为默认 evidence path 的阻塞问题；默认数据证据图直接走 R/ggplot2，同时保留 AI 对布局、panel、配色、标签、backend 和组合方式的 paper-local 改造权限。
