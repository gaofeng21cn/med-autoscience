from __future__ import annotations

from typing import Any

from med_autoscience.display_pack_agent_parts.composition_recipe_route import composition_recipe_payload
from med_autoscience.medical_figure_family_catalog import load_medical_figure_family_catalog


def composition_recipe_discovery_payload(*, include_recipes: bool = False) -> dict[str, Any]:
    catalog = load_medical_figure_family_catalog()
    payload: dict[str, Any] = {
        "policy": dict(catalog.composition_recipe_policy),
        "composition_recipe_count": len(catalog.composition_recipes),
        "recipe_ids": [recipe.recipe_id for recipe in catalog.composition_recipes],
        "quality_floor_only": True,
        "blocks_default_evidence_progress": False,
        "manual_gallery_browsing_required": False,
        "data_evidence_programmatic_first": True,
        "design_shells_allow_svg_or_imagegen_art_direction": True,
    }
    if include_recipes:
        payload["recipes"] = [
            composition_recipe_payload(recipe)
            for recipe in catalog.composition_recipes
        ]
    return payload
