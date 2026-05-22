from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import control_intent
from med_autoscience.controllers import gate_clearing_batch
from med_autoscience.controllers import gate_clearing_batch_blockers
from med_autoscience.controllers import gate_clearing_batch_currentness
from med_autoscience.controllers import quality_repair_batch_upstream
from med_autoscience.controllers import paper_repair_execution_evidence
from med_autoscience.controllers import quality_repair_paper_owner_surface
from med_autoscience.controllers import publication_work_units
from med_autoscience.controllers import study_runtime_router
from med_autoscience.controllers.quality_repair_batch_parts import repair_execution_gate
from med_autoscience.controllers.quality_repair_batch_parts import story_surface_delta
from med_autoscience.controllers.quality_repair_batch_parts import upstream_route_context
from med_autoscience.controllers.quality_repair_batch_parts import writer_handoff
from med_autoscience.controllers.gate_clearing_batch_work_units import UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS
from med_autoscience.controllers.control_plane_route_gate import assert_control_plane_route_authorized
from med_autoscience.controllers.study_runtime_execution_parts.controller_authorization_context import (
    _load_controller_decision_authorization_context,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience import study_task_intake
from med_autoscience.study_decision_record import StudyDecisionActionType, StudyDecisionType


SCHEMA_VERSION = 1
STABLE_QUALITY_REPAIR_BATCH_RELATIVE_PATH = Path("artifacts/controller/quality_repair_batch/latest.json")
EVAL_HYGIENE_QUALITY_SUMMARY_RELATIVE_PATH = Path("artifacts/eval_hygiene/evaluation_summary/latest.json")
LEGACY_QUALITY_SUMMARY_RELATIVE_PATH = Path("artifacts/evaluation_summary/latest.json")
_QUALITY_REPAIR_CLOSURE_STATES = frozenset({"quality_repair_required"})
_QUALITY_REPAIR_LANES = frozenset({"general_quality_repair", "quality_floor_blocker"})
_ANALYSIS_REPAIR_WORK_UNIT_ID = "analysis_claim_evidence_repair"
_ANALYSIS_REPAIR_ROUTE_TARGET = "analysis-campaign"
_ANALYSIS_REPAIR_ACTION = StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value
_HARD_METHODOLOGY_NEXT_OWNER = "analysis_harmonization_owner"
_HARD_METHODOLOGY_NEXT_WORK_UNIT = "unit_harmonized_external_validation_rerun"
_HARD_METHODOLOGY_BLOCKED_REASON = "unit_harmonized_rerun_required"


def stable_quality_repair_batch_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / STABLE_QUALITY_REPAIR_BATCH_RELATIVE_PATH


def story_surface_delta_blocker_supersedes_lifecycle(
    *,
    study_root: Path,
    lifecycle: Mapping[str, Any],
) -> bool:
    resolved_study_root = Path(study_root).expanduser().resolve()
    return story_surface_delta.blocker_supersedes_lifecycle(
        study_root=resolved_study_root,
        lifecycle=lifecycle,
        batch_path=stable_quality_repair_batch_path(study_root=resolved_study_root),
    )


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _materialize_writer_worker_handoff(handoff: Mapping[str, Any] | None) -> str | None:
    if handoff is None:
        return None
    refs = handoff.get("refs") if isinstance(handoff.get("refs"), Mapping) else {}
    dispatch_path_text = _non_empty_text(refs.get("dispatch_path"))
    if dispatch_path_text is None:
        raise ValueError("writer_worker_handoff_missing_dispatch_path")
    dispatch_path = Path(dispatch_path_text).expanduser()
    _write_json(dispatch_path, handoff)
    return str(dispatch_path)


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _quality_summary_path(*, study_root: Path) -> Path:
    resolved_study_root = Path(study_root).expanduser().resolve()
    canonical_path = resolved_study_root / EVAL_HYGIENE_QUALITY_SUMMARY_RELATIVE_PATH
    if canonical_path.exists():
        return canonical_path
    return resolved_study_root / LEGACY_QUALITY_SUMMARY_RELATIVE_PATH


def _read_quality_summary(*, study_root: Path) -> dict[str, Any]:
    return _read_json_object(_quality_summary_path(study_root=study_root))


def _effective_quality_summary(
    *,
    study_root: Path,
    gate_report: Mapping[str, Any],
    summary_payload: Mapping[str, Any],
) -> dict[str, Any]:
    override = study_task_intake.build_task_intake_progress_override(
        study_task_intake.read_latest_task_intake(study_root=study_root),
        study_root=study_root,
        publishability_gate_report=dict(gate_report),
        evaluation_summary=dict(summary_payload),
    )
    if not isinstance(override, Mapping):
        return dict(summary_payload)
    return {
        **dict(summary_payload),
        "quality_closure_truth": dict(override.get("quality_closure_truth") or {}),
        "quality_execution_lane": dict(override.get("quality_execution_lane") or {}),
        "same_line_route_truth": dict(override.get("same_line_route_truth") or {}),
        "same_line_route_surface": dict(override.get("same_line_route_surface") or {}),
    }


def _quality_repair_context(summary_payload: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), Mapping)
        else {}
    )
    quality_execution_lane = (
        dict(summary_payload.get("quality_execution_lane") or {})
        if isinstance(summary_payload.get("quality_execution_lane"), Mapping)
        else {}
    )
    return quality_closure_truth, quality_execution_lane


