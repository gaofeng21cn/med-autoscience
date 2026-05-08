from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def empty_state(
    studies: Sequence[Mapping[str, Any]],
    runs: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    if runs:
        return None
    if not studies:
        return {
            "reason": "no_studies",
            "summary": "当前 profile 没有发现可展示的 study。",
            "study_count": 0,
            "next_action": "确认 workspace profile 和 studies root。",
        }
    return {
        "reason": "no_live_run",
        "summary": "当前没有 live run；terminal/log 缺失是运行状态证据，而不是页面加载失败。",
        "study_count": len(studies),
        "next_action": "回到 Progress Portal 查看 blocker，必要时通过 MAS controller 请求 reconcile。",
    }


def runtime_observation_status(*, active_run_id: str | None, worker_running: bool) -> str:
    if active_run_id and worker_running:
        return "live_run_observed"
    if active_run_id:
        return "run_id_without_worker"
    return "no_live_run"


__all__ = ["empty_state", "runtime_observation_status"]
