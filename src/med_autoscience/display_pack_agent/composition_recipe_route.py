from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from med_autoscience.medical_figure_composition_recipes import CompositionRecipe
from med_autoscience.medical_figure_family_catalog import MedicalFigureFamilyCatalog


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _text(value: object) -> str:
    return str(value or "").strip()


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(value.casefold()))


def _route_text(request: Mapping[str, Any]) -> str:
    return " ".join(
        _text(request.get(key))
        for key in (
            "query",
            "claim_role",
            "core_conclusion",
            "audit_family",
            "medical_figure_family_id",
            "medical_figure_family_title",
            "medical_figure_category_id",
            "figure_kind",
            "template_id",
        )
    )


def _trigger_score(route_text: str, trigger: str) -> int:
    normalized = " ".join(_tokens(route_text))
    trigger_normalized = " ".join(_tokens(trigger))
    if not normalized or not trigger_normalized:
        return 0
    if trigger_normalized in normalized:
        return 40 + min(len(trigger_normalized), 20)
    overlap = set(_tokens(route_text)) & set(_tokens(trigger))
    return 8 * len(overlap) if overlap else 0


def _family_score(request_family_ids: set[str], recipe: CompositionRecipe) -> int:
    overlap = request_family_ids & set(recipe.evidence_primitive_family_ids)
    return 60 * len(overlap)


def _specificity_score(route_text: str, recipe: CompositionRecipe) -> int:
    normalized = " ".join(_tokens(route_text))
    if recipe.recipe_id == "single_cell_atlas_storyboard" and any(
        token in normalized
        for token in (
            "single cell",
            "scrna",
            "cell type",
            "atlas",
            "spatial transcriptomics",
            "umap",
            "tsne",
        )
    ):
        return 80
    if recipe.recipe_id == "asymmetric_genomics_figure" and any(
        token in normalized
        for token in ("genomic", "genomics", "mutation", "oncoplot", "heatmap", "pathway")
    ):
        return 60
    if recipe.recipe_id == "model_validation_dashboard" and any(
        token in normalized
        for token in ("shap", "threshold", "subgroup", "generalizability", "robustness")
    ):
        return 70
    return 0


def select_composition_recipe(
    request: Mapping[str, Any],
    catalog: MedicalFigureFamilyCatalog,
) -> CompositionRecipe:
    request_family_ids = {
        _text(item)
        for item in _list(request.get("medical_family_ids"))
        if _text(item)
    }
    if _text(request.get("medical_figure_family_id")):
        request_family_ids.add(_text(request.get("medical_figure_family_id")))

    text = _route_text(request)
    scored: list[tuple[int, CompositionRecipe]] = []
    for recipe in catalog.composition_recipes:
        score = _family_score(request_family_ids, recipe)
        score += sum(_trigger_score(text, trigger) for trigger in recipe.claim_triggers)
        score += _specificity_score(text, recipe)
        if recipe.design_shell_allowed and _text(request.get("figure_kind")) == "illustration_shell":
            score += 30
        if score > 0:
            scored.append((score, recipe))

    if not scored:
        return catalog.composition_recipes_by_id["schematic_led_composite"] if (
            _text(request.get("figure_kind")) == "illustration_shell"
        ) else catalog.composition_recipes_by_id["clinical_triptych_prediction"]
    scored.sort(key=lambda item: (item[0], item[1].recipe_id), reverse=True)
    return scored[0][1]


def composition_recipe_payload(recipe: CompositionRecipe) -> dict[str, Any]:
    return {
        "recipe_id": recipe.recipe_id,
        "title": recipe.title,
        "intent": recipe.intent,
        "claim_triggers": list(recipe.claim_triggers),
        "hero_panel_role": recipe.hero_panel_role,
        "supporting_panel_roles": list(recipe.supporting_panel_roles),
        "evidence_primitive_family_ids": list(recipe.evidence_primitive_family_ids),
        "recommended_starter_recipe_ids": list(recipe.recommended_starter_recipe_ids),
        "design_shell_allowed": recipe.design_shell_allowed,
        "programmatic_evidence_required": recipe.programmatic_evidence_required,
        "default_layout": recipe.default_layout,
        "guide_strategy": recipe.guide_strategy,
        "label_strategy": recipe.label_strategy,
        "style_tokens": list(recipe.style_tokens),
        "palette_tokens": list(recipe.palette_tokens),
        "qa_gate_ids": list(recipe.qa_gate_ids),
        "learned_patterns": list(recipe.learned_patterns),
        "ai_may_change": list(recipe.ai_may_change),
        "ai_must_preserve": list(recipe.ai_must_preserve),
        "forbidden_authority": list(recipe.forbidden_authority),
        "quality_floor_only": True,
    }
