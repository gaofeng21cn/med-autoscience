from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.default_executor_closeout_contract import (
    default_executor_typed_closeout_contract,
)
from med_autoscience.controllers import domain_action_request_lifecycle
from med_autoscience.controllers.runtime_ai_repair_policy import (
    default_executor_policy,
    two_layer_ai_repair_policy_payload,
)
from med_autoscience.controllers.domain_action_request_materializer_parts import (
    writer_handoff_preservation,
)
from med_autoscience.controllers.domain_owner_action_dispatch_parts import output_readiness
from med_autoscience.controllers.owner_route_reconcile import SUPERVISION_LATEST_RELATIVE_PATH
from med_autoscience.developer_supervisor_mode import resolve_developer_supervisor_mode
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.runtime_control import owner_route_attempt_protocol
from med_autoscience.runtime_control import repeat_suppression
from med_autoscience.runtime_protocol import domain_authority_refs_index


SCHEMA_VERSION = 1
CONSUMER_LATEST_RELATIVE_PATH = Path("artifacts/supervision/consumer/latest.json")
CONSUMER_HISTORY_RELATIVE_PATH = Path("artifacts/supervision/consumer/history.jsonl")
DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT = Path(
    "artifacts/supervision/consumer/default_executor_dispatches"
)
SUPPORTED_REQUEST_ACTION_TYPES = frozenset(
    {
        "publication_gate_specificity_required",
        "current_package_freshness_required",
        "artifact_display_surface_materialization_required",
        "return_to_ai_reviewer_workflow",
        "canonical_paper_inputs_rehydrate_required",
        "run_quality_repair_batch",
        "unit_harmonized_external_validation_rerun",
        "recover_transport_model_provenance",
        "methodology_reframe_route_decision",
        "provenance_limited_harmonization_audit",
    }
)
SUPPORTED_MODE = "developer_apply_safe"
FORBIDDEN_SURFACES = [
    "paper/**",
    "manuscript/**",
    "current_package/**",
    "paper/current_package/**",
    "manuscript/current_package/**",
    "src/med_autoscience/platform/**",
]
RETIRED_ABSENT_SURFACES = [
    "src/med_autoscience/runtime_transport/",
]
SOURCE_ACTION_REF_FIELDS = (
    "surface",
    "study_id",
    "quest_id",
    "action_type",
    "action_id",
    "reason",
    "owner",
    "request_owner",
    "recommended_owner",
    "authority",
    "required_output_surface",
    "next_work_unit",
    "work_unit_fingerprint",
    "route_target",
    "route_key_question",
    "route_rationale",
    "source_ref",
    "stale_record_ref",
    "required_currentness_refs",
    "record_only_surface",
    "publication_eval_latest_write_allowed",
    "controller_decision_write_allowed",
    "terminal_source_provenance_blocker",
    "hard_methodology_target",
)
SOURCE_HANDOFF_REF_FIELDS = (
    "surface",
    "request_kind",
    "authority",
    "owner",
    "request_owner",
    "recommended_owner",
    "next_executable_owner",
    "required_output_surface",
    "next_work_unit",
    "work_unit_fingerprint",
    "route_target",
    "route_key_question",
    "route_rationale",
    "source_ref",
    "terminal_source_provenance_blocker",
    "hard_methodology_target",
)
RUNTIME_COMPLETION_SOURCE_ACTION_FIELDS = frozenset(
    {
        "provider_completion",
        "running_worker",
        "queue_status",
        "retry_budget_remaining",
        "domain_completion",
        "stage_state",
        "provider_completion_is_domain_completion",
        "provider_completion_is_stage_state",
        "queue_succeeded_is_domain_completion",
        "retry_budget_is_domain_completion",
        "running_worker_is_stage_state",
    }
)
ALLOWED_WRITE_SURFACES = [
    "artifacts/supervision/consumer/latest.json",
    "artifacts/supervision/consumer/history.jsonl",
    "studies/<study_id>/artifacts/supervision/consumer/publication_gate_specificity_required.json",
    "studies/<study_id>/artifacts/supervision/consumer/current_package_freshness_required.json",
    "studies/<study_id>/artifacts/supervision/consumer/artifact_display_surface_materialization_required.json",
    "studies/<study_id>/artifacts/supervision/consumer/return_to_ai_reviewer_workflow.json",
    "studies/<study_id>/artifacts/supervision/consumer/canonical_paper_inputs_rehydrate_required.json",
    "studies/<study_id>/artifacts/supervision/consumer/run_quality_repair_batch.json",
    "studies/<study_id>/artifacts/supervision/consumer/unit_harmonized_external_validation_rerun.json",
    "studies/<study_id>/artifacts/supervision/consumer/recover_transport_model_provenance.json",
    "studies/<study_id>/artifacts/supervision/consumer/methodology_reframe_route_decision.json",
    "studies/<study_id>/artifacts/supervision/consumer/provenance_limited_harmonization_audit.json",
    "studies/<study_id>/artifacts/supervision/consumer/default_executor_dispatches/*.json",
    "studies/<study_id>/artifacts/supervision/requests/ai_reviewer/latest.json",
]
MERGE_CLEANUP_CHECKLIST = [
    "focused pytest green",
    "git diff --check green",
    "review diff touches only owned files",
    "merge branch into main after parallel worker coordination",
    "remove worktree after absorb",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def _request_packet_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path:
    if action_type not in SUPPORTED_REQUEST_ACTION_TYPES:
        raise ValueError(f"unsupported supervisor request action_type: {action_type}")
    return _study_root(profile, study_id) / "artifacts" / "supervision" / "consumer" / f"{action_type}.json"


def _default_executor_dispatch_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path:
    return _study_root(profile, study_id) / DEFAULT_EXECUTOR_DISPATCH_RELATIVE_ROOT / f"{action_type}.json"


def _scan_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_LATEST_RELATIVE_PATH


def _consumer_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_LATEST_RELATIVE_PATH


def _consumer_history_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_HISTORY_RELATIVE_PATH


def _current_scan_study(scan_payload: Mapping[str, Any], study_id: str) -> dict[str, Any] | None:
    for study in scan_payload.get("studies") or []:
        payload = _mapping(study)
        if _text(payload.get("study_id")) == study_id:
            return payload
    return None


def _required_output_pending(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    current_study: Mapping[str, Any] | None,
) -> bool:
    return output_readiness.required_output_pending(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        current_study=current_study,
    )


def _github_block_reason(developer_mode_payload: Mapping[str, Any]) -> str | None:
    if text := _text(developer_mode_payload.get("blocked_reason")):
        return text
    gate = _mapping(developer_mode_payload.get("github_user_gate"))
    if text := _text(gate.get("reason")):
        return text
    if _text(developer_mode_payload.get("mode")) != SUPPORTED_MODE:
        return "developer_apply_safe_required"
    return None


def _request_owner_for_action_type(action_type: str) -> str:
    if action_type == "publication_gate_specificity_required":
        return "publication_gate"
    if action_type == "current_package_freshness_required":
        return "artifact_os"
    if action_type == "artifact_display_surface_materialization_required":
        return "artifact_os"
    if action_type == "return_to_ai_reviewer_workflow":
        return "ai_reviewer"
    if action_type == "canonical_paper_inputs_rehydrate_required":
        return "write"
    if action_type == "run_quality_repair_batch":
        return "write"
    if action_type == "unit_harmonized_external_validation_rerun":
        return "analysis_harmonization_owner"
    if action_type == "recover_transport_model_provenance":
        return "source_provenance_owner"
    if action_type == "methodology_reframe_route_decision":
        return "decision"
    if action_type == "provenance_limited_harmonization_audit":
        return "provenance_limited_harmonization_owner"
    return "controller"


def _owner_from_action(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(handoff_packet.get("owner"))
        or _text(handoff_packet.get("request_owner"))
        or _text(handoff_packet.get("recommended_owner"))
        or _request_owner_for_action_type(action_type)
    )


def _request_output_surface_for_action_type(action_type: str) -> str:
    if action_type == "publication_gate_specificity_required":
        return "artifacts/publication_eval/latest.json"
    if action_type == "current_package_freshness_required":
        return "artifacts/controller/gate_clearing_batch/latest.json"
    if action_type == "artifact_display_surface_materialization_required":
        return "artifacts/controller/gate_clearing_batch/latest.json"
    if action_type == "return_to_ai_reviewer_workflow":
        return "artifacts/publication_eval/latest.json"
    if action_type == "canonical_paper_inputs_rehydrate_required":
        return "paper/medical_manuscript_blueprint_source.json"
    if action_type == "run_quality_repair_batch":
        return (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        )
    if action_type == "unit_harmonized_external_validation_rerun":
        return (
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        )
    if action_type == "recover_transport_model_provenance":
        return (
            "canonical transport model provenance bundle or "
            "typed blocker:transport_model_provenance_recovery_required"
        )
    if action_type == "methodology_reframe_route_decision":
        return (
            "controller route decision for a provenance-limited reframe, reproducible-model restart, "
            "stop-loss, or human gate"
        )
    if action_type == "provenance_limited_harmonization_audit":
        return (
            "provenance-limited harmonization audit or "
            "typed blocker:provenance_limited_harmonization_audit_required"
        )
    return "artifacts/supervision/requests"


def _request_packet_ref_for_action_type(action_type: str) -> str:
    if action_type == "publication_gate_specificity_required":
        return "artifacts/supervision/requests/publication_gate_specificity/latest.json"
    if action_type == "current_package_freshness_required":
        return "artifacts/supervision/requests/current_package_freshness/latest.json"
    if action_type == "artifact_display_surface_materialization_required":
        return "artifacts/supervision/requests/artifact_display_materialization/latest.json"
    if action_type == "return_to_ai_reviewer_workflow":
        return "artifacts/supervision/requests/ai_reviewer/latest.json"
    if action_type == "canonical_paper_inputs_rehydrate_required":
        return "artifacts/supervision/requests/canonical_paper_inputs_rehydrate/latest.json"
    if action_type == "run_quality_repair_batch":
        return "artifacts/supervision/requests/quality_repair_batch/latest.json"
    if action_type == "unit_harmonized_external_validation_rerun":
        return "artifacts/supervision/requests/analysis_harmonization/latest.json"
    if action_type == "recover_transport_model_provenance":
        return "artifacts/supervision/requests/source_provenance/latest.json"
    if action_type == "methodology_reframe_route_decision":
        return "artifacts/supervision/requests/decision/latest.json"
    if action_type == "provenance_limited_harmonization_audit":
        return "artifacts/supervision/requests/provenance_limited_harmonization/latest.json"
    return "artifacts/supervision/requests"


def _request_packet_ref_for_dispatch(action_type: str) -> str | None:
    if action_type in SUPPORTED_REQUEST_ACTION_TYPES:
        return _request_packet_ref_for_action_type(action_type)
    return None


def _source_action_ref(action: Mapping[str, Any]) -> dict[str, Any]:
    source_ref = {key: action[key] for key in SOURCE_ACTION_REF_FIELDS if key in action}
    handoff = _mapping(action.get("handoff_packet"))
    handoff_ref = {key: handoff[key] for key in SOURCE_HANDOFF_REF_FIELDS if key in handoff}
    if handoff_ref:
        source_ref["handoff_packet"] = handoff_ref
    return source_ref


def _required_output_surface(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("required_output_surface"))
        or _text(handoff_packet.get("required_output_surface"))
        or _request_output_surface_for_action_type(action_type)
    )


