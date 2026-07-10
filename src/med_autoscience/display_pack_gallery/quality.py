from __future__ import annotations

from collections import Counter
from typing import Any

from med_autoscience.display_pack_gallery_catalog import (
    TABLE_PREVIEW_GALLERY_TEMPLATE_IDS,
    TemplateRecord,
)
from med_autoscience.display_pack_gallery.assets import RenderedAsset
from med_autoscience.display_pack_gallery.composition_gallery import (
    build_composition_gallery_surface,
)
from med_autoscience.display_pack_agent.figure_contract import figure_contract_policy
from med_autoscience.display_pack_agent.figure_workflow import figure_workflow_policy
from med_autoscience.display_pack_agent.composition_recipe_projection import (
    composition_recipe_discovery_payload,
)
from med_autoscience.display_pack_agent.publication_polish_policy import (
    publication_polish_policy,
)
from med_autoscience.display_pack_dependency_environment import (
    dependency_requirements_for_template_ids,
)
from med_autoscience.display_pack_gallery import paths
from med_autoscience.display_pack_renderer_policy import (
    R_GGPLOT2_RENDERER,
    renderer_policy_completion,
    renderer_policy_payload,
)


EXTERNAL_QUALITY_REFERENCES: tuple[dict[str, str], ...] = (
    {
        "ref_id": "nature_final_submission_artwork",
        "url": "https://www.nature.com/nature/for-authors/final-submission",
        "lesson": "Use consistent figure lettering, readable reduced-size labels, vector line art when possible, RGB color, and production-quality figure files.",
    },
    {
        "ref_id": "ggplot2_theme_system",
        "url": "https://ggplot2.tidyverse.org/reference/theme.html",
        "lesson": "Use a single theme system for titles, labels, fonts, backgrounds, gridlines, and legends so all evidence figures share one article-level visual grammar.",
    },
    {
        "ref_id": "ggsci_npg_palette",
        "url": "https://nanx.me/ggsci/reference/scale_npg.html",
        "lesson": "Nature Publishing Group inspired discrete palettes are mature ggplot2-compatible references for publication-style categorical roles.",
    },
    {
        "ref_id": "colorspace_hcl_palettes",
        "url": "https://colorspace.r-forge.r-project.org/",
        "lesson": "HCL-based qualitative, sequential and diverging palettes are a stable basis for article-level semantic color roles.",
    },
    {
        "ref_id": "viridis_perceptual_palette",
        "url": "https://sjmgarnier.github.io/viridis/",
        "lesson": "Perceptually uniform and color-vision-friendly sequential palettes are preferred for continuous matrix and density-like encodings.",
    },
    {
        "ref_id": "complexheatmap_color_mapping",
        "url": "https://jokergoo.github.io/ComplexHeatmap-reference/book/a-single-heatmap.html",
        "lesson": "Matrix heatmaps need fixed value-to-color mapping rather than per-plot drift; shared sequential and diverging mappings preserve cross-figure comparability.",
    },
    {
        "ref_id": "nature_skills_figure_contract",
        "url": "https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-figure",
        "lesson": "Figure work should start from core conclusion, evidence chain, panel hierarchy, backend-exclusive export, and final visual QA; MAS adapts this into a nonblocking R-first agent contract.",
    },
    {
        "ref_id": "scientific_agent_skills_provenance",
        "url": "https://github.com/K-Dense-AI/scientific-agent-skills",
        "lesson": "Scientific figure skills should be discoverable, task-scoped, and provenance-carrying instead of hidden inside a generic plotting prompt.",
    },
    {
        "ref_id": "papervizagent_reference_pipeline",
        "url": "https://github.com/google-research/papervizagent",
        "lesson": "Reference-driven figure agents separate retrieval, planning, styling, visualization, and critique; MAS adapts this as refs-only quality-floor evidence.",
    },
    {
        "ref_id": "paperbanana_candidate_critic_loop",
        "url": "https://github.com/dwzhu-pku/PaperBanana",
        "lesson": "Academic illustration generation benefits from multiple candidates and critic rounds before owner review rather than single-shot template reuse.",
    },
    {
        "ref_id": "figmirror_reference_preserve_list",
        "url": "https://github.com/VILA-Lab/FigMirror",
        "lesson": "Reference matching needs an explicit preserve list so style transfer does not drift away from claim, evidence, labels, or source constraints.",
    },
    {
        "ref_id": "scientific_plotting_skill_hard_rules",
        "url": "https://github.com/dazhiyang/scientific-plotting-skill",
        "lesson": "Small hard rules for vector export, dimensions, color, typography, and parameter blocks raise the plotting floor without constraining the figure concept.",
    },
    {
        "ref_id": "abstract_fig_editable_source",
        "url": "https://github.com/keros68/abstract-fig",
        "lesson": "Graphical abstract skills are easier to review and revise when the visual source remains editable instead of only producing a flattened image.",
    },
    {
        "ref_id": "graphical_abstract_template_three_panel",
        "url": "https://github.com/kpoduska/GraphicalAbstractTemplate",
        "lesson": "A simple three-panel flow remains useful as a low-risk default only when it is treated as a brief-driven composition skeleton, not a fixed final visual system.",
    },
    {
        "ref_id": "figpad_research_prompt_patterns",
        "url": "https://github.com/Figpad/awesome-research-figure-prompts",
        "lesson": "Prompt collections are most useful when converted into explicit brief, preserve-list, candidate, and critic gates rather than copied as prose prompts.",
    },
    {
        "ref_id": "sciga_graphical_abstract_dataset",
        "url": "https://github.com/IyatomiLab/SciGA",
        "lesson": "Graphical abstracts vary by field and paper intent; a renderer should preserve AI choice of composition while enforcing readable layout and evidence constraints.",
    },
)

