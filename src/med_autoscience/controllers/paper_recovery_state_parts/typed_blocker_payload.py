from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.typed_blocker_owner_answer import (
    typed_blocker_answer_ref as _typed_blocker_answer_ref,
)
from med_autoscience.controllers.paper_recovery_state_parts.state_diagnostics import (
    current_work_unit_status as _current_work_unit_status,
    first_text as _first_text,
    mapping as _mapping,
    text as _text,
    text_items as _text_items,
)


def current_typed_blocker(current_work_unit: Mapping[str, Any]) -> dict[str, Any]:
    if _current_work_unit_status(current_work_unit) not in {"typed_blocker", "blocked_current_work_unit"}:
        return {}
    state = _mapping(current_work_unit.get("state"))
    typed_blocker = _mapping(state.get("typed_blocker")) or _mapping(current_work_unit.get("typed_blocker"))
    if not typed_blocker:
        typed_blocker = {
            "blocker_type": _text(state.get("blocker_type")),
            "blocked_reason": _text(state.get("blocked_reason")),
        }
    for key in ("owner", "action_type", "work_unit_id", "work_unit_fingerprint"):
        if key not in typed_blocker and _text(current_work_unit.get(key)) is not None:
            typed_blocker[key] = _text(current_work_unit.get(key))
    if _current_work_unit_status(current_work_unit) == "blocked_current_work_unit" and _generic_unresolved_blocker(
        typed_blocker=typed_blocker,
        source=_text(state.get("source")),
    ):
        return {}
    return {key: value for key, value in typed_blocker.items() if value not in (None, "", [], {})}


def typed_blocker_from_closeout(
    closeout: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any]:
    embedded = _mapping(closeout.get("typed_blocker"))
    domain_blocker = _mapping(closeout.get("domain_blocker"))
    owner_result = _mapping(closeout.get("owner_result"))
    paper_log = _mapping(closeout.get("paper_stage_log"))
    blocker_type = _first_text(
        embedded.get("blocked_reason"),
        embedded.get("blocker_type"),
        embedded.get("blocker_kind"),
        embedded.get("reason"),
        embedded.get("blocker_id"),
        domain_blocker.get("blocked_reason"),
        domain_blocker.get("blocker_type"),
        domain_blocker.get("blocker_kind"),
        domain_blocker.get("reason"),
        domain_blocker.get("blocker_id"),
        closeout.get("typed_blocker_reason"),
        closeout.get("blocked_reason"),
        owner_result.get("blocked_reason"),
        *_text_items(paper_log.get("remaining_blockers")),
    )
    if blocker_type is None:
        progress_delta = _text(paper_log.get("progress_delta_classification"))
        if progress_delta != "typed_blocker" and _text(closeout.get("typed_blocker_ref")) is None:
            return {}
        blocker_type = "typed_blocker"
    explicit_typed_signal = any(
        value is not None
        for value in (
            _text(closeout.get("typed_blocker_ref")),
            _text(closeout.get("typed_blocker_reason")),
            _text(closeout.get("blocked_reason")),
            _text(owner_result.get("blocked_reason")),
            _text(paper_log.get("progress_delta_classification"))
            if _text(paper_log.get("progress_delta_classification")) == "typed_blocker"
            else None,
        )
    ) or bool(embedded) or bool(domain_blocker) or bool(_text_items(paper_log.get("remaining_blockers")))
    if not explicit_typed_signal:
        return {}
    owner = (
        _text(embedded.get("owner"))
        or _text(embedded.get("next_owner"))
        or _text(domain_blocker.get("owner"))
        or _text(domain_blocker.get("next_owner"))
        or _text(owner_result.get("owner"))
        or _text(closeout.get("next_owner"))
        or _text(obligation.get("owner"))
        or "MedAutoScience"
    )
    return {
        key: value
        for key, value in {
            **embedded,
            **domain_blocker,
            "blocker_type": blocker_type,
            "blocked_reason": blocker_type,
            "owner": owner,
            "action_type": _text(closeout.get("action_type")) or _text(obligation.get("action_type")),
            "work_unit_id": _text(closeout.get("work_unit_id")) or _text(obligation.get("work_unit_id")),
            "work_unit_fingerprint": _text(closeout.get("work_unit_fingerprint"))
            or _text(closeout.get("action_fingerprint"))
            or _text(obligation.get("work_unit_fingerprint")),
        }.items()
        if value not in (None, "", [], {})
    }


def typed_blocker_reason(typed_blocker: Mapping[str, Any]) -> str | None:
    for key in ("blocked_reason", "blocker_type", "blocker_kind", "reason", "blocker_id"):
        if text := _text(typed_blocker.get(key)):
            return text
    anti_loop = _mapping(typed_blocker.get("anti_loop_budget"))
    if _text(anti_loop.get("status")) == "exhausted":
        return "anti_loop_budget_exhausted"
    return None


def typed_blocker_has_stable_outcome_ref(typed_blocker: Mapping[str, Any]) -> bool:
    if _typed_blocker_answer_ref(typed_blocker) is not None:
        return True
    if _text_items(typed_blocker.get("closeout_refs")):
        return True
    if _text(typed_blocker.get("latest_owner_answer_kind")) == "typed_blocker":
        return _text(typed_blocker.get("latest_owner_answer_ref")) is not None
    if _text(typed_blocker.get("owner_answer_shape")) == "typed_blocker_ref":
        return _text(typed_blocker.get("latest_owner_answer_ref")) is not None
    return False


def _generic_unresolved_blocker(*, typed_blocker: Mapping[str, Any], source: str | None) -> bool:
    if source != "blocked_current_work_unit":
        return False
    if typed_blocker_reason(typed_blocker) != "current_work_unit_unresolved":
        return False
    identity_fields = (
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "action_fingerprint",
        "blocker_id",
        "latest_owner_answer_ref",
        "typed_blocker_ref",
    )
    return not any(_text(typed_blocker.get(key)) is not None for key in identity_fields)


__all__ = [
    "current_typed_blocker",
    "typed_blocker_from_closeout",
    "typed_blocker_has_stable_outcome_ref",
    "typed_blocker_reason",
]
