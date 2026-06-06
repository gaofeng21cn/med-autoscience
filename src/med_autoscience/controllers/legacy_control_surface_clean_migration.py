from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.controllers.owner_route_reconcile_parts import study_identity
from med_autoscience.profiles import WorkspaceProfile, load_profile
from med_autoscience.study_completion import resolve_study_completion_contract


SURFACE_KIND = "legacy_control_surface_clean_migration"
MIGRATION_ROOT_RELPATH = Path("artifacts") / "runtime" / "legacy_control_surface_clean_migration"
HISTORY_ROOT_RELPATH = MIGRATION_ROOT_RELPATH / "history"
STUDY_MIGRATION_ROOT_RELPATH = Path("artifacts") / "runtime" / "legacy_control_surface_clean_migration"
DISPATCH_ROOT_RELPATH = (
    Path("artifacts") / "supervision" / "consumer" / "default_executor_dispatches"
)
CURRENT_CONTROL_RELPATH = Path("artifacts") / "supervision" / "opl_current_control_state" / "latest.json"
MANUAL_PAUSE_RELPATH = Path("artifacts") / "runtime" / "manual_pause"
RUNTIME_STATE_RELPATH = Path("artifacts") / "runtime" / "state" / "runtime_state.json"
LEGACY_PAUSE_REASON = "manual_pause_for_mas_rebuild"
TOMBSTONE_SURFACE = "legacy_control_surface_tombstone"
DEFAULT_EXECUTOR_SURFACE = "default_executor_dispatch_request"
MANUAL_PAUSE_SURFACE = "mas_quest_manual_pause_receipt"


def run_legacy_control_surface_clean_migration(
    *,
    profile_path: Path,
    study_ids: Iterable[str] | None = None,
    apply: bool,
) -> dict[str, Any]:
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    profile = load_profile(resolved_profile_path)
    selected_study_ids = _resolve_study_ids(profile=profile, study_ids=study_ids)
    recorded_at = _utc_now()
    current_control = _read_json_object(profile.workspace_root / CURRENT_CONTROL_RELPATH)
    studies = [
        _study_plan(
            profile=profile,
            study_id=study_id,
            current_control=current_control,
            recorded_at=recorded_at,
        )
        for study_id in selected_study_ids
    ]
    report: dict[str, Any] = {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "mode": "apply" if apply else "dry_run",
        "recorded_at": recorded_at,
        "profile_path": str(resolved_profile_path),
        "workspace_root": str(profile.workspace_root.expanduser().resolve()),
        "current_control_ref": str((profile.workspace_root / CURRENT_CONTROL_RELPATH).resolve()),
        "authority_boundary": _authority_boundary(apply=apply),
        "migration_policy": {
            "legacy_active_material_after_migration": "provenance_or_tombstone_only",
            "current_action_source_of_truth": "OPL current_control_state action_queue owner_route",
            "missing_current_control_policy": "fail_closed_no_active_path_mutation",
            "current_allowed_actions_retained": True,
            "legacy_reader_compatibility_added": False,
        },
        "study_count": len(studies),
        "studies": studies,
        "next_required_actions": _workspace_next_actions(studies),
    }
    if apply:
        applied = [
            _apply_study_migration(
                profile=profile,
                study_plan=study,
                recorded_at=recorded_at,
            )
            for study in studies
            if study["apply_allowed"]
        ]
        post_studies = [
            _study_plan(
                profile=profile,
                study_id=study_id,
                current_control=current_control,
                recorded_at=recorded_at,
            )
            for study_id in selected_study_ids
        ]
        report["studies"] = post_studies
        report["next_required_actions"] = _workspace_next_actions(post_studies)
        report["post_apply"] = {
            "applied_study_count": len(applied),
            "dispatch_file_tombstone_count": sum(
                item["dispatch_file_tombstone_count"] for item in applied
            ),
            "immutable_action_directory_migration_count": sum(
                item["immutable_action_directory_migration_count"] for item in applied
            ),
            "manual_pause_tombstone_count": sum(
                item["manual_pause_tombstone_count"] for item in applied
            ),
            "runtime_state_pause_migration_count": sum(
                item["runtime_state_pause_migration_count"] for item in applied
            ),
            "applied": applied,
        }
        _write_workspace_receipt(
            profile=profile,
            report=report,
            recorded_at=recorded_at,
        )
    return report


