from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


def inspect_workspace_python_environment(*, workspace_root: Path) -> dict[str, Any]:
    root = Path(workspace_root).expanduser().resolve()
    python_path = root / ".venv" / "bin" / "python3"
    ready = python_path.is_file() and os.access(python_path, os.X_OK)
    analysis_bundle = _inspect_analysis_bundle_with_workspace_python(python_path) if ready else None
    return {
        "status": "ready" if ready else "workspace_python_missing",
        "workspace_root": str(root),
        "python_path": str(python_path),
        "ready": ready,
        "analysis_bundle": analysis_bundle,
        "provisioning": {
            "owner": "uv",
            "owner_surface": "uv sync",
            "requirement_profile": "med-autoscience[analysis]",
            "effect": "read_only",
            "mas_provisioning_allowed": False,
        },
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


__all__ = ["inspect_workspace_python_environment"]
