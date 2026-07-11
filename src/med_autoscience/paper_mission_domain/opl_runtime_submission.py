from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_domain.common import (
    _first_mapping,
    _first_text,
    _mapping,
    _mapping_list,
    _optional_text,
    _parse_json_object,
    _stable_sha256,
)
from med_autoscience.paper_mission_domain.transaction_readback import (
    _consume_candidate_status_for_transaction_readback,
    _paper_mission_transaction_readback,
    _transaction_readback_output_fields,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_missing,
)
from med_autoscience.domain_route_profile import (
    build_domain_route_handoff_intake_readback,
)

PACKAGED_OPL_BIN = Path("/Users/gaofeng/Library/Application Support/OPL/runtime/current/bin/opl")
DEV_OPL_BIN = Path("/Users/gaofeng/workspace/one-person-lab/bin/opl")
PATH_OPL_BIN = "opl"
OPL_RUNTIME_DOMAIN_ID = "medautoscience"


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
                "Submit opl_route_handoff through OPL family-runtime attempt create "
                "with an explicit stage and typed workspace locator."
            ),
        }
    if _optional_text(handoff.get("handoff_status")) != "ready_for_opl_route_command":
        return {
            "status": "not_actionable",
            "writes_runtime": False,
            "reason": "opl_route_handoff_not_ready",
        }
    route_intake = build_domain_route_handoff_intake_readback(handoff)
    runtime_request = _mapping(route_intake.get("runtime_request"))
    if not runtime_request:
        blockers = _mapping_list(route_intake.get("blockers"))
        stage_blocker = next(
            (
                blocker
                for blocker in blockers
                if _optional_text(blocker.get("field"))
                == "declarative_target_stage_id"
            ),
            {},
        )
        stage_reason = _optional_text(stage_blocker.get("reason"))
        return {
            "status": "not_actionable",
            "writes_runtime": False,
            "reason": (
                "opl_stage_attempt_target_stage_mismatch"
                if stage_reason == "domain_route_stage_identity_mismatch"
                else "opl_stage_attempt_target_stage_missing"
                if stage_blocker
                else "opl_stage_route_runtime_request_not_materialized"
            ),
            "blockers": blockers,
        }
    stage_id = _optional_text(runtime_request.get("declarative_target_stage_id"))
    if stage_id is None:
        return {
            "status": "not_actionable",
            "writes_runtime": False,
            "reason": "opl_stage_attempt_target_stage_missing",
        }
    workspace_root = _handoff_workspace_root(handoff)
    if workspace_root is None:
        return {
            "status": "not_actionable",
            "writes_runtime": False,
            "reason": "opl_stage_attempt_workspace_locator_missing",
        }
    selected_opl_bin = _resolve_opl_bin(opl_bin)
    if selected_opl_bin is None:
        return {
            "status": "not_configured",
            "writes_runtime": False,
            "reason": "opl_bin_not_found",
            "expected_command": (
                "opl family-runtime attempt create --domain medautoscience "
                f"--stage {stage_id} --workspace-locator <json> --start --json"
            ),
        }
    route_identity = _mapping(runtime_request.get("route_identity"))
    command = [
        selected_opl_bin,
        "family-runtime",
        "attempt",
        "create",
        "--domain",
        OPL_RUNTIME_DOMAIN_ID,
        "--stage",
        stage_id,
        "--workspace-locator",
        json.dumps(
            {"workspace_root": workspace_root},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    ]
    action_id = _first_text(
        handoff.get("domain_action_id"),
        handoff.get("action_id"),
    )
    if action_id is not None:
        command.extend(["--action", action_id])
    source_fingerprint = _optional_text(route_identity.get("source_fingerprint"))
    if source_fingerprint is not None:
        command.extend(["--source-fingerprint", source_fingerprint])
    command.extend(["--require-stage-admission", "--start", "--json"])
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
            "reason": "opl_stage_attempt_create_exec_failed",
            "error": str(exc),
            "opl_bin": selected_opl_bin,
            "command_preview": _opl_command_preview(command),
            "stage_attempt_request_input": runtime_request,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "writes_runtime": False,
            "reason": "opl_stage_attempt_create_timeout",
            "error": str(exc),
            "opl_bin": selected_opl_bin,
            "command_preview": _opl_command_preview(command),
            "stage_attempt_request_input": runtime_request,
        }
    parsed = _parse_json_object(completed.stdout)
    attempt_surface = _mapping(parsed.get("family_runtime_stage_attempt"))
    attempt = _mapping(attempt_surface.get("attempt"))
    admission_gate = _mapping(attempt_surface.get("stage_launch_admission_gate"))
    idempotent_noop = attempt_surface.get("idempotent_noop") is True
    attempt_id = _optional_text(attempt.get("stage_attempt_id"))
    response_stage_id = _optional_text(attempt.get("stage_id"))
    admission_blocked = (
        _optional_text(admission_gate.get("status")) == "blocked"
        or _optional_text(attempt.get("status")) == "blocked"
    )
    readback_matches_request = response_stage_id == stage_id
    accepted = (
        completed.returncode == 0
        and attempt_id is not None
        and readback_matches_request
        and not admission_blocked
    )
    failure_reason = (
        "opl_stage_attempt_admission_blocked"
        if admission_blocked
        else "opl_stage_attempt_readback_stage_mismatch"
        if attempt_id is not None and not readback_matches_request
        else "opl_stage_attempt_create_failed"
    )
    return {
        "status": (
            "idempotent_noop"
            if accepted and idempotent_noop
            else "submitted"
            if accepted
            else "failed"
        ),
        **({"reason": failure_reason} if not accepted else {}),
        "writes_runtime": attempt_id is not None,
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
        "stage_attempt_request_input": runtime_request,
        "attempt_readback": attempt,
        "stage_launch_admission_gate": admission_gate,
        "temporal_start_readback": _mapping(attempt_surface.get("temporal_start")),
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
        transaction_source_override="authority_consume_readback",
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
    if "--workspace-locator" in preview:
        locator_index = preview.index("--workspace-locator") + 1
        if locator_index < len(preview):
            preview[locator_index] = "<json>"
    return preview


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
    "stage_closure_missing_runtime_submission",
]
