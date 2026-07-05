from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _first_mapping,
    _first_text,
    _mapping,
    _mapping_list,
    _optional_text,
    _parse_json_object,
    _stable_sha256,
)
from med_autoscience.cli_parts.paper_mission_command_parts.route_back_budget import (
    NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS,
    _paper_mission_progress_refs_for_guard,
    _paper_mission_required_executor_delta_present,
    _paper_mission_route_back_budget_status,
    _paper_mission_route_request_progress_guard,
    _paper_mission_semantic_progress_signature_payload,
    _paper_mission_mas_owned_executor_stage_packet,
)
from med_autoscience.cli_parts.paper_mission_command_parts.transaction_readback import (
    _consume_candidate_status_for_transaction_readback,
    _paper_mission_transaction_readback,
    _transaction_readback_output_fields,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_missing,
)

PACKAGED_OPL_BIN = Path("/Users/gaofeng/Library/Application Support/OPL/runtime/current/bin/opl")
DEV_OPL_BIN = Path("/Users/gaofeng/workspace/one-person-lab/bin/opl")
PATH_OPL_BIN = "opl"
PAPER_MISSION_STAGE_ROUTE_RUNTIME_REQUEST_VERSION = "user-stage-log-v2"
OPL_RUNTIME_TICK_FOLLOWTHROUGH_TIMEOUT_SECONDS = 15


