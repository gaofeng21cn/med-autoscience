from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_escalation_record import RuntimeEscalationRecordRef
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.study_decision_record import (
    StudyDecisionActionType,
    StudyDecisionCharterRef,
    StudyDecisionControllerAction,
    StudyDecisionPublicationEvalRef,
    StudyDecisionRecord,
    StudyDecisionType,
)


DECISION_REQUEST_RELATIVE_PATH = Path("artifacts/supervision/requests/decision/latest.json")
PUBLICATION_EVAL_LATEST_RELATIVE_PATH = Path("artifacts/publication_eval/latest.json")
TASK_INTAKE_LATEST_RELATIVE_PATH = Path("artifacts/controller/task_intake/latest.json")
SOURCE_PROVENANCE_LATEST_RELATIVE_PATH = Path("artifacts/controller/source_provenance/latest.json")
REBUILD_AUTHORIZATION_KIND = "methodology_rebuild_authorization"
METHODOLOGY_REFRAME_DECISION_OPTIONS = (
    "stop_loss_current_transport_claim",
    "provenance_limited_harmonization_audit",
    "rebuild_reproducible_model_route",
    "human_gate",
)
METHODOLOGY_REFRAME_CLEAN_REBUILD_WORK_UNIT = {
    "unit_id": "unit_harmonized_external_validation_rerun",
    "lane": "analysis-campaign",
    "summary": (
        "Human-gate authorization selected a clean reproducible-model rebuild after the terminal "
        "transported-model provenance blocker; define and execute a unit-harmonized external-validation rerun "
        "or produce an analysis-harmonization typed blocker before any manuscript claim work."
    ),
    "hard_methodology": True,
    "selected_route_option": "rebuild_reproducible_model_route",
    "terminal_source_provenance_blocker_consumed": True,
    "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
    "clean_reproducible_model_rebuild_authorized": True,
    "required_owner": "analysis_harmonization_owner",
    "required_next_work_unit": "unit_harmonized_external_validation_rerun",
    "typed_blocker": "unit_harmonized_rerun_required",
    "required_prior_owner_outputs": [
        "source_provenance_owner.recover_transport_model_provenance_or_typed_blocker",
        "task_intake.methodology_rebuild_authorization",
    ],
    "required_output": (
        "unit-harmonized external-validation rerun evidence or "
        "typed blocker:unit_harmonized_rerun_required"
    ),
    "route_options": list(METHODOLOGY_REFRAME_DECISION_OPTIONS),
}
METHODOLOGY_REFRAME_ANALYSIS_WORK_UNIT = {
    "unit_id": "provenance_limited_harmonization_audit",
    "lane": "analysis-campaign",
    "summary": (
        "Consume the terminal transported-model provenance blocker by materializing a provenance-limited "
        "harmonization audit and a reproducible-model rebuild or stop-loss route before any manuscript claim work."
    ),
    "hard_methodology": True,
    "selected_route_option": "provenance_limited_harmonization_audit",
    "terminal_source_provenance_blocker_consumed": True,
    "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
    "required_prior_owner_outputs": [
        "analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker",
        "source_provenance_owner.recover_transport_model_provenance_or_typed_blocker",
    ],
    "required_output": (
        "provenance-limited harmonization audit with either a reproducible-model rebuild route, "
        "a stop-loss record for the current transported claim, or a human-gate blocker"
    ),
    "route_options": list(METHODOLOGY_REFRAME_DECISION_OPTIONS),
}


