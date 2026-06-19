from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class StarterRecipe:
    recipe_id: str
    category_id: str
    family_id: str
    title: str
    purpose: str
    starter_kind: str
    panel_grammar: str
    required_data_roles: tuple[str, ...]
    recommended_template_seed_ids: tuple[str, ...]
    style_tokens: tuple[str, ...]
    palette_tokens: tuple[str, ...]
    qa_gate_ids: tuple[str, ...]
    policy_id: str
    payload: dict[str, Any]


def parse_starter_recipes(
    path: Path,
    *,
    read_json_object: Callable[[Path], dict[str, Any]],
    expect_str: Callable[[dict[str, Any], str], str],
    expect_str_tuple: Callable[[dict[str, Any], str], tuple[str, ...]],
    expect_object_list: Callable[[dict[str, Any], str], tuple[dict[str, Any], ...]],
) -> tuple[StarterRecipe, ...]:
    payload = read_json_object(path)
    category_id = expect_str(payload, "category_id")
    recipes: list[StarterRecipe] = []
    seen: set[str] = set()
    for index, item in enumerate(expect_object_list(payload, "recipes")):
        context = f"{path.name}.recipes[{index}]"
        recipe_id = expect_str(item, "recipe_id")
        if recipe_id in seen:
            raise ValueError(f"duplicate starter recipe `{recipe_id}` in {path.name}")
        seen.add(recipe_id)
        recipe_category = expect_str(item, "category_id")
        if recipe_category != category_id:
            raise ValueError(f"{context}.category_id must equal `{category_id}`")
        recipes.append(
            StarterRecipe(
                recipe_id=recipe_id,
                category_id=recipe_category,
                family_id=expect_str(item, "family_id"),
                title=expect_str(item, "title"),
                purpose=expect_str(item, "purpose"),
                starter_kind=expect_str(item, "starter_kind"),
                panel_grammar=expect_str(item, "panel_grammar"),
                required_data_roles=expect_str_tuple(item, "required_data_roles"),
                recommended_template_seed_ids=expect_str_tuple(item, "recommended_template_seed_ids"),
                style_tokens=expect_str_tuple(item, "style_tokens"),
                palette_tokens=expect_str_tuple(item, "palette_tokens"),
                qa_gate_ids=expect_str_tuple(item, "qa_gate_ids"),
                policy_id=expect_str(item, "policy_id"),
                payload=item,
            )
        )
    if not recipes:
        raise ValueError(f"{path.name}.recipes must be non-empty")
    return tuple(recipes)


def validate_starter_recipe_refs(
    recipes: tuple[StarterRecipe, ...],
    *,
    style_profile_ids: set[str],
    palette_token_ids: set[str],
    qa_gate_ids: set[str],
    policy_id: str,
) -> dict[str, StarterRecipe]:
    recipes_by_id: dict[str, StarterRecipe] = {}
    for recipe in recipes:
        if recipe.recipe_id in recipes_by_id:
            raise ValueError(f"duplicate starter recipe `{recipe.recipe_id}`")
        unknown_styles = set(recipe.style_tokens) - style_profile_ids
        if unknown_styles:
            raise ValueError(f"{recipe.recipe_id} references unknown style tokens {sorted(unknown_styles)!r}")
        unknown_palettes = set(recipe.palette_tokens) - palette_token_ids
        if unknown_palettes:
            raise ValueError(f"{recipe.recipe_id} references unknown palette tokens {sorted(unknown_palettes)!r}")
        unknown_gates = set(recipe.qa_gate_ids) - qa_gate_ids
        if unknown_gates:
            raise ValueError(f"{recipe.recipe_id} references unknown QA gates {sorted(unknown_gates)!r}")
        if recipe.policy_id != policy_id:
            raise ValueError(f"{recipe.recipe_id}.policy_id must equal `{policy_id}`")
        recipes_by_id[recipe.recipe_id] = recipe
    return recipes_by_id
