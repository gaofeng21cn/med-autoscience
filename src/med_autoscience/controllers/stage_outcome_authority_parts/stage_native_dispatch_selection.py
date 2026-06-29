from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import opl_domain_progress_transition_contract
from med_autoscience.controllers import stage_native_next_action_admission
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part

from . import opl_execution_preflight
from . import opl_owner_callable_proof


def next_action(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any] | None:
    del profile, study_id
    return None


def next_action_matches_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> bool:
    del profile, study_id
    if dispatch_has_canonical_next_action_envelope(dispatch):
        return True
    return False


def next_action_has_opl_execution_proof(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> bool:
    del profile, study_id
    return dispatch_has_canonical_next_action_envelope(dispatch) and dispatch_has_opl_execution_proof(dispatch)


def without_unauthorized_dispatches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dispatch
        for dispatch in dispatches
        if not dispatch_uses_stage_native_next_action(dispatch)
        or next_action_matches_dispatch(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch,
        )
    ]


def dispatch_uses_stage_native_next_action(dispatch: Mapping[str, Any]) -> bool:
    return stage_native_next_action_admission.dispatch_uses_stage_native_next_action(dispatch)


def dispatch_has_canonical_next_action_envelope(dispatch: Mapping[str, Any]) -> bool:
    return opl_domain_progress_transition_contract.next_action_identity_complete(
        _dispatch_next_action(dispatch)
    )


def dispatch_has_opl_execution_proof(dispatch: Mapping[str, Any]) -> bool:
    return (
        opl_execution_preflight.provider_hosted_exact_stage_run_current_execution_authority(
            dispatch
        )
        or opl_owner_callable_proof.trusted_owner_callable_opl_proof(dispatch) is not None
    )


def read_fresh_study_progress(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any]:
    try:
        from med_autoscience.controllers import study_progress

        payload = study_progress.read_study_progress(
            profile=profile,
            study_id=study_id,
            sync_runtime_summary=False,
            materialize_read_model_artifacts=False,
            enable_opl_live_provider_attempt_probe=False,
        )
    except Exception:
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )


def _dispatch_next_action(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action"))
    handoff = _mapping(dispatch.get("handoff_packet"))
    return (
        _mapping(dispatch.get("next_action"))
        or _mapping(prompt_contract.get("next_action"))
        or _mapping(source_action.get("next_action"))
        or _mapping(handoff.get("next_action"))
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "dispatch_has_opl_execution_proof",
    "dispatch_has_canonical_next_action_envelope",
    "dispatch_owner_route",
    "dispatch_uses_stage_native_next_action",
    "next_action",
    "next_action_has_opl_execution_proof",
    "next_action_matches_dispatch",
    "read_fresh_study_progress",
    "without_unauthorized_dispatches",
]
