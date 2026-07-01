from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_opl_readback_parts.primitives import (
    read_json_object,
    study_relative_ref,
    text_value,
    workspace_relative_ref,
    workspace_root_for_study_root,
)


def matching_terminal_closeout(
    *,
    carrier: Mapping[str, Any],
    study_root: Path,
    closeout_relative_roots: Sequence[Path],
    workspace_closeout_relative_roots: Sequence[Path],
    matches_carrier: Callable[..., bool],
) -> tuple[dict[str, Any], str] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    matches: list[tuple[float, dict[str, Any], str]] = []
    for root_ref in closeout_relative_roots:
        closeout_root = resolved_study_root / root_ref
        if not closeout_root.is_dir():
            continue
        for closeout_path in closeout_root.glob("*.json"):
            closeout = read_json_object(closeout_path)
            if closeout is None or not matches_carrier(
                closeout=closeout,
                carrier=carrier,
            ):
                continue
            matches.append(
                (
                    closeout_path.stat().st_mtime,
                    closeout,
                    study_relative_ref(
                        study_root=resolved_study_root,
                        path=closeout_path,
                    ),
                )
            )
    workspace_root = workspace_root_for_study_root(resolved_study_root)
    if workspace_root is not None:
        for root_ref in workspace_closeout_relative_roots:
            closeout_root = workspace_root / root_ref
            if not closeout_root.is_dir():
                continue
            pattern = f"**/{text_value(carrier.get('study_id'))}/stage_attempt_closeout_packet.json"
            for closeout_path in closeout_root.glob(pattern):
                closeout = read_json_object(closeout_path)
                if closeout is None or not matches_carrier(
                    closeout=closeout,
                    carrier=carrier,
                ):
                    continue
                matches.append(
                    (
                        closeout_path.stat().st_mtime,
                        closeout,
                        workspace_relative_ref(
                            workspace_root=workspace_root,
                            path=closeout_path,
                        ),
                    )
                )
    if not matches:
        return None
    _mtime, closeout, closeout_ref = sorted(
        matches,
        key=lambda item: item[0],
        reverse=True,
    )[0]
    return closeout, closeout_ref
