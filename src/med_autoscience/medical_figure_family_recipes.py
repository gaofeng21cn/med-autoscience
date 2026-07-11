from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from med_autoscience.medical_figure_family_catalog import FigureFamily, FigureFamilyCategory


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


def derive_starter_recipes(
    overrides: tuple[dict[str, Any], ...],
    *,
    family: FigureFamily,
    policy_id: str,
    context: str,
    expect_str: Callable[..., str],
    expect_str_tuple: Callable[..., tuple[str, ...]],
) -> tuple[StarterRecipe, ...]:
    allowed_keys = {
        "recipe_id",
        "starter_kind",
        "panel_grammar",
        "title",
        "purpose",
        "recommended_template_seed_ids",
    }
    recipes: list[StarterRecipe] = []
    for index, override in enumerate(overrides):
        override_context = f"{context}[{index}]"
        unknown_keys = set(override) - allowed_keys
        if unknown_keys:
            raise ValueError(
                f"{override_context} has unsupported starter recipe overrides {sorted(unknown_keys)!r}"
            )
        recipe_id = expect_str(override, "recipe_id", context=override_context)
        title = (
            expect_str(override, "title", context=override_context)
            if "title" in override
            else f"{family.title} starter"
        )
        purpose = (
            expect_str(override, "purpose", context=override_context)
            if "purpose" in override
            else f"Create a first renderable, auditable lower-bound figure for {family.intent}"
        )
        template_seed_ids = (
            expect_str_tuple(override, "recommended_template_seed_ids", context=override_context)
            if "recommended_template_seed_ids" in override
            else family.template_seed_ids
        )
        starter_kind = expect_str(override, "starter_kind", context=override_context)
        panel_grammar = expect_str(override, "panel_grammar", context=override_context)
        payload = {
            "recipe_id": recipe_id,
            "category_id": family.category_id,
            "family_id": family.family_id,
            "title": title,
            "purpose": purpose,
            "starter_kind": starter_kind,
            "panel_grammar": panel_grammar,
            "required_data_roles": list(family.data_roles),
            "recommended_template_seed_ids": list(template_seed_ids),
            "style_tokens": list(family.style_tokens),
            "palette_tokens": list(family.palette_tokens),
            "qa_gate_ids": list(family.qa_gate_ids),
            "policy_id": policy_id,
        }
        recipes.append(
            StarterRecipe(
                recipe_id=recipe_id,
                category_id=family.category_id,
                family_id=family.family_id,
                title=title,
                purpose=purpose,
                starter_kind=starter_kind,
                panel_grammar=panel_grammar,
                required_data_roles=family.data_roles,
                recommended_template_seed_ids=template_seed_ids,
                style_tokens=family.style_tokens,
                palette_tokens=family.palette_tokens,
                qa_gate_ids=family.qa_gate_ids,
                policy_id=policy_id,
                payload=payload,
            )
        )
    return tuple(recipes)


def validate_starter_recipes(
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


def validate_family_recipe_refs(
    categories: tuple[FigureFamilyCategory, ...],
    *,
    style_profile_ids: set[str],
    palette_token_ids: set[str],
    qa_gate_ids: set[str],
    external_source_ids: set[str],
    starter_recipes_by_id: dict[str, StarterRecipe],
) -> dict[str, FigureFamily]:
    families_by_id: dict[str, FigureFamily] = {}
    for category in categories:
        for family in category.families:
            if family.family_id in families_by_id:
                raise ValueError(f"duplicate medical figure family `{family.family_id}`")
            unknown_styles = set(family.style_tokens) - style_profile_ids
            if unknown_styles:
                raise ValueError(f"{family.family_id} references unknown style tokens {sorted(unknown_styles)!r}")
            unknown_palettes = set(family.palette_tokens) - palette_token_ids
            if unknown_palettes:
                raise ValueError(f"{family.family_id} references unknown palette tokens {sorted(unknown_palettes)!r}")
            unknown_gates = set(family.qa_gate_ids) - qa_gate_ids
            if unknown_gates:
                raise ValueError(f"{family.family_id} references unknown QA gates {sorted(unknown_gates)!r}")
            unknown_sources = set(family.external_refs) - external_source_ids
            if unknown_sources:
                raise ValueError(f"{family.family_id} references unknown external sources {sorted(unknown_sources)!r}")
            unknown_recipes = set(family.starter_recipe_refs) - set(starter_recipes_by_id)
            if unknown_recipes:
                raise ValueError(
                    f"{family.family_id} references unknown starter recipes {sorted(unknown_recipes)!r}"
                )
            for recipe_id in family.starter_recipe_refs:
                recipe = starter_recipes_by_id[recipe_id]
                if recipe.family_id != family.family_id:
                    raise ValueError(f"starter recipe `{recipe_id}` family_id must equal `{family.family_id}`")
                if recipe.category_id != family.category_id:
                    raise ValueError(f"starter recipe `{recipe_id}` category_id must equal `{family.category_id}`")
            families_by_id[family.family_id] = family
    return families_by_id
