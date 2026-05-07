from __future__ import annotations

import shlex
from pathlib import Path

from .shared_labels import _non_empty_text


def _quote_cli_arg(value: str | Path | None) -> str:
    text = str(value or "").strip()
    if not text:
        return "<profile>"
    return shlex.quote(text)


def _profile_command_prefix(profile_ref: str | Path | None) -> str:
    return "uv run python -m med_autoscience.cli --help >/dev/null 2>&1 || true\nuv run python -m med_autoscience.cli"


def _profile_arg(profile_ref: str | Path | None) -> str:
    return _quote_cli_arg(Path(profile_ref).expanduser().resolve() if profile_ref is not None else None)


def _command_prefix(profile_ref: str | Path | None) -> str:
    del profile_ref
    return "uv run python -m med_autoscience.cli"


def _json_surface_command(command: str) -> str:
    if "--format" in command:
        return command
    return f"{command} --format json"


def _study_selector(*, study_id: str | None = None, study_root: Path | None = None) -> str:
    if study_id is not None:
        return f"--study-id {_quote_cli_arg(study_id)}"
    if study_root is not None:
        return f"--study-root {_quote_cli_arg(Path(study_root).expanduser().resolve())}"
    raise ValueError("study_id or study_root is required")


def _require_direct_entry_mode(value: str | None, *, supported_modes: tuple[str, ...]) -> str:
    mode = _non_empty_text(value) or "direct"
    if mode not in supported_modes:
        raise ValueError(f"direct entry mode 不支持: {mode}")
    return mode