def opl_runtime_submission_readback(
    *,
    handoff: Mapping[str, Any],
    submit_opl_runtime: bool,
    opl_bin: str | Path | None,
) -> dict[str, Any]:
    if not submit_opl_runtime:
        return {
            "status": "not_requested",
            "writes_runtime": False,
            "required_next_action": (
                "Submit opl_route_handoff to OPL DomainProgressTransitionRuntime "
                "through the legal OPL intake surface."
            ),
        }
    if _optional_text(handoff.get("handoff_status")) != "ready_for_opl_route_command":
        return {
            "status": "not_actionable",
            "writes_runtime": False,
            "reason": "opl_route_handoff_not_ready",
        }
    runtime_request = _opl_stage_route_runtime_request_from_handoff(handoff)
    if runtime_request is None:
        return {
            "status": "not_actionable",
            "writes_runtime": False,
            "reason": "opl_stage_route_runtime_request_not_materialized",
        }
    selected_opl_bin = _resolve_opl_bin(opl_bin)
    if selected_opl_bin is None:
        return {
            "status": "not_configured",
            "writes_runtime": False,
            "reason": "opl_bin_not_found",
            "expected_command": "opl family-runtime enqueue --domain medautoscience --task-kind paper_mission/stage-route",
        }
    command = [
        selected_opl_bin,
        "family-runtime",
        "enqueue",
        "--domain",
        "medautoscience",
        "--task-kind",
        "paper_mission/stage-route",
        "--payload",
        json.dumps(runtime_request["payload"], ensure_ascii=False, separators=(",", ":")),
        "--dedupe-key",
        runtime_request["dedupe_key"],
        "--priority",
        "100",
        "--source",
        "mas-paper-mission-drive",
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except OSError as exc:
        return {
            "status": "failed",
            "writes_runtime": False,
            "reason": "opl_enqueue_exec_failed",
            "error": str(exc),
            "opl_bin": selected_opl_bin,
            "command_preview": _opl_command_preview(command),
            "runtime_request_input": runtime_request,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "writes_runtime": False,
            "reason": "opl_enqueue_timeout",
            "error": str(exc),
            "opl_bin": selected_opl_bin,
            "command_preview": _opl_command_preview(command),
            "runtime_request_input": runtime_request,
        }
    parsed = _parse_json_object(completed.stdout)
    enqueue = _mapping(parsed.get("family_runtime_enqueue"))
    accepted = enqueue.get("accepted") is True
    idempotent_noop = enqueue.get("idempotent_noop") is True
    tick_readback = (
        _opl_runtime_tick_readback(
            opl_bin=selected_opl_bin,
            runtime_request=runtime_request,
        )
        if accepted or idempotent_noop
        else {}
    )
    return {
        "status": (
            "submitted"
            if accepted
            else "idempotent_noop"
            if idempotent_noop
            else "failed"
        ),
        "writes_runtime": bool(accepted or idempotent_noop),
        "writes_runtime_owner": "one-person-lab",
        "writes_mas_authority": False,
        "can_claim_opl_runtime_enqueued": False,
        "can_claim_opl_stage_run_created": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "opl_bin": selected_opl_bin,
        "command_preview": _opl_command_preview(command),
        "exit_code": completed.returncode,
        "runtime_request_input": runtime_request,
        "enqueue_readback": enqueue or parsed,
        **({"tick_readback": tick_readback} if tick_readback else {}),
        "stage_route_followthrough_attempted": bool(tick_readback),
        **({"stderr": completed.stderr.strip()} if completed.stderr.strip() else {}),
    }


def stage_closure_missing_runtime_submission(
    stage_closure_decision: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "status": "not_actionable",
        "writes_runtime": False,
        "reason": "stage_closure_decision_missing",
        "stage_closure_decision_ref": _mapping(stage_closure_decision).get("decision_ref"),
        "stage_closure_outcome": _mapping(
            _mapping(stage_closure_decision).get("outcome")
        ).get("kind"),
        "required_next_owner": "MedAutoScience.stage_closure_terminalizer",
        "required_next_action": "paper-mission terminalize-stage",
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
    }


def refresh_consume_readback_after_opl_submission(
    *,
    consume_readback: Mapping[str, Any],
    opl_runtime_submission: Mapping[str, Any],
) -> dict[str, Any]:
    if _optional_text(opl_runtime_submission.get("status")) not in {
        "submitted",
        "idempotent_noop",
    }:
        return dict(consume_readback)
    submission_source_transaction = _first_mapping(
        _mapping(consume_readback.get("stage_route_submission_source_transaction")),
        _mapping(consume_readback.get("candidate_source_transaction")),
        _mapping(consume_readback.get("paper_mission_transaction")),
    )
    transaction_readback = _paper_mission_transaction_readback(
        mission_id=_optional_text(consume_readback.get("mission_id"))
        or "paper-mission::unknown",
        study_id=_optional_text(consume_readback.get("study_id")) or "unknown_study",
        objective=_optional_text(consume_readback.get("objective"))
        or "PaperMission runtime followthrough readback",
        paper_mission_command="consume-candidate",
        study_root=Path(_optional_text(consume_readback.get("study_root")) or "."),
        mission=None,
        candidate=_optional_text(consume_readback.get("candidate_ref")),
        authority_consume_readback=_mapping(
            consume_readback.get("authority_consume_readback")
        ),
        transaction_override=_mapping(consume_readback.get("paper_mission_transaction")),
        transaction_source_override="paper_mission_consumption_ledger",
        enable_opl_live_probe=True,
        opl_bin=_optional_text(opl_runtime_submission.get("opl_bin")),
    )
    refreshed = dict(consume_readback)
    refreshed.update(_transaction_readback_output_fields(transaction_readback))
    refreshed["stage_route_submission_source_transaction"] = submission_source_transaction
    refreshed["consume_candidate_status"] = (
        _consume_candidate_status_for_transaction_readback(
            transaction_readback=transaction_readback,
            authority_consume_readback=_mapping(
                consume_readback.get("authority_consume_readback")
            ),
        )
    )
    return refreshed


def _opl_runtime_tick_readback(
    *,
    opl_bin: str,
    runtime_request: Mapping[str, Any],
) -> dict[str, Any]:
    payload = _mapping(runtime_request.get("payload"))
    transaction_ref = _optional_text(payload.get("paper_mission_transaction_ref"))
    study_id = _optional_text(payload.get("study_id"))
    command = [
        opl_bin,
        "family-runtime",
        "tick",
        "--source",
        "mas-paper-mission-drive-followthrough",
        "--hydrate",
        "--limit",
        "1",
        "--domain",
        "medautoscience",
        "--task-kind",
        "paper_mission/stage-route",
    ]
    if study_id is not None:
        command.extend(["--study", study_id])
    if transaction_ref is not None:
        command.extend(["--payload-match", f"paper_mission_transaction_ref={transaction_ref}"])
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=OPL_RUNTIME_TICK_FOLLOWTHROUGH_TIMEOUT_SECONDS,
        )
    except OSError as exc:
        return {
            "status": "failed",
            "reason": "opl_tick_exec_failed",
            "error": str(exc),
            "command_preview": _opl_command_preview(command),
            "can_claim_stage_run_created": False,
            "can_claim_provider_running": False,
            "can_claim_paper_progress": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "reason": "opl_tick_followthrough_timeout",
            "error": str(exc),
            "command_preview": _opl_command_preview(command),
            "followthrough_observation_window_seconds": (
                OPL_RUNTIME_TICK_FOLLOWTHROUGH_TIMEOUT_SECONDS
            ),
            "can_claim_stage_run_created": False,
            "can_claim_provider_running": False,
            "can_claim_paper_progress": False,
        }
    parsed = _parse_json_object(completed.stdout)
    tick = _mapping(parsed.get("family_runtime_tick"))
    dispatches = _mapping_list(tick.get("dispatches"))
    return {
        "status": "completed" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
        "command_preview": _opl_command_preview(command),
        "tick_readback": tick or parsed,
        "selected_count": tick.get("selected_count"),
        "dispatch_count": len(dispatches),
        "dispatch_statuses": [
            _optional_text(dispatch.get("status")) for dispatch in dispatches
        ],
        "can_claim_stage_run_created": any(
            _dispatch_started_stage_route_attempt(dispatch) for dispatch in dispatches
        ),
        "can_claim_provider_running": any(
            _dispatch_reports_provider_running(dispatch) for dispatch in dispatches
        ),
        "can_claim_paper_progress": False,
        **({"stderr": completed.stderr.strip()} if completed.stderr.strip() else {}),
    }


