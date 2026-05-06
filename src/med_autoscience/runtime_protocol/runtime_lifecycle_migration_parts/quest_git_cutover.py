from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
from typing import Any


QUEST_GIT_CUTOVER_MODES = ("dry_run", "apply")
QUEST_GIT_CUTOVER_ELIGIBLE_STATUSES = frozenset(
    {"paused", "parked", "stopped", "completed", "failed", "cancelled", "canceled"}
)
QUEST_GIT_CUTOVER_BLOCKED_STATUSES = frozenset(
    {"active", "running", "live", "waiting_for_user", "created", "idle"}
)


def cutover_quest_git_active_paths(
    *,
    workspace_root: Path,
    inventory_builder: Callable[[Path], Mapping[str, Any]],
    schema_version: int,
    mode: str = "dry_run",
    migration_run_id: str | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    normalized_mode = _require_choice("mode", mode, QUEST_GIT_CUTOVER_MODES)
    started_at = _utc_now()
    run_id = migration_run_id or f"quest-git-cutover-{_artifact_slug(started_at)}"
    run_root = (
        Path(output_root).expanduser().resolve()
        if output_root is not None
        else resolved_workspace_root / "artifacts" / "runtime" / "lifecycle_migration" / run_id
    )
    archive_root = run_root / "quest_git_archives"
    inventory = inventory_builder(resolved_workspace_root)
    items = [
        _quest_git_cutover_item(
            workspace_root=resolved_workspace_root,
            item=item,
            mode=normalized_mode,
            archive_root=archive_root,
            schema_version=schema_version,
        )
        for item in inventory["items"]
    ]

    summary = {
        "item_count": len(items),
        "eligible_count": sum(1 for item in items if item["gate"]["eligible"]),
        "planned_count": sum(1 for item in items if item["status"] == "planned"),
        "applied_count": sum(1 for item in items if item["status"] == "retired"),
        "skipped_count": sum(1 for item in items if item["status"] == "skipped"),
        "active_git_count_before": inventory["summary"]["active_git_count"],
        "active_git_count_after": sum(1 for item in items if item["quest_git_present_in_active_path_after"]),
    }
    payload = {
        "surface_kind": "quest_git_active_path_cutover",
        "schema_version": schema_version,
        "migration_run_id": run_id,
        "workspace_root": str(resolved_workspace_root),
        "mode": normalized_mode,
        "started_at": started_at,
        "finished_at": _utc_now(),
        "archive_root": str(archive_root),
        "items": items,
        "summary": summary,
        "status": "verified" if summary["active_git_count_after"] == 0 else "pending",
        "next_required_action": (
            "Build runtime lifecycle ledger with quest_git_cutover_status=verified."
            if summary["active_git_count_after"] == 0
            else "Resolve skipped active/unknown quest Git paths under controller/operator authorization."
        ),
    }
    if normalized_mode == "apply":
        _write_quest_git_cutover_record(run_root=run_root, payload=payload, schema_version=schema_version)
    return payload


def read_latest_quest_git_cutover_record(*, ledger_root: Path) -> dict[str, Any]:
    latest_path = ledger_root / "quest_git_active_path_cutover.latest.json"
    latest = _read_json_mapping(latest_path)
    record_path_text = str(latest.get("record_path") or "").strip()
    if not record_path_text:
        return {}
    record_path = Path(record_path_text).expanduser()
    if not record_path.is_absolute():
        record_path = ledger_root / record_path
    return _read_json_mapping(record_path)


def quest_git_cutover_status_from_record(record: Mapping[str, Any]) -> dict[str, Any]:
    status = str(record.get("status") or "").strip()
    return {
        "status": status or "pending",
        "verified": status == "verified",
        "migration_run_id": record.get("migration_run_id"),
        "record_surface_kind": record.get("surface_kind"),
        "summary": dict(_mapping(record.get("summary"))),
    }


def merge_quest_git_cutover_record_items(
    *,
    inventory_items: list[Mapping[str, Any]],
    cutover_record: Mapping[str, Any],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in inventory_items:
        normalized = _quest_git_inventory_item(item)
        key = str(normalized.get("active_path") or "")
        if key:
            merged[key] = normalized
    record_items = cutover_record.get("items")
    if not isinstance(record_items, list):
        return list(merged.values())
    for item in record_items:
        if not isinstance(item, Mapping):
            continue
        normalized = _quest_git_inventory_item(item)
        key = str(normalized.get("active_path") or "")
        if not key:
            continue
        current = merged.get(key)
        if current and current.get("quest_git_present_in_active_path"):
            current.update(
                {
                    "archive_ref": current.get("archive_ref") or normalized.get("archive_ref"),
                    "restore_proof_path": current.get("restore_proof_path") or normalized.get("restore_proof_path"),
                    "projection_equivalence": current.get("projection_equivalence")
                    or normalized.get("projection_equivalence"),
                }
            )
            continue
        merged[key] = normalized
    return sorted(merged.values(), key=lambda item: str(item.get("active_path") or ""))


def _quest_git_cutover_item(
    *,
    workspace_root: Path,
    item: Mapping[str, Any],
    mode: str,
    archive_root: Path,
    schema_version: int,
) -> dict[str, Any]:
    normalized = _quest_git_inventory_item(item)
    active_path = Path(str(normalized.get("active_path") or "")).expanduser().resolve()
    git_path = Path(str(normalized.get("git_path") or "")).expanduser().resolve()
    gate = _quest_git_cutover_gate(workspace_root=workspace_root, active_path=active_path)
    result = {
        **normalized,
        "gate": gate,
        "quest_git_present_in_active_path_before": git_path.exists(),
        "quest_git_present_in_active_path_after": git_path.exists(),
        "archive_manifest_path": None,
        "archive_ref": normalized.get("archive_ref"),
        "restore_proof_path": normalized.get("restore_proof_path"),
    }
    if not git_path.exists():
        result.update(
            {
                "status": "retired",
                "action": "none",
                "quest_git_active_path_retired": True,
                "quest_git_present_in_active_path": False,
                "quest_git_present_in_active_path_after": False,
            }
        )
        return result
    if not gate["eligible"]:
        result.update(
            {
                "status": "skipped",
                "action": "audit_only",
                "skipped_reason": gate["reason"],
            }
        )
        return result

    safe_quest_id = _safe_artifact_name(str(normalized.get("quest_id") or active_path.name))
    manifest_path = archive_root / f"{safe_quest_id}.quest_git_archive.json"
    archive_path = archive_root / f"{safe_quest_id}.git.tar.gz"
    if mode == "dry_run":
        result.update(
            {
                "status": "planned",
                "action": "archive_then_remove_active_git",
                "archive_ref": str(archive_path),
                "archive_manifest_path": str(manifest_path),
                "restore_proof_path": str(manifest_path),
            }
        )
        return result

    manifest = _archive_and_remove_quest_git(
        workspace_root=workspace_root,
        active_path=active_path,
        git_path=git_path,
        archive_path=archive_path,
        manifest_path=manifest_path,
        inventory_item=normalized,
        gate=gate,
        schema_version=schema_version,
    )
    result.update(
        {
            "status": "retired",
            "action": "archived_and_removed_active_git",
            "quest_git_present_in_active_path": False,
            "quest_git_active_path_retired": True,
            "quest_git_present_in_active_path_after": git_path.exists(),
            "archive_ref": manifest["archive_path"],
            "archive_manifest_path": str(manifest_path),
            "restore_proof_path": str(manifest_path),
            "projection_equivalence": manifest["restore_proof"]["status"],
            "skipped_reason": None,
        }
    )
    return result


def _quest_git_inventory_item(item: Mapping[str, Any]) -> dict[str, Any]:
    quest_id = _text(item.get("quest_id"))
    active_path = _quest_git_active_path_text(item)
    git_path = _quest_git_path_text(item, active_path=active_path)
    git_present = _quest_git_present(item, git_path=git_path)
    active_path_retired = _quest_git_active_path_retired(item, git_present=git_present)
    status = _quest_git_status(item, git_present=git_present, active_path_retired=active_path_retired)
    skipped_reason = _quest_git_skipped_reason(item, status=status, git_present=git_present)
    return {
        "source": item.get("source"),
        "quest_id": quest_id or (Path(active_path).name if active_path else None),
        "study_id": item.get("study_id"),
        "active_path": active_path or None,
        "git_path": git_path or None,
        "quest_git_present_in_active_path": git_present,
        "quest_git_active_path_retired": bool(active_path_retired),
        "archive_ref": item.get("archive_ref"),
        "restore_proof_path": item.get("restore_proof_path"),
        "projection_equivalence": item.get("projection_equivalence"),
        "status": status,
        "action": item.get("action") or ("audit_only" if status == "pending" else "none"),
        "skipped_reason": skipped_reason,
    }


def _quest_git_active_path_text(item: Mapping[str, Any]) -> str:
    return str(item.get("active_path") or item.get("quest_root") or "").strip()


def _quest_git_path_text(item: Mapping[str, Any], *, active_path: str) -> str:
    return str(item.get("git_path") or (f"{active_path}/.git" if active_path else "")).strip()


def _quest_git_present(item: Mapping[str, Any], *, git_path: str) -> bool:
    if "quest_git_present_in_active_path" in item:
        return bool(item.get("quest_git_present_in_active_path"))
    return bool(git_path and Path(git_path).expanduser().exists())


def _quest_git_active_path_retired(item: Mapping[str, Any], *, git_present: bool) -> bool:
    value = item.get("quest_git_active_path_retired")
    return not git_present if value is None else bool(value)


def _quest_git_status(
    item: Mapping[str, Any],
    *,
    git_present: bool,
    active_path_retired: bool,
) -> str:
    status = str(item.get("status") or "").strip()
    return status or ("pending" if git_present or not active_path_retired else "retired")


def _quest_git_skipped_reason(item: Mapping[str, Any], *, status: str, git_present: bool) -> Any:
    reason = item.get("skipped_reason")
    if reason or status != "pending":
        return reason
    return "active_quest_git_present" if git_present else "active_path_retirement_unverified"


def _quest_git_cutover_gate(*, workspace_root: Path, active_path: Path) -> dict[str, Any]:
    if not _is_relative_to(active_path, workspace_root):
        return {"eligible": False, "reason": "active_path_outside_workspace"}
    runtime_state_path = active_path / ".ds" / "runtime_state.json"
    if not runtime_state_path.exists():
        return {
            "eligible": False,
            "reason": "runtime_state_missing",
            "runtime_state_path": str(runtime_state_path),
        }
    runtime_state = _read_json_mapping(runtime_state_path)
    status = str(runtime_state.get("status") or "").strip().lower()
    active_run_id = str(runtime_state.get("active_run_id") or "").strip()
    worker_running = bool(runtime_state.get("worker_running"))
    if active_run_id:
        reason = "active_run_id_present"
    elif worker_running:
        reason = "worker_running"
    elif status in QUEST_GIT_CUTOVER_BLOCKED_STATUSES:
        reason = "live_or_active_quest"
    elif status not in QUEST_GIT_CUTOVER_ELIGIBLE_STATUSES:
        reason = "runtime_state_not_cutover_eligible"
    else:
        reason = "controller_operator_safe_state"
    return {
        "eligible": reason == "controller_operator_safe_state",
        "reason": reason,
        "runtime_state_path": str(runtime_state_path),
        "runtime_status": status or None,
        "active_run_id": active_run_id or None,
        "worker_running": worker_running,
    }


def _archive_and_remove_quest_git(
    *,
    workspace_root: Path,
    active_path: Path,
    git_path: Path,
    archive_path: Path,
    manifest_path: Path,
    inventory_item: Mapping[str, Any],
    gate: Mapping[str, Any],
    schema_version: int,
) -> dict[str, Any]:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    source_file_count = _count_files(git_path)
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(git_path, arcname=".git")
    archive_sha256 = _file_sha256(archive_path)
    with tarfile.open(archive_path, "r:gz") as tar:
        member_names = tar.getnames()
    if not member_names:
        raise RuntimeError(f"quest Git archive is empty: {archive_path}")
    if git_path.is_dir():
        shutil.rmtree(git_path)
    else:
        git_path.unlink()
    manifest = {
        "surface_kind": "quest_git_active_path_archive_manifest",
        "schema_version": schema_version,
        "created_at": _utc_now(),
        "workspace_root": str(workspace_root),
        "quest_id": inventory_item.get("quest_id"),
        "study_id": inventory_item.get("study_id"),
        "active_path": str(active_path),
        "git_path": str(git_path),
        "archive_path": str(archive_path),
        "archive_sha256": archive_sha256,
        "source_file_count": source_file_count,
        "archive_member_count": len(member_names),
        "gate": dict(gate),
        "restore_command": f"tar -xzf {archive_path} -C {active_path}",
        "restore_proof": {
            "status": "verified",
            "archive_sha256": archive_sha256,
            "archive_member_count": len(member_names),
            "active_git_removed": not git_path.exists(),
        },
    }
    _write_json(manifest_path, manifest)
    return manifest


def _write_quest_git_cutover_record(
    *,
    run_root: Path,
    payload: Mapping[str, Any],
    schema_version: int,
) -> None:
    _write_json(run_root / "quest_git_active_path_cutover.json", payload)
    latest_path = run_root.parent / "quest_git_active_path_cutover.latest.json"
    _write_json(
        latest_path,
        {
            "surface_kind": "quest_git_active_path_cutover_latest",
            "schema_version": schema_version,
            "migration_run_id": payload["migration_run_id"],
            "workspace_root": payload["workspace_root"],
            "status": payload["status"],
            "record_path": str(run_root / "quest_git_active_path_cutover.json"),
            "finished_at": payload["finished_at"],
        },
    )


def _read_json_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _count_files(path: Path) -> int:
    if path.is_file() or path.is_symlink():
        return 1
    return sum(1 for candidate in path.rglob("*") if candidate.is_file() or candidate.is_symlink())


def _safe_artifact_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value).strip("._") or "quest"


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _require_choice(name: str, value: str, choices: tuple[str, ...]) -> str:
    normalized = str(value or "").strip()
    if normalized not in choices:
        raise ValueError(f"{name} must be one of {choices}: {value!r}")
    return normalized


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _artifact_slug(value: str) -> str:
    return value.replace(":", "").replace("-", "").replace("+0000", "Z").replace("+00:00", "Z")


__all__ = [
    "cutover_quest_git_active_paths",
    "merge_quest_git_cutover_record_items",
    "quest_git_cutover_status_from_record",
    "read_latest_quest_git_cutover_record",
]
