from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli.paper_mission_commands.common import (
    _compact_non_null_mapping,
    _first_text,
    _mapping,
    _optional_text,
    _stable_sha256,
)
from med_autoscience.cli.paper_mission_commands.opl_runtime_submission import (
    drive_result_status as _paper_mission_drive_result_status,
)
from med_autoscience.cli.paper_mission_commands.route_back_budget import (
    _paper_mission_mas_owned_executor_stage_packet,
)
from med_autoscience.cli.paper_mission_output_roots import (
    PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH,
    PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH,
    YANG_WORKSPACE_ROOT,
    _is_under_yang_workspace,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_missing,
)

DEFAULT_PAPER_MISSION_DRIVE_FOLLOWTHROUGH_LIMIT = 2


def paper_mission_drive_followthrough_empty(
    *,
    route_back_budget_ledger: Mapping[str, Any],
    route_back_budget_ledger_ref: Path,
    progress_guard: Mapping[str, Any],
    stage_closure_decision: Mapping[str, Any],
    stop_reason: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "paper_mission_drive_followthrough_readback",
        "schema_version": 1,
        "attempted": False,
        "round_count": 0,
        "max_rounds": DEFAULT_PAPER_MISSION_DRIVE_FOLLOWTHROUGH_LIMIT,
        "rounds": [],
        "stop_reason": stop_reason,
        "semantic_progress_guard": dict(progress_guard),
        "stage_closure_decision": dict(stage_closure_decision),
        "stage_closure_decision_ref": _mapping(stage_closure_decision).get(
            "decision_ref"
        ),
        "stage_closure_outcome": _mapping(
            _mapping(stage_closure_decision).get("outcome")
        ).get("kind"),
        "non_advancing_route_back": None,
        "route_back_budget_ledger": dict(route_back_budget_ledger),
        "route_back_budget_ledger_ref": str(route_back_budget_ledger_ref),
        "mas_owned_executor_delta": None,
        "mas_owned_executor_stage": None,
        "requires_mas_owned_executor_delta": False,
        "final_drive_result": {
            "status": stop_reason,
            "stage_closure_decision_ref": _mapping(stage_closure_decision).get(
                "decision_ref"
            ),
            "stage_closure_outcome": _mapping(
                _mapping(stage_closure_decision).get("outcome")
            ).get("kind"),
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "authority_materialized": False,
        },
        "authority_boundary": {
            "mas_authority_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "writes_authority": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_runtime_queue": False,
            "writes_opl_queue": False,
            "writes_opl_outbox": False,
            "writes_provider_attempt": False,
        },
    }


