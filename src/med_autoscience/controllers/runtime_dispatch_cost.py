from __future__ import annotations

from collections.abc import Mapping
from typing import Any


OBSERVE_ONLY = "observe_only"
RECONCILE_DRY_RUN = "reconcile_dry_run"
CONTROLLER_APPLY = "controller_apply"
CODEX_WORKER_DISPATCH = "codex_worker_dispatch"

ACTION_CLASSES = frozenset(
    {
        OBSERVE_ONLY,
        RECONCILE_DRY_RUN,
        CONTROLLER_APPLY,
        CODEX_WORKER_DISPATCH,
    }
)


def action_cost_contract(
    *,
    action_class: str,
    will_start_llm: bool,
    reason: str,
    action_fingerprint: str | None = None,
    recommended_command: str | None = None,
) -> dict[str, Any]:
    resolved_class = action_class if action_class in ACTION_CLASSES else OBSERVE_ONLY
    return {
        "schema_version": 1,
        "surface_kind": "runtime_dispatch_cost_contract",
        "action_class": resolved_class,
        "will_start_llm": bool(will_start_llm),
        "reason": reason,
        "action_fingerprint": action_fingerprint,
        "recommended_command": recommended_command,
        "llm_dispatch_allowed": resolved_class == CODEX_WORKER_DISPATCH,
        "codex_worker_dispatch": resolved_class == CODEX_WORKER_DISPATCH,
    }


def observe_only_contract(*, reason: str, action_fingerprint: str | None = None) -> dict[str, Any]:
    return action_cost_contract(
        action_class=OBSERVE_ONLY,
        will_start_llm=False,
        reason=reason,
        action_fingerprint=action_fingerprint,
    )


def reconcile_dry_run_contract(
    *,
    reason: str,
    action_fingerprint: str | None = None,
    recommended_command: str | None = None,
) -> dict[str, Any]:
    return action_cost_contract(
        action_class=RECONCILE_DRY_RUN,
        will_start_llm=False,
        reason=reason,
        action_fingerprint=action_fingerprint,
        recommended_command=recommended_command,
    )


def controller_apply_contract(*, reason: str, action_fingerprint: str | None = None) -> dict[str, Any]:
    return action_cost_contract(
        action_class=CONTROLLER_APPLY,
        will_start_llm=False,
        reason=reason,
        action_fingerprint=action_fingerprint,
    )


def codex_worker_dispatch_contract(*, reason: str, action_fingerprint: str | None = None) -> dict[str, Any]:
    return action_cost_contract(
        action_class=CODEX_WORKER_DISPATCH,
        will_start_llm=True,
        reason=reason,
        action_fingerprint=action_fingerprint,
    )


def compact_action_cost(value: object) -> dict[str, Any] | None:
    payload = dict(value) if isinstance(value, Mapping) else {}
    action_cost = payload.get("action_cost")
    if isinstance(action_cost, Mapping):
        payload = dict(action_cost)
    if not payload:
        return None
    action_class = str(payload.get("action_class") or "").strip()
    if action_class not in ACTION_CLASSES:
        return None
    return {
        "surface_kind": "runtime_dispatch_cost_contract",
        "action_class": action_class,
        "will_start_llm": bool(payload.get("will_start_llm")),
        "action_fingerprint": _text(payload.get("action_fingerprint")),
        "recommended_command": _text(payload.get("recommended_command")),
        "llm_dispatch_allowed": bool(payload.get("llm_dispatch_allowed")),
        "codex_worker_dispatch": bool(payload.get("codex_worker_dispatch")),
    }


def dispatch_budget_window(
    *,
    scope: str = "owner_route_action_fingerprint",
    max_codex_dispatches: int = 1,
) -> dict[str, Any]:
    return {
        "scope": scope,
        "max_codex_dispatches": int(max_codex_dispatches),
        "duplicate_policy": "suppress_same_action_fingerprint",
        "dry_run_starts_llm": False,
        "observe_only_starts_llm": False,
    }


def dispatch_action_fingerprint(*, dispatch: Mapping[str, Any], dispatch_path: Any) -> str:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    for value in (
        dispatch.get("work_unit_fingerprint"),
        dispatch.get("action_fingerprint"),
        prompt_contract.get("work_unit_fingerprint"),
        prompt_contract.get("repeat_suppression_key"),
        dispatch.get("idempotency_key"),
        prompt_contract.get("idempotency_key"),
    ):
        if text := _text(value):
            return text
    return f"default_executor_dispatch::{dispatch_path.as_posix()}"


def executor_action_cost(
    *,
    action_type: str,
    apply: bool,
    execution: Mapping[str, Any],
    action_fingerprint: str,
) -> dict[str, Any]:
    status = _text(execution.get("execution_status"))
    if not apply or status == "dry_run":
        return reconcile_dry_run_contract(
            reason="default_executor_dispatch_dry_run",
            action_fingerprint=action_fingerprint,
        )
    if status in {"repeat_suppressed", "blocked"}:
        return observe_only_contract(
            reason=f"default_executor_dispatch_{status}",
            action_fingerprint=action_fingerprint,
        )
    if action_type == "runtime_platform_repair" and runtime_platform_repair_started_worker(execution):
        return codex_worker_dispatch_contract(
            reason="runtime_platform_repair_started_codex_worker",
            action_fingerprint=action_fingerprint,
        )
    return controller_apply_contract(
        reason="default_executor_dispatch_controller_apply",
        action_fingerprint=action_fingerprint,
    )


def runtime_platform_repair_started_worker(execution: Mapping[str, Any]) -> bool:
    owner_result = _mapping(execution.get("owner_result"))
    candidates: list[Mapping[str, Any]] = [owner_result]
    for key in ("resume_result", "ensure_runtime_result", "runtime_platform_repair_apply", "owner_result"):
        nested = _mapping(owner_result.get(key))
        if nested:
            candidates.append(nested)
    return any(
        candidate.get("started") is True
        or candidate.get("worker_running") is True
        or (_text(candidate.get("active_run_id")) is not None and _text(candidate.get("status")) in {"running", "scheduled"})
        for candidate in candidates
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ACTION_CLASSES",
    "CODEX_WORKER_DISPATCH",
    "CONTROLLER_APPLY",
    "OBSERVE_ONLY",
    "RECONCILE_DRY_RUN",
    "action_cost_contract",
    "codex_worker_dispatch_contract",
    "compact_action_cost",
    "controller_apply_contract",
    "dispatch_budget_window",
    "dispatch_action_fingerprint",
    "executor_action_cost",
    "observe_only_contract",
    "reconcile_dry_run_contract",
    "runtime_platform_repair_started_worker",
]
