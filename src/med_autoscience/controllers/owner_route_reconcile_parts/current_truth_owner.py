from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import publication_work_unit_lifecycle
from med_autoscience.controllers import publication_work_units
from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers import provenance_limited_harmonization_owner_result
from med_autoscience.controllers import ai_reviewer_publication_eval_records
from med_autoscience.controllers.medical_prose_story_surface_parts.eval_bound_currentness import (
    EVAL_BOUND_CURRENT_MANUSCRIPT_DIGEST_MISMATCH_BLOCKER,
)
from med_autoscience.controllers.story_surface_work_units import (
    is_claim_evidence_alignment_write_work_unit,
    is_story_surface_delta_write_work_unit,
)
from med_autoscience.controllers.study_domain_transition_table_parts import ai_reviewer_transitions
from med_autoscience.controllers.current_truth_owner_parts import writer_handoff
from med_autoscience.publication_eval_specificity_targets import specificity_target_status


RUNTIME_CONTROLLER_REDRIVE_REASON = "runtime_controller_redrive_required"
OPL_STAGE_ATTEMPT_ADMISSION_REASON = "opl_stage_attempt_admission_required"
QUALITY_REPAIR_BATCH_RELATIVE_PATH = Path("artifacts/controller/quality_repair_batch/latest.json")
GATE_CLEARING_BATCH_RELATIVE_PATH = Path("artifacts/controller/gate_clearing_batch/latest.json")
SPECIFICITY_WORK_UNIT_IDS = {"gate_needs_specificity", "needs_specificity"}
RUNTIME_REDRIVE_ACTIONS = {
    "request_opl_stage_attempt",
    "request_opl_stage_attempt_relaunch",
    "run_gate_clearing_batch",
    "run_quality_repair_batch",
}
DOMAIN_TRANSITION_ACTIONS_BY_DECISION_TYPE = {
    "ai_reviewer_re_eval": {"return_to_ai_reviewer_workflow"},
    "bundle_stage_finalize": {"request_opl_stage_attempt"},
    "publication_gate_blocker": {"run_gate_clearing_batch"},
    "route_back_same_line": {"run_quality_repair_batch"},
}
METHODOLOGY_REFRAME_DECISION_FINGERPRINT = "decision::methodology_reframe_route_decision"
METHODOLOGY_REFRAME_ANALYSIS_WORK_UNIT = "provenance_limited_harmonization_audit"
METHODOLOGY_REFRAME_REBUILD_WORK_UNIT = "unit_harmonized_external_validation_rerun"


def next_owner_for_reason(reason: str | None) -> str | None:
    if reason in {RUNTIME_CONTROLLER_REDRIVE_REASON, OPL_STAGE_ATTEMPT_ADMISSION_REASON}:
        return "one-person-lab"
    if reason in {
        "runtime_recovery_not_authorized",
        "runtime_recovery_retry_budget_exhausted",
        "runtime_relaunch_no_live_run_started",
    }:
        return "one-person-lab"
    return None