def _dispatch_started_stage_route_attempt(dispatch: Mapping[str, Any]) -> bool:
    if _optional_text(dispatch.get("status")) == "running":
        return True
    stage_run = _mapping(dispatch.get("stage_run_request"))
    return (
        stage_run.get("stage_run_created") is True
        or stage_run.get("provider_attempt_requested") is True
    )


def _dispatch_reports_provider_running(dispatch: Mapping[str, Any]) -> bool:
    if _optional_text(dispatch.get("status")) == "running":
        return True
    stage_run = _mapping(dispatch.get("stage_run_request"))
    return stage_run.get("provider_running") is True


def _resolve_opl_bin(opl_bin: str | Path | None) -> str | None:
    if opl_bin is not None:
        selected = Path(opl_bin).expanduser()
        if selected.exists():
            return str(selected.resolve())
        resolved = shutil.which(str(opl_bin))
        return resolved
    configured = os.environ.get("OPL_BIN") or os.environ.get("OPL_FAMILY_RUNTIME_BIN")
    if configured:
        selected = Path(configured).expanduser()
        if selected.exists():
            return str(selected.resolve())
        return shutil.which(configured)
    path_candidate = shutil.which(PATH_OPL_BIN)
    if path_candidate is not None:
        return path_candidate
    for candidate in (PACKAGED_OPL_BIN, DEV_OPL_BIN):
        if candidate.exists():
            return str(candidate.resolve())
    return None


def _opl_command_preview(command: list[str]) -> list[str]:
    preview = list(command)
    if "--payload" in preview:
        payload_index = preview.index("--payload") + 1
        if payload_index < len(preview):
            preview[payload_index] = "<json>"
    return preview


