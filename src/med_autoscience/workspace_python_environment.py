from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def ensure_workspace_python_environment(*, workspace_root: Path) -> dict[str, Any]:
    root = Path(workspace_root).expanduser().resolve()
    python_path = root / ".venv" / "bin" / "python3"
    uv_path = shutil.which("uv")
    if uv_path is None:
        return {
            "status": "uv_missing",
            "workspace_root": str(root),
            "python_path": str(python_path),
            "ready": python_path.is_file() and python_path.stat().st_mode & 0o111 != 0,
            "exit_code": None,
            "stdout": "",
            "stderr": "uv executable not found on PATH",
        }
    sync = subprocess.run(
        [uv_path, "sync", "--directory", str(root), "--extra", "analysis", "--inexact"],
        capture_output=True,
        text=True,
        check=False,
    )
    ready = python_path.is_file() and python_path.stat().st_mode & 0o111 != 0
    analysis_bundle = _inspect_analysis_bundle_with_workspace_python(python_path) if ready else None
    return {
        "status": "ready" if ready and sync.returncode == 0 else "failed",
        "workspace_root": str(root),
        "python_path": str(python_path),
        "ready": ready and sync.returncode == 0,
        "sync": {
            "command": [uv_path, "sync", "--directory", str(root), "--extra", "analysis", "--inexact"],
            "exit_code": sync.returncode,
            "stdout": sync.stdout,
            "stderr": sync.stderr,
        },
        "analysis_bundle": analysis_bundle,
    }


def _inspect_analysis_bundle_with_workspace_python(python_path: Path) -> dict[str, Any]:
    probe = (
        "import json\n"
        "from med_autoscience import study_runtime_analysis_bundle\n"
        "print(json.dumps(study_runtime_analysis_bundle.inspect_analysis_bundle(), ensure_ascii=False))\n"
    )
    completed = subprocess.run(
        [str(python_path), "-c", probe],
        capture_output=True,
        text=True,
        check=False,
    )
    payload: dict[str, Any] | None = None
    if completed.returncode == 0:
        try:
            loaded = json.loads(completed.stdout)
        except json.JSONDecodeError:
            loaded = None
        if isinstance(loaded, dict):
            payload = loaded
    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "payload": payload,
        "ready": bool(payload and payload.get("ready") is True),
    }


__all__ = ["ensure_workspace_python_environment"]
