from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

from med_autoscience.controllers import data_assets, study_runtime_resolution
from med_autoscience.profiles import WorkspaceProfile
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
    runtime_state = quest_state.load_runtime_state(quest_root)
    return {
        "quest_exists": (quest_root / "quest.yaml").exists(),
        "status": str(runtime_state.get("status") or "").strip().lower() or None,
        "active_run_id": str(runtime_state.get("active_run_id") or "").strip() or None,
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
        return {
            "category": "runtime",
            "path": str(quest_root),
            "bytes": int(size_summary.get("total_bytes") or 0),
            "risk": "missing_truth_surface",
            "candidate_action": "blocked-missing-quest",
            "estimated_release_bytes": 0,
            "blockers": ["missing_quest_root"],
        }
    if status in _LIVE_RUNTIME_STATUSES and active_run_id is not None:
        return {
            "category": "runtime",
            "path": str(quest_root),
            "bytes": int(size_summary.get("total_bytes") or 0),
            "risk": "live_runtime",
            "candidate_action": "audit-only",
            "estimated_release_bytes": 0,
            "blockers": ["live_runtime_active"],
        }
    if status in _TERMINAL_RUNTIME_STATUSES or not active_run_id:
        release_bytes = sum(
            int(bucket.get("bytes") or 0)
            for name, bucket in dict(size_summary.get("buckets") or {}).items()
            if name in _PRIMARY_BUCKETS
        )
        return {
            "category": "runtime",
            "path": str(quest_root),
            "bytes": int(size_summary.get("total_bytes") or 0),
            "risk": "process_state_only",
            "candidate_action": "compress-online",
            "secondary_actions": ["dedupe-online", "archive-expanded-worktree-runtime"],
            "estimated_release_bytes": release_bytes,
            "blockers": [],
        }
    return {
        "category": "runtime",
        "path": str(quest_root),
        "bytes": int(size_summary.get("total_bytes") or 0),
        "risk": "unknown_runtime_state",
        "candidate_action": "audit-only",
        "estimated_release_bytes": 0,
        "blockers": ["unknown_runtime_state"],
    }


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


def _release_restore_handle(release: Mapping[str, Any]) -> str | None:
    source_release = release.get("source_release")
    source_payload = source_release if isinstance(source_release, Mapping) else {}
    release_contract = release.get("declared_release_contract")
    contract_payload = release_contract if isinstance(release_contract, Mapping) else {}
    for payload in (source_payload, contract_payload, release):
        for key in ("restore_handle", "restore_command", "archive_ref", "archive_uri", "external_archive_uri"):
            value = payload.get(key) if isinstance(payload, Mapping) else None
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _release_checksum(release: Mapping[str, Any]) -> str | None:
    source_release = release.get("source_release")
    source_payload = source_release if isinstance(source_release, Mapping) else {}
    release_contract = release.get("declared_release_contract")
    contract_payload = release_contract if isinstance(release_contract, Mapping) else {}
    for payload in (source_payload, contract_payload, release):
        for key in ("sha256", "checksum", "manifest_sha256", "archive_sha256"):
            value = payload.get(key) if isinstance(payload, Mapping) else None
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _dataset_retention_audit(workspace_root: Path) -> dict[str, Any]:
    releases = data_assets._scan_private_releases(workspace_root)
    superseded_by: dict[tuple[str, str], list[str]] = {}
    for release in releases:
        family_id = str(release.get("family_id") or "")
        version_id = str(release.get("version_id") or "")
        for superseded_version in release.get("supersedes_versions") or []:
            if not isinstance(superseded_version, str) or not superseded_version:
                continue
            superseded_by.setdefault((family_id, superseded_version), []).append(version_id)

    release_reports: list[dict[str, Any]] = []
    totals = {
        "total_bytes": 0,
        "keep_online_bytes": 0,
        "archive_offline_candidate_bytes": 0,
        "blocked_bytes": 0,
    }
    for release in releases:
        family_id = str(release.get("family_id") or "")
        version_id = str(release.get("version_id") or "")
        inventory = release.get("inventory_summary") if isinstance(release.get("inventory_summary"), Mapping) else {}
        release_bytes = int(inventory.get("total_size_bytes") or 0)
        totals["total_bytes"] += release_bytes
        superseding_versions = sorted(superseded_by.get((family_id, version_id), []))
        blockers: list[str] = []
        restore_handle = _release_restore_handle(release)
        checksum = _release_checksum(release)
        if release.get("contract_status") != "manifest_backed":
            blockers.append("missing_dataset_manifest")
        if superseding_versions:
            if not restore_handle:
                blockers.append("missing_restore_handle")
            if not checksum:
                blockers.append("missing_checksum")
            if blockers:
                action = "blocked"
                risk = "lineage_incomplete"
                estimated_release_bytes = 0
                totals["blocked_bytes"] += release_bytes
            else:
                action = "archive-offline"
                risk = "superseded_lineage_with_restore"
                estimated_release_bytes = release_bytes
                totals["archive_offline_candidate_bytes"] += release_bytes
        else:
            action = "keep-online"
            risk = "canonical_or_unsuperseded_release"
            estimated_release_bytes = 0
            totals["keep_online_bytes"] += release_bytes
        release_reports.append(
            {
                "family_id": family_id,
                "dataset_id": release.get("dataset_id"),
                "version_id": version_id,
                "data_root": release.get("data_root"),
                "manifest_path": release.get("manifest_path"),
                "bytes": release_bytes,
                "superseded_by": superseding_versions,
                "source_release": release.get("source_release"),
                "restore_handle": restore_handle,
                "checksum": checksum,
                "candidate_action": action,
                "risk": risk,
                "estimated_release_bytes": estimated_release_bytes,
                "blockers": blockers,
            }
        )
    return {
        "category": "dataset",
        "workspace_root": str(workspace_root),
        "release_count": len(release_reports),
        "total_bytes": totals["total_bytes"],
        "candidate_action": "lineage-aware-retention",
        "estimated_release_bytes": totals["archive_offline_candidate_bytes"],
        "totals": totals,
        "releases": release_reports,
    }


def _git_storage_audit(workspace_root: Path) -> dict[str, Any]:
    git_root = workspace_root / ".git"
    tmp_pack_files = []
    objects_root = git_root / "objects"
    if objects_root.exists():
        tmp_pack_files = [
            {
                "path": str(path),
                "bytes": _directory_size_bytes(path),
                "candidate_action": "delete-safe-via-git-maintenance",
            }
            for path in sorted(objects_root.glob("pack/tmp_pack_*"))
            if path.is_file()
        ]
    return {
        "category": "git",
        "path": str(git_root),
        "bytes": _directory_size_bytes(git_root),
        "risk": "git_object_store",
        "candidate_action": "git-maintenance-advisory",
        "estimated_release_bytes": 0,
        "tmp_pack_files": tmp_pack_files,
        "restore_command": "git fsck && git gc",
    }


def _delete_safe_candidates(workspace_root: Path) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    if not workspace_root.exists():
        return {
            "category": "cache",
            "workspace_root": str(workspace_root),
            "candidate_action": "delete-safe",
            "bytes": 0,
            "estimated_release_bytes": 0,
            "candidates": [],
        }
    for current_root, dirnames, filenames in os.walk(workspace_root):
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
    return {
        "category": "cache",
        "workspace_root": str(workspace_root),
        "candidate_action": "delete-safe",
        "bytes": total_bytes,
        "estimated_release_bytes": total_bytes,
        "candidates": candidates,
    }


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


def audit_workspace_storage(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    all_studies: bool = True,
    stopped_only: bool = False,
    apply: bool = False,
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
) -> dict[str, Any]:
    recorded_at = _utc_now()
    workspace_root = profile.workspace_root.expanduser().resolve()
    selected_roots = _selected_study_roots(profile=profile, study_id=study_id, all_studies=all_studies)
    study_reports: list[dict[str, Any]] = []
    runtime_total_bytes = 0
    runtime_estimated_release_bytes = 0
    artifact_total_bytes = 0
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
            snapshot = _quest_runtime_snapshot(quest_root)
            size_before = _size_summary(quest_root)
            candidate = _runtime_candidate(quest_root=quest_root, snapshot=snapshot, size_summary=size_before)
            if stopped_only and str(snapshot.get("status") or "") not in _TERMINAL_RUNTIME_STATUSES:
                study_reports.append(
                    {
                        "study_id": resolved_study_id,
                        "study_root": str(resolved_study_root),
                        "quest_id": quest_id,
                        "quest_root": str(quest_root),
                        "status": "skipped_stopped_only",
                        "quest_runtime": snapshot,
                        "runtime": candidate,
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
                )
            size_after = _size_summary(quest_root)
            artifact_summary = _study_artifact_size_summary(resolved_study_root)
            runtime_total_bytes += int(size_before.get("total_bytes") or 0)
            runtime_estimated_release_bytes += int(candidate.get("estimated_release_bytes") or 0)
            artifact_total_bytes += int(artifact_summary.get("total_bytes") or 0)
            study_reports.append(
                {
                    "study_id": resolved_study_id,
                    "study_root": str(resolved_study_root),
                    "quest_id": quest_id,
                    "quest_root": str(quest_root),
                    "status": "applied" if apply_result and apply_result.get("status") == "maintained" else "audited",
                    "quest_runtime": snapshot,
                    "runtime": candidate,
                    "size_before": size_before,
                    "size_after": size_after,
                    "study_artifacts": artifact_summary,
                    "apply_result": apply_result,
                }
            )
        except Exception as exc:
            study_reports.append(
                {
                    "study_root": str(selected_study_root),
                    "status": "blocked_study_resolution_failed",
                    "error": str(exc),
                }
            )

    dataset_report = _dataset_retention_audit(workspace_root)
    git_report = _git_storage_audit(workspace_root)
    cache_report = _delete_safe_candidates(workspace_root)
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
        },
        "summary": {
            "study_count": len(study_reports),
            "runtime_total_bytes": runtime_total_bytes,
            "runtime_estimated_release_bytes": runtime_estimated_release_bytes,
            "dataset_total_bytes": dataset_report["total_bytes"],
            "dataset_archive_offline_candidate_bytes": dataset_report["estimated_release_bytes"],
            "cache_delete_safe_bytes": cache_report["estimated_release_bytes"],
            "study_artifact_total_bytes": artifact_total_bytes,
        },
        "categories": {
            "runtime": {
                "category": "runtime",
                "bytes": runtime_total_bytes,
                "candidate_action": "compress-online",
                "estimated_release_bytes": runtime_estimated_release_bytes,
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
    }
    result["quest_runtime_before"] = _quest_runtime_snapshot(resolved_quest_root)
    result["size_before"] = _size_summary(resolved_quest_root)

    if not result["quest_runtime_before"]["quest_exists"]:
        result["status"] = "blocked_missing_quest_root"
        result["summary"] = "quest root 尚未就绪，当前无法执行 runtime storage maintenance。"
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
