from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def owner_result_executed(owner_result: Mapping[str, Any]) -> bool:
    if owner_result_handoff_ready(owner_result):
        return True
    if _owner_result_has_blocker(owner_result):
        return False
    if owner_result.get("ok") is False:
        return False
    if owner_result.get("ok") is True:
        return True
    if _text(owner_result.get("status")) in {"executed", "skipped_duplicate_eval"}:
        return True
    if int(owner_result.get("executed_count") or 0) > 0 and int(owner_result.get("blocked_count") or 0) == 0:
        return True
    return False


def owner_result_handoff_ready(owner_result: Mapping[str, Any]) -> bool:
    if _text(owner_result.get("status")) != "handoff_ready":
        return False
    handoff = _mapping(owner_result.get("writer_worker_handoff"))
    return (
        _text(handoff.get("surface")) == "default_executor_dispatch_request"
        and _text(handoff.get("dispatch_status")) == "ready"
        and _text(handoff.get("next_executable_owner")) == "write"
    )


def owner_result_blocker(owner_result: Mapping[str, Any]) -> str:
    for execution in owner_result.get("executions") or ():
        if not isinstance(execution, Mapping):
            continue
        if reason := _text(execution.get("blocked_reason")):
            return reason
        if _text(execution.get("execution_status")) == "repeat_suppressed":
            return "repeat_suppressed"
        if why_not_applied := _text(execution.get("why_not_applied")):
            return why_not_applied
    if int(owner_result.get("repeat_suppressed_count") or 0) > 0:
        return "repeat_suppressed"
    if blocker := _first_blocker(owner_result):
        return blocker
    evidence = _mapping(owner_result.get("repair_execution_evidence"))
    if blocker := _first_blocker(evidence):
        return blocker
    manuscript_hygiene = _mapping(evidence.get("manuscript_surface_hygiene"))
    if blocker := _first_blocker(manuscript_hygiene):
        return blocker
    artifact_delta = _mapping(evidence.get("canonical_artifact_delta"))
    if _text(artifact_delta.get("status")) == "blocked":
        return "canonical_artifact_delta_blocked"
    if (
        artifact_delta.get("meaningful_artifact_delta") is False
        and manuscript_hygiene.get("story_surface_delta_required") is True
        and manuscript_hygiene.get("story_surface_delta_present") is False
    ):
        return "manuscript_story_surface_delta_missing"
    return (
        _text(owner_result.get("blocked_reason"))
        or _text(owner_result.get("reason"))
        or "owner_callable_surface_blocked"
    )


def _owner_result_has_blocker(owner_result: Mapping[str, Any]) -> bool:
    if _text(owner_result.get("status")) == "blocked":
        return True
    if _blockers(owner_result):
        return True
    evidence = _mapping(owner_result.get("repair_execution_evidence"))
    if not evidence:
        return False
    if _text(evidence.get("status")) == "blocked":
        return True
    if _blockers(evidence):
        return True
    artifact_delta = _mapping(evidence.get("canonical_artifact_delta"))
    if _text(artifact_delta.get("status")) == "blocked":
        return True
    manuscript_hygiene = _mapping(evidence.get("manuscript_surface_hygiene"))
    if _text(manuscript_hygiene.get("status")) == "blocked":
        return True
    if _blockers(manuscript_hygiene):
        return True
    return (
        artifact_delta.get("meaningful_artifact_delta") is False
        and manuscript_hygiene.get("story_surface_delta_required") is True
        and manuscript_hygiene.get("story_surface_delta_present") is False
    )


def _first_blocker(value: Mapping[str, Any]) -> str | None:
    if blocker := _blockers(value):
        return blocker[0]
    return _text(value.get("blocked_reason")) or _text(value.get("reason"))


def _blockers(value: Mapping[str, Any]) -> list[str]:
    blockers = value.get("blockers")
    if not isinstance(blockers, list):
        return []
    return [blocker for blocker in (_text(item) for item in blockers) if blocker]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["owner_result_blocker", "owner_result_executed", "owner_result_handoff_ready"]