def _resolve_study_ids(*, profile: WorkspaceProfile, study_ids: Iterable[str] | None) -> tuple[str, ...]:
    selected = tuple(item for raw in (study_ids or ()) if (item := _text(raw)) is not None)
    available = set(study_identity.resolve_owner_route_reconcile_study_ids(profile))
    if selected:
        for study_id in selected:
            if study_id not in available:
                known = ", ".join(sorted(available)) or "<none>"
                raise ValueError(f"Unknown legacy control surface study_id: {study_id}; known study_ids: {known}")
        return selected
    return tuple(sorted(available))


def _study_plan(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    current_control: Mapping[str, Any] | None,
    recorded_at: str,
) -> dict[str, Any]:
    study_root = (profile.studies_root / study_id).expanduser().resolve()
    quest_root = (profile.runtime_root / study_id).expanduser().resolve()
    archive_root = profile.workspace_root / HISTORY_ROOT_RELPATH / _history_stamp(recorded_at) / "studies" / study_id
    route = _current_route_for_study(current_control=current_control, study_id=study_id)
    completion_contract = _completed_study_terminal_contract(study_root=study_root, study_id=study_id)
    blockers: list[dict[str, Any]] = []
    if route is None:
        if completion_contract is None:
            blockers.append({"reason": "current_control_state_missing_for_study", "study_id": study_id})
            route = _empty_route(study_id)
        else:
            route = _completion_terminal_route(study_id=study_id, completion_contract=completion_contract)
    if not route["allowed_actions"]:
        if completion_contract is None:
            blockers.append({"reason": "current_control_state_allowed_actions_missing", "study_id": study_id})
    dispatch_plan = _dispatch_migration_plan(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        route=route,
        archive_root=archive_root,
        blockers=blockers,
    )
    manual_pause_plan = _manual_pause_migration_plan(
        profile=profile,
        study_id=study_id,
        quest_root=quest_root,
        route=route,
        archive_root=archive_root,
    )
    receipt_path = study_root / STUDY_MIGRATION_ROOT_RELPATH / "latest.json"
    receipt = _read_json_object(receipt_path)
    migration_count = (
        len(dispatch_plan["dispatch_files"])
        + len(dispatch_plan["immutable_action_directories"])
        + (1 if manual_pause_plan["migration_required"] else 0)
        + (1 if manual_pause_plan["runtime_state_migration_required"] else 0)
    )
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "current_route": route,
        "study_completion_contract": completion_contract,
        "blockers": blockers,
        "dispatch_files": dispatch_plan["dispatch_files"],
        "retained_dispatch_files": dispatch_plan["retained_dispatch_files"],
        "retained_tombstones": dispatch_plan["retained_tombstones"],
        "immutable_action_directories": dispatch_plan["immutable_action_directories"],
        "retained_immutable_action_directories": dispatch_plan["retained_immutable_action_directories"],
        "manual_pause": manual_pause_plan,
        "migration_required": migration_count > 0,
        "migration_count": migration_count,
        "apply_allowed": migration_count > 0 and not blockers,
        "archive_root": str(archive_root),
        "migration_receipt": {
            "path": str(receipt_path),
            "exists": bool(receipt),
            "status": _text(_mapping(receipt).get("status")),
        },
        "next_required_actions": _study_next_actions(migration_count=migration_count, blockers=blockers),
    }


def _completed_study_terminal_contract(*, study_root: Path, study_id: str) -> dict[str, Any] | None:
    try:
        completion = resolve_study_completion_contract(study_root=study_root)
    except (OSError, TypeError, ValueError, yaml.YAMLError):
        return None
    if completion is None or not completion.ready:
        return None
    payload = _read_yaml_object(study_root / "study.yaml")
    execution = _mapping(payload.get("execution"))
    if execution.get("auto_resume") is not False:
        return None
    return {
        "study_id": study_id,
        "status": completion.status.value,
        "ready": True,
        "completed_at": completion.completed_at,
        "evidence_paths": list(completion.evidence_paths),
        "auto_resume": False,
        "source_ref": str((study_root / "study.yaml").resolve()),
    }


