from __future__ import annotations

from typing import Any


def build_gallery_reference_markdown(
    *,
    category_lines: str,
    default_style: dict[str, Any],
    renderer_inventory: dict[str, int],
    rendered_count: int,
    canonical_gallery_family_count: int,
    nature_skills_head: str,
    r_evidence_count: int,
    illustration_shell_count: int,
) -> str:
    return f"""# MAS Display Pack Gallery

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
{category_lines}

## 当前默认风格

- `style_profile_id`: `{default_style["style_profile_id"]}`
- `journal_palette_ref`: `{default_style["journal_palette_ref"]}`
- canonical renderer inventory: `r_ggplot2={renderer_inventory.get("r_ggplot2", 0)}`, `python={renderer_inventory.get("python", 0)}`, `n/a={renderer_inventory.get("n/a", 0)}`
- default R/ggplot2 evidence templates: `{r_evidence_count}`
- current Python evidence templates: `0`
- default Python design / flow shells: `{illustration_shell_count}`
- canonical rendered image templates: `{rendered_count}`
- visual canonical gallery families: `{canonical_gallery_family_count}`
- migration inventory templates are retained in `gallery_manifest.json`; duplicate / legacy aliases are not shown as separate Gallery cards.
- core medical figure families: sourced from `contracts/medical-figure-family-catalog/`
- figure family policy: `core_catalog_bound_metadata_only`
- AI adaptation policy: `canonical_family_baseline_then_paper_local_adaptation`
- upstream nature-skills fresh HEAD checked on `2026-06-19`: `{nature_skills_head}`

## 风格口径

MAS 默认不是 Nature 官方模板复刻，也不是 Lancet 专用模板。当前内置默认是 `nature_informed_clinical_publication_v1`：白底、左下轴线、小字号、细轴线、弱网格、统一 clinical palette、sequential/diverging heatmap palette 和横向 colorbar。数据分析产生的 evidence figure 以 R/ggplot2 为第一公民；未证明优于 R/ggplot2 的 Python evidence 模板已从当前 pack 退役，不作为隐藏库存或 Gallery 对比图保留。设计、流程和 graphical abstract shell 可以用 SVG、Python composition 或 imagegen-assisted art direction，但不承担统计证据权威。旧模板 ID 只在 canonical catalog 中作为现有 R 模板的 alias 或历史退役记录存在，不作为用户默认候选。Gallery manifest 的医学图型 ontology 来自 `contracts/medical-figure-family-catalog/`，当前模板展示面由 pack-local canonical template catalog 提供代表模板和 aliases。
"""
