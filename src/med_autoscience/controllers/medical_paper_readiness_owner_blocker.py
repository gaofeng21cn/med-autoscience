from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import medical_paper_readiness


SURFACE = "medical_paper_readiness_owner_blocker"
SCHEMA_VERSION = 1
CONTROLLER_DECISION_REF = Path("artifacts/controller_decisions/latest.json")


def build_readiness_owner_blocker(
    *,
    study_root: str | Path,
    source: str = "medical_paper_readiness_owner_blocker",
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    readiness = medical_paper_readiness.build_medical_paper_readiness_surface(study_root=root)
    status = _text(readiness.get("overall_status")) or "missing"
    missing_surfaces = _missing_required_surfaces(readiness)
    decision_path = (root / CONTROLLER_DECISION_REF).resolve()
    ready = status == "ready"
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": "ready_no_blocker" if ready else "stable_blocker",
        "study_root": str(root),
        "source": _text(source) or "medical_paper_readiness_owner_blocker",
        "readiness_ref": str(medical_paper_readiness.stable_medical_paper_readiness_path(study_root=root)),
        "controller_decision_ref": str(decision_path),
        "will_write_controller_decision": not ready,
        "controller_decision": None if ready else _controller_decision_payload(
            study_root=root,
            readiness=readiness,
            missing_surfaces=missing_surfaces,
            source=source,
        ),
        "authority_boundary": {
            "owner": "med-autoscience",
            "surface_owner": "med-autoscience",
            "writes_domain_truth": False,
            "writes_publication_quality": False,
            "writes_current_package": False,
            "writes_memory_body": False,
            "writes_controller_decision": not ready,
        },
    }


def materialize_readiness_owner_blocker(
    *,
    study_root: str | Path,
    source: str = "medical_paper_readiness_owner_blocker",
    apply: bool = False,
) -> dict[str, Any]:
    projection = build_readiness_owner_blocker(study_root=study_root, source=source)
    decision = projection.get("controller_decision")
    if not apply or not isinstance(decision, Mapping):
        projection["status"] = "dry_run" if projection["will_write_controller_decision"] else "ready_no_blocker"
        projection["applied"] = False
        return projection
    decision_path = Path(str(projection["controller_decision_ref"]))
    _write_json(decision_path, decision)
    projection["status"] = "materialized"
    projection["applied"] = True
    return projection


def _controller_decision_payload(
    *,
    study_root: Path,
    readiness: Mapping[str, Any],
    missing_surfaces: list[dict[str, Any]],
    source: str,
) -> dict[str, Any]:
    missing_keys = [_text(item.get("surface_key")) for item in missing_surfaces if _text(item.get("surface_key"))]
    next_action = _mapping(readiness.get("next_action"))
    return {
        "surface": "controller_decision",
        "schema_version": SCHEMA_VERSION,
        "decision_type": "medical_paper_readiness_owner_blocker",
        "generated_at": _utc_now(),
        "source": _text(source) or "medical_paper_readiness_owner_blocker",
        "study_root": str(study_root),
        "route_decision": "stable_blocker",
        "runtime_decision": "blocked",
        "blocked_reason": "medical_paper_readiness_missing",
        "blocked_surfaces": missing_keys,
        "next_owner": "med-autoscience",
        "requires_human_confirmation": False,
        "quality_claim_authorized": False,
        "submission_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "write_authorized": True,
        "readiness_ref": str(medical_paper_readiness.stable_medical_paper_readiness_path(study_root=study_root)),
        "readiness_status": _text(readiness.get("overall_status")) or "missing",
        "readiness_next_action": dict(next_action),
        "controller_blocker": {
            "blocker_id": "medical_paper_readiness_missing",
            "owner": "MedAutoScience",
            "reason": "medical paper readiness has missing or blocked required surfaces",
            "required_owner_surface": "medical_paper_readiness owner surface",
            "write_permitted": False,
        },
        "authority_boundary": {
            "owner": "med-autoscience",
            "domain_truth_owner": "med-autoscience",
            "quality_gate_owner": "med-autoscience",
            "artifact_authority_owner": "med-autoscience",
            "can_authorize_quality": False,
            "can_authorize_submission": False,
            "can_write_current_package": False,
            "can_write_memory_body": False,
        },
    }


def _missing_required_surfaces(readiness: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in readiness.get("capability_surfaces", [])
        if isinstance(item, Mapping)
        and item.get("required_for_ready") is True
        and _text(item.get("status")) != "present"
    ]


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["build_readiness_owner_blocker", "materialize_readiness_owner_blocker"]
