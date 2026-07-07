from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.display_pack_agent.composition_recipe_route import (
    composition_recipe_payload,
    select_composition_recipe,
)
from med_autoscience.display_pack_agent.scipilot_runtime_advisor import (
    build_figure_advisor_probe,
    build_figure_export_lint,
)
from med_autoscience.medical_figure_family_catalog import load_medical_figure_family_catalog


POLICY_ID = "mas_nature_skills_figure_workflow_lifecycle.v1"
COMPOSITION_POLICY_ID = "mas_medical_figure_composition_recipes.v1"
OBSERVED_NATURE_SKILLS_HEAD = "5d2ba1dee1c087be6de8f4a8aad4b27f04974be9"
OBSERVED_NATURE_SKILLS_DATE = "2026-06-20"
OBSERVED_SCIPILOT_HEAD = "43098ddb9e6a6d142218540c114f9ed38922fc42"
OBSERVED_SCIPILOT_DATE = "2026-07-05"

AUTHORITY_BOUNDARY = {
    "can_mutate_data_or_statistics": False,
    "can_authorize_publication_readiness": False,
    "can_authorize_quality_verdict": False,
    "can_replace_visual_audit": False,
    "can_replace_owner_receipt": False,
}
PAPER_MISSION_SUBORDINATION = {
    "surface_kind": "mas_paper_mission_subordination",
    "authority_owner": "MedAutoScience",
    "mainline_route": [
        "PaperMission",
        "submission_authority",
        "submission_authority_owner_gate_or_typed_blocker",
    ],
    "control_plane_role": "subordinate_input_or_advisory_only",
    "can_start_parallel_mainline": False,
    "can_bypass_submission_authority": False,
    "can_close_without_owner_gate_or_typed_blocker": False,
}

WORKFLOW_STATES = (
    "figure_brief",
    "storyboard",
    "draft_render",
    "deterministic_qc",
    "visual_audit",
    "revise_or_record_residual",
    "owner_or_publication_gate",
)

PAPER_USE_ACCEPTANCE = (
    "core_conclusion_and_evidence_chain_locked",
    "storyboard_panel_hierarchy_declared",
    "paper_local_data_and_statistics_refs_present",
    "semantic_palette_roles_resolved_from_article_style_profile",
    "rendered_artifact_inspected_at_final_size",
    "deterministic_qc_and_ai_visual_review_refs_recorded_or_residualized",
    "guide_legend_colorbar_overlap_checked_after_render",
    "revision_delta_or_residual_item_recorded",
    "visual_audit_receipt_or_residual_item_recorded",
    "owner_or_publication_gate_receipt_present_for_claim_bearing_figures",
)

DISPLAY_PACK_AGENT_RECEIPT_REFS = {
    "display_pack_lock": "paper/build/display_pack_lock.json",
    "dependency_environment_lock": "paper/build/dependency_environment_lock.json",
    "dependency_environment_receipt": "paper/build/dependency_environment_receipt.json",
    "dependency_run_context": "paper/build/dependency_run_context.json",
    "publication_manifest": "paper/build/display_pack_publication_manifest.json",
    "visual_audit_receipt": "paper/figure_visual_audit_receipt.json",
    "figure_render_receipt": "paper/figure_render_receipt.json",
    "polish_lifecycle": "paper/figure_polish_lifecycle.json",
    "figure_workflow_packet": "paper/figure_workflow_packet.json",
    "figure_provenance_index": "paper/build/provenance/figure_provenance_index.json",
}


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _query_tokens(compiled_request: Mapping[str, Any]) -> str:
    return " ".join(
        _text(compiled_request.get(key))
        for key in (
            "query",
            "audit_family",
            "medical_figure_family_id",
            "medical_figure_family_title",
            "claim_role",
            "figure_kind",
        )
    ).lower()


