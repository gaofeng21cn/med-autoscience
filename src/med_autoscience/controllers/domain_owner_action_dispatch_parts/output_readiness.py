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
MEDICAL_PROSE_REVIEW_RELATIVE_PATH = Path("artifacts/publication_eval/medical_prose_review.json")
AI_REVIEWER_REQUEST_RELATIVE_PATH = Path("artifacts/supervision/requests/ai_reviewer/latest.json")
MEDICAL_MANUSCRIPT_BLUEPRINT_SOURCE_RELATIVE_PATH = Path("paper/medical_manuscript_blueprint_source.json")
ANALYSIS_HARMONIZATION_RESULT_RELATIVE_PATH = Path("artifacts/controller/analysis_harmonization/latest.json")
SOURCE_PROVENANCE_RESULT_RELATIVE_PATH = Path("artifacts/controller/source_provenance/latest.json")
PROVENANCE_LIMITED_HARMONIZATION_RESULT_RELATIVE_PATH = Path(
    "artifacts/controller/provenance_limited_harmonization/latest.json"
)
CONTROLLER_DECISION_RELATIVE_PATH = Path("artifacts/controller_decisions/latest.json")
_ROUTE_TARGET_ALIASES = {
    "analysis": "analysis-campaign",
    "analysis_campaign": "analysis-campaign",
    "bounded_analysis": "analysis-campaign",
}
_AI_REVIEWER_ROUTE_BACK_TARGETS = frozenset({"write", "analysis-campaign", "blueprint"})
_ROUTE_BACK_ACTION_TYPES = frozenset({"route_back_same_line", "bounded_analysis", "stop_loss"})


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
    return ai_reviewer_output_pending(
        current_study,
        profile=profile,
        study_id=study_id,
    )


def ai_reviewer_output_pending(
    current_study: Mapping[str, Any] | None,
    *,
    profile: WorkspaceProfile | None = None,
    study_id: str | None = None,
) -> bool:
    assessment = _mapping(_mapping(current_study).get("ai_reviewer_assessment"))
    if assessment.get("missing") is True:
        return True
    if profile is None or study_id is None:
        return False
    return ai_reviewer_study_output_pending(profile=profile, study_id=study_id)


def ai_reviewer_study_output_pending(*, profile: WorkspaceProfile, study_id: str) -> bool:
    study_root = profile.studies_root / study_id
    latest = _read_json_object(study_root / PUBLICATION_EVAL_RELATIVE_PATH)
    if _request_record_newer_than_latest(study_root=study_root, latest=latest):
        return True
    return _current_medical_prose_route_back_unconsumed(study_root=study_root, latest=latest)


def _request_record_newer_than_latest(*, study_root: Path, latest: Mapping[str, Any] | None) -> bool:
    request = _read_json_object(study_root / AI_REVIEWER_REQUEST_RELATIVE_PATH)
    record = _mapping(_mapping(request).get("ai_reviewer_record"))
    request_eval_id = _text(record.get("eval_id"))
    if request_eval_id is None:
        return False
    return _text(_mapping(latest).get("eval_id")) != request_eval_id


def _current_medical_prose_route_back_unconsumed(*, study_root: Path, latest: Mapping[str, Any] | None) -> bool:
    prose = _read_json_object(study_root / MEDICAL_PROSE_REVIEW_RELATIVE_PATH)
    quality = _mapping(_mapping(prose).get("medical_journal_prose_quality"))
    route_back = _mapping(quality.get("route_back_recommendation"))
    if route_back.get("required") is not True:
        return False
    route_target = _normalized_route_target(route_back.get("route_target"))
    if route_target not in _AI_REVIEWER_ROUTE_BACK_TARGETS:
        return False
    if latest is None:
        return True
    current_provenance = _mapping(_mapping(prose).get("assessment_provenance"))
    reviewer_os = _mapping(latest.get("reviewer_operating_system"))
    currentness_checks = _mapping(reviewer_os.get("currentness_checks"))
    latest_prose = _mapping(currentness_checks.get("medical_prose_review"))
    if _text(latest_prose.get("status")) != "current":
        return True
    if latest_prose.get("route_back_required") is not True:
        return True
    if _normalized_route_target(latest_prose.get("route_target")) != route_target:
        return True
    for field in ("request_digest", "manuscript_digest"):
        current_value = _text(current_provenance.get(field))
        if current_value is not None and _text(latest_prose.get(field)) != current_value:
            return True
    current_manuscript_ref = _text(current_provenance.get("manuscript_ref"))
    if current_manuscript_ref is not None and not _refs_match(
        left=_text(latest_prose.get("manuscript_ref")),
        right=current_manuscript_ref,
    ):
        return True
    return not _latest_recommends_same_route_back(latest=latest, route_target=route_target)


def _latest_recommends_same_route_back(*, latest: Mapping[str, Any], route_target: str) -> bool:
    for action in _list(latest.get("recommended_actions")):
        payload = _mapping(action)
        if payload.get("requires_controller_decision") is not True:
            continue
        if _text(payload.get("action_type")) not in _ROUTE_BACK_ACTION_TYPES:
            continue
        if _normalized_route_target(payload.get("route_target")) == route_target:
            return True
    return False


def _normalized_route_target(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    return _ROUTE_TARGET_ALIASES.get(text, text)


def _refs_match(*, left: str | None, right: str) -> bool:
    if left is None:
        return False
    if left == right:
        return True
    try:
        return Path(left).expanduser().resolve() == Path(right).expanduser().resolve()
    except OSError:
        return False


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
    next_work_unit = _mapping(payload.get("next_work_unit"))
    selected_route_option = _text(next_work_unit.get("selected_route_option"))
    unit_id = _text(next_work_unit.get("unit_id"))
    route_selected = (
        selected_route_option == "provenance_limited_harmonization_audit"
        and unit_id == "provenance_limited_harmonization_audit"
    ) or (
        selected_route_option == "rebuild_reproducible_model_route"
        and unit_id == "unit_harmonized_external_validation_rerun"
        and next_work_unit.get("clean_reproducible_model_rebuild_authorized") is True
    )
    return not (
        _text(payload.get("decision_type")) in {"route_back_same_line", "bounded_analysis", "stop_loss"}
        and _text(payload.get("work_unit_fingerprint")) == "decision::methodology_reframe_route_decision"
        and route_selected
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
