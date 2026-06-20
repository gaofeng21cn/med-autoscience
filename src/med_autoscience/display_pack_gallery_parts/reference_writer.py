from __future__ import annotations

from collections import Counter
from pathlib import Path

from med_autoscience import publication_display_contract as display_contract
from med_autoscience.display_pack_gallery_catalog import (
    TemplateRecord,
    gallery_display_records,
    visual_gallery_records,
)
from med_autoscience.display_pack_gallery_parts.assets import RenderedAsset
from med_autoscience.display_pack_gallery_parts.taxonomy import CATEGORY_ORDER
from med_autoscience.display_pack_gallery_reference import build_gallery_reference_markdown
from med_autoscience.display_pack_gallery_parts import paths
from med_autoscience.display_pack_gallery_parts.composition_gallery import (
    build_composition_gallery_surface,
)
from med_autoscience.display_pack_agent_parts.composition_recipe_projection import (
    composition_recipe_discovery_payload,
)

def _write_reference(
    records: list[TemplateRecord],
    rendered: dict[str, RenderedAsset],
    baseline_rendered: dict[str, RenderedAsset],
    *,
    reference_path: Path,
) -> None:
    default_style = display_contract._DEFAULT_STYLE_PROFILE_PAYLOAD
    visible_records = gallery_display_records(records)
    canonical_visual_records = visual_gallery_records(records)
    categories = Counter(record.canonical_family_category for record in visible_records)
    rendered_count = sum(1 for record in visible_records if rendered[record.template_id].status == "rendered")
    r_evidence_count = sum(
        1
        for record in visible_records
        if record.kind == "evidence_figure" and record.renderer_family == "r_ggplot2"
    )
    illustration_shell_count = sum(1 for record in visible_records if record.kind == "illustration_shell")
    category_lines = "\n".join(
        f"| {category} | {categories[category]} |"
        for category in CATEGORY_ORDER
        if category in categories
    )
    composition_surface = composition_recipe_discovery_payload(include_recipes=True)
    composition_gallery = build_composition_gallery_surface(composition_surface, records)
    composition_recipe_lines = "\n".join(
        f"| `{item['recipe_id']}` | {item['hero_panel_role']} | "
        f"{len(item['supporting_panel_roles'])} | {len(item['preview_template_ids'])} |"
        for item in composition_gallery["recipes"]
    )
    reference_path.parent.mkdir(parents=True, exist_ok=True)
    reference_path.write_text(
        build_gallery_reference_markdown(
            category_lines=category_lines,
            default_style=default_style,
            renderer_inventory=Counter(record.renderer_family for record in visible_records),
            rendered_count=rendered_count,
            canonical_gallery_family_count=len(canonical_visual_records),
            nature_skills_head=paths.NATURE_SKILLS_HEAD,
            r_evidence_count=r_evidence_count,
            illustration_shell_count=illustration_shell_count,
            composition_recipe_count=int(composition_surface["composition_recipe_count"]),
            composition_recipe_lines=composition_recipe_lines,
        ),
        encoding="utf-8",
    )
