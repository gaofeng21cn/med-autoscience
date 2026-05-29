from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import ai_reviewer_owner_output_consumption
from med_autoscience.controllers.owner_route_reconcile_parts import ai_reviewer_actions
from med_autoscience.controllers.owner_route_reconcile_parts import claim_evidence_alignment_actions
from med_autoscience.controllers.owner_route_reconcile_parts import current_truth_owner
from med_autoscience.controllers.owner_route_reconcile_parts import story_surface_delta_actions


REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH = Path("artifacts/controller/repair_execution_evidence/latest.json")


def pre_write_route_action(
    *,
    ai_reviewer_assessment: Mapping[str, Any],
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    digest_mismatch_route = current_truth_owner.current_manuscript_digest_mismatch_ai_reviewer_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if digest_mismatch_route is not None:
        return ai_reviewer_owner_output_consumption.current_manuscript_digest_mismatch_action(
            digest_mismatch_route
        )
    claim_alignment_action = claim_evidence_alignment_actions.action_from_ai_reviewer_alignment_blocker(
        study_root=study_root,
    )
    if claim_alignment_action is not None:
        return claim_alignment_action
    if _explicit_ai_reviewer_request_pending(
        ai_reviewer_assessment
    ) and _pending_ai_reviewer_recheck_consumes_current_write_routeback(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return ai_reviewer_actions.ai_reviewer_required_action(
            reason=_text(ai_reviewer_assessment.get("blocked_reason")) or "ai_reviewer_assessment_required"
        )
    return None


def current_ai_reviewer_write_routeback_action(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    controller_route = current_truth_owner.current_ai_reviewer_write_routeback_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if controller_route is None:
        return None
    return story_surface_delta_actions.write_owner_action_from_controller_route(controller_route)


def _explicit_ai_reviewer_request_pending(ai_reviewer_assessment: Mapping[str, Any]) -> bool:
    return (
        ai_reviewer_assessment.get("missing") is True
        and _text(ai_reviewer_assessment.get("request_state")) in {"requested", "assigned"}
    )


def _pending_ai_reviewer_recheck_consumes_current_write_routeback(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> bool:
    action = story_surface_delta_actions.write_owner_action(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if action is None:
        return False
    expected_eval_id = _text(publication_eval_payload.get("eval_id"))
    expected_work_unit = _text(action.get("controller_work_unit_id")) or _text(action.get("next_work_unit"))
    if expected_eval_id is None or expected_work_unit is None:
        return False
    resolved_study_root = Path(study_root).expanduser().resolve()
    evidence = _read_json_object(resolved_study_root / REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH)
    if evidence is None:
        return False
    if _text(evidence.get("status")) not in {"progress_delta_candidate", "controller_progress_delta_candidate"}:
        return False
    if evidence.get("ai_reviewer_recheck_required") is not True:
        return False
    if evidence.get("ai_reviewer_recheck_done") is not True:
        return False
    if _string_items(evidence.get("blockers")):
        return False
    source_eval_id = _text(evidence.get("source_eval_id")) or _text(
        _mapping(evidence.get("review_finding")).get("source_eval_id")
    )
    if source_eval_id != expected_eval_id:
        return False
    repair_work_unit = _mapping(evidence.get("repair_work_unit"))
    if _text(repair_work_unit.get("unit_id")) != expected_work_unit:
        return False
    recheck_ref = _text(evidence.get("ai_reviewer_recheck_request_ref"))
    if recheck_ref is None:
        return False
    recheck_path = Path(recheck_ref).expanduser()
    if not recheck_path.is_absolute():
        recheck_path = resolved_study_root / recheck_path
    request = _read_json_object(recheck_path)
    if request is None:
        return False
    if _text(request.get("request_kind")) != "return_to_ai_reviewer_workflow":
        return False
    if _text(request.get("request_owner")) not in {None, "ai_reviewer"}:
        return False
    return _text(_mapping(request.get("request_lifecycle")).get("state")) in {"requested", "assigned"}


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


__all__ = [
    "current_ai_reviewer_write_routeback_action",
    "pre_write_route_action",
]