def _quality_repair_required(summary_payload: Mapping[str, Any]) -> bool:
    quality_closure_truth, quality_execution_lane = _quality_repair_context(summary_payload)
    closure_state = _non_empty_text(quality_closure_truth.get("state"))
    lane_id = _non_empty_text(quality_execution_lane.get("lane_id"))
    return closure_state in _QUALITY_REPAIR_CLOSURE_STATES or lane_id in _QUALITY_REPAIR_LANES


def _same_line_paper_repair_required(summary_payload: Mapping[str, Any]) -> bool:
    quality_closure_truth, quality_execution_lane = _quality_repair_context(summary_payload)
    if _non_empty_text(quality_closure_truth.get("state")) not in _QUALITY_REPAIR_CLOSURE_STATES:
        return False
    current_required_action = _non_empty_text(quality_closure_truth.get("current_required_action"))
    route_target = (
        _non_empty_text(quality_execution_lane.get("route_target"))
        or _non_empty_text(quality_closure_truth.get("route_target"))
    )
    return current_required_action in {"return_to_analysis_campaign", "continue_write_stage"} or route_target in {
        "analysis-campaign",
        "write",
    }


def _gate_blockers(gate_report: Mapping[str, Any]) -> set[str]:
    return {
        text
        for item in (gate_report.get("blockers") or [])
        if (text := _non_empty_text(item)) is not None
    }


def _repairable_medical_surface(gate_report: Mapping[str, Any]) -> bool:
    return gate_clearing_batch_blockers.repairable_medical_surface(dict(gate_report))


def _repair_candidates(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    quest_id: str,
    gate_report: Mapping[str, Any],
    publication_work_unit_payload: Mapping[str, Any] | None = None,
    include_downstream_delivery: bool = True,
) -> list[str]:
    candidates: list[str] = []
    quest_root = profile.managed_runtime_quests_root / quest_id
    _, mapping_payload = gate_clearing_batch._eligible_mapping_payload(
        quest_root=quest_root,
        study_root=study_root,
    )
    if mapping_payload:
        candidates.append("scientific-anchor fields can be frozen from bounded-analysis output")
    if _repairable_medical_surface(gate_report):
        candidates.append("paper-facing display/reporting blockers are deterministic repair candidates")
    next_work_unit = (
        publication_work_unit_payload.get("next_work_unit")
        if isinstance(publication_work_unit_payload, Mapping)
        else None
    )
    if (
        isinstance(next_work_unit, Mapping)
        and _non_empty_text(next_work_unit.get("unit_id")) in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS
        and "paper-facing display/reporting blockers are deterministic repair candidates" not in candidates
    ):
        candidates.append("paper-facing specificity targets are deterministic repair candidates")
    if include_downstream_delivery and "stale_study_delivery_mirror" in _gate_blockers(gate_report):
        candidates.append("study delivery mirror is stale but repairable through controller-owned replay")
    return candidates


def _latest_batch_record(*, study_root: Path) -> dict[str, Any]:
    return _read_json_object(stable_quality_repair_batch_path(study_root=study_root))


def _runtime_control_plane_route_context(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    source_eval_id: str | None = None,
) -> dict[str, Any] | None:
    status_payload = study_runtime_router.study_runtime_status(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        entry_mode=None,
        sync_runtime_summary=False,
        include_progress_projection=False,
    )
    if not isinstance(status_payload, Mapping):
        return None
    control_plane_snapshot = status_payload.get("control_plane_snapshot")
    if not isinstance(control_plane_snapshot, Mapping):
        return None
    route_context: dict[str, Any] = {"control_plane_snapshot": dict(control_plane_snapshot)}
    controller_route_context = _controller_route_context_for_latest_controller_decision(
        study_root=study_root,
        source_eval_id=source_eval_id,
    ) or _controller_route_context_for_runtime_authorization(
        status_payload,
        source_eval_id=source_eval_id,
    )
    if controller_route_context is not None:
        route_context.update(controller_route_context)
    return route_context