def _supporting_panel_roles(compiled_request: Mapping[str, Any], archetype: str) -> list[str]:
    tokens = _query_tokens(compiled_request)
    if any(token in tokens for token in ("roc", "auc", "discrimination")):
        return ["discrimination_curve", "threshold_or_reference_context", "calibration_or_utility_when_claim_requires"]
    if any(token in tokens for token in ("calibration", "decision curve", "dca", "clinical utility")):
        return ["calibration_summary", "clinical_utility_curve", "threshold_context"]
    if any(token in tokens for token in ("km", "kaplan", "survival", "time-to-event", "hazard")):
        return ["survival_curve", "risk_table", "event_or_censor_context"]
    if "forest" in tokens or "subgroup" in tokens:
        return ["effect_estimate_axis", "subgroup_labels", "uncertainty_interval_and_reference_line"]
    if "heatmap" in tokens or "matrix" in tokens or "oncoplot" in tokens:
        return ["matrix_pattern", "annotation_tracks", "fixed_color_scale"]
    if any(token in tokens for token in ("shap", "importance", "explanation")):
        return ["global_importance", "direction_or_dependence_context", "feature_label_strategy"]
    if any(token in tokens for token in ("umap", "tsne", "t-sne", "pca", "phate", "embedding")):
        return ["computed_embedding", "group_or_state_labels", "variance_or_method_context"]
    if archetype == "schematic_led_composite":
        return ["schematic_hero", "validation_panel", "source_or_process_context"]
    if archetype == "image_plate_plus_quant":
        return ["image_plate", "scale_or_channel_labels", "quantification_panel"]
    if archetype == "asymmetric_mixed_modality_figure":
        return ["claim_bearing_hero_panel", "supporting_quant_panel", "context_or_robustness_panel"]
    return ["primary_evidence_panel", "supporting_context_panel", "uncertainty_or_reference_panel"]


def _phase_status(phase: str, visual_audit_status: str = "") -> str:
    if phase == "rendered":
        if visual_audit_status == "clear":
            return "audit_clear"
        if visual_audit_status in {"findings_open", "blocked"}:
            return "residual_items_open"
        return "rendered_needs_audit"
    if phase == "blocked":
        return "blocked_needs_repair"
    return "planning_ready"