def current_controller_runtime_route(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    decision_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    decision = _read_json_object(decision_path)
    if decision is None or decision.get("requires_human_confirmation") is True:
        return None
    action_types = _controller_action_types(decision)
    work_unit = _mapping(decision.get("next_work_unit"))
    work_unit_id = _text(work_unit.get("unit_id"))
    if work_unit_id is None:
        return None
    decision_fingerprint = _text(decision.get("work_unit_fingerprint")) or _text(work_unit.get("fingerprint"))
    if decision_fingerprint is None:
        return None
    domain_transition_allowed = domain_transition_runtime_route_allowed(
        work_unit_fingerprint=decision_fingerprint,
        action_types=action_types,
        work_unit_id=work_unit_id,
    )
    methodology_reframe_allowed = methodology_reframe_runtime_route_allowed(
        decision=decision,
        work_unit=work_unit,
        work_unit_fingerprint=decision_fingerprint,
        action_types=action_types,
        work_unit_id=work_unit_id,
    )
    if not domain_transition_allowed and not methodology_reframe_allowed:
        if not action_types & RUNTIME_REDRIVE_ACTIONS:
            return None
        publication_fingerprints = _publication_work_unit_fingerprints(publication_eval_payload)
        if decision_fingerprint not in publication_fingerprints:
            return None
    if work_unit_id in SPECIFICITY_WORK_UNIT_IDS and not domain_transition_allowed and not methodology_reframe_allowed:
        if not _publication_eval_specificity_targets_complete_for_fingerprint(
            publication_eval_payload,
            decision_fingerprint=decision_fingerprint,
        ):
            return None
    if _publication_work_unit_closed(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=decision_fingerprint,
    ):
        return None
    if (
        work_unit_id == METHODOLOGY_REFRAME_ANALYSIS_WORK_UNIT
        and provenance_limited_harmonization_owner_result.required_output_satisfied(study_root=study_root)
    ):
        return None
    if (
        work_unit_id == METHODOLOGY_REFRAME_REBUILD_WORK_UNIT
        and analysis_harmonization_owner_result.required_output_satisfied(study_root=study_root)
    ):
        return None
    return {
        "decision_path": str(decision_path),
        "decision_id": _text(decision.get("decision_id")),
        "controller_actions": sorted(action_types),
        "route_target": _text(decision.get("route_target")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": decision_fingerprint,
    }


def current_story_surface_delta_blocker_route(
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
    if source_eval_id is None or source_eval_id != _text(publication_eval_payload.get("eval_id")):
        return None
    if not _story_surface_delta_blocker_present(batch):
        return None
    if _text(batch.get("next_owner")) != "write":
        return None
    action = _publication_story_repair_action(publication_eval_payload)
    if action is None:
        return None
    next_work_unit = _mapping(action.get("next_work_unit"))
    work_unit_id = _text(next_work_unit.get("unit_id"))
    action_route_target = _text(action.get("route_target"))
    gate_batch = _mapping(batch.get("gate_clearing_batch"))
    route = {
        "decision_path": None,
        "decision_id": None,
        "controller_actions": ["run_quality_repair_batch"],
        "route_target": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": _text(action.get("work_unit_fingerprint"))
        or _text(gate_batch.get("work_unit_fingerprint"))
        or _text(gate_batch.get("source_work_unit_fingerprint")),
        "quality_repair_batch_path": str(batch_path),
        "authorization_basis": "quality_repair_story_surface_delta_blocker",
    }
    if action_route_target and action_route_target != "write":
        route["original_route_target"] = action_route_target
    return route


def current_quality_repair_writer_handoff_route(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    return writer_handoff.current_quality_repair_writer_handoff_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )


def current_gate_replay_routeback_route(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    batch_path = resolved_study_root / GATE_CLEARING_BATCH_RELATIVE_PATH
    batch = _read_json_object(batch_path)
    if batch is None:
        return None
    if _text(batch.get("source_eval_id")) != _text(publication_eval_payload.get("eval_id")):
        return None
    gate_report = _gate_replay_report_payload(batch, study_root=resolved_study_root)
    if gate_report is None:
        return None
    if _text(gate_report.get("status")) != "blocked" or gate_report.get("allow_write") is True:
        return None
    batch_work_unit = _mapping(batch.get("current_publication_work_unit"))
    batch_write_route_back = _text(batch_work_unit.get("lane")) == "write"
    work_units = publication_work_units.derive_publication_work_units(gate_report)
    next_work_unit = batch_work_unit if batch_write_route_back else _first_work_unit_for_lane(work_units, lane="write")
    if (
        _text(gate_report.get("medical_publication_surface_route_back_recommendation")) != "return_to_write"
        and not batch_write_route_back
        and next_work_unit is None
    ):
        return None
    if next_work_unit is None:
        return None
    work_unit_id = _text(next_work_unit.get("unit_id"))
    if work_unit_id is None:
        return None
    fingerprint = (
        _text(batch.get("work_unit_fingerprint"))
        or _text(work_units.get("fingerprint"))
        or _text(gate_report.get("gate_fingerprint"))
    )
    source_eval_id = _text(publication_eval_payload.get("eval_id"))
    return {
        "decision_path": None,
        "decision_id": None,
        "controller_actions": ["run_quality_repair_batch"],
        "route_target": "write",
        "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
        "route_rationale": _text(gate_report.get("controller_stage_note")),
        "source_route_key_question": "publication_gate_replay_blocked_route_back",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": f"gate-replay-route-back::write::{fingerprint or work_unit_id}",
        "publication_eval_id": source_eval_id,
        "publication_eval_ref": {
            "eval_id": source_eval_id,
            "artifact_path": ai_reviewer_publication_eval_records.projection_source_ref(
                publication_eval_payload,
                (resolved_study_root / "artifacts" / "publication_eval" / "latest.json").resolve(),
            ),
        },
        "next_work_unit": dict(next_work_unit),
        "blocking_work_units": [
            dict(item)
            for item in work_units.get("blocking_work_units") or []
            if isinstance(item, Mapping)
        ],
        "gate_report_path": _text(_mapping(batch.get("gate_replay")).get("report_json")),
        "gate_clearing_batch_path": str(batch_path),
        "gate_fingerprint": _text(gate_report.get("gate_fingerprint")),
        "gate_blockers": sorted(_string_set(gate_report.get("blockers"))),
        "source": "owner_route_reconcile_gate_replay_routeback",
        "authorization_basis": "gate_replay_route_back",
    }


def current_gate_replay_submission_refresh_route(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    batch_path = resolved_study_root / GATE_CLEARING_BATCH_RELATIVE_PATH
    batch = _read_json_object(batch_path)
    if batch is None:
        return None
    if _text(batch.get("source_eval_id")) != _text(publication_eval_payload.get("eval_id")):
        return None
    gate_report = _gate_replay_report_payload(batch, study_root=resolved_study_root)
    if gate_report is None:
        return None
    if _text(gate_report.get("status")) != "blocked" or gate_report.get("allow_write") is True:
        return None
    batch_work_unit = _mapping(batch.get("current_publication_work_unit"))
    work_unit_id = _text(batch_work_unit.get("unit_id"))
    if work_unit_id != "submission_minimal_refresh":
        return None
    if _text(batch_work_unit.get("lane")) != "finalize":
        return None
    work_units = publication_work_units.derive_publication_work_units(gate_report)
    if _first_work_unit_for_lane(work_units, lane="write") is not None:
        return None
    fingerprint = (
        _text(batch.get("work_unit_fingerprint"))
        or _text(_mapping(batch.get("work_unit_currentness")).get("current_work_unit_fingerprint"))
        or _text(gate_report.get("gate_fingerprint"))
    )
    source_eval_id = _text(publication_eval_payload.get("eval_id"))
    return {
        "decision_path": None,
        "decision_id": None,
        "controller_actions": ["run_gate_clearing_batch"],
        "route_target": "finalize",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": f"gate-replay-route-back::finalize::{fingerprint or work_unit_id}",
        "publication_eval_id": source_eval_id,
        "publication_eval_ref": {
            "eval_id": source_eval_id,
            "artifact_path": ai_reviewer_publication_eval_records.projection_source_ref(
                publication_eval_payload,
                (resolved_study_root / "artifacts" / "publication_eval" / "latest.json").resolve(),
            ),
        },
        "next_work_unit": dict(batch_work_unit),
        "gate_report_path": _text(_mapping(batch.get("gate_replay")).get("report_json")),
        "gate_clearing_batch_path": str(batch_path),
        "gate_fingerprint": _text(gate_report.get("gate_fingerprint")),
        "gate_blockers": sorted(_string_set(gate_report.get("blockers"))),
        "source": "owner_route_reconcile_gate_replay_submission_refresh",
        "authorization_basis": "gate_replay_submission_minimal_refresh",
    }


def current_manuscript_digest_mismatch_ai_reviewer_route(
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
    if source_eval_id is None or source_eval_id != _text(publication_eval_payload.get("eval_id")):
        return None
    blocker = _current_manuscript_digest_mismatch_blocker(batch)
    if blocker is None:
        return None
    if _current_ai_reviewer_eval_consumes_digest_mismatch(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
        blocker=blocker,
    ):
        return None
    action = _publication_story_repair_action(publication_eval_payload)
    next_work_unit = _mapping(action.get("next_work_unit")) if action is not None else {}
    blocker_work_unit_id = _text(blocker.get("work_unit_id"))
    work_unit_id = blocker_work_unit_id or _text(next_work_unit.get("unit_id"))
    publication_eval_latest_path = resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
    stale_record_ref = _text(batch.get("source_eval_artifact_path")) or ai_reviewer_publication_eval_records.projection_source_ref(
        publication_eval_payload,
        publication_eval_latest_path,
    )
    return {
        "decision_path": None,
        "decision_id": None,
        "controller_actions": ["return_to_ai_reviewer_workflow"],
        "route_target": "review",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": _text(action.get("work_unit_fingerprint")) if action is not None else None,
        "publication_eval_id": source_eval_id,
        "publication_eval_ref": {
            "eval_id": source_eval_id,
            "artifact_path": stale_record_ref,
        },
        "quality_repair_batch_path": str(batch_path),
        "authorization_basis": "quality_repair_current_manuscript_digest_mismatch",
        "blocked_reason": EVAL_BOUND_CURRENT_MANUSCRIPT_DIGEST_MISMATCH_BLOCKER,
        "stale_record_ref": stale_record_ref,
        "source_ref": str(batch_path),
        "required_currentness_refs": _current_story_surface_refs(blocker),
        "reviewer_manuscript_ref": _text(blocker.get("reviewer_manuscript_ref")),
        "reviewer_manuscript_digest": _text(blocker.get("reviewer_manuscript_digest")),
        "story_surface_digests": [
            dict(item)
            for item in blocker.get("story_surface_digests") or []
            if isinstance(item, Mapping)
        ],
    }


def current_ai_reviewer_write_routeback_route(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    if ai_reviewer_transitions.requires_owner_authorized_publication_gate_recheck_only(publication_eval_payload):
        return None
    if not _ai_reviewer_write_routeback_current(publication_eval_payload):
        return None
    action = _publication_story_repair_action(publication_eval_payload)
    if action is None:
        return None
    next_work_unit = _mapping(action.get("next_work_unit"))
    work_unit_id = _text(next_work_unit.get("unit_id"))
    if not _is_ai_reviewer_write_repair_work_unit(next_work_unit):
        return None
    source_eval_id = _text(publication_eval_payload.get("eval_id"))
    resolved_study_root = Path(study_root).expanduser().resolve()
    action_route_target = _text(action.get("route_target"))
    route = {
        "decision_path": None,
        "decision_id": None,
        "controller_actions": ["run_quality_repair_batch"],
        "route_target": "write",
        "route_key_question": _text(action.get("route_key_question")),
        "route_rationale": _text(action.get("route_rationale")) or _text(action.get("reason")),
        "source_route_key_question": _text(action.get("route_key_question")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": _text(action.get("work_unit_fingerprint")) or _text(next_work_unit.get("fingerprint")),
        "publication_eval_id": source_eval_id,
        "publication_eval_ref": {
            "eval_id": source_eval_id,
            "artifact_path": ai_reviewer_publication_eval_records.projection_source_ref(
                publication_eval_payload,
                (resolved_study_root / "artifacts" / "publication_eval" / "latest.json").resolve(),
            ),
        },
        "next_work_unit": dict(next_work_unit),
        "blocking_work_units": [dict(next_work_unit)] if next_work_unit else [],
        "source": "owner_route_reconcile_ai_reviewer_write_routeback",
        "authorization_basis": "ai_reviewer_current_write_routeback",
    }
    if action_route_target and action_route_target != "write":
        route["original_route_target"] = action_route_target
    return route


def _gate_replay_report_payload(batch: Mapping[str, Any], *, study_root: Path) -> dict[str, Any] | None:
    gate_replay = _mapping(batch.get("gate_replay"))
    report_ref = _text(gate_replay.get("report_json")) or _text(gate_replay.get("report_path"))
    if report_ref:
        report_path = Path(report_ref).expanduser()
        if not report_path.is_absolute():
            report_path = study_root / report_path
        report = _read_json_object(report_path)
        if report is not None:
            return report
    return gate_replay or None


def _first_work_unit_for_lane(work_units: Mapping[str, Any], *, lane: str) -> dict[str, Any] | None:
    candidates: list[Any] = []
    next_work_unit = work_units.get("next_work_unit")
    if isinstance(next_work_unit, Mapping):
        candidates.append(next_work_unit)
    candidates.extend(work_units.get("blocking_work_units") or [])
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        if _text(candidate.get("lane")) == lane:
            return dict(candidate)
    return None


def _ai_reviewer_write_routeback_current(publication_eval_payload: Mapping[str, Any]) -> bool:
    provenance = _mapping(publication_eval_payload.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer":
        return False
    reviewer_os = _mapping(publication_eval_payload.get("reviewer_operating_system"))
    currentness = _mapping(reviewer_os.get("currentness_checks"))
    prose = _mapping(currentness.get("medical_prose_review"))
    current_manuscript = _mapping(currentness.get("current_manuscript"))
    prose_current = _text(prose.get("status")) == "current"
    manuscript_current = _text(current_manuscript.get("status")) == "current"
    if not prose_current and not manuscript_current:
        return False
    if prose_current and prose.get("route_back_required") is not True:
        return False
    if _text(prose.get("route_target")) not in {None, "write"}:
        return False
    if prose_current:
        for key in ("request_digest", "manuscript_ref", "manuscript_digest"):
            if _text(prose.get(key)) is None:
                return False
    if manuscript_current:
        for key in ("manuscript_ref", "manuscript_digest"):
            if _text(current_manuscript.get(key)) is None:
                return False
    return _publication_story_repair_action(publication_eval_payload) is not None


def _publication_story_repair_action(publication_eval_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(actions, list):
        return None
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        next_work_unit = _mapping(action.get("next_work_unit"))
        work_unit_id = _text(next_work_unit.get("unit_id"))
        if _text(action.get("action_type")) != "route_back_same_line":
            continue
        if (
            _text(action.get("route_target")) != "write"
            and _text(next_work_unit.get("lane")) != "write"
            and not is_story_surface_delta_write_work_unit(work_unit_id)
        ):
            continue
        return dict(action)
    return None


def _is_ai_reviewer_write_repair_work_unit(next_work_unit: Mapping[str, Any]) -> bool:
    work_unit_id = _text(next_work_unit.get("unit_id"))
    return (
        _text(next_work_unit.get("lane")) == "write"
        or is_story_surface_delta_write_work_unit(work_unit_id)
        or is_claim_evidence_alignment_write_work_unit(work_unit_id)
    )


def _story_surface_delta_blocker_present(batch: Mapping[str, Any]) -> bool:
    if _text(batch.get("blocked_reason")) == "manuscript_story_surface_delta_missing":
        return True
    evidence = _mapping(batch.get("repair_execution_evidence"))
    if _text(evidence.get("status")) != "blocked":
        return False
    blockers = _string_set(evidence.get("blockers"))
    if "manuscript_story_surface_delta_missing" in blockers:
        return True
    artifact_delta = _mapping(evidence.get("canonical_artifact_delta"))
    return (
        _text(artifact_delta.get("status")) == "blocked"
        and artifact_delta.get("meaningful_artifact_delta") is False
        and "forbidden_manuscript_terms_present" in blockers
    )


def _current_manuscript_digest_mismatch_blocker(batch: Mapping[str, Any]) -> dict[str, Any] | None:
    fallback: dict[str, Any] | None = None
    for payload in _current_manuscript_digest_mismatch_candidates(batch):
        if _text(payload.get("blocked_reason")) == EVAL_BOUND_CURRENT_MANUSCRIPT_DIGEST_MISMATCH_BLOCKER:
            candidate = dict(payload)
            if candidate.get("story_surface_digests") or _text(candidate.get("reviewer_manuscript_ref")):
                return candidate
            if fallback is None:
                fallback = candidate
    return fallback


def _current_manuscript_digest_mismatch_candidates(batch: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if _text(batch.get("blocked_reason")) == EVAL_BOUND_CURRENT_MANUSCRIPT_DIGEST_MISMATCH_BLOCKER or _text(
        batch.get("typed_blocker")
    ) == EVAL_BOUND_CURRENT_MANUSCRIPT_DIGEST_MISMATCH_BLOCKER:
        candidates.append(dict(batch))
    for unit in _mapping(batch.get("gate_clearing_batch")).get("unit_results") or []:
        if not isinstance(unit, Mapping):
            continue
        result = _mapping(unit.get("result"))
        currentness_blocker = _mapping(result.get("currentness_blocker"))
        if currentness_blocker:
            candidates.append(
                {
                    **currentness_blocker,
                    "work_unit_id": _text(result.get("work_unit_id")) or _text(unit.get("unit_id")),
                }
            )
        if result:
            candidates.append(
                {
                    **result,
                    "work_unit_id": _text(result.get("work_unit_id")) or _text(unit.get("unit_id")),
                }
            )
    upstream_result = _mapping(batch.get("upstream_unit_result"))
    upstream_currentness = _mapping(_mapping(upstream_result.get("result")).get("currentness_blocker"))
    if upstream_currentness:
        candidates.append(
            {
                **upstream_currentness,
                "work_unit_id": _text(_mapping(upstream_result.get("result")).get("work_unit_id"))
                or _text(upstream_result.get("unit_id")),
            }
        )
    return candidates


def _current_story_surface_refs(blocker: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for item in blocker.get("story_surface_digests") or []:
        if not isinstance(item, Mapping) or item.get("present") is not True:
            continue
        if path := _text(item.get("path")):
            refs.append(path)
    if not refs and (manuscript_ref := _text(blocker.get("reviewer_manuscript_ref"))):
        refs.append(manuscript_ref)
    return list(dict.fromkeys(refs))


def _current_ai_reviewer_eval_consumes_digest_mismatch(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    blocker: Mapping[str, Any],
) -> bool:
    provenance = _mapping(publication_eval_payload.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer":
        return False
    currentness = _mapping(_mapping(publication_eval_payload.get("reviewer_operating_system")).get("currentness_checks"))
    current_manuscript = _mapping(currentness.get("current_manuscript"))
    if _text(current_manuscript.get("status")) != "current":
        return False
    current_ref = _text(current_manuscript.get("manuscript_ref"))
    current_digest = _text(current_manuscript.get("manuscript_digest"))
    if current_ref is None or current_digest is None:
        return False
    reviewer_digest = _text(blocker.get("reviewer_manuscript_digest"))
    if reviewer_digest is not None and reviewer_digest == current_digest:
        return False
    current_path = _resolve_study_ref(study_root, current_ref)
    if current_path is None or _sha256_path(current_path) != current_digest:
        return False
    story_items = [
        dict(item)
        for item in blocker.get("story_surface_digests") or []
        if isinstance(item, Mapping) and item.get("present") is True and _text(item.get("path"))
    ]
    if not story_items:
        return False
    authority_refs = [
        ref
        for ref in [_text(current_ref), *[_text(item) for item in provenance.get("source_refs") or []]]
        if ref is not None
    ]
    current_ref_seen = False
    for item in story_items:
        story_ref = _text(item.get("path"))
        story_digest = _text(item.get("digest"))
        if story_ref is None or story_digest is None:
            return False
        story_path = _resolve_study_ref(study_root, story_ref)
        if story_path is None or _sha256_path(story_path) != story_digest:
            return False
        if story_digest != current_digest:
            return False
        if not _ref_in_authority_refs(study_root=study_root, ref=story_ref, authority_refs=authority_refs):
            return False
        if _refs_equal(study_root=study_root, left=story_ref, right=current_ref):
            current_ref_seen = True
    return current_ref_seen


def methodology_reframe_runtime_route_allowed(
    *,
    decision: Mapping[str, Any],
    work_unit: Mapping[str, Any],
    work_unit_fingerprint: str | None,
    action_types: set[str],
    work_unit_id: str | None,
) -> bool:
    if not (
        _text(decision.get("decision_type")) in {"route_back_same_line", "bounded_analysis", "stop_loss"}
        and work_unit_fingerprint == METHODOLOGY_REFRAME_DECISION_FINGERPRINT
        and "request_opl_stage_attempt" in action_types
        and work_unit.get("hard_methodology") is True
        and work_unit.get("terminal_source_provenance_blocker_consumed") is True
        and work_unit.get("current_transport_claim_must_not_be_used_as_medical_conclusion") is True
    ):
        return False
    if (
        work_unit_id == METHODOLOGY_REFRAME_ANALYSIS_WORK_UNIT
        and _text(work_unit.get("selected_route_option")) == "provenance_limited_harmonization_audit"
    ):
        return True
    return bool(
        work_unit_id == METHODOLOGY_REFRAME_REBUILD_WORK_UNIT
        and _text(work_unit.get("selected_route_option")) == "rebuild_reproducible_model_route"
        and work_unit.get("clean_reproducible_model_rebuild_authorized") is True
    )


def domain_transition_runtime_route_allowed(
    *,
    work_unit_fingerprint: str | None,
    action_types: set[str],
    work_unit_id: str | None,
) -> bool:
    decision_type, fingerprint_work_unit_id = _domain_transition_fingerprint_parts(work_unit_fingerprint)
    if decision_type is None or fingerprint_work_unit_id is None or work_unit_id is None:
        return False
    if fingerprint_work_unit_id != work_unit_id:
        return False
    allowed_actions = DOMAIN_TRANSITION_ACTIONS_BY_DECISION_TYPE.get(decision_type, set())
    return bool(action_types & allowed_actions)


def _domain_transition_fingerprint_parts(work_unit_fingerprint: str | None) -> tuple[str | None, str | None]:
    fingerprint = _text(work_unit_fingerprint)
    if fingerprint is None:
        return None, None
    parts = fingerprint.split("::", 2)
    if len(parts) != 3 or parts[0] != "domain-transition" or not parts[1] or not parts[2]:
        return None, None
    return parts[1], parts[2]


def _publication_work_unit_fingerprints(publication_eval_payload: Mapping[str, Any]) -> set[str]:
    fingerprints: set[str] = set()
    for action in publication_eval_payload.get("recommended_actions") or []:
        if not isinstance(action, Mapping):
            continue
        if fingerprint := _text(action.get("work_unit_fingerprint")):
            fingerprints.add(fingerprint)
        next_work_unit = _mapping(action.get("next_work_unit"))
        if fingerprint := _text(next_work_unit.get("fingerprint")):
            fingerprints.add(fingerprint)
    return fingerprints


def _publication_eval_specificity_targets_complete_for_fingerprint(
    publication_eval_payload: Mapping[str, Any],
    *,
    decision_fingerprint: str,
) -> bool:
    for action in publication_eval_payload.get("recommended_actions") or []:
        if not isinstance(action, Mapping):
            continue
        next_work_unit = _mapping(action.get("next_work_unit"))
        action_fingerprint = _text(action.get("work_unit_fingerprint")) or _text(next_work_unit.get("fingerprint"))
        if action_fingerprint != decision_fingerprint:
            continue
        if specificity_target_status(action.get("specificity_targets")).get("complete") is True:
            return True
    return False


def _publication_work_unit_closed(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    work_unit_id: str,
    work_unit_fingerprint: str | None = None,
) -> bool:
    resolved_study_root = Path(study_root).expanduser().resolve()
    lifecycle_path = (
        resolved_study_root
        / "artifacts"
        / "controller"
        / "publication_work_unit_lifecycle"
        / "latest.json"
    )
    lifecycle = _read_json_object(lifecycle_path)
    if lifecycle is not None and publication_work_unit_lifecycle.lifecycle_payload_is_closed(lifecycle):
        source_eval_id = _text(lifecycle.get("source_eval_id"))
        current_eval_id = _text(publication_eval_payload.get("eval_id"))
        if source_eval_id is not None and current_eval_id is not None and source_eval_id == current_eval_id:
            lifecycle_work_unit = _mapping(lifecycle.get("work_unit"))
            if _text(lifecycle_work_unit.get("unit_id")) == work_unit_id:
                return True
    return _runtime_turn_closeout_closes_work_unit(
        study_root=resolved_study_root,
        publication_eval_payload=publication_eval_payload,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
    )


def _runtime_turn_closeout_closes_work_unit(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    work_unit_id: str,
    work_unit_fingerprint: str | None,
) -> bool:
    quest_root = _publication_eval_quest_root(publication_eval_payload)
    if quest_root is None:
        return False
    closeout_root = quest_root / "artifacts" / "runtime" / "turn_closeouts"
    if not closeout_root.exists():
        return False
    for closeout_path in sorted(closeout_root.glob("*.json")):
        closeout = _read_json_object(closeout_path)
        if closeout is None or closeout.get("status") != "completed":
            continue
        if closeout.get("meaningful_artifact_delta") is not True:
            continue
        for artifact_ref in closeout.get("artifact_refs") or []:
            artifact_path = _resolve_runtime_artifact_ref(quest_root, artifact_ref)
            if artifact_path is None or not _runtime_artifact_ref_is_json_payload(artifact_path):
                continue
            package_closure = _read_json_artifact_object(artifact_path)
            if _package_closure_matches_work_unit(
                package_closure,
                study_root=study_root,
                work_unit_id=work_unit_id,
                work_unit_fingerprint=work_unit_fingerprint,
            ):
                return True
    return False


def _publication_eval_quest_root(publication_eval_payload: Mapping[str, Any]) -> Path | None:
    runtime_context_refs = _mapping(publication_eval_payload.get("runtime_context_refs"))
    runtime_escalation_ref = _text(runtime_context_refs.get("runtime_escalation_ref"))
    if runtime_escalation_ref is not None:
        path = Path(runtime_escalation_ref).expanduser()
        parts = path.parts
        if "artifacts" in parts:
            artifacts_index = parts.index("artifacts")
            if artifacts_index > 0:
                return Path(*parts[:artifacts_index]).resolve()
    return None


def _resolve_runtime_artifact_ref(quest_root: Path, artifact_ref: object) -> Path | None:
    text = _text(artifact_ref)
    if text is None:
        return None
    path = Path(text).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (quest_root / path).resolve()


def _runtime_artifact_ref_is_json_payload(path: Path) -> bool:
    return path.suffix.lower() == ".json"


def _read_json_artifact_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _package_closure_matches_work_unit(
    payload: Mapping[str, Any] | None,
    *,
    study_root: Path,
    work_unit_id: str,
    work_unit_fingerprint: str | None,
) -> bool:
    if payload is None:
        return False
    if _text(payload.get("artifact_kind")) != work_unit_id:
        return False
    work_unit = _mapping(payload.get("work_unit"))
    if _text(work_unit.get("unit_id")) != work_unit_id:
        return False
    if work_unit_fingerprint is not None and _text(work_unit.get("fingerprint")) != work_unit_fingerprint:
        return False
    authority_closure = _mapping(payload.get("authority_closure"))
    if _text(authority_closure.get("status")) != "closed_for_bundle_stage":
        return False
    if _text(authority_closure.get("publication_gate_status")) != "clear":
        return False
    if authority_closure.get("publication_gate_allow_write") is not True:
        return False
    if list(authority_closure.get("publication_gate_blockers") or []):
        return False
    submission_authority = _mapping(payload.get("submission_minimal_authority"))
    if _text(submission_authority.get("status")) != "current":
        return False
    human_facing_delivery = _mapping(payload.get("human_facing_delivery"))
    current_package_zip = _text(human_facing_delivery.get("current_package_zip"))
    if current_package_zip is None:
        return False
    package_path = Path(current_package_zip).expanduser()
    if not package_path.is_absolute():
        package_path = study_root / package_path
    try:
        package_path.resolve().relative_to(study_root.resolve())
    except ValueError:
        return False
    return _text(human_facing_delivery.get("status")) == "current"


def _controller_action_types(payload: Mapping[str, Any]) -> set[str]:
    action_types: set[str] = set()
    for action in payload.get("controller_actions") or []:
        if isinstance(action, Mapping):
            text = _text(action.get("action_type"))
        else:
            text = _text(action)
        if text is not None:
            action_types.add(text)
    return action_types


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


def _resolve_study_ref(study_root: Path, ref: str | None) -> Path | None:
    text = _text(ref)
    if text is None:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = study_root / path
    return path.resolve()


def _sha256_path(path: Path) -> str | None:
    try:
        return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
    except OSError:
        return None


def _refs_equal(*, study_root: Path, left: str, right: str) -> bool:
    left_path = _resolve_study_ref(study_root, left)
    right_path = _resolve_study_ref(study_root, right)
    return left_path is not None and right_path is not None and left_path == right_path


def _ref_in_authority_refs(*, study_root: Path, ref: str, authority_refs: list[str]) -> bool:
    return any(_refs_equal(study_root=study_root, left=ref, right=authority_ref) for authority_ref in authority_refs)


__all__ = [
    "GATE_CLEARING_BATCH_RELATIVE_PATH",
    "QUALITY_REPAIR_BATCH_RELATIVE_PATH",
    "OPL_STAGE_ATTEMPT_ADMISSION_REASON",
    "RUNTIME_CONTROLLER_REDRIVE_REASON",
    "current_gate_replay_submission_refresh_route",
    "current_gate_replay_routeback_route",
    "current_manuscript_digest_mismatch_ai_reviewer_route",
    "current_quality_repair_writer_handoff_route",
    "current_story_surface_delta_blocker_route",
    "current_controller_runtime_route",
    "next_owner_for_reason",
]
