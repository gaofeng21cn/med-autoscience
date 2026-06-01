from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


ENVELOPE_KEYS = (
    "state_kind",
    "owner",
    "next_work_unit",
    "typed_blocker",
    "parked_state",
    "source_refs",
    "conflict_suppression_refs",
    "authority_boundary",
)
ALLOWED_STATE_KINDS = ("parked", "executable_owner_action", "typed_blocker")
EVIDENCE_ONLY_SURFACES = ("action_queue", "runtime_health", "no_op")
AUTHORITY_BOUNDARY = {
    "surface_kind": "current_execution_envelope",
    "authority": "read_model_projection",
    "top_level_truth": "state_kind",
    "allowed_state_kinds": list(ALLOWED_STATE_KINDS),
    "evidence_only_surfaces": list(EVIDENCE_ONLY_SURFACES),
}


def build_current_execution_envelope(
    *,
    status: Mapping[str, Any] | None = None,
    progress: Mapping[str, Any] | None = None,
    actions: Sequence[Mapping[str, Any]] | None = None,
    blocked_reason: str | None = None,
    next_owner: str | None = None,
    typed_blocker: Mapping[str, Any] | None = None,
    runtime_health: Mapping[str, Any] | None = None,
    source_refs: Sequence[str] | None = None,
    conflict_suppression_refs: Sequence[str] | None = None,
) -> dict[str, Any]:
    status_payload = _mapping(status)
    progress_payload = _mapping(progress)
    action_items = [dict(item) for item in actions or [] if isinstance(item, Mapping)]
    resolved_source_refs = _source_refs(status_payload, progress_payload, source_refs)
    resolved_suppression_refs = _conflict_suppression_refs(
        status=status_payload,
        progress=progress_payload,
        runtime_health=runtime_health,
        extra=conflict_suppression_refs,
    )
    parked = _parked_state(status_payload, progress_payload)
    if parked is not None:
        return _envelope(
            state_kind="parked",
            owner=parked["owner"],
            next_work_unit=None,
            typed_blocker=None,
            parked_state=parked["parked_state"],
            source_refs=resolved_source_refs,
            conflict_suppression_refs=resolved_suppression_refs,
        )
    action = _first_action(action_items)
    if action is not None and not _mapping(typed_blocker):
        return _envelope(
            state_kind="executable_owner_action",
            owner=_text(action.get("owner")) or _text(action.get("recommended_owner")) or _text(next_owner) or "med-autoscience",
            next_work_unit=_next_work_unit(action),
            typed_blocker=None,
            parked_state=None,
            source_refs=resolved_source_refs,
            conflict_suppression_refs=resolved_suppression_refs,
        )
    resolved_typed_blocker = _typed_blocker(typed_blocker, blocked_reason=blocked_reason, owner=next_owner)
    if resolved_typed_blocker is not None:
        return _envelope(
            state_kind="typed_blocker",
            owner=_text(resolved_typed_blocker.get("owner")) or _text(next_owner) or "med-autoscience",
            next_work_unit=None,
            typed_blocker=resolved_typed_blocker,
            parked_state=None,
            source_refs=resolved_source_refs,
            conflict_suppression_refs=resolved_suppression_refs,
        )
    return _envelope(
        state_kind="typed_blocker",
        owner=_text(next_owner) or "med-autoscience",
        next_work_unit=None,
        typed_blocker=_minimal_blocker(blocked_reason or "current_execution_unresolved", owner=next_owner),
        parked_state=None,
        source_refs=resolved_source_refs,
        conflict_suppression_refs=resolved_suppression_refs,
    )


