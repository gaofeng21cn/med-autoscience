from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.domain_route_scan_parts import current_truth_owner


def write_owner_action(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    controller_route = current_truth_owner.current_story_surface_delta_blocker_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if controller_route is None:
        return None
    work_unit_id = _text(controller_route.get("work_unit_id")) or "medical_prose_write_repair"
    return {
        "action_type": "run_quality_repair_batch",
        "authority": "observability_only",
        "owner": "write",
        "request_owner": "write",
        "recommended_owner": "write",
        "reason": "manuscript_story_surface_delta_missing",
        "summary": (
            "The current AI reviewer-backed write route has a same-source story-surface blocker; "
            "redrive the write owner through the quality repair batch until the canonical "
            "manuscript surface changes or a typed blocker remains."
        ),
        "required_output_surface": (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        "route_target": "write",
        "next_work_unit": work_unit_id,
        "executable_work_unit": work_unit_id,
        "controller_route": controller_route,
        "work_unit_fingerprint": _text(controller_route.get("work_unit_fingerprint")),
        "controller_work_unit_id": work_unit_id,
        "quality_repair_batch_ref": _text(controller_route.get("quality_repair_batch_path")),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["write_owner_action"]