def _completion_terminal_route(*, study_id: str, completion_contract: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "study_id": study_id,
        "action_type": None,
        "allowed_actions": [],
        "blocked_actions": [],
        "next_owner": "completion_evidence",
        "current_owner": "study_completion_contract",
        "owner_reason": "study_completion_contract_completed",
        "work_unit_id": "study_completion_contract_completed",
        "work_unit_fingerprint": None,
        "action_id": None,
        "terminal_contract": dict(completion_contract),
    }


def _current_route_for_study(
    *,
    current_control: Mapping[str, Any] | None,
    study_id: str,
) -> dict[str, Any] | None:
    if not isinstance(current_control, Mapping):
        return None
    for item in _list(current_control.get("action_queue")):
        action = _mapping(item)
        owner_route = _mapping(_mapping(action.get("handoff_packet")).get("owner_route")) or _mapping(
            _mapping(action.get("controller_route")).get("owner_route")
        )
        candidate_study_id = (
            _text(action.get("study_id"))
            or _text(owner_route.get("study_id"))
            or _text(_mapping(action.get("controller_route")).get("study_id"))
        )
        if candidate_study_id != study_id:
            continue
        action_type = _text(action.get("action_type"))
        controller_route = _mapping(action.get("controller_route"))
        allowed_actions = set(_string_list(owner_route.get("allowed_actions")))
        allowed_actions.update(_string_list(controller_route.get("controller_actions")))
        if action_type is not None:
            allowed_actions.add(action_type)
        blocked_actions = set(_string_list(owner_route.get("blocked_actions")))
        return {
            "study_id": study_id,
            "action_type": action_type,
            "allowed_actions": sorted(allowed_actions),
            "blocked_actions": sorted(blocked_actions),
            "next_owner": _text(owner_route.get("next_owner")) or _text(action.get("owner")),
            "current_owner": _text(owner_route.get("current_owner")),
            "owner_reason": _text(owner_route.get("owner_reason")),
            "work_unit_id": (
                _text(action.get("controller_work_unit_id"))
                or _text(action.get("executable_work_unit"))
                or _text(controller_route.get("work_unit_id"))
                or _text(_mapping(owner_route.get("source_refs")).get("work_unit_id"))
            ),
            "work_unit_fingerprint": (
                _text(action.get("work_unit_fingerprint"))
                or _text(controller_route.get("work_unit_fingerprint"))
                or _text(owner_route.get("work_unit_fingerprint"))
            ),
            "action_id": _text(action.get("action_id")),
        }
    return None


