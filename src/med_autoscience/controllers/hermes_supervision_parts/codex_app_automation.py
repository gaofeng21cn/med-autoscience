from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import tomllib
from typing import Any


CODEX_APP_AUTOMATION_REQUIRED_PROMPT_TOKENS = (
    "developer_apply_safe",
    "mode=developer_apply_safe",
    "supervisor-reconcile --mode developer_apply_safe --apply",
    "supervisor-scan --apply-safe-actions",
    "--apply-runtime-platform-repair",
    "--developer-supervisor-mode developer_apply_safe",
    "supervisor-consume --mode developer_apply_safe --apply",
    "supervisor-execute-dispatch --mode developer_apply_safe --apply",
    "workspace_dynamic_active_studies",
    "new MAS tasks",
    "active_run_id",
    "worker_running",
    "worktree",
    "action_queue",
    "why_not_applied",
)
SCOPE_POLICY = "workspace_dynamic_active_studies"


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
    "codex_app_automation_prompt_check",
]
