from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.stage_outcome_authority import owner_route_policy as owner_route_part

from . import opl_execution_preflight
from . import opl_owner_callable_proof


def dispatch_has_current_execution_proof(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> bool:
    del profile, study_id
    return dispatch_has_opl_execution_proof(dispatch)


def dispatch_uses_stage_native_next_action(dispatch: Mapping[str, Any]) -> bool:
    source_action = _mapping(dispatch.get("source_action"))
    return _text(source_action.get("authority")) == "stage_native_workspace_next_action"


def dispatch_has_opl_execution_proof(dispatch: Mapping[str, Any]) -> bool:
    return (
        opl_execution_preflight.provider_hosted_exact_stage_run_current_execution_authority(
            dispatch
        )
        or opl_owner_callable_proof.trusted_owner_callable_opl_proof(dispatch) is not None
    )


def read_fresh_study_progress(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any]:
    from med_autoscience.controllers.study_progress.projection import read_study_progress

    try:
        payload = read_study_progress(
            profile=profile,
            study_id=study_id,
            sync_runtime_summary=False,
            materialize_read_model_artifacts=False,
        )
    except Exception:
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "dispatch_has_opl_execution_proof",
    "dispatch_has_current_execution_proof",
    "dispatch_owner_route",
    "dispatch_uses_stage_native_next_action",
    "read_fresh_study_progress",
]