def execute(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    study_root = profile.studies_root / study_id
    request_path = study_root / DECISION_REQUEST_RELATIVE_PATH
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    request = _request(study_id=study_id, dispatch=dispatch or {})
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "decision_owner.methodology_reframe_route_decision",
            "request_path": str(request_path),
            "controller_decision_ref": str(decision_path),
            "next_owner": "decision",
        }
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request["path"] = str(request_path)
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written_record = study_runtime_protocol.write_study_decision_record(
        study_root=study_root,
        record=_decision_record(
            study_root=study_root,
            study_id=study_id,
            request_path=request_path,
            dispatch=dispatch or {},
        ),
    )
    return {
        "execution_status": "executed",
        "blocked_reason": None,
        "owner_callable_surface": "decision_owner.methodology_reframe_route_decision",
        "next_owner": "decision",
        "owner_result": _owner_result(
            study_id=study_id,
            request_path=request_path,
            decision_path=decision_path,
            decision_id=written_record.decision_id,
        ),
        "request_path": str(request_path),
        "controller_decision_ref": str(decision_path),
    }


def _owner_result(*, study_id: str, request_path: Path, decision_path: Path, decision_id: str) -> dict[str, Any]:
    study_root = request_path.parents[4]
    route_selection = _route_selection(study_root=study_root)
    return {
        "surface": "methodology_reframe_decision_owner_result",
        "schema_version": 1,
        "generated_at": _utc_now(),
        "study_id": study_id,
        "owner": "decision",
        "work_unit": "methodology_reframe_route_decision",
        "status": "routed",
        "blocked_reason": "methodology_reframe_required",
        "request_path": str(request_path),
        "controller_decision_ref": str(decision_path),
        "controller_decision_id": decision_id,
        "next_owner": "decision",
        "route_decision": "bounded_analysis",
        "route_target": "analysis-campaign",
        "selected_route_option": route_selection["selected_route_option"],
        "selected_next_work_unit": dict(route_selection["next_work_unit"]),
        "route_selection_basis": route_selection["basis"],
        "route_options": list(METHODOLOGY_REFRAME_DECISION_OPTIONS),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "publication_eval_written": False,
        "controller_decision_written": True,
    }