def _controller_route_context_for_latest_controller_decision(
    *,
    study_root: Path,
    source_eval_id: str | None,
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    decision_payload = _read_json_object(resolved_study_root / "artifacts" / "controller_decisions" / "latest.json")
    decision_eval_ref = decision_payload.get("publication_eval_ref")
    decision_eval_id = (
        _non_empty_text(decision_eval_ref.get("eval_id"))
        if isinstance(decision_eval_ref, Mapping)
        else None
    )
    if source_eval_id is not None and decision_eval_id != source_eval_id:
        return None
    authorization = _load_controller_decision_authorization_context(study_root=resolved_study_root)
    if not isinstance(authorization, Mapping):
        return None
    controller_actions = {
        text
        for action in (authorization.get("controller_actions") or ())
        if (text := _non_empty_text(action)) is not None
    }
    if StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value not in controller_actions:
        return None
    return _controller_route_context_for_authorization(
        authorization,
        source_eval_id=source_eval_id,
    )


def _controller_route_context_for_runtime_authorization(
    status_payload: Mapping[str, Any],
    *,
    source_eval_id: str | None,
) -> dict[str, Any] | None:
    authorization = status_payload.get("last_controller_decision_authorization")
    return _controller_route_context_for_authorization(
        authorization,
        source_eval_id=source_eval_id,
    )


def _controller_route_context_for_authorization(
    authorization: object,
    *,
    source_eval_id: str | None,
) -> dict[str, Any] | None:
    if not isinstance(authorization, Mapping):
        return None
    if bool(authorization.get("requires_human_confirmation")):
        return None
    next_work_unit = authorization.get("next_work_unit")
    next_work_unit_id = (
        _non_empty_text(next_work_unit.get("unit_id"))
        if isinstance(next_work_unit, Mapping)
        else None
    )
    identity = authorization.get("control_intent_identity")
    identity_work_unit_id = (
        _non_empty_text(identity.get("work_unit_id"))
        if isinstance(identity, Mapping)
        else None
    )
    candidate_ids = [
        text
        for text in (
            next_work_unit_id,
            _non_empty_text(authorization.get("work_unit_id")),
            identity_work_unit_id,
        )
        if text is not None
    ]
    if not candidate_ids:
        return None
    work_unit_id = candidate_ids[0]
    if any(candidate_id != work_unit_id for candidate_id in candidate_ids):
        return None
    work_unit_fingerprint = _non_empty_text(authorization.get("work_unit_fingerprint"))
    if work_unit_fingerprint is None and isinstance(identity, Mapping):
        work_unit_fingerprint = _non_empty_text(identity.get("blocker_authority_fingerprint"))
    return {
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
            "work_unit_id": work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": source_eval_id,
            "work_unit_fingerprint": work_unit_fingerprint,
        }
    }


def _controller_route_context_for_gate(
    *,
    gate_report: Mapping[str, Any],
    source_eval_id: str | None,
) -> dict[str, Any] | None:
    blockers = _gate_blockers(gate_report)
    if _non_empty_text(gate_report.get("current_required_action")) not in {
        "complete_bundle_stage",
        "continue_bundle_stage",
    }:
        return None
    if gate_clearing_batch.gate_clearing_batch_submission.submission_minimal_refresh_requested(
        gate_report=dict(gate_report)
    ):
        work_unit_id = "submission_minimal_refresh"
    elif "stale_study_delivery_mirror" in blockers:
        work_unit_id = "submission_delivery_sync_closure"
    else:
        return None
    return {
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
            "work_unit_id": work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": source_eval_id,
            "gate_fingerprint": _non_empty_text(gate_report.get("gate_fingerprint")),
            "work_unit_fingerprint": _non_empty_text(gate_report.get("work_unit_fingerprint")),
        }
    }


def _controller_route_context_for_publication_work_unit(
    *,
    gate_report: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    source_eval_id: str | None,
) -> dict[str, Any] | None:
    publication_work_unit_payload = publication_work_units.derive_publication_work_units(
        dict(gate_report),
        specificity_targets=_upstream_repair_specificity_targets(publication_eval_payload),
    )
    publication_work_unit_payload = _apply_explicit_upstream_publication_work_unit(
        publication_work_unit_payload,
        publication_eval_payload=publication_eval_payload,
    )
    return _controller_route_context_for_publication_work_unit_payload(
        publication_work_unit_payload=publication_work_unit_payload,
        gate_report=gate_report,
        source_eval_id=source_eval_id,
    )


