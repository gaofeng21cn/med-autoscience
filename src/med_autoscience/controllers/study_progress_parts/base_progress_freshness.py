from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .gate_clearing_progress import append_gate_clearing_batch_progress_signal, append_progress_signal
from .stage_state import progress_freshness_required
from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def _latest_progress_signal(
    *,
    bash_summary_payload: dict[str, Any] | None,
    details_projection_payload: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    publication_eval_payload: dict[str, Any] | None,
    gate_clearing_batch_payload: dict[str, Any] | None,
    gate_clearing_batch_path: Path | None,
) -> dict[str, Any] | None:
    signals: list[dict[str, Any]] = []
    latest_session = (bash_summary_payload or {}).get("latest_session")
    if isinstance(latest_session, dict):
        last_progress = latest_session.get("last_progress")
        if isinstance(last_progress, dict):
            append_progress_signal(
                signals=signals,
                timestamp=_non_empty_text(last_progress.get("ts")) or _non_empty_text(latest_session.get("updated_at")),
                source="bash_summary",
                summary=_non_empty_text(last_progress.get("message")) or _non_empty_text(last_progress.get("step")),
            )
    if details_projection_payload is not None:
        append_progress_signal(
            signals=signals,
            timestamp=_non_empty_text(((details_projection_payload.get("summary") or {}).get("updated_at")))
            or _non_empty_text((details_projection_payload or {}).get("generated_at")),
            source="details_projection",
            summary=_non_empty_text(((details_projection_payload.get("summary") or {}).get("status_line"))),
        )
    if controller_decision_payload is not None:
        decision_type = _DECISION_TYPE_LABELS.get(
            _non_empty_text(controller_decision_payload.get("decision_type")) or "",
            "形成控制面决定",
        )
        reason = _display_text(controller_decision_payload.get("reason"))
        summary = f"控制面正式决定：{decision_type}。"
        if reason:
            summary += f" 原因：{reason}"
        append_progress_signal(
            signals=signals,
            timestamp=controller_decision_payload.get("emitted_at"),
            source="controller_decision",
            summary=summary,
        )
    if publication_eval_payload is not None:
        verdict = (publication_eval_payload.get("verdict") or {}) if isinstance(publication_eval_payload, dict) else {}
        append_progress_signal(
            signals=signals,
            timestamp=publication_eval_payload.get("emitted_at"),
            source="publication_eval",
            summary=_non_empty_text(verdict.get("summary")) or "发表评估已更新。",
        )
    append_gate_clearing_batch_progress_signal(
        signals=signals,
        gate_clearing_batch_payload=gate_clearing_batch_payload,
        gate_clearing_batch_path=gate_clearing_batch_path,
        publication_eval_payload=publication_eval_payload,
    )
    if not signals:
        return None
    return max(signals, key=lambda item: item["timestamp"])


def _progress_freshness(
    *,
    current_stage: str,
    bash_summary_payload: dict[str, Any] | None,
    details_projection_payload: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    publication_eval_payload: dict[str, Any] | None,
    gate_clearing_batch_payload: dict[str, Any] | None,
    gate_clearing_batch_path: Path | None,
) -> dict[str, Any]:
    required = progress_freshness_required(current_stage)
    latest_signal = _latest_progress_signal(
        bash_summary_payload=bash_summary_payload,
        details_projection_payload=details_projection_payload,
        controller_decision_payload=controller_decision_payload,
        publication_eval_payload=publication_eval_payload,
        gate_clearing_batch_payload=gate_clearing_batch_payload,
        gate_clearing_batch_path=gate_clearing_batch_path,
    )
    if not required:
        return {
            "status": "not_required",
            "required": False,
            "summary": "当前阶段以人工判断或收尾为主，不要求系统继续产出新的自动推进信号。",
            "stale_after_seconds": _PROGRESS_STALE_AFTER_SECONDS,
            "latest_progress_at": latest_signal.get("timestamp") if latest_signal else None,
            "latest_progress_time_label": latest_signal.get("time_label") if latest_signal else None,
            "latest_progress_source": latest_signal.get("source") if latest_signal else None,
            "latest_progress_summary": latest_signal.get("summary") if latest_signal else None,
            "seconds_since_latest_progress": None,
        }
    if latest_signal is None:
        return {
            "status": "missing",
            "required": True,
            "summary": "当前还没有看到明确的研究推进记录，用户现在只能看到监管或状态面。",
            "stale_after_seconds": _PROGRESS_STALE_AFTER_SECONDS,
            "latest_progress_at": None,
            "latest_progress_time_label": None,
            "latest_progress_source": None,
            "latest_progress_summary": None,
            "seconds_since_latest_progress": None,
        }

    progress_freshness_now = _controller_override("_progress_freshness_now", _progress_freshness_now)
    age_seconds = max(
        0,
        int((progress_freshness_now() - datetime.fromisoformat(str(latest_signal["timestamp"]))).total_seconds()),
    )
    if age_seconds > _PROGRESS_STALE_AFTER_SECONDS:
        summary = (
            f"距离上一次明确研究推进已经超过 {_duration_hours_label(_PROGRESS_STALE_AFTER_SECONDS)}，"
            "当前要重点排查是否卡住或空转。"
        )
        status = "stale"
    else:
        summary = f"最近 {_duration_hours_label(_PROGRESS_STALE_AFTER_SECONDS)}内仍有明确研究推进记录。"
        status = "fresh"
    return {
        "status": status,
        "required": True,
        "summary": summary,
        "stale_after_seconds": _PROGRESS_STALE_AFTER_SECONDS,
        "latest_progress_at": latest_signal["timestamp"],
        "latest_progress_time_label": latest_signal["time_label"],
        "latest_progress_source": latest_signal["source"],
        "latest_progress_summary": latest_signal["summary"],
        "seconds_since_latest_progress": age_seconds,
    }
