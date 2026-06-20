from __future__ import annotations

from typing import Any


POLICY_ID = "mas_publication_polish_policy.v1"

SOURCE_REFS: tuple[dict[str, str], ...] = (
    {
        "ref_id": "nature_skills_nature_figure",
        "url": "https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-figure",
        "lesson": "Start from a figure contract: core conclusion, evidence chain, panel hierarchy, backend-exclusive render/export, and final visual QA.",
    },
    {
        "ref_id": "nature_final_submission_artwork",
        "url": "https://www.nature.com/nature/for-authors/final-submission",
        "lesson": "Check final-size lettering, line weight, reduced-size readability, vector line art, RGB color, and production-quality export before paper use.",
    },
    {
        "ref_id": "ggplot2_theme_and_guides",
        "url": "https://ggplot2.tidyverse.org/reference/theme.html",
        "lesson": "Keep article-level visual grammar in one theme and guide system rather than per-template styling drift.",
    },
    {
        "ref_id": "colorspace_hcl_palettes",
        "url": "https://colorspace.r-forge.r-project.org/",
        "lesson": "Select qualitative, sequential, and diverging palettes by data semantics and accessibility, not by plot-local taste.",
    },
    {
        "ref_id": "viridis_perceptual_palette",
        "url": "https://sjmgarnier.github.io/viridis/",
        "lesson": "Use perceptually uniform sequential scales for unsigned continuous evidence encodings.",
    },
    {
        "ref_id": "complexheatmap_fixed_color_mapping",
        "url": "https://jokergoo.github.io/ComplexHeatmap-reference/book/a-single-heatmap.html",
        "lesson": "Use fixed value-to-color mappings for comparable matrix heatmaps instead of per-figure color drift.",
    },
    {
        "ref_id": "patchwork_cowplot_multipanel",
        "url": "https://patchwork.data-imaginist.com/",
        "lesson": "Treat multipanel figures as claim-led storyboards with shared legends and explicit hierarchy.",
    },
    {
        "ref_id": "survminer_km_practice",
        "url": "https://rpkgs.datanovia.com/survminer/",
        "lesson": "Survival figures need risk table, censor marks, event definition, and time scale reviewed together.",
    },
)

REQUIRED_BEFORE_PAPER_USE: tuple[str, ...] = (
    "core_conclusion_and_evidence_chain_locked",
    "paper_local_data_and_statistics_refs_present",
    "semantic_palette_roles_resolved_from_article_style_profile",
    "guide_legend_colorbar_overlap_checked_after_render",
    "final_physical_size_readability_checked",
    "multipanel_hierarchy_and_shared_guides_checked",
    "vector_or_high_resolution_export_recorded",
    "visual_audit_receipt_or_residual_item_recorded",
)

HIGH_RISK_FAMILY_CHECKS: tuple[dict[str, object], ...] = (
    {
        "family": "kaplan_meier_with_risk_table",
        "checks": ["risk_table", "censor_marks", "time_scale", "event_definition", "strata_order"],
    },
    {
        "family": "genomic_landscape_or_oncoprint",
        "checks": ["sample_order", "annotation_tracks", "alteration_semantics", "shared_heatmap_palette"],
    },
    {
        "family": "matrix_heatmap",
        "checks": ["fixed_scale_mapping", "sequential_vs_diverging_semantics", "colorbar_tick_density"],
    },
    {
        "family": "shap_and_model_explanation",
        "checks": ["feature_order", "direction_encoding", "legend_density", "panel_claim_mapping"],
    },
    {
        "family": "coefficient_path_or_high_density_lines",
        "checks": ["label_strategy", "direct_label_or_shared_legend", "line_density", "semantic_fit"],
    },
    {
        "family": "multipanel_storyboard",
        "checks": ["hero_panel", "panel_labels", "shared_guides", "remove_non_claim_panels"],
    },
)


def publication_polish_policy() -> dict[str, Any]:
    return {
        "policy_id": POLICY_ID,
        "source_refs": [dict(item) for item in SOURCE_REFS],
        "nonblocking_agent_policy": {
            "manual_template_browsing_required": False,
            "blocks_default_evidence_progress": False,
            "warnings_are_visual_audit_hints_not_agent_blockers": True,
            "starter_templates_are_quality_floor_not_ceiling": True,
            "ai_may_redesign_layout_palette_panel_structure_and_backend_when_semantics_are_preserved": True,
        },
        "palette_scale_policy": {
            "article_level_style_profile_required": True,
            "categorical_roles": "stable_series_roles_from_publication_style_profile",
            "continuous_unsigned_default": "perceptual_sequential_scale",
            "continuous_signed_default": "centered_diverging_scale",
            "matrix_heatmap_scale_mapping": "fixed_by_semantic_role_across_figures",
            "per_plot_palette_drift_allowed": False,
        },
        "guide_layout_policy": {
            "legend_position": "outside_or_shared_when_multi_series",
            "crowded_legend_policy": "wrap_rows_or_use_direct_labels",
            "colorbar_policy": "horizontal_or_compact_with_fewer_breaks_when_ticks_collide",
            "final_size_overlap_check": "required_before_paper_use",
        },
        "multipanel_policy": {
            "claim_bearing_hero_panel_preferred": True,
            "shared_guides_preferred": True,
            "drop_panels_without_unique_evidence": True,
            "panel_labels_required_for_storyboard_figures": True,
            "final_size_readability_check": "required_before_paper_use",
        },
        "required_before_paper_use": list(REQUIRED_BEFORE_PAPER_USE),
        "high_risk_family_checks": [dict(item) for item in HIGH_RISK_FAMILY_CHECKS],
        "residual_limit": (
            "This policy improves the default lower bound and agent hints; it does not authorize "
            "publication readiness, replace visual audit, or replace paper-local owner review."
        ),
    }
