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
    candidate_priority: Callable[..., Any] | None = None,
) -> tuple[dict[str, Any], str] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    matches: list[tuple[tuple[Any, ...], dict[str, Any], str]] = []
    for root_ref in closeout_relative_roots:
        closeout_root = resolved_study_root / root_ref
        if not closeout_root.is_dir():
            continue
        for closeout_path in closeout_root.glob("*.json"):
            closeout = read_json_object(closeout_path)
            route_back = _closeout_route_back_sidecar(closeout_path)
            if closeout is None or not matches_carrier(
                closeout=closeout,
                carrier=carrier,
                route_back=route_back,
            ):
                continue
            matches.append(
                (
                    _candidate_priority_tuple(
                        closeout=closeout,
                        carrier=carrier,
                        closeout_path=closeout_path,
                        closeout_ref=study_relative_ref(
                            study_root=resolved_study_root,
                            path=closeout_path,
                        ),
                        route_back=route_back,
                        candidate_priority=candidate_priority,
                    ),
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
            study_id = text_value(carrier.get("study_id"))
            patterns = [
                f"**/{study_id}/stage_attempt_closeout_packet.json",
                "**/stage_attempt_closeout_packet.json",
            ]
            seen_paths: set[Path] = set()
            for pattern in patterns:
                for closeout_path in closeout_root.glob(pattern):
                    resolved_path = closeout_path.resolve()
                    if resolved_path in seen_paths:
                        continue
                    seen_paths.add(resolved_path)
                    closeout = read_json_object(closeout_path)
                    route_back = _closeout_route_back_sidecar(closeout_path)
                    if closeout is None or not matches_carrier(
                        closeout=closeout,
                        carrier=carrier,
                        route_back=route_back,
                    ):
                        continue
                    matches.append(
                        (
                            _candidate_priority_tuple(
                                closeout=closeout,
                                carrier=carrier,
                                closeout_path=closeout_path,
                                closeout_ref=workspace_relative_ref(
                                    workspace_root=workspace_root,
                                    path=closeout_path,
                                ),
                                route_back=route_back,
                                candidate_priority=candidate_priority,
                            ),
                            closeout,
                            workspace_relative_ref(
                                workspace_root=workspace_root,
                                path=closeout_path,
                            ),
                        )
                    )
    if not matches:
        return None
    _priority, closeout, closeout_ref = sorted(
        matches,
        key=lambda item: item[0],
        reverse=True,
    )[0]
    return closeout, closeout_ref


def _candidate_priority_tuple(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
    closeout_path: Path,
    closeout_ref: str,
    route_back: Mapping[str, Any] | None,
    candidate_priority: Callable[..., Any] | None,
) -> tuple[Any, ...]:
    if candidate_priority is None:
        return (closeout_path.stat().st_mtime,)
    priority = candidate_priority(
        closeout=closeout,
        carrier=carrier,
        closeout_path=closeout_path,
        closeout_ref=closeout_ref,
        route_back=route_back,
    )
    return priority if isinstance(priority, tuple) else (priority,)


def _closeout_route_back_sidecar(closeout_path: Path) -> dict[str, Any] | None:
    if closeout_path.name != "stage_attempt_closeout_packet.json":
        return None
    route_back_path = closeout_path.with_name("route_back_evidence_packet.json")
    if not route_back_path.exists():
        return None
    return read_json_object(route_back_path)
