from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.control_plane_route_gate import authorize_control_plane_route


SCHEMA_VERSION = 1
CONTRACT_NAME = "control_plane_cleanup_apply.json"
ALLOWED_PHYSICAL_ACTIONS = frozenset({"delete-safe-cache"})
LIVE_RUNTIME_STATUSES = frozenset({"running", "active"})
TERMINAL_RUNTIME_STATUSES = frozenset({"stopped", "completed", "failed", "terminal", "parked"})


def run_cleanup_apply(
    *,
    workspace_roots: Iterable[str | Path],
    apply: bool = False,
    control_plane_snapshot: Mapping[str, Any] | None = None,
    retention_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    workspaces: list[dict[str, Any]] = []
    apply_plan: list[dict[str, Any]] = []
    applied_actions: list[dict[str, Any]] = []
    if apply:
        control_plane_route_gate = authorize_control_plane_route(
            "cleanup_apply",
            {"control_plane_snapshot": dict(control_plane_snapshot or {})},
        )
    else:
        gate = authorize_control_plane_route("cleanup_apply", {"projection_only": True})
        control_plane_route_gate = {
            **gate,
            "authorized": True,
            "allowed": True,
            "blocking_reasons": [],
            "planning_only": True,
        }

    for root in sorted(Path(item).expanduser().resolve() for item in workspace_roots):
        workspace_report = _workspace_plan(
            workspace_root=root,
            control_plane_route_gate=control_plane_route_gate,
            retention_report=retention_report,
        )
        workspaces.append(workspace_report["workspace"])
        for action in workspace_report["actions"]:
            planned_action = dict(action)
            if apply and control_plane_route_gate.get("authorized") and planned_action["eligible_for_apply"]:
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
        "control_plane_route_gate": control_plane_route_gate,
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


def _workspace_plan(
    *,
    workspace_root: Path,
    control_plane_route_gate: Mapping[str, Any],
    retention_report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    contract_path = workspace_root / CONTRACT_NAME
    contract = _read_json(contract_path)
    runtime = _mapping(contract.get("runtime"))
    controller_decision = _mapping(contract.get("controller_decision"))
    allowlist = {
        text
        for item in _list(contract.get("action_allowlist"))
        if (text := _text(item)) is not None
    }
    contract_actions = [
        _plan_action(
            workspace_root=workspace_root,
            runtime=runtime,
            controller_decision=controller_decision,
            allowlist=allowlist,
            control_plane_route_gate=control_plane_route_gate,
            action_payload=_mapping(item),
        )
        for item in _list(contract.get("actions"))
    ]
    report_actions = [
        _plan_action(
            workspace_root=workspace_root,
            runtime=runtime,
            controller_decision=controller_decision,
            allowlist=allowlist | ALLOWED_PHYSICAL_ACTIONS,
            control_plane_route_gate=control_plane_route_gate,
            action_payload=item,
        )
        for item in _retention_report_safe_cache_actions(
            workspace_root=workspace_root,
            retention_report=retention_report,
        )
    ]
    actions = [*contract_actions, *report_actions]
    return {
        "workspace": {
            "workspace_root": str(workspace_root),
            "contract_path": str(contract_path),
            "contract_present": contract_path.exists(),
            "runtime_status": _text(runtime.get("status")),
            "action_count": len(actions),
            "retention_report_candidate_count": len(report_actions),
        },
        "actions": actions,
    }


def _control_plane_gate_blockers(control_plane_route_gate: Mapping[str, Any]) -> list[str]:
    if bool(control_plane_route_gate.get("authorized")):
        return []
    return [
        f"control_plane_route_gate:{reason}"
        for reason in _list(control_plane_route_gate.get("blocking_reasons"))
        if _text(reason) is not None
    ]


def _runtime_blockers(runtime_status: str | None) -> list[str]:
    if runtime_status in LIVE_RUNTIME_STATUSES:
        return ["live_runtime_active"]
    if runtime_status not in TERMINAL_RUNTIME_STATUSES:
        return ["runtime_not_terminal"]
    return []


def _controller_decision_blockers(controller_decision: Mapping[str, Any]) -> list[str]:
    if (
        controller_decision.get("apply_intent") is True
        and _text(controller_decision.get("decision")) == "approve_cleanup_apply"
    ):
        return []
    return ["controller_apply_intent_missing"]


def _action_allowlist_blockers(*, action: str, allowlist: set[str]) -> list[str]:
    blockers: list[str] = []
    if action not in ALLOWED_PHYSICAL_ACTIONS:
        blockers.append("action_not_allowlisted")
    if action not in allowlist:
        blockers.append("action_not_allowlisted")
    return blockers


def _target_path_blockers(*, workspace_root: Path, target_path: Path) -> list[str]:
    try:
        target_path.relative_to(workspace_root.resolve())
    except ValueError:
        return ["target_outside_workspace"]
    return []


def _target_allowlist_blockers(action_payload: Mapping[str, Any]) -> list[str]:
    if _mapping(action_payload.get("target_allowlist")):
        return []
    return ["target_allowlist_missing"]


def _artifact_role_blockers(*, artifact_role: str, restore_contract: Mapping[str, Any]) -> list[str]:
    if artifact_role == "safe_cache":
        return []
    if artifact_role in {"data_release", "runtime_payload"} and not restore_contract:
        return ["missing_restore_contract"]
    return []


def _plan_action(
    *,
    workspace_root: Path,
    runtime: Mapping[str, Any],
    controller_decision: Mapping[str, Any],
    allowlist: set[str],
    control_plane_route_gate: Mapping[str, Any],
    action_payload: Mapping[str, Any],
) -> dict[str, Any]:
    action = _text(action_payload.get("action")) or "unknown"
    target_ref = _text(action_payload.get("target_path"))
    target_path = (workspace_root / target_ref).resolve() if target_ref else workspace_root
    artifact_role = _text(action_payload.get("artifact_role")) or "unknown"
    restore_contract = _mapping(action_payload.get("restore_contract"))
    safe_cache_candidate = _mapping(action_payload.get("safe_cache_candidate"))
    runtime_status = _text(runtime.get("status"))
    blockers = _dedupe(
        [
            *_control_plane_gate_blockers(control_plane_route_gate),
            *_runtime_blockers(runtime_status),
            *_controller_decision_blockers(controller_decision),
            *_action_allowlist_blockers(action=action, allowlist=allowlist),
            *_target_path_blockers(workspace_root=workspace_root, target_path=target_path),
            *_target_allowlist_blockers(action_payload),
            *_restore_contract_blockers(
                workspace_root=workspace_root,
                target_path=target_path,
                restore_contract=restore_contract,
                restore_contract_required=artifact_role != "safe_cache",
            ),
            *_artifact_role_blockers(artifact_role=artifact_role, restore_contract=restore_contract),
        ]
    )

    candidate_action = "audit-only" if "live_runtime_active" in blockers else action
    audit_payload = {
        "candidate_source": _text(action_payload.get("source")) or "cleanup_apply_contract",
        "source_ref": _text(safe_cache_candidate.get("source_ref")),
        "requested_action": action,
        "candidate_action": candidate_action,
        "artifact_role": artifact_role,
        "workspace_root": str(workspace_root),
        "target_path": str(target_path),
        "workspace_relative_path": _workspace_relative_target(
            workspace_root=workspace_root,
            target_path=target_path,
        ),
        "safe_cache_candidate": dict(safe_cache_candidate),
        "blocked_reasons": list(blockers),
        "target_allowlist": dict(_mapping(action_payload.get("target_allowlist"))),
        "control_plane_route_gate": {
            "authorized": bool(control_plane_route_gate.get("authorized")),
            "action": _text(control_plane_route_gate.get("action")),
            "snapshot_ref": dict(_mapping(control_plane_route_gate.get("snapshot_ref"))),
        },
    }
    return {
        "workspace_root": str(workspace_root),
        "action": action,
        "candidate_action": candidate_action,
        "target_path": str(target_path),
        "artifact_role": artifact_role,
        "safe_cache_candidate": dict(safe_cache_candidate),
        "audit_payload": audit_payload,
        "eligible_for_apply": not blockers,
        "blockers": blockers,
        "control_plane_route_gate": dict(control_plane_route_gate),
        "restore_contract": dict(restore_contract),
        "applied": False,
    }


def _restore_contract_blockers(
    *,
    workspace_root: Path,
    target_path: Path,
    restore_contract: Mapping[str, Any],
    restore_contract_required: bool,
) -> list[str]:
    blockers: list[str] = []
    if not restore_contract:
        if not restore_contract_required:
            return []
        blockers.append("missing_restore_contract")
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


def _retention_report_safe_cache_actions(
    *,
    workspace_root: Path,
    retention_report: Mapping[str, Any] | None,
) -> list[Mapping[str, Any]]:
    if not retention_report:
        return []
    actions: list[Mapping[str, Any]] = []
    for source_ref, operation in _iter_retention_operations(
        workspace_root=workspace_root,
        retention_report=retention_report,
    ):
        if not _is_delete_safe_cache_candidate(operation):
            continue
        target_ref = _text(operation.get("workspace_relative_path")) or _text(operation.get("path"))
        if target_ref is None:
            continue
        actions.append(
            {
                "action": "delete-safe-cache",
                "target_path": target_ref,
                "artifact_role": "safe_cache",
                "source": "retention_report",
                "target_allowlist": {
                    "source": "retention_report",
                    "source_ref": source_ref,
                    "target_path": target_ref,
                },
                "safe_cache_candidate": {
                    "source": "retention_report",
                    "source_ref": source_ref,
                    "retention_action": _text(operation.get("retention_action")),
                    "cleanup_candidate_action": _text(operation.get("cleanup_candidate_action")),
                    "workspace_relative_path": _text(operation.get("workspace_relative_path")),
                    "path": _text(operation.get("path")),
                },
            }
        )
    return actions


def _iter_retention_operations(
    *,
    workspace_root: Path,
    retention_report: Mapping[str, Any],
) -> Iterable[tuple[str, Mapping[str, Any]]]:
    if _workspace_matches(workspace_root, _text(retention_report.get("workspace_root"))):
        plan = retention_report
        for index, operation in enumerate(_plan_operations(plan)):
            yield f"retention_report.operations[{index}]", operation

    for workspace_index, workspace in enumerate(_list(retention_report.get("workspaces"))):
        workspace_payload = _mapping(workspace)
        if not _workspace_matches(workspace_root, _text(workspace_payload.get("workspace_root"))):
            continue
        plan = _mapping(workspace_payload.get("retention_plan"))
        for index, operation in enumerate(_plan_operations(plan)):
            yield f"workspaces[{workspace_index}].retention_plan.operation_sample[{index}]", operation


def _plan_operations(plan: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    operations = _list(plan.get("operations"))
    if not operations:
        operations = _list(plan.get("operation_sample"))
    return [_mapping(item) for item in operations if _mapping(item)]


def _is_delete_safe_cache_candidate(operation: Mapping[str, Any]) -> bool:
    return (
        _text(operation.get("retention_action")) == "delete_safe_cache"
        and _text(operation.get("cleanup_candidate_action")) == "delete-safe-cache"
        and operation.get("physical_delete_allowed") is True
    )


def _workspace_matches(workspace_root: Path, candidate_root: str | None) -> bool:
    if not candidate_root:
        return False
    return Path(candidate_root).expanduser().resolve() == workspace_root


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
    blockers = _apply_action_blockers(workspace_root=workspace_root, target_path=target_path, action=action)
    if blockers:
        return {
            "applied": False,
            "action": action_id,
            "target_path": str(target_path),
            "workspace_root": str(workspace_root),
            "reason": "apply_action_guard_blocked",
            "blockers": blockers,
        }
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


def _apply_action_blockers(
    *,
    workspace_root: Path,
    target_path: Path,
    action: Mapping[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if _text(action.get("action")) not in ALLOWED_PHYSICAL_ACTIONS:
        blockers.append("action_not_allowlisted")
    if action.get("eligible_for_apply") is not True:
        blockers.append("action_not_eligible_for_apply")
    blockers.extend(_target_path_blockers(workspace_root=workspace_root, target_path=target_path))
    audit_payload = _mapping(action.get("audit_payload"))
    if not audit_payload:
        blockers.append("audit_payload_missing")
    elif _text(audit_payload.get("requested_action")) != _text(action.get("action")):
        blockers.append("audit_payload_action_mismatch")
    if not _mapping(audit_payload.get("target_allowlist")):
        blockers.append("audit_payload_target_allowlist_missing")
    return _dedupe(blockers)


def _workspace_relative_target(*, workspace_root: Path, target_path: Path) -> str | None:
    try:
        return target_path.relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        return None


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
