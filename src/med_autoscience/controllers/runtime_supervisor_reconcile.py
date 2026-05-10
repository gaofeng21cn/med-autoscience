from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from . import outer_supervision_slo, paper_progress_reconciler, runtime_supervisor_consumer
from . import runtime_supervisor_dispatch_executor, runtime_supervisor_scan
from . import runtime_dispatch_cost


SCHEMA_VERSION = 1
RECONCILE_LATEST_RELATIVE_PATH = Path("artifacts/supervision/reconcile/latest.json")
RECONCILE_HISTORY_RELATIVE_PATH = Path("artifacts/supervision/reconcile/history.jsonl")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def _latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / RECONCILE_LATEST_RELATIVE_PATH


def _history_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / RECONCILE_HISTORY_RELATIVE_PATH


def _study_map(scan_payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    studies: dict[str, dict[str, Any]] = {}
    for item in scan_payload.get("studies") or []:
        study = _mapping(item)
        study_id = _text(study.get("study_id"))
        if study_id is not None:
            studies[study_id] = study
    return studies


def _study_action_queue(scan_payload: Mapping[str, Any], study_id: str) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for action in scan_payload.get("action_queue") or []:
        payload = _mapping(action)
        if _text(payload.get("study_id")) == study_id:
            actions.append(payload)
    return actions


def _study_projection(scan_payload: Mapping[str, Any], study_id: str) -> dict[str, Any]:
    study = _study_map(scan_payload).get(study_id, {})
    return {
        "owner_route": _mapping(study.get("owner_route")) or None,
        "action_queue": _study_action_queue(scan_payload, study_id) or list(study.get("action_queue") or []),
        "why_not_applied": study.get("why_not_applied"),
        "owner_forwarded": study.get("owner_forwarded"),
        "stable_blocker": (
            _mapping(study.get("stable_blocker"))
            or _mapping(study.get("block_state"))
            or _mapping(study.get("current_blocker"))
            or None
        ),
    }


def _resolve_study_ids(
    *,
    requested: Iterable[str],
    before_scan: Mapping[str, Any],
    after_scan: Mapping[str, Any],
    consumed: Mapping[str, Any],
    executed: Mapping[str, Any],
) -> tuple[str, ...]:
    resolved: list[str] = [study_id for item in requested if (study_id := _text(item)) is not None]
    for source in (before_scan, after_scan):
        for study in source.get("studies") or []:
            if isinstance(study, Mapping) and (study_id := _text(study.get("study_id"))) is not None:
                resolved.append(study_id)
        for action in source.get("action_queue") or []:
            if isinstance(action, Mapping) and (study_id := _text(action.get("study_id"))) is not None:
                resolved.append(study_id)
    for key in ("request_tasks", "repair_tasks", "default_executor_dispatches"):
        for item in consumed.get(key) or []:
            if isinstance(item, Mapping) and (study_id := _text(item.get("study_id"))) is not None:
                resolved.append(study_id)
    for execution in executed.get("executions") or []:
        if isinstance(execution, Mapping) and (study_id := _text(execution.get("study_id"))) is not None:
            resolved.append(study_id)
    return tuple(dict.fromkeys(resolved))


def _step_receipts(
    *,
    before_scan: Mapping[str, Any],
    consumed: Mapping[str, Any],
    executed: Mapping[str, Any],
    after_scan: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "step": "scan",
            "surface": before_scan.get("surface"),
            "study_count": len(before_scan.get("studies") or []),
            "action_count": len(before_scan.get("action_queue") or []),
        },
        {
            "step": "consume",
            "surface": consumed.get("surface"),
            "repair_task_count": consumed.get("repair_task_count"),
            "request_task_count": consumed.get("request_task_count"),
            "default_executor_dispatch_count": consumed.get("default_executor_dispatch_count"),
        },
        {
            "step": "execute-dispatch",
            "surface": executed.get("surface"),
            "execution_count": executed.get("execution_count"),
            "executed_count": executed.get("executed_count"),
            "blocked_count": executed.get("blocked_count"),
        },
        {
            "step": "rescan",
            "surface": after_scan.get("surface"),
            "study_count": len(after_scan.get("studies") or []),
            "action_count": len(after_scan.get("action_queue") or []),
        },
    ]


def _dispatch_counters(*, consumed: Mapping[str, Any], executed: Mapping[str, Any]) -> dict[str, Any]:
    codex_dispatch_count = int(executed.get("codex_dispatch_count") or 0)
    suppressed_dispatch_count = int(executed.get("suppressed_dispatch_count") or 0) + int(
        consumed.get("repeat_suppressed_count") or 0
    )
    return {
        "codex_dispatch_count": codex_dispatch_count,
        "suppressed_dispatch_count": suppressed_dispatch_count,
        "default_executor_dispatch_count": int(consumed.get("default_executor_dispatch_count") or 0),
        "executed_count": int(executed.get("executed_count") or 0),
        "blocked_count": int(executed.get("blocked_count") or 0),
        "dry_run_count": int(executed.get("dry_run_count") or 0),
        "dispatch_budget_window": runtime_dispatch_cost.dispatch_budget_window(),
        "action_fingerprints": list(executed.get("action_fingerprints") or []),
    }


