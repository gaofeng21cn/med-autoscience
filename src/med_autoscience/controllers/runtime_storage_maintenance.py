from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Mapping

from med_autoscience.controllers import study_runtime_resolution
from med_autoscience.controllers.artifact_lifecycle_inventory import build_study_artifact_lifecycle_registry
from med_autoscience.controllers.runtime_storage_maintenance_parts import git_garbage
from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction import (
    compact_cold_runtime_buckets,
    restore_proof_compaction_blockers,
    restore_proof_compaction_candidate,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.dataset_retention import (
    audit_dataset_retention as _dataset_retention_audit,
    dataset_release_blockers as _dataset_release_blockers,
    dataset_release_decision as _dataset_release_decision,
    release_checksum as _release_checksum,
    release_rehydrate_verification as _release_rehydrate_verification,
    release_restore_handle as _release_restore_handle,
    superseded_release_index as _superseded_release_index,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import runtime_lifecycle_store
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol.study_runtime import resolve_study_runtime_paths


SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
_LIVE_RUNTIME_STATUSES = frozenset({"running", "active"})
_TERMINAL_RUNTIME_STATUSES = frozenset({"completed", "failed", "stopped", "terminated"})
_PRIMARY_BUCKETS = ("bash_exec", "codex_homes", "runs", "codex_history", "worktrees")
_DELETE_SAFE_DIR_NAMES = {
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "cache",
    "tmp",
}
_DELETE_SAFE_FILE_SUFFIXES = (".tmp", ".pyc", ".pyo")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _artifact_slug(recorded_at: str) -> str:
    normalized = recorded_at.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized).astimezone(UTC).strftime(_TIMESTAMP_FORMAT)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _report_root(study_root: Path) -> Path:
    return study_root / "artifacts" / "runtime" / "runtime_storage_maintenance"


def _latest_report_path(study_root: Path) -> Path:
    return _report_root(study_root) / "latest.json"


def _timestamped_report_path(study_root: Path, recorded_at: str) -> Path:
    return _report_root(study_root) / f"{_artifact_slug(recorded_at)}.json"


def _read_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = study_runtime_resolution._load_yaml_dict(path)
    return payload if isinstance(payload, dict) else {}


def _resolve_quest_id(*, study_id: str, study_root: Path, study_payload: Mapping[str, Any]) -> str:
    runtime_binding = _read_yaml_dict(study_root / "runtime_binding.yaml")
    binding_quest_id = str(runtime_binding.get("quest_id") or "").strip()
    if binding_quest_id:
        return binding_quest_id
    execution = study_payload.get("execution")
    if isinstance(execution, Mapping):
        execution_quest_id = str(execution.get("quest_id") or "").strip()
        if execution_quest_id:
            return execution_quest_id
    return study_id


def _directory_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for current_root, _, filenames in os.walk(path):
        current_path = Path(current_root)
        for filename in filenames:
            candidate = current_path / filename
            try:
                total += candidate.stat().st_size
            except OSError:
                continue
    return total


def _size_summary(quest_root: Path) -> dict[str, Any]:
    ds_root = quest_root / ".ds"
    buckets: dict[str, Any] = {}
    for bucket_name in _PRIMARY_BUCKETS:
        bucket_path = ds_root / bucket_name
        buckets[bucket_name] = {
            "path": str(bucket_path),
            "bytes": _directory_size_bytes(bucket_path),
        }
    return {
        "root": str(ds_root),
        "total_bytes": _directory_size_bytes(ds_root),
        "buckets": buckets,
    }


def _study_artifact_size_summary(study_root: Path) -> dict[str, Any]:
    buckets: dict[str, Any] = {}
    for name in ("artifacts", "manuscript", "paper"):
        path = study_root / name
        buckets[name] = {
            "path": str(path),
            "bytes": _directory_size_bytes(path),
        }
    return {
        "root": str(study_root),
        "total_bytes": sum(int(item["bytes"]) for item in buckets.values()),
        "buckets": buckets,
        "candidate_action": "keep-online",
        "risk": "high_traceability_surface",
        "estimated_release_bytes": 0,
    }


def _quest_runtime_snapshot(quest_root: Path) -> dict[str, Any]:
    runtime_state: dict[str, Any] = {}
    runtime_state_error: str | None = None
    try:
        runtime_state = quest_state.load_runtime_state(quest_root)
    except (OSError, json.JSONDecodeError) as exc:
        runtime_state_error = f"{type(exc).__name__}: {exc}"
    return {
        "quest_exists": (quest_root / "quest.yaml").exists(),
        "status": str(runtime_state.get("status") or "").strip().lower() or None,
        "active_run_id": str(runtime_state.get("active_run_id") or "").strip() or None,
        "runtime_state_error": runtime_state_error,
    }


def _selected_study_roots(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    all_studies: bool,
) -> list[Path]:
    if study_id:
        return [profile.studies_root / study_id]
    if not all_studies:
        return []
    if not profile.studies_root.exists():
        return []
    return sorted(
        path
        for path in profile.studies_root.iterdir()
        if path.is_dir() and ((path / "study.yaml").exists() or (path / "runtime_binding.yaml").exists())
    )


def _runtime_candidate(
    *,
    quest_root: Path,
    snapshot: Mapping[str, Any],
    size_summary: Mapping[str, Any],
) -> dict[str, Any]:
    status = str(snapshot.get("status") or "").strip().lower()
    active_run_id = snapshot.get("active_run_id")
    if not bool(snapshot.get("quest_exists")):
        return _runtime_candidate_payload(
            quest_root=quest_root,
            size_summary=size_summary,
            risk="missing_truth_surface",
            candidate_action="blocked-missing-quest",
            estimated_release_bytes=0,
            blockers=["missing_quest_root"],
        )
    if snapshot.get("runtime_state_error"):
        return _runtime_candidate_payload(
            quest_root=quest_root,
            size_summary=size_summary,
            risk="runtime_state_unreadable",
            candidate_action="audit-only",
            estimated_release_bytes=0,
            blockers=["runtime_state_unreadable"],
        )
    if status in _LIVE_RUNTIME_STATUSES and active_run_id is not None:
        return _runtime_candidate_payload(
            quest_root=quest_root,
            size_summary=size_summary,
            risk="live_runtime",
            candidate_action="audit-only",
            estimated_release_bytes=0,
            blockers=["live_runtime_active"],
        )
    if status in _TERMINAL_RUNTIME_STATUSES or not active_run_id:
        candidate = _runtime_candidate_payload(
            quest_root=quest_root,
            size_summary=size_summary,
            risk="process_state_only",
            candidate_action="compress-online",
            estimated_release_bytes=_primary_runtime_bucket_bytes(size_summary),
            blockers=[],
        )
        candidate["secondary_actions"] = ["dedupe-online", "archive-expanded-worktree-runtime"]
        return candidate
    return _runtime_candidate_payload(
        quest_root=quest_root,
        size_summary=size_summary,
        risk="unknown_runtime_state",
        candidate_action="audit-only",
        estimated_release_bytes=0,
        blockers=["unknown_runtime_state"],
    )


def _runtime_candidate_payload(
    *,
    quest_root: Path,
    size_summary: Mapping[str, Any],
    risk: str,
    candidate_action: str,
    estimated_release_bytes: int,
    blockers: list[str],
) -> dict[str, Any]:
    return {
        "category": "runtime",
        "path": str(quest_root),
        "bytes": int(size_summary.get("total_bytes") or 0),
        "risk": risk,
        "candidate_action": candidate_action,
        "estimated_release_bytes": estimated_release_bytes,
        "blockers": blockers,
    }


def _primary_runtime_bucket_bytes(size_summary: Mapping[str, Any]) -> int:
    return sum(
        int(bucket.get("bytes") or 0)
        for name, bucket in dict(size_summary.get("buckets") or {}).items()
        if name in _PRIMARY_BUCKETS
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _backend_script_path(profile: WorkspaceProfile) -> Path | None:
    repo_root = profile.med_deepscientist_repo_root
    if repo_root is None:
        return None
    resolved_repo_root = Path(repo_root).expanduser().resolve()
    script_path = resolved_repo_root / "scripts" / "maintain_quest_runtime_storage.py"
    return script_path if script_path.is_file() else None


def _pythonpath_env(repo_root: Path) -> str:
    src_root = str((repo_root / "src").resolve())
    existing = str(os.environ.get("PYTHONPATH") or "").strip()
    if not existing:
        return src_root
    return os.pathsep.join([src_root, existing])


def _build_command(
    *,
    script_path: Path,
    quest_root: Path,
    include_worktrees: bool,
    older_than_seconds: int,
    jsonl_max_mb: int,
    text_max_mb: int,
    event_segment_max_mb: int,
    slim_jsonl_threshold_mb: int | None,
    dedupe_worktree_min_mb: int | None,
    head_lines: int,
    tail_lines: int,
) -> list[str]:
    command = [
        sys.executable,
        str(script_path),
        str(quest_root),
        "--older-than-hours",
        str(max(1, older_than_seconds // 3600)),
        "--jsonl-max-mb",
        str(max(1, jsonl_max_mb)),
        "--text-max-mb",
        str(max(1, text_max_mb)),
        "--event-segment-max-mb",
        str(max(1, event_segment_max_mb)),
        "--head-lines",
        str(max(1, head_lines)),
        "--tail-lines",
        str(max(1, tail_lines)),
    ]
    if not include_worktrees:
        command.append("--no-worktrees")
    if slim_jsonl_threshold_mb is None:
        command.append("--no-slim-oversized-jsonl")
    else:
        command.extend(["--slim-jsonl-threshold-mb", str(max(1, slim_jsonl_threshold_mb))])
    if dedupe_worktree_min_mb is None:
        command.append("--no-dedupe-worktrees")
    else:
        command.extend(["--dedupe-worktree-min-mb", str(max(1, dedupe_worktree_min_mb))])
    return command


def _git_storage_audit(
    workspace_root: Path,
    *,
    older_than_seconds: int = git_garbage.GIT_TEMP_GARBAGE_MIN_AGE_SECONDS,
    apply: bool = False,
    reinitialize_empty_workspace_git: bool = False,
) -> dict[str, Any]:
    return git_garbage.audit_git_storage(
        workspace_root,
        older_than_seconds=older_than_seconds,
        apply=apply,
        reinitialize_empty_workspace_git=reinitialize_empty_workspace_git,
    )


def _delete_safe_candidates(
    workspace_root: Path,
    *,
    apply: bool = False,
    scan_roots: list[Path] | None = None,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    if not workspace_root.exists():
        return {
            "category": "cache",
            "workspace_root": str(workspace_root),
            "candidate_action": "delete-safe",
            "bytes": 0,
            "estimated_release_bytes": 0,
            "actual_release_bytes": 0,
            "candidates": [],
            "apply_result": _empty_cache_apply_result("workspace_missing") if apply else None,
            "deleted_count": 0,
            "deleted_bytes": 0,
            "skipped": [],
            "errors": [],
        }
    roots_to_scan = _cache_scan_roots(workspace_root=workspace_root, scan_roots=scan_roots)
    for root in roots_to_scan:
        if not root.exists():
            continue
        for current_root, dirnames, filenames in os.walk(root):
            current = Path(current_root)
            dirnames[:] = [name for name in dirnames if name not in {".git", "storage_audit"}]
            for dirname in list(dirnames):
                if dirname not in _DELETE_SAFE_DIR_NAMES:
                    continue
                candidate = current / dirname
                candidate_bytes = _directory_size_bytes(candidate)
                candidates.append(
                    {
                        "path": str(candidate),
                        "bytes": candidate_bytes,
                        "candidate_action": "delete-safe",
                        "risk": "rebuildable_process_cache",
                    }
                )
                dirnames.remove(dirname)
            for filename in filenames:
                if filename == ".DS_Store" or filename.endswith(_DELETE_SAFE_FILE_SUFFIXES):
                    candidate = current / filename
                    candidates.append(
                        {
                            "path": str(candidate),
                            "bytes": _directory_size_bytes(candidate),
                            "candidate_action": "delete-safe",
                            "risk": "rebuildable_process_cache",
                        }
                    )
    total_bytes = sum(int(item["bytes"]) for item in candidates)
    apply_result = _apply_delete_safe_candidates(workspace_root=workspace_root, candidates=candidates) if apply else None
    deleted_bytes = int((apply_result or {}).get("deleted_bytes") or 0)
    deleted_count = int((apply_result or {}).get("deleted_count") or 0)
    skipped = list((apply_result or {}).get("skipped") or [])
    errors = list((apply_result or {}).get("errors") or [])
    return {
        "category": "cache",
        "workspace_root": str(workspace_root),
        "candidate_action": "delete-safe",
        "bytes": total_bytes,
        "estimated_release_bytes": total_bytes,
        "actual_release_bytes": deleted_bytes,
        "candidates": candidates,
        "apply_result": apply_result,
        "deleted_count": deleted_count,
        "deleted_bytes": deleted_bytes,
        "skipped": skipped,
        "errors": errors,
    }


def _cache_scan_roots(*, workspace_root: Path, scan_roots: list[Path] | None) -> list[Path]:
    if scan_roots is None:
        return [workspace_root]
    resolved_roots: list[Path] = []
    seen: set[Path] = set()
    for root in scan_roots:
        resolved_root = root.expanduser().resolve()
        if not _path_is_inside_workspace(resolved_root, workspace_root):
            continue
        if resolved_root in seen:
            continue
        seen.add(resolved_root)
        resolved_roots.append(resolved_root)
    return resolved_roots


def _empty_cache_apply_result(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "deleted_count": 0,
        "deleted_bytes": 0,
        "deleted_paths": [],
        "skipped": [],
        "errors": [],
    }


def _apply_delete_safe_candidates(
    *,
    workspace_root: Path,
    candidates: list[Mapping[str, Any]],
) -> dict[str, Any]:
    if not candidates:
        return _empty_cache_apply_result("nothing_to_delete")
    deleted_paths: list[str] = []
    skipped: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    deleted_bytes = 0
    for item in candidates:
        candidate = Path(str(item.get("path") or ""))
        if not _path_is_inside_workspace(candidate, workspace_root):
            errors.append({"path": str(candidate), "error": "outside_workspace"})
            continue
        if not candidate.exists() and not candidate.is_symlink():
            skipped.append({"path": str(candidate), "reason": "missing"})
            continue
        item_bytes = int(item.get("bytes") or _directory_size_bytes(candidate))
        try:
            if candidate.is_symlink() or candidate.is_file():
                candidate.unlink()
            elif candidate.is_dir():
                shutil.rmtree(candidate)
            else:
                skipped.append({"path": str(candidate), "reason": "unsupported_file_type"})
                continue
        except OSError as exc:
            errors.append({"path": str(candidate), "error": str(exc)})
            continue
        deleted_paths.append(str(candidate))
        deleted_bytes += item_bytes
    if errors and deleted_paths:
        status = "partially_deleted"
    elif errors:
        status = "delete_failed"
    elif skipped and deleted_paths:
        status = "partially_deleted"
    elif deleted_paths:
        status = "deleted"
    elif skipped:
        status = "nothing_deleted"
    else:
        status = "nothing_to_delete"
    return {
        "status": status,
        "deleted_count": len(deleted_paths),
        "deleted_bytes": deleted_bytes,
        "deleted_paths": deleted_paths,
        "skipped": skipped,
        "errors": errors,
    }


def _path_is_inside_workspace(path: Path, workspace_root: Path) -> bool:
    try:
        path.absolute().relative_to(workspace_root.absolute())
    except ValueError:
        return False
    return True


def _run_backend_command(*, repo_root: Path, command: list[str]) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = _pythonpath_env(repo_root)
    completed = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    payload_text = stdout or stderr
    if completed.returncode != 0:
        return {
            "status": "backend_failed",
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "command": command,
        }
    try:
        payload = json.loads(payload_text) if payload_text else {}
    except json.JSONDecodeError:
        return {
            "status": "backend_output_invalid",
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "command": command,
        }
    if not isinstance(payload, dict):
        return {
            "status": "backend_output_invalid",
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "command": command,
        }
    payload["command"] = command
    payload["returncode"] = completed.returncode
    return payload


def _skipped_storage_category(*, category: str, workspace_root: Path, reason: str) -> dict[str, Any]:
    return {
        "category": category,
        "workspace_root": str(workspace_root),
        "bytes": 0,
        "total_bytes": 0,
        "candidate_action": f"skipped-{reason}",
        "estimated_release_bytes": 0,
        "actual_release_bytes": 0,
        "blockers": [reason],
    }


def _actual_release_bytes(before: Mapping[str, Any], after: Mapping[str, Any]) -> int:
    return max(0, int(before.get("total_bytes") or 0) - int(after.get("total_bytes") or 0))


def _deleted_bytes_from_apply_result(report: Mapping[str, Any]) -> int:
    apply_result = report.get("apply_result")
    deleted_bytes = int(apply_result.get("deleted_bytes") or 0) if isinstance(apply_result, Mapping) else 0
    reinitialize_result = report.get("empty_repo_reinitialize_result")
    reinitialized_bytes = (
        int(reinitialize_result.get("released_bytes") or 0) if isinstance(reinitialize_result, Mapping) else 0
    )
    return deleted_bytes + reinitialized_bytes


def audit_workspace_storage(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    all_studies: bool = True,
    stopped_only: bool = False,
    apply: bool = False,
    git_only: bool = False,
    include_worktrees: bool = True,
    older_than_seconds: int = 6 * 3600,
    jsonl_max_mb: int = 64,
    text_max_mb: int = 16,
    event_segment_max_mb: int = 64,
    slim_jsonl_threshold_mb: int | None = 8,
    dedupe_worktree_min_mb: int | None = 16,
    head_lines: int = 200,
    tail_lines: int = 200,
    allow_live_runtime: bool = False,
    restore_proof_compaction: bool = False,
    include_parked_controller_stop: bool = False,
    reinitialize_empty_workspace_git: bool = False,
) -> dict[str, Any]:
    recorded_at = _utc_now()
    workspace_root = profile.workspace_root.expanduser().resolve()
    selected_roots = [] if git_only else _selected_study_roots(profile=profile, study_id=study_id, all_studies=all_studies)
    study_reports: list[dict[str, Any]] = []
    runtime_total_bytes = 0
    runtime_estimated_release_bytes = 0
    runtime_actual_release_bytes = 0
    artifact_total_bytes = 0
    cache_scan_roots: list[Path] | None = [] if study_id and not git_only else None
    for selected_study_root in selected_roots:
        try:
            resolved_study_id, resolved_study_root, study_payload = study_runtime_resolution._resolve_study(
                profile=profile,
                study_id=selected_study_root.name,
                study_root=None,
            )
            quest_id = _resolve_quest_id(
                study_id=resolved_study_id,
                study_root=resolved_study_root,
                study_payload=study_payload,
            )
            runtime_paths = resolve_study_runtime_paths(
                profile=profile,
                study_root=resolved_study_root,
                study_id=resolved_study_id,
                quest_id=quest_id,
            )
            quest_root = Path(runtime_paths["quest_root"]).expanduser().resolve()
            if cache_scan_roots is not None:
                cache_scan_roots.extend([resolved_study_root, quest_root])
            snapshot = _quest_runtime_snapshot(quest_root)
            size_before = _size_summary(quest_root)
            candidate = _runtime_candidate(quest_root=quest_root, snapshot=snapshot, size_summary=size_before)
            if restore_proof_compaction:
                candidate = restore_proof_compaction_candidate(
                    candidate=candidate,
                    snapshot=snapshot,
                    include_parked_controller_stop=include_parked_controller_stop,
                )
            if stopped_only and str(snapshot.get("status") or "") not in _TERMINAL_RUNTIME_STATUSES:
                runtime_report = dict(candidate)
                if apply:
                    runtime_report["estimated_release_bytes"] = 0
                runtime_report["actual_release_bytes"] = 0
                study_reports.append(
                    {
                        "study_id": resolved_study_id,
                        "study_root": str(resolved_study_root),
                        "quest_id": quest_id,
                        "quest_root": str(quest_root),
                        "status": "skipped_stopped_only",
                        "quest_runtime": snapshot,
                        "runtime": runtime_report,
                        "actual_runtime_release_bytes": 0,
                    }
                )
                continue
            apply_result: dict[str, Any] | None = None
            if apply:
                apply_result = maintain_runtime_storage(
                    profile=profile,
                    study_id=resolved_study_id,
                    study_root=None,
                    include_worktrees=include_worktrees,
                    older_than_seconds=older_than_seconds,
                    jsonl_max_mb=jsonl_max_mb,
                    text_max_mb=text_max_mb,
                    event_segment_max_mb=event_segment_max_mb,
                    slim_jsonl_threshold_mb=slim_jsonl_threshold_mb,
                    dedupe_worktree_min_mb=dedupe_worktree_min_mb,
                    head_lines=head_lines,
                    tail_lines=tail_lines,
                    allow_live_runtime=allow_live_runtime,
                    restore_proof_compaction=restore_proof_compaction,
                    include_parked_controller_stop=include_parked_controller_stop,
                )
            size_after = _size_summary(quest_root)
            actual_runtime_release_bytes = _actual_release_bytes(size_before, size_after) if apply else 0
            runtime_report = dict(candidate)
            runtime_estimated_release_bytes_for_report = (
                actual_runtime_release_bytes
                if apply
                else int(candidate.get("estimated_release_bytes") or 0)
            )
            runtime_report["estimated_release_bytes"] = runtime_estimated_release_bytes_for_report
            runtime_report["actual_release_bytes"] = actual_runtime_release_bytes
            artifact_summary = _study_artifact_size_summary(resolved_study_root)
            artifact_lifecycle_registry = build_study_artifact_lifecycle_registry(
                study_root=resolved_study_root,
                workspace_root=workspace_root,
                quest_root=quest_root,
                runtime_status=snapshot,
            )
            runtime_total_bytes += int(size_before.get("total_bytes") or 0)
            runtime_estimated_release_bytes += runtime_estimated_release_bytes_for_report
            runtime_actual_release_bytes += actual_runtime_release_bytes
            artifact_total_bytes += int(artifact_summary.get("total_bytes") or 0)
            study_reports.append(
                {
                    "study_id": resolved_study_id,
                    "study_root": str(resolved_study_root),
                    "quest_id": quest_id,
                    "quest_root": str(quest_root),
                    "status": "applied" if apply_result and apply_result.get("status") == "maintained" else "audited",
                    "quest_runtime": snapshot,
                    "runtime": runtime_report,
                    "artifact_lifecycle_registry": artifact_lifecycle_registry,
                    "size_before": size_before,
                    "size_after": size_after,
                    "study_artifacts": artifact_summary,
                    "apply_result": apply_result,
                    "restore_proof_compaction": _mapping(apply_result.get("restore_proof_compaction"))
                    if isinstance(apply_result, Mapping)
                    else {},
                    "actual_runtime_release_bytes": actual_runtime_release_bytes,
                }
            )
        except Exception as exc:
            if cache_scan_roots is not None:
                cache_scan_roots.append(selected_study_root)
            study_reports.append(
                {
                    "study_root": str(selected_study_root),
                    "status": "blocked_study_resolution_failed",
                    "error": str(exc),
                }
            )

    dataset_report = (
        _skipped_storage_category(category="dataset", workspace_root=workspace_root, reason="git_only")
        if git_only
        else _dataset_retention_audit(workspace_root)
    )
    git_report = _git_storage_audit(
        workspace_root,
        older_than_seconds=older_than_seconds,
        apply=apply,
        reinitialize_empty_workspace_git=reinitialize_empty_workspace_git,
    )
    git_report["actual_release_bytes"] = _deleted_bytes_from_apply_result(git_report)
    cache_report = (
        _skipped_storage_category(category="cache", workspace_root=workspace_root, reason="git_only")
        if git_only
        else _delete_safe_candidates(workspace_root, apply=apply, scan_roots=cache_scan_roots)
    )
    cache_actual_release_bytes = int(cache_report.get("actual_release_bytes") or 0)
    dataset_estimated_release_bytes = int(dataset_report.get("estimated_release_bytes") or 0)
    estimated_release_bytes = (
        runtime_estimated_release_bytes
        + (0 if apply else dataset_estimated_release_bytes)
        + int(git_report.get("estimated_release_bytes") or 0)
        + int(cache_report.get("estimated_release_bytes") or 0)
    )
    actual_release_bytes = (
        runtime_actual_release_bytes
        + int(git_report.get("actual_release_bytes") or 0)
        + cache_actual_release_bytes
    )
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": recorded_at,
        "profile_name": profile.name,
        "workspace_root": str(workspace_root),
        "mode": "apply" if apply else "dry-run",
        "selection": {
            "study_id": study_id,
            "all_studies": all_studies,
            "stopped_only": stopped_only,
            "allow_live_runtime": allow_live_runtime,
            "restore_proof_compaction": restore_proof_compaction,
            "include_parked_controller_stop": include_parked_controller_stop,
            "git_only": git_only,
            "reinitialize_empty_workspace_git": reinitialize_empty_workspace_git,
        },
        "summary": {
            "study_count": len(study_reports),
            "estimated_release_bytes": estimated_release_bytes,
            "actual_release_bytes": actual_release_bytes,
            "runtime_total_bytes": runtime_total_bytes,
            "runtime_estimated_release_bytes": runtime_estimated_release_bytes,
            "runtime_actual_release_bytes": runtime_actual_release_bytes,
            "dataset_total_bytes": dataset_report["total_bytes"],
            "dataset_archive_offline_candidate_bytes": dataset_report["estimated_release_bytes"],
            "cache_delete_safe_bytes": cache_report["estimated_release_bytes"],
            "cache_actual_release_bytes": cache_actual_release_bytes,
            "git_actual_release_bytes": int(git_report.get("actual_release_bytes") or 0),
            "study_artifact_total_bytes": artifact_total_bytes,
        },
        "categories": {
            "runtime": {
                "category": "runtime",
                "bytes": runtime_total_bytes,
                "candidate_action": "skipped-git-only" if git_only else "compress-online",
                "estimated_release_bytes": runtime_estimated_release_bytes,
                "actual_release_bytes": runtime_actual_release_bytes,
                "actual_runtime_release_bytes": runtime_actual_release_bytes,
                "studies": study_reports,
            },
            "dataset": dataset_report,
            "git": git_report,
            "cache": cache_report,
            "study_artifact": {
                "category": "study_artifact",
                "bytes": artifact_total_bytes,
                "candidate_action": "keep-online",
                "estimated_release_bytes": 0,
            },
        },
    }
    audit_root = workspace_root / "storage_audit"
    report_path = audit_root / f"{_artifact_slug(recorded_at)}.json"
    latest_path = audit_root / "latest.json"
    report["report_path"] = str(report_path)
    report["latest_report_path"] = str(latest_path)
    _write_json(report_path, report)
    _write_json(latest_path, report)
    report["runtime_lifecycle_index"] = runtime_lifecycle_store.record_workspace_storage_audit(
        workspace_root=workspace_root,
        report=report,
        report_path=report_path,
        latest_report_path=latest_path,
    )
    _write_json(report_path, report)
    _write_json(latest_path, report)
    return report


def maintain_runtime_storage(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: Path | None,
    include_worktrees: bool = True,
    older_than_seconds: int = 6 * 3600,
    jsonl_max_mb: int = 64,
    text_max_mb: int = 16,
    event_segment_max_mb: int = 64,
    slim_jsonl_threshold_mb: int | None = 8,
    dedupe_worktree_min_mb: int | None = 16,
    head_lines: int = 200,
    tail_lines: int = 200,
    allow_live_runtime: bool = False,
    restore_proof_compaction: bool = False,
    include_parked_controller_stop: bool = False,
) -> dict[str, Any]:
    recorded_at = _utc_now()
    resolved_study_id, resolved_study_root, study_payload = study_runtime_resolution._resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    quest_id = _resolve_quest_id(
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
    )
    runtime_paths = resolve_study_runtime_paths(
        profile=profile,
        study_root=resolved_study_root,
        study_id=resolved_study_id,
        quest_id=quest_id,
    )
    resolved_quest_root = Path(runtime_paths["quest_root"]).expanduser().resolve()
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": recorded_at,
        "profile_name": profile.name,
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "quest_id": quest_id,
        "quest_root": str(resolved_quest_root),
        "include_worktrees": include_worktrees,
        "allow_live_runtime": allow_live_runtime,
        "restore_proof_compaction_enabled": restore_proof_compaction,
        "include_parked_controller_stop": include_parked_controller_stop,
    }
    result["quest_runtime_before"] = _quest_runtime_snapshot(resolved_quest_root)
    result["size_before"] = _size_summary(resolved_quest_root)

    if not result["quest_runtime_before"]["quest_exists"]:
        result["status"] = "blocked_missing_quest_root"
        result["summary"] = "quest root 尚未就绪，当前无法执行 runtime storage maintenance。"
    elif restore_proof_compaction:
        blockers = restore_proof_compaction_blockers(
            result["quest_runtime_before"],
            include_parked_controller_stop=include_parked_controller_stop,
        )
        if blockers:
            result["status"] = "blocked_restore_proof_compaction"
            result["summary"] = "quest 未达到 stopped-cold restore-proof compaction 条件。"
            result["restore_proof_compaction"] = {
                "surface_kind": "runtime_restore_proof_compaction",
                "status": "blocked_not_stopped_cold",
                "quest_id": quest_id,
                "quest_root": str(resolved_quest_root),
                "actual_release_bytes": 0,
                "blockers": blockers,
            }
        else:
            compaction_result = compact_cold_runtime_buckets(
                quest_root=resolved_quest_root,
                quest_id=quest_id,
                recorded_at=recorded_at,
                buckets=_PRIMARY_BUCKETS,
            )
            result["restore_proof_compaction"] = compaction_result
            archive_ref = compaction_result.get("archive_ref")
            if isinstance(archive_ref, Mapping):
                result["runtime_lifecycle_archive_index"] = runtime_lifecycle_store.record_archive_ref(
                    quest_root=resolved_quest_root,
                    archive_ref=archive_ref,
                )
            status = str(compaction_result.get("status") or "")
            if status in {"compacted", "nothing_to_archive"}:
                result["status"] = "maintained"
                result["summary"] = "stopped-cold runtime restore-proof compaction 已完成。"
            else:
                result["status"] = status or "blocked_restore_proof_compaction"
                result["summary"] = "stopped-cold runtime restore-proof compaction 未完成。"
    elif (
        not allow_live_runtime
        and result["quest_runtime_before"]["status"] in _LIVE_RUNTIME_STATUSES
        and result["quest_runtime_before"]["active_run_id"] is not None
    ):
        result["status"] = "blocked_live_runtime"
        result["summary"] = "quest 当前仍在 live runtime，storage maintenance 需要先停车或显式放行。"
    else:
        script_path = _backend_script_path(profile)
        if script_path is None or profile.med_deepscientist_repo_root is None:
            result["status"] = "blocked_backend_unavailable"
            result["summary"] = "med-deepscientist runtime storage maintenance 脚本当前不可用。"
        else:
            command = _build_command(
                script_path=script_path,
                quest_root=resolved_quest_root,
                include_worktrees=include_worktrees,
                older_than_seconds=older_than_seconds,
                jsonl_max_mb=jsonl_max_mb,
                text_max_mb=text_max_mb,
                event_segment_max_mb=event_segment_max_mb,
                slim_jsonl_threshold_mb=slim_jsonl_threshold_mb,
                dedupe_worktree_min_mb=dedupe_worktree_min_mb,
                head_lines=head_lines,
                tail_lines=tail_lines,
            )
            backend_result = _run_backend_command(
                repo_root=profile.med_deepscientist_repo_root.expanduser().resolve(),
                command=command,
            )
            result["maintenance"] = backend_result
            if backend_result.get("status") in {"backend_failed", "backend_output_invalid"}:
                result["status"] = str(backend_result.get("status"))
                result["summary"] = "med-deepscientist runtime storage maintenance 执行失败。"
            else:
                result["status"] = "maintained"
                result["summary"] = "runtime storage maintenance 已完成。"

    result["quest_runtime_after"] = _quest_runtime_snapshot(resolved_quest_root)
    result["size_after"] = _size_summary(resolved_quest_root)
    report_path = _timestamped_report_path(resolved_study_root, recorded_at)
    latest_report_path = _latest_report_path(resolved_study_root)
    result["report_path"] = str(report_path)
    result["latest_report_path"] = str(latest_report_path)
    _write_json(report_path, result)
    _write_json(latest_report_path, result)
    return result
