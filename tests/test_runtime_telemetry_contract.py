from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_runtime_telemetry_contract_records_stable_event_identity() -> None:
    doc = _read("docs/runtime/study_runtime_orchestration.md")

    for required in (
        "Runtime telemetry and accounting",
        "`program_id`",
        "`study_id`",
        "`quest_id`",
        "`active_run_id`",
        "`work_unit_id`",
        "`route_id`",
        "`attempt_count`",
        "`run_attempt_phase`",
        "`session_id`",
        "`event_type`",
        "`outcome`",
        "`failure_reason`",
        "`worker_host`",
        "`workspace_root`",
        "`cwd`",
        "`timestamp`",
        "`token_usage_updated`",
        "`rate_limit_updated`",
        "`workspace_cleanup_completed`",
    ):
        assert required in doc

    for prohibited in (
        "整稿、raw data、完整 ledger 或投稿包内容直接塞进 event",
        "医学质量裁决",
    ):
        assert prohibited in doc


def test_runtime_accounting_uses_absolute_totals_and_keeps_context_window_separate() -> None:
    combined = "\n".join(
        (
            _read("docs/runtime/study_runtime_orchestration.md"),
            _read("docs/runtime/study_runtime_control_surface.md"),
        )
    )

    for required in (
        "`thread/tokenUsage/updated.tokenUsage.total`",
        "`total_token_usage` / `tokenUsage.total` 表示累计快照",
        "`last_token_usage` / `tokenUsage.last` 表示最新增量",
        "不得把 delta 再累加到已经接受的 absolute total",
        "`turn/completed.usage`",
        "event type / payload path",
        "`model_context_window`",
        "context window / model context capacity 必须和 spend 分开投影",
        "rate-limit snapshot",
        "runtime throttling / backoff",
    ):
        assert required in combined


def test_snapshot_observability_is_read_only_regression_evidence() -> None:
    combined = "\n".join(
        (
            _read("docs/runtime/study_runtime_orchestration.md"),
            _read("docs/runtime/study_runtime_control_surface.md"),
        )
    )

    for required in (
        "Snapshot observability evidence",
        "read-only projection",
        "`snapshot_timeout` / `snapshot_unavailable`",
        "idle、running with session/token usage、retry/backoff queue",
        "operator projection regression oracle",
        "dashboard snapshot、API response 和 terminal status 可以作为 regression evidence",
        "不能成为医学研究 authority",
        "不得直接写入 research result、paper package 或 publication eval",
    ):
        assert required in combined


def test_workspace_lifecycle_teardown_hygiene_is_fail_closed() -> None:
    doc = _read("docs/runtime/study_runtime_orchestration.md")

    for required in (
        "Workspace lifecycle and teardown hygiene",
        "`after_create`",
        "`before_run`",
        "`after_run`",
        "`before_remove`",
        "cleanup evidence",
        "`cleanup_reason`",
        "preserved artifact refs",
        "terminal/released cleanup 与 non-active stop 语义分开",
        "path canonicalization 必须解析 symlink",
        "root escape",
        "relative path escape",
        "fail-closed",
        "`failure_reason=workspace_boundary_violation`",
        "不得把 Linear/GitHub/Symphony teardown hook 写成 MAS 必需流程",
    ):
        assert required in doc
