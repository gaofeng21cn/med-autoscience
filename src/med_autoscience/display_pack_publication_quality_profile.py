from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from med_autoscience.medical_figure_family_catalog import load_medical_figure_family_catalog


def _dedupe(items: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return tuple(normalized)


def publication_quality_profile_for_medical_families(
    medical_family_ids: Sequence[str],
) -> dict[str, Any]:
    family_ids = _dedupe(medical_family_ids)
    if not family_ids:
        raise ValueError("medical_family_ids must contain at least one family id")
    catalog = load_medical_figure_family_catalog()
    families = [catalog.family(family_id) for family_id in family_ids]
    starter_recipe_ids = _dedupe(
        [
            recipe_id
            for family in families
            for recipe_id in family.starter_recipe_refs
        ]
    )
    recipes = [catalog.starter_recipes_by_id[recipe_id] for recipe_id in starter_recipe_ids]
    return {
        "medical_family_ids": list(family_ids),
        "primary_medical_family_id": family_ids[0],
        "medical_category_ids": list(_dedupe([family.category_id for family in families])),
        "starter_recipe_ids": list(starter_recipe_ids),
        "starter_recipe_titles": [recipe.title for recipe in recipes],
        "starter_recipe_panel_grammars": list(_dedupe([recipe.panel_grammar for recipe in recipes])),
        "style_profile_ids": list(
            _dedupe(
                [
                    *[style for family in families for style in family.style_tokens],
                    *[style for recipe in recipes for style in recipe.style_tokens],
                ]
            )
        ),
        "palette_token_ids": list(
            _dedupe(
                [
                    *[palette for family in families for palette in family.palette_tokens],
                    *[palette for recipe in recipes for palette in recipe.palette_tokens],
                ]
            )
        ),
        "qa_gate_ids": list(
            _dedupe(
                [
                    *[gate for family in families for gate in family.qa_gate_ids],
                    *[gate for recipe in recipes for gate in recipe.qa_gate_ids],
                    "figure_contract_before_render",
                    "backend_exclusive_export_receipt",
                    "publication_polish_visual_audit",
                    "paper_use_polish_lifecycle",
                ]
            )
        ),
        "required_data_roles": list(
            _dedupe(
                [
                    *[role for family in families for role in family.data_roles],
                    *[role for recipe in recipes for role in recipe.required_data_roles],
                ]
            )
        ),
        "ai_adaptation_notes": [
            family.ai_adaptation_notes
            for family in families
            if family.ai_adaptation_notes
        ],
        "policy_id": catalog.starter_recipe_policy["policy_id"],
        "starter_templates_are_floor_not_ceiling": bool(
            catalog.starter_recipe_policy["starter_recipe_is_floor_not_ceiling"]
        ),
        "ai_may_change": list(catalog.starter_recipe_policy["default_ai_may_change"]),
        "ai_must_preserve": list(catalog.starter_recipe_policy["default_ai_must_preserve"]),
        "required_request_refs": list(catalog.starter_recipe_policy["required_request_refs"]),
        "quality_gate_route": list(catalog.starter_recipe_policy["quality_gate_route"]),
    }


__all__ = ["publication_quality_profile_for_medical_families"]