def paper_mission_mas_owned_executor_delta_checkpoint(
    *,
    package_readback: Mapping[str, Any],
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
    progress_guard: Mapping[str, Any],
) -> dict[str, Any] | None:
    output_manifest = _mapping(package_readback.get("output_manifest"))
    owner_decision_packet_ref = _optional_text(
        output_manifest.get("owner_decision_packet_ref")
    )
    paper_facing_delta_ref = _optional_text(
        output_manifest.get("paper_facing_candidate_delta_ref")
    )
    if owner_decision_packet_ref is None and paper_facing_delta_ref is None:
        return None
    decision = _mapping(consume_readback.get("stage_terminal_decision"))
    next_decision = _mapping(consume_readback.get("next_owner_or_human_decision"))
    next_owner = _first_text(
        decision.get("next_owner"),
        handoff.get("next_owner"),
        next_decision.get("next_owner"),
    )
    if next_owner != "mission_executor":
        return None
    runtime_status = _optional_text(consume_readback.get("opl_runtime_readback_status"))
    if runtime_status not in {
        "waiting_for_opl_runtime_live_readback",
        "opl_runtime_readback_missing",
        None,
    }:
        return None
    signature = _optional_text(progress_guard.get("signature")) or _stable_sha256(
        _mapping(progress_guard.get("signature_payload"))
    )
    signature_payload = _mapping(progress_guard.get("signature_payload")) or {
        "study_id": _optional_text(consume_readback.get("study_id")),
        "mission_id": _optional_text(consume_readback.get("mission_id")),
        "paper_mission_transaction_ref": _optional_text(
            handoff.get("paper_mission_transaction_ref")
        ),
        "route_command": _first_text(
            handoff.get("route_command_kind"),
            _mapping(consume_readback.get("opl_route_command")).get("command_kind"),
        ),
        "route_target": _first_text(
            handoff.get("route_target"),
            _mapping(consume_readback.get("opl_route_command")).get("target"),
        ),
    }
    produced_outputs = _compact_non_null_mapping(
        {
            "owner_decision_packet_ref": owner_decision_packet_ref,
            "paper_facing_delta_ref": paper_facing_delta_ref,
            "owner_consumption_request_ref": _optional_text(
                output_manifest.get("owner_consumption_request_ref")
            ),
            "owner_blocker_packet_ref": _optional_text(
                output_manifest.get("owner_blocker_packet_ref")
            ),
            "submission_milestone_checklist_ref": _optional_text(
                output_manifest.get("submission_milestone_checklist_ref")
            ),
            "package_manifest_ref": _optional_text(
                output_manifest.get("package_manifest_ref")
            ),
            "consume_readback_ref": _optional_text(
                _mapping(consume_readback.get("consume_output_manifest")).get(
                    "consume_readback_ref"
                )
            ),
        }
    )
    return {
        "surface_kind": "paper_mission_mas_owned_executor_delta_checkpoint",
        "schema_version": 1,
        "status": "mas_owned_executor_delta_ready",
        "owner": "MedAutoScience",
        "executor": "Codex CLI",
        "trigger": "opl_runtime_live_readback_missing_after_candidate_materialization",
        "next_owner": "mission_executor",
        "semantic_progress_signature": signature,
        "semantic_progress_signature_payload": signature_payload,
        "mas_owned_executor_stage": _paper_mission_mas_owned_executor_stage_packet(
            signature=signature,
            signature_payload=signature_payload,
        ),
        "produced_outputs": produced_outputs,
        "stop_same_semantic_redrive": True,
        "forbidden_next_action": "synonymous_route_back_redrive",
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
    }


def paper_mission_followthrough_trigger(
    *,
    consume_readback: Mapping[str, Any],
    opl_runtime_submission: Mapping[str, Any],
) -> str | None:
    drive_result = paper_mission_drive_result(
        consume_readback=consume_readback,
        handoff=_mapping(
            _mapping(consume_readback.get("consume_output_manifest")).get(
                "opl_route_handoff"
            )
        ),
        opl_runtime_submission=opl_runtime_submission,
    )
    if drive_result.get("provider_attempt_running_observed") is True:
        return None
    decision = _mapping(consume_readback.get("stage_terminal_decision"))
    next_decision = _mapping(consume_readback.get("next_owner_or_human_decision"))
    terminal_gate = _mapping(consume_readback.get("terminal_owner_gate"))
    owner_answer = _mapping(
        consume_readback.get("terminal_owner_gate_owner_answer_readback")
    )
    owner_answer_decision = _mapping(owner_answer.get("stage_terminal_decision"))
    terminal_route_back_observed = drive_result.get("terminal_closeout_observed") is True
    owner_answer_route_back_observed = (
        _optional_text(owner_answer.get("status")) == "route_back"
        and _optional_text(owner_answer.get("owner_answer_shape"))
        == "route_back_evidence_ref"
        and _optional_text(owner_answer_decision.get("decision_kind")) == "route_back"
    )
    if not terminal_route_back_observed and not owner_answer_route_back_observed:
        return None
    if _optional_text(terminal_gate.get("gate_kind")) == "human_gate":
        return None
    if _optional_text(next_decision.get("human_decision_required")) == "true":
        return None
    decision_kind = _first_text(
        owner_answer_decision.get("decision_kind"),
        decision.get("decision_kind"),
    )
    if decision_kind != "route_back":
        return None
    if _first_text(
        owner_answer_decision.get("next_owner"),
        decision.get("next_owner"),
        next_decision.get("next_owner"),
    ) != "mission_executor":
        return None
    return (
        "terminal_owner_answer_route_back_followthrough"
        if owner_answer_route_back_observed
        else "terminal_route_back_followthrough"
    )


