from __future__ import annotations

import json
from pathlib import Path

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
    if publication_gate_report.get("force_publication_gate_specificity_refresh") is True:
        return None
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
