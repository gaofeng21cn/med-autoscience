from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers import current_work_unit


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
ALLOWED_STATE_KINDS = ("parked", "executable_owner_action", "running_provider_attempt", "typed_blocker")
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
    live_provider_attempt: Mapping[str, Any] | None = None,
    current_work_unit_payload: Mapping[str, Any] | None = None,
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
    canonical_work_unit = _mapping(
        current_work_unit_payload
    ) or current_work_unit.build_current_work_unit(
        status=status_payload,
        progress=progress_payload,
        actions=action_items,
        provider_admission=live_provider_attempt,
        live_provider_attempt=live_provider_attempt,
        typed_blocker=typed_blocker,
        blocked_reason=blocked_reason,
        next_owner=next_owner,
        runtime_health=runtime_health,
        source_refs=resolved_source_refs,
    )
    if _current_work_unit_status(canonical_work_unit) == "running_provider_attempt":
        return _envelope_from_current_work_unit(
            canonical_work_unit,
            source_refs=resolved_source_refs,
            conflict_suppression_refs=resolved_suppression_refs,
        )
    if _current_work_unit_stage_owner_answer(canonical_work_unit):
        return _envelope_from_current_work_unit(
            canonical_work_unit,
            source_refs=resolved_source_refs,
            conflict_suppression_refs=resolved_suppression_refs,
        )
    parked = _parked_state(status_payload, progress_payload)
    if parked is not None:
        if _parked_state_requires_human_resume(
            status=status_payload,
            progress=progress_payload,
            parked=parked,
            current_work_unit=canonical_work_unit,
        ):
            return _envelope(
                state_kind="parked",
                owner=parked["owner"],
                next_work_unit=None,
                typed_blocker=None,
                parked_state=parked["parked_state"],
                source_refs=resolved_source_refs,
                conflict_suppression_refs=resolved_suppression_refs,
            )
        if _current_work_unit_status(canonical_work_unit) != "executable_owner_action":
            return _envelope(
                state_kind="parked",
                owner=parked["owner"],
                next_work_unit=None,
                typed_blocker=None,
                parked_state=parked["parked_state"],
                source_refs=resolved_source_refs,
                conflict_suppression_refs=resolved_suppression_refs,
            )
    return _envelope_from_current_work_unit(
        canonical_work_unit,
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


def _envelope_from_current_work_unit(
    work_unit: Mapping[str, Any],
    *,
    source_refs: list[str],
    conflict_suppression_refs: list[str],
) -> dict[str, Any]:
    status = _current_work_unit_status(work_unit)
    state = _mapping(work_unit.get("state"))
    if status == "executable_owner_action":
        return _envelope(
            state_kind="executable_owner_action",
            owner=_text(work_unit.get("owner")) or "med-autoscience",
            next_work_unit=_text(work_unit.get("work_unit_id")) or _text(work_unit.get("action_type")),
            typed_blocker=None,
            parked_state=None,
            source_refs=source_refs,
            conflict_suppression_refs=conflict_suppression_refs,
        )
    if status == "running_provider_attempt":
        return _envelope(
            state_kind="running_provider_attempt",
            owner=_text(work_unit.get("owner")) or "supervisor_only/live_provider_attempt",
            next_work_unit=_text(work_unit.get("work_unit_id")),
            typed_blocker=None,
            parked_state=None,
            source_refs=source_refs,
            conflict_suppression_refs=conflict_suppression_refs,
        )
    blocker = _mapping(state.get("typed_blocker")) or _minimal_blocker(
        _text(state.get("blocker_type")) or "current_execution_unresolved",
        owner=_text(work_unit.get("owner")),
    )
    return _envelope(
        state_kind="typed_blocker",
        owner=_text(work_unit.get("owner")) or _text(blocker.get("owner")) or "med-autoscience",
        next_work_unit=None,
        typed_blocker=blocker,
        parked_state=None,
        source_refs=source_refs,
        conflict_suppression_refs=conflict_suppression_refs,
    )


def _current_work_unit_status(work_unit: Mapping[str, Any]) -> str | None:
    return _text(work_unit.get("status"))


def _current_work_unit_stage_owner_answer(work_unit: Mapping[str, Any]) -> bool:
    if _current_work_unit_status(work_unit) != "typed_blocker":
        return False
    return _text(_mapping(work_unit.get("state")).get("source")) == "stage_owner_answer"


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


def _parked_state_requires_human_resume(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    parked: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
) -> bool:
    if _text(parked.get("parked_state")) == "explicit_resume_pending":
        if _current_work_unit_supersedes_explicit_resume(
            status=status,
            progress=progress,
            current_work_unit=current_work_unit,
        ):
            return False
        return True
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    if auto_parked.get("auto_execution_complete") is True:
        return True
    if auto_parked.get("awaiting_explicit_wakeup") is True:
        if _text(parked.get("parked_state")) == "waiting_user_decision":
            classification = _mapping(auto_parked.get("runtime_failure_classification"))
            return (
                classification.get("requires_human_gate") is True
                and _has_human_gate_authority_ref(status=status, progress=progress)
            )
        return True
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    return _text(runtime_health.get("canonical_runtime_action")) == "await_explicit_resume"


def _current_work_unit_supersedes_explicit_resume(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
) -> bool:
    if _current_work_unit_status(current_work_unit) != "executable_owner_action":
        return False
    owner = _text(current_work_unit.get("owner"))
    if owner in {None, "user", "human"}:
        return False
    if _has_human_gate_authority_ref(status=status, progress=progress):
        return False
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    classification = _mapping(auto_parked.get("runtime_failure_classification"))
    return classification.get("requires_human_gate") is not True


def _minimal_blocker(blocker_type: str, *, owner: str | None) -> dict[str, Any]:
    return {
        "blocker_type": blocker_type,
        "owner": _text(owner) or "med-autoscience",
    }


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


def _has_human_gate_authority_ref(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    for surface in (
        status,
        progress,
        _mapping(status.get("auto_runtime_parked")),
        _mapping(progress.get("auto_runtime_parked")),
        _mapping(status.get("refs")),
        _mapping(progress.get("refs")),
    ):
        if _surface_has_human_gate_ref(surface):
            return True
    return False


def _surface_has_human_gate_ref(surface: Mapping[str, Any]) -> bool:
    for key in (
        "human_gate_ref",
        "human_gate_resume_ref",
        "human_gate_or_resume_ref",
        "human_gate_authority_ref",
        "decision_ref",
        "receipt_ref",
        "source_artifact_path",
    ):
        if _text(surface.get(key)) is not None:
            return True
    for key in (
        "human_gate_refs",
        "human_gate_resume_refs",
        "human_gate_or_resume_refs",
        "human_gate_authority_refs",
    ):
        if _text_items(surface.get(key)):
            return True
    for gate in surface.get("family_human_gates") or []:
        gate_payload = _mapping(gate)
        if _surface_has_human_gate_ref(gate_payload):
            return True
        for evidence in gate_payload.get("evidence_refs") or []:
            if _text(_mapping(evidence).get("ref")) is not None:
                return True
    return False


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


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, (list, tuple, set)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


__all__ = [
    "ALLOWED_STATE_KINDS",
    "ENVELOPE_KEYS",
    "build_current_execution_envelope",
    "build_current_execution_evidence",
]