SCIENTIFIC_FIGURE_QUALITY_FLOOR_POLICY: dict[str, Any] = {
    "policy_id": "mas_scientific_figure_quality_floor.v1",
    "scope": "all_gallery_and_paper_candidate_figures",
    "graphical_abstract_strategy": "brief_first_reference_guided_ai_candidate_not_single_template_reuse",
    "ai_executor_freedom": (
        "ai_may_choose_figure_type_layout_panel_hierarchy_backend_and_candidate_count_from_paper_local_claims"
    ),
    "template_library_role": "quality_floor_and_reviewable_starting_point_not_ceiling_or_publication_ready_authority",
    "learned_scientific_figure_patterns": [
        "discoverable_skill_pack_with_provenance",
        "figure_brief_before_plotting",
        "reference_selection_and_style_brief",
        "reference_target_preserve_list",
        "candidate_generation_before_owner_gate",
        "critic_review_or_route_back",
        "final_size_readability_inspection",
        "vector_export_when_possible",
        "semantic_palette_and_color_vision_check",
        "source_data_statistics_and_claim_refs_preserved",
    ],
    "required_before_gallery_or_paper_use": [
        "core_claim_and_evidence_chain_ref",
        "figure_brief_ref",
        "reference_selection_ref",
        "style_brief_ref",
        "preserve_list_ref",
        "candidate_artifact_ref",
        "critic_review_ref",
        "final_size_inspection_ref",
        "source_preservation_ref",
        "owner_gate_ref",
    ],
    "rebuild_boundary": {
        "design_shell_graphical_abstract_reporting_flow": (
            "may_be_rebuilt_into_stronger_visual_systems_when_the_figure_brief_and_owner_gate_require_it"
        ),
        "r_ggplot2_evidence_figures": (
            "raise_quality_through_theme_size_qc_critic_gate_references_and_source_preservation_not_wholesale_manual_redraw"
        ),
    },
    "external_learning_sources": [
        "K-Dense-AI/scientific-agent-skills",
        "Yuan1z0825/nature-skills",
        "google-research/papervizagent",
        "dwzhu-pku/PaperBanana",
        "VILA-Lab/FigMirror",
        "dazhiyang/scientific-plotting-skill",
        "keros68/abstract-fig",
        "kpoduska/GraphicalAbstractTemplate",
        "Figpad/awesome-research-figure-prompts",
        "IyatomiLab/SciGA",
    ],
    "reference_learning_sources": [
        {
            "source_id": ref["ref_id"],
            "url": ref["url"],
            "lesson": ref["lesson"],
        }
        for ref in EXTERNAL_QUALITY_REFERENCES
    ],
    "forbidden_claims": [
        "publication_ready",
        "owner_accepted",
        "artifact_authority",
        "style_reference_as_claim_or_data_authority",
    ],
}

FAMILY_BASELINE_WARNINGS: dict[str, tuple[str, ...]] = {
    "coefficient_path_panel": ("coefficient_path_semantic_fit_review",),
    "genomic_alteration_landscape_panel": ("oncoprint_annotation_track_review",),
    "kaplan_meier_grouped": ("km_risk_table_and_censor_mark_review",),
    "model_complexity_audit_panel": ("multi_panel_readability_review",),
    "shap_waterfall_local_explanation_panel": ("multi_panel_readability_review",),
}

KIND_BASELINE_WARNINGS: dict[str, tuple[str, ...]] = {
    "illustration_shell": ("illustration_shell_style_review_required",),
}


