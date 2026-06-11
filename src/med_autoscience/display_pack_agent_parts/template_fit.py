from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from med_autoscience.display_pack_loader import LoadedDisplayTemplate


DEFAULT_KIND = "evidence_figure"
DEFAULT_RENDERER_PREFERENCE = "r_ggplot2"
EXACT_TEMPLATE_FIT_POLICY = "exact_descriptor_match"
ADAPTABLE_TEMPLATE_FIT_POLICY = "adaptable_baseline_not_exact_contract"

_TEMPLATE_ADAPTATION_BOUNDARY = {
    "allowed_layers": [
        "layout",
        "panel_arrangement",
        "labels_and_caption",
        "axis_scale_presentation",
        "legend_placement",
        "style_tokens",
        "facet_or_split",
        "evidence_ref_tied_annotations",
        "journal_style_profile",
        "display_payload_mapping",
    ],
    "forbidden_layers": [
        "data_values",
        "statistical_estimates",
        "model_estimates",
        "claim_content",
        "evidence_marks",
        "source_refs",
        "owner_receipt",
        "publication_readiness_verdict",
        "visual_audit_replacement",
    ],
    "required_receipts": [
        "display_pack_lock",
        "layout_qc_receipt",
        "visual_audit_receipt",
        "figure_polish_lifecycle",
    ],
}
_MINIMUM_FIT_FLOOR = {
    "hard_constraints": [
        "figure_kind_compatible",
        "explicit_template_id_match_when_requested",
        "deterministic_renderer_contract_present",
        "display_pack_descriptor_valid",
        "forbidden_authority_boundary_preserved",
    ],
    "semantic_anchor_required": True,
    "quality_floor_only": True,
    "publication_readiness_verdict": False,
}


def _text(value: object) -> str:
    return str(value or "").strip()


def payload_copy(value: Mapping[str, Any]) -> dict[str, Any]:
    return deepcopy(dict(value))


def minimum_fit_floor() -> dict[str, Any]:
    return payload_copy(_MINIMUM_FIT_FLOOR)


def _template_id_matches(record: LoadedDisplayTemplate, template_id: str) -> bool:
    manifest = record.template_manifest
    return template_id in {manifest.template_id, manifest.full_template_id}


def _template_haystack(record: LoadedDisplayTemplate) -> str:
    manifest = record.template_manifest
    return " ".join(
        (
            manifest.template_id,
            manifest.full_template_id,
            manifest.display_name,
            manifest.display_class_id,
            manifest.audit_family,
            manifest.input_schema_ref,
            " ".join(manifest.paper_family_ids),
        )
    ).lower()


def _query_matches_template(record: LoadedDisplayTemplate, request: Mapping[str, Any]) -> bool:
    query = _text(request.get("query") or request.get("figure_goal") or request.get("claim_role")).lower()
    return bool(query and query in _template_haystack(record))


def hard_compatible(record: LoadedDisplayTemplate, request: Mapping[str, Any]) -> bool:
    manifest = record.template_manifest
    kind = _text(request.get("figure_kind") or request.get("kind") or DEFAULT_KIND)
    if kind and manifest.kind != kind:
        return False
    template_id = _text(request.get("template_id"))
    if template_id and not _template_id_matches(record, template_id):
        return False
    return True


def has_semantic_fit_anchor(record: LoadedDisplayTemplate, request: Mapping[str, Any]) -> bool:
    manifest = record.template_manifest
    if _text(request.get("template_id")):
        return True
    audit_family = _text(request.get("audit_family"))
    paper_family = _text(request.get("paper_family"))
    input_schema_ref = _text(request.get("input_schema_ref"))
    query = _text(request.get("query") or request.get("figure_goal") or request.get("claim_role"))
    requested_semantics = any((audit_family, paper_family, input_schema_ref, query))
    if not requested_semantics:
        return True
    return any(
        (
            bool(audit_family and manifest.audit_family == audit_family),
            bool(paper_family and paper_family in manifest.paper_family_ids),
            bool(input_schema_ref and manifest.input_schema_ref == input_schema_ref),
            _query_matches_template(record, request),
        )
    )


