from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.medical_quality_operating_system import (
    build_quality_os_runtime_materialization_contract,
)
from med_autoscience.publication_eval_reviewer_os import (
    validate_ai_reviewer_operating_system_trace,
)


__all__ = ["build_pre_draft_quality_runtime_state"]


_SURFACE = "pre_draft_quality_runtime_state"
_SCHEMA_VERSION = 1
_REQUIRED_STATUS = "closed"
_REQUIRED_POLICY_ID = "medical_publication_critique_v1"
_REQUIRED_READINESS_IDS = (
    "clinical_question",
    "population_design_outcome",
    "display_to_claim_map",
    "claim_evidence_map",
    "section_purpose",
    "reader_flow_plan",
    "journal_voice",
    "ai_prose_review_feedback_loop",
)
_AUTHORITY_SURFACES = {
    "pre_draft_readiness": Path("paper/pre_draft_writing_readiness.json"),
    "evidence_ledger": Path("paper/evidence_ledger.json"),
    "review_ledger": Path("paper/review_ledger.json"),
    "medical_manuscript_blueprint": Path("paper/medical_manuscript_blueprint.json"),
    "publication_eval": Path("artifacts/publication_eval/latest.json"),
}


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(payload, dict):
        return None, "not_json_object"
    return payload, None


def _text(value: object) -> str:
    return str(value or "").strip()


def _status(payload: dict[str, Any] | None) -> str:
    if not isinstance(payload, dict):
        return ""
    return _text(payload.get("status") or payload.get("readiness_status"))


def _surface_ref(path: Path, payload: dict[str, Any] | None, read_error: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
    }
    if read_error is not None:
        result["read_error"] = read_error
    if payload is not None:
        payload_status = _status(payload)
        if payload_status:
            result["status"] = payload_status
        eval_id = _text(payload.get("eval_id"))
        if eval_id:
            result["eval_id"] = eval_id
    return result