def figure_workflow_policy() -> dict[str, Any]:
    return {
        "policy_id": POLICY_ID,
        "learned_from": "Yuan1z0825/nature-skills/skills/nature-figure",
        "observed_head": OBSERVED_NATURE_SKILLS_HEAD,
        "observed_date": OBSERVED_NATURE_SKILLS_DATE,
        "adopted_patterns": [
            "figure_brief_before_code",
            "claim_led_panel_storyboard",
            "hero_panel_plus_supporting_evidence_hierarchy",
            "page_level_composition_recipes",
            "clinical_triptych",
            "schematic_led_composite",
            "asymmetric_genomics_figure",
            "dark_image_plate_plus_quantification",
            "shared_legends_and_direct_labels",
            "render_inspect_revise_before_paper_use",
            "final_size_visual_qa_receipt",
            "data_question_first_chart_selection_ref",
            "misleading_chart_warning_ref_floor",
            "programmatic_layout_qc_before_ai_visual_review",
            "design_shells_get_art_direction_not_statistical_renderer_constraints",
        ],
        "secondary_learning_sources": [
            {
                "source_project": "Haojae/scipilot-figure-skill",
                "observed_head": OBSERVED_SCIPILOT_HEAD,
                "observed_date": OBSERVED_SCIPILOT_DATE,
                "absorbed_as": "scientific_visualization_advisor_quality_floor",
                "runtime_dependency": False,
                "default_backend_dependency": False,
                "hard_gate_by_default": False,
            }
        ],
        "mas_adaptations": [
            "default_data_evidence_path_stays_r_ggplot2_and_nonblocking",
            "missing_refs_route_to_typed_repair_without_manual_gallery_browsing",
            "workflow_packet_is_quality_ceiling_guidance_not_publication_authority",
            "ai_may_redesign_panels_layout_palette_and_backend_when_truth_refs_are_preserved",
            "real_paper_visual_audit_and_owner_gate_remain_required_for_final_acceptance",
            "plot_selection_and_warning_refs_are_nonblocking_until_current_delta_requires_repair",
        ],
        "workflow_states": list(WORKFLOW_STATES),
        "paper_use_acceptance": list(PAPER_USE_ACCEPTANCE),
        "plot_selection_quality_floor": {
            "requires_question_or_claim": True,
            "requires_variable_type_and_sample_size_profile": True,
            "requires_uncertainty_or_statistical_annotation_policy": True,
            "blocks_default_evidence_progress": False,
        },
        "misleading_chart_warning_floor": [
            "small_n_mean_bar_without_points",
            "dual_y_axis_without_shared_unit_or_scatter_rationale",
            "pie_or_3d_chart_for_scientific_evidence",
            "categorical_axis_connected_as_line_without_ordered_scale_rationale",
            "rainbow_or_jet_for_ordered_scientific_data",
            "error_bar_or_interval_type_missing_from_caption",
        ],
        "composition_recipe_policy_ref": COMPOSITION_POLICY_ID,
        "composition_recipes_are_floor_not_ceiling": True,
        "paper_mission_subordination": dict(PAPER_MISSION_SUBORDINATION),
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def display_pack_agent_receipt_refs() -> dict[str, str]:
    return dict(DISPLAY_PACK_AGENT_RECEIPT_REFS)


def build_planning_figure_workflow_packet(
    *,
    request: Mapping[str, Any],
    figure_intent: Mapping[str, Any],
    recommended_template: Mapping[str, Any] | None,
    status: str,
) -> dict[str, Any]:
    return build_figure_workflow_packet(
        compiled_request=request,
        figure_contract=_mapping(figure_intent.get("figure_contract")),
        recommended_template=recommended_template,
        phase="planning" if status == "display_plan_ready" else "blocked",
    )


def build_figure_workflow_packet(
    *,
    compiled_request: Mapping[str, Any],
    figure_contract: Mapping[str, Any],
    recommended_template: Mapping[str, Any] | None = None,
    phase: str = "planning",
    visual_audit_status: str = "",
    receipt_refs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = _mapping(figure_contract)
    request = _mapping(compiled_request)
    template = _mapping(recommended_template)
    panel_logic = _mapping(contract.get("panel_logic"))
    backend_policy = _mapping(contract.get("backend_policy"))
    archetype = _text(panel_logic.get("archetype")) or "quantitative_grid"
    claim_ref = _text(request.get("claim_ref") or contract.get("claim_ref"))
    data_ref = _text(request.get("data_ref") or contract.get("data_ref"))
    figure_id = _text(request.get("figure_id")) or "planned_figure"
    family_id = _text(request.get("medical_figure_family_id"))
    family_title = _text(request.get("medical_figure_family_title"))
    template_id = _text(template.get("template_id") or request.get("template_id"))
    full_template_id = _text(template.get("full_template_id") or template_id)
    catalog = load_medical_figure_family_catalog()
    composition_recipe = select_composition_recipe(request, catalog)
    composition = composition_recipe_payload(composition_recipe)
    advisor_probe = build_figure_advisor_probe(compiled_request=request, figure_contract=contract)
    export_lint = build_figure_export_lint(compiled_request=request, receipt_refs=receipt_refs)
    supporting_roles = [composition_recipe.hero_panel_role, *composition_recipe.supporting_panel_roles]
    if not supporting_roles:
        supporting_roles = _supporting_panel_roles(request, archetype)
    missing_refs = [
        field
        for field, value in {
            "claim_ref": claim_ref,
            "data_ref": data_ref,
        }.items()
        if not value
    ]
    return {
        "schema_version": 1,
        "surface_kind": "display_pack_figure_workflow_packet",
        "packet_id": f"display-pack-workflow-{figure_id}",
        "policy_ref": POLICY_ID,
        "workflow_status": _phase_status(phase, visual_audit_status),
        "phase": phase,
        "nonblocking_progress_policy": {
            "blocks_default_evidence_progress": False,
            "manual_template_browsing_required": False,
            "missing_refs_route_to_typed_repair": True,
            "paper_use_acceptance_required_before_final_claim": True,
        },
        "paper_mission_subordination": dict(PAPER_MISSION_SUBORDINATION),
        "figures": [
            {
                "figure_id": figure_id,
                "figure_brief": {
                    "core_conclusion": _text(contract.get("core_conclusion")),
                    "claim_ref": claim_ref,
                    "data_ref": data_ref,
                    "target_journal_or_output": _text(request.get("paper_target")) or "paper_local_target",
                    "figure_family_id": family_id,
                    "figure_family_title": family_title,
                    "figure_archetype": archetype,
                    "selected_backend": _text(backend_policy.get("selected_backend")),
                    "design_track": "data_evidence_programmatic" if request.get("figure_kind") != "illustration_shell" else "design_or_flow_expression",
                    "plot_selection_ref": _text(request.get("plot_selection_ref")),
                    "variable_profile_ref": _text(request.get("variable_profile_ref")),
                },
                "plot_selection_quality_floor": {
                    "question_or_claim_present": bool(_text(contract.get("core_conclusion")) or claim_ref),
                    "variable_profile_ref": _text(request.get("variable_profile_ref")),
                    "group_sample_size_ref": _text(request.get("group_sample_size_ref")),
                    "plot_selection_ref": _text(request.get("plot_selection_ref")),
                    "warning_ref": _text(request.get("graph_warnings_ref") or request.get("figure_warning_ref")),
                    "blocks_unrelated_progress": False,
                    "missing_items_route": "repair_hint_or_current_delta_typed_repair_only",
                },
                "figure_advisor_probe": advisor_probe,
                "storyboard": {
                    "composition_recipe": composition,
                    "hero_panel": supporting_roles[0],
                    "supporting_panel_roles": supporting_roles[1:],
                    "panel_drop_policy": "drop_or_merge_panels_without_unique_evidence",
                    "guide_strategy": composition_recipe.guide_strategy,
                    "label_strategy": composition_recipe.label_strategy,
                    "default_layout": composition_recipe.default_layout,
                    "layout_hierarchy": "hero_panel_first_when_claim_has_primary_evidence",
                    "programmatic_evidence_required": composition_recipe.programmatic_evidence_required,
                    "design_shell_allowed": composition_recipe.design_shell_allowed,
                    "ai_may_change": list(composition_recipe.ai_may_change),
                    "ai_must_preserve": list(composition_recipe.ai_must_preserve),
                    "starter_template": {
                        "template_id": template_id,
                        "full_template_id": full_template_id,
                        "canonical_family_id": _text(template.get("canonical_family_id")),
                        "quality_floor_only": True,
                    },
                },
                "render_inspect_revise": {
                    "loop_states": list(WORKFLOW_STATES[2:]),
                    "inspect_at_final_size": True,
                    "required_receipt_refs": [
                        "paper/figure_render_receipt.json",
                        "paper/figure_visual_audit_receipt.json",
                        "paper/figure_polish_lifecycle.json",
                    ],
                    "qa_split": {
                        "deterministic_qc": [
                            "glyph_or_missing_font_warning",
                            "text_clipping",
                            "tick_label_overlap",
                            "export_format_and_final_size",
                        ],
                        "ai_visual_review": [
                            "legend_or_annotation_occlusion",
                            "panel_label_alignment",
                            "grayscale_or_colorblind_discrimination",
                            "visible_claim_matches_evidence_refs",
                        ],
                        "both_are_evidence_refs_not_publication_authority": True,
                    },
                    "figure_export_lint": export_lint,
                    "revision_record_required": True,
                    "next_action": "display-pack-render" if not missing_refs else "display-pack-repair",
                    "receipt_refs": dict(receipt_refs or {}),
                },
                "paper_use_acceptance": {
                    "required_before_paper_use": list(PAPER_USE_ACCEPTANCE),
                    "missing_contract_items": missing_refs,
                    "real_paper_visual_audit_required": True,
                    "owner_or_publication_gate_required": True,
                    "publication_readiness_authorized": False,
                },
            }
        ],
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def build_rendered_figure_workflow_packet(
    *,
    figure_entries: list[Mapping[str, Any]],
    audit_receipt: Mapping[str, Any],
    receipt_refs: Mapping[str, Any],
) -> dict[str, Any]:
    figures: list[dict[str, Any]] = []
    visual_status = _text(audit_receipt.get("final_status"))
    for entry in figure_entries:
        rendered = _mapping(entry.get("rendered_artifacts"))
        deterministic_qc = _mapping(entry.get("deterministic_qc"))
        request = {
            "figure_id": entry.get("figure_id"),
            "claim_ref": entry.get("claim_ref"),
            "data_ref": entry.get("data_ref"),
            "figure_kind": entry.get("figure_kind"),
            "template_id": entry.get("short_template_id") or entry.get("template_id"),
            "paper_target": "paper_local_target",
        }
        contract = {
            "core_conclusion": _text(entry.get("claim_ref")) or _text(entry.get("figure_id")),
            "panel_logic": {"archetype": "quantitative_grid", "hero_panel_preferred": True},
            "backend_policy": {"selected_backend": entry.get("renderer_family")},
        }
        base = build_figure_workflow_packet(
            compiled_request=request,
            figure_contract=contract,
            recommended_template={
                "template_id": entry.get("short_template_id"),
                "full_template_id": entry.get("template_id"),
            },
            phase="rendered",
            visual_audit_status=visual_status,
            receipt_refs=receipt_refs,
        )["figures"][0]
        base["render_inspect_revise"].update(
            {
                "rendered_artifact_refs": [
                    _text(rendered.get("png_ref")),
                    _text(rendered.get("pdf_ref")),
                ],
                "layout_sidecar_ref": _text(rendered.get("layout_sidecar_ref")),
                "deterministic_qc_ref": _text(deterministic_qc.get("ref")),
                "visual_audit_final_status": visual_status,
            }
        )
        figures.append(base)
    return {
        "schema_version": 1,
        "surface_kind": "display_pack_figure_workflow_packet",
        "packet_id": "display-pack-rendered-workflow",
        "policy_ref": POLICY_ID,
        "workflow_status": _phase_status("rendered", visual_status),
        "phase": "rendered",
        "nonblocking_progress_policy": {
            "blocks_default_evidence_progress": False,
            "manual_template_browsing_required": False,
            "paper_use_acceptance_required_before_final_claim": True,
        },
        "paper_mission_subordination": dict(PAPER_MISSION_SUBORDINATION),
        "figures": figures,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }
