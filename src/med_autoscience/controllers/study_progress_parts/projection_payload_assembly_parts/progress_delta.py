from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)


def progress_delta_metrics(
    *,
    quality_repair_batch_followthrough: dict[str, Any],
    gate_clearing_batch_followthrough: dict[str, Any],
    opl_current_control_state_handoff: dict[str, Any] | None,
    runtime_efficiency: dict[str, Any],
    repair_progress_projection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    quality_followthrough = (
        quality_repair_batch_followthrough
        if isinstance(quality_repair_batch_followthrough, dict)
        else {}
    )
    gate_followthrough = (
        gate_clearing_batch_followthrough
        if isinstance(gate_clearing_batch_followthrough, dict)
        else {}
    )
    efficiency = runtime_efficiency if isinstance(runtime_efficiency, dict) else {}
    token_usage = _mapping_copy(efficiency.get("token_usage"))
    total_tokens = _token_usage_total(token_usage)
    paper_triggered = _paper_progress_triggered(
        quality_repair_batch_followthrough=quality_followthrough,
        gate_clearing_batch_followthrough=gate_followthrough,
    )
    repair_progress_triggered = _repair_progress_triggered(
        repair_progress_projection=repair_progress_projection,
    )
    terminal_paper_triggered = _terminal_stage_paper_progress_triggered(
        opl_current_control_state_handoff=opl_current_control_state_handoff,
    )
    paper_triggered = paper_triggered or repair_progress_triggered or terminal_paper_triggered
    platform_triggered = _platform_repair_triggered(
        opl_current_control_state_handoff=opl_current_control_state_handoff
    )
    paper_tokens = total_tokens if paper_triggered and not platform_triggered else 0
    platform_tokens = total_tokens if platform_triggered else 0
    deliverable_delta = {
        "count": 1 if paper_triggered else 0,
        "token_usage_total": paper_tokens,
        "sources": _paper_progress_sources(
            quality_repair_batch_followthrough=quality_followthrough,
            gate_clearing_batch_followthrough=gate_followthrough,
            repair_progress_triggered=repair_progress_triggered,
            terminal_paper_triggered=terminal_paper_triggered,
        ),
    }
    paper_refs = _paper_progress_refs(
        repair_progress_projection=repair_progress_projection,
    )
    if paper_refs:
        deliverable_delta["refs"] = paper_refs
    platform_delta = {
        "count": 1 if platform_triggered else 0,
        "token_usage_total": platform_tokens,
        "sources": _platform_repair_sources(
            opl_current_control_state_handoff=opl_current_control_state_handoff
        ),
    }
    return {
        "deliverable_progress_delta": deliverable_delta,
        "paper_progress_delta": deliverable_delta,
        "platform_repair_delta": platform_delta,
        "progress_delta_classification": _progress_delta_classification(
            deliverable_triggered=paper_triggered,
            platform_triggered=platform_triggered,
        ),
    }


def _paper_progress_triggered(
    *,
    quality_repair_batch_followthrough: dict[str, Any],
    gate_clearing_batch_followthrough: dict[str, Any],
) -> bool:
    quality_status = _non_empty_text(quality_repair_batch_followthrough.get("status"))
    gate_status = _non_empty_text(gate_clearing_batch_followthrough.get("status"))
    if quality_status == "executed":
        return True
    if gate_status in {"executed", "pending"}:
        return True
    if _non_empty_text(quality_repair_batch_followthrough.get("gate_replay_status")) is not None:
        return True
    return _non_empty_text(gate_clearing_batch_followthrough.get("gate_replay_status")) is not None


def _repair_progress_triggered(
    *,
    repair_progress_projection: dict[str, Any] | None,
) -> bool:
    repair_progress = _mapping_copy(repair_progress_projection)
    return repair_progress.get("paper_delta_observed") is True


def _platform_repair_triggered(*, opl_current_control_state_handoff: dict[str, Any] | None) -> bool:
    handoff = _mapping_copy(opl_current_control_state_handoff)
    if not handoff:
        return False
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    blocked_reason = _non_empty_text(handoff.get("blocked_reason"))
    next_owner = _non_empty_text(handoff.get("next_owner"))
    health_status = _non_empty_text(runtime_health.get("health_status"))
    if blocked_reason in {
        "runtime_recovery_not_authorized",
        "runtime_recovery_retry_budget_exhausted",
        "opl_stage_attempt_admission_required",
    }:
        return True
    if health_status in {"recover_runtime", "escalated", "degraded"}:
        return True
    reason_blob = " ".join(
        text
        for text in (blocked_reason, next_owner, health_status)
        if text is not None
    ).lower()
    if any(
        token in reason_blob
        for token in (
            "currentness",
            "controller",
            "read_model",
            "provider",
            "runtime_recovery",
            "opl_stage_attempt_admission_required",
        )
    ):
        return True
    return False


def _paper_progress_sources(
    *,
    quality_repair_batch_followthrough: dict[str, Any],
    gate_clearing_batch_followthrough: dict[str, Any],
    repair_progress_triggered: bool = False,
    terminal_paper_triggered: bool = False,
) -> list[str]:
    result: list[str] = []
    if repair_progress_triggered:
        result.append("repair_progress_projection.mas_owner_repair_execution_evidence")
    if _non_empty_text(quality_repair_batch_followthrough.get("status")) is not None:
        result.append("quality_repair_batch_followthrough")
    if _non_empty_text(gate_clearing_batch_followthrough.get("status")) is not None:
        result.append("gate_clearing_batch_followthrough")
    if _non_empty_text(quality_repair_batch_followthrough.get("gate_replay_status")) is not None:
        result.append("quality_repair_gate_replay")
    if _non_empty_text(gate_clearing_batch_followthrough.get("gate_replay_status")) is not None:
        result.append("gate_clearing_gate_replay")
    if terminal_paper_triggered:
        result.append("opl_current_control_state.latest_terminal_stage_log.paper_stage_log")
    return result


def _paper_progress_refs(
    *,
    repair_progress_projection: dict[str, Any] | None,
) -> list[str]:
    repair_progress = _mapping_copy(repair_progress_projection)
    refs: list[str] = []
    for item in _mapping_items(repair_progress.get("changed_artifact_refs")):
        if text := _non_empty_text(item.get("path")):
            refs.append(text)
    for key in (
        "repair_execution_evidence_ref",
        "owner_receipt_ref",
        "ai_reviewer_recheck_request_ref",
    ):
        if text := _non_empty_text(repair_progress.get(key)):
            refs.append(text)
    refs.extend(_text_list(repair_progress.get("gate_replay_refs")))
    return list(dict.fromkeys(refs))


def _mapping_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _terminal_stage_paper_progress_triggered(
    *,
    opl_current_control_state_handoff: dict[str, Any] | None,
) -> bool:
    handoff = _mapping_copy(opl_current_control_state_handoff)
    terminal = _mapping_copy(handoff.get("latest_terminal_stage_log"))
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    if not terminal or not paper_stage_log:
        return False
    if _non_empty_text(terminal.get("typed_blocker_reason")) is not None:
        return False
    if _non_empty_text(terminal.get("status")) == "typed_blocker":
        return False
    if _non_empty_text(paper_stage_log.get("outcome")) == "typed_blocker":
        return False
    classification = _non_empty_text(paper_stage_log.get("progress_delta_classification"))
    if classification is not None and classification not in {"deliverable_progress", "mixed"}:
        return False
    blocking_missing_fields = [
        field
        for field in _text_list(terminal.get("missing_user_stage_log_fields"))
        if field != "progress_delta_classification"
    ]
    if blocking_missing_fields:
        return False
    if not _text_list(paper_stage_log.get("changed_paper_surfaces")):
        return False
    return _terminal_stage_paper_delta_backed(
        terminal=terminal,
        paper_stage_log=paper_stage_log,
    )


def _terminal_stage_paper_delta_backed(
    *,
    terminal: dict[str, Any],
    paper_stage_log: dict[str, Any],
) -> bool:
    if _text_list(terminal.get("closeout_refs")):
        return True
    for field in (
        "accepted_artifact_refs",
        "owner_receipt_refs",
        "product_delta_refs",
        "semantic_delta_refs",
        "stage_owner_answer_refs",
        "reviewer_gate_delta_refs",
    ):
        if _text_list(paper_stage_log.get(field)):
            return True
    return False


def _platform_repair_sources(*, opl_current_control_state_handoff: dict[str, Any] | None) -> list[str]:
    handoff = _mapping_copy(opl_current_control_state_handoff)
    result: list[str] = []
    if _non_empty_text(handoff.get("blocked_reason")) is not None:
        result.append("opl_current_control_state.blocked_reason")
    if _mapping_copy(handoff.get("stage_progress_log")):
        result.append("opl_current_control_state.stage_progress_log")
    if _mapping_copy(handoff.get("runtime_health")):
        result.append("opl_current_control_state.runtime_health")
    return result


def _progress_delta_classification(
    *,
    deliverable_triggered: bool,
    platform_triggered: bool,
) -> str:
    if deliverable_triggered and platform_triggered:
        return "mixed"
    if deliverable_triggered:
        return "deliverable_progress"
    if platform_triggered:
        return "platform_repair"
    return "typed_blocker"


def _token_usage_total(token_usage: dict[str, Any]) -> int:
    total = _number(
        token_usage.get("total_tokens")
        if token_usage
        else None
    )
    if total is not None:
        return total
    partial = _sum_numbers(
        token_usage.get("input_tokens") if token_usage else None,
        token_usage.get("cached_input_tokens") if token_usage else None,
        token_usage.get("output_tokens") if token_usage else None,
        token_usage.get("reasoning_tokens") if token_usage else None,
    )
    return partial or 0


def _number(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(float(text))
        except ValueError:
            return None
    return None


def _sum_numbers(*values: object) -> int | None:
    present = [_number(value) for value in values]
    numbers = [value for value in present if value is not None]
    if not numbers:
        return None
    return sum(numbers)


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _non_empty_text(item)) is not None]
