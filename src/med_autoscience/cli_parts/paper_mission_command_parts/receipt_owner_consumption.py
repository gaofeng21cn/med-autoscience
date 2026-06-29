from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli_parts.paper_mission_output_roots import (
    PAPER_MISSION_RECEIPT_OWNER_CONSUMPTION_RELPATH,
    _assert_safe_receipt_owner_consumption_output_root,
)
from med_autoscience.controllers.paper_mission_receipt_owner_consumption import (
    latest_receipt_owner_consumption_readback,
    materialize_receipt_owner_consumption,
)


def build_receipt_owner_consumption_readback(
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
            "surface_kind": "paper_mission_receipt_owner_consumption",
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
        resolved_output_root = Path(output_root)
        _assert_safe_receipt_owner_consumption_output_root(resolved_output_root)
    elif apply_mode is not None:
        resolved_output_root = receipt_owner_consumption_output_root(
            profile=profile,
            output_root=None,
        )
        _assert_safe_receipt_owner_consumption_output_root(resolved_output_root)
    return materialize_receipt_owner_consumption(
        paper_mission_readback=readback,
        study_id=study_id,
        profile_ref=str(profile_ref),
        output_root=resolved_output_root,
        apply_mode=apply_mode,
        source=source,
    )


def receipt_owner_consumption_apply_mode(
    *,
    apply_typed_blocker: bool,
    apply_route_checkpoint: bool,
) -> str | None:
    if apply_typed_blocker:
        return "typed_blocker"
    if apply_route_checkpoint:
        return "route_checkpoint"
    return None


def receipt_owner_consumption_output_root(
    *,
    profile: Any,
    output_root: str | Path | None,
) -> Path:
    if output_root is not None:
        return Path(output_root).expanduser().resolve()
    workspace_root = Path(profile.workspace_root).expanduser().resolve()
    return workspace_root / PAPER_MISSION_RECEIPT_OWNER_CONSUMPTION_RELPATH


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return dict(payload)

