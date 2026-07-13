from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy import (
    normalize_currentness_sources,
)


def build_ai_route_context(
    *,
    study_id: str,
    action_type: str,
    quest_id: str | None = None,
    work_unit_id: str | None = None,
    work_unit_fingerprint: str | None = None,
    next_owner: str | None = None,
    policy_kind: str | None = None,
    source_generation: str | None = None,
    expected_version: str | None = None,
    dispatch_ref: str | None = None,
    dispatch_authority: str | None = None,
    required_output_surface: str | None = None,
    currentness_basis: Mapping[str, Any] | None = None,
    idempotency_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build non-authoritative context for Codex to choose the next declared stage."""
    return _clean(
        {
            "surface_kind": "mas_ai_route_context",
            "schema_version": 1,
            "route_selection_owner": "codex_cli",
            "study_id": study_id,
            "quest_id": quest_id or study_id,
            "current_action_type": action_type,
            "candidate_stage_or_action": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_owner_hint": next_owner,
            "route_hint_kind": policy_kind,
            "source_generation": source_generation or work_unit_fingerprint,
            "expected_version": expected_version,
            "dispatch_ref": dispatch_ref,
            "dispatch_authority": dispatch_authority,
            "required_output_surface": required_output_surface,
            "currentness_basis": normalize_currentness_sources(currentness_basis),
            "idempotency_context": dict(idempotency_context or {}),
            "progress_first": {
                "artifact_is_next_stage_input": True,
                "negative_result_is_evidence": True,
                "route_may_skip_repeat_reverse_or_target_any_declared_stage": True,
                "route_back_preserves_failed_path_lineage": True,
                "blocks_stage_transition": False,
            },
            "authority_boundary": {
                "context_can_select_route": False,
                "context_can_reject_codex_route": False,
                "context_can_create_typed_blocker": False,
                "context_can_authorize_quality_or_publication": False,
                "opl_can_run_semantic_transition_controller": False,
            },
        }
    )


def _clean(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


def is_nonbinding_codex_route_context(value: Mapping[str, Any]) -> bool:
    surface_kind = value.get("surface_kind")
    if surface_kind == "mas_ai_route_context":
        return value.get("route_selection_owner") == "codex_cli"
    if surface_kind != "mas_next_action_envelope":
        return False
    boundary = value.get("authority_boundary")
    boundary = boundary if isinstance(boundary, Mapping) else {}
    return (
        boundary.get("next_action_authority") is False
        and boundary.get("route_selection_owner") == "codex_cli"
        and boundary.get("action_family_authority") is False
    )


__all__ = ["build_ai_route_context", "is_nonbinding_codex_route_context"]
