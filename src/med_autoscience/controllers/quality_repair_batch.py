from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import control_intent
from med_autoscience.controllers import gate_clearing_batch
from med_autoscience.controllers import gate_clearing_batch_blockers
from med_autoscience.controllers import gate_clearing_batch_currentness
from med_autoscience.controllers import publication_work_units
from med_autoscience.controllers import study_runtime_router
from med_autoscience.controllers.gate_clearing_batch_work_units import UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS
from med_autoscience.controllers.control_plane_route_gate import assert_control_plane_route_authorized
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_eval_latest import read_publication_eval_latest
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


def stable_quality_repair_batch_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / STABLE_QUALITY_REPAIR_BATCH_RELATIVE_PATH


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
    return {"control_plane_snapshot": dict(control_plane_snapshot)}


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
    source_eval_id: str | None,
) -> dict[str, Any] | None:
    publication_work_unit_payload = publication_work_units.derive_publication_work_units(dict(gate_report))
    next_work_unit = publication_work_unit_payload.get("next_work_unit")
    if not isinstance(next_work_unit, Mapping):
        return None
    work_unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    if work_unit_id not in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS:
        return None
    return {
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
            "work_unit_id": work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": source_eval_id,
            "gate_fingerprint": _non_empty_text(gate_report.get("gate_fingerprint")),
            "work_unit_fingerprint": _non_empty_text(publication_work_unit_payload.get("fingerprint")),
        }
    }


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


def _merge_route_contexts(*contexts: Mapping[str, Any] | None) -> dict[str, Any] | None:
    merged: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, Mapping):
            merged.update(dict(context))
    return merged or None


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
    if not summary_payload or not _quality_repair_required(summary_payload):
        return None

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

    candidates = _repair_candidates(
        profile=profile,
        study_root=resolved_study_root,
        quest_id=quest_id,
        gate_report=gate_report,
        include_downstream_delivery=not bool(gate_report.get("bundle_tasks_downstream_only")),
    )
    if not candidates:
        return None

    publication_work_unit_payload = publication_work_units.derive_publication_work_units(gate_report)
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
        "blocking_artifact_refs": gate_report.get("blocking_artifact_refs") or [],
        "blocking_work_units": publication_work_unit_payload.get("blocking_work_units") or [],
        "next_work_unit": publication_work_unit_payload.get("next_work_unit"),
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
    resolved_route_context = (
        control_plane_route_context
        or route_context
        or _runtime_control_plane_route_context(
            profile=profile,
            study_id=study_id,
            study_root=resolved_study_root,
        )
    )
    publication_eval_payload = read_publication_eval_latest(study_root=resolved_study_root)
    current_eval_id = _non_empty_text(publication_eval_payload.get("eval_id"))
    quest_root = profile.managed_runtime_quests_root / quest_id
    gate_state = gate_clearing_batch.publication_gate.build_gate_state(quest_root)
    gate_report = gate_clearing_batch.publication_gate.build_gate_report(gate_state)
    controller_route_context = _controller_route_context_for_gate(
        gate_report=gate_report,
        source_eval_id=current_eval_id,
    )
    if controller_route_context is None:
        controller_route_context = _controller_route_context_for_publication_work_unit(
            gate_report=gate_report,
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
    summary_payload = _read_quality_summary(study_root=resolved_study_root)
    quality_closure_truth, quality_execution_lane = _quality_repair_context(summary_payload)
    source_summary_id = _non_empty_text(summary_payload.get("summary_id"))
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
    gate_clearing_execution_summary = (
        dict(gate_clearing_result.get("execution_summary"))
        if isinstance(gate_clearing_result.get("execution_summary"), Mapping)
        else None
    )
    record = {
        "schema_version": SCHEMA_VERSION,
        "source_eval_id": current_eval_id,
        "source_eval_artifact_path": str(
            (resolved_study_root / "artifacts" / "publication_eval" / "latest.json").resolve()
        ),
        "source_summary_id": source_summary_id,
        "source_summary_artifact_path": str(_quality_summary_path(study_root=resolved_study_root).resolve()),
        "status": _non_empty_text(gate_clearing_result.get("status")) or "executed",
        "ok": bool(gate_clearing_result.get("ok")),
        "quest_id": quest_id,
        "study_id": study_id,
        "quality_closure_state": _non_empty_text(quality_closure_truth.get("state")),
        "quality_execution_lane_id": _non_empty_text(quality_execution_lane.get("lane_id")),
        "gate_clearing_batch": gate_clearing_result,
        "gate_clearing_execution_summary": gate_clearing_execution_summary,
        "control_plane_route_gate": control_plane_route_gate,
    }
    record_path = stable_quality_repair_batch_path(study_root=resolved_study_root)
    _write_json(record_path, record)
    return {
        "ok": bool(record["ok"]),
        "status": str(record["status"]),
        "record_path": str(record_path),
        **record,
    }
