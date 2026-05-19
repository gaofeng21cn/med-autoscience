from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers import provenance_limited_harmonization_owner_result
from med_autoscience.controllers import source_provenance_owner_result
from med_autoscience.profiles import WorkspaceProfile


CURRENT_PACKAGE_FRESHNESS_PROOF_RELATIVE_PATH = Path("artifacts/controller/current_package_freshness/latest.json")
GATE_CLEARING_BATCH_RELATIVE_PATH = Path("artifacts/controller/gate_clearing_batch/latest.json")
PUBLICATION_EVAL_RELATIVE_PATH = Path("artifacts/publication_eval/latest.json")
MEDICAL_MANUSCRIPT_BLUEPRINT_SOURCE_RELATIVE_PATH = Path("paper/medical_manuscript_blueprint_source.json")
ANALYSIS_HARMONIZATION_RESULT_RELATIVE_PATH = Path("artifacts/controller/analysis_harmonization/latest.json")
SOURCE_PROVENANCE_RESULT_RELATIVE_PATH = Path("artifacts/controller/source_provenance/latest.json")
PROVENANCE_LIMITED_HARMONIZATION_RESULT_RELATIVE_PATH = Path(
    "artifacts/controller/provenance_limited_harmonization/latest.json"
)
CONTROLLER_DECISION_RELATIVE_PATH = Path("artifacts/controller_decisions/latest.json")


def required_output_pending(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    current_study: Mapping[str, Any] | None,
) -> bool:
    if action_type == "current_package_freshness_required":
        return current_package_freshness_output_pending(profile=profile, study_id=study_id)
    if action_type == "canonical_paper_inputs_rehydrate_required":
        return canonical_paper_inputs_rehydrate_output_pending(profile=profile, study_id=study_id)
    if action_type == "unit_harmonized_external_validation_rerun":
        return unit_harmonized_external_validation_output_pending(profile=profile, study_id=study_id)
    if action_type == "recover_transport_model_provenance":
        return transport_model_provenance_output_pending(profile=profile, study_id=study_id)
    if action_type == "methodology_reframe_route_decision":
        return methodology_reframe_route_decision_output_pending(profile=profile, study_id=study_id)
    if action_type == "provenance_limited_harmonization_audit":
        return provenance_limited_harmonization_audit_output_pending(profile=profile, study_id=study_id)
    if action_type != "return_to_ai_reviewer_workflow":
        return False
    return ai_reviewer_output_pending(current_study)


def ai_reviewer_output_pending(current_study: Mapping[str, Any] | None) -> bool:
    assessment = _mapping(_mapping(current_study).get("ai_reviewer_assessment"))
    return assessment.get("missing") is True


def current_package_freshness_output_pending(*, profile: WorkspaceProfile, study_id: str) -> bool:
    study_root = profile.studies_root / study_id
    current_eval_id = _text(_mapping(_read_json_object(study_root / PUBLICATION_EVAL_RELATIVE_PATH)).get("eval_id"))
    batch = _read_json_object(study_root / GATE_CLEARING_BATCH_RELATIVE_PATH)
    if _source_eval_id_stale(batch, current_eval_id=current_eval_id):
        return True
    if _gate_clearing_batch_still_pending(batch):
        return True
    proof = _read_json_object(study_root / CURRENT_PACKAGE_FRESHNESS_PROOF_RELATIVE_PATH)
    if proof is None:
        return True
    if _source_eval_id_stale(proof, current_eval_id=current_eval_id):
        return True
    return _text(proof.get("status")) not in {"fresh", "current"}


def canonical_paper_inputs_rehydrate_output_pending(*, profile: WorkspaceProfile, study_id: str) -> bool:
    return not (profile.studies_root / study_id / MEDICAL_MANUSCRIPT_BLUEPRINT_SOURCE_RELATIVE_PATH).is_file()


def unit_harmonized_external_validation_output_pending(*, profile: WorkspaceProfile, study_id: str) -> bool:
    payload = _read_json_object(profile.studies_root / study_id / ANALYSIS_HARMONIZATION_RESULT_RELATIVE_PATH)
    return analysis_harmonization_owner_result.output_pending_for_result(payload)


def transport_model_provenance_output_pending(*, profile: WorkspaceProfile, study_id: str) -> bool:
    payload = _read_json_object(profile.studies_root / study_id / SOURCE_PROVENANCE_RESULT_RELATIVE_PATH)
    return source_provenance_owner_result.output_pending_for_result(payload)


def provenance_limited_harmonization_audit_output_pending(*, profile: WorkspaceProfile, study_id: str) -> bool:
    payload = _read_json_object(profile.studies_root / study_id / PROVENANCE_LIMITED_HARMONIZATION_RESULT_RELATIVE_PATH)
    return provenance_limited_harmonization_owner_result.output_pending_for_result(payload)


def methodology_reframe_route_decision_output_pending(*, profile: WorkspaceProfile, study_id: str) -> bool:
    payload = _read_json_object(profile.studies_root / study_id / CONTROLLER_DECISION_RELATIVE_PATH)
    if not payload:
        return True
    return not (
        _text(payload.get("decision_type")) in {"route_back_same_line", "bounded_analysis", "stop_loss"}
        and _text(payload.get("work_unit_fingerprint")) == "decision::methodology_reframe_route_decision"
        and _text(_mapping(payload.get("next_work_unit")).get("unit_id"))
        == "provenance_limited_harmonization_audit"
    )


def _source_eval_id_stale(payload: Mapping[str, Any] | None, *, current_eval_id: str | None) -> bool:
    if current_eval_id is None:
        return False
    source_eval_id = _text(_mapping(payload).get("source_eval_id"))
    return source_eval_id is not None and source_eval_id != current_eval_id


def _gate_clearing_batch_still_pending(batch: Mapping[str, Any] | None) -> bool:
    payload = _mapping(batch)
    if not payload:
        return False
    for unit in _list(payload.get("unit_results")):
        status = _text(_mapping(unit).get("status"))
        if status in {"failed", "control_plane_route_blocked", "missing", "skipped_failed_dependency"}:
            return True
    replay = _mapping(payload.get("gate_replay"))
    if _text(replay.get("status")) == "blocked" and _list(replay.get("blockers")):
        return True
    return False


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


def _list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


__all__ = [
    "MEDICAL_MANUSCRIPT_BLUEPRINT_SOURCE_RELATIVE_PATH",
    "PUBLICATION_EVAL_RELATIVE_PATH",
    "ANALYSIS_HARMONIZATION_RESULT_RELATIVE_PATH",
    "CONTROLLER_DECISION_RELATIVE_PATH",
    "PROVENANCE_LIMITED_HARMONIZATION_RESULT_RELATIVE_PATH",
    "SOURCE_PROVENANCE_RESULT_RELATIVE_PATH",
    "ai_reviewer_output_pending",
    "canonical_paper_inputs_rehydrate_output_pending",
    "current_package_freshness_output_pending",
    "methodology_reframe_route_decision_output_pending",
    "provenance_limited_harmonization_audit_output_pending",
    "required_output_pending",
    "transport_model_provenance_output_pending",
    "unit_harmonized_external_validation_output_pending",
]
