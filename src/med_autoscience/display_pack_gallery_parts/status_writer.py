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


def _design_rows(manifest: dict[str, Any]) -> str:
    inventory = manifest.get("design_gallery_templates")
    if not isinstance(inventory, list) or not inventory:
        return "| none | none | none | none |"
    return "\n".join(
        f"| `{item.get('template_id', '')}` | {item.get('display_name', '')} | "
        f"{item.get('renderer_family', '')} | {item.get('render_status', '')} |"
        for item in inventory
        if isinstance(item, dict)
    )


def _analysis_responsibility_rows(manifest: dict[str, Any]) -> str:
    counts = manifest.get("analysis_responsibility_counts")
    if not isinstance(counts, dict) or not counts:
        return "| none | 0 |"
    return "\n".join(f"| `{key}` | {value} |" for key, value in sorted(counts.items()))


def _join_counted(values: object) -> str:
    if not isinstance(values, list):
        return "0"
    return str(len([item for item in values if isinstance(item, str) and item]))


def build_gallery_status_markdown(manifest: dict[str, Any]) -> str:
    quality = manifest.get("quality_audit") if isinstance(manifest.get("quality_audit"), dict) else {}
    profile_coverage = (
        manifest.get("publication_quality_profile_coverage")
        if isinstance(manifest.get("publication_quality_profile_coverage"), dict)
        else {}
    )
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
    workflow_policy = (
        manifest.get("figure_workflow_policy")
        if isinstance(manifest.get("figure_workflow_policy"), dict)
        else {}
    )
    composition_surface = (
        manifest.get("composition_recipe_surface")
        if isinstance(manifest.get("composition_recipe_surface"), dict)
        else {}
    )
    composition_gallery = (
        manifest.get("composition_gallery_surface")
        if isinstance(manifest.get("composition_gallery_surface"), dict)
        else {}
    )
    composition_policy = (
        composition_surface.get("policy")
        if isinstance(composition_surface.get("policy"), dict)
        else {}
    )
    required_before_paper = "\n".join(
        f"- `{item}`"
        for item in policy.get("required_before_paper_use", [])
        if isinstance(item, str)
    ) or "- none"
    required_workflow_before_paper = "\n".join(
        f"- `{item}`"
        for item in workflow_policy.get("paper_use_acceptance", [])
        if isinstance(item, str)
    ) or "- none"
    composition_rows = "\n".join(
        f"| `{item.get('recipe_id', '')}` | {item.get('title', '')} | "
        f"{item.get('hero_panel_role', '')} | {_join_counted(item.get('supporting_panel_roles'))} | "
        f"{_join_counted(item.get('evidence_primitive_family_ids'))} | {item.get('default_layout', '')} |"
        for item in composition_gallery.get("recipes", [])
        if isinstance(item, dict)
    ) or "| none | none | none | 0 | 0 | none |"
    return f"""# MAS 医学论文配图 Gallery 生成状态

Owner: `MedAutoScience`
Purpose: `generated_display_pack_gallery_status`
State: `generated_active_support`
Machine boundary: 本文由 `scripts/build-display-pack-gallery.py --publish-docs` 从 Gallery manifest / canonical catalog 生成。机器真相继续归 template descriptor、canonical catalog、Gallery manifest、layout sidecar、renderer source、tests、真实论文 artifact、visual-audit receipt、owner receipt 和 publication gate。

## 当前数量口径

| 指标 | 数量 |
| --- | ---: |
| Gallery evidence figures | {_count(manifest, "evidence_gallery_template_count")} |
| Gallery design / flow figures | {_count(manifest, "design_gallery_template_count")} |
| Gallery visual templates | {_count(manifest, "visual_gallery_template_count")} |
| Current canonical templates | {_count(manifest, "canonical_template_count")} |
| Current non-visual canonical inventory | {_count(manifest, "non_visual_canonical_template_count")} |
| Retired alias / duplicate ids | {_count(manifest, "retired_alias_template_count")} |
| Migration index entries | {_count(manifest, "migration_inventory_template_count") + _count(manifest, "retired_alias_template_count")} |
| Current Python evidence templates | {renderer_completion.get("python_evidence_retained_count", 0)} |
| Page-level composition recipes | {composition_surface.get("composition_recipe_count", 0)} |
| Composition storyboard gallery pages | {composition_gallery.get("composition_recipe_count", 0)} |

`Gallery evidence figures` 是 PDF 画册中展示的 R/ggplot2 数据证据图数量。`Gallery design / flow figures` 是 PDF/HTML 中真实渲染的 cohort flow、graphical abstract 等非数据设计图起点。`Composition storyboard gallery pages` 是 PDF/HTML 前段展示的图页级方案数量。`Page-level composition recipes` 是组织多个数据证据面板的图页方案，不是更多单图模板。`Current canonical templates` 是当前可推荐 canonical surface。`Retired alias / duplicate ids` 只用于显式旧 ID 迁移，不是 current template，也不是画册卡片。

## 渲染器与质量口径

- gallery default surface: `{manifest.get("template_surface_policy", {}).get("gallery_default_surface", "")}`
- evidence gallery default surface: `{manifest.get("template_surface_policy", {}).get("evidence_gallery_default_surface", "")}`
- design gallery default surface: `{manifest.get("template_surface_policy", {}).get("design_gallery_default_surface", "")}`
- evidence figures default to R/ggplot2: `{str(manifest.get("template_surface_policy", {}).get("evidence_figures_default_to_r_ggplot2", False)).lower()}`
- Python illustration shells visible as design cards: `{str(manifest.get("template_surface_policy", {}).get("python_illustration_shells_are_visible_design_gallery_cards", False)).lower()}`
- Python evidence retained without advantage proof: `{str(not manifest.get("template_surface_policy", {}).get("python_evidence_templates_not_retained_without_advantage_proof", True)).lower()}`
- style profile: `{manifest.get("style_profile_id", "")}`
- journal palette: `{manifest.get("journal_palette_ref", "")}`
- quality overall status: `{quality.get("overall_status", "")}`
- publication-ready claim authorized: `{str(quality.get("publication_ready_claim_authorized", False)).lower()}`
- blocked templates after current render: `{quality.get("blocked_template_count", 0)}`
- lower-bound review required: `{quality.get("lower_bound_review_required_count", 0)}`
- gallery lower-bound admission: `{quality.get("gallery_lower_bound_admission_status", "")}`
- publication quality profile coverage: `{profile_coverage.get("complete_profile_template_count", 0)}/{profile_coverage.get("current_template_count", 0)}` ({profile_coverage.get("complete_profile_percent", 0)}%)
- publication polish policy: `{policy.get("policy_id", "")}`
- figure workflow policy: `{workflow_policy.get("policy_id", "")}`
- composition recipe policy: `{composition_policy.get("policy_id", "")}`

## 数据处理责任

| Responsibility | Current templates |
| --- | ---: |
{_analysis_responsibility_rows(manifest)}

- raw analysis requests fail closed unless the selected template declares `computed_in_template`
- `validated_summary_required` templates render upstream analysis outputs; they do not fit models, recompute curves, run differential testing, infer SHAP values, or call variants

## Paper-use 前置检查

{required_before_paper}

## 图件工作流前置检查

{required_workflow_before_paper}

## 页面级图页方案

| Recipe | Title | Hero panel | Supporting | Primitive families | Default layout |
| --- | --- | --- | ---: | ---: | --- |
{composition_rows}

## 非数据设计/流程图 Gallery

| Template | Display name | Renderer | Render status |
| --- | --- | --- | --- |
{_design_rows(manifest)}

## 画册分类

| Category | Gallery evidence figures |
| --- | ---: |
{_category_rows(manifest)}

## 表格/非图像库存

| Template | Category | Kind |
| --- | --- | --- |
{_non_visual_rows(manifest)}
"""