def _default_executor_forbidden_surfaces(owner_route: Mapping[str, Any]) -> list[str]:
    forbidden = list(FORBIDDEN_SURFACES)
    for item in _mapping(owner_route.get("owner_reason_contract")).get("forbidden_surfaces") or []:
        if (surface := _text(item)) is not None and surface not in forbidden:
            forbidden.append(surface)
    return forbidden


def _executor_prompt(
    *,
    action_type: str,
    study_id: str,
    next_executable_owner: str,
    required_output_surface: str,
) -> str:
    typed_closeout_contract = default_executor_typed_closeout_contract(action_type=action_type)
    return (
        "Use Codex CLI as the default MAS repair executor. "
        f"Handle action `{action_type}` for study `{study_id}` as owner `{next_executable_owner}`. "
        f"Read the referenced MAS durable truth surfaces and write only the owner-authorized output `{required_output_surface}` "
        "or the supervision handoff surfaces listed in this dispatch. Do not patch paper/current_package, "
        "manuscript/current_package, publication gates, or medical conclusions outside the owner workflow. "
        f"{typed_closeout_contract['terminal_output_instruction']}"
    )


def _default_executor_dispatch(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    action_type: str,
    next_executable_owner: str,
    required_output_surface: str,
    apply: bool,
    developer_mode_payload: Mapping[str, Any],
    scan_payload: Mapping[str, Any],
) -> dict[str, Any]:
    study_id = _text(action.get("study_id")) or "unknown-study"
    dispatch_path = _default_executor_dispatch_path(profile, study_id, action_type)
    executor_policy = default_executor_policy()
    owner_route = owner_route_part.ensure_owner_route_v2(
        _mapping(action.get("owner_route")) or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    )
    preserved_writer_handoff = writer_handoff_preservation.preserved_quality_repair_writer_handoff_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        action=action,
        dispatch_path=dispatch_path,
        owner_route=owner_route,
        apply=apply,
        forbidden_surfaces=FORBIDDEN_SURFACES,
    )
    if preserved_writer_handoff is not None:
        return preserved_writer_handoff
    idempotency_key = _text(owner_route.get("idempotency_key"))
    repeat_key = repeat_suppression.repeat_key(owner_route)
    typed_closeout_contract = default_executor_typed_closeout_contract(action_type=action_type)
    forbidden_surfaces = _default_executor_forbidden_surfaces(owner_route)
    prompt_contract = {
        "study_id": study_id,
        "quest_id": _text(action.get("quest_id")) or _text(_mapping(action.get("handoff_packet")).get("quest_id")),
        "action_type": action_type,
        "next_executable_owner": next_executable_owner,
        "required_output_surface": required_output_surface,
        "owner_route": owner_route or None,
        "owner_reason_contract": _mapping(owner_route.get("owner_reason_contract")) or None,
        "owner_route_attempt_protocol": _mapping(owner_route.get("owner_route_attempt_protocol")) or None,
        "owner_route_currentness_basis": _mapping(_mapping(owner_route.get("source_refs")).get("owner_route_currentness_basis")) or None,
        "idempotency_key": idempotency_key,
        "prompt_budget": {"max_prompt_tokens": 6000},
        "compact_evidence_packet_ref": f"artifacts/supervision/compact_evidence_packets/{action_type}.json",
        "do_not_repeat": True,
        "repeat_suppression_key": repeat_key,
        "request_packet_ref": _request_packet_ref_for_dispatch(action_type),
        "paper_progress_stall": _mapping(action.get("paper_progress_stall")) or None,
        "source_scan_latest": str(_scan_latest_path(profile)),
        "required_closeout_packet": typed_closeout_contract,
        "terminal_output_instruction": typed_closeout_contract["terminal_output_instruction"],
        "forbidden_surfaces": list(forbidden_surfaces),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
    dispatch_status = (
        "ready"
        if apply
        and _text(developer_mode_payload.get("mode")) == SUPPORTED_MODE
        and developer_mode_payload.get("safe_actions_enabled") is True
        and owner_route_part.route_allows_action(
            action={
                **dict(action),
                "next_executable_owner": next_executable_owner,
                "action_type": action_type,
            },
            owner_route=owner_route,
        )
        else "dry_run" if not apply else "blocked"
    )
    blocked_reason = _default_executor_dispatch_blocked_reason(
        dispatch_status=dispatch_status,
        developer_mode_payload=developer_mode_payload,
        action=action,
        action_type=action_type,
        next_executable_owner=next_executable_owner,
        owner_route=owner_route,
    )
    current_study = _current_scan_study(scan_payload, study_id)
    repeat_guard = repeat_suppression.dispatch_repeat_suppression(
        dispatch={"prompt_contract": prompt_contract, "owner_route": owner_route, "dispatch_status": dispatch_status},
        current_study=current_study,
        existing_dispatch=_read_json_object(dispatch_path),
        required_output_pending=_required_output_pending(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            current_study=current_study,
        ),
    )
    if dispatch_status == "ready" and repeat_guard["repeat_suppressed"]:
        dispatch_status = "repeat_suppressed"
        blocked_reason = repeat_suppression.REPEAT_SUPPRESSED_REASON
    dispatch_shell = {
        "action_type": action_type,
        "next_executable_owner": next_executable_owner,
        "owner_route": owner_route or None,
        "prompt_contract": prompt_contract,
        "required_closeout_packet": typed_closeout_contract,
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "forbidden_surfaces": list(forbidden_surfaces),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
    }
    owner_route_attempt_envelope = owner_route_attempt_protocol.default_executor_attempt_envelope(
        dispatch=dispatch_shell
    )
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": SCHEMA_VERSION,
        **executor_policy,
        "study_id": study_id,
        "quest_id": prompt_contract["quest_id"],
        "action_type": action_type,
        "action_id": _text(action.get("action_id")),
        "next_executable_owner": next_executable_owner,
        "required_output_surface": required_output_surface,
        "owner_route": owner_route or None,
        "idempotency_key": idempotency_key,
        "repeat_suppression_key": repeat_key,
        "action_fingerprint": _text(action.get("action_fingerprint")),
        "paper_progress_stall": _mapping(action.get("paper_progress_stall")) or None,
        "dispatch_status": dispatch_status,
        "blocked_reason": blocked_reason,
        "repeat_suppressed": bool(repeat_guard["repeat_suppressed"]),
        "why_not_applied": repeat_guard["why_not_applied"],
        "repeat_suppression": repeat_guard,
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "required_closeout_packet": typed_closeout_contract,
        "owner_route_attempt_envelope": owner_route_attempt_envelope,
        "terminal_output_instruction": typed_closeout_contract["terminal_output_instruction"],
        "default_executor_policy": executor_policy,
        "two_layer_ai_repair_policy": two_layer_ai_repair_policy_payload(),
        "prompt_contract": prompt_contract,
        "executor_prompt": _executor_prompt(
            action_type=action_type,
            study_id=study_id,
            next_executable_owner=next_executable_owner,
            required_output_surface=required_output_surface,
        ),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "source_action": _source_action_ref(action),
        "source_action_runtime_completion_fields_omitted": sorted(
            key for key in action if key in RUNTIME_COMPLETION_SOURCE_ACTION_FIELDS
        ),
        "refs": {
            "scan_latest": str(_scan_latest_path(profile)),
            "dispatch_path": str(dispatch_path),
        },
    }


