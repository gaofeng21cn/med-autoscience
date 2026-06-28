from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_authority_snapshot


def route_context_from_study_authority_surfaces(*, study_root: Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    truth_snapshot = _read_json_object(resolved_study_root / "artifacts" / "truth" / "latest.json")
    runtime_health_snapshot = _read_json_object(
        resolved_study_root / "artifacts" / "runtime" / "health" / "latest.json"
    )
    publication_eval = _read_json_object(
        resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
    )
    if not truth_snapshot or not runtime_health_snapshot:
        return {}
    return {
        "authority_snapshot": domain_authority_snapshot.build_authority_snapshot(
            {
                "study_id": resolved_study_root.name,
                "study_truth_snapshot": truth_snapshot,
                "runtime_health_snapshot": runtime_health_snapshot,
                "publication_eval": publication_eval,
            }
        )
    }


def with_study_authority_route_context(
    *,
    study_root: Path,
    context: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if context is not None and context.get("authority_snapshot"):
        return context
    derived = route_context_from_study_authority_surfaces(study_root=study_root)
    if not derived:
        return context
    return {**derived, **(context or {})}


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


__all__ = [
    "route_context_from_study_authority_surfaces",
    "with_study_authority_route_context",
]