def _baseline_quality_gates(record: TemplateRecord, asset: RenderedAsset) -> list[str]:
    gates = [
        "template_family_canonicalized",
        "medical_figure_family_mapped" if record.medical_family_ids else "medical_figure_family_missing",
        "starter_recipe_profile_present"
        if record.publication_quality_profile.get("starter_recipe_ids")
        else "starter_recipe_profile_missing",
        "style_palette_qa_profile_present"
        if (
            record.publication_quality_profile.get("style_profile_ids")
            and record.publication_quality_profile.get("palette_token_ids")
            and record.publication_quality_profile.get("qa_gate_ids")
        )
        else "style_palette_qa_profile_missing",
        "reference_ratio_gallery_preview",
        "vector_export_available" if asset.pdf_ref or asset.svg_ref else "vector_export_missing",
        "semantic_palette_context",
        "synthetic_payload_only",
        "requires_ai_local_adaptation",
        "core_conclusion_before_plotting",
        "evidence_chain_maps_panels_to_claim",
        "journal_export_contract_before_paper_use",
        "final_visual_qa_required",
    ]
    if record.renderer_family == "r_ggplot2":
        gates.append("ggplot2_publication_theme")
        gates.append("r_ggplot2_default_evidence_backend")
    if record.kind == "illustration_shell" and record.renderer_family == "python":
        gates.append("python_renderer_style_alignment_required")
    return gates


def audit_template_quality(record: TemplateRecord, asset: RenderedAsset, baseline: RenderedAsset) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if asset.status != "rendered":
        blockers.append(f"render_status_{asset.status}")
    table_preview_card = (
        record.kind == "table_shell"
        and record.template_id in TABLE_PREVIEW_GALLERY_TEMPLATE_IDS
    )
    if (record.renderer_family == "n/a" or record.kind == "table_shell") and not table_preview_card:
        blockers.append("non_visual_template_not_gallery_card")
    if not record.medical_family_ids:
        blockers.append("medical_figure_family_mapping_missing")
    if not record.publication_quality_profile.get("starter_recipe_ids"):
        blockers.append("starter_recipe_profile_missing")
    if not record.publication_quality_profile.get("style_profile_ids"):
        blockers.append("style_profile_mapping_missing")
    if not record.publication_quality_profile.get("palette_token_ids"):
        blockers.append("palette_token_mapping_missing")
    if not record.publication_quality_profile.get("qa_gate_ids"):
        blockers.append("qa_gate_mapping_missing")
    if "vector_export_missing" in _baseline_quality_gates(record, asset):
        warnings.append("vector_export_missing")
    if record.kind == "illustration_shell" and record.renderer_family == "python":
        warnings.append("python_renderer_style_alignment_required")
    if table_preview_card:
        warnings.append("table_shell_preview_not_table_authority")
    if record.kind == "evidence_figure" and record.renderer_family == "python":
        blockers.append("python_evidence_retained_without_advantage_proof")
    warnings.extend(FAMILY_BASELINE_WARNINGS.get(record.canonical_family_id, ()))
    warnings.extend(KIND_BASELINE_WARNINGS.get(record.kind, ()))
    if record.canonical_family_category in {"Matrix Pattern", "Model Explanation"}:
        warnings.append("legend_or_colorbar_overlap_risk")
    if record.canonical_family_category in {"Publication Shells and Tables", "Generalizability"}:
        warnings.append("composition_density_risk")

    unique_blockers = sorted(set(blockers))
    unique_warnings = sorted(set(warnings))
    status = "not_publication_ready" if unique_blockers else "lower_bound_review_required"
    return {
        "template_id": record.template_id,
        "canonical_family_id": record.canonical_family_id,
        "canonical_family_title": record.canonical_family_title,
        "category": record.canonical_family_category,
        "renderer_family": record.renderer_family,
        "renderer_policy": renderer_policy_payload(record),
        "medical_family_ids": list(record.medical_family_ids),
        "publication_quality_profile": dict(record.publication_quality_profile),
        "status": status,
        "publication_ready_claim_authorized": False,
        "quality_gates": _baseline_quality_gates(record, asset),
        "blockers": unique_blockers,
        "warnings": unique_warnings,
        "figure_contract_policy_ref": figure_contract_policy()["policy_id"],
        "figure_workflow_policy_ref": figure_workflow_policy()["policy_id"],
        "publication_polish_policy_ref": publication_polish_policy()["policy_id"],
        "recommended_next_actions": recommended_next_actions(record, unique_blockers, unique_warnings),
    }


