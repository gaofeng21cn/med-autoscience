from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


def run_quest_storage_maintenance(
    *,
    profile: WorkspaceProfile,
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
) -> dict[str, Any] | None:
    script_path = _backend_script_path(profile)
    if script_path is None or profile.med_deepscientist_repo_root is None:
        return None
    repo_root = profile.med_deepscientist_repo_root.expanduser().resolve()
    command = _build_command(
        script_path=script_path,
        quest_root=quest_root,
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
    return _run_backend_command(repo_root=repo_root, command=command)


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
