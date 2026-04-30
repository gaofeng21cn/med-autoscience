from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_runtime_docs() -> dict[str, str]:
    return {
        path: (REPO_ROOT / path).read_text(encoding="utf-8")
        for path in (
            "docs/runtime/study_runtime_orchestration.md",
            "docs/runtime/study_runtime_control_surface.md",
        )
    }


def test_work_unit_attempt_runtime_contract_is_documented() -> None:
    docs = _read_runtime_docs()
    combined = "\n".join(docs.values())
    orchestration = docs["docs/runtime/study_runtime_orchestration.md"]

    for required in (
        "work-unit / route-unit attempt",
        "`unclaimed`",
        "`claimed`",
        "`running`",
        "`retry_queued`",
        "retry queued",
        "`released`",
        "`run_attempt_phase`",
        "run attempt phase",
        "`attempt_count`",
        "attempt 计数",
        "`failure_reason`",
        "failure reason",
        "running state refresh",
        "terminal/non-active handling",
        "stalled detection",
        "bounded retry",
        "retry/backoff 是恢复策略，不是研究裁决策略",
    ):
        assert required in orchestration

    for required in (
        "future external worker / hosted runtime",
        "`workspace_root` / `root` / `cwd`",
        "路径越界",
        "fail-closed",
        "`Codex-default host-agent runtime`",
        "不因为本节新增 work-unit contract 而改变 CLI、MCP、product-entry 或当前 Codex path 的默认执行模型",
    ):
        assert required in combined


def test_work_unit_control_surface_keeps_observability_and_scheduler_boundaries() -> None:
    docs = _read_runtime_docs()
    control = docs["docs/runtime/study_runtime_control_surface.md"]

    for required in (
        "observability-only surface",
        "dashboard / API / logs / status",
        "只能读取 orchestrator/controller state",
        "不得成为 study truth、publication authority 或 paper write authority",
        "`study_runtime_status(...)`",
        "`ensure_study_runtime(...)`",
        "`study_outer_loop_tick(...)`",
        "`study_decision_record`",
        "现有 CLI / MCP / product-entry surface",
        "Linear、Symphony scheduler 或任何外部 issue tracker 都不是 MAS 必需入口",
        "unsupported external scheduler boundaries",
    ):
        assert required in control

    for forbidden in (
        "Linear 是 MAS 必需入口",
        "Linear is a MAS required entry",
        "Symphony scheduler 是 MAS 必需入口",
        "Symphony scheduler is a MAS required entry",
        "外部 issue tracker 是 MAS 必需入口",
        "external issue tracker is a MAS required entry",
    ):
        assert forbidden not in control
