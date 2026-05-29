from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


MECHANISM_REPAIR_ESCALATION = "mechanism_repair_owner"
HUMAN_GATE_OR_STOP_LOSS_ESCALATION = "human_gate_or_stop_loss_candidate"
PAPER_PROGRESS_OBSERVED = "paper_progress_observed"
SAME_OWNER_RETRY_BUDGET = "same_owner_retry_budget"


def enrich_typed_blocker(
    blocker: Mapping[str, Any],
    *,
    study_id: str,
    work_unit_id: str,
    eval_id: str | None,
    source_fingerprint: str | None,
    repeat_count: int,
    first_seen: str,
    last_seen: str,
    paper_progress_delta: Mapping[str, Any] | None = None,
    platform_repair_delta: Mapping[str, Any] | None = None,
    no_forbidden_write_refs: Sequence[str] = (),
) -> dict[str, Any]:
    payload = dict(blocker)
    paper_delta = _mapping(paper_progress_delta)
    platform_delta = _mapping(platform_repair_delta)
    family = _blocker_family(payload)
    payload.setdefault("surface_kind", "mas_domain_typed_blocker")
    payload.setdefault("schema_version", 1)
    payload["blocker_family"] = family
    payload["study_id"] = study_id
    payload["work_unit_id"] = work_unit_id
    payload["eval_id"] = eval_id
    payload["source_fingerprint"] = source_fingerprint
    payload["repeat_count"] = max(0, int(repeat_count))
    payload["first_seen"] = first_seen
    payload["last_seen"] = last_seen
    payload["paper_progress_delta"] = paper_delta
    payload["platform_repair_delta"] = platform_delta
    payload["next_escalation"] = _next_escalation(
        repeat_count=payload["repeat_count"],
        paper_progress_delta=paper_delta,
    )
    payload["no_forbidden_write_refs"] = [ref for item in no_forbidden_write_refs if (ref := _text(item))]
    payload["next_owner"] = _text(payload.get("next_owner")) or "med-autoscience"
    return payload


def _next_escalation(
    *,
    repeat_count: int,
    paper_progress_delta: Mapping[str, Any],
) -> str:
    if _delta_count(paper_progress_delta) > 0:
        return PAPER_PROGRESS_OBSERVED
    if repeat_count >= 3:
        return HUMAN_GATE_OR_STOP_LOSS_ESCALATION
    if repeat_count >= 2:
        return MECHANISM_REPAIR_ESCALATION
    return SAME_OWNER_RETRY_BUDGET


def _blocker_family(payload: Mapping[str, Any]) -> str:
    return (
        _text(payload.get("blocker_family"))
        or _text(payload.get("reason"))
        or _text(payload.get("blocked_reason"))
        or _text(payload.get("blocker_id"))
        or _text(payload.get("failure_signature"))
        or "unknown_typed_blocker"
    )


def _delta_count(payload: Mapping[str, Any]) -> int:
    value = payload.get("count")
    if isinstance(value, bool) or value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value.strip()))
        except ValueError:
            return 0
    return 0


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {"count": 0, "token_usage_total": 0}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "HUMAN_GATE_OR_STOP_LOSS_ESCALATION",
    "MECHANISM_REPAIR_ESCALATION",
    "PAPER_PROGRESS_OBSERVED",
    "SAME_OWNER_RETRY_BUDGET",
    "enrich_typed_blocker",
]

