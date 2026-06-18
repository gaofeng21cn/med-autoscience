# MAS R/ggplot2 模板风格参考

Owner: `MedAutoScience`
Purpose: `human_readable_reference_for_builtin_mas_r_ggplot2_medical_display_style`
State: `active_support`
Machine boundary: 人读示例文档。机器真相继续归 display-pack template descriptor、renderer source、`paper/publication_style_profile.json`、layout sidecar、display lock、publication manifest、tests 和真实论文 artifacts。

Codex 内置 Markdown 浏览器对相对图片不稳定；全量图请直接打开 HTML gallery，或使用同目录生成的 PDF：

- [MAS R/ggplot2 模板全量 Gallery](./ggplot2_template_gallery.html)
- [MAS R/ggplot2 模板全量 Gallery PDF](./ggplot2_template_gallery.pdf)

## 结论

- 当前 core pack 模板库存共 `98` 个：`r_ggplot2` `55` 个，`python` `36` 个，table/非图形 `n/a` `7` 个。
- HTML gallery 已全量渲染所有 `r_ggplot2` 模板，并按医学展示大类分组展示具体图类型。
- 默认风格不是 Nature 专用模板；当前 `journal_palette_ref` 是 `large_journal_safe_lancet_like_v1`，整体是中性临床论文风格。
- MAS 现在是 `R/ggplot2-first`，不是 `R/ggplot2-only`；命中 Python 模板时仍可能输出 Python 风格图。

## 分类覆盖

| Category | Rendered templates |
| --- | ---: |
| Prediction Performance | 3 |
| Clinical Utility | 5 |
| Time-to-Event | 10 |
| Effect Estimate | 7 |
| Generalizability | 1 |
| Data Geometry | 7 |
| Matrix Pattern | 15 |
| Model Explanation | 6 |
| Model Audit | 1 |

## 默认风格 Token

- `style_profile_id`: `paper_neutral_clinical_v1`
- `journal_palette_ref`: `large_journal_safe_lancet_like_v1`
- typography: `font_family=sans`, `base_size=11.0`, `title_size=12.5`
- primary: `#5F766B`; secondary: `#B9AD9C`; text: `#13293D`; grid: `#E6EDF2`
