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
METHODOLOGY_REFRAME_DECISION_OPTIONS = (
    "stop_loss_current_transport_claim",
    "provenance_limited_harmonization_audit",
    "rebuild_reproducible_model_route",
    "human_gate",
)
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
        "selected_route_option": "provenance_limited_harmonization_audit",
        "selected_next_work_unit": dict(METHODOLOGY_REFRAME_ANALYSIS_WORK_UNIT),
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
        "selected_next_work_unit": dict(METHODOLOGY_REFRAME_ANALYSIS_WORK_UNIT),
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
            "selected_route_option": "provenance_limited_harmonization_audit",
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
            "medical conclusion; route the same study to a provenance-limited harmonization audit and "
            "reproducible-model rebuild or stop-loss decision before manuscript work."
        ),
        route_target="analysis-campaign",
        route_key_question="Can DM002 continue as a valid external-validation paper without the original transported model provenance?",
        route_rationale=(
            "HDL/unit harmonization and transported Cox model provenance are unresolved; MAS must choose "
            "stop-loss, provenance-limited harmonization audit, reproducible-model rebuild, or human gate."
        ),
        source_route_key_question="methodology_reframe_required",
        work_unit_fingerprint="decision::methodology_reframe_route_decision",
        next_work_unit=dict(METHODOLOGY_REFRAME_ANALYSIS_WORK_UNIT),
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
            },
        ),
    )


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
