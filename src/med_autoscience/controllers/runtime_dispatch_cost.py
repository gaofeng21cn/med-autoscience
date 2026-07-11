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
    "observe_only_contract",
    "reconcile_dry_run_contract",
]
