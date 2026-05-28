from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import ai_reviewer_publication_eval_records
from med_autoscience.controllers.owner_route_reconcile_parts import ai_reviewer_actions
from med_autoscience.publication_eval_reviewer_os import current_ai_reviewer_route_back_action


def record_production_transition_action(
    *,
    status: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    transition = _mapping(status.get("domain_transition"))
    if _text(transition.get("decision_type")) != "ai_reviewer_re_eval":
        return None
    next_work_unit = _mapping(transition.get("next_work_unit"))
    work_unit_id = _text(next_work_unit.get("unit_id"))
    reason = record_production_reason_for_work_unit(work_unit_id)
    if reason is None:
        return None
    if current_ai_reviewer_eval_consumes_record_production(
        ai_reviewer_assessment=ai_reviewer_assessment,
        publication_eval_payload=publication_eval_payload,
        reason=reason,
    ):
        return None
    action = ai_reviewer_actions.ai_reviewer_required_action(reason=reason)
    action["summary"] = (
        "Produce a current AI reviewer publication-eval record before refreshing "
        "publication_eval/latest.json."
    )
    action["required_output_surface"] = "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    action["next_work_unit"] = work_unit_id
    action["executable_work_unit"] = work_unit_id
    action["controller_work_unit_id"] = work_unit_id
    action["domain_transition_decision_type"] = "ai_reviewer_re_eval"
    action["controller_next_work_unit"] = next_work_unit
    action["publication_eval_latest_write_allowed"] = False
    action["controller_decision_write_allowed"] = False
    action["record_only_surface"] = True
    if required_refs := _string_items(ai_reviewer_assessment.get("required_currentness_refs")):
        action["required_currentness_refs"] = required_refs
    if stale_record_ref := _text(ai_reviewer_assessment.get("stale_record_ref")):
        action["stale_record_ref"] = stale_record_ref
    if source_ref := _text(ai_reviewer_assessment.get("source_ref")):
        action["source_ref"] = source_ref
    return action


def current_ai_reviewer_eval_consumes_record_production(
    *,
    ai_reviewer_assessment: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    reason: str,
) -> bool:
    if not current_ai_reviewer_assessment_resolved(ai_reviewer_assessment):
        return False
    provenance = _mapping(publication_eval_payload.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer" or provenance.get("ai_reviewer_required") is not False:
        return False
    reviewer_os = _mapping(publication_eval_payload.get("reviewer_operating_system"))
    currentness = _mapping(reviewer_os.get("currentness_checks"))
    source_eval = _mapping(currentness.get("source_eval"))
    eval_id = _text(publication_eval_payload.get("eval_id"))
    if eval_id is None or _text(source_eval.get("status")) != "current" or _text(source_eval.get("eval_id")) != eval_id:
        return False
    if reason == ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_MANUSCRIPT_REASON:
        current_manuscript = _mapping(currentness.get("current_manuscript"))
        return _text(current_manuscript.get("status")) == "current"
    if reason == ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_INPUTS_REASON:
        required_inputs = ("current_manuscript", "evidence_ledger", "claim_evidence_map")
        return all(_text(_mapping(currentness.get(key)).get("status")) == "current" for key in required_inputs)
    if reason == ai_reviewer_actions.RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN_REASON:
        return _text(currentness.get("analysis_harmonization_status")) == "current" or any(
            "analysis" in key and _text(_mapping(value).get("status")) == "current"
            for key, value in currentness.items()
            if isinstance(key, str)
        )
    return False


def gate_replay_action(
    *,
    ai_reviewer_assessment: Mapping[str, Any],
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not current_ai_reviewer_assessment_resolved(ai_reviewer_assessment):
        return None
    route_back_action = current_ai_reviewer_route_back_action(dict(publication_eval_payload))
    if route_back_action is None:
        return None
    next_work_unit = _mapping(route_back_action.get("next_work_unit"))
    work_unit_id = _text(next_work_unit.get("unit_id"))
    if _text(route_back_action.get("route_target")) != "finalize":
        return None
    if work_unit_id != "owner_authorized_publication_gate_replay":
        return None
    publication_eval_latest_path = Path(study_root).expanduser().resolve() / "artifacts" / "publication_eval" / "latest.json"
    eval_id = _text(publication_eval_payload.get("eval_id"))
    controller_route = {
        "decision_path": None,
        "decision_id": None,
        "controller_actions": ["run_gate_clearing_batch"],
        "route_target": "finalize",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
        "publication_eval_id": eval_id,
        "publication_eval_ref": {
            "eval_id": eval_id,
            "artifact_path": ai_reviewer_publication_eval_records.projection_source_ref(
                publication_eval_payload,
                publication_eval_latest_path,
            ),
        },
        "next_work_unit": dict(next_work_unit),
        "source": "owner_route_reconcile_current_ai_reviewer_gate_replay",
        "authorization_basis": "ai_reviewer_current_finalize_gate_replay",
    }
    return {
        "action_type": "run_gate_clearing_batch",
        "authority": "observability_only",
        "owner": "gate_clearing_batch",
        "request_owner": "gate_clearing_batch",
        "recommended_owner": "gate_clearing_batch",
        "reason": work_unit_id,
        "summary": "The current AI reviewer record routes publication-gate replay to the finalize owner.",
        "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
        "route_target": "finalize",
        "next_work_unit": work_unit_id,
        "executable_work_unit": work_unit_id,
        "controller_work_unit_id": work_unit_id,
        "controller_next_work_unit": dict(next_work_unit),
        "controller_action": "run_gate_clearing_batch",
        "controller_route": controller_route,
        "domain_transition_decision_type": "route_back_same_line",
        "original_route_target": "finalize",
        "work_unit_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
        "source_eval_id": eval_id,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def current_ai_reviewer_assessment_resolved(ai_reviewer_assessment: Mapping[str, Any]) -> bool:
    return (
        ai_reviewer_assessment.get("present") is True
        and ai_reviewer_assessment.get("missing") is not True
        and _text(ai_reviewer_assessment.get("blocked_reason")) is None
    )


def record_production_reason_for_work_unit(work_unit_id: str | None) -> str | None:
    if work_unit_id == "produce_ai_reviewer_publication_eval_record_against_current_manuscript":
        return ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_MANUSCRIPT_REASON
    if work_unit_id == "produce_ai_reviewer_publication_eval_record_against_current_inputs":
        return ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_INPUTS_REASON
    if work_unit_id == "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization":
        return ai_reviewer_actions.RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN_REASON
    return None


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
    "gate_replay_action",
    "record_production_reason_for_work_unit",
    "record_production_transition_action",
]
