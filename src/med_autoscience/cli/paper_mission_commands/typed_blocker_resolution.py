from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli.paper_mission_output_roots import (
    PAPER_MISSION_TYPED_BLOCKER_RESOLUTION_RELPATH,
    _assert_safe_typed_blocker_resolution_output_root,
)
from med_autoscience.controllers.paper_mission_typed_blocker_resolution import (
    diagnose_typed_blocker_resolution_gap,
    latest_typed_blocker_resolution_readback,
    materialize_typed_blocker_resolution,
)


def build_typed_blocker_resolution_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    paper_mission_readback_file: str | Path | None,
    output_root: str | Path | None,
    apply_mode: str | None,
    source: str,
) -> dict[str, Any]:
    if paper_mission_readback_file is None:
        return {
            "surface_kind": "paper_mission_typed_blocker_resolution",
            "schema_version": 1,
            "status": "blocked_missing_paper_mission_readback_file",
            "study_id": study_id,
            "profile_ref": str(profile_ref),
            "write_permitted": False,
            "authority_materialized": False,
        }
    readback = _load_json_object(Path(paper_mission_readback_file))
    resolved_output_root = None
    if output_root is not None:
        resolved_output_root = Path(output_root).expanduser().resolve()
        _assert_safe_typed_blocker_resolution_output_root(resolved_output_root)
    elif apply_mode is not None:
        resolved_output_root = typed_blocker_resolution_output_root(
            profile=profile,
            output_root=None,
        )
        _assert_safe_typed_blocker_resolution_output_root(resolved_output_root)
    if output_root is None and apply_mode is None:
        return diagnose_typed_blocker_resolution_gap(
            paper_mission_readback=readback,
            study_id=study_id,
            profile_ref=str(profile_ref),
            source=source,
        )
    return materialize_typed_blocker_resolution(
        paper_mission_readback=readback,
        study_id=study_id,
        profile_ref=str(profile_ref),
        output_root=resolved_output_root,
        apply_mode=apply_mode,
        source=source,
    )


def typed_blocker_resolution_apply_mode(
    *,
    apply_owner_decision: bool,
    apply_human_gate: bool,
    apply_route_redesign: bool,
) -> str | None:
    if apply_owner_decision:
        return "owner_decision"
    if apply_human_gate:
        return "human_gate"
    if apply_route_redesign:
        return "route_redesign"
    return None


def typed_blocker_resolution_output_root(
    *,
    profile: Any,
    output_root: str | Path | None,
) -> Path:
    if output_root is not None:
        return Path(output_root).expanduser().resolve()
    workspace_root = Path(profile.workspace_root).expanduser().resolve()
    return workspace_root / PAPER_MISSION_TYPED_BLOCKER_RESOLUTION_RELPATH


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return dict(payload)