def supervisor_reconcile(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
) -> dict[str, Any]:
    generated_at = _utc_now()
    requested_study_ids = tuple(study_id for item in study_ids if (study_id := _text(item)) is not None)
    before_scan = runtime_supervisor_scan.supervisor_scan(
        profile=profile,
        study_ids=requested_study_ids or runtime_supervisor_scan.resolve_supervisor_scan_study_ids(profile),
        apply_safe_actions=apply,
        apply_runtime_platform_repair=False,
        developer_supervisor_mode=mode,
    )
    consumed = runtime_supervisor_consumer.supervisor_consume(
        profile=profile,
        study_ids=requested_study_ids,
        mode=mode,
        apply=apply,
    )
    executed = runtime_supervisor_dispatch_executor.execute_default_executor_dispatches(
        profile=profile,
        study_ids=requested_study_ids,
        action_types=(),
        mode=mode,
        apply=apply,
    )
    resolved_study_ids = _resolve_study_ids(
        requested=requested_study_ids,
        before_scan=before_scan,
        after_scan={},
        consumed=consumed,
        executed=executed,
    )
    after_scan = runtime_supervisor_scan.supervisor_scan(
        profile=profile,
        study_ids=resolved_study_ids,
        apply_safe_actions=apply,
        apply_runtime_platform_repair=False,
        developer_supervisor_mode=mode,
    )
    resolved_study_ids = _resolve_study_ids(
        requested=resolved_study_ids,
        before_scan=before_scan,
        after_scan=after_scan,
        consumed=consumed,
        executed=executed,
    )
    study_receipts = [
        {
            "study_id": study_id,
            "before": _study_projection(before_scan, study_id),
            "after": _study_projection(after_scan, study_id),
        }
        for study_id in resolved_study_ids
    ]
    dispatch_counters = _dispatch_counters(consumed=consumed, executed=executed)
    paper_progress_reconcile = paper_progress_reconciler.build_paper_progress_reconcile_receipt(
        profile=profile,
        requested_study_ids=requested_study_ids,
        resolved_study_ids=resolved_study_ids,
        before_scan=before_scan,
        consumed=consumed,
        executed=executed,
        after_scan=after_scan,
        apply=apply,
        generated_at=generated_at,
    )
    action_cost = (
        runtime_dispatch_cost.reconcile_dry_run_contract(
            reason="runtime_supervisor_reconcile_dry_run",
            action_fingerprint=f"runtime_supervisor_reconcile::{','.join(resolved_study_ids) or 'workspace'}",
        )
        if not apply
        else runtime_dispatch_cost.controller_apply_contract(
            reason="runtime_supervisor_reconcile_controller_apply",
            action_fingerprint=f"runtime_supervisor_reconcile::{','.join(resolved_study_ids) or 'workspace'}",
        )
    )
    latest_path = _latest_path(profile)
    history_path = _history_path(profile)
    payload = {
        "surface": "runtime_supervisor_reconcile_receipt",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "dry_run": not apply,
        "requested_mode": mode,
        "requested_studies": list(requested_study_ids),
        "resolved_studies": list(resolved_study_ids),
        "step_receipts": _step_receipts(
            before_scan=before_scan,
            consumed=consumed,
            executed=executed,
            after_scan=after_scan,
        ),
        "before": {
            "studies": list(before_scan.get("studies") or []),
            "action_queue": list(before_scan.get("action_queue") or []),
        },
        "after": {
            "studies": list(after_scan.get("studies") or []),
            "action_queue": list(after_scan.get("action_queue") or []),
        },
        "consumed": consumed,
        "executed_dispatch": executed,
        "action_class": action_cost["action_class"],
        "will_start_llm": dispatch_counters["codex_dispatch_count"] > 0,
        "action_cost": {**action_cost, "will_start_llm": dispatch_counters["codex_dispatch_count"] > 0},
        "dispatch_counters": dispatch_counters,
        **dispatch_counters,
        "paper_progress_reconcile": paper_progress_reconcile,
        "study_receipts": study_receipts,
        "refs": {
            "latest_path": str(latest_path),
            "history_path": str(history_path),
        },
    }
    payload["outer_supervision_slo"] = outer_supervision_slo.build_outer_supervision_slo_projection(
        profile=profile,
        study_id=resolved_study_ids[0] if len(resolved_study_ids) == 1 else None,
        reconcile_payload=payload,
        generated_at=generated_at,
    )
    _write_json(latest_path, payload)
    _append_json_line(
        history_path,
        {
            "generated_at": generated_at,
            "study_ids": list(resolved_study_ids),
            "dry_run": not apply,
            "execution_count": executed.get("execution_count"),
            "blocked_count": executed.get("blocked_count"),
        },
    )
    return payload


__all__ = [
    "RECONCILE_HISTORY_RELATIVE_PATH",
    "RECONCILE_LATEST_RELATIVE_PATH",
    "SCHEMA_VERSION",
    "supervisor_reconcile",
]