def _controller_route_context_for_publication_work_unit_payload(
    *,
    publication_work_unit_payload: Mapping[str, Any],
    gate_report: Mapping[str, Any],
    source_eval_id: str | None,
) -> dict[str, Any] | None:
    return upstream_route_context.controller_route_context_for_publication_work_unit_payload(
        publication_work_unit_payload=publication_work_unit_payload,
        gate_report=gate_report,
        source_eval_id=source_eval_id,
        upstream_work_unit_ids=UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS,
        controller_action_type=StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
        non_empty_text=_non_empty_text,
    )


def _route_context_work_unit_id(route_context: Mapping[str, Any] | None) -> str | None:
    return upstream_route_context.route_context_work_unit_id(
        route_context,
        non_empty_text=_non_empty_text,
    )


def _route_action_for_controller_context(route_context: Mapping[str, Any] | None) -> str:
    controller_route_context = (
        route_context.get("controller_route_context")
        if isinstance(route_context, Mapping)
        else None
    )
    if not isinstance(controller_route_context, Mapping):
        return "bundle_build"
    if _non_empty_text(controller_route_context.get("work_unit_id")) in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS:
        return "paper_write"
    return "bundle_build"


def _upstream_repair_specificity_targets(publication_eval_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    return publication_work_units.specificity_targets_from_publication_eval(
        publication_eval_payload,
        require_complete=False,
        include_upstream_repair_work_units=True,
    )


def _merge_route_contexts(*contexts: Mapping[str, Any] | None) -> dict[str, Any] | None:
    merged: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, Mapping):
            merged.update(dict(context))
    return merged or None


def _has_explicit_controller_route_context(route_context: Mapping[str, Any] | None) -> bool:
    if not isinstance(route_context, Mapping):
        return False
    return any(isinstance(route_context.get(key), Mapping) for key in ("controller_route_context", "explicit_controller_route_context"))


def _latest_owner_handoff(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    work_unit_fingerprint: str | None,
) -> dict[str, Any] | None:
    if work_unit_fingerprint is None:
        return None
    identity = control_intent.build_control_intent_identity(
        study_id=study_id,
        quest_id=quest_id,
        route_target=_ANALYSIS_REPAIR_ROUTE_TARGET,
        work_unit_id=_ANALYSIS_REPAIR_WORK_UNIT_ID,
        blocker_authority_fingerprint=work_unit_fingerprint,
        controller_actions=(_ANALYSIS_REPAIR_ACTION,),
        source_kind="controller_decision_authorization",
    )
    latest = None
    for event in reversed(control_intent.events_for_business_key(study_root=study_root, business_key=identity.business_key)):
        if _non_empty_text(event.get("event_type")) == "owner_handoff":
            latest = event
            break
    if not isinstance(latest, Mapping):
        return None
    payload = latest.get("payload")
    if not isinstance(payload, Mapping):
        return None
    next_work_unit = _non_empty_text(payload.get("next_work_unit"))
    next_owner = _non_empty_text(payload.get("next_owner"))
    if next_work_unit is None or next_owner is None:
        return None
    return {
        "from_work_unit": _ANALYSIS_REPAIR_WORK_UNIT_ID,
        "work_unit_fingerprint": work_unit_fingerprint,
        "next_owner": next_owner,
        "next_work_unit": next_work_unit,
        "reason": _non_empty_text(payload.get("reason")),
        "event_recorded_at": _non_empty_text(latest.get("recorded_at")),
    }


