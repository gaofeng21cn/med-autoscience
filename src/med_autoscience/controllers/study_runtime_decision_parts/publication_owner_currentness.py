from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers import paper_authority_migration
from med_autoscience.controllers import publication_work_units
from med_autoscience.publication_eval_latest import stable_publication_eval_latest_path
from med_autoscience.publication_eval_specificity_targets import specificity_target_status


def _normalized_path_text(value: object) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return str(Path(text).expanduser().resolve())
    except (OSError, RuntimeError):
        return text


def _publication_eval_work_unit_fingerprints(payload: dict[str, object]) -> set[str]:
    fingerprints: set[str] = set()
    actions = payload.get("recommended_actions")
    if not isinstance(actions, list):
        return fingerprints
    for action in actions:
        if not isinstance(action, dict):
            continue
        text = str(action.get("work_unit_fingerprint") or "").strip()
        if text:
            fingerprints.add(text)
    return fingerprints


def _publication_eval_specificity_targets_complete(payload: dict[str, object]) -> bool:
    actions = payload.get("recommended_actions")
    if not isinstance(actions, list):
        return False
    for action in actions:
        if not isinstance(action, dict):
            continue
        if specificity_target_status(action.get("specificity_targets")).get("complete") is True:
            return True
    return False


def _publication_eval_action_types(payload: dict[str, object]) -> set[str]:
    action_types: set[str] = set()
    actions = payload.get("recommended_actions")
    if not isinstance(actions, list):
        return action_types
    for action in actions:
        if not isinstance(action, dict):
            continue
        text = str(action.get("action_type") or "").strip()
        if text:
            action_types.add(text)
    return action_types


def _current_medical_prose_route_back(payload: dict[str, object]) -> bool:
    reviewer_os = payload.get("reviewer_operating_system")
    if not isinstance(reviewer_os, dict):
        return False
    currentness = reviewer_os.get("currentness_checks")
    if not isinstance(currentness, dict):
        return False
    prose = currentness.get("medical_prose_review")
    if not isinstance(prose, dict):
        return False
    if str(prose.get("status") or "").strip() != "current":
        return False
    if prose.get("route_back_required") is not True:
        return False
    for field in ("request_digest", "manuscript_ref", "manuscript_digest"):
        if not str(prose.get(field) or "").strip():
            return False
    route_target = str(prose.get("route_target") or "").strip()
    if route_target and route_target != "write":
        return False
    actions = payload.get("recommended_actions")
    if not isinstance(actions, list):
        return False
    return any(
        isinstance(action, dict)
        and str(action.get("action_type") or "").strip() == "route_back_same_line"
        and str(action.get("route_target") or "").strip() == "write"
        for action in actions
    )


def _publication_eval_verdict(payload: dict[str, object]) -> str | None:
    verdict = payload.get("verdict")
    if not isinstance(verdict, dict):
        return None
    text = str(verdict.get("overall_verdict") or "").strip()
    return text or None


def _ai_reviewer_eval_matches_clear_gate(
    payload: dict[str, object],
    *,
    gate_required_action: str,
) -> bool:
    verdict = _publication_eval_verdict(payload)
    if verdict in {"blocked", "rejected", "stop_loss"}:
        return False
    action_types = _publication_eval_action_types(payload)
    if gate_required_action == "continue_write_stage":
        return bool(action_types & {"bounded_analysis", "continue_same_line"})
    if gate_required_action in {"continue_bundle_stage", "complete_bundle_stage"}:
        return bool(action_types & {"continue_same_line", "prepare_promotion_review"})
    return bool(action_types - {"route_back_same_line", "return_to_controller", "stop_loss"})


def _report_work_unit_fingerprint(publication_gate_report: dict[str, object]) -> str | None:
    try:
        work_unit_payload = publication_work_units.derive_publication_work_units(publication_gate_report)
    except (TypeError, ValueError):
        return None
    text = str(work_unit_payload.get("fingerprint") or "").strip()
    return text or None


