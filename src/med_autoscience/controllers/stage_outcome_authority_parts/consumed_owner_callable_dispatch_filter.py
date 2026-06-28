from __future__ import annotations

from typing import Any

from med_autoscience.controllers.study_transition_receipt_consumption import (
    owner_callable_receipt_consumption,
)
from med_autoscience.profiles import WorkspaceProfile

from . import current_writer_handoff
from . import opl_execution_preflight


def without_consumed_owner_callable_adapters(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dispatch
        for dispatch in dispatches
        if not consumed_owner_callable_dispatch(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch,
        )
    ]


def consumed_owner_callable_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: dict[str, Any],
) -> bool:
    if opl_execution_preflight.provider_hosted_exact_stage_run_current_execution_authority(
        dispatch
    ):
        return False
    action_type = _text(dispatch.get("action_type"))
    if action_type is None:
        return False
    route = current_writer_handoff.raw_dispatch_owner_route(dispatch) or current_writer_handoff.dispatch_owner_route(
        dispatch
    )
    if not route:
        return False
    receipt = owner_callable_receipt_consumption(
        study_root=profile.studies_root / study_id,
        owner_route=route,
        actions=[{"action_type": action_type}],
    )
    if _stage_native_provider_handoff_requires_admission(dispatch) and _receipt_is_stale_transport_only(receipt):
        return False
    return bool(receipt)


def _stage_native_provider_handoff_requires_admission(dispatch: dict[str, Any]) -> bool:
    if _text(dispatch.get("action_type")) != "run_quality_repair_batch":
        return False
    if _text(dispatch.get("next_executable_owner")) != "write":
        return False
    source_action = _mapping(dispatch.get("source_action"))
    if _text(source_action.get("authority")) != "stage_native_workspace_next_action":
        return False
    route = current_writer_handoff.raw_dispatch_owner_route(dispatch) or current_writer_handoff.dispatch_owner_route(
        dispatch
    )
    refs = _mapping(route.get("source_refs"))
    if _text(refs.get("current_stage_id")) != "08-publication_package_handoff":
        return False
    if _text(refs.get("source_surface")) != "artifacts/reports/medical_publication_surface/latest.json":
        return False
    return True


def _receipt_is_stale_transport_only(receipt: dict[str, Any]) -> bool:
    if not receipt:
        return False
    if _text(receipt.get("blocked_reason")) == "progress_first_owner_redrive_budget_exhausted":
        return True
    typed_blocker = _mapping(receipt.get("typed_blocker"))
    if _text(typed_blocker.get("reason")) == "progress_first_owner_redrive_budget_exhausted":
        return True
    if _text(receipt.get("next_action")) == "honor_typed_blocker_without_redrive":
        return True
    return False


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "consumed_owner_callable_dispatch",
    "without_consumed_owner_callable_adapters",
]