def build_current_execution_evidence(
    *,
    action_queue: Sequence[Mapping[str, Any]] | None = None,
    runtime_health: Mapping[str, Any] | None = None,
    no_op: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    evidence = {
        "action_queue": [dict(item) for item in action_queue or [] if isinstance(item, Mapping)],
        "runtime_health": dict(runtime_health) if isinstance(runtime_health, Mapping) else None,
        "no_op": _no_op_evidence(no_op),
    }
    for key, value in _mapping(extra).items():
        if key not in evidence:
            evidence[key] = value
    return evidence


def _envelope(
    *,
    state_kind: str,
    owner: str,
    next_work_unit: object,
    typed_blocker: dict[str, Any] | None,
    parked_state: str | None,
    source_refs: list[str],
    conflict_suppression_refs: list[str],
) -> dict[str, Any]:
    payload = {
        "state_kind": state_kind,
        "owner": owner,
        "next_work_unit": next_work_unit,
        "typed_blocker": typed_blocker,
        "parked_state": parked_state,
        "source_refs": source_refs,
        "conflict_suppression_refs": conflict_suppression_refs,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }
    return {key: payload[key] for key in ENVELOPE_KEYS}


def _parked_state(status: Mapping[str, Any], progress: Mapping[str, Any]) -> dict[str, str] | None:
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    if auto_parked.get("parked") is True:
        parked_state = _text(auto_parked.get("parked_state")) or _text(progress.get("parked_state"))
        if parked_state is not None:
            return {
                "parked_state": parked_state,
                "owner": _text(auto_parked.get("parked_owner")) or _text(progress.get("parked_owner")) or "user",
            }
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    if _text(runtime_health.get("canonical_runtime_action")) == "await_explicit_resume":
        return {
            "parked_state": _text(progress.get("parked_state")) or "explicit_resume_pending",
            "owner": _text(progress.get("parked_owner")) or "user",
        }
    return None


def _typed_blocker(
    typed_blocker: Mapping[str, Any] | None,
    *,
    blocked_reason: str | None,
    owner: str | None,
) -> dict[str, Any] | None:
    if isinstance(typed_blocker, Mapping) and typed_blocker:
        return dict(typed_blocker)
    text = _text(blocked_reason)
    if text is None:
        return None
    return _minimal_blocker(text, owner=owner)


def _minimal_blocker(blocker_type: str, *, owner: str | None) -> dict[str, Any]:
    return {
        "blocker_type": blocker_type,
        "owner": _text(owner) or "med-autoscience",
    }


def _first_action(actions: list[dict[str, Any]]) -> dict[str, Any] | None:
    return actions[0] if actions else None


def _next_work_unit(action: Mapping[str, Any]) -> object:
    next_work_unit = action.get("next_work_unit")
    if isinstance(next_work_unit, Mapping):
        return dict(next_work_unit)
    text = _text(next_work_unit)
    if text is not None:
        return text
    for key in ("executable_work_unit", "controller_work_unit_id", "action_type"):
        if (value := _text(action.get(key))) is not None:
            return value
    return None


def _source_refs(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    source_refs: Sequence[str] | None,
) -> list[str]:
    refs: list[str] = []
    for item in source_refs or []:
        ref = _text(item)
        if ref is not None:
            refs.append(ref)
    refs.extend(_refs_from(_mapping(progress.get("refs"))))
    refs.extend(_refs_from(_mapping(status.get("refs"))))
    return sorted(dict.fromkeys(refs))


def _refs_from(value: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("controller_decision_path", "publication_eval_path", "runtime_status_summary_path"):
        if (ref := _text(value.get(key))) is not None:
            refs.append(ref)
    return refs


def _conflict_suppression_refs(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    runtime_health: Mapping[str, Any] | None,
    extra: Sequence[str] | None,
) -> list[str]:
    refs: list[str] = []
    for item in extra or []:
        ref = _text(item)
        if ref is not None:
            refs.append(ref)
    health = _mapping(runtime_health) or _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    if (action := _text(health.get("canonical_runtime_action"))) is not None:
        refs.append(f"runtime_health:{action}")
    return sorted(dict.fromkeys(refs))


def _no_op_evidence(value: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        return [dict(value)]
    return [dict(item) for item in value or [] if isinstance(item, Mapping)]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ALLOWED_STATE_KINDS",
    "ENVELOPE_KEYS",
    "build_current_execution_envelope",
    "build_current_execution_evidence",
]