def _checked_in_reporting_flow_renderer_family(record: TemplateRecord) -> str:
    requirements = dependency_requirements_for_template_ids(
        repo_root=paths.REPO_ROOT,
        template_ids={record.template_id, record.full_template_id},
    )
    for requirement in requirements:
        render_contract = requirement.get("render_contract")
        if isinstance(render_contract, dict):
            checked_in_family = render_contract.get("checked_in_renderer_family")
            if isinstance(checked_in_family, str) and checked_in_family:
                return checked_in_family
        renderer_family = requirement.get("renderer_family")
        if isinstance(renderer_family, str) and renderer_family:
            return renderer_family
    return record.renderer_family


def _audit_reporting_flow_quality(
    record: TemplateRecord,
    asset: RenderedAsset,
    baseline: RenderedAsset,
) -> dict[str, Any]:
    audit = audit_template_quality(record, asset, baseline)
    audit["renderer_family"] = _checked_in_reporting_flow_renderer_family(record)
    return audit


def recommended_next_actions(record: TemplateRecord, blockers: list[str], warnings: list[str]) -> list[str]:
    actions = [
        "Use this template as a lower-bound starting point; AI may freely alter structure, layout, labels, scale, and composition for the paper-specific claim.",
        "Render-inspect-revise before any paper-facing use; do not accept the synthetic Gallery preview as final artwork.",
    ]
    if "python_renderer_style_alignment_required" in warnings:
        actions.append("Align design-shell typography, palette roles, export discipline, and composition with the MAS publication style profile.")
    if "legend_or_colorbar_overlap_risk" in warnings:
        actions.append("Check guide boxes after rendering; prefer direct labels or horizontal colorbars when tick labels collide.")
    if "km_risk_table_and_censor_mark_review" in warnings:
        actions.append("Verify risk table, censor marks, time scale, and event definition against the paper-local survival estimand.")
    if "oncoprint_annotation_track_review" in warnings:
        actions.append("Verify annotation tracks, sample ordering, alteration semantics, and shared heatmap palette roles.")
    if "multi_panel_readability_review" in warnings:
        actions.append("Rebalance panel hierarchy around the claim-bearing hero panel and recheck final-size labels.")
    if "python_evidence_retained_without_advantage_proof" in blockers:
        actions.append("Retire this Python evidence template or promote it only after documented advantage over the R/ggplot2 baseline and visual audit.")
    if record.kind == "illustration_shell":
        actions.append("Treat shell figures as editorial layouts requiring paper-local composition, not fixed statistical plot templates.")
    return actions


