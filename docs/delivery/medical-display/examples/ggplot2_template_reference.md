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
| Prediction Performance | 5 |
| Clinical Utility | 5 |
| Time-to-Event | 8 |
| Effect Estimate | 7 |
| Generalizability | 1 |
| Data Geometry | 6 |
| Matrix Pattern | 16 |
| Model Explanation | 6 |
| Model Audit | 1 |

## 当前默认风格

- `style_profile_id`: `paper_neutral_clinical_v1`
- `journal_palette_ref`: `nature_informed_clinical_publication_v1`
- canonical renderer inventory: `r_ggplot2=55`, `python=0`, `n/a=0`
- full R/ggplot2 evidence gallery cards: `55`
- current Python evidence templates: `0`
- Python design / flow shells in ggplot2 evidence Gallery: `0`
- rendered evidence gallery cards: `55`
- visual canonical representative families: `18`
- migration inventory templates are retained in `gallery_manifest.json`; duplicate / legacy aliases are mapped to canonical families but current R/ggplot2 evidence aliases are still shown in this full evidence Gallery.
- core medical figure families: sourced from `contracts/medical-figure-family-catalog/`
- figure family policy: `core_catalog_bound_metadata_only`
- AI adaptation policy: `canonical_family_baseline_then_paper_local_adaptation`
- upstream nature-skills fresh HEAD checked on `2026-06-19`: `54eadc65d1c0535e90d792a87ab718d848ccbb7a`

## 风格口径

MAS 默认不是 Nature 官方模板复刻，也不是 Lancet 专用模板。当前内置默认是 `nature_informed_clinical_publication_v1`：白底、左下轴线、小字号、细轴线、弱网格、统一 clinical palette、sequential/diverging heatmap palette 和横向 colorbar。数据分析产生的 evidence figure 以 R/ggplot2 为第一公民；未证明优于 R/ggplot2 的 Python evidence 模板不进入当前 pack、隐藏库存或 Gallery 对比图。设计、流程和 graphical abstract shell 可以用 SVG、Python composition 或 imagegen-assisted art direction，但不承担统计证据权威，也不混入这份 ggplot2 evidence Gallery。当前 catalog 只保留现有模板的 canonical family 与 alias 映射，不维护旧 Python evidence ID 清单。Gallery manifest 的医学图型 ontology 来自 `contracts/medical-figure-family-catalog/`；PDF Gallery 展示全量 current R/ggplot2 evidence templates，canonical representative families 只用于索引、推荐面和 alias 映射。