def _dispatch_migration_plan(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    route: Mapping[str, Any],
    archive_root: Path,
    blockers: list[dict[str, Any]],
) -> dict[str, Any]:
    dispatch_root = study_root / DISPATCH_ROOT_RELPATH
    allowed = set(_string_list(route.get("allowed_actions")))
    blocked = set(_string_list(route.get("blocked_actions")))
    dispatch_files: list[dict[str, Any]] = []
    retained_dispatch_files: list[dict[str, Any]] = []
    retained_tombstones: list[dict[str, Any]] = []
    immutable_directories: list[dict[str, Any]] = []
    retained_immutable_directories: list[dict[str, Any]] = []
    if not dispatch_root.is_dir():
        return {
            "dispatch_files": dispatch_files,
            "retained_dispatch_files": retained_dispatch_files,
            "retained_tombstones": retained_tombstones,
            "immutable_action_directories": immutable_directories,
            "retained_immutable_action_directories": retained_immutable_directories,
        }
    for path in sorted(dispatch_root.glob("*.json")):
        payload = _read_json_object(path)
        surface = _surface(payload)
        action_type = _text(_mapping(payload).get("action_type"))
        if surface == TOMBSTONE_SURFACE:
            retained_tombstones.append({"path": str(path), "reason": "already_tombstoned"})
            continue
        if action_type is None:
            blockers.append({"path": str(path), "reason": "dispatch_action_type_missing"})
            continue
        if action_type in allowed:
            retained_dispatch_files.append(
                {"path": str(path), "action_type": action_type, "reason": "current_allowed_action"}
            )
            continue
        reason = (
            "current_owner_route_blocked_action"
            if action_type in blocked
            else "current_owner_route_non_current_action"
        )
        dispatch_files.append(
            {
                "path": str(path),
                "relative_path": _workspace_relative(path, workspace_root=profile.workspace_root),
                "action_type": action_type,
                "surface": surface,
                "reason": reason,
                "archive_path": str(_archive_path(profile.workspace_root, archive_root, path)),
                "tombstone_path": str(path),
            }
        )
    immutable_root = dispatch_root / "immutable"
    if immutable_root.is_dir():
        for path in sorted(item for item in immutable_root.iterdir() if item.is_dir()):
            action_type = path.name
            if action_type in allowed:
                retained_immutable_directories.append(
                    {"path": str(path), "action_type": action_type, "reason": "current_allowed_action"}
                )
                continue
            reason = (
                "current_owner_route_blocked_action"
                if action_type in blocked
                else "current_owner_route_non_current_action"
            )
            immutable_directories.append(
                {
                    "path": str(path),
                    "relative_path": _workspace_relative(path, workspace_root=profile.workspace_root),
                    "action_type": action_type,
                    "reason": reason,
                    "file_count": _file_count(path),
                    "archive_path": str(_archive_path(profile.workspace_root, archive_root, path)),
                }
            )
    return {
        "dispatch_files": dispatch_files,
        "retained_dispatch_files": retained_dispatch_files,
        "retained_tombstones": retained_tombstones,
        "immutable_action_directories": immutable_directories,
        "retained_immutable_action_directories": retained_immutable_directories,
    }


def _manual_pause_migration_plan(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    quest_root: Path,
    route: Mapping[str, Any],
    archive_root: Path,
) -> dict[str, Any]:
    manual_pause_root = quest_root / MANUAL_PAUSE_RELPATH
    latest_path = manual_pause_root / "latest.json"
    latest = _read_json_object(latest_path)
    surface = _surface(latest)
    reason = _text(_mapping(_mapping(latest).get("manual_pause")).get("reason"))
    migration_required = surface == MANUAL_PAUSE_SURFACE and reason == LEGACY_PAUSE_REASON
    sibling_files: list[dict[str, Any]] = []
    if migration_required and manual_pause_root.is_dir():
        for path in sorted(manual_pause_root.glob("*.json")):
            if path == latest_path:
                continue
            payload = _read_json_object(path)
            if _surface(payload) != MANUAL_PAUSE_SURFACE:
                continue
            sibling_files.append(
                {
                    "path": str(path),
                    "relative_path": _workspace_relative(path, workspace_root=profile.workspace_root),
                    "archive_path": str(_archive_path(profile.workspace_root, archive_root, path)),
                }
            )
    runtime_state_path = quest_root / RUNTIME_STATE_RELPATH
    runtime_state = _read_json_object(runtime_state_path)
    runtime_state_migration = _runtime_state_pause_migration_plan(
        profile=profile,
        study_id=study_id,
        runtime_state_path=runtime_state_path,
        runtime_state=runtime_state,
        manual_pause=latest,
        route=route,
        archive_root=archive_root,
    )
    return {
        "path": str(latest_path),
        "exists": latest_path.is_file(),
        "surface": surface,
        "reason": reason,
        "migration_required": migration_required,
        "archive_path": str(_archive_path(profile.workspace_root, archive_root, latest_path)),
        "tombstone_path": str(latest_path),
        "sibling_receipts": sibling_files,
        "runtime_state_migration_required": runtime_state_migration["migration_required"],
        "runtime_state_migration": runtime_state_migration,
    }