def score_template(record: LoadedDisplayTemplate, request: Mapping[str, Any]) -> tuple[int, list[str]]:
    manifest = record.template_manifest
    score = 0
    reasons: list[str] = []

    preferred_renderer = _text(request.get("preferred_renderer_family") or DEFAULT_RENDERER_PREFERENCE)
    if preferred_renderer and manifest.renderer_family == preferred_renderer:
        score += 25
        reasons.append(f"preferred_renderer:{preferred_renderer}")
    if manifest.paper_proven:
        score += 20
        reasons.append("paper_proven")
    audit_family = _text(request.get("audit_family"))
    if audit_family and manifest.audit_family == audit_family:
        score += 18
        reasons.append(f"audit_family:{audit_family}")
    paper_family = _text(request.get("paper_family"))
    if paper_family and paper_family in manifest.paper_family_ids:
        score += 12
        reasons.append(f"paper_family:{paper_family}")
    input_schema_ref = _text(request.get("input_schema_ref"))
    if input_schema_ref and manifest.input_schema_ref == input_schema_ref:
        score += 10
        reasons.append(f"input_schema_ref:{input_schema_ref}")
    if _query_matches_template(record, request):
        score += 8
        reasons.append("query_match")
        query = _text(request.get("query") or request.get("figure_goal") or request.get("claim_role")).lower()
        primary_tokens = (
            manifest.template_id.lower(),
            manifest.display_name.lower(),
            manifest.display_class_id.lower(),
        )
        if any(
            token == query or token.startswith(f"{query}_") or token.startswith(f"{query} ")
            for token in primary_tokens
        ):
            score += 5
            reasons.append("query_primary_template_role")
    if manifest.golden_case_paths:
        score += 6
        reasons.append("golden_available")
    if manifest.exemplar_refs:
        score += 3
        reasons.append("exemplar_refs")
    return score, reasons


def _template_adaptation_hints(
    record: LoadedDisplayTemplate,
    request: Mapping[str, Any],
) -> list[dict[str, Any]]:
    manifest = record.template_manifest
    hints: list[dict[str, Any]] = []
    audit_family = _text(request.get("audit_family"))
    if audit_family and manifest.audit_family != audit_family:
        hints.append(
            {
                "code": "audit_family_adaptation_required",
                "layer": "medical_semantic_mapping",
                "requested": audit_family,
                "selected": manifest.audit_family,
                "allowed_action": (
                    "map the paper-specific display role onto the selected template baseline "
                    "while preserving claim/data refs"
                ),
                "blocks_render": False,
            }
        )
    paper_family = _text(request.get("paper_family"))
    if paper_family and paper_family not in manifest.paper_family_ids:
        hints.append(
            {
                "code": "paper_family_adaptation_required",
                "layer": "journal_style_profile",
                "requested": paper_family,
                "selected": list(manifest.paper_family_ids),
                "allowed_action": "apply the paper publication_style_profile and paper-local display overrides",
                "blocks_render": False,
            }
        )
    input_schema_ref = _text(request.get("input_schema_ref"))
    if input_schema_ref and manifest.input_schema_ref != input_schema_ref:
        hints.append(
            {
                "code": "input_schema_adaptation_required",
                "layer": "display_payload_mapping",
                "requested": input_schema_ref,
                "selected": manifest.input_schema_ref,
                "allowed_action": (
                    "map frozen source data into the selected template input schema without "
                    "changing source values or statistics"
                ),
                "blocks_render": False,
            }
        )
    requested_renderer = _text(request.get("renderer_family") or request.get("preferred_renderer_family"))
    if requested_renderer and manifest.renderer_family != requested_renderer:
        hints.append(
            {
                "code": "renderer_preference_adaptation_required",
                "layer": "renderer_runtime",
                "requested": requested_renderer,
                "selected": manifest.renderer_family,
                "allowed_action": (
                    "use the selected deterministic renderer or route renderer promotion "
                    "through Display Pack governance"
                ),
                "blocks_render": False,
            }
        )
    query = _text(request.get("query") or request.get("figure_goal") or request.get("claim_role"))
    if query and not _query_matches_template(record, request):
        hints.append(
            {
                "code": "composition_query_adaptation_required",
                "layer": "layout_and_composition",
                "requested": query,
                "selected": manifest.display_name,
                "allowed_action": (
                    "adapt panel composition, labels, legends, and annotations within the "
                    "selected template family"
                ),
                "blocks_render": False,
            }
        )
    return hints


def template_fit_entry(
    record: LoadedDisplayTemplate,
    request: Mapping[str, Any],
) -> dict[str, Any]:
    hints = _template_adaptation_hints(record, request)
    return {
        "template_fit_policy": ADAPTABLE_TEMPLATE_FIT_POLICY if hints else EXACT_TEMPLATE_FIT_POLICY,
        "adaptation_required": bool(hints),
        "adaptation_hints": hints,
        "adaptation_boundary": payload_copy(_TEMPLATE_ADAPTATION_BOUNDARY),
        "minimum_fit_floor": minimum_fit_floor(),
    }


def template_sort_key(item: Mapping[str, Any]) -> tuple[int, bool, bool, str]:
    return (
        int(item["recommendation_score"]),
        bool(item["paper_proven"]),
        item["renderer_family"] == DEFAULT_RENDERER_PREFERENCE,
        str(item["template_id"]),
    )
