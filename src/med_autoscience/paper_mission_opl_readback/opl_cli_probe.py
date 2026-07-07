from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any


PACKAGED_OPL_BIN = Path("/Users/gaofeng/Library/Application Support/OPL/runtime/current/bin/opl")
DEV_OPL_BIN = Path("/Users/gaofeng/workspace/one-person-lab/bin/opl")
PATH_OPL_BIN = "opl"
DEFAULT_OPL_READBACK_TIMEOUT_SECONDS = 8.0


def ranked_opl_bin_candidates(opl_bin: str | Path | None = None) -> list[Path]:
    if opl_bin is not None:
        explicit = Path(opl_bin).expanduser()
        if explicit.exists():
            return [explicit]
        resolved = shutil.which(str(opl_bin))
        return [Path(resolved).expanduser()] if resolved is not None else [explicit]
    configured = os.environ.get("OPL_BIN") or os.environ.get("OPL_FAMILY_RUNTIME_BIN")
    if configured:
        return [Path(configured).expanduser()]
    candidates: list[Path] = []
    path_candidate = shutil.which(PATH_OPL_BIN)
    if path_candidate is not None:
        candidates.append(Path(path_candidate).expanduser())
    candidates.extend([PACKAGED_OPL_BIN, DEV_OPL_BIN])
    ranked: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        if resolved in seen:
            continue
        seen.add(resolved)
        ranked.append(candidate)
    return ranked


def run_opl_json(
    opl_bin: Path,
    args: tuple[str, ...],
    *,
    timeout_seconds: float = DEFAULT_OPL_READBACK_TIMEOUT_SECONDS,
) -> dict[str, Any] | None:
    if timeout_seconds <= 0:
        return None
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            [str(opl_bin), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        stdout, _ = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        if process is not None:
            _terminate_process_group(process)
        return None
    except OSError:
        return None
    if process.returncode != 0:
        return None
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def remaining_seconds(deadline: float) -> float:
    return max(0.0, deadline - time.monotonic())


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        process.kill()
        return
    try:
        process.communicate(timeout=0.2)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except OSError:
        process.kill()
        return
    try:
        process.communicate(timeout=0.2)
    except subprocess.TimeoutExpired:
        pass


__all__ = [
    "DEFAULT_OPL_READBACK_TIMEOUT_SECONDS",
    "DEV_OPL_BIN",
    "PACKAGED_OPL_BIN",
    "PATH_OPL_BIN",
    "ranked_opl_bin_candidates",
    "remaining_seconds",
    "run_opl_json",
]
