from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import ai_reviewer_publication_eval_records
from med_autoscience.controllers.story_surface_work_units import (
    is_story_surface_delta_write_work_unit,
)


QUALITY_REPAIR_BATCH_RELATIVE_PATH = Path("artifacts/controller/quality_repair_batch/latest.json")
BLOCKED_REASON = "manuscript_story_surface_delta_missing"


def current_quality_repair_writer_handoff_route(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    batch_path = resolved_study_root / QUALITY_REPAIR_BATCH_RELATIVE_PATH
    batch = _read_json_object(batch_path)
    if batch is None:
        return None
    source_eval_id = _text(batch.get("source_eval_id"))
    current_eval_id = _text(publication_eval_payload.get("eval_id"))
    if source_eval_id is None or source_eval_id != current_eval_id:
        return None
    if _text(batch.get("status")) != "handoff_ready":
        return None
    if _text(batch.get("next_owner")) != "write":
        return None
    handoff = _mapping(batch.get("writer_worker_handoff"))
    if _text(handoff.get("surface")) != "default_executor_dispatch_request":
        return None
    if _text(handoff.get("dispatch_status")) != "ready":
        return None
    if _text(handoff.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return None
    if _text(handoff.get("action_type")) != "run_quality_repair_batch":
        return None
    if _text(handoff.get("next_executable_owner")) != "write":
        return None
    source_action = _mapping(handoff.get("source_action"))
    if _text(source_action.get("surface")) != "quality_repair_batch":
        return None
    if _text(source_action.get("blocked_reason")) != BLOCKED_REASON:
        return None
    if _text(source_action.get("source_eval_id")) not in {None, source_eval_id}:
        return None
    route = _mapping(handoff.get("owner_route"))
    if _text(route.get("next_owner")) != "write":
        return None
    if _text(route.get("owner_reason")) != BLOCKED_REASON:
        return None
    if "run_quality_repair_batch" not in _string_set(route.get("allowed_actions")):
        return None
    repair_evidence = _writer_handoff_repair_evidence(
        handoff=handoff,
        source_action=source_action,
        batch=batch,
        study_root=resolved_study_root,
    )
    if not _repair_evidence_has_story_surface_delta_blocker(
        repair_evidence,
        source_eval_id=source_eval_id,
    ):
        return None
    work_unit_id = _writer_handoff_work_unit_id(
        handoff=handoff,
        route=route,
        repair_evidence=repair_evidence,
    )
    if not is_story_surface_delta_write_work_unit(work_unit_id):
        return None
    publication_eval_latest_path = resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
    return {
        "decision_path": None,
        "decision_id": None,
        "controller_actions": ["run_quality_repair_batch"],
        "route_target": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": _text(route.get("work_unit_fingerprint")),
        "publication_eval_id": source_eval_id,
        "publication_eval_ref": {
            "eval_id": source_eval_id,
            "artifact_path": _text(_mapping(handoff.get("refs")).get("source_eval_path"))
            or ai_reviewer_publication_eval_records.projection_source_ref(
                publication_eval_payload,
                publication_eval_latest_path.resolve(),
            ),
        },
        "next_work_unit": {
            "unit_id": work_unit_id,
            "lane": "write",
            "summary": "Repair canonical manuscript story surfaces or emit the typed story-surface blocker.",
        },
        "blocking_work_units": [
            {
                "unit_id": work_unit_id,
                "lane": "write",
            }
        ],
        "quality_repair_batch_path": str(batch_path),
        "repair_execution_evidence_path": _text(_mapping(handoff.get("refs")).get("repair_execution_evidence_path"))
        or _text(source_action.get("repair_execution_evidence_ref")),
        "source": "owner_route_reconcile_quality_repair_writer_handoff",
        "authorization_basis": "quality_repair_writer_handoff",
        "source_eval_id": source_eval_id,
        "owner_route": dict(route),
    }


def _writer_handoff_repair_evidence(
    *,
    handoff: Mapping[str, Any],
    source_action: Mapping[str, Any],
    batch: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    refs = _mapping(handoff.get("refs"))
    evidence_ref = _text(refs.get("repair_execution_evidence_path")) or _text(
        source_action.get("repair_execution_evidence_ref")
    )
    if evidence_ref:
        evidence_path = Path(evidence_ref).expanduser()
        if not evidence_path.is_absolute():
            evidence_path = study_root / evidence_path
        evidence = _read_json_object(evidence_path)
        if evidence is not None:
            return evidence
    return _mapping(batch.get("repair_execution_evidence"))


def _repair_evidence_has_story_surface_delta_blocker(
    repair_evidence: Mapping[str, Any],
    *,
    source_eval_id: str,
) -> bool:
    if _text(repair_evidence.get("status")) != "blocked":
        return False
    evidence_source_eval_id = _text(repair_evidence.get("source_eval_id")) or _text(
        _mapping(repair_evidence.get("review_finding")).get("source_eval_id")
    )
    if evidence_source_eval_id is not None and evidence_source_eval_id != source_eval_id:
        return False
    blockers = _string_set(repair_evidence.get("blockers"))
    if BLOCKED_REASON in blockers:
        return True
    hygiene = _mapping(repair_evidence.get("manuscript_surface_hygiene"))
    hygiene_blockers = _string_set(hygiene.get("blockers"))
    if BLOCKED_REASON in hygiene_blockers:
        return True
    artifact_delta = _mapping(repair_evidence.get("canonical_artifact_delta"))
    return (
        _text(artifact_delta.get("status")) == "blocked"
        and artifact_delta.get("meaningful_artifact_delta") is False
        and BLOCKED_REASON in blockers
    )


def _writer_handoff_work_unit_id(
    *,
    handoff: Mapping[str, Any],
    route: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
) -> str | None:
    source_action = _mapping(handoff.get("source_action"))
    source_next_work_unit = _mapping(source_action.get("next_work_unit"))
    route_refs = _mapping(route.get("source_refs"))
    route_basis = _mapping(route_refs.get("owner_route_currentness_basis"))
    repair_work_unit = _mapping(repair_evidence.get("repair_work_unit"))
    return (
        _text(source_next_work_unit.get("unit_id"))
        or _text(route_refs.get("work_unit_id"))
        or _text(route_basis.get("work_unit_id"))
        or _text(repair_work_unit.get("unit_id"))
    )


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_set(value: object) -> set[str]:
    if isinstance(value, str):
        item = value.strip()
        return {item} if item else set()
    if not isinstance(value, list | tuple | set):
        return set()
    return {text for item in value if (text := _text(item)) is not None}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["current_quality_repair_writer_handoff_route"]