def _default_executor_dispatch_blocked_reason(
    *,
    dispatch_status: str,
    developer_mode_payload: Mapping[str, Any],
    action: Mapping[str, Any],
    action_type: str,
    next_executable_owner: str,
    owner_route: Mapping[str, Any],
) -> str | None:
    if dispatch_status != "blocked":
        return None
    if reason := _github_block_reason(developer_mode_payload):
        return reason
    if owner_route_part.route_allows_action(
        action={
            **dict(action),
            "next_executable_owner": next_executable_owner,
            "action_type": action_type,
        },
        owner_route=owner_route,
    ):
        return None
    return "owner_route_next_owner_mismatch"


def _request_task(
    *,
    profile: WorkspaceProfile,
    action: Mapping[str, Any],
    developer_mode_payload: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any]:
    study_id = _text(action.get("study_id")) or "unknown-study"
    action_type = _text(action.get("action_type")) or "unknown_action"
    handoff_packet = _mapping(action.get("handoff_packet"))
    packet_path = _request_packet_path(profile, study_id, action_type)
    apply_allowed = (
        apply
        and _text(developer_mode_payload.get("mode")) == SUPPORTED_MODE
        and developer_mode_payload.get("safe_actions_enabled") is True
    )
    blocked_reason = None if apply_allowed or not apply else _github_block_reason(developer_mode_payload)
    authority = _text(action.get("authority")) or _text(handoff_packet.get("authority")) or "observability_only"
    request_owner = _owner_from_action(action, action_type)
    required_output_surface = _required_output_surface(action, action_type)
    request_packet_ref = _request_packet_ref_for_action_type(action_type)
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(action.get("owner_route")) or _mapping(handoff_packet.get("owner_route")))
    idempotency_key = _text(owner_route.get("idempotency_key"))
    owner_route_current = owner_route_part.route_allows_action(
        action={
            **dict(action),
            "next_executable_owner": request_owner,
            "action_type": action_type,
        },
        owner_route=owner_route,
    )
    if blocked_reason is None and apply and not owner_route_current:
        blocked_reason = "owner_route_next_owner_mismatch"
    dispatch_status = (
        "applied"
        if apply_allowed and owner_route_current
        else "dry_run" if not apply else "blocked"
    )
    owner_pickup = {
        "owner": request_owner,
        "state": "pending",
        "required_output_surface": required_output_surface,
        "owner_route": owner_route or None,
        "idempotency_key": idempotency_key,
        "request_packet_ref": request_packet_ref,
        "supervisor_authority_boundary": "request_only",
    }
    return {
        "surface": "supervisor_request_handoff_task",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "quest_id": _text(action.get("quest_id")) or _text(handoff_packet.get("quest_id")),
        "action_type": action_type,
        "action_id": _text(action.get("action_id")),
        "reason": _text(action.get("reason")) or _text(handoff_packet.get("reason")),
        "authority": authority,
        "request_owner": request_owner,
        "expected_owner": request_owner,
        "next_executable_owner": request_owner,
        "required_output_surface": required_output_surface,
        "request_packet_ref": request_packet_ref,
        "owner_pickup": owner_pickup,
        "owner_route": owner_route or None,
        "idempotency_key": idempotency_key,
        "owner_route_current": owner_route_current,
        "dispatch_status": dispatch_status,
        "blocked_reason": blocked_reason,
        "dry_run": not apply,
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "github_gate": dict(_mapping(developer_mode_payload.get("github_user_gate"))),
        "effective_mode": _text(developer_mode_payload.get("mode")),
        "requested_mode": _text(developer_mode_payload.get("requested_mode")),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "platform_code_mutation_allowed": False,
        "source_action": dict(action),
        "handoff_packet": {
            **handoff_packet,
            "surface": "supervisor_request_handoff_packet",
            "schema_version": SCHEMA_VERSION,
            "study_id": study_id,
            "quest_id": _text(action.get("quest_id")) or _text(handoff_packet.get("quest_id")),
            "request_kind": _text(handoff_packet.get("request_kind")) or action_type,
            "action_type": action_type,
            "authority": authority,
            "request_owner": request_owner,
            "expected_owner": request_owner,
            "next_executable_owner": request_owner,
            "required_output_surface": required_output_surface,
            "owner_route": owner_route or None,
            "idempotency_key": idempotency_key,
            "request_packet_ref": request_packet_ref,
            "owner_pickup": owner_pickup,
            "supervisor_authority_boundary": "request_only",
            "consumer_mutation_scope": "supervision_handoff_only",
            "consumer_does_not_mutate": [
                "paper",
                "manuscript",
                "current_package",
                "submission_minimal",
                "publication_eval",
                "medical_claims",
            ],
            "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
            "effective_mode": _text(developer_mode_payload.get("mode")),
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
            "platform_code_mutation_allowed": False,
        },
        "refs": {
            "scan_latest": str(_scan_latest_path(profile)),
            "request_packet_path": str(packet_path),
        },
    }


