from __future__ import annotations

from typing import Any


def _count(manifest: dict[str, Any], key: str) -> int:
    value = manifest.get(key, 0)
    return value if isinstance(value, int) else 0


def _category_rows(manifest: dict[str, Any]) -> str:
    categories = manifest.get("categories")
    if not isinstance(categories, dict) or not categories:
        return "| none | 0 |"
    return "\n".join(f"| {category} | {count} |" for category, count in sorted(categories.items()))


def _non_visual_rows(manifest: dict[str, Any]) -> str:
    inventory = manifest.get("non_visual_inventory")
    if not isinstance(inventory, list) or not inventory:
        return "| none | none | none |"
    return "\n".join(
        f"| `{item.get('template_id', '')}` | {item.get('canonical_family_category', '')} | "
        f"{item.get('kind', '')} |"
        for item in inventory
        if isinstance(item, dict)
    )


def build_gallery_status_markdown(manifest: dict[str, Any]) -> str:
    quality = manifest.get("quality_audit") if isinstance(manifest.get("quality_audit"), dict) else {}
    renderer_completion = (
        manifest.get("renderer_policy_completion")
        if isinstance(manifest.get("renderer_policy_completion"), dict)
        else {}
    )
    policy = (
        manifest.get("publication_polish_policy")
        if isinstance(manifest.get("publication_polish_policy"), dict)
        else {}
    )
    required_before_paper = "\n".join(
        f"- `{item}`"
        for item in policy.get("required_before_paper_use", [])
        if isinstance(item, str)
    ) or "- none"
    return f"""# MAS Display Pack Gallery Status

Owner: `MedAutoScience`
Purpose: `generated_display_pack_gallery_status`
State: `generated_active_support`
Machine boundary: 本文由 `scripts/build-display-pack-gallery.py --publish-docs` 从 Gallery manifest / canonical catalog 生成。机器真相继续归 template descriptor、canonical catalog、Gallery manifest、layout sidecar、renderer source、tests、真实论文 artifact、visual-audit receipt、owner receipt 和 publication gate。

## 当前数量口径

| Metric | Count |
| --- | ---: |
| Gallery evidence figures | {_count(manifest, "evidence_gallery_template_count")} |
| Current canonical templates | {_count(manifest, "canonical_template_count")} |
| Current non-visual canonical inventory | {_count(manifest, "non_visual_canonical_template_count")} |
| Retired alias / duplicate ids | {_count(manifest, "retired_alias_template_count")} |
| Migration index entries | {_count(manifest, "migration_inventory_template_count") + _count(manifest, "retired_alias_template_count")} |
| Current Python evidence templates | {renderer_completion.get("python_evidence_retained_count", 0)} |

`Gallery evidence figures` 是 PDF Gallery 中展示的 R/ggplot2 数据证据图数量。`Current canonical templates` 是当前可推荐 canonical surface，包含不进入 ggplot2 evidence Gallery 的非视觉库存。`Retired alias / duplicate ids` 只用于显式旧 ID 迁移，不是 current template，也不是 Gallery 卡片。

## Renderer 与质量口径

- gallery default surface: `{manifest.get("template_surface_policy", {}).get("gallery_default_surface", "")}`
- evidence figures default to R/ggplot2: `{str(manifest.get("template_surface_policy", {}).get("evidence_figures_default_to_r_ggplot2", False)).lower()}`
- Python evidence retained without advantage proof: `{str(not manifest.get("template_surface_policy", {}).get("python_evidence_templates_not_retained_without_advantage_proof", True)).lower()}`
- style profile: `{manifest.get("style_profile_id", "")}`
- journal palette: `{manifest.get("journal_palette_ref", "")}`
- quality overall status: `{quality.get("overall_status", "")}`
- publication-ready claim authorized: `{str(quality.get("publication_ready_claim_authorized", False)).lower()}`
- blocked templates after current render: `{quality.get("blocked_template_count", 0)}`
- lower-bound review required: `{quality.get("lower_bound_review_required_count", 0)}`
- publication polish policy: `{policy.get("policy_id", "")}`

## Paper-use 前置检查

{required_before_paper}

## Gallery 分类

| Category | Gallery evidence figures |
| --- | ---: |
{_category_rows(manifest)}

## 非视觉库存

| Template | Category | Kind |
| --- | --- | --- |
{_non_visual_rows(manifest)}
"""