def build_quality_audit(
    *,
    records: list[TemplateRecord],
    visual_records: list[TemplateRecord],
    non_visual_records: list[TemplateRecord],
    design_records: list[TemplateRecord],
    reporting_flow_records: list[TemplateRecord],
    table_preview_records: list[TemplateRecord],
    default_surface_excluded_records: list[TemplateRecord],
    rendered: dict[str, RenderedAsset],
    baseline_rendered: dict[str, RenderedAsset],
) -> dict[str, Any]:
    template_audits = [
        audit_template_quality(
            record,
            rendered[record.template_id],
            baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")),
        )
        for record in visual_records
    ]
    reporting_flow_audits = [
        _audit_reporting_flow_quality(
            record,
            rendered[record.template_id],
            baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")),
        )
        for record in reporting_flow_records
    ]
    design_audits = [
        audit_template_quality(
            record,
            rendered[record.template_id],
            baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")),
        )
        for record in design_records
    ]
    table_preview_audits = [
        audit_template_quality(
            record,
            rendered[record.template_id],
            baseline_rendered.get(record.template_id, RenderedAsset(status="not_applicable")),
        )
        for record in table_preview_records
    ]
    blocker_counts = Counter(
        blocker
        for audit in [*template_audits, *reporting_flow_audits, *design_audits, *table_preview_audits]
        for blocker in audit["blockers"]
    )
    warning_counts = Counter(
        warning
        for audit in [*template_audits, *reporting_flow_audits, *design_audits, *table_preview_audits]
        for warning in audit["warnings"]
    )
    blocked_count = sum(1 for audit in template_audits if audit["blockers"])
    gallery_visual_blocked_count = sum(
        1 for audit in [*template_audits, *reporting_flow_audits, *design_audits, *table_preview_audits] if audit["blockers"]
    )
    ready_like_count = len(template_audits) - blocked_count
    profile_coverage = _publication_quality_profile_coverage(records)
    completion_by_category = _category_completion(
        records=records,
        visual_records=visual_records,
        non_visual_records=non_visual_records,
        default_surface_excluded_records=default_surface_excluded_records,
    )
    composition_recipe_surface = composition_recipe_discovery_payload(include_recipes=True)
    composition_gallery_surface = build_composition_gallery_surface(composition_recipe_surface, records)
    return {
        "schema_version": 1,
        "overall_status": "not_publication_ready",
        "publication_ready_claim_authorized": False,
        "quality_surface": "gallery_lower_bound_visual_audit",
        "visual_template_count": len(visual_records),
        "reporting_flow_visual_template_count": len(reporting_flow_records),
        "design_visual_template_count": len(design_records),
        "table_preview_visual_template_count": len(table_preview_records),
        "total_gallery_visual_template_count": (
            len(visual_records) + len(reporting_flow_records) + len(design_records) + len(table_preview_records)
        ),
        "non_visual_template_count": len(non_visual_records),
        "lower_bound_review_required_count": ready_like_count,
        "blocked_template_count": blocked_count,
        "gallery_visual_blocked_template_count": gallery_visual_blocked_count,
        "gallery_lower_bound_admission_status": (
            "gallery_lower_bound_passed_requires_paper_audit"
            if gallery_visual_blocked_count == 0 and profile_coverage["complete_profile_percent"] == 100
            else "gallery_lower_bound_blocked"
        ),
        "publication_quality_profile_coverage": profile_coverage,
        "renderer_policy_completion": renderer_policy_completion(
            records
        ),
        "completion_by_category": completion_by_category,
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "warning_counts": dict(sorted(warning_counts.items())),
        "quality_policy": {
            "default_gallery_claim": "lower_bound_reference_templates_only",
            "ai_authority": "ai_may_freely_modify_template_structure_layout_palette_labels_and_composition_for_paper_specific_claim",
            "not_authority": "gallery_does_not_authorize_publication_readiness_or_final_artwork_acceptance",
            "current_surface": "canonical_current_gallery_templates_not_input_data_specific_variants",
            "scientific_figure_quality_floor_policy": SCIENTIFIC_FIGURE_QUALITY_FLOOR_POLICY,
            "composition_recipe_policy": "page_level_recipes_organize_primitives_without_becoming_duplicate_gallery_cards",
            "reporting_flow_gallery_policy": "validated_reporting_flow_shells_are_programmatic_disposition_starting_points",
            "design_gallery_policy": "illustration_shells_are_visible_non_statistical_design_starting_points",
            "table_preview_gallery_policy": "table_shells_keep_table_authority_with_gallery_only_gridextra_preview",
            "required_before_paper_use": publication_polish_policy()["required_before_paper_use"],
            "required_workflow_before_paper_use": figure_workflow_policy()["paper_use_acceptance"],
            "composition_recipe_required_before_paper_use": [
                "composition_recipe_selected_or_explicitly_declined",
                "hero_panel_role_declared",
                "shared_legend_or_direct_label_strategy_declared",
                "programmatic_evidence_primitives_preserve_data_statistics_refs",
            ],
            "gallery_lower_bound_admission_requires": [
                "current_template_has_medical_family_mapping",
                "current_template_has_starter_recipe_profile",
                "current_template_has_style_palette_qa_profile",
                "default_gallery_render_respects_template_reference_ratio",
                "default_gallery_render_has_vector_export_when_possible",
            ],
        },
        "figure_contract_policy": figure_contract_policy(),
        "figure_workflow_policy": figure_workflow_policy(),
        "composition_recipe_surface": composition_recipe_surface,
        "composition_gallery_surface": composition_gallery_surface,
        "publication_polish_policy": publication_polish_policy(),
        "external_quality_references": list(EXTERNAL_QUALITY_REFERENCES),
        "templates": template_audits,
        "reporting_flow_gallery_templates": reporting_flow_audits,
        "design_gallery_templates": design_audits,
        "table_preview_gallery_templates": table_preview_audits,
        "non_visual_inventory": [
            {
                "template_id": record.template_id,
                "canonical_family_id": record.canonical_family_id,
                "canonical_family_title": record.canonical_family_title,
                "kind": record.kind,
                "renderer_family": record.renderer_family,
                "status": (
                    "reporting_flow_gallery_card"
                    if record in reporting_flow_records
                    else "design_gallery_card"
                    if record in design_records
                    else "table_preview_gallery_card"
                    if record in table_preview_records
                    else "kept_out_of_image_gallery"
                ),
            }
            for record in non_visual_records
        ],
        "default_surface_excluded_inventory": [
            {
                "template_id": record.template_id,
                "canonical_family_id": record.canonical_family_id,
                "canonical_family_title": record.canonical_family_title,
                "category": record.canonical_family_category,
                "kind": record.kind,
                "renderer_family": record.renderer_family,
                "status": "kept_out_of_default_gallery",
                "reason": renderer_policy_payload(record)["default_surface_reason"],
            }
            for record in default_surface_excluded_records
        ],
        "retired_alias_inventory": [
            {
                "template_id": alias,
                "canonical_template_id": record.canonical_template_id,
                "canonical_family_id": record.canonical_family_id,
                "status": "retired_alias_not_gallery_card",
            }
            for record in records
            for alias in record.migrated_alias_template_ids
        ],
    }


