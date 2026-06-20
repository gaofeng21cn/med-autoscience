from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class CompositionRecipe:
    recipe_id: str
    title: str
    intent: str
    claim_triggers: tuple[str, ...]
    hero_panel_role: str
    supporting_panel_roles: tuple[str, ...]
    evidence_primitive_family_ids: tuple[str, ...]
    recommended_starter_recipe_ids: tuple[str, ...]
    design_shell_allowed: bool
    programmatic_evidence_required: bool
    default_layout: str
    guide_strategy: str
    label_strategy: str
    style_tokens: tuple[str, ...]
    palette_tokens: tuple[str, ...]
    qa_gate_ids: tuple[str, ...]
    learned_patterns: tuple[str, ...]
    ai_may_change: tuple[str, ...]
    ai_must_preserve: tuple[str, ...]
    forbidden_authority: tuple[str, ...]
    payload: dict[str, Any]


def parse_composition_recipes(
    path: Path,
    *,
    read_json_object: Callable[[Path], dict[str, Any]],
    expect_str: Callable[[dict[str, Any], str], str],
    expect_bool: Callable[[dict[str, Any], str], bool],
    expect_str_tuple: Callable[[dict[str, Any], str], tuple[str, ...]],
    expect_object_list: Callable[[dict[str, Any], str], tuple[dict[str, Any], ...]],
) -> tuple[CompositionRecipe, ...]:
    payload = read_json_object(path)
    recipes: list[CompositionRecipe] = []
    seen: set[str] = set()
    for index, item in enumerate(expect_object_list(payload, "recipes")):
        recipe_id = expect_str(item, "recipe_id")
        if recipe_id in seen:
            raise ValueError(f"duplicate composition recipe `{recipe_id}`")
        seen.add(recipe_id)
        recipes.append(
            CompositionRecipe(
                recipe_id=recipe_id,
                title=expect_str(item, "title"),
                intent=expect_str(item, "intent"),
                claim_triggers=expect_str_tuple(item, "claim_triggers"),
                hero_panel_role=expect_str(item, "hero_panel_role"),
                supporting_panel_roles=expect_str_tuple(item, "supporting_panel_roles"),
                evidence_primitive_family_ids=expect_str_tuple(item, "evidence_primitive_family_ids"),
                recommended_starter_recipe_ids=expect_str_tuple(item, "recommended_starter_recipe_ids"),
                design_shell_allowed=expect_bool(item, "design_shell_allowed"),
                programmatic_evidence_required=expect_bool(item, "programmatic_evidence_required"),
                default_layout=expect_str(item, "default_layout"),
                guide_strategy=expect_str(item, "guide_strategy"),
                label_strategy=expect_str(item, "label_strategy"),
                style_tokens=expect_str_tuple(item, "style_tokens"),
                palette_tokens=expect_str_tuple(item, "palette_tokens"),
                qa_gate_ids=expect_str_tuple(item, "qa_gate_ids"),
                learned_patterns=expect_str_tuple(item, "learned_patterns"),
                ai_may_change=expect_str_tuple(item, "ai_may_change"),
                ai_must_preserve=expect_str_tuple(item, "ai_must_preserve"),
                forbidden_authority=expect_str_tuple(item, "forbidden_authority"),
                payload=item,
            )
        )
    if not recipes:
        raise ValueError(f"{path.name}.recipes must be non-empty")
    return tuple(recipes)


def validate_composition_recipe_refs(
    recipes: tuple[CompositionRecipe, ...],
    *,
    family_ids: set[str],
    starter_recipe_ids: set[str],
    style_profile_ids: set[str],
    palette_token_ids: set[str],
    qa_gate_ids: set[str],
) -> dict[str, CompositionRecipe]:
    recipes_by_id: dict[str, CompositionRecipe] = {}
    for recipe in recipes:
        if recipe.recipe_id in recipes_by_id:
            raise ValueError(f"duplicate composition recipe `{recipe.recipe_id}`")
        unknown_families = set(recipe.evidence_primitive_family_ids) - family_ids
        if unknown_families:
            raise ValueError(
                f"{recipe.recipe_id} references unknown figure families {sorted(unknown_families)!r}"
            )
        unknown_recipes = set(recipe.recommended_starter_recipe_ids) - starter_recipe_ids
        if unknown_recipes:
            raise ValueError(
                f"{recipe.recipe_id} references unknown starter recipes {sorted(unknown_recipes)!r}"
            )
        unknown_styles = set(recipe.style_tokens) - style_profile_ids
        if unknown_styles:
            raise ValueError(f"{recipe.recipe_id} references unknown style tokens {sorted(unknown_styles)!r}")
        unknown_palettes = set(recipe.palette_tokens) - palette_token_ids
        if unknown_palettes:
            raise ValueError(f"{recipe.recipe_id} references unknown palette tokens {sorted(unknown_palettes)!r}")
        unknown_gates = set(recipe.qa_gate_ids) - qa_gate_ids
        if unknown_gates:
            raise ValueError(f"{recipe.recipe_id} references unknown QA gates {sorted(unknown_gates)!r}")
        recipes_by_id[recipe.recipe_id] = recipe
    return recipes_by_id