def _opl_stage_route_runtime_request_from_handoff(
    handoff: Mapping[str, Any],
) -> dict[str, Any] | None:
    study_id = _optional_text(handoff.get("study_id"))
    transaction_ref = _optional_text(handoff.get("paper_mission_transaction_ref"))
    route = _mapping(handoff.get("opl_route_command"))
    command_kind = _first_text(handoff.get("route_command_kind"), route.get("command_kind"))
    if not study_id or not transaction_ref or command_kind not in {
        "start_next_stage",
        "resume_stage",
        "route_back",
    }:
        return None
    workspace_root = _handoff_workspace_root(handoff)
    if workspace_root is None:
        return None
    route_identity_key = _optional_text(handoff.get("route_identity_key"))
    attempt_idempotency_key = _optional_text(handoff.get("attempt_idempotency_key"))
    request_idempotency_key = _optional_text(handoff.get("request_idempotency_key"))
    candidate_ref = _optional_text(handoff.get("candidate_ref"))
    candidate_hash = _paper_mission_candidate_ref_hash(candidate_ref)
    task_intake_ref = _mapping(handoff.get("task_intake_ref"))
    task_intake_summary = _mapping(handoff.get("task_intake_summary"))
    task_intake_kind = _optional_text(handoff.get("task_intake_kind")) or _optional_text(
        task_intake_summary.get("task_intake_kind")
    )
    owner_consumption_readback_ref = _optional_text(
        handoff.get("owner_consumption_readback_ref")
    )
    route_checkpoint_evidence_ref = _optional_text(
        handoff.get("route_checkpoint_evidence_ref")
    )
    carrier = _mapping(handoff.get("opl_runtime_carrier"))
    work_unit_id = _first_text(handoff.get("work_unit_id"), carrier.get("work_unit_id"))
    work_unit_fingerprint = _first_text(
        handoff.get("work_unit_fingerprint"),
        carrier.get("work_unit_fingerprint"),
    )
    if request_idempotency_key is None:
        return None
    identity_basis = request_idempotency_key
    advancing_delta_identity = _paper_mission_stage_route_advancing_delta_identity(
        handoff=handoff,
        command_kind=command_kind,
        candidate_ref=candidate_ref,
        candidate_hash=candidate_hash,
        owner_consumption_readback_ref=owner_consumption_readback_ref,
        route_checkpoint_evidence_ref=route_checkpoint_evidence_ref,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
    )
    advancing_delta_fingerprint = _stable_sha256(advancing_delta_identity)
    dedupe_key = ":".join(
        [
            "paper-mission-route",
            PAPER_MISSION_STAGE_ROUTE_RUNTIME_REQUEST_VERSION,
            study_id,
            identity_basis,
            command_kind,
            advancing_delta_fingerprint,
        ]
    )
    progress_guard = _paper_mission_route_request_progress_guard(handoff=handoff)
    user_stage_log = _paper_mission_stage_route_user_stage_log(
        handoff=handoff,
        progress_guard=progress_guard,
    )
    route_impact = {
        "decision": command_kind,
        "route_target": _first_text(handoff.get("route_target"), route.get("target")),
        "domain_ready_verdict": "domain_gate_pending",
        "progress_delta_classification": user_stage_log["progress_delta_classification"],
        "deliverable_progress_delta": user_stage_log["deliverable_progress_delta"],
        "platform_repair_delta": user_stage_log["platform_repair_delta"],
        "next_forced_delta": user_stage_log["next_forced_delta"],
        "remaining_blockers": list(user_stage_log["remaining_blockers"]),
        "evidence_refs": list(user_stage_log["evidence_refs"]),
        "user_stage_log": user_stage_log,
    }
    payload = {
        "surface_kind": "opl_mas_paper_mission_route_runtime_request",
        "schema_version": 1,
        "runtime_request_status": "queued_request",
        "runtime_request_kind": "mas_paper_mission_stage_route",
        "study_id": study_id,
        "mission_id": _optional_text(handoff.get("mission_id")),
        "candidate_ref": candidate_ref,
        "candidate_hash": candidate_hash,
        "task_intake_kind": task_intake_kind,
        "task_intake_ref": task_intake_ref or None,
        "task_intake_summary": task_intake_summary or None,
        "owner_consumption_readback_ref": owner_consumption_readback_ref,
        "route_checkpoint_evidence_ref": route_checkpoint_evidence_ref,
        "advancing_delta_fingerprint": advancing_delta_fingerprint,
        "advancing_delta_identity": advancing_delta_identity,
        "paper_mission_transaction_ref": transaction_ref,
        "opl_route_command_ref": _optional_text(handoff.get("opl_route_command_ref")),
        "route_identity_key": route_identity_key,
        "attempt_idempotency_key": attempt_idempotency_key,
        "request_idempotency_key": request_idempotency_key,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "idempotency_key": request_idempotency_key,
        "command_kind": command_kind,
        "route_target": _first_text(handoff.get("route_target"), route.get("target")),
        "workspace_root": workspace_root,
        "domain_workspace_root": workspace_root,
        "route_command_materialized": handoff.get("transaction_materialized") is True,
        "opl_route_command": route,
        "opl_route_handoff_record": dict(handoff),
        "semantic_progress_guard": progress_guard,
        "mas_owned_executor_stage": progress_guard.get("mas_owned_executor_stage"),
        "domain_ready_verdict": "domain_gate_pending",
        "route_impact": route_impact,
        "user_stage_log": user_stage_log,
        "stage_run_request": {
            "request_status": "requested",
            "requested_by": "mas_paper_mission_route_handoff",
            "domain_truth_owner": "med-autoscience",
            "runtime_owner": "one-person-lab",
            "command_kind": command_kind,
            "route_target": _first_text(handoff.get("route_target"), route.get("target")),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "stage_run_created": False,
            "provider_attempt_requested": False,
        },
        "authority_boundary": {
            "domain_truth_owner": "med-autoscience",
            "runtime_owner": "one-person-lab",
            "runtime_request_scope": "opl_queue_and_stage_route_request_only",
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_paper_body": False,
            "writes_runtime_queue": False,
            "writes_opl_queue": True,
            "writes_opl_outbox": True,
            "writes_opl_event": True,
            "writes_opl_stage_run": False,
            "writes_provider_attempt": False,
            "can_claim_opl_runtime_enqueued": False,
            "can_claim_opl_stage_run_created": False,
            "can_claim_provider_running": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
        },
    }
    return {
        "domainId": "medautoscience",
        "taskKind": "paper_mission/stage-route",
        "dedupe_key": dedupe_key,
        "priority": 100,
        "source": "mas-paper-mission-drive",
        "payload": payload,
    }


