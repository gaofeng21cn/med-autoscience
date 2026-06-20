from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.display_pack_agent_parts.template_fit import (
    DEFAULT_KIND,
    DEFAULT_RENDERER_PREFERENCE,
)
from med_autoscience.display_pack_agent_parts.publication_polish_policy import (
    publication_polish_policy,
)
from med_autoscience.display_pack_agent_parts.query_family_route import resolve_query_family_route
from med_autoscience.medical_figure_family_catalog import load_medical_figure_family_catalog


DEFAULT_AUDIT_FAMILY = "Prediction Performance"
DEFAULT_AUTHORITY_BOUNDARY = {
    "can_mutate_data_or_statistics": False,
    "can_authorize_publication_readiness": False,
    "can_replace_visual_audit": False,
    "can_replace_owner_receipt": False,
    "can_emit_display_refs_and_receipts": True,
}

NATURE_SKILLS_OBSERVED_HEAD = "5d2ba1dee1c087be6de8f4a8aad4b27f04974be9"
NATURE_SKILLS_OBSERVED_DATE = "2026-06-20"

FIGURE_CONTRACT_POLICY = {
    "policy_id": "mas_nature_skills_informed_figure_contract.v1",
    "learned_from": "Yuan1z0825/nature-skills/skills/nature-figure",
    "observed_head": NATURE_SKILLS_OBSERVED_HEAD,
    "observed_date": NATURE_SKILLS_OBSERVED_DATE,
    "adopted_patterns": [
        "core_conclusion_before_plotting",
        "evidence_chain_maps_panels_to_claim",
        "figure_archetype_first_layout",
        "backend_exclusive_render_export_receipt",
        "journal_export_contract_before_styling",
        "final_visual_qa_after_render",
    ],
    "mas_adaptations": [
        "r_ggplot2_is_default_for_data_evidence",
        "no_python_or_r_question_on_default_mas_evidence_path",
        "query_resolves_through_medical_figure_family_catalog_before_template_scoring",
        "missing_refs_become_typed_repair_routes_not_manual_template_browsing",
        "starter_template_is_quality_floor_not_ceiling",
        "ai_may_redesign_layout_palette_panel_structure_and_backend_when_semantics_are_preserved",
    ],
    "rejected_patterns": [
        {
            "pattern": "backend_choice_blocks_every_figure_request",
            "reason": "MAS evidence figures must keep the autonomous path smooth; default evidence routing uses R/ggplot2 and only routes Python when explicitly justified.",
        },
        {
            "pattern": "vendor_skill_runner_or_default_skill_source",
            "reason": "Nature-Skills remains a clean-room learning source, not a MAS runtime, selector, or publication authority.",
        },
    ],
    "machine_boundary": (
        "planning_and_quality_floor_policy_only_not_renderer_not_publication_verdict_"
        "not_statistical_truth_not_visual_audit_replacement"
    ),
}

JOURNAL_EXPORT_CONTRACT = {
    "editable_text_required": True,
    "vector_export_preferred": True,
    "required_export_formats": ["pdf", "png"],
    "paper_facing_export_formats": ["svg_or_pdf", "tiff_or_png_preview"],
    "final_size_policy": "check_at_target_single_or_double_column_width_before_publication_use",
    "font_policy": "Arial_or_Helvetica_family_consistent_5_to_8pt_at_final_size",
    "line_weight_policy": "thin_axes_and_guides_with_sufficient_print_readability",
    "panel_label_policy": "bold_lowercase_near_top_left_when_multipanel",
}

