from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REPEAT_SUPPRESSED_REASON = "repeat_suppressed"


def repeat_key(payload: Mapping[str, Any] | None) -> str | None:
    mapping = _mapping(payload)
    if not mapping:
        return None
    prompt_contract = _mapping(mapping.get("prompt_contract"))
    owner_route = _mapping(mapping.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    for value in (
        prompt_contract.get("repeat_suppression_key"),
        mapping.get("repeat_suppression_key"),
        owner_route.get("work_unit_fingerprint"),
        mapping.get("work_unit_fingerprint"),
    ):
        if text := _text(value):
            return text
    return None


def meaningful_artifact_delta_observed(payload: Mapping[str, Any] | None) -> bool:
    mapping = _mapping(payload)
    if not mapping:
        return False
    if mapping.get("meaningful_artifact_delta") is True:
        return True
    artifact_delta = _mapping(mapping.get("artifact_delta"))
    if _text(artifact_delta.get("latest_meaningful_delta_at")) is not None:
        return True
    return _text(mapping.get("last_meaningful_progress_at")) is not None


def scan_repeat_suppression(
    *,
    previous_payload: Mapping[str, Any] | None,
    study_id: str,
    owner_route: Mapping[str, Any],
    current_meaningful_artifact_delta: bool,
) -> dict[str, Any]:
    key = repeat_key(owner_route)
    if key is None or current_meaningful_artifact_delta:
        return _not_suppressed(key)
    for study in _list(_mapping(previous_payload).get("studies")):
        study_payload = _mapping(study)
        if _text(study_payload.get("study_id")) != study_id:
            continue
        if meaningful_artifact_delta_observed(study_payload):
            return _not_suppressed(key)
        previous_route = _mapping(study_payload.get("owner_route"))
        if repeat_key(previous_route) == key:
            return _suppressed(key, "previous_scan_same_work_unit_without_artifact_delta")
    for action in _list(_mapping(previous_payload).get("action_queue")):
        action_payload = _mapping(action)
        if _text(action_payload.get("study_id")) != study_id:
            continue
        if repeat_key(action_payload) == key:
            return _suppressed(key, "previous_scan_action_same_work_unit_without_artifact_delta")
    return _not_suppressed(key)


def dispatch_repeat_suppression(
    *,
    dispatch: Mapping[str, Any],
    current_study: Mapping[str, Any] | None,
    existing_dispatch: Mapping[str, Any] | None,
) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    if prompt_contract.get("do_not_repeat") is not True:
        return _not_suppressed(repeat_key(dispatch))
    key = repeat_key(dispatch)
    if key is None:
        return _not_suppressed(None)
    if meaningful_artifact_delta_observed(current_study):
        return _not_suppressed(key)
    existing = _mapping(existing_dispatch)
    if existing and _text(existing.get("dispatch_status")) in {"ready", "repeat_suppressed"} and repeat_key(existing) == key:
        return _suppressed(key, "existing_dispatch_same_work_unit_without_artifact_delta")
    return _not_suppressed(key)


def execution_repeat_suppression(
    *,
    dispatch: Mapping[str, Any],
    current_study: Mapping[str, Any] | None,
    previous_execution_latest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    if prompt_contract.get("do_not_repeat") is not True:
        return _not_suppressed(repeat_key(dispatch))
    key = repeat_key(dispatch)
    if key is None:
        return _not_suppressed(None)
    if meaningful_artifact_delta_observed(current_study):
        return _not_suppressed(key)
    for execution in _list(_mapping(previous_execution_latest).get("executions")):
        execution_payload = _mapping(execution)
        if repeat_key(execution_payload) == key:
            return _suppressed(key, "previous_execution_same_work_unit_without_artifact_delta")
    return _not_suppressed(key)


def _suppressed(key: str, source: str) -> dict[str, Any]:
    return {
        "repeat_suppressed": True,
        "why_not_applied": REPEAT_SUPPRESSED_REASON,
        "work_unit_fingerprint": key,
        "repeat_suppression_key": key,
        "suppression_source": source,
    }


def _not_suppressed(key: str | None) -> dict[str, Any]:
    return {
        "repeat_suppressed": False,
        "why_not_applied": None,
        "work_unit_fingerprint": key,
        "repeat_suppression_key": key,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "REPEAT_SUPPRESSED_REASON",
    "dispatch_repeat_suppression",
    "execution_repeat_suppression",
    "meaningful_artifact_delta_observed",
    "repeat_key",
    "scan_repeat_suppression",
]