def _apply_owner_handoff_to_publication_work_units(
    publication_work_unit_payload: Mapping[str, Any],
    *,
    owner_handoff: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(publication_work_unit_payload)
    if not isinstance(owner_handoff, Mapping):
        return payload
    handoff_next_unit = _non_empty_text(owner_handoff.get("next_work_unit"))
    current_next_work_unit = payload.get("next_work_unit")
    if (
        handoff_next_unit is None
        or not isinstance(current_next_work_unit, Mapping)
        or _non_empty_text(current_next_work_unit.get("unit_id")) != _ANALYSIS_REPAIR_WORK_UNIT_ID
    ):
        return payload
    units = [dict(item) for item in payload.get("blocking_work_units") or [] if isinstance(item, Mapping)]
    promoted_unit: dict[str, Any] | None = None
    for unit in units:
        if _non_empty_text(unit.get("unit_id")) == handoff_next_unit:
            promoted_unit = unit
            break
    if promoted_unit is None:
        return payload
    remaining_units = [unit for unit in units if _non_empty_text(unit.get("unit_id")) != _ANALYSIS_REPAIR_WORK_UNIT_ID]
    payload["blocking_work_units"] = remaining_units
    payload["next_work_unit"] = promoted_unit
    payload["controller_work_unit_owner_handoff"] = dict(owner_handoff)
    return payload


def _compact_publication_work_unit(value: object) -> dict[str, str] | None:
    if not isinstance(value, Mapping):
        return None
    unit_id = _non_empty_text(value.get("unit_id"))
    if unit_id is None:
        return None
    payload = {"unit_id": unit_id}
    lane = _non_empty_text(value.get("lane"))
    summary = _non_empty_text(value.get("summary"))
    if lane is not None:
        payload["lane"] = lane
    if summary is not None:
        payload["summary"] = summary
    return payload


def _hard_methodology_target_from_publication_work_units(
    publication_work_unit_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    target = publication_work_unit_payload.get("hard_methodology_target")
    return dict(target) if isinstance(target, Mapping) else None


def _hard_methodology_owner_handoff_record(
    *,
    study_id: str,
    quest_id: str,
    source_eval_id: str | None,
    source_eval_artifact_path: str,
    source_summary_id: str | None,
    source_summary_artifact_path: str,
    control_plane_route_gate: Mapping[str, Any],
    paper_owner_surface_prepare: Mapping[str, Any],
    gate_clearing_result: Mapping[str, Any],
    hard_methodology_target: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "source_eval_id": source_eval_id,
        "source_eval_artifact_path": source_eval_artifact_path,
        "source_summary_id": source_summary_id,
        "source_summary_artifact_path": source_summary_artifact_path,
        "status": "blocked",
        "ok": False,
        "quest_id": quest_id,
        "study_id": study_id,
        "blocked_reason": _HARD_METHODOLOGY_BLOCKED_REASON,
        "next_owner": _HARD_METHODOLOGY_NEXT_OWNER,
        "next_work_unit": _HARD_METHODOLOGY_NEXT_WORK_UNIT,
        "hard_methodology_target": dict(hard_methodology_target),
        "gate_clearing_batch": dict(gate_clearing_result),
        "control_plane_route_gate": dict(control_plane_route_gate),
        "paper_owner_surface_prepare": dict(paper_owner_surface_prepare),
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
    }


def _explicit_upstream_publication_work_unit(
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    return upstream_route_context.explicit_upstream_publication_work_unit(
        publication_eval_payload,
        upstream_work_unit_ids=UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS,
        compact_publication_work_unit=_compact_publication_work_unit,
        non_empty_text=_non_empty_text,
        bounded_analysis_action=StudyDecisionType.BOUNDED_ANALYSIS.value,
        route_back_same_line_action=StudyDecisionType.ROUTE_BACK_SAME_LINE.value,
    )


def _apply_explicit_upstream_publication_work_unit(
    publication_work_unit_payload: Mapping[str, Any],
    *,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return upstream_route_context.apply_explicit_upstream_publication_work_unit(
        publication_work_unit_payload,
        publication_eval_payload=publication_eval_payload,
        upstream_work_unit_ids=UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS,
        compact_publication_work_unit=_compact_publication_work_unit,
        non_empty_text=_non_empty_text,
        bounded_analysis_action=StudyDecisionType.BOUNDED_ANALYSIS.value,
        route_back_same_line_action=StudyDecisionType.ROUTE_BACK_SAME_LINE.value,
    )


def build_quality_repair_batch_recommended_action(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    quest_id: str,
    publication_eval_payload: dict[str, Any],
    gate_report: dict[str, Any],
) -> dict[str, Any] | None:
    verdict = publication_eval_payload.get("verdict")
    if not isinstance(verdict, dict) or _non_empty_text(verdict.get("overall_verdict")) != "blocked":
        return None
    if _non_empty_text(gate_report.get("status")) != "blocked":
        return None

    resolved_study_root = Path(study_root).expanduser().resolve()
    summary_payload = _read_quality_summary(study_root=resolved_study_root)

    current_eval_id = _non_empty_text(publication_eval_payload.get("eval_id"))
    latest_batch = _latest_batch_record(study_root=resolved_study_root)
    nested_gate_batch = latest_batch.get("gate_clearing_batch")
    if not isinstance(nested_gate_batch, dict):
        nested_gate_batch = {}
    if gate_clearing_batch_currentness.batch_closed_for_source_eval(
        nested_gate_batch,
        source_eval_id=current_eval_id,
    ):
        return None

    specificity_targets = _upstream_repair_specificity_targets(publication_eval_payload)
    publication_work_unit_payload = publication_work_units.derive_publication_work_units(
        gate_report,
        specificity_targets=specificity_targets,
    )
    publication_work_unit_payload = _apply_explicit_upstream_publication_work_unit(
        publication_work_unit_payload,
        publication_eval_payload=publication_eval_payload,
    )
    candidates = _repair_candidates(
        profile=profile,
        study_root=resolved_study_root,
        quest_id=quest_id,
        gate_report=gate_report,
        publication_work_unit_payload=publication_work_unit_payload,
        include_downstream_delivery=not bool(gate_report.get("bundle_tasks_downstream_only")),
    )
    if not candidates:
        return None

    summary_payload = _effective_quality_summary(
        study_root=resolved_study_root,
        gate_report=gate_report,
        summary_payload=summary_payload,
    )
    if not summary_payload or not _quality_repair_required(summary_payload):
        return None

    publication_work_unit_payload = _apply_owner_handoff_to_publication_work_units(
        publication_work_unit_payload,
        owner_handoff=_latest_owner_handoff(
            study_root=resolved_study_root,
            study_id=resolved_study_root.name,
            quest_id=quest_id,
            work_unit_fingerprint=_non_empty_text(publication_work_unit_payload.get("fingerprint")),
        ),
    )
    quality_closure_truth, quality_execution_lane = _quality_repair_context(summary_payload)
    route_target = (
        _non_empty_text(quality_execution_lane.get("route_target"))
        or _non_empty_text(quality_closure_truth.get("route_target"))
        or "review"
    )
    route_key_question = _non_empty_text(quality_execution_lane.get("route_key_question")) or (
        "Which deterministic quality repair is still blocking the publishability gate?"
    )
    route_rationale = (
        _non_empty_text(quality_execution_lane.get("summary"))
        or _non_empty_text(quality_closure_truth.get("summary"))
        or "Run deterministic quality repair units before replaying the publishability gate."
    )
    reason_bits = ["quality_closure_truth requires deterministic repair", *candidates]
    return {
        "action_id": f"quality-repair-batch::{resolved_study_root.name}::{current_eval_id or 'latest'}",
        "action_type": StudyDecisionType.ROUTE_BACK_SAME_LINE.value,
        "priority": "now",
        "reason": "Run one controller-owned quality repair batch before returning to publishability gate.",
        "route_target": route_target,
        "route_key_question": route_key_question,
        "route_rationale": route_rationale,
        "requires_controller_decision": True,
        "controller_action_type": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
        "quality_repair_batch_reason": "; ".join(reason_bits),
        "work_unit_fingerprint": publication_work_unit_payload.get("fingerprint"),
        "gate_fingerprint": gate_report.get("gate_fingerprint"),
        "blocking_artifact_refs": publication_work_unit_payload.get("blocking_artifact_refs")
        or gate_report.get("blocking_artifact_refs")
        or [],
        "blocking_work_units": publication_work_unit_payload.get("blocking_work_units") or [],
        "next_work_unit": publication_work_unit_payload.get("next_work_unit"),
        **({"specificity_targets": specificity_targets} if specificity_targets else {}),
        **(
            {"controller_work_unit_owner_handoff": publication_work_unit_payload["controller_work_unit_owner_handoff"]}
            if isinstance(publication_work_unit_payload.get("controller_work_unit_owner_handoff"), Mapping)
            else {}
        ),
    }


def run_quality_repair_batch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    source: str = "med_autoscience",
    control_plane_route_context: Mapping[str, Any] | None = None,
    route_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    publication_eval_payload = read_publication_eval_latest(study_root=resolved_study_root)
    current_eval_id = _non_empty_text(publication_eval_payload.get("eval_id"))
    resolved_route_context = (
        control_plane_route_context
        or route_context
        or _runtime_control_plane_route_context(
            profile=profile,
            study_id=study_id,
            study_root=resolved_study_root,
            source_eval_id=current_eval_id,
        )
    )
    quest_root = profile.managed_runtime_quests_root / quest_id
    gate_state = gate_clearing_batch.publication_gate.build_gate_state(quest_root)
    gate_report = gate_clearing_batch.publication_gate.build_gate_report(gate_state)
    specificity_targets = _upstream_repair_specificity_targets(publication_eval_payload)
    publication_work_unit_payload = publication_work_units.derive_publication_work_units(
        gate_report,
        specificity_targets=specificity_targets,
    )
    publication_work_unit_payload = _apply_explicit_upstream_publication_work_unit(
        publication_work_unit_payload,
        publication_eval_payload=publication_eval_payload,
    )
    hard_methodology_target = _hard_methodology_target_from_publication_work_units(publication_work_unit_payload)
    summary_payload = _read_quality_summary(study_root=resolved_study_root)
    summary_payload = _effective_quality_summary(
        study_root=resolved_study_root,
        gate_report=gate_report,
        summary_payload=summary_payload,
    )
    if _has_explicit_controller_route_context(resolved_route_context):
        explicit_work_unit_id = _route_context_work_unit_id(resolved_route_context)
        controller_route_context = (
            _controller_route_context_for_publication_work_unit_payload(
                publication_work_unit_payload=publication_work_unit_payload,
                gate_report=gate_report,
                source_eval_id=current_eval_id,
            )
            if explicit_work_unit_id not in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS
            else None
        )
    else:
        if _same_line_paper_repair_required(summary_payload):
            controller_route_context = _controller_route_context_for_publication_work_unit(
                gate_report=gate_report,
                publication_eval_payload=publication_eval_payload,
                source_eval_id=current_eval_id,
            )
        else:
            controller_route_context = _controller_route_context_for_gate(
                gate_report=gate_report,
                source_eval_id=current_eval_id,
            )
            if controller_route_context is None:
                controller_route_context = _controller_route_context_for_publication_work_unit(
                    gate_report=gate_report,
                    publication_eval_payload=publication_eval_payload,
                    source_eval_id=current_eval_id,
                )
    resolved_route_context = _merge_route_contexts(
        resolved_route_context,
        controller_route_context,
    )
    control_plane_route_gate = assert_control_plane_route_authorized(
        _route_action_for_controller_context(resolved_route_context),
        {"projection_only": True} if resolved_route_context is None else resolved_route_context,
    )
    source_eval_artifact_path = str(
        (resolved_study_root / "artifacts" / "publication_eval" / "latest.json").resolve()
    )
    source_summary_artifact_path = str(_quality_summary_path(study_root=resolved_study_root).resolve())
    source_summary_id = _non_empty_text(summary_payload.get("summary_id"))
    if hard_methodology_target is not None:
        record = _hard_methodology_owner_handoff_record(
            study_id=study_id,
            quest_id=quest_id,
            source_eval_id=current_eval_id,
            source_eval_artifact_path=source_eval_artifact_path,
            source_summary_id=source_summary_id,
            source_summary_artifact_path=source_summary_artifact_path,
            control_plane_route_gate=control_plane_route_gate,
            paper_owner_surface_prepare={
                "status": "not_applicable",
                "reason": "hard_methodology_owner_handoff",
            },
            gate_clearing_result={
                "ok": False,
                "status": "not_run",
                "reason": _HARD_METHODOLOGY_BLOCKED_REASON,
            },
            hard_methodology_target=hard_methodology_target,
        )
        record_path = stable_quality_repair_batch_path(study_root=resolved_study_root)
        _write_json(record_path, record)
        return {
            "ok": False,
            "status": "blocked",
            "record_path": str(record_path),
            **record,
        }
    paper_owner_surface_prepare = (
        quality_repair_paper_owner_surface.prepare_canonical_paper_owner_surface_for_upstream_repair(
        profile=profile,
        study_id=study_id,
        study_root=resolved_study_root,
        quest_id=quest_id,
        gate_state=gate_state,
        control_plane_route_gate=control_plane_route_gate,
        )
    )
    if _non_empty_text(paper_owner_surface_prepare.get("status")) == "blocked_missing_authorized_canonical_inputs":
        record = {
            "schema_version": SCHEMA_VERSION,
            "source_eval_id": current_eval_id,
            "source_eval_artifact_path": str(
                (resolved_study_root / "artifacts" / "publication_eval" / "latest.json").resolve()
            ),
            "status": "blocked_no_paper_root",
            "ok": False,
            "quest_id": quest_id,
            "study_id": study_id,
            "control_plane_route_gate": control_plane_route_gate,
            "paper_owner_surface_prepare": paper_owner_surface_prepare,
            "blocked_reason": "canonical_paper_inputs_rehydrate_required",
            "next_owner": "write",
        }
        record_path = stable_quality_repair_batch_path(study_root=resolved_study_root)
        _write_json(record_path, record)
        return {
            "ok": False,
            "status": "blocked_no_paper_root",
            "record_path": str(record_path),
            **record,
        }
    quality_closure_truth, quality_execution_lane = _quality_repair_context(summary_payload)
    latest_batch = _latest_batch_record(study_root=resolved_study_root)
    nested_gate_batch = latest_batch.get("gate_clearing_batch")
    if not isinstance(nested_gate_batch, dict):
        nested_gate_batch = {}
    if gate_clearing_batch_currentness.batch_closed_for_source_eval(
        nested_gate_batch,
        source_eval_id=current_eval_id,
    ):
        return {
            "ok": True,
            "status": "skipped_duplicate_eval",
            "source_eval_id": current_eval_id,
            "latest_record_path": str(stable_quality_repair_batch_path(study_root=resolved_study_root)),
            "control_plane_route_gate": control_plane_route_gate,
        }

    gate_clearing_result = gate_clearing_batch.run_gate_clearing_batch(
        profile=profile,
        study_id=study_id,
        study_root=resolved_study_root,
        quest_id=quest_id,
        source=source,
        control_plane_route_context=resolved_route_context,
    )
    upstream_work_unit_id = repair_execution_gate.selected_work_unit_id_from_gate_result(
        gate_clearing_result,
        upstream_work_unit_ids=UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS,
    )
    if upstream_work_unit_id is None:
        route_work_unit_id = _route_context_work_unit_id(resolved_route_context)
        if route_work_unit_id in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS:
            upstream_work_unit_id = route_work_unit_id
    upstream_unit_result = quality_repair_batch_upstream.run_upstream_paper_repair_unit(
        study_id=study_id,
        quest_id=quest_id,
        study_root=resolved_study_root,
        gate_report=gate_report,
        work_unit_id=upstream_work_unit_id,
        source_eval_id=current_eval_id,
    )
    gate_clearing_result = repair_execution_gate.merge_upstream_unit_result(
        gate_clearing_result=gate_clearing_result,
        upstream_unit_result=upstream_unit_result,
    )
    gate_clearing_execution_summary = (
        dict(gate_clearing_result.get("execution_summary"))
        if isinstance(gate_clearing_result.get("execution_summary"), Mapping)
        else None
    )
    repair_execution_evidence = paper_repair_execution_evidence.build_from_quality_repair_batch_result(
        study_id=study_id,
        quest_id=quest_id,
        study_root=resolved_study_root,
        source_eval_id=current_eval_id,
        source_eval_artifact_path=source_eval_artifact_path,
        source_summary_id=source_summary_id,
        source_summary_artifact_path=source_summary_artifact_path,
        gate_clearing_result=gate_clearing_result,
        previous_quality_repair_batch=latest_batch,
    )
    repair_execution_evidence_path = paper_repair_execution_evidence.write_repair_execution_evidence(
        study_root=resolved_study_root,
        evidence=repair_execution_evidence,
    )
    blocked_repair_reason = repair_execution_gate.blocked_repair_execution_reason(repair_execution_evidence)
    writer_worker_handoff = (
        writer_handoff.build_writer_worker_handoff(
            profile=profile,
            study_id=study_id,
            quest_id=quest_id,
            schema_version=SCHEMA_VERSION,
            source_eval_id=current_eval_id,
            source_eval_artifact_path=source_eval_artifact_path,
            source_summary_artifact_path=source_summary_artifact_path,
            repair_execution_evidence_path=repair_execution_evidence_path,
            blocked_repair_reason=blocked_repair_reason,
            control_plane_route_context=resolved_route_context,
        )
        if writer_handoff.should_emit_writer_handoff(blocked_repair_reason)
        else None
    )
    writer_worker_handoff_path = _materialize_writer_worker_handoff(writer_worker_handoff)
    record = {
        "schema_version": SCHEMA_VERSION,
        "source_eval_id": current_eval_id,
        "source_eval_artifact_path": source_eval_artifact_path,
        "source_summary_id": source_summary_id,
        "source_summary_artifact_path": source_summary_artifact_path,
        "status": (
            "handoff_ready"
            if writer_worker_handoff is not None
            else "blocked"
            if blocked_repair_reason
            else (_non_empty_text(gate_clearing_result.get("status")) or "executed")
        ),
        "ok": True if writer_worker_handoff is not None else (False if blocked_repair_reason else bool(gate_clearing_result.get("ok"))),
        "quest_id": quest_id,
        "study_id": study_id,
        "quality_closure_state": _non_empty_text(quality_closure_truth.get("state")),
        "quality_execution_lane_id": _non_empty_text(quality_execution_lane.get("lane_id")),
        "gate_clearing_batch": gate_clearing_result,
        "gate_clearing_execution_summary": gate_clearing_execution_summary,
        "control_plane_route_gate": control_plane_route_gate,
        "paper_owner_surface_prepare": paper_owner_surface_prepare,
        "repair_execution_evidence": repair_execution_evidence,
        "repair_execution_evidence_path": str(repair_execution_evidence_path),
        **({"writer_worker_handoff": writer_worker_handoff} if writer_worker_handoff is not None else {}),
        **({"writer_worker_handoff_path": writer_worker_handoff_path} if writer_worker_handoff_path is not None else {}),
        **(
            {
                "blocked_reason": None if writer_worker_handoff is not None else blocked_repair_reason,
                "next_owner": writer_handoff.NEXT_OWNER,
            }
            if blocked_repair_reason
            else {}
        ),
    }
    record_path = stable_quality_repair_batch_path(study_root=resolved_study_root)
    _write_json(record_path, record)
    return {
        "ok": bool(record["ok"]),
        "status": str(record["status"]),
        "record_path": str(record_path),
        **record,
    }
