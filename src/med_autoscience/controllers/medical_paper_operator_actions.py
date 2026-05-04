from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import medical_paper_v2_materializers


SCHEMA_VERSION = 1
COMMAND_SURFACE = "medical_paper_v3_guarded_operator_command"
RESULT_SURFACE = "medical_paper_v3_guarded_operator_action_result"

ACTION_SURFACE_KEYS: dict[str, str] = {
    "run_provider_literature_scout": "literature_provider_runtime",
    "materialize_route_decision": "route_decision_orchestrator",
    "resolve_statistical_blockers": "statistical_discipline_operations",
    "start_revision_rebuttal_loop": "revision_rebuttal_loop",
    "authorize_manuscript_drafting": "authoring_runtime_authorization",
    "run_real_workspace_soak_monitor": "real_workspace_soak_monitor",
}


def guarded_operator_authority_contract() -> dict[str, Any]:
    return {
        "surface": "medical_paper_v3_operator_authority_contract",
        "schema_version": SCHEMA_VERSION,
        "guard": "existing_product_entry_controller_guard",
        "owner": "MAS_controller_product_entry",
        "execution_boundary": "guarded_operator_action",
        "can_mutate_runtime": False,
        "can_write_runtime_owned_artifacts": False,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "runtime_write_policy": "supervisor_runtime_guard_required",
    }


def guarded_operator_command(
    *,
    action_id: str,
    surface_key: str | None,
) -> dict[str, Any]:
    return {
        "surface": COMMAND_SURFACE,
        "action_id": action_id,
        "surface_key": surface_key,
        "entrypoint": "product_entry.dispatch_guarded_medical_paper_operator_action",
        "guard": "existing_product_entry_controller_guard",
        "requires": ["profile_ref", "study_id", "operator_payload"],
        "status": "guarded_pending",
    }


def guarded_pending_action_result(
    *,
    missing_reason: str | None,
    next_action: str,
) -> dict[str, Any]:
    return {
        "status": "guarded_pending",
        "durable_ref": None,
        "missing_reason": missing_reason,
        "next_action": next_action,
        "authority_contract": guarded_operator_authority_contract(),
    }


def dispatch_guarded_medical_paper_operator_action(
    *,
    study_root: Path,
    action_id: str,
    surface_key: str | None = None,
    operator_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    expected_surface_key = ACTION_SURFACE_KEYS.get(action_id)
    if expected_surface_key is None:
        return _blocked_result(
            action_id=action_id,
            surface_key=surface_key,
            missing_reason="unsupported_guarded_operator_action",
        )
    if surface_key is not None and surface_key != expected_surface_key:
        return _blocked_result(
            action_id=action_id,
            surface_key=surface_key,
            missing_reason="action_surface_mismatch",
        )
    if not operator_payload:
        return _blocked_result(
            action_id=action_id,
            surface_key=expected_surface_key,
            missing_reason="missing_operator_payload",
        )

    materialized = medical_paper_v2_materializers.materialize_medical_paper_v2_surface(
        study_root=study_root,
        surface_key=expected_surface_key,
        payload=operator_payload,
    )
    status = _text(materialized.get("status")) or "blocked"
    missing_reason = _text(materialized.get("missing_reason"))
    durable_ref = _text(materialized.get("artifact_path")) or None
    return {
        "surface": RESULT_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "action_id": action_id,
        "surface_key": expected_surface_key,
        "status": status,
        "durable_ref": durable_ref if status not in {"blocked", "missing"} else durable_ref,
        "missing_reason": missing_reason,
        "next_action": _next_action_for_status(status=status, missing_reason=missing_reason),
        "authority_contract": guarded_operator_authority_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "materializer_result": materialized,
    }


def _blocked_result(
    *,
    action_id: str,
    surface_key: str | None,
    missing_reason: str,
) -> dict[str, Any]:
    return {
        "surface": RESULT_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "action_id": action_id,
        "surface_key": surface_key,
        "status": "blocked",
        "durable_ref": None,
        "missing_reason": missing_reason,
        "next_action": "补齐 operator payload 后再通过 product-entry/controller guard 调用。",
        "authority_contract": guarded_operator_authority_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _next_action_for_status(*, status: str, missing_reason: str | None) -> str:
    if status == "ready":
        return "guarded operator action 已物化 durable surface，继续读取 readiness/progress 投影。"
    if status == "partial":
        return missing_reason or "继续补齐 partial surface 缺口。"
    return missing_reason or "operator action blocked；补齐输入后重试。"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ACTION_SURFACE_KEYS",
    "COMMAND_SURFACE",
    "RESULT_SURFACE",
    "dispatch_guarded_medical_paper_operator_action",
    "guarded_operator_authority_contract",
    "guarded_operator_command",
    "guarded_pending_action_result",
]
