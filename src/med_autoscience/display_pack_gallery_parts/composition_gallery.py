from __future__ import annotations

from typing import Any

from med_autoscience.display_pack_gallery_catalog import TemplateRecord


FAMILY_PROXY_IDS: dict[str, tuple[str, ...]] = {
    "cell_composition": ("risk_stratification",),
    "feature_expression_map": ("dimension_reduction_scatter", "annotated_heatmap"),
    "marker_or_feature_evidence": ("marker_dotplot",),
    "mechanism_schematic": ("effect_forest",),
    "paired_change": ("effect_forest",),
    "single_cell_embedding": ("dimension_reduction_scatter",),
    "spatial_feature_map": ("dimension_reduction_scatter", "annotated_heatmap"),
    "subgroup_interaction_forest": ("effect_forest", "external_validation_performance"),
    "sensitivity_analysis_panel": ("effect_forest", "external_validation_performance"),
    "threshold_governance": ("decision_curve_analysis", "model_complexity_audit"),
}

FAMILY_TEMPLATE_PREFERENCES: dict[str, tuple[str, ...]] = {
    "annotated_heatmap": ("heatmap_group_comparison",),
    "calibration_panel": ("calibration_curve_binary", "time_to_event_multihorizon_calibration_panel"),
    "decision_curve_analysis": ("decision_curve_binary", "time_to_event_decision_curve"),
    "dimension_reduction_scatter": ("umap_scatter_grouped", "pca_scatter_grouped", "tsne_scatter_grouped"),
    "discrimination_curve": ("roc_curve_binary", "time_dependent_roc_horizon", "pr_curve_binary"),
    "effect_forest": ("forest_effect_main",),
    "enrichment_dotplot": ("pathway_enrichment_dotplot_panel",),
    "external_validation_performance": ("generalizability_subgroup_composite_panel",),
    "genomic_consequence_summary": ("genomic_alteration_consequence_panel",),
    "marker_dotplot": ("celltype_marker_dotplot_panel",),
    "model_complexity_audit": ("model_complexity_audit_panel",),
    "oncoplot_landscape": ("genomic_alteration_landscape_panel",),
    "risk_stratification": ("risk_layering_monotonic_bars",),
    "shap_local_explanation": ("shap_waterfall_local_explanation_panel",),
    "shap_summary": ("shap_summary_beeswarm",),
    "volcano_or_ma_plot": ("omics_volcano_panel",),
}


def _text(value: object) -> str:
    return str(value or "").strip()


def _strings(value: object) -> list[str]:
    return [_text(item) for item in value] if isinstance(value, list) else []


def _display_records_by_family(records: list[TemplateRecord]) -> dict[str, list[TemplateRecord]]:
    by_family: dict[str, list[TemplateRecord]] = {}
    for record in records:
        if record.kind != "evidence_figure" or record.renderer_family != "r_ggplot2":
            continue
        for family_id in record.medical_family_ids:
            by_family.setdefault(family_id, []).append(record)
    for family_records in by_family.values():
        family_records.sort(key=lambda item: item.template_id)
    return by_family


def _candidate_records(
    family_id: str,
    records_by_family: dict[str, list[TemplateRecord]],
) -> list[TemplateRecord]:
    candidates = list(records_by_family.get(family_id, ()))
    for proxy_id in FAMILY_PROXY_IDS.get(family_id, ()):
        candidates.extend(records_by_family.get(proxy_id, ()))
    preferences = FAMILY_TEMPLATE_PREFERENCES.get(family_id, ())
    preference_rank = {
        template_id: index
        for index, template_id in enumerate(preferences)
    }
    candidates.sort(
        key=lambda item: (
            preference_rank.get(item.template_id, len(preference_rank)),
            item.template_id,
        )
    )
    return candidates


def _panel_payload(
    *,
    panel_role: str,
    panel_kind: str,
    family_id: str,
    template: TemplateRecord | None,
    uses_proxy: bool,
) -> dict[str, Any]:
    return {
        "panel_role": panel_role,
        "panel_kind": panel_kind,
        "evidence_primitive_family_id": family_id,
        "template_id": template.template_id if template else "",
        "canonical_family_title": template.canonical_family_title if template else "",
        "canonical_family_category": template.canonical_family_category if template else "",
        "uses_gallery_proxy": uses_proxy,
        "visual_status": "preview_template" if template else "storyboard_placeholder",
    }


def _recipe_panels(
    recipe: dict[str, Any],
    records_by_family: dict[str, list[TemplateRecord]],
) -> list[dict[str, Any]]:
    roles = [_text(recipe.get("hero_panel_role")), *_strings(recipe.get("supporting_panel_roles"))]
    family_ids = _strings(recipe.get("evidence_primitive_family_ids"))
    used_template_ids: set[str] = set()
    panels: list[dict[str, Any]] = []
    for index, role in enumerate(roles):
        family_id = family_ids[index % len(family_ids)] if family_ids else ""
        template = None
        uses_proxy = False
        for candidate in _candidate_records(family_id, records_by_family):
            if candidate.template_id in used_template_ids:
                continue
            template = candidate
            uses_proxy = family_id not in candidate.medical_family_ids
            used_template_ids.add(candidate.template_id)
            break
        panels.append(
            _panel_payload(
                panel_role=role,
                panel_kind="hero" if index == 0 else "supporting",
                family_id=family_id,
                template=template,
                uses_proxy=uses_proxy,
            )
        )
    return panels


def build_composition_gallery_surface(
    composition_surface: dict[str, Any],
    records: list[TemplateRecord],
) -> dict[str, Any]:
    records_by_family = _display_records_by_family(records)
    recipes: list[dict[str, Any]] = []
    for recipe in composition_surface.get("recipes", []):
        if not isinstance(recipe, dict):
            continue
        panels = _recipe_panels(recipe, records_by_family)
        recipes.append(
            {
                "recipe_id": _text(recipe.get("recipe_id")),
                "title": _text(recipe.get("title")),
                "intent": _text(recipe.get("intent")),
                "default_layout": _text(recipe.get("default_layout")),
                "hero_panel_role": _text(recipe.get("hero_panel_role")),
                "supporting_panel_roles": _strings(recipe.get("supporting_panel_roles")),
                "guide_strategy": _text(recipe.get("guide_strategy")),
                "label_strategy": _text(recipe.get("label_strategy")),
                "design_shell_allowed": bool(recipe.get("design_shell_allowed")),
                "programmatic_evidence_required": bool(recipe.get("programmatic_evidence_required")),
                "evidence_primitive_family_ids": _strings(recipe.get("evidence_primitive_family_ids")),
                "recommended_starter_recipe_ids": _strings(recipe.get("recommended_starter_recipe_ids")),
                "style_tokens": _strings(recipe.get("style_tokens")),
                "palette_tokens": _strings(recipe.get("palette_tokens")),
                "qa_gate_ids": _strings(recipe.get("qa_gate_ids")),
                "storyboard_panels": panels,
                "preview_template_ids": [
                    panel["template_id"]
                    for panel in panels
                    if panel.get("template_id")
                ],
                "quality_floor_only": True,
                "not_publication_ready": True,
            }
        )
    return {
        "schema_version": 1,
        "surface_kind": "display_pack_composition_recipe_gallery",
        "gallery_visible": True,
        "included_in_html_pdf": True,
        "composition_recipe_count": len(recipes),
        "storyboard_preview_policy": (
            "visual storyboards show page-level organization using current evidence "
            "primitive thumbnails and placeholders; they are not paper-local data results"
        ),
        "recipes": recipes,
    }
