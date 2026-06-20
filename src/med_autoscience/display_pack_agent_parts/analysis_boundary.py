from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.display_pack_analysis_responsibility import (
    analysis_boundary_blocker,
    analysis_responsibility_allows_request,
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def analysis_template_surface_policy_flags() -> dict[str, bool]:
    return {
        "template_analysis_responsibility_required": True,
        "raw_analysis_inputs_must_match_computed_workflow_templates": True,
        "validated_summary_templates_fail_closed_on_raw_analysis_requests": True,
    }


def analysis_blocker_for_template_summary(
    template: Mapping[str, Any] | None,
    request: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not isinstance(template, Mapping):
        return None
    mode = _text(template.get("analysis_responsibility"))
    if not mode or analysis_responsibility_allows_request(mode=mode, request=request):
        return None
    return analysis_boundary_blocker(
        template_id=_text(template.get("template_id")),
        canonical_family_id=_text(template.get("canonical_family_id")),
        mode=mode,
        input_state=_text(template.get("analysis_input_state")),
        request=request,
    )


def analysis_finding_from_blocker(blocker: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "code": _text(blocker.get("blocked_reason")) or "analysis_summary_required_before_display_render",
        "template_id": _text(blocker.get("template_id")),
        "canonical_family_id": _text(blocker.get("canonical_family_id")),
        "analysis_responsibility": _mapping(blocker.get("analysis_responsibility")),
        "required_input_state": _text(blocker.get("required_input_state")),
        "request_input_state": _text(blocker.get("request_input_state")),
        "route_hint": _text(blocker.get("route_hint")),
    }


def missing_input_repair_routes(missing_inputs: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "surface_kind": "display_pack_typed_repair_route",
            "code": f"{field}_missing",
            "layer": "figure_intent",
            "repair_owner": "MedAutoScience",
            "next_callable": "provide_claim_and_data_refs",
            "blocks_render": True,
            "authority_boundary": {
                "repair_route_can_mutate_data_or_statistics": False,
                "repair_route_can_authorize_publication_readiness": False,
            },
        }
        for field in missing_inputs
    ]
