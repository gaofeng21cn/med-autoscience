from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli.paper_mission_commands.common import (
    _first_mapping,
    _first_text,
    _mapping,
    _mapping_list,
    _optional_text,
    _parse_json_object,
    _stable_sha256,
)
from med_autoscience.cli.paper_mission_commands.route_back_budget import (
    NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS,
    _paper_mission_progress_refs_for_guard,
    _paper_mission_required_executor_delta_present,
    _paper_mission_route_back_budget_status,
    _paper_mission_route_request_progress_guard,
    _paper_mission_semantic_progress_signature_payload,
    _paper_mission_mas_owned_executor_stage_packet,
)
from med_autoscience.cli.paper_mission_commands.transaction_readback import (
    _consume_candidate_status_for_transaction_readback,
    _paper_mission_transaction_readback,
    _transaction_readback_output_fields,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_missing,
)
from med_autoscience.domain_route_profile import (
    DOMAIN_ID as DOMAIN_ROUTE_DOMAIN_ID,
    DOMAIN_ROUTE_TASK_KIND,
    build_domain_route_runtime_request,
)

PACKAGED_OPL_BIN = Path("/Users/gaofeng/Library/Application Support/OPL/runtime/current/bin/opl")
DEV_OPL_BIN = Path("/Users/gaofeng/workspace/one-person-lab/bin/opl")
PATH_OPL_BIN = "opl"
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
            "expected_command": (
                "opl family-runtime enqueue --domain medautoscience "
                "--task-kind domain_route/stage-route"
            ),
        }
    command = [
        selected_opl_bin,
        "family-runtime",
        "enqueue",
        "--domain",
        DOMAIN_ROUTE_DOMAIN_ID,
        "--task-kind",
        DOMAIN_ROUTE_TASK_KIND,
        "--payload",
        json.dumps(runtime_request["payload"], ensure_ascii=False, separators=(",", ":")),
        "--dedupe-key",
        runtime_request["dedupe_key"],
        "--priority",
        "100",
        "--source",
        "mas-domain-route",
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
    transaction_ref = _optional_text(payload.get("domain_route_transaction_ref"))
    command = [
        opl_bin,
        "family-runtime",
        "tick",
        "--source",
        "mas-domain-route-followthrough",
        "--hydrate",
        "--limit",
        "1",
        "--domain",
        DOMAIN_ROUTE_DOMAIN_ID,
        "--task-kind",
        DOMAIN_ROUTE_TASK_KIND,
    ]
    if transaction_ref is not None:
        command.extend(["--payload-match", f"domain_route_transaction_ref={transaction_ref}"])
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
    payload = build_domain_route_runtime_request(handoff)
    if payload is None:
        return None
    dedupe_key = _optional_text(_mapping(payload.get("route_identity")).get("dedupe_key"))
    if dedupe_key is None:
        return None
    return {
        "domainId": DOMAIN_ROUTE_DOMAIN_ID,
        "taskKind": DOMAIN_ROUTE_TASK_KIND,
        "dedupe_key": dedupe_key,
        "priority": 100,
        "source": "mas-domain-route",
        "payload": payload,
    }


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