def _category_completion(
    *,
    records: list[TemplateRecord],
    visual_records: list[TemplateRecord],
    non_visual_records: list[TemplateRecord],
    default_surface_excluded_records: list[TemplateRecord],
) -> list[dict[str, Any]]:
    categories = sorted(
        {
            record.canonical_family_category
            for record in records
        }
    )
    rows: list[dict[str, Any]] = []
    for category in categories:
        visible = [record for record in visual_records if record.canonical_family_category == category]
        explicit_default_excluded = [
            record
            for record in default_surface_excluded_records
            if record.canonical_family_category == category
        ]
        default_r_family_ids = {
            record.canonical_family_id
            for record in visible
            if record.kind == "evidence_figure" and record.renderer_family == R_GGPLOT2_RENDERER
        }
        retained_python_evidence = [
            record
            for record in records
            if record.canonical_family_category == category
            and record.kind == "evidence_figure"
            and record.renderer_family == "python"
        ]
        non_visual = [
            record
            for record in non_visual_records
            if record.canonical_family_category == category
        ]
        evidence = [record for record in visible if record.kind == "evidence_figure"]
        r_evidence = [record for record in evidence if record.renderer_family == R_GGPLOT2_RENDERER]
        status = "done"
        if retained_python_evidence:
            status = "partial"
        if visible or non_visual:
            completion_percent = 100 if not retained_python_evidence else round(
                100 * len(visible) / (len(visible) + len(retained_python_evidence))
            )
        else:
            completion_percent = 0
        rows.append(
            {
                "category": category,
                "status": status,
                "completion_percent": completion_percent,
                "default_visual_families": len(visible),
                "default_r_ggplot2_evidence_families": len(r_evidence),
                "default_non_visual_families": len(non_visual),
                "default_surface_excluded_templates": len(explicit_default_excluded),
                "retained_python_evidence_templates": len(retained_python_evidence),
                "retained_python_evidence_template_ids": [record.template_id for record in retained_python_evidence],
            }
        )
    return rows


def _publication_quality_profile_coverage(records: list[TemplateRecord]) -> dict[str, Any]:
    missing_family = sorted(record.template_id for record in records if not record.medical_family_ids)
    missing_recipe = sorted(
        record.template_id
        for record in records
        if not record.publication_quality_profile.get("starter_recipe_ids")
    )
    missing_style = sorted(
        record.template_id
        for record in records
        if not record.publication_quality_profile.get("style_profile_ids")
    )
    missing_palette = sorted(
        record.template_id
        for record in records
        if not record.publication_quality_profile.get("palette_token_ids")
    )
    missing_qa = sorted(
        record.template_id
        for record in records
        if not record.publication_quality_profile.get("qa_gate_ids")
    )
    incomplete = set(missing_family) | set(missing_recipe) | set(missing_style) | set(missing_palette) | set(missing_qa)
    complete_count = len(records) - len(incomplete)
    return {
        "schema_version": 1,
        "current_template_count": len(records),
        "complete_profile_template_count": complete_count,
        "complete_profile_percent": round(100 * complete_count / len(records)) if records else 0,
        "medical_family_missing_template_ids": missing_family,
        "starter_recipe_missing_template_ids": missing_recipe,
        "style_profile_missing_template_ids": missing_style,
        "palette_token_missing_template_ids": missing_palette,
        "qa_gate_missing_template_ids": missing_qa,
    }


