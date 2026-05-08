from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import runtime_live_console_read_model


def build_live_console_read_model(**kwargs: Any) -> dict[str, Any]:
    return runtime_live_console_read_model.build_live_console_read_model(**kwargs)


def materialize_live_console_read_model(
    *,
    workspace_root: str | Path,
    profile_name: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return runtime_live_console_read_model.materialize_live_console_read_model(
        workspace_root=workspace_root,
        profile_name=profile_name,
        **kwargs,
    )


def build_live_console_stream_events(read_model: Mapping[str, Any]) -> list[dict[str, Any]]:
    return runtime_live_console_read_model.build_live_console_stream_events(read_model)


__all__ = [
    "build_live_console_read_model",
    "build_live_console_stream_events",
    "materialize_live_console_read_model",
]