VISUAL_QA_REQUIREMENTS = [
    "core_conclusion_present",
    "every_panel_maps_to_claim_or_is_removed",
    "claim_data_and_statistics_refs_present",
    "selected_backend_used_for_render_preview_export_and_qa",
    "no_text_or_legend_overlap_at_final_size",
    "shared_or_direct_labels_when_repeated_legends_would_crowd",
    "palette_roles_match_data_semantics",
    "colorblind_and_grayscale_interpretability_checked",
    "vector_or_high_resolution_export_available",
    "layout_sidecar_or_visual_audit_receipt_present",
    "publication_readiness_not_authorized_by_template_or_gallery",
]


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _current_delta_text(delta: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = _text(delta.get(key))
        if value:
            return value
    owner_route = _mapping(delta.get("owner_route"))
    for key in keys:
        value = _text(owner_route.get(key))
        if value:
            return value
    return ""


def _infer_audit_family(intent_text: str, delta: Mapping[str, Any], request: Mapping[str, Any]) -> str:
    explicit = _text(request.get("audit_family"))
    if explicit:
        return explicit
    lowered = " ".join(
        [
            intent_text,
            _current_delta_text(delta, "action_type", "action_id", "work_unit_id"),
            " ".join(_text_list(delta.get("route_required_ref_families"))),
            " ".join(_text_list(delta.get("capability_families"))),
        ]
    ).lower()
    if any(token in lowered for token in ("roc", "auc", "calibration", "decision curve", "dca", "prediction")):
        return "Prediction Performance"
    if any(token in lowered for token in ("survival", "kaplan", "hazard", "time-to-event")):
        return "Time-to-event"
    if any(token in lowered for token in ("forest", "subgroup", "effect", "odds ratio", "hazard ratio")):
        return "Effects"
    if any(token in lowered for token in ("baseline table", "table one", "characteristics")):
        return "Table"
    return DEFAULT_AUDIT_FAMILY


def _infer_query(intent_text: str, audit_family: str, delta: Mapping[str, Any], request: Mapping[str, Any]) -> str:
    explicit = _text(request.get("query"))
    if explicit:
        return explicit
    lowered = " ".join(
        [
            intent_text,
            audit_family,
            _current_delta_text(delta, "action_type", "work_unit_id", "desired_delta"),
        ]
    ).lower()
    for token in ("roc", "calibration", "dca", "decision", "km", "kaplan", "forest", "nomogram", "baseline"):
        if token in lowered:
            return "decision curve" if token == "decision" else token
    if audit_family == "Prediction Performance":
        return "roc"
    return audit_family.lower()


def _infer_archetype(figure_kind: str, audit_family: str, query: str) -> str:
    lowered = " ".join((figure_kind, audit_family, query)).lower()
    if any(token in lowered for token in ("flow", "graphical abstract", "schematic")):
        return "schematic_led_composite"
    if any(token in lowered for token in ("image", "microscopy", "blot", "histology", "spatial")):
        return "image_plate_plus_quant"
    if any(token in lowered for token in ("composite", "generalizability", "multi", "dashboard")):
        return "asymmetric_mixed_modality_figure"
    return "quantitative_grid"


def figure_contract_policy() -> dict[str, Any]:
    return {
        **FIGURE_CONTRACT_POLICY,
        "journal_export_contract": dict(JOURNAL_EXPORT_CONTRACT),
        "visual_qa_requirements": list(VISUAL_QA_REQUIREMENTS),
        "authority_boundary": dict(DEFAULT_AUTHORITY_BOUNDARY),
        "publication_polish_policy": publication_polish_policy(),
    }


def _backend_policy_for_request(figure_kind: str, preferred_renderer: str) -> dict[str, Any]:
    if figure_kind == DEFAULT_KIND:
        selected = preferred_renderer or DEFAULT_RENDERER_PREFERENCE
        if selected != DEFAULT_RENDERER_PREFERENCE:
            return {
                "selected_backend": selected,
                "default_backend": DEFAULT_RENDERER_PREFERENCE,
                "backend_gate": "explicit_non_default_backend_requires_documented_advantage_and_visual_audit",
                "backend_exclusivity_required": True,
                "blocks_agent_progress": False,
            }
        return {
            "selected_backend": DEFAULT_RENDERER_PREFERENCE,
            "default_backend": DEFAULT_RENDERER_PREFERENCE,
            "backend_gate": "r_ggplot2_default_for_mas_data_evidence_no_user_question_required",
            "backend_exclusivity_required": True,
            "blocks_agent_progress": False,
        }
    return {
        "selected_backend": preferred_renderer or "composition_or_svg",
        "default_backend": "composition_or_svg",
        "backend_gate": "design_flow_shells_may_use_svg_python_composition_or_imagegen_art_direction",
        "backend_exclusivity_required": False,
        "blocks_agent_progress": False,
    }


def _build_figure_contract(
    *,
    intent_text: str,
    compiled_request: Mapping[str, Any],
) -> dict[str, Any]:
    figure_kind = _text(compiled_request.get("figure_kind")) or DEFAULT_KIND
    audit_family = _text(compiled_request.get("audit_family")) or DEFAULT_AUDIT_FAMILY
    query = _text(compiled_request.get("query"))
    claim_ref = _text(compiled_request.get("claim_ref"))
    data_ref = _text(compiled_request.get("data_ref"))
    preferred_renderer = _text(compiled_request.get("preferred_renderer_family")) or DEFAULT_RENDERER_PREFERENCE
    core_conclusion = _text(
        compiled_request.get("core_conclusion")
        or compiled_request.get("claim_role")
        or intent_text
        or "display_current_owner_delta"
    )
    return {
        "schema_version": 1,
        "contract_id": "mas_display_figure_contract.v1",
        "policy_ref": FIGURE_CONTRACT_POLICY["policy_id"],
        "core_conclusion": core_conclusion,
        "evidence_chain": [
            {
                "role": "claim",
                "ref": claim_ref,
                "required": True,
                "status": "present" if claim_ref else "missing",
            },
            {
                "role": "source_data_or_statistics",
                "ref": data_ref,
                "required": True,
                "status": "present" if data_ref else "missing",
            },
        ],
        "panel_logic": {
            "archetype": _infer_archetype(figure_kind, audit_family, query),
            "hero_panel_preferred": True,
            "drop_panels_without_unique_evidence": True,
            "direct_labels_preferred_when_legends_would_crowd": True,
        },
        "backend_policy": _backend_policy_for_request(figure_kind, preferred_renderer),
        "journal_export_contract": dict(JOURNAL_EXPORT_CONTRACT),
        "visual_qa_requirements": list(VISUAL_QA_REQUIREMENTS),
        "publication_polish_policy_ref": publication_polish_policy()["policy_id"],
        "publication_polish_required_before_paper_use": publication_polish_policy()[
            "required_before_paper_use"
        ],
        "missing_contract_items": [
            item["role"]
            for item in [
                {"role": "claim_ref", "present": bool(claim_ref)},
                {"role": "data_ref", "present": bool(data_ref)},
            ]
            if not item["present"]
        ],
        "agent_progress_policy": {
            "manual_template_browsing_required": False,
            "backend_question_required_for_default_mas_evidence_path": False,
            "missing_refs_route_to_typed_repair": True,
            "templates_are_lower_bound_floor_not_ceiling": True,
        },
        "authority_boundary": dict(DEFAULT_AUTHORITY_BOUNDARY),
    }


def compile_display_figure_intent(
    *,
    current_owner_delta: Mapping[str, Any] | None = None,
    claim_ref: str = "",
    data_ref: str = "",
    paper_target: str = "",
    intent: str = "",
    figure_request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    delta = _mapping(current_owner_delta)
    request = dict(figure_request or {})
    intent_text = _text(
        intent
        or request.get("intent")
        or request.get("figure_goal")
        or request.get("claim_role")
        or _current_delta_text(delta, "display_intent", "desired_delta", "summary", "action_type")
    )
    resolved_claim_ref = _text(claim_ref or request.get("claim_ref") or delta.get("claim_ref"))
    resolved_data_ref = _text(data_ref or request.get("data_ref") or delta.get("data_ref"))
    audit_family = _infer_audit_family(intent_text, delta, request)
    figure_kind = _text(request.get("figure_kind") or request.get("kind") or DEFAULT_KIND)
    compiled_request = {
        **request,
        "figure_kind": figure_kind,
        "audit_family": audit_family,
        "preferred_renderer_family": _text(
            request.get("preferred_renderer_family") or DEFAULT_RENDERER_PREFERENCE
        ),
        "query": _infer_query(intent_text, audit_family, delta, request),
        "claim_ref": resolved_claim_ref,
        "data_ref": resolved_data_ref,
        "paper_target": _text(paper_target or request.get("paper_target") or delta.get("paper_target")),
        "claim_role": _text(request.get("claim_role") or intent_text or "display_current_owner_delta"),
    }
    query_family_route = resolve_query_family_route(
        compiled_request,
        load_medical_figure_family_catalog(),
    )
    if query_family_route is not None:
        compiled_request.update(query_family_route.as_request_patch())
    if _text(request.get("template_id")):
        compiled_request["template_id"] = _text(request.get("template_id"))
    figure_contract = _build_figure_contract(
        intent_text=intent_text,
        compiled_request=compiled_request,
    )
    return {
        "schema_version": 1,
        "surface_kind": "display_pack_agent_figure_intent",
        "status": "compiled",
        "planning_root": "current_owner_delta",
        "current_owner_delta": {
            "action_type": _current_delta_text(delta, "action_type", "action_id"),
            "owner": _current_delta_text(delta, "owner"),
            "work_unit_id": _current_delta_text(delta, "work_unit_id"),
            "work_unit_fingerprint": _current_delta_text(delta, "work_unit_fingerprint"),
            "source_ref": _current_delta_text(delta, "source_ref"),
        },
        "claim_ref": resolved_claim_ref,
        "data_ref": resolved_data_ref,
        "paper_target": compiled_request["paper_target"],
        "intent_text": intent_text,
        "compiled_figure_request": compiled_request,
        "figure_contract": figure_contract,
        "figure_contract_policy": figure_contract_policy(),
        "missing_inputs": [
            field
            for field, value in {
                "claim_ref": resolved_claim_ref,
                "data_ref": resolved_data_ref,
            }.items()
            if not value
        ],
        "authority_boundary": dict(DEFAULT_AUTHORITY_BOUNDARY),
    }