def _current_ai_reviewer_publication_eval_ref(
    *,
    study_root: Path,
    study_id: str,
    resolved_quest_id: str,
    publication_gate_report: dict[str, object],
) -> dict[str, str] | None:
    force_specificity_refresh = publication_gate_report.get("force_publication_gate_specificity_refresh") is True
    gate_required_action = str(publication_gate_report.get("current_required_action") or "").strip()
    gate_supervisor_phase = str(publication_gate_report.get("supervisor_phase") or "").strip()
    gate_status = str(publication_gate_report.get("status") or "").strip()
    gate_blockers = [
        str(item).strip()
        for item in (publication_gate_report.get("blockers") or [])
        if str(item).strip()
    ]
    gate_blocks_current_owner = gate_required_action == "return_to_publishability_gate" or (
        gate_supervisor_phase == "publishability_gate_blocked" and gate_status == "blocked"
    )
    latest_path = stable_publication_eval_latest_path(study_root=study_root)
    if not latest_path.exists():
        return None
    try:
        payload = json.loads(latest_path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    if str(payload.get("study_id") or "").strip() != study_id:
        return None
    if str(payload.get("quest_id") or "").strip() != resolved_quest_id:
        return None
    provenance = payload.get("assessment_provenance")
    if not isinstance(provenance, dict):
        return None
    if str(provenance.get("owner") or "").strip() != "ai_reviewer":
        return None
    if provenance.get("ai_reviewer_required") is not False:
        return None
    quality_assessment = payload.get("quality_assessment")
    if not isinstance(quality_assessment, dict) or not isinstance(
        quality_assessment.get("medical_journal_prose_quality"),
        dict,
    ):
        return None
    if paper_authority_migration.new_mas_authority_eval_current(study_root=study_root):
        eval_id = str(payload.get("eval_id") or "").strip()
        return {"eval_id": eval_id, "artifact_path": str(latest_path)} if eval_id else None
    if force_specificity_refresh and _publication_eval_verdict(payload) == "blocked":
        action_types = _publication_eval_action_types(payload)
        if action_types <= {"return_to_controller"}:
            eval_id = str(payload.get("eval_id") or "").strip()
            return {"eval_id": eval_id, "artifact_path": str(latest_path)} if eval_id else None
        return None
    if (
        gate_status == "clear"
        and gate_required_action in {
            "continue_write_stage",
            "continue_bundle_stage",
            "complete_bundle_stage",
            "prepare_promotion_review",
        }
        and _current_medical_prose_route_back(payload)
    ):
        eval_id = str(payload.get("eval_id") or "").strip()
        return {"eval_id": eval_id, "artifact_path": str(latest_path)} if eval_id else None
    eval_paper_root = None
    gate_paper_root = None
    delivery_context_refs = payload.get("delivery_context_refs")
    if isinstance(delivery_context_refs, dict):
        eval_paper_root = _normalized_path_text(delivery_context_refs.get("paper_root_ref"))
        gate_paper_root = _normalized_path_text(publication_gate_report.get("paper_root"))
    if (
        eval_paper_root is not None
        and gate_paper_root is not None
        and eval_paper_root != gate_paper_root
    ):
        return None
    if gate_status == "clear" and gate_required_action in {
        "continue_write_stage",
        "continue_bundle_stage",
        "complete_bundle_stage",
        "prepare_promotion_review",
    }:
        if not _ai_reviewer_eval_matches_clear_gate(payload, gate_required_action=gate_required_action):
            return None
    if gate_status == "blocked" and gate_blockers and (
        gate_blocks_current_owner
        or (
            gate_required_action in {"complete_bundle_stage", "continue_bundle_stage"}
            and gate_supervisor_phase == "bundle_stage_blocked"
        )
    ):
        gate_fingerprint = _report_work_unit_fingerprint(publication_gate_report)
        eval_fingerprints = _publication_eval_work_unit_fingerprints(payload)
        if gate_fingerprint is None or gate_fingerprint not in eval_fingerprints:
            return None
        if not _publication_eval_specificity_targets_complete(payload):
            return None
        if not str(payload.get("emitted_at") or "").strip():
            return None
    eval_id = str(payload.get("eval_id") or "").strip()
    if not eval_id:
        return None
    return {"eval_id": eval_id, "artifact_path": str(latest_path)}


__all__ = [name for name in globals() if not name.startswith("__")]