def _runtime_state_pause_migration_plan(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    runtime_state_path: Path,
    runtime_state: Mapping[str, Any] | None,
    manual_pause: Mapping[str, Any] | None,
    route: Mapping[str, Any],
    archive_root: Path,
) -> dict[str, Any]:
    state = _mapping(runtime_state)
    last_manual_pause = _mapping(state.get("last_manual_pause"))
    state_reason = _text(state.get("pause_reason")) or _text(last_manual_pause.get("reason"))
    migration_required = state_reason == LEGACY_PAUSE_REASON and runtime_state_path.is_file()
    previous = _mapping(_mapping(manual_pause).get("previous_runtime_state"))
    restored_status = _text(previous.get("status")) or _status_for_route(route)
    restored_display_status = _text(previous.get("display_status")) or restored_status
    restored_continuation = _text(previous.get("continuation_reason")) or "blocked_turn_closeout_waiting_for_owner"
    return {
        "path": str(runtime_state_path),
        "exists": runtime_state_path.is_file(),
        "migration_required": migration_required,
        "reason": state_reason,
        "archive_path": str(_archive_path(profile.workspace_root, archive_root, runtime_state_path)),
        "restored_fields": {
            "status": restored_status,
            "display_status": restored_display_status,
            "continuation_reason": restored_continuation,
            "active_run_id": previous.get("active_run_id"),
            "worker_running": previous.get("worker_running", False),
        },
        "removed_fields": [
            key
            for key in (
                "pause_reason",
                "turn_reason",
                "last_manual_pause",
                "manual_hold",
                "human_takeover_contract",
                "continuation_updated_at",
            )
            if key in state
        ],
        "study_id": study_id,
    }