def _paper_mission_candidate_ref_hash(candidate_ref: str | None) -> str | None:
    if candidate_ref is None:
        return None
    path = Path(candidate_ref).expanduser()
    if not path.is_file():
        return None
    try:
        import hashlib

        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return f"sha256:{digest.hexdigest()}"


def _paper_mission_stage_route_advancing_delta_identity(
    *,
    handoff: Mapping[str, Any],
    command_kind: str,
    candidate_ref: str | None,
    candidate_hash: str | None,
    owner_consumption_readback_ref: str | None,
    route_checkpoint_evidence_ref: str | None,
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
) -> dict[str, Any]:
    consume_result = _mapping(
        _mapping(handoff.get("authority_consume_readback")).get("consume_result")
    )
    stage_terminal_decision = _mapping(handoff.get("stage_terminal_decision"))
    terminal_owner_gate = _mapping(handoff.get("terminal_owner_gate"))
    route = _mapping(handoff.get("opl_route_command"))
    task_intake_ref = _mapping(handoff.get("task_intake_ref"))
    task_intake_summary = _mapping(handoff.get("task_intake_summary"))
    return {
        "command_kind": command_kind,
        "route_target": _first_text(handoff.get("route_target"), route.get("target")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "candidate_ref": candidate_ref,
        "candidate_hash": candidate_hash,
        "task_intake_ref": _first_text(
            task_intake_ref.get("artifact_path"),
            task_intake_ref.get("task_id"),
        ),
        "task_intake_summary_fingerprint": (
            _stable_sha256(task_intake_summary)[:12] if task_intake_summary else None
        ),
        "owner_consumption_readback_ref": owner_consumption_readback_ref,
        "route_checkpoint_evidence_ref": route_checkpoint_evidence_ref,
        "owner_receipt_ref": _first_text(
            handoff.get("owner_receipt_ref"),
            handoff.get("domain_owner_receipt_ref"),
            consume_result.get("owner_receipt_ref"),
            consume_result.get("domain_owner_receipt_ref"),
        ),
        "typed_blocker_ref": _first_text(
            handoff.get("typed_blocker_ref"),
            terminal_owner_gate.get("typed_blocker_ref"),
            consume_result.get("typed_blocker_ref"),
        ),
        "human_gate_ref": _first_text(
            handoff.get("human_gate_ref"),
            terminal_owner_gate.get("human_gate_ref"),
            consume_result.get("human_gate_ref"),
        ),
        "route_back_evidence_ref": _first_text(
            handoff.get("route_back_evidence_ref"),
            stage_terminal_decision.get("route_back_evidence_ref"),
            terminal_owner_gate.get("route_back_evidence_ref"),
            consume_result.get("route_back_evidence_ref"),
        ),
        "paper_facing_delta_ref": _first_text(
            handoff.get("paper_facing_delta_ref"),
            consume_result.get("paper_facing_delta_ref"),
        ),
    }


def _paper_mission_stage_route_user_stage_log(
    *,
    handoff: Mapping[str, Any],
    progress_guard: Mapping[str, Any],
) -> dict[str, Any]:
    route = _mapping(handoff.get("opl_route_command"))
    study_id = _optional_text(handoff.get("study_id")) or "unknown-study"
    task_intake_ref = _mapping(handoff.get("task_intake_ref"))
    task_intake_summary = _mapping(handoff.get("task_intake_summary"))
    task_intake_kind = _optional_text(handoff.get("task_intake_kind")) or _optional_text(
        task_intake_summary.get("task_intake_kind")
    )
    command_kind = _first_text(
        handoff.get("route_command_kind"),
        route.get("command_kind"),
    ) or "paper_mission_stage_route"
    route_target = _first_text(handoff.get("route_target"), route.get("target"))
    candidate_ref = _optional_text(handoff.get("candidate_ref"))
    transaction_ref = _optional_text(handoff.get("paper_mission_transaction_ref"))
    route_back_ref = _first_text(
        handoff.get("route_back_evidence_ref"),
        _mapping(handoff.get("stage_terminal_decision")).get("route_back_evidence_ref"),
        _mapping(handoff.get("terminal_owner_gate")).get("route_back_evidence_ref"),
    )
    task_intake_artifact_path = _optional_text(task_intake_ref.get("artifact_path"))
    task_intake_intent = _optional_text(task_intake_summary.get("task_intent"))
    first_cycle_outputs = _string_list(task_intake_summary.get("first_cycle_outputs"))
    revision_checklist = _string_list(task_intake_summary.get("revision_checklist"))
    evidence_refs = [
        ref
        for ref in (
            candidate_ref,
            transaction_ref,
            _optional_text(handoff.get("opl_route_command_ref")),
            route_back_ref,
            _optional_text(handoff.get("source_ref")),
            task_intake_artifact_path,
        )
        if ref is not None
    ]
    remaining_blockers = [
        blocker
        for blocker in (
            _first_text(
                handoff.get("blocked_reason"),
                _mapping(handoff.get("stage_terminal_decision")).get("reason"),
                _mapping(handoff.get("terminal_owner_gate")).get("blocked_reason"),
                "paper_mission_stage_route_domain_gate_pending",
            ),
        )
        if blocker is not None
    ]
    changed_surfaces = [ref for ref in (candidate_ref,) if ref is not None]
    deliverable_delta_count = 1 if changed_surfaces else 0
    reviewer_revision = task_intake_kind == "reviewer_revision"
    if task_intake_intent is not None:
        stage_goal = (
            f"Execute the active {task_intake_kind or 'study'} scope for {study_id} "
            f"through the MAS canonical paper route. Scoped objective: "
            f"{task_intake_intent}"
        )
    else:
        stage_goal = (
            "Carry the PaperMission route command to OPL without claiming "
            "submission readiness, publication readiness, owner receipt, "
            "typed blocker, human gate, current package, or provider running."
        )
    if reviewer_revision:
        problem_summary = (
            "The latest reviewer_revision reactivated this study, but the current "
            "route still needs a paper-facing repair delta or a typed source-readiness "
            "blocker on the canonical paper surface."
        )
        next_forced_delta = "paper_facing_reviewer_revision_delta_or_typed_blocker"
    else:
        problem_summary = (
            "MAS PaperMission produced or consumed a submission milestone "
            "candidate, but the governed owner route remains at domain gate."
        )
        next_forced_delta = "domain_owner_answer_or_human_gate_or_non_synonymous_paper_delta"
    stage_work_done = [
        f"materialized {command_kind} request for {route_target or 'current stage'}",
        "preserved MAS/OPL authority boundary",
    ]
    if task_intake_intent is not None:
        stage_work_done.append("bound latest task_intake scope into the OPL route request")
    if first_cycle_outputs:
        stage_work_done.append(
            "recorded expected first-cycle outputs: " + "; ".join(first_cycle_outputs)
        )
    return {
        "surface_kind": "opl_user_stage_log",
        "schema_version": 1,
        "semantic_status": "provided_by_domain",
        "semantic_source": "med_autoscience.paper_mission_stage_route",
        "stage_name": f"PaperMission stage route for {study_id}",
        "problem_summary": problem_summary,
        "stage_goal": stage_goal,
        "progress_delta_classification": (
            "deliverable_progress" if deliverable_delta_count else "typed_blocker"
        ),
        "deliverable_progress_delta": {
            "delta_count": deliverable_delta_count,
            "delta_refs": changed_surfaces,
            "delta_summary": "non-authority paper-facing candidate refs routed",
        },
        "platform_repair_delta": {
            "delta_count": 0,
            "delta_refs": [],
            "delta_summary": None,
        },
        "next_forced_delta": next_forced_delta,
        "stage_work_done": stage_work_done,
        "changed_stage_surfaces": changed_surfaces,
        "outcome": "domain_gate_pending",
        "remaining_blockers": remaining_blockers,
        "evidence_refs": evidence_refs,
        "task_scope": {
            "task_intake_kind": task_intake_kind,
            "task_intake_ref": task_intake_ref or None,
            "task_intake_intent": task_intake_intent,
            "revision_checklist": revision_checklist,
            "first_cycle_outputs": first_cycle_outputs,
        },
        "authority_boundary": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "can_claim_paper_progress": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
            "can_claim_runtime_ready": False,
        },
        "semantic_progress_guard": {
            "signature": _optional_text(progress_guard.get("signature")),
            "status": _optional_text(progress_guard.get("status")),
            "guard_kind": _optional_text(progress_guard.get("guard_kind")),
        },
    }


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = _optional_text(item)
        if text is not None:
            result.append(text)
    return result


