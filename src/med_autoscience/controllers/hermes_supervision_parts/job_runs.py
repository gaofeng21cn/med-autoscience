from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


def latest_job_run(
    profile: WorkspaceProfile,
    *,
    job_id: str | None,
    silent_success_response: str,
) -> dict[str, Any] | None:
    session_path = _latest_job_session_path(profile, job_id=job_id)
    if session_path is None:
        return None
    payload = _read_latest_job_session_payload(session_path)
    if payload is None:
        return _latest_job_run_projection(
            status="invalid",
            summary="latest cron session payload is unreadable",
            session_path=session_path,
            recorded_at=None,
        )
    if not isinstance(payload, dict):
        return _latest_job_run_projection(
            status="invalid",
            summary="latest cron session payload is invalid",
            session_path=session_path,
            recorded_at=None,
        )
    latest_content = _latest_assistant_content(payload.get("messages"))
    status, summary = _latest_job_run_status(
        latest_content,
        silent_success_response=silent_success_response,
    )
    return _latest_job_run_projection(
        status=status,
        summary=summary,
        session_path=session_path,
        recorded_at=str(payload.get("last_updated") or payload.get("session_start") or "").strip() or None,
    )


def _latest_job_session_path(profile: WorkspaceProfile, *, job_id: str | None) -> Path | None:
    resolved_job_id = str(job_id or "").strip()
    if not resolved_job_id:
        return None
    candidates = sorted((profile.hermes_home_root / "sessions").glob(f"session_cron_{resolved_job_id}_*.json"))
    if not candidates:
        return None
    return candidates[-1]


def _read_latest_job_session_payload(session_path: Path) -> object | None:
    try:
        return json.loads(session_path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return None


def _latest_assistant_content(messages: object) -> str | None:
    latest_content: str | None = None
    if isinstance(messages, list):
        for item in reversed(messages):
            if not isinstance(item, dict):
                continue
            if str(item.get("role") or "").strip() != "assistant":
                continue
            candidate = item.get("content")
            if isinstance(candidate, str) and candidate.strip():
                latest_content = candidate.strip()
                break
    return latest_content


def _latest_job_run_status(
    latest_content: str | None,
    *,
    silent_success_response: str,
) -> tuple[str, str | None]:
    status = "unknown"
    summary = None
    if latest_content == silent_success_response:
        status = "success"
        summary = "latest Hermes supervision tick completed"
    elif latest_content is not None and "data-collection script failed" in latest_content.lower():
        status = "failed"
        summary = latest_content.splitlines()[0].strip()
    elif latest_content is not None:
        status = "reported"
        summary = latest_content.splitlines()[0].strip()
    return status, summary


def _latest_job_run_projection(
    *,
    status: str,
    summary: str | None,
    session_path: Path,
    recorded_at: str | None,
) -> dict[str, Any]:
    return {
        "status": status,
        "summary": summary,
        "session_path": str(session_path),
        "recorded_at": recorded_at,
    }


__all__ = ["latest_job_run"]
