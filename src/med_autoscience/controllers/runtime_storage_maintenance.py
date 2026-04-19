from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

from med_autoscience.controllers import study_runtime_resolution
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol.study_runtime import resolve_study_runtime_paths


SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
_LIVE_RUNTIME_STATUSES = frozenset({"running", "active"})
_PRIMARY_BUCKETS = ("bash_exec", "codex_homes", "runs", "codex_history", "worktrees")


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


def _quest_runtime_snapshot(quest_root: Path) -> dict[str, Any]:
    runtime_state = quest_state.load_runtime_state(quest_root)
    return {
        "quest_exists": (quest_root / "quest.yaml").exists(),
        "status": str(runtime_state.get("status") or "").strip().lower() or None,
        "active_run_id": str(runtime_state.get("active_run_id") or "").strip() or None,
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