def semantic_progress_guard(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
    previous_guard: Mapping[str, Any] | None = None,
    route_back_budget_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    signature_payload = _paper_mission_semantic_progress_signature_payload(
        consume_readback=consume_readback,
        handoff=handoff,
    )
    signature = _stable_sha256(signature_payload)
    previous_signature = _optional_text(_mapping(previous_guard).get("signature"))
    semantic_progress_observed = (
        previous_signature is None or previous_signature != signature
    )
    has_required_delta = _paper_mission_required_executor_delta_present(
        consume_readback=consume_readback,
        handoff=handoff,
    )
    budget_status = _paper_mission_route_back_budget_status(
        signature=signature,
        signature_payload=signature_payload,
        ledger=route_back_budget_ledger,
        has_required_delta=has_required_delta,
    )
    status = (
        "semantic_progress_observed"
        if (semantic_progress_observed and not budget_status["budget_exhausted"])
        or has_required_delta
        else "non_advancing_route_back"
    )
    result = {
        "surface_kind": "paper_mission_semantic_progress_guard",
        "schema_version": 1,
        "status": status,
        "signature": signature,
        "previous_signature": previous_signature,
        "signature_payload": signature_payload,
        "progress_refs": _paper_mission_progress_refs_for_guard(
            consume_readback=consume_readback,
            handoff=handoff,
        ),
        "semantic_progress_observed": semantic_progress_observed,
        "required_executor_delta_present": has_required_delta,
        "route_back_budget": budget_status,
        "required_executor_outputs": list(NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS),
        "can_claim_paper_progress": False,
        "can_claim_submission_ready": False,
        "can_claim_runtime_ready": False,
    }
    if status == "non_advancing_route_back":
        executor_stage = _paper_mission_mas_owned_executor_stage_packet(
            signature=signature,
            signature_payload=signature_payload,
        )
        result.update(
            {
                "reason": (
                    "MAS observed a route-back/domain-gate handoff with the same "
                    "semantic progress signature and no new owner decision, "
                    "human gate, paper-facing delta, typed blocker, owner receipt, "
                    "or route-back evidence ref."
                ),
                "requires_mas_owned_executor_delta": True,
                "required_next_executor_stage": executor_stage["stage_type"],
                "mas_owned_executor_stage": executor_stage,
                "next_legal_actions": list(NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS),
                "stop_same_semantic_redrive": True,
                "owner_surface": "med-autoscience PaperMissionRun / MAS authority",
            }
        )
    return result


def drive_result_status(
    *,
    handoff_ready: bool,
    submission_status: str | None,
    runtime_status: str | None,
    carrier_readback: Mapping[str, Any],
) -> str:
    if runtime_status == "opl_runtime_attempt_running_observed":
        return "opl_stage_route_running"
    if runtime_status == "opl_runtime_terminal_readback_observed":
        gate = _mapping(carrier_readback.get("terminal_closeout"))
        if _optional_text(gate.get("gate_kind")) == "human_gate":
            return "waiting_for_human_gate"
        return "opl_terminal_closeout_observed"
    if submission_status in {"submitted", "idempotent_noop"}:
        return "submitted_to_opl_runtime"
    if submission_status in {"not_configured", "failed", "timeout", "not_actionable"}:
        return "opl_runtime_submission_failed"
    return "waiting_for_owner_resolution" if not handoff_ready else "opl_runtime_submission_pending"


def _handoff_workspace_root(handoff: Mapping[str, Any]) -> str | None:
    explicit = _first_text(
        handoff.get("domain_workspace_root"),
        handoff.get("workspace_root"),
        handoff.get("repo_root"),
    )
    if explicit is not None:
        return str(Path(explicit).expanduser().resolve())
    for key in ("candidate_ref", "source_ref"):
        ref = _optional_text(handoff.get(key))
        if ref is None:
            continue
        resolved = _workspace_root_from_ops_ref(ref)
        if resolved is not None:
            return str(resolved)
    return None


def _workspace_root_from_ops_ref(ref: str) -> Path | None:
    path = Path(ref).expanduser()
    if not path.is_absolute():
        return None
    parts = path.parts
    for index in range(0, len(parts) - 1):
        if parts[index : index + 2] == ("ops", "medautoscience"):
            if index == 0:
                return None
            return Path(*parts[:index]).resolve()
    return None


__all__ = [
    "drive_result_status",
    "opl_runtime_submission_readback",
    "refresh_consume_readback_after_opl_submission",
    "semantic_progress_guard",
    "stage_closure_missing_runtime_submission",
]
