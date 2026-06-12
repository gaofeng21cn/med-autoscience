from __future__ import annotations

from collections.abc import Mapping
from typing import Any

ANTI_LOOP_BUDGET_EXHAUSTED = "anti_loop_budget_exhausted"
REPEAT_SUPPRESSED_TYPED_BLOCKER_OUTCOMES = frozenset(
    {
        "repeat_suppressed_with_typed_blocker",
        "typed_blocker_anti_loop_budget_exhausted",
    }
)


def is_anti_loop_stop_loss_closeout(closeout: Mapping[str, Any]) -> bool:
    typed_blocker = _mapping(closeout.get("typed_blocker"))
    anti_loop_budget = _mapping(typed_blocker.get("anti_loop_budget"))
    paper_stage_log = _mapping(closeout.get("paper_stage_log"))
    next_forced_delta = _mapping(paper_stage_log.get("next_forced_delta"))
    values = (
        closeout.get("blocked_reason"),
        closeout.get("typed_blocker_reason"),
        closeout.get("outcome"),
        closeout.get("stage_closeout_outcome"),
        closeout.get("status"),
        closeout.get("stage_closeout_status"),
        typed_blocker.get("blocker_kind"),
        typed_blocker.get("blocker_type"),
        typed_blocker.get("blocked_reason"),
        typed_blocker.get("reason"),
        anti_loop_budget.get("status"),
        paper_stage_log.get("outcome"),
        paper_stage_log.get("progress_delta_classification"),
        next_forced_delta.get("reason"),
    )
    for value in values:
        text = _text(value)
        if text == ANTI_LOOP_BUDGET_EXHAUSTED:
            return True
        if text in REPEAT_SUPPRESSED_TYPED_BLOCKER_OUTCOMES:
            return True
        if text == "exhausted" and anti_loop_budget:
            return True
        if text and ANTI_LOOP_BUDGET_EXHAUSTED in text:
            return True
    return False


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None
