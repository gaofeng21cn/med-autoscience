from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport import med_deepscientist as med_deepscientist_transport


def parse_json_object_from_cli_stdout(stdout: str) -> dict[str, Any]:
    text = (stdout or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        payload = None
        for index, char in enumerate(text):
            if char != "{":
                continue
            try:
                candidate, consumed = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            if text[index + consumed :].strip():
                continue
            payload = candidate
            break
        if payload is None:
            raise
    if not isinstance(payload, dict):
        raise RuntimeError("CLI returned a non-object JSON payload")
    return payload


def run_workspace_display_repair_script(*, paper_root: Path) -> dict[str, Any]:
    script_path = paper_root / "build" / "generate_display_exports.py"
    if not script_path.exists():
        return {
            "status": "missing",
            "script_path": str(script_path),
        }
    completed = subprocess.run(
        [shutil.which("python3") or sys.executable, str(script_path)],
        cwd=str(paper_root.parent),
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        "status": "updated",
        "script_path": str(script_path),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def repair_paper_live_paths(
    *,
    profile: Any,
    quest_id: str,
    workspace_root: Path,
    current_workspace_root: Path,
) -> dict[str, Any]:
    launcher = med_deepscientist_transport._read_config_env_value(
        path=profile.med_deepscientist_runtime_root.parent / "config.env",
        key="MED_DEEPSCIENTIST_LAUNCHER",
    )
    command = [
        launcher,
        "--home",
        str(profile.managed_runtime_home),
        "repair",
        "paper-live-paths",
        "--quest-id",
        quest_id,
        "--workspace-root",
        str(workspace_root),
        "--current-workspace-root",
        str(current_workspace_root),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return parse_json_object_from_cli_stdout(completed.stdout or "")