def _readiness_items_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = payload.get("readiness_items")
    if not isinstance(items, list):
        items = payload.get("required_readiness_items")
    if not isinstance(items, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        readiness_id = _text(item.get("readiness_id"))
        if readiness_id:
            result[readiness_id] = item
    return result


def _append_readiness_blockers(payload: dict[str, Any], blockers: list[str]) -> None:
    if _status(payload) != _REQUIRED_STATUS:
        blockers.append("pre_draft_readiness_not_closed")
    items_by_id = _readiness_items_by_id(payload)
    for readiness_id in _REQUIRED_READINESS_IDS:
        item = items_by_id.get(readiness_id)
        if item is None:
            blockers.append(f"pre_draft_readiness_item_missing:{readiness_id}")
            continue
        if _status(item) != _REQUIRED_STATUS:
            blockers.append(f"pre_draft_readiness_item_not_closed:{readiness_id}")


def _append_closed_surface_blocker(
    *,
    payload: dict[str, Any],
    surface_key: str,
    blockers: list[str],
) -> None:
    if _status(payload) != _REQUIRED_STATUS:
        blockers.append(f"{surface_key}_not_closed")


def _append_optional_closed_surface_blocker(
    *,
    payload: dict[str, Any],
    surface_key: str,
    blockers: list[str],
) -> None:
    payload_status = _status(payload)
    if payload_status and payload_status != _REQUIRED_STATUS:
        blockers.append(f"{surface_key}_not_closed")


def _blueprint_authorized(payload: dict[str, Any]) -> bool:
    provenance = payload.get("authoring_provenance")
    if not isinstance(provenance, dict):
        return False
    return (
        _text(provenance.get("owner")) in {"ai_author", "ai_reviewer"}
        and provenance.get("ai_reviewer_required") is False
    )


def _provenance_summary(publication_eval: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(publication_eval, dict):
        return {}
    provenance = publication_eval.get("assessment_provenance")
    if not isinstance(provenance, dict):
        return {}
    result: dict[str, Any] = {
        "owner": _text(provenance.get("owner")),
        "policy_id": _text(provenance.get("policy_id")),
        "ai_reviewer_required": provenance.get("ai_reviewer_required"),
    }
    source_refs = provenance.get("source_refs")
    if isinstance(source_refs, list):
        result["source_refs"] = [_text(item) for item in source_refs if _text(item)]
    return result


def _publication_eval_ai_reviewer_backed(publication_eval: dict[str, Any]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    provenance = publication_eval.get("assessment_provenance")
    if not isinstance(provenance, dict):
        return False, ["publication_eval_ai_reviewer_provenance_missing"]

    if _text(provenance.get("owner")) != "ai_reviewer":
        blockers.append("publication_eval_not_ai_reviewer_backed")
    if _text(provenance.get("policy_id")) != _REQUIRED_POLICY_ID:
        blockers.append("publication_eval_policy_not_ai_reviewer_critique")
    if provenance.get("ai_reviewer_required") is not False:
        blockers.append("publication_eval_still_requires_ai_reviewer")

    quality_assessment = publication_eval.get("quality_assessment")
    prose_quality = quality_assessment.get("medical_journal_prose_quality") if isinstance(quality_assessment, dict) else None
    if not isinstance(prose_quality, dict) or not _text(prose_quality.get("summary")):
        blockers.append("publication_eval_medical_prose_quality_missing")

    reviewer_os_errors = validate_ai_reviewer_operating_system_trace(
        publication_eval.get("reviewer_operating_system")
    )
    blockers.extend(f"publication_eval_reviewer_operating_system_invalid:{error}" for error in reviewer_os_errors)
    return not blockers, blockers


def _publication_eval_not_blocked(publication_eval: dict[str, Any]) -> bool:
    verdict = publication_eval.get("verdict")
    if not isinstance(verdict, dict):
        return False
    overall = _text(verdict.get("overall_verdict")).lower()
    if overall in {"blocked", "fail", "failed", "needs_review", "review_required"}:
        return False
    gaps = publication_eval.get("gaps")
    if isinstance(gaps, list) and gaps:
        return False
    return bool(overall)


def _route_back_for_status(status: str, blockers: list[str]) -> dict[str, Any]:
    if status == "first_full_draft_ready":
        return {
            "required": False,
            "status": "clear",
            "target": "first_full_draft",
            "reason": "pre_draft_quality_authority_closed",
        }
    if status == "review_required":
        return {
            "required": True,
            "status": "review_required",
            "target": "ai_reviewer_publication_eval",
            "reason": "ai_reviewer_quality_authority_missing",
            "blockers": list(blockers),
        }
    return {
        "required": True,
        "status": "route_back_required",
        "target": "pre_draft_writing_readiness",
        "reason": "pre_draft_authority_surface_not_closed",
        "blockers": list(blockers),
    }


def build_pre_draft_quality_runtime_state(study_root: str | Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    payloads: dict[str, dict[str, Any] | None] = {}
    refs: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    review_blockers: list[str] = []
    route_back_blockers: list[str] = []

    for surface_key, relative_path in _AUTHORITY_SURFACES.items():
        path = resolved_study_root / relative_path
        payload, read_error = _read_json(path)
        payloads[surface_key] = payload
        refs[surface_key] = _surface_ref(path, payload, read_error)
        if read_error is None:
            continue
        blocker = f"{surface_key}_{read_error}"
        blockers.append(blocker)
        if surface_key == "publication_eval":
            review_blockers.append(blocker)
        else:
            route_back_blockers.append(blocker)

    readiness = payloads["pre_draft_readiness"]
    if readiness is not None:
        before = len(blockers)
        _append_readiness_blockers(readiness, blockers)
        route_back_blockers.extend(blockers[before:])

    for surface_key in ("evidence_ledger", "review_ledger"):
        payload = payloads[surface_key]
        if payload is None:
            continue
        before = len(blockers)
        _append_closed_surface_blocker(payload=payload, surface_key=surface_key, blockers=blockers)
        route_back_blockers.extend(blockers[before:])

    blueprint = payloads["medical_manuscript_blueprint"]
    if blueprint is not None:
        before = len(blockers)
        _append_optional_closed_surface_blocker(
            payload=blueprint,
            surface_key="medical_manuscript_blueprint",
            blockers=blockers,
        )
        if not _blueprint_authorized(blueprint):
            blockers.append("medical_manuscript_blueprint_ai_authority_missing")
        route_back_blockers.extend(blockers[before:])

    publication_eval = payloads["publication_eval"]
    reviewer_os_errors: list[str] = []
    if publication_eval is not None:
        before = len(blockers)
        if not _publication_eval_not_blocked(publication_eval):
            blockers.append("publication_eval_not_clear")
        _ai_backed, ai_blockers = _publication_eval_ai_reviewer_backed(publication_eval)
        reviewer_os_errors = [
            item.removeprefix("publication_eval_reviewer_operating_system_invalid:")
            for item in ai_blockers
            if item.startswith("publication_eval_reviewer_operating_system_invalid:")
        ]
        blockers.extend(ai_blockers)
        review_blockers.extend(blockers[before:])

    if review_blockers:
        status = "review_required"
    elif route_back_blockers:
        status = "route_back_required"
    else:
        status = "first_full_draft_ready"

    return {
        "surface": _SURFACE,
        "schema_version": _SCHEMA_VERSION,
        "study_root": str(resolved_study_root),
        "readiness": {
            "required_before": "first_full_draft",
            "draft_ready": status == "first_full_draft_ready",
            "next_route": "first_full_draft" if status == "first_full_draft_ready" else status,
            "mechanical_file_presence_can_authorize_ready": False,
        },
        "status": status,
        "blockers": blockers,
        "route_back": _route_back_for_status(status, blockers),
        "refs": refs,
        "authority": {
            "source_contract": build_quality_os_runtime_materialization_contract(),
            "assessment_provenance": _provenance_summary(publication_eval),
            "reviewer_operating_system_valid": publication_eval is not None and not reviewer_os_errors,
            "reviewer_operating_system_errors": reviewer_os_errors,
            "mechanical_file_presence_can_authorize_ready": False,
            "mechanical_projection_can_authorize_ready": False,
        },
    }