def _ignored_action(action: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "study_id": _text(action.get("study_id")),
        "action_type": _text(action.get("action_type")),
        "action_id": _text(action.get("action_id")),
        "reason": reason,
    }


def _selected_actions(
    *,
    scan_payload: Mapping[str, Any],
    study_ids: tuple[str, ...],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    request_selected: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    allowed_studies = set(study_ids)
    actions = _current_actions_for_studies(scan_payload=scan_payload, study_ids=study_ids)
    if not isinstance(actions, list):
        return request_selected, ignored
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        study_id = _text(action.get("study_id"))
        if study_id not in allowed_studies:
            ignored.append(_ignored_action(action, "study_not_requested"))
            continue
        action_type = _text(action.get("action_type"))
        if action_type in SUPPORTED_REQUEST_ACTION_TYPES:
            request_selected.append(dict(action))
            continue
        else:
            ignored.append(_ignored_action(action, "unsupported_action_type"))
            continue
    return request_selected, ignored


def _current_actions_for_studies(*, scan_payload: Mapping[str, Any], study_ids: tuple[str, ...]) -> list[dict[str, Any]] | None:
    if not study_ids:
        actions = scan_payload.get("action_queue")
        return list(actions) if isinstance(actions, list) else None
    per_study_actions: list[dict[str, Any]] = []
    requested = set(study_ids)
    for study in scan_payload.get("studies") or []:
        study_payload = _mapping(study)
        study_id = _text(study_payload.get("study_id"))
        if study_id not in requested:
            continue
        quest_id = _text(study_payload.get("quest_id"))
        for action in study_payload.get("action_queue") or []:
            if not isinstance(action, Mapping):
                continue
            payload = dict(action)
            payload["study_id"] = _text(payload.get("study_id")) or study_id
            if quest_id is not None:
                payload["quest_id"] = _text(payload.get("quest_id")) or quest_id
            per_study_actions.append(payload)
    if per_study_actions:
        return per_study_actions
    actions = scan_payload.get("action_queue")
    return list(actions) if isinstance(actions, list) else None


def _resolve_study_ids_from_scan(scan_payload: Mapping[str, Any], study_ids: Iterable[str]) -> tuple[str, ...]:
    explicit = tuple(study_id for item in study_ids if (study_id := _text(item)) is not None)
    if explicit:
        return explicit
    resolved: list[str] = []
    for action in scan_payload.get("action_queue") or []:
        if isinstance(action, Mapping) and (study_id := _text(action.get("study_id"))) is not None:
            resolved.append(study_id)
    for study in scan_payload.get("studies") or []:
        if isinstance(study, Mapping) and (study_id := _text(study.get("study_id"))) is not None:
            resolved.append(study_id)
    return tuple(dict.fromkeys(resolved))


def _ai_reviewer_request_refresh(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
) -> dict[str, Any] | None:
    study_root = _study_root(profile, study_id)
    request_path = domain_action_request_lifecycle.stable_ai_reviewer_request_path(study_root=study_root)
    packet = domain_action_request_lifecycle.read_ai_reviewer_request(study_root=study_root)
    if packet is None:
        return None
    refreshed = domain_action_request_lifecycle.ai_reviewer_request_with_latest_record(
        study_root=study_root,
        packet=packet,
    )
    changed = refreshed != packet
    if apply and changed:
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(
            json.dumps(refreshed, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return {
        "surface": "ai_reviewer_request_refresh",
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "request_path": str(request_path),
        "refresh_status": "refreshed" if changed else "unchanged",
        "written": bool(apply and changed),
        "publication_eval_record_ref": _text(refreshed.get("publication_eval_record_ref")),
        "attached_eval_id": _text(_mapping(refreshed.get("ai_reviewer_record")).get("eval_id")),
        "blocked_reason": _text(_mapping(refreshed.get("request_lifecycle")).get("blocked_reason")),
    }


def _ai_reviewer_request_refreshes(
    *,
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...],
    apply: bool,
) -> list[dict[str, Any]]:
    refreshes: list[dict[str, Any]] = []
    for study_id in study_ids:
        refresh = _ai_reviewer_request_refresh(profile=profile, study_id=study_id, apply=apply)
        if refresh is not None:
            refreshes.append(refresh)
    return refreshes


def materialize_domain_action_requests(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
) -> dict[str, Any]:
    generated_at = _utc_now()
    developer_mode = resolve_developer_supervisor_mode(
        profile=profile,
        requested_mode=mode,
        apply_safe_actions=apply,
        scheduler_owner="external_queue_consumer",
    )
    developer_mode_payload = developer_mode.to_dict()
    scan_payload = _read_json_object(_scan_latest_path(profile)) or {}
    resolved_study_ids = _resolve_study_ids_from_scan(scan_payload, study_ids)
    selected_request_actions, ignored_actions = _selected_actions(
        scan_payload=scan_payload,
        study_ids=resolved_study_ids,
    )
    request_tasks = [
        _request_task(
            profile=profile,
            action=action,
            developer_mode_payload=developer_mode_payload,
            apply=apply,
        )
        for action in selected_request_actions
    ]
    default_executor_dispatches = [
        _default_executor_dispatch(
            profile=profile,
            action=action,
            action_type=_text(action.get("action_type")) or "unknown_action",
            next_executable_owner=_owner_from_action(action, _text(action.get("action_type")) or "unknown_action"),
            required_output_surface=_required_output_surface(action, _text(action.get("action_type")) or "unknown_action"),
            apply=apply,
            developer_mode_payload=developer_mode_payload,
            scan_payload=scan_payload,
        )
        for action in selected_request_actions
    ]
    ai_reviewer_request_refreshes: list[dict[str, Any]] = []
    written_files: list[str] = []
    if apply and developer_mode.safe_actions_enabled:
        for dispatch in default_executor_dispatches:
            if _text(dispatch.get("dispatch_status")) != "ready":
                continue
            dispatch_path = Path(_mapping(dispatch.get("refs")).get("dispatch_path"))
            _write_json(dispatch_path, dispatch)
            dispatch["dispatch_id"] = f"dispatch::{_text(dispatch.get('study_id'))}::{_text(dispatch.get('action_type'))}"
            quest_root = profile.runtime_root / (_text(dispatch.get("quest_id")) or _text(dispatch.get("study_id")) or "")
            dispatch["domain_authority_ref_index"] = domain_authority_refs_index.record_dispatch_receipt(
                quest_root=quest_root,
                receipt=dispatch,
                receipt_path=dispatch_path,
                db_path=domain_authority_refs_index.workspace_authority_refs_index_path(profile.workspace_root),
            )
            _write_json(dispatch_path, dispatch)
            written_files.append(str(dispatch_path))
        for task in request_tasks:
            if _text(task.get("dispatch_status")) != "applied":
                continue
            packet_path = Path(_mapping(task.get("refs")).get("request_packet_path"))
            packet = _mapping(task.get("handoff_packet"))
            _write_json(packet_path, packet)
            written_files.append(str(packet_path))
        ai_reviewer_request_refreshes = _ai_reviewer_request_refreshes(
            profile=profile,
            study_ids=resolved_study_ids,
            apply=True,
        )
        for refresh in ai_reviewer_request_refreshes:
            if refresh.get("written") is True:
                written_files.append(str(refresh["request_path"]))
    else:
        ai_reviewer_request_refreshes = _ai_reviewer_request_refreshes(
            profile=profile,
            study_ids=resolved_study_ids,
            apply=False,
        )

    payload = {
        "surface": "domain_action_request_materializer",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "source_surface": str(_scan_latest_path(profile)),
        "dry_run": not apply,
        "requested_studies": list(resolved_study_ids),
        "requested_mode": mode,
        "effective_mode": developer_mode.mode,
        "github_gate": dict(developer_mode.github_user_gate),
        "developer_supervisor_mode": developer_mode_payload,
        "apply_allowed": bool(apply and developer_mode.safe_actions_enabled),
        "runtime_control_owner": "one-person-lab",
        "request_task_count": len(request_tasks),
        "request_tasks": request_tasks,
        "ai_reviewer_request_refresh_count": len(ai_reviewer_request_refreshes),
        "ai_reviewer_request_refreshes": ai_reviewer_request_refreshes,
        "default_executor_dispatch_count": len(default_executor_dispatches),
        "repeat_suppressed_count": sum(item.get("repeat_suppressed") is True for item in default_executor_dispatches),
        "default_executor_dispatches": default_executor_dispatches,
        "ignored_actions": ignored_actions,
        "two_layer_ai_repair_policy": two_layer_ai_repair_policy_payload(),
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
        "allowed_write_surfaces": list(ALLOWED_WRITE_SURFACES),
        "merge_cleanup_checklist": list(MERGE_CLEANUP_CHECKLIST),
        "written_files": written_files,
        "refs": {
            "latest_path": str(_consumer_latest_path(profile)),
            "history_path": str(_consumer_history_path(profile)),
        },
    }
    if apply and developer_mode.safe_actions_enabled:
        written_files.append(str(_consumer_latest_path(profile)))
        payload["written_files"] = written_files
        _write_json(_consumer_latest_path(profile), payload)
        _append_json_line(
            _consumer_history_path(profile),
            {
                "generated_at": generated_at,
                "study_ids": list(resolved_study_ids),
                "request_task_count": len(request_tasks),
                "ai_reviewer_request_refresh_count": len(ai_reviewer_request_refreshes),
                "written_files": list(written_files),
                "effective_mode": developer_mode.mode,
            },
        )
    return payload


__all__ = [
    "CONSUMER_LATEST_RELATIVE_PATH",
    "FORBIDDEN_SURFACES",
    "RETIRED_ABSENT_SURFACES",
    "SCHEMA_VERSION",
    "SUPPORTED_REQUEST_ACTION_TYPES",
    "materialize_domain_action_requests",
]