def paper_mission_followthrough_stop_reason(
    *,
    consume_readback: Mapping[str, Any],
    opl_runtime_submission: Mapping[str, Any],
    exhausted: bool,
    non_advancing_route_back: bool = False,
) -> str:
    if non_advancing_route_back:
        return "non_advancing_route_back"
    if exhausted:
        return "followthrough_round_limit_reached"
    trigger = paper_mission_followthrough_trigger(
        consume_readback=consume_readback,
        opl_runtime_submission=opl_runtime_submission,
    )
    if trigger is not None:
        return "followthrough_available"
    drive_status = paper_mission_drive_result(
        consume_readback=consume_readback,
        handoff=_mapping(
            _mapping(consume_readback.get("consume_output_manifest")).get(
                "opl_route_handoff"
            )
        ),
        opl_runtime_submission=opl_runtime_submission,
    ).get("status")
    return _optional_text(drive_status) or "no_followthrough_needed"


def paper_mission_drive_output_roots(
    *,
    profile: Any,
    output_root: str | Path | None,
    run_id: str | None,
) -> dict[str, Path]:
    if output_root is not None:
        root = Path(output_root).expanduser().resolve()
        if _is_under_yang_workspace(root):
            selected_run_id = _optional_text(run_id) or root.name or "paper_mission_drive"
            workspace_root = yang_workspace_root_for_path(root)
            return {
                "root": root,
                "candidate_package": (
                    workspace_root / PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH / selected_run_id
                ),
                "consumption_ledger": (
                    workspace_root / PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH / selected_run_id
                ),
            }
        selected_run_id = _optional_text(run_id) or "paper_mission_drive"
        return {
            "root": root,
            "candidate_package": root / "candidate_package",
            "consumption_ledger": root / "consumption_ledger",
        }
    selected_run_id = _optional_text(run_id) or "paper_mission_drive"
    workspace_root = Path(profile.workspace_root).expanduser().resolve()
    return {
        "root": workspace_root / "ops" / "medautoscience",
        "candidate_package": (
            workspace_root / PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH / selected_run_id
        ),
        "consumption_ledger": (
            workspace_root / PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH / selected_run_id
        ),
    }


def yang_workspace_root_for_path(path: Path) -> Path:
    normalized = path.expanduser().resolve()
    relative = normalized.relative_to(YANG_WORKSPACE_ROOT)
    return YANG_WORKSPACE_ROOT / relative.parts[0]


def paper_mission_drive_result(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
    opl_runtime_submission: Mapping[str, Any],
    mas_owned_executor_delta: Mapping[str, Any] | None = None,
    stage_closure_decision: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    handoff_ready = _optional_text(handoff.get("handoff_status")) == (
        "ready_for_opl_route_command"
    )
    route = _mapping(consume_readback.get("opl_route_command"))
    decision = _mapping(consume_readback.get("stage_terminal_decision"))
    carrier_readback = _mapping(consume_readback.get("opl_runtime_carrier_readback"))
    runtime_status = _optional_text(consume_readback.get("opl_runtime_readback_status"))
    submission_status = _optional_text(opl_runtime_submission.get("status"))
    status = _paper_mission_drive_result_status(
        handoff_ready=handoff_ready,
        submission_status=submission_status,
        runtime_status=runtime_status,
        carrier_readback=carrier_readback,
    )
    if (
        _optional_text(_mapping(mas_owned_executor_delta).get("status"))
        == "mas_owned_executor_delta_ready"
        and status == "opl_runtime_submission_pending"
    ):
        status = "mas_owned_executor_delta_ready"
    if stage_closure_decision_missing(_mapping(stage_closure_decision)):
        status = "stage_closure_decision_missing"
    return {
        "status": status,
        "stage_closure_decision_ref": _mapping(stage_closure_decision).get(
            "decision_ref"
        ),
        "stage_closure_outcome": _mapping(
            _mapping(stage_closure_decision).get("outcome")
        ).get("kind"),
        "stage_terminal_decision": decision.get("decision_kind"),
        "route_command": route.get("command_kind"),
        "next_owner": _first_text(
            decision.get("next_owner"),
            handoff.get("next_owner"),
            _mapping(consume_readback.get("next_owner_or_human_decision")).get(
                "next_owner"
            ),
        ),
        "can_submit_to_opl_runtime": bool(handoff.get("can_submit_to_opl_runtime")),
        "opl_runtime_submission_status": submission_status,
        "opl_runtime_readback_status": runtime_status,
        "provider_attempt_running_observed": (
            runtime_status == "opl_runtime_attempt_running_observed"
        ),
        "terminal_closeout_observed": (
            runtime_status == "opl_runtime_terminal_readback_observed"
        ),
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
    }