def build_quality_audit_markdown(audit: dict[str, Any]) -> str:
    blockers = audit["blocker_counts"]
    warnings = audit["warning_counts"]
    polish = audit["publication_polish_policy"]
    workflow = audit["figure_workflow_policy"]
    composition = audit["composition_recipe_surface"]
    composition_gallery = audit["composition_gallery_surface"]
    blocker_lines = "\n".join(f"| `{key}` | {value} |" for key, value in blockers.items()) or "| none | 0 |"
    warning_lines = "\n".join(f"| `{key}` | {value} |" for key, value in warnings.items()) or "| none | 0 |"
    before_paper_lines = "\n".join(
        f"- `{item}`" for item in polish["required_before_paper_use"]
    )
    workflow_before_paper_lines = "\n".join(
        f"- `{item}`" for item in workflow["paper_use_acceptance"]
    )
    composition_before_paper_lines = "\n".join(
        f"- `{item}`" for item in audit["quality_policy"]["composition_recipe_required_before_paper_use"]
    )
    scientific_floor = audit["quality_policy"]["scientific_figure_quality_floor_policy"]
    scientific_floor_pattern_lines = "\n".join(
        f"- `{item}`" for item in scientific_floor["learned_scientific_figure_patterns"]
    )
    scientific_floor_required_lines = "\n".join(
        f"- `{item}`" for item in scientific_floor["required_before_gallery_or_paper_use"]
    )
    scientific_floor_rebuild_lines = "\n".join(
        f"- `{key}`: {value}" for key, value in scientific_floor["rebuild_boundary"].items()
    )
    scientific_floor_source_lines = "\n".join(
        f"- `{item}`" for item in scientific_floor["external_learning_sources"]
    )
    scientific_floor_reference_lines = "\n".join(
        f"- [{item['source_id']}]({item['url']}): {item['lesson']}"
        for item in scientific_floor["reference_learning_sources"]
    )
    design_lines = "\n".join(
        (
            f"| `{item['template_id']}` | {item['category']} | {item['renderer_family']} | "
            f"`{item['status']}` | {', '.join(f'`{warning}`' for warning in item['warnings']) or 'none'} |"
        )
        for item in audit.get("design_gallery_templates", [])
    ) or "| none | none | none | none | none |"
    table_preview_lines = "\n".join(
        (
            f"| `{item['template_id']}` | {item['category']} | {item['renderer_family']} | "
            f"`{item['status']}` | {', '.join(f'`{warning}`' for warning in item['warnings']) or 'none'} |"
        )
        for item in audit.get("table_preview_gallery_templates", [])
    ) or "| none | none | none | none | none |"
    reporting_flow_lines = "\n".join(
        (
            f"| `{item['template_id']}` | {item['category']} | {item['renderer_family']} | "
            f"`{item['status']}` | {', '.join(f'`{warning}`' for warning in item['warnings']) or 'none'} |"
        )
        for item in audit.get("reporting_flow_gallery_templates", [])
    ) or "| none | none | none | none | none |"
    composition_recipe_lines = "\n".join(
        (
            f"| `{item['recipe_id']}` | {item['title']} | {item['hero_panel_role']} | "
            f"{len(item['supporting_panel_roles'])} | {len(item['evidence_primitive_family_ids'])} | "
            f"`{str(item['programmatic_evidence_required']).lower()}` | "
            f"`{str(item['design_shell_allowed']).lower()}` |"
        )
        for item in composition_gallery["recipes"]
    )
    high_risk_lines = "\n".join(
        f"| `{item['family']}` | {', '.join(f'`{check}`' for check in item['checks'])} |"
        for item in polish["high_risk_family_checks"]
    )
    template_lines = "\n".join(
        (
            f"| `{item['template_id']}` | {item['category']} | {item['renderer_family']} | "
            f"`{item['status']}` | {', '.join(f'`{blocker}`' for blocker in item['blockers']) or 'none'} |"
        )
        for item in audit["templates"]
    )
    completion_lines = "\n".join(
        (
            f"| {item['category']} | `{item['status']}` | {item['completion_percent']}% | "
            f"{item['default_visual_families']} | {item['default_r_ggplot2_evidence_families']} | "
            f"{item['retained_python_evidence_templates']} |"
        )
        for item in audit["completion_by_category"]
    )
    excluded_lines = "\n".join(
        (
            f"| `{item['template_id']}` | {item['category']} | {item['kind']} | "
            f"{item['renderer_family']} | `{item['reason']}` |"
        )
        for item in audit["default_surface_excluded_inventory"]
    ) or "| none | none | none | none | none |"
    reference_lines = "\n".join(
        f"- [{item['ref_id']}]({item['url']}): {item['lesson']}"
        for item in audit["external_quality_references"]
    )
    return f"""# MAS 医学论文配图 Gallery 质量审计

Owner: `MedAutoScience`
Purpose: `human_readable_quality_audit_for_display_pack_gallery`
State: `generated_support_reference`
Machine boundary: 本文由 `scripts/build-display-pack-gallery.py` 从本地 Gallery manifest 和质量审计 builder 生成。机器真相继续归 Gallery manifest、template descriptor、renderer source、layout sidecar、display lock、publication manifest、真实论文 artifact 和 owner receipt；本文不持有 publication verdict、artifact authority 或 owner receipt。MAS 不把本文发布为 tracked docs gallery；人读 compact review package 归 ScholarSkills。

## 结论

当前画册定位为 `lower_bound_reference_templates_only`：它提供统一风格、图型结构和程序化出图起点。真实论文 publication-ready 结论由 paper-local visual audit、证据引用检查和 owner receipt 签认；AI 被授权按论文具体主张自由修改结构、排版、标签、配色和组合方式来拔高上限。

- overall_status: `{audit["overall_status"]}`
- publication_ready_claim_authorized: `{str(audit["publication_ready_claim_authorized"]).lower()}`
- visual template count: `{audit["visual_template_count"]}`
- reporting flow visual template count: `{audit["reporting_flow_visual_template_count"]}`
- design visual template count: `{audit["design_visual_template_count"]}`
- table preview visual template count: `{audit["table_preview_visual_template_count"]}`
- total Gallery visual template count: `{audit["total_gallery_visual_template_count"]}`
- non-visual inventory count: `{audit["non_visual_template_count"]}`
- lower-bound review required: `{audit["lower_bound_review_required_count"]}`
- blocked evidence templates: `{audit["blocked_template_count"]}`
- blocked gallery visual templates: `{audit["gallery_visual_blocked_template_count"]}`
- publication polish policy: `{polish["policy_id"]}`
- figure workflow policy: `{workflow["policy_id"]}`
- composition recipe policy: `{composition["policy"]["policy_id"]}`
- composition recipes: `{composition["composition_recipe_count"]}`
- composition storyboard gallery pages: `{composition_gallery["composition_recipe_count"]}`

## Paper-use 前置检查

{before_paper_lines}

## 图件工作流前置检查

{workflow_before_paper_lines}

## 页面级图页方案前置检查

{composition_before_paper_lines}

## 通用科研做图 Quality Floor

- policy: `{scientific_floor["policy_id"]}`
- scope: `{scientific_floor["scope"]}`
- graphical abstract strategy: `{scientific_floor["graphical_abstract_strategy"]}`
- AI executor freedom: `{scientific_floor["ai_executor_freedom"]}`
- template library role: `{scientific_floor["template_library_role"]}`
- publication ready claim authorized: `false`

Learned patterns:

{scientific_floor_pattern_lines}

Required refs before Gallery or paper use:

{scientific_floor_required_lines}

Rebuild boundary:

{scientific_floor_rebuild_lines}

Template-library refactor decision:

- `submission_graphical_abstract`: rebuilt back onto the no-regression full-width three-panel GA skeleton after the single-canvas experiment degraded layout balance. It keeps the medical `cohort -> risk signal -> care action` story, evidence cues, SVG source, and layout-QC sidecar. It is still a refs-only lower-bound example, not paper-specific publication authority.
- `r_ggplot2_evidence_figures`: no wholesale visual redraw in this Gallery pass. Current R templates already share the publication theme/palette system; broad redraw would risk visual regression. Reuse work should continue through shared theme, legend, payload-normalization, and QC helpers with before/after screenshots.
- `cohort_flow_figure` and `table1_baseline_characteristics`: remain reporting/table previews with their own authority boundaries; do not force them into the GA visual system.

External learning sources:

{scientific_floor_source_lines}

Reference learning lessons:

{scientific_floor_reference_lines}

## 页面级图页方案

| Recipe | Title | Hero panel | Supporting | Primitive families | Programmatic evidence | Design shell |
| --- | --- | --- | ---: | ---: | --- | --- |
{composition_recipe_lines}

## 数据驱动报告流程图起点

| Template | Category | Renderer | Status | Warnings |
| --- | --- | --- | --- | --- |
{reporting_flow_lines}

## 非数据设计图起点

| Template | Category | Renderer | Status | Warnings |
| --- | --- | --- | --- | --- |
{design_lines}

## 表格预览图起点

| Template | Category | Renderer | Status | Warnings |
| --- | --- | --- | --- | --- |
{table_preview_lines}

## 高风险图族复核项

| Family | Checks |
| --- | --- |
{high_risk_lines}

## 主要阻断项

| Blocker | Templates |
| --- | ---: |
{blocker_lines}

## 主要风险项

| Warning | Templates |
| --- | ---: |
{warning_lines}

## 模板审计

| Template | Category | Renderer | Status | Blockers |
| --- | --- | --- | --- | --- |
{template_lines}

## 分类完成度

| Category | Status | Completion | Gallery visual | R/ggplot2 evidence | Current Python evidence |
| --- | --- | ---: | ---: | ---: | ---: |
{completion_lines}

## 当前 Python 数据证据模板

| Template | Category | Kind | Renderer | Reason |
| --- | --- | --- | --- | --- |
| none | none | evidence_figure | python | current_pack_retains_no_python_evidence_templates |

## 默认面排除的表格/非图像库存

| Template | Category | Kind | Renderer | Reason |
| --- | --- | --- | --- | --- |
{excluded_lines}

## 外部准则

{reference_lines}
"""