def _apply_study_migration(
    *,
    profile: WorkspaceProfile,
    study_plan: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    study_id = str(study_plan["study_id"])
    route = _mapping(study_plan.get("current_route"))
    dispatch_results = [
        _apply_dispatch_file_migration(
            profile=profile,
            item=_mapping(item),
            study_id=study_id,
            route=route,
            recorded_at=recorded_at,
        )
        for item in _list(study_plan.get("dispatch_files"))
    ]
    immutable_results = [
        _apply_immutable_directory_migration(item=_mapping(item))
        for item in _list(study_plan.get("immutable_action_directories"))
    ]
    manual_pause_result = _apply_manual_pause_migration(
        profile=profile,
        study_id=study_id,
        route=route,
        plan=_mapping(study_plan.get("manual_pause")),
        recorded_at=recorded_at,
    )
    result = {
        "study_id": study_id,
        "dispatch_file_tombstone_count": len(dispatch_results),
        "immutable_action_directory_migration_count": len(immutable_results),
        "manual_pause_tombstone_count": 1 if manual_pause_result.get("manual_pause_tombstoned") else 0,
        "runtime_state_pause_migration_count": 1 if manual_pause_result.get("runtime_state_migrated") else 0,
        "dispatch_files": dispatch_results,
        "immutable_action_directories": immutable_results,
        "manual_pause": manual_pause_result,
    }
    _write_study_receipt(profile=profile, study_plan=study_plan, applied=result, recorded_at=recorded_at)
    return result


def _apply_dispatch_file_migration(
    *,
    profile: WorkspaceProfile,
    item: Mapping[str, Any],
    study_id: str,
    route: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    path = Path(str(item["path"])).expanduser().resolve()
    archive_path = Path(str(item["archive_path"])).expanduser().resolve()
    original = _read_json_object(path)
    before_sha256 = _sha256_path(path)
    _archive_file(path=path, archive_path=archive_path)
    tombstone = _legacy_tombstone(
        study_id=study_id,
        original_path=path,
        archive_path=archive_path,
        reason=str(item["reason"]),
        original_surface=_surface(original),
        action_type=_text(item.get("action_type")),
        current_route=route,
        recorded_at=recorded_at,
    )
    _write_json(path, tombstone)
    return {
        **dict(item),
        "before_sha256": before_sha256,
        "tombstone_sha256": _sha256_path(path),
        "workspace_relative_tombstone_path": _workspace_relative(path, workspace_root=profile.workspace_root),
    }


def _apply_immutable_directory_migration(*, item: Mapping[str, Any]) -> dict[str, Any]:
    path = Path(str(item["path"])).expanduser().resolve()
    archive_path = Path(str(item["archive_path"])).expanduser().resolve()
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        raise FileExistsError(f"legacy control surface archive already exists: {archive_path}")
    shutil.move(str(path), str(archive_path))
    return {**dict(item), "moved": True}


def _apply_manual_pause_migration(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    route: Mapping[str, Any],
    plan: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "study_id": study_id,
        "manual_pause_tombstoned": False,
        "runtime_state_migrated": False,
        "sibling_receipt_migration_count": 0,
    }
    if plan.get("migration_required") is True:
        path = Path(str(plan["path"])).expanduser().resolve()
        archive_path = Path(str(plan["archive_path"])).expanduser().resolve()
        original = _read_json_object(path)
        _archive_file(path=path, archive_path=archive_path)
        tombstone = _legacy_tombstone(
            study_id=study_id,
            original_path=path,
            archive_path=archive_path,
            reason="legacy_manual_pause_replaced_by_current_opl_owner_route",
            original_surface=_surface(original),
            action_type=None,
            current_route=route,
            recorded_at=recorded_at,
        )
        _write_json(path, tombstone)
        result["manual_pause_tombstoned"] = True
        result["manual_pause"] = {
            "path": str(path),
            "archive_path": str(archive_path),
            "tombstone_sha256": _sha256_path(path),
        }
        sibling_results = []
        for sibling in _list(plan.get("sibling_receipts")):
            sibling_path = Path(str(_mapping(sibling)["path"])).expanduser().resolve()
            sibling_archive = Path(str(_mapping(sibling)["archive_path"])).expanduser().resolve()
            _archive_file(path=sibling_path, archive_path=sibling_archive)
            sibling_path.unlink()
            sibling_results.append({**_mapping(sibling), "moved": True})
        result["sibling_receipt_migration_count"] = len(sibling_results)
        result["sibling_receipts"] = sibling_results
    runtime_state_plan = _mapping(plan.get("runtime_state_migration"))
    if runtime_state_plan.get("migration_required") is True:
        runtime_state_result = _apply_runtime_state_pause_migration(plan=runtime_state_plan)
        result["runtime_state_migrated"] = True
        result["runtime_state"] = runtime_state_result
    return result


def _apply_runtime_state_pause_migration(*, plan: Mapping[str, Any]) -> dict[str, Any]:
    path = Path(str(plan["path"])).expanduser().resolve()
    archive_path = Path(str(plan["archive_path"])).expanduser().resolve()
    original = _read_json_object(path)
    if original is None:
        raise FileNotFoundError(f"runtime state missing for legacy pause migration: {path}")
    before_sha256 = _sha256_path(path)
    _archive_file(path=path, archive_path=archive_path)
    updated = dict(original)
    for key in _list(plan.get("removed_fields")):
        if isinstance(key, str):
            updated.pop(key, None)
    for key, value in _mapping(plan.get("restored_fields")).items():
        updated[key] = value
    _write_json(path, updated)
    return {
        "path": str(path),
        "archive_path": str(archive_path),
        "before_sha256": before_sha256,
        "after_sha256": _sha256_path(path),
        "restored_fields": dict(_mapping(plan.get("restored_fields"))),
        "removed_fields": list(_list(plan.get("removed_fields"))),
    }


def _write_workspace_receipt(
    *,
    profile: WorkspaceProfile,
    report: Mapping[str, Any],
    recorded_at: str,
) -> None:
    root = profile.workspace_root / MIGRATION_ROOT_RELPATH
    history_root = profile.workspace_root / HISTORY_ROOT_RELPATH
    latest_path = root / "latest.json"
    history_path = history_root / f"{_history_stamp(recorded_at)}.json"
    payload = {
        **dict(report),
        "status": "applied",
        "latest_path": str(latest_path),
        "history_path": str(history_path),
    }
    history_root.mkdir(parents=True, exist_ok=True)
    _write_json(history_path, payload)
    _write_json(latest_path, payload)


def _write_study_receipt(
    *,
    profile: WorkspaceProfile,
    study_plan: Mapping[str, Any],
    applied: Mapping[str, Any],
    recorded_at: str,
) -> None:
    study_root = Path(str(study_plan["study_root"])).expanduser().resolve()
    root = study_root / STUDY_MIGRATION_ROOT_RELPATH
    history_root = root / "history"
    latest_path = root / "latest.json"
    history_path = history_root / f"{_history_stamp(recorded_at)}.json"
    payload = {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "status": "applied",
        "recorded_at": recorded_at,
        "workspace_root": str(profile.workspace_root),
        "study_id": str(study_plan["study_id"]),
        "study_root": str(study_root),
        "quest_root": str(study_plan["quest_root"]),
        "current_route": dict(_mapping(study_plan.get("current_route"))),
        "authority_boundary": _authority_boundary(apply=True),
        "applied": dict(applied),
        "latest_path": str(latest_path),
        "history_path": str(history_path),
    }
    history_root.mkdir(parents=True, exist_ok=True)
    _write_json(history_path, payload)
    _write_json(latest_path, payload)


def _legacy_tombstone(
    *,
    study_id: str,
    original_path: Path,
    archive_path: Path,
    reason: str,
    original_surface: str | None,
    action_type: str | None,
    current_route: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface_kind": TOMBSTONE_SURFACE,
        "status": "migrated_to_provenance",
        "recorded_at": recorded_at,
        "study_id": study_id,
        "reason": reason,
        "original_surface": original_surface,
        "action_type": action_type,
        "original_path": str(original_path),
        "archive_path": str(archive_path),
        "current_route": dict(current_route),
        "authority_boundary": {
            "active_control_authority": False,
            "domain_truth_authority": False,
            "publication_quality_authority": False,
            "paper_content_authority": False,
            "runtime_queue_authority": False,
            "provenance_only": True,
        },
    }


def _archive_file(*, path: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        raise FileExistsError(f"legacy control surface archive already exists: {archive_path}")
    shutil.copy2(path, archive_path)


def _archive_path(workspace_root: Path, archive_root: Path, path: Path) -> Path:
    relative = Path(_workspace_relative(path, workspace_root=workspace_root))
    return archive_root / relative


def _workspace_relative(path: Path, *, workspace_root: Path) -> str:
    resolved = Path(path).expanduser().resolve()
    try:
        return resolved.relative_to(workspace_root.expanduser().resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _authority_boundary(*, apply: bool) -> dict[str, Any]:
    return {
        "publication_eval_written": False,
        "controller_decisions_written": False,
        "paper_content_mutation": False,
        "current_package_mutation": False,
        "quality_verdict_written": False,
        "runtime_queue_mutation": False,
        "legacy_reader_compatibility_added": False,
        "active_legacy_control_material_migrated": bool(apply),
        "runtime_state_pause_metadata_migrated": bool(apply),
    }


def _study_next_actions(*, migration_count: int, blockers: list[dict[str, Any]]) -> list[str]:
    if blockers:
        return ["resolve_current_control_state_before_legacy_control_surface_migration"]
    if migration_count:
        return ["apply_legacy_control_surface_clean_migration"]
    return []


def _workspace_next_actions(studies: list[Mapping[str, Any]]) -> list[str]:
    actions: list[str] = []
    for study in studies:
        for action in _list(study.get("next_required_actions")):
            if isinstance(action, str) and action not in actions:
                actions.append(action)
    return actions


def _status_for_route(route: Mapping[str, Any]) -> str:
    action_type = _text(route.get("action_type"))
    if action_type:
        return "waiting_for_user"
    return "active"


def _empty_route(study_id: str) -> dict[str, Any]:
    return {
        "study_id": study_id,
        "action_type": None,
        "allowed_actions": [],
        "blocked_actions": [],
        "next_owner": None,
        "current_owner": None,
        "owner_reason": None,
        "work_unit_id": None,
        "work_unit_fingerprint": None,
        "action_id": None,
    }


def _surface(payload: Mapping[str, Any] | None) -> str | None:
    data = _mapping(payload)
    return _text(data.get("surface_kind")) or _text(data.get("surface"))


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _read_yaml_object(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_path(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _file_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _history_stamp(recorded_at: str) -> str:
    return recorded_at.replace("+00:00", "Z").replace("+0000", "Z").replace("-", "").replace(":", "").replace(".", "")


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _string_list(value: object) -> list[str]:
    return [text for item in _list(value) if (text := _text(item)) is not None]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["run_legacy_control_surface_clean_migration"]
