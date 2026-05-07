from __future__ import annotations

from typing import Any

from med_autoscience.native_runtime_event import NativeRuntimeEventRecord
from med_autoscience.runtime_event_record import RuntimeEventRecordRef
from med_autoscience.startup_contract import stable_startup_contract


def _normalize_stable_bash_session_entry(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    bash_id = str(payload.get("bash_id") or "").strip()
    status = str(payload.get("status") or "").strip()
    if not bash_id or not status:
        raise RuntimeError("stable bash session contract requires `bash_id` and `status`")
    return dict(payload)


def _normalize_stable_quest_session(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    quest_id = str(payload.get("quest_id") or "").strip()
    snapshot = payload.get("snapshot")
    runtime_audit = payload.get("runtime_audit")
    if not quest_id or not isinstance(snapshot, dict) or not isinstance(runtime_audit, dict):
        raise RuntimeError("missing stable quest session contract")
    required_runtime_audit_keys = {
        "ok",
        "status",
        "source",
        "active_run_id",
        "worker_running",
        "worker_pending",
        "stop_requested",
    }
    if not required_runtime_audit_keys.issubset(runtime_audit):
        raise RuntimeError("missing stable quest session contract")
    normalized_payload = dict(payload)
    runtime_event_ref_payload = payload.get("runtime_event_ref")
    runtime_event_payload = payload.get("runtime_event")
    normalized_runtime_event_ref: dict[str, str] | None = None
    normalized_runtime_event: dict[str, Any] | None = None
    runtime_event_contract_errors: dict[str, str] = {}
    if runtime_event_ref_payload is not None:
        try:
            normalized_runtime_event_ref = RuntimeEventRecordRef.from_payload(runtime_event_ref_payload).to_dict()
        except (TypeError, ValueError) as exc:
            runtime_event_contract_errors["runtime_event_ref_contract_error"] = str(exc)
    if runtime_event_payload is not None:
        try:
            native_runtime_event = NativeRuntimeEventRecord.from_payload(runtime_event_payload)
            if native_runtime_event.quest_id != quest_id:
                raise ValueError("stable quest session runtime_event quest_id mismatch")
        except (TypeError, ValueError) as exc:
            runtime_event_contract_errors["runtime_event_contract_error"] = str(exc)
            normalized_runtime_event_ref = None
        else:
            normalized_runtime_event = native_runtime_event.to_dict()
            native_runtime_event_ref: dict[str, str] | None = None
            try:
                native_runtime_event_ref = native_runtime_event.ref().to_dict()
            except ValueError:
                native_runtime_event_ref = None
            if (
                normalized_runtime_event_ref is not None
                and native_runtime_event_ref is not None
                and native_runtime_event_ref != normalized_runtime_event_ref
            ):
                runtime_event_contract_errors["runtime_event_ref_contract_error"] = (
                    "stable quest session runtime_event_ref mismatch against runtime_event"
                )
            if native_runtime_event_ref is not None:
                normalized_runtime_event_ref = native_runtime_event_ref
    if normalized_runtime_event_ref is not None:
        normalized_payload["runtime_event_ref"] = normalized_runtime_event_ref
    else:
        normalized_payload.pop("runtime_event_ref", None)
    if normalized_runtime_event is not None:
        normalized_payload["runtime_event"] = normalized_runtime_event
    else:
        normalized_payload.pop("runtime_event", None)
    normalized_payload.update(runtime_event_contract_errors)
    return normalized_payload


def _normalize_stable_quest_create_result(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    snapshot = payload.get("snapshot")
    if payload.get("ok") is not True or not isinstance(snapshot, dict) or not str(snapshot.get("quest_id") or "").strip():
        raise RuntimeError("missing stable quest create contract")
    return dict(payload)


def _normalize_stable_startup_context_result(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    snapshot = payload.get("snapshot")
    quest_id = str(payload.get("quest_id") or "").strip()
    if payload.get("ok") is not True or not isinstance(snapshot, dict):
        raise RuntimeError("missing stable startup-context contract")
    if not quest_id:
        quest_id = str(snapshot.get("quest_id") or "").strip()
    if not quest_id:
        raise RuntimeError("missing stable startup-context contract")
    try:
        startup_contract = _normalize_startup_contract_for_stable_transport(
            startup_contract=snapshot.get("startup_contract")
        )
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    if not isinstance(startup_contract, dict):
        raise RuntimeError("missing stable startup-context contract")
    normalized_snapshot = dict(snapshot)
    normalized_snapshot["startup_contract"] = startup_contract
    normalized_payload = dict(payload)
    normalized_payload["snapshot"] = normalized_snapshot
    return normalized_payload


def _normalize_stable_quest_control_result(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    quest_id = str(payload.get("quest_id") or "").strip()
    action = str(payload.get("action") or "").strip()
    snapshot = payload.get("snapshot")
    status = str(payload.get("status") or (snapshot.get("status") if isinstance(snapshot, dict) else "") or "").strip()
    if payload.get("ok") is not True or not quest_id or not action or not isinstance(snapshot, dict) or not status:
        raise RuntimeError("missing stable quest control contract")
    return dict(payload)


def _normalize_stable_artifact_completion_result(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    snapshot = payload.get("snapshot")
    summary_refresh = payload.get("summary_refresh")
    status = str(payload.get("status") or "").strip()
    if payload.get("ok") is not True or not isinstance(snapshot, dict) or not isinstance(summary_refresh, dict) or not status:
        raise RuntimeError("missing stable artifact completion contract")
    return dict(payload)


def _normalize_startup_contract_for_stable_transport(
    *,
    startup_contract: dict[str, Any] | None | object,
    unset: object | None = None,
) -> dict[str, Any] | None | object:
    if startup_contract is unset or startup_contract is None:
        return startup_contract
    if not isinstance(startup_contract, dict):
        raise ValueError("startup_contract must be a mapping or null")
    return stable_startup_contract(startup_contract)
