from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import tomllib
from typing import Any


CODEX_APP_AUTOMATION_REQUIRED_PROMPT_TOKENS = (
    "developer_apply_safe",
    "mode=developer_apply_safe",
    "domain-route-reconcile --mode developer_apply_safe --apply",
    "domain-route-scan --apply-safe-actions",
    "--apply-runtime-platform-repair",
    "--developer-supervisor-mode developer_apply_safe",
    "domain-action-request-materialize --mode developer_apply_safe --apply",
    "domain-owner-action-dispatch --mode developer_apply_safe --apply",
    "workspace_dynamic_active_studies",
    "new MAS tasks",
    "active_run_id",
    "worker_running",
    "worktree",
    "action_queue",
    "why_not_applied",
    "OPL family user config",
    "study-runtime-status",
    "study-progress",
    "runtime_supervision/latest",
    "runtime_watch/latest",
    "controller_decisions/latest",
    "publication_eval/latest",
    "gate_clearing_batch/latest",
    "paper-facing artifact delta",
    "publication gate blocker",
    "controller/route/work_unit",
    "MAS repo/controller/runtime root cause",
    "不得手工改论文包或 runtime-owned surfaces",
)
SCOPE_POLICY = "workspace_dynamic_active_studies"


def canonical_codex_app_automation_prompt() -> str:
    return "\n".join(
        [
            "MAS 开发者模式外围巡检：developer_apply_safe；mode=developer_apply_safe。",
            "每次 heartbeat 面向 workspace_dynamic_active_studies 动态发现所有活跃 MAS studies，包括 new MAS tasks；不要只按固定 study allowlist 巡检。",
            "先通过 MAS/OPL 维护的外层监督合同推进同 tick：domain-route-reconcile --mode developer_apply_safe --apply；domain-route-scan --apply-safe-actions --apply-runtime-platform-repair --developer-supervisor-mode developer_apply_safe；domain-action-request-materialize --mode developer_apply_safe --apply；domain-owner-action-dispatch --mode developer_apply_safe --apply。",
            "必须读取 MAS stable runtime/control surfaces：study-runtime-status、study-progress、runtime_supervision/latest、runtime_watch/latest、controller_decisions/latest、publication_eval/latest、gate_clearing_batch/latest。",
            "逐 study 报告 active_run_id、worker_running、worktree、过去窗口内是否有 paper-facing artifact delta、publication gate blocker、是否卡在 controller/route/work_unit 授权、action_queue、why_not_applied。",
            "遇到 no live worker、无 paper-facing artifact delta、gate replay 循环、controller/route/work_unit 授权异常、MCP/CLI 观察面异常时，先定位并修复 MAS repo/controller/runtime root cause；只能通过 MAS/controller/runtime 合同推进。",
            "不得手工改论文包或 runtime-owned surfaces，不得 patch paper/package/current_package/publication_eval/controller_decisions，不得放宽 publication/quality gate。",
            "只有看到 MAS-owned paper-facing artifact delta 后，才能说对应论文实际推进；否则报告阻断原因和已触发的 MAS-owned 修复动作。",
            "OPL family user config 是 developer_apply_safe authority 的用户级来源；如 authority 不足，报告 gate 与 why_not_applied。",
            "输出中文、简洁、带具体时间和 active_run_id。",
        ]
    )


def _string_values(value: object, *, key: str | None = None) -> Iterable[tuple[str | None, str]]:
    if isinstance(value, str):
        yield key, value
    elif isinstance(value, dict):
        for nested_key, nested_value in value.items():
            yield from _string_values(nested_value, key=str(nested_key))
    elif isinstance(value, list):
        for item in value:
            yield from _string_values(item, key=key)


def _base_result(*, path: Path, status: str, active: bool, prompt_contains_required_tokens: bool) -> dict[str, Any]:
    return {
        "path": str(path),
        "status": status,
        "active": active,
        "prompt_contains_required_tokens": prompt_contains_required_tokens,
        "scope_policy": SCOPE_POLICY,
        "new_task_auto_enrollment_required": True,
        "required_prompt_tokens": list(CODEX_APP_AUTOMATION_REQUIRED_PROMPT_TOKENS),
        "canonical_prompt": canonical_codex_app_automation_prompt(),
        "recommended_prompt": canonical_codex_app_automation_prompt(),
    }


def codex_app_automation_prompt_check(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            **_base_result(path=path, status="missing", active=False, prompt_contains_required_tokens=False),
            "missing_prompt_tokens": list(CODEX_APP_AUTOMATION_REQUIRED_PROMPT_TOKENS),
        }
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return {
            **_base_result(path=path, status="invalid", active=False, prompt_contains_required_tokens=False),
            "missing_prompt_tokens": list(CODEX_APP_AUTOMATION_REQUIRED_PROMPT_TOKENS),
            "details": str(exc),
        }
    status_values = [value.strip().upper() for key, value in _string_values(payload) if key == "status" and value.strip()]
    prompt_text = "\n".join(value for key, value in _string_values(payload) if key == "prompt" and value.strip())
    missing_tokens = [token for token in CODEX_APP_AUTOMATION_REQUIRED_PROMPT_TOKENS if token not in prompt_text]
    active = "ACTIVE" in status_values
    return {
        **_base_result(
            path=path,
            status="ok" if active and not missing_tokens else "incomplete",
            active=active,
            prompt_contains_required_tokens=not missing_tokens,
        ),
        "status_values": status_values,
        "missing_prompt_tokens": missing_tokens,
    }


__all__ = [
    "CODEX_APP_AUTOMATION_REQUIRED_PROMPT_TOKENS",
    "canonical_codex_app_automation_prompt",
    "codex_app_automation_prompt_check",
]