def _request(*, study_id: str, dispatch: Mapping[str, Any]) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action"))
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    required_output_surface = _text(dispatch.get("required_output_surface")) or _text(
        prompt_contract.get("required_output_surface")
    )
    if required_output_surface is None:
        required_output_surface = (
            "controller route decision for a provenance-limited reframe, "
            "reproducible-model restart, stop-loss, or human gate"
        )
    study_root = _study_root_from_dispatch(dispatch=dispatch)
    route_selection = _route_selection(study_root=study_root) if study_root is not None else _default_route_selection()
    return {
        "surface": "supervisor_action_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")) or _text(prompt_contract.get("quest_id")) or study_id,
        "request_kind": "methodology_reframe_route_decision",
        "request_owner": "decision",
        "assigned_to": "decision",
        "status": "requested",
        "blocked_reason": "methodology_reframe_required",
        "next_owner": "decision",
        "next_work_unit": "methodology_reframe_route_decision",
        "selected_next_work_unit": dict(route_selection["next_work_unit"]),
        "required_output_surface": required_output_surface,
        "owner_route": owner_route,
        "idempotency_key": _text(dispatch.get("idempotency_key")) or _text(prompt_contract.get("idempotency_key")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint"))
        or _text(dispatch.get("repeat_suppression_key"))
        or _text(prompt_contract.get("repeat_suppression_key"))
        or "decision::methodology_reframe_route_decision",
        "source_action_ref": {
            "action_type": _text(dispatch.get("action_type")),
            "action_id": _text(dispatch.get("action_id")),
            "dispatch_authority": _text(dispatch.get("dispatch_authority")),
            "dispatch_path": _text(_mapping(dispatch.get("refs")).get("dispatch_path")),
            "source_ref": _text(source_action.get("source_ref")),
            "terminal_source_provenance_blocker": source_action.get("terminal_source_provenance_blocker") is True,
        },
        "decision_options": list(METHODOLOGY_REFRAME_DECISION_OPTIONS),
        "decision_contract": {
            "current_transport_claim_must_not_be_used_as_medical_conclusion": True,
            "allowed_route_options": list(METHODOLOGY_REFRAME_DECISION_OPTIONS),
            "quality_ready_verdict_allowed": False,
            "paper_surface_mutation_allowed": False,
        },
        "required_output": {
            "accepted_evidence": "controller route decision",
            "accepted_route_decision": "bounded_analysis",
            "selected_route_option": route_selection["selected_route_option"],
        },
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _decision_record(
    *,
    study_root: Path,
    study_id: str,
    request_path: Path,
    dispatch: Mapping[str, Any],
) -> StudyDecisionRecord:
    emitted_at = _utc_now()
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    quest_id = _text(dispatch.get("quest_id")) or _text(prompt_contract.get("quest_id")) or study_id
    route_selection = _route_selection(study_root=study_root)
    return StudyDecisionRecord(
        schema_version=1,
        decision_id=f"study-decision::{study_id}::{quest_id}::methodology_reframe_route_decision::{emitted_at}",
        study_id=study_id,
        quest_id=quest_id,
        emitted_at=emitted_at,
        decision_type=StudyDecisionType.BOUNDED_ANALYSIS,
        charter_ref=_charter_ref(study_root=study_root, study_id=study_id),
        runtime_escalation_ref=_runtime_escalation_ref(study_root=study_root, study_id=study_id, quest_id=quest_id),
        publication_eval_ref=_publication_eval_ref_or_placeholder(study_root=study_root),
        requires_human_confirmation=False,
        controller_actions=(
            StudyDecisionControllerAction(
                action_type=StudyDecisionActionType.ENSURE_STUDY_RUNTIME,
                payload_ref=str(request_path),
            ),
        ),
        reason=(
            "Terminal source-provenance blocker prevents using the current transported-model claim as a "
            "medical conclusion; route the same study through the selected methodology reframe path "
            "before manuscript work."
        ),
        route_target="analysis-campaign",
        route_key_question="Can DM002 continue as a valid external-validation paper without the original transported model provenance?",
        route_rationale=(
            f"HDL/unit harmonization and transported Cox model provenance are unresolved; MAS selected "
            f"{route_selection['selected_route_option']} using {route_selection['basis']}."
        ),
        source_route_key_question="methodology_reframe_required",
        work_unit_fingerprint="decision::methodology_reframe_route_decision",
        next_work_unit=dict(route_selection["next_work_unit"]),
        blocking_work_units=(
            {
                "unit_id": "recover_transport_model_provenance",
                "owner": "source_provenance_owner",
                "blocked_reason": "transport_model_provenance_recovery_required",
                "terminal_blocker_consumed": True,
            },
            {
                "unit_id": "methodology_reframe_route_decision",
                "owner": "decision",
                "blocked_reason": "methodology_reframe_required",
                "terminal_blocker_consumed": True,
                "route_options": list(METHODOLOGY_REFRAME_DECISION_OPTIONS),
                "selected_route_option": route_selection["selected_route_option"],
            },
        ),
    )


def _route_selection(*, study_root: Path) -> dict[str, Any]:
    if _rebuild_authorized(study_root=study_root) and _terminal_source_provenance_blocker(study_root=study_root):
        return {
            "selected_route_option": "rebuild_reproducible_model_route",
            "next_work_unit": dict(METHODOLOGY_REFRAME_CLEAN_REBUILD_WORK_UNIT),
            "basis": "human_gate_methodology_rebuild_authorization_and_terminal_source_provenance_blocker",
        }
    return _default_route_selection()


def _default_route_selection() -> dict[str, Any]:
    return {
        "selected_route_option": "provenance_limited_harmonization_audit",
        "next_work_unit": dict(METHODOLOGY_REFRAME_ANALYSIS_WORK_UNIT),
        "basis": "terminal_source_provenance_blocker_without_clean_rebuild_authorization",
    }


def _rebuild_authorized(*, study_root: Path) -> bool:
    task = _read_json_object(study_root / TASK_INTAKE_LATEST_RELATIVE_PATH) or {}
    return _text(task.get("task_intake_kind")) == REBUILD_AUTHORIZATION_KIND


def _terminal_source_provenance_blocker(*, study_root: Path) -> bool:
    source = _read_json_object(study_root / SOURCE_PROVENANCE_LATEST_RELATIVE_PATH) or {}
    provenance_search = _mapping(source.get("provenance_search"))
    return bool(
        _text(source.get("surface")) == "source_provenance_owner_result"
        and _text(source.get("owner")) == "source_provenance_owner"
        and _text(source.get("work_unit")) == "recover_transport_model_provenance"
        and _text(source.get("status")) == "blocked"
        and _text(source.get("blocked_reason")) == "transport_model_provenance_recovery_required"
        and source.get("transport_model_provenance_recovered") is not True
        and provenance_search.get("searched") is True
        and "accepted_bundle_ref" in provenance_search
        and not provenance_search.get("accepted_bundle_ref")
        and provenance_search.get("result_summary_acceptance_allowed") is False
        and provenance_search.get("substitute_refit_allowed") is False
    )


def _study_root_from_dispatch(*, dispatch: Mapping[str, Any]) -> Path | None:
    refs = _mapping(dispatch.get("refs"))
    path_text = _text(refs.get("dispatch_path"))
    if path_text is None:
        return None
    path = Path(path_text).expanduser().resolve()
    parts = path.parts
    try:
        studies_index = parts.index("studies")
    except ValueError:
        return None
    if len(parts) <= studies_index + 2:
        return None
    return Path(*parts[: studies_index + 2])


def _charter_ref(*, study_root: Path, study_id: str) -> StudyDecisionCharterRef:
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    charter_payload = _read_json_object(charter_path) or {}
    charter_id = _text(charter_payload.get("charter_id")) or f"charter::{study_id}::unknown"
    return StudyDecisionCharterRef(charter_id=charter_id, artifact_path=str(charter_path))


def _publication_eval_ref_or_placeholder(*, study_root: Path) -> StudyDecisionPublicationEvalRef:
    path = study_root / PUBLICATION_EVAL_LATEST_RELATIVE_PATH
    payload = _read_json_object(path) or {}
    return StudyDecisionPublicationEvalRef(
        eval_id=_text(payload.get("eval_id")) or "publication-eval-unavailable-for-methodology-reframe",
        artifact_path=str(path),
    )


def _runtime_escalation_ref(*, study_root: Path, study_id: str, quest_id: str) -> RuntimeEscalationRecordRef:
    artifact_path = study_root / "artifacts" / "runtime" / "escalation" / "methodology_reframe_required.json"
    summary_ref = study_root / "artifacts" / "runtime" / "escalation" / "methodology_reframe_required.md"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "record_id": f"runtime-escalation::{study_id}::methodology_reframe_required",
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": _utc_now(),
        "trigger": {
            "trigger_id": "methodology_reframe_required",
            "source": "runtime_supervisor_dispatch_executor",
        },
        "scope": "study_methodology",
        "severity": "blocking",
        "reason": "terminal source-provenance blocker requires controller route decision",
        "recommended_actions": list(METHODOLOGY_REFRAME_DECISION_OPTIONS),
        "evidence_refs": ["artifacts/controller/source_provenance/latest.json"],
        "runtime_context_refs": {
            "decision_request": str(study_root / DECISION_REQUEST_RELATIVE_PATH),
            "source_provenance_result": "artifacts/controller/source_provenance/latest.json",
        },
        "summary_ref": str(summary_ref),
        "artifact_path": str(artifact_path),
    }
    artifact_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not summary_ref.exists():
        summary_ref.write_text(
            "Methodology reframe required: terminal source-provenance blocker prevents current transported-model claim closure.\n",
            encoding="utf-8",
        )
    return RuntimeEscalationRecordRef.from_payload(payload)


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


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


__all__ = [
    "DECISION_REQUEST_RELATIVE_PATH",
    "METHODOLOGY_REFRAME_DECISION_OPTIONS",
    "execute",
]
