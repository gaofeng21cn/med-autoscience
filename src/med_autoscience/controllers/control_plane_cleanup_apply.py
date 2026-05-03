from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
CONTRACT_NAME = "control_plane_cleanup_apply.json"
ALLOWED_PHYSICAL_ACTIONS = frozenset({"delete-safe-cache"})
LIVE_RUNTIME_STATUSES = frozenset({"running", "active"})
TERMINAL_RUNTIME_STATUSES = frozenset({"stopped", "completed", "failed", "terminal", "parked"})


def run_cleanup_apply(
    *,
    workspace_roots: Iterable[str | Path],
    apply: bool = False,
) -> dict[str, Any]:
    workspaces: list[dict[str, Any]] = []
    apply_plan: list[dict[str, Any]] = []
    applied_actions: list[dict[str, Any]] = []

    for root in sorted(Path(item).expanduser().resolve() for item in workspace_roots):
        workspace_report = _workspace_plan(workspace_root=root)
        workspaces.append(workspace_report["workspace"])
        for action in workspace_report["actions"]:
            planned_action = dict(action)
            if apply and planned_action["eligible_for_apply"]:
                applied = _apply_action(workspace_root=root, action=planned_action)
                planned_action["applied"] = applied["applied"]
                planned_action["apply_result"] = applied
                if applied["applied"]:
                    applied_actions.append(planned_action)
            apply_plan.append(planned_action)

    blocked_count = sum(1 for item in apply_plan if item["blockers"])
    eligible_count = sum(1 for item in apply_plan if item["eligible_for_apply"])
    applied_count = len(applied_actions)
    contract_count = sum(1 for item in workspaces if item["contract_present"])
    return {
        "surface": "control_plane_cleanup_apply",
        "schema_version": SCHEMA_VERSION,
        "apply": bool(apply),
        "status": _report_status(
            applied_count=applied_count,
            blocked_count=blocked_count,
            contract_count=contract_count,
            workspace_count=len(workspaces),
        ),
        "workspace_count": len(workspaces),
        "action_counts": {
            "planned": eligible_count,
            "blocked": blocked_count,
            "applied": applied_count,
            "mutating": applied_count,
        },
        "mutation_policy": {
            "migration_audit_remains_dry_run_only": True,
            "live_runtime_audit_only": True,
            "allowed_physical_actions": sorted(ALLOWED_PHYSICAL_ACTIONS),
        },
        "workspaces": workspaces,
        "apply_plan": apply_plan,
        "applied_actions": applied_actions,
    }


def _workspace_plan(*, workspace_root: Path) -> dict[str, Any]:
    contract_path = workspace_root / CONTRACT_NAME
    contract = _read_json(contract_path)
    runtime = _mapping(contract.get("runtime"))
    controller_decision = _mapping(contract.get("controller_decision"))
    allowlist = {
        text
        for item in _list(contract.get("action_allowlist"))
        if (text := _text(item)) is not None
    }
    actions = [
        _plan_action(
            workspace_root=workspace_root,
            runtime=runtime,
            controller_decision=controller_decision,
            allowlist=allowlist,
            action_payload=_mapping(item),
        )
        for item in _list(contract.get("actions"))
    ]
    return {
        "workspace": {
            "workspace_root": str(workspace_root),
            "contract_path": str(contract_path),
            "contract_present": contract_path.exists(),
            "runtime_status": _text(runtime.get("status")),
            "action_count": len(actions),
        },
        "actions": actions,
    }


def _plan_action(
    *,
    workspace_root: Path,
    runtime: Mapping[str, Any],
    controller_decision: Mapping[str, Any],
    allowlist: set[str],
    action_payload: Mapping[str, Any],
) -> dict[str, Any]:
    action = _text(action_payload.get("action")) or "unknown"
    target_ref = _text(action_payload.get("target_path"))
    target_path = (workspace_root / target_ref).resolve() if target_ref else workspace_root
    artifact_role = _text(action_payload.get("artifact_role")) or "unknown"
    restore_contract = _mapping(action_payload.get("restore_contract"))
    blockers: list[str] = []
    runtime_status = _text(runtime.get("status"))

    if runtime_status in LIVE_RUNTIME_STATUSES:
        blockers.append("live_runtime_active")
    elif runtime_status not in TERMINAL_RUNTIME_STATUSES:
        blockers.append("runtime_not_terminal")
    if controller_decision.get("apply_intent") is not True or _text(controller_decision.get("decision")) != "approve_cleanup_apply":
        blockers.append("controller_apply_intent_missing")
    if action not in ALLOWED_PHYSICAL_ACTIONS:
        blockers.append("action_not_allowlisted")
    if action not in allowlist:
        blockers.append("action_not_allowlisted")
    try:
        target_path.relative_to(workspace_root.resolve())
    except ValueError:
        blockers.append("target_outside_workspace")
    restore_blockers = _restore_contract_blockers(
        workspace_root=workspace_root,
        target_path=target_path,
        restore_contract=restore_contract,
    )
    if restore_blockers:
        blockers.extend(restore_blockers)
    if artifact_role in {"data_release", "runtime_payload"} and not restore_contract:
        blockers.append("missing_restore_contract")

    candidate_action = "audit-only" if "live_runtime_active" in blockers else action
    return {
        "workspace_root": str(workspace_root),
        "action": action,
        "candidate_action": candidate_action,
        "target_path": str(target_path),
        "artifact_role": artifact_role,
        "eligible_for_apply": not blockers,
        "blockers": _dedupe(blockers),
        "restore_contract": dict(restore_contract),
        "applied": False,
    }


def _restore_contract_blockers(
    *,
    workspace_root: Path,
    target_path: Path,
    restore_contract: Mapping[str, Any],
) -> list[str]:
    if not restore_contract:
        return ["missing_restore_contract"]
    blockers: list[str] = []
    restore_index = _text(restore_contract.get("restore_index_path") or restore_contract.get("restore_index"))
    checksum = _text(restore_contract.get("sha256") or restore_contract.get("checksum"))
    rehydrate = _mapping(restore_contract.get("rehydrate_verification"))
    if restore_index is None:
        blockers.append("missing_restore_index")
    elif not (workspace_root / restore_index).exists():
        blockers.append("missing_restore_index")
    if checksum is None:
        blockers.append("missing_checksum")
    elif target_path.exists() and _path_sha256(target_path) != checksum:
        blockers.append("checksum_mismatch")
    if _text(rehydrate.get("status")) != "verified":
        blockers.append("missing_rehydrate_verification")
    return blockers


def _report_status(
    *,
    applied_count: int,
    blocked_count: int,
    contract_count: int,
    workspace_count: int,
) -> str:
    if applied_count:
        return "applied"
    if blocked_count:
        return "blocked"
    if workspace_count and not contract_count:
        return "no_contract"
    return "planned"


def _apply_action(*, workspace_root: Path, action: Mapping[str, Any]) -> dict[str, Any]:
    target_path = Path(str(action["target_path"]))
    action_id = _text(action.get("action"))
    if action_id == "delete-safe-cache":
        if target_path.is_dir():
            shutil.rmtree(target_path)
        elif target_path.exists():
            target_path.unlink()
        return {"applied": True, "action": action_id, "target_path": str(target_path)}
    return {
        "applied": False,
        "action": action_id,
        "target_path": str(target_path),
        "reason": "apply_action_not_implemented_for_non_delete_safe_cache",
        "workspace_root": str(workspace_root),
    }


def _path_sha256(path: Path) -> str:
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(child.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _dedupe(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


__all__ = ["run_cleanup_apply"]
