from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli_parts.paper_mission_command_parts.candidate_package_readback import (
    build_materialized_candidate_package_readback as _build_materialized_candidate_package_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts.command_metadata import (
    PAPER_MISSION_CONTRACT_REF,
    PAPER_MISSION_CONTRACT_VERSION,
    action_intent as _action_intent,
)
from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _load_json_object,
    _mapping,
    _optional_text,
)
from med_autoscience.cli_parts.paper_mission_command_parts.direct_next_action_handoff import (
    build_direct_next_action_handoff,
)
from med_autoscience.cli_parts.paper_mission_command_parts.drive_helpers import (
    DEFAULT_PAPER_MISSION_DRIVE_FOLLOWTHROUGH_LIMIT,
    paper_mission_drive_followthrough_empty as _paper_mission_drive_followthrough_empty,
    paper_mission_drive_output_roots as _paper_mission_drive_output_roots,
    paper_mission_drive_result as _paper_mission_drive_result,
    paper_mission_followthrough_stop_reason as _paper_mission_followthrough_stop_reason,
    paper_mission_followthrough_trigger as _paper_mission_followthrough_trigger,
    paper_mission_mas_owned_executor_delta_checkpoint as _paper_mission_mas_owned_executor_delta_checkpoint,
)
from med_autoscience.cli_parts.paper_mission_command_parts.opl_runtime_submission import (
    opl_runtime_submission_readback as _opl_runtime_submission_readback,
    refresh_consume_readback_after_opl_submission as _refresh_consume_readback_after_opl_submission,
    semantic_progress_guard as _paper_mission_semantic_progress_guard,
    stage_closure_missing_runtime_submission as _stage_closure_missing_runtime_submission,
)
from med_autoscience.cli_parts.paper_mission_command_parts.route_back_budget import (
    _load_paper_mission_route_back_budget_ledger,
    _paper_mission_route_back_budget_exhausted,
    _paper_mission_route_back_budget_ledger_path,
    _record_paper_mission_route_back_budget_ledger,
)
from med_autoscience.cli_parts.paper_mission_command_parts.stage_closure_terminalizer import (
    attach_stage_closure_ledger_to_drive_readback as _attach_stage_closure_ledger_to_drive_readback,
    materialize_stage_closure_for_drive_readback as _materialize_stage_closure_for_drive_readback,
)
from med_autoscience.cli_parts.paper_mission_output_roots import (
    _is_yang_ops_candidate_package_root,
    _is_yang_ops_consumption_ledger_root,
)
from med_autoscience.controllers.owner_route_handoff_parts.paper_mission_consumption_route_handoff import (
    latest_paper_mission_consumption_route_handoff,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_missing,
    stage_closure_decision_projection,
)
from med_autoscience.paper_mission_opl_readback import (
    paper_mission_opl_runtime_carrier_readback,
)


def build_paper_mission_drive_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: str | Path | None,
    run_id: str | None,
    submit_opl_runtime: bool | None,
    opl_bin: str | Path | None,
    source: str,
    consume_candidate_readback_builder: Callable[..., dict[str, Any]],
    consumption_ledger_forbidden_authority_writes: tuple[str, ...],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    output_roots = _paper_mission_drive_output_roots(
        profile=profile,
        output_root=output_root,
        run_id=run_id,
    )
    root = output_roots["root"]
    package_root = output_roots["candidate_package"]
    ledger_root = output_roots["consumption_ledger"]
    route_back_budget_ledger_ref = _paper_mission_route_back_budget_ledger_path(
        profile=profile,
        output_root=root,
        ledger_root=ledger_root,
        study_id=study_id,
    )
    route_back_budget_ledger = _load_paper_mission_route_back_budget_ledger(
        ledger_ref=route_back_budget_ledger_ref,
        study_id=study_id,
    )
    next_action_source_readback = _drive_next_action_source_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        source=source,
        consume_candidate_readback_builder=consume_candidate_readback_builder,
    )
    owner_action_stop = _drive_owner_action_stop_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        output_root=root,
        source=source,
        inspect_readback=next_action_source_readback,
        forbidden_authority_claims=forbidden_authority_claims,
    )
    if owner_action_stop is not None:
        return owner_action_stop
    if _drive_should_submit_direct_next_action(next_action_source_readback):
        return _drive_direct_next_action_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            output_root=root,
            submit_opl_runtime=submit_opl_runtime,
            opl_bin=opl_bin,
            source=source,
            inspect_readback=next_action_source_readback,
            forbidden_authority_claims=forbidden_authority_claims,
        )
    source_readback_override = (
        next_action_source_readback
        if _drive_can_package_from_next_action(next_action_source_readback)
        else None
    )
    try:
        package_readback = _build_materialized_candidate_package_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            output_root=package_root,
            source=f"{source}:drive:package-candidate",
            source_readback_override=source_readback_override,
        )
    except ValueError as exc:
        if "package-candidate requires a materialized PaperMissionRun" not in str(exc):
            raise
        existing_handoff = latest_paper_mission_consumption_route_handoff(
            workspace_root=Path(profile.workspace_root).expanduser().resolve(),
            study_id=study_id,
        )
        if existing_handoff is None:
            raise
        return _existing_consumption_handoff_drive_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            output_root=root,
            submit_opl_runtime=submit_opl_runtime,
            opl_bin=opl_bin,
            source=source,
            handoff=existing_handoff,
            forbidden_authority_claims=forbidden_authority_claims,
        )
    candidate_ref = package_readback["output_manifest"]["package_manifest_ref"]
    consume_readback = consume_candidate_readback_builder(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="consume-candidate",
        candidate=candidate_ref,
        output_root=ledger_root,
        source=f"{source}:drive:consume-candidate",
        enable_opl_live_probe=True,
    )
    consume_readback = _attach_stage_closure_ledger_to_drive_readback(
        profile=profile,
        consume_readback=consume_readback,
    )
    handoff = _mapping(
        _mapping(consume_readback.get("consume_output_manifest")).get(
            "opl_route_handoff"
        )
    )
    if not handoff:
        handoff_ref = _optional_text(
            _mapping(consume_readback.get("consume_output_manifest")).get(
                "opl_route_handoff_ref"
            )
        )
        handoff = _load_json_object(Path(handoff_ref)) if handoff_ref else {}
    runtime_submit_requested = submit_opl_runtime is not False
    initial_stage_closure_decision = stage_closure_decision_projection(
        readback=consume_readback,
        handoff=handoff,
    )
    stage_closure_output_manifest = None
    if stage_closure_decision_missing(initial_stage_closure_decision):
        consume_readback, stage_closure_output_manifest = (
            _materialize_stage_closure_for_drive_readback(
                profile=profile,
                study_id=study_id,
                consume_readback=consume_readback,
                source=f"{source}:drive:stage-closure-terminalizer",
            )
        )
        initial_stage_closure_decision = stage_closure_decision_projection(
            readback=consume_readback,
            handoff=handoff,
        )
    initial_progress_guard = _paper_mission_semantic_progress_guard(
        consume_readback=consume_readback,
        handoff=handoff,
        route_back_budget_ledger=route_back_budget_ledger,
    )
    route_back_budget_ledger = _record_paper_mission_route_back_budget_ledger(
        ledger=route_back_budget_ledger,
        ledger_ref=route_back_budget_ledger_ref,
        progress_guard=initial_progress_guard,
        consume_readback=consume_readback,
        handoff=handoff,
        trigger="drive-initial",
        source=source,
    )
    if stage_closure_decision_missing(initial_stage_closure_decision):
        opl_runtime_submission = _stage_closure_missing_runtime_submission(
            initial_stage_closure_decision
        )
        followthrough = _paper_mission_drive_followthrough_empty(
            route_back_budget_ledger=route_back_budget_ledger,
            route_back_budget_ledger_ref=route_back_budget_ledger_ref,
            progress_guard=initial_progress_guard,
            stage_closure_decision=initial_stage_closure_decision,
            stop_reason="stage_closure_decision_missing",
        )
    else:
        opl_runtime_submission = _opl_runtime_submission_readback(
            handoff=handoff,
            submit_opl_runtime=runtime_submit_requested,
            opl_bin=opl_bin,
        )
        consume_readback = _refresh_consume_readback_after_opl_submission(
            consume_readback=consume_readback,
            opl_runtime_submission=opl_runtime_submission,
        )
        consume_readback = _attach_stage_closure_ledger_to_drive_readback(
            profile=profile,
            consume_readback=consume_readback,
        )
        handoff = _mapping(
            _mapping(consume_readback.get("consume_output_manifest")).get(
                "opl_route_handoff"
            )
        ) or handoff
        followthrough = _paper_mission_drive_followthrough(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            root=root,
            package_root=package_root,
            ledger_root=ledger_root,
            source=source,
            opl_bin=opl_bin,
            submit_opl_runtime=runtime_submit_requested,
            initial_package_readback=package_readback,
            initial_consume_readback=consume_readback,
            initial_handoff=handoff,
            initial_opl_runtime_submission=opl_runtime_submission,
            initial_progress_guard=initial_progress_guard,
            route_back_budget_ledger=route_back_budget_ledger,
            route_back_budget_ledger_ref=route_back_budget_ledger_ref,
            consume_candidate_readback_builder=consume_candidate_readback_builder,
        )
    if followthrough["rounds"]:
        final_round = _mapping(followthrough["rounds"][-1])
        package_readback = _mapping(final_round.get("candidate_package_readback"))
        consume_readback = _mapping(final_round.get("consume_readback"))
        handoff = _mapping(final_round.get("opl_route_handoff"))
        opl_runtime_submission = _mapping(final_round.get("opl_runtime_submission"))
        stage_closure_output_manifest = _mapping(
            final_round.get("stage_closure_output_manifest")
        ) or stage_closure_output_manifest
    stage_closure_decision = stage_closure_decision_projection(
        readback=consume_readback,
        handoff=handoff,
        opl_runtime_submission=opl_runtime_submission,
    )
    mas_executor_delta = _paper_mission_mas_owned_executor_delta_checkpoint(
        package_readback=package_readback,
        consume_readback=consume_readback,
        handoff=handoff,
        progress_guard=followthrough["semantic_progress_guard"],
    )
    drive_result = _paper_mission_drive_result(
        consume_readback=consume_readback,
        handoff=handoff,
        opl_runtime_submission=opl_runtime_submission,
        mas_owned_executor_delta=mas_executor_delta,
        stage_closure_decision=stage_closure_decision,
    )
    return {
        "surface_kind": "paper_mission_drive_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": "drive",
        "action_intent": _action_intent("drive"),
        "source": source,
        "drive_mode": "package_consume_and_optionally_submit",
        "dry_run": False,
        "profile": package_readback["profile"],
        "requested_study_id": package_readback["requested_study_id"],
        "study_id": package_readback["study_id"],
        "study_root": package_readback["study_root"],
        "study_root_exists": package_readback["study_root_exists"],
        "mission_id": consume_readback["mission_id"],
        "objective": consume_readback["objective"],
        "output_root": str(root),
        **(
            {"inspect_readback": dict(next_action_source_readback)}
            if next_action_source_readback is not None
            else {}
        ),
        "candidate_package_readback": package_readback,
        "authority_consume_readback": consume_readback.get(
            "authority_consume_readback"
        ),
        "consume_readback": consume_readback,
        "stage_terminal_decision": consume_readback["stage_terminal_decision"],
        "opl_route_command": consume_readback["opl_route_command"],
        "opl_runtime_carrier": consume_readback["opl_runtime_carrier"],
        "opl_runtime_carrier_readback": consume_readback[
            "opl_runtime_carrier_readback"
        ],
        "opl_runtime_readback_status": consume_readback[
            "opl_runtime_readback_status"
        ],
        "terminal_owner_gate": consume_readback.get("terminal_owner_gate"),
        "terminal_owner_gate_authority_readback": consume_readback.get(
            "terminal_owner_gate_authority_readback"
        ),
        "terminal_owner_gate_owner_answer_readback": consume_readback.get(
            "terminal_owner_gate_owner_answer_readback"
        ),
        "semantic_progress_signature": consume_readback.get(
            "semantic_progress_signature"
        ),
        "route_back_budget": consume_readback.get("route_back_budget"),
        "mission_executor_fallback_action": consume_readback.get(
            "mission_executor_fallback_action"
        ),
        "carry_forward_risk_receipt_ref": consume_readback.get(
            "carry_forward_risk_receipt_ref"
        ),
        "opl_route_handoff": handoff or None,
        "opl_runtime_submission": opl_runtime_submission,
        "followthrough": followthrough,
        "stage_closure_decision": stage_closure_decision,
        "stage_closure_decision_ref": stage_closure_decision.get("decision_ref"),
        "stage_closure_outcome": _mapping(stage_closure_decision.get("outcome")).get(
            "kind"
        ),
        "semantic_progress_guard": followthrough["semantic_progress_guard"],
        "non_advancing_route_back": followthrough["non_advancing_route_back"],
        "route_back_budget_ledger": followthrough["route_back_budget_ledger"],
        "route_back_budget_ledger_ref": followthrough["route_back_budget_ledger_ref"],
        "mas_owned_executor_delta": mas_executor_delta,
        "mas_owned_executor_stage": _mapping(mas_executor_delta).get(
            "mas_owned_executor_stage"
        ),
        "requires_mas_owned_executor_delta": followthrough[
            "requires_mas_owned_executor_delta"
        ],
        "transaction_state": consume_readback["transaction_state"],
        "consume_candidate_status": consume_readback["consume_candidate_status"],
        "next_owner_or_human_decision": consume_readback[
            "next_owner_or_human_decision"
        ],
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": runtime_submit_requested
            and opl_runtime_submission.get("status") == "submitted",
            "writes_yang_authority": False,
            "writes_yang_ops_candidate_package": _is_yang_ops_candidate_package_root(
                package_root
            ),
            "writes_yang_ops_consumption_ledger": _is_yang_ops_consumption_ledger_root(
                ledger_root
            ),
            "writes_paper_body": False,
            "writes_candidate_workspace": True,
            "dry_run_only": False,
            "forbidden_authority_writes": list(
                consumption_ledger_forbidden_authority_writes
            ),
        },
        "output_manifest": {
            "mode": "paper_mission_drive",
            "output_root": str(root),
            "candidate_package": package_readback["output_manifest"],
            "consumption_ledger": consume_readback.get("consume_output_manifest"),
            **(
                {"stage_closure": stage_closure_output_manifest}
                if stage_closure_output_manifest
                else {}
            ),
            "route_back_budget_ledger_ref": followthrough[
                "route_back_budget_ledger_ref"
            ],
            "followthrough_round_count": followthrough["round_count"],
            "writes_authority": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "writes_runtime": runtime_submit_requested
            and opl_runtime_submission.get("status") == "submitted",
        },
        "forbidden_authority_writes": list(
            consumption_ledger_forbidden_authority_writes
        ),
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "drive_result": drive_result,
    }


def _drive_should_submit_direct_next_action(
    inspect_readback: Mapping[str, Any] | None,
) -> bool:
    readback = _mapping(inspect_readback)
    next_action = _mapping(readback.get("next_action"))
    action_family = _optional_text(next_action.get("action_family"))
    if action_family in {
        "paper.package.submission_minimal",
        "paper.stage_closure.owner_consumption",
    }:
        return False
    authority_boundary = _mapping(next_action.get("authority_boundary"))
    if (
        action_family == "runtime.opl_route"
        and _optional_text(next_action.get("action_kind")) == "submit_to_opl_runtime"
        and authority_boundary.get("can_submit_to_opl_runtime") is True
        and bool(_mapping(readback.get("terminal_owner_gate")))
        and _optional_text(next_action.get("owner")) is not None
        and _optional_text(next_action.get("work_unit_id")) is not None
    ):
        return True
    if _optional_text(next_action.get("action_type")) == "request_opl_stage_attempt":
        return True
    return (
        _optional_text(readback.get("canonical_next_action_source"))
        == "domain_transition.next_action"
        and _optional_text(next_action.get("surface_kind")) == "mas_next_action_envelope"
        and action_family is not None
        and _optional_text(next_action.get("owner")) is not None
        and _optional_text(next_action.get("work_unit_id")) is not None
    )


def _drive_direct_next_action_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: Path,
    submit_opl_runtime: bool | None,
    opl_bin: str | Path | None,
    source: str,
    inspect_readback: Mapping[str, Any] | None,
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    readback = _mapping(inspect_readback)
    next_action = _mapping(readback.get("next_action"))
    handoff = _drive_direct_next_action_handoff(
        profile=profile,
        study_id=study_id,
        inspect_readback=readback,
        next_action=next_action,
    )
    runtime_submit_requested = submit_opl_runtime is not False
    opl_runtime_submission = _opl_runtime_submission_readback(
        handoff=handoff,
        submit_opl_runtime=runtime_submit_requested,
        opl_bin=opl_bin,
    )
    carrier = _mapping(handoff.get("opl_runtime_carrier"))
    carrier_readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=Path(profile.studies_root) / study_id,
        enable_opl_live_probe=runtime_submit_requested,
        opl_bin=opl_bin,
    )
    drive_result = _drive_direct_next_action_result(
        handoff=handoff,
        opl_runtime_submission=opl_runtime_submission,
        carrier_readback=carrier_readback,
    )
    followthrough = _paper_mission_drive_followthrough_empty(
        route_back_budget_ledger={},
        route_back_budget_ledger_ref=output_root / "route_back_budget.json",
        progress_guard={},
        stage_closure_decision={},
        stop_reason="domain_transition_direct_stage_attempt",
    )
    writes_runtime = bool(opl_runtime_submission.get("writes_runtime"))
    return {
        "surface_kind": "paper_mission_drive_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": "drive",
        "action_intent": _action_intent("drive"),
        "source": source,
        "drive_mode": "domain_transition_direct_stage_attempt",
        "dry_run": False,
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "requested_study_id": study_id,
        "study_id": study_id,
        "study_root": str(Path(profile.studies_root) / study_id),
        "study_root_exists": (Path(profile.studies_root) / study_id).exists(),
        "mission_id": handoff["mission_id"],
        "objective": _optional_text(readback.get("objective"))
        or _optional_text(next_action.get("action_family"))
        or "MAS domain transition direct stage attempt",
        "output_root": str(output_root),
        "inspect_readback": dict(readback),
        "next_action": dict(next_action),
        "paper_mission_transaction": handoff["paper_mission_transaction"],
        "stage_terminal_decision": handoff["stage_terminal_decision"],
        "opl_route_command": handoff["opl_route_command"],
        "opl_runtime_carrier": carrier,
        "opl_runtime_carrier_readback": carrier_readback,
        "opl_runtime_readback_status": carrier_readback["carrier_status"],
        "opl_route_handoff": handoff,
        "opl_runtime_submission": opl_runtime_submission,
        "followthrough": followthrough,
        "transaction_state": "domain_transition_direct_stage_attempt",
        "consume_candidate_status": "not_applicable_domain_transition_direct",
        "next_owner_or_human_decision": {
            "kind": "owner_or_route",
            "next_owner": _optional_text(next_action.get("owner"))
            or _optional_text(next_action.get("stage_id")),
            "human_decision_required": False,
            "summary": "MAS domain transition selected a concrete OPL stage attempt.",
            "can_execute": False,
            "can_authorize_provider_admission": False,
        },
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": writes_runtime,
            "writes_yang_authority": False,
            "writes_yang_ops_candidate_package": False,
            "writes_yang_ops_consumption_ledger": False,
            "writes_paper_body": False,
            "writes_candidate_workspace": False,
            "dry_run_only": False,
        },
        "output_manifest": {
            "mode": "paper_mission_drive_domain_transition_direct_stage_attempt",
            "output_root": str(output_root),
            "writes_authority": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "writes_runtime": writes_runtime,
            "candidate_package": None,
            "consumption_ledger": None,
            "followthrough_round_count": 0,
        },
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "drive_result": drive_result,
    }


def _drive_direct_next_action_handoff(
    *,
    profile: Any,
    study_id: str,
    inspect_readback: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    return build_direct_next_action_handoff(
        profile=profile,
        study_id=study_id,
        inspect_readback=inspect_readback,
        next_action=next_action,
    )


def _drive_direct_next_action_result(
    *,
    handoff: Mapping[str, Any],
    opl_runtime_submission: Mapping[str, Any],
    carrier_readback: Mapping[str, Any],
) -> dict[str, Any]:
    carrier_status = _optional_text(carrier_readback.get("carrier_status"))
    submission_status = _optional_text(opl_runtime_submission.get("status"))
    status = (
        "opl_stage_route_running"
        if carrier_status == "opl_runtime_attempt_running_observed"
        else "opl_terminal_closeout_observed"
        if carrier_status == "opl_runtime_terminal_readback_observed"
        else "submitted_to_opl_runtime"
        if submission_status in {"submitted", "idempotent_noop"}
        else "opl_runtime_submission_pending"
        if submission_status == "not_requested"
        else "opl_runtime_submission_failed"
    )
    return {
        "surface_kind": "paper_mission_drive_result",
        "status": status,
        "reason": "domain_transition_direct_stage_attempt",
        "route_target": _optional_text(handoff.get("route_target")),
        "work_unit_id": _optional_text(handoff.get("work_unit_id")),
        "work_unit_fingerprint": _optional_text(handoff.get("work_unit_fingerprint")),
        "can_submit_to_opl_runtime": handoff.get("can_submit_to_opl_runtime") is True,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
    }


def _drive_next_action_source_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    source: str,
    consume_candidate_readback_builder: Callable[..., dict[str, Any]],
) -> dict[str, Any] | None:
    inspect_readback = consume_candidate_readback_builder(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="inspect",
        source=f"{source}:drive:canonical-next-action-inspect",
        enable_opl_live_probe=False,
    )
    next_action = _mapping(inspect_readback.get("next_action"))
    if _optional_text(next_action.get("surface_kind")) != "mas_next_action_envelope":
        return None
    if _optional_text(next_action.get("work_unit_id")) is None:
        return None
    return inspect_readback


def _drive_canonical_next_action_source_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    source: str,
    consume_candidate_readback_builder: Callable[..., dict[str, Any]],
) -> dict[str, Any] | None:
    inspect_readback = _drive_next_action_source_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        source=source,
        consume_candidate_readback_builder=consume_candidate_readback_builder,
    )
    if not _drive_can_package_from_next_action(inspect_readback):
        return None
    return dict(inspect_readback)


def _drive_can_package_from_next_action(
    inspect_readback: Mapping[str, Any] | None,
) -> bool:
    next_action = _mapping(_mapping(inspect_readback).get("next_action"))
    action_type = _optional_text(next_action.get("action_type"))
    return (
        action_type == "request_opl_stage_attempt"
        or _optional_text(next_action.get("action_family"))
        == "paper.package.submission_minimal"
        or action_type == "classify_quality_blockers_or_materialize_degraded_handoff_gate"
    )


def _drive_owner_action_stop_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: Path,
    source: str,
    inspect_readback: Mapping[str, Any] | None,
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any] | None:
    readback = _mapping(inspect_readback)
    next_action = _mapping(readback.get("next_action"))
    if _optional_text(next_action.get("surface_kind")) != "mas_next_action_envelope":
        return None
    can_package_from_next_action = _drive_can_package_from_next_action(readback)
    if _drive_should_submit_direct_next_action(readback):
        return None
    if can_package_from_next_action:
        return None
    has_owner_stop = _drive_has_terminal_owner_consumption_action(readback) or (
        bool(_mapping(readback.get("typed_blocker_resolution_readback")))
    )
    if not has_owner_stop:
        return None
    current_action = _mapping(readback.get("current_executable_owner_action"))
    reason = _drive_owner_action_stop_reason(readback)
    drive_result = {
        "surface_kind": "paper_mission_drive_result",
        "status": "owner_action_ready_no_redrive",
        "reason": reason,
        "next_legal_action": _optional_text(next_action.get("action_type")),
        "forbidden_next_action": "synonymous_route_back_redrive",
        "can_submit_to_opl_runtime": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
    }
    return {
        "surface_kind": "paper_mission_drive_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": "drive",
        "action_intent": _action_intent("drive"),
        "source": source,
        "drive_mode": "owner_action_ready_no_redrive",
        "dry_run": False,
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "requested_study_id": study_id,
        "study_id": study_id,
        "study_root": str(Path(profile.studies_root) / study_id),
        "study_root_exists": (Path(profile.studies_root) / study_id).exists(),
        "mission_id": readback.get("mission_id"),
        "objective": readback.get("objective"),
        "output_root": str(output_root),
        "inspect_readback": dict(readback),
        "next_action": dict(next_action),
        "stage_closure_decision": _mapping(readback.get("stage_closure_decision"))
        or None,
        "terminal_owner_gate_authority_readback": _mapping(
            readback.get("terminal_owner_gate_authority_readback")
        )
        or None,
        "terminal_owner_gate_owner_answer_readback": _mapping(
            readback.get("terminal_owner_gate_owner_answer_readback")
        )
        or None,
        **(
            {"current_executable_owner_action": dict(current_action)}
            if current_action
            else {}
        ),
        "typed_blocker_resolution_readback": dict(
            _mapping(readback.get("typed_blocker_resolution_readback"))
        ),
        "drive_result": drive_result,
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_yang_ops_candidate_package": False,
            "writes_yang_ops_consumption_ledger": False,
            "writes_paper_body": False,
            "writes_candidate_workspace": False,
            "dry_run_only": True,
        },
        "output_manifest": {
            "mode": "paper_mission_drive_owner_action_ready_no_redrive",
            "output_root": str(output_root),
            "writes_authority": False,
            "writes_yang_authority": False,
            "writes_runtime": False,
            "writes_candidate_workspace": False,
        },
        "forbidden_authority_claims": list(forbidden_authority_claims),
    }


def _drive_has_terminal_owner_consumption_action(
    readback: Mapping[str, Any],
) -> bool:
    from_consumption_ledger = _optional_text(
        readback.get("paper_mission_current_transaction_source")
    ) == "paper_mission_consumption_ledger"
    owner_answer = _mapping(readback.get("terminal_owner_gate_owner_answer_readback"))
    consume_result = _mapping(owner_answer.get("consume_result"))
    owner_answer_route_back = (
        _optional_text(consume_result.get("outcome")) == "route_back_evidence_ref"
    )
    next_action = _mapping(readback.get("next_action"))
    if _optional_text(next_action.get("action_family")) == (
        "paper.stage_closure.owner_consumption"
    ):
        return from_consumption_ledger or owner_answer_route_back
    if _optional_text(next_action.get("action_type")) == "request_opl_stage_attempt":
        return False
    outcome = _mapping(_mapping(readback.get("stage_closure_decision")).get("outcome"))
    if outcome.get("transition_kind") == "route_back_candidate_checkpoint":
        return from_consumption_ledger or owner_answer_route_back
    if owner_answer_route_back:
        return True
    authority = _mapping(readback.get("terminal_owner_gate_authority_readback"))
    if _optional_text(authority.get("status")) in {
        "owner_answer_required",
        "typed_blocker_required",
        "owner_gate_required",
    }:
        return from_consumption_ledger
    return False


def _drive_owner_action_stop_reason(readback: Mapping[str, Any]) -> str:
    if _mapping(readback.get("typed_blocker_resolution_readback")):
        return "typed_blocker_resolution_successor_requires_owner_action"
    next_action = _mapping(readback.get("next_action"))
    if _optional_text(next_action.get("action_family")) == (
        "paper.stage_closure.owner_consumption"
    ):
        return "stage_closure_route_back_checkpoint_requires_owner_consumption"
    owner_answer = _mapping(readback.get("terminal_owner_gate_owner_answer_readback"))
    consume_result = _mapping(owner_answer.get("consume_result"))
    if _optional_text(consume_result.get("outcome")) == "route_back_evidence_ref":
        return "terminal_owner_gate_route_back_evidence_requires_owner_consumption"
    return "terminal_owner_gate_requires_owner_action"


def _existing_consumption_handoff_drive_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: Path,
    submit_opl_runtime: bool | None,
    opl_bin: str | Path | None,
    source: str,
    handoff: Mapping[str, Any],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    source_ref = _optional_text(handoff.get("source_ref"))
    consume_readback = _load_existing_consumption_readback(source_ref)
    if not consume_readback:
        consume_readback = {
            "surface_kind": "paper_mission_existing_consumption_handoff_readback",
            "schema_version": 1,
            "mission_id": _optional_text(handoff.get("mission_id"))
            or "paper-mission::unknown",
            "objective": "reuse latest paper mission consumption route handoff",
            "study_id": study_id,
            "study_root": str(Path(profile.studies_root) / study_id),
            "candidate_ref": _optional_text(handoff.get("candidate_ref")),
            "paper_mission_transaction": _mapping(
                handoff.get("paper_mission_transaction")
            ),
            "stage_terminal_decision": _mapping(
                handoff.get("stage_terminal_decision")
            ),
            "opl_route_command": _mapping(handoff.get("opl_route_command")),
            "opl_runtime_carrier": _mapping(handoff.get("opl_runtime_carrier")),
            "transaction_state": _optional_text(handoff.get("transaction_state"))
            or "ready_for_opl_route_command",
            "consume_candidate_status": _optional_text(handoff.get("status"))
            or "accepted_candidate",
            "next_action": _mapping(handoff.get("next_action")),
            "next_owner_or_human_decision": {
                "kind": "owner_or_route",
                "next_owner": _optional_text(handoff.get("next_owner")),
                "human_decision_required": False,
                "summary": "Reuse latest materialized paper mission route handoff.",
                "can_execute": False,
                "can_authorize_provider_admission": False,
            },
            "consume_output_manifest": {
                "mode": "existing_consumption_handoff",
                "opl_route_handoff": dict(handoff),
                "opl_route_handoff_ref": source_ref,
                "route_handoff_status": _optional_text(handoff.get("handoff_status")),
                "next_owner": _optional_text(handoff.get("next_owner")),
                "writes_authority": False,
                "writes_runtime": False,
                "writes_yang_authority": False,
            },
        }
    if "objective" not in consume_readback:
        decision = _mapping(consume_readback.get("stage_terminal_decision"))
        consume_readback = {
            **consume_readback,
            "objective": _optional_text(decision.get("next_work_unit"))
            or "reuse latest paper mission consumption route handoff",
        }
    if "next_owner_or_human_decision" not in consume_readback:
        decision = _mapping(consume_readback.get("stage_terminal_decision"))
        consume_readback = {
            **consume_readback,
            "next_owner_or_human_decision": {
                "kind": "owner_or_route",
                "next_owner": _optional_text(decision.get("next_owner"))
                or _optional_text(handoff.get("next_owner")),
                "human_decision_required": False,
                "summary": _optional_text(decision.get("reason"))
                or "Reuse latest materialized paper mission route handoff.",
                "can_execute": False,
                "can_authorize_provider_admission": False,
            },
        }
    if "consume_output_manifest" not in consume_readback:
        consume_readback = {
            **consume_readback,
            "consume_output_manifest": {
                "mode": "existing_consumption_handoff",
                "opl_route_handoff": dict(handoff),
                "opl_route_handoff_ref": source_ref,
                "route_handoff_status": _optional_text(handoff.get("handoff_status")),
                "next_owner": _optional_text(handoff.get("next_owner")),
                "writes_authority": False,
                "writes_runtime": False,
                "writes_yang_authority": False,
            },
        }
    runtime_submit_requested = submit_opl_runtime is not False
    opl_runtime_submission = _opl_runtime_submission_readback(
        handoff=handoff,
        submit_opl_runtime=runtime_submit_requested,
        opl_bin=opl_bin,
    )
    refreshed_consume_readback = _refresh_consume_readback_after_opl_submission(
        consume_readback=consume_readback,
        opl_runtime_submission=opl_runtime_submission,
    )
    drive_result = _paper_mission_drive_result(
        consume_readback=refreshed_consume_readback,
        handoff=handoff,
        opl_runtime_submission=opl_runtime_submission,
    )
    package_readback = {
        "surface_kind": "paper_mission_existing_consumption_handoff_package_readback",
        "schema_version": 1,
        "status": "skipped_existing_consumption_handoff",
        "reason": (
            "A materialized consumption route handoff already exists; drive reused "
            "it instead of requiring a one-shot migration package."
        ),
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "requested_study_id": study_id,
        "study_id": study_id,
        "study_root": str(Path(profile.studies_root) / study_id),
        "study_root_exists": (Path(profile.studies_root) / study_id).exists(),
        "output_manifest": {
            "mode": "existing_consumption_handoff",
            "package_manifest_ref": _optional_text(handoff.get("candidate_ref")),
            "opl_route_handoff_ref": source_ref,
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
        },
    }
    return {
        "surface_kind": "paper_mission_drive_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": "drive",
        "action_intent": _action_intent("drive"),
        "source": source,
        "drive_mode": "existing_consumption_handoff",
        "dry_run": False,
        "profile": package_readback["profile"],
        "requested_study_id": study_id,
        "study_id": study_id,
        "study_root": package_readback["study_root"],
        "study_root_exists": package_readback["study_root_exists"],
        "mission_id": refreshed_consume_readback["mission_id"],
        "objective": refreshed_consume_readback["objective"],
        "output_root": str(output_root),
        "candidate_package_readback": package_readback,
        "authority_consume_readback": refreshed_consume_readback.get(
            "authority_consume_readback"
        ),
        "consume_readback": refreshed_consume_readback,
        "stage_terminal_decision": refreshed_consume_readback["stage_terminal_decision"],
        "opl_route_command": refreshed_consume_readback["opl_route_command"],
        "opl_runtime_carrier": refreshed_consume_readback["opl_runtime_carrier"],
        "opl_runtime_carrier_readback": refreshed_consume_readback.get(
            "opl_runtime_carrier_readback"
        )
        or {},
        "opl_runtime_readback_status": refreshed_consume_readback.get(
            "opl_runtime_readback_status"
        )
        or "not_requested",
        "terminal_owner_gate": refreshed_consume_readback.get("terminal_owner_gate"),
        "terminal_owner_gate_authority_readback": refreshed_consume_readback.get(
            "terminal_owner_gate_authority_readback"
        ),
        "terminal_owner_gate_owner_answer_readback": refreshed_consume_readback.get(
            "terminal_owner_gate_owner_answer_readback"
        ),
        "semantic_progress_signature": refreshed_consume_readback.get(
            "semantic_progress_signature"
        ),
        "route_back_budget": refreshed_consume_readback.get("route_back_budget"),
        "mission_executor_fallback_action": refreshed_consume_readback.get(
            "mission_executor_fallback_action"
        ),
        "carry_forward_risk_receipt_ref": refreshed_consume_readback.get(
            "carry_forward_risk_receipt_ref"
        ),
        "opl_route_handoff": dict(handoff),
        "opl_runtime_submission": opl_runtime_submission,
        "followthrough": _paper_mission_drive_followthrough_empty(
            route_back_budget_ledger={},
            route_back_budget_ledger_ref=output_root / "route_back_budget.json",
            progress_guard={},
            stage_closure_decision={},
            stop_reason="existing_consumption_handoff_reused",
        ),
        "drive_result": drive_result,
        "transaction_state": refreshed_consume_readback["transaction_state"],
        "consume_candidate_status": refreshed_consume_readback[
            "consume_candidate_status"
        ],
        "next_owner_or_human_decision": refreshed_consume_readback[
            "next_owner_or_human_decision"
        ],
        "next_action": refreshed_consume_readback.get("next_action"),
        "stage_closure_decision": None,
        "stage_closure_decision_ref": None,
        "stage_closure_outcome": None,
        "durable_mission_stop_guard": {
            "surface_kind": "paper_mission_durable_stop_guard",
            "accepted_submission_milestone_candidate_is_durable_stop": False,
            "durable_stop_allowed": False,
            "can_claim_paper_progress": False,
        },
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": bool(opl_runtime_submission.get("writes_runtime")),
            "writes_yang_authority": False,
        },
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "output_manifest": {
            "mode": "paper_mission_drive_existing_consumption_handoff",
            "output_root": str(output_root),
            "writes_authority": False,
            "writes_yang_authority": False,
            "writes_runtime": bool(opl_runtime_submission.get("writes_runtime")),
            "consumption_ledger": refreshed_consume_readback.get(
                "consume_output_manifest"
            ),
            "candidate_package": package_readback.get("output_manifest"),
        },
    }


def _load_existing_consumption_readback(source_ref: str | None) -> dict[str, Any]:
    if source_ref is None:
        return {}
    handoff_path = Path(source_ref).expanduser()
    if handoff_path.name != "opl_route_handoff.json":
        return {}
    readback_path = handoff_path.with_name("consume_readback.json")
    try:
        payload = _load_json_object(readback_path)
    except (OSError, ValueError):
        return {}
    return _mapping(payload)


def _paper_mission_drive_followthrough(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    root: Path,
    package_root: Path,
    ledger_root: Path,
    source: str,
    opl_bin: str | Path | None,
    submit_opl_runtime: bool,
    initial_package_readback: Mapping[str, Any],
    initial_consume_readback: Mapping[str, Any],
    initial_handoff: Mapping[str, Any],
    initial_opl_runtime_submission: Mapping[str, Any],
    initial_progress_guard: Mapping[str, Any],
    route_back_budget_ledger: Mapping[str, Any],
    route_back_budget_ledger_ref: Path,
    consume_candidate_readback_builder: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    rounds: list[dict[str, Any]] = []
    current_package_readback = dict(initial_package_readback)
    current_consume_readback = dict(initial_consume_readback)
    current_handoff = dict(initial_handoff)
    current_submission = dict(initial_opl_runtime_submission)
    current_progress_guard = dict(initial_progress_guard)
    current_route_back_budget_ledger = dict(route_back_budget_ledger)
    non_advancing_route_back: dict[str, Any] | None = None
    current_stage_closure_decision = stage_closure_decision_projection(
        readback=current_consume_readback,
        handoff=current_handoff,
        opl_runtime_submission=current_submission,
    )
    for index in range(DEFAULT_PAPER_MISSION_DRIVE_FOLLOWTHROUGH_LIMIT):
        if _paper_mission_route_back_budget_exhausted(current_progress_guard):
            non_advancing_route_back = current_progress_guard
            break
        if stage_closure_decision_missing(current_stage_closure_decision):
            break
        trigger = _paper_mission_followthrough_trigger(
            consume_readback=current_consume_readback,
            opl_runtime_submission=current_submission,
        )
        if trigger is None:
            break
        round_id = f"followthrough-{index + 1:02d}"
        package_round_root = package_root / round_id
        ledger_round_root = ledger_root / round_id
        package_readback = _build_materialized_candidate_package_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            output_root=package_round_root,
            source=f"{source}:drive:{round_id}:package-candidate",
            source_readback_override=current_consume_readback,
        )
        candidate_ref = package_readback["output_manifest"]["package_manifest_ref"]
        consume_readback = consume_candidate_readback_builder(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command="consume-candidate",
            candidate=candidate_ref,
            output_root=ledger_round_root,
            source=f"{source}:drive:{round_id}:consume-candidate",
            enable_opl_live_probe=True,
            opl_bin=opl_bin,
        )
        consume_readback = _attach_stage_closure_ledger_to_drive_readback(
            profile=profile,
            consume_readback=consume_readback,
        )
        stage_closure_output_manifest = None
        stage_closure_decision = stage_closure_decision_projection(
            readback=consume_readback,
            handoff={},
        )
        if stage_closure_decision_missing(stage_closure_decision):
            consume_readback, stage_closure_output_manifest = (
                _materialize_stage_closure_for_drive_readback(
                    profile=profile,
                    study_id=study_id,
                    consume_readback=consume_readback,
                    source=f"{source}:drive:{round_id}:stage-closure-terminalizer",
                )
            )
        handoff = _mapping(
            _mapping(consume_readback.get("consume_output_manifest")).get(
                "opl_route_handoff"
            )
        )
        if not handoff:
            handoff_ref = _optional_text(
                _mapping(consume_readback.get("consume_output_manifest")).get(
                    "opl_route_handoff_ref"
                )
            )
            handoff = _load_json_object(Path(handoff_ref)) if handoff_ref else {}
        submission = _opl_runtime_submission_readback(
            handoff=handoff,
            submit_opl_runtime=submit_opl_runtime,
            opl_bin=opl_bin,
        )
        consume_readback = _refresh_consume_readback_after_opl_submission(
            consume_readback=consume_readback,
            opl_runtime_submission=submission,
        )
        consume_readback = _attach_stage_closure_ledger_to_drive_readback(
            profile=profile,
            consume_readback=consume_readback,
        )
        handoff = _mapping(
            _mapping(consume_readback.get("consume_output_manifest")).get(
                "opl_route_handoff"
            )
        ) or handoff
        stage_closure_decision = stage_closure_decision_projection(
            readback=consume_readback,
            handoff=handoff,
            opl_runtime_submission=submission,
        )
        next_progress_guard = _paper_mission_semantic_progress_guard(
            consume_readback=consume_readback,
            handoff=handoff,
            previous_guard=current_progress_guard,
            route_back_budget_ledger=current_route_back_budget_ledger,
        )
        current_route_back_budget_ledger = _record_paper_mission_route_back_budget_ledger(
            ledger=current_route_back_budget_ledger,
            ledger_ref=route_back_budget_ledger_ref,
            progress_guard=next_progress_guard,
            consume_readback=consume_readback,
            handoff=handoff,
            trigger=round_id,
            source=source,
        )
        round_readback = {
            "round": index + 1,
            "round_id": round_id,
            "trigger": trigger,
            "output_root": str(root / round_id),
            "candidate_package_readback": package_readback,
            "consume_readback": consume_readback,
            "opl_route_handoff": handoff or None,
            "opl_runtime_submission": submission,
            **(
                {"stage_closure_output_manifest": stage_closure_output_manifest}
                if stage_closure_output_manifest
                else {}
            ),
            "stage_closure_decision": stage_closure_decision,
            "stage_closure_decision_ref": stage_closure_decision.get("decision_ref"),
            "stage_closure_outcome": _mapping(
                stage_closure_decision.get("outcome")
            ).get("kind"),
            "drive_result": _paper_mission_drive_result(
                consume_readback=consume_readback,
                handoff=handoff,
                opl_runtime_submission=submission,
                stage_closure_decision=stage_closure_decision,
            ),
            "semantic_progress_guard": next_progress_guard,
        }
        rounds.append(round_readback)
        current_package_readback = package_readback
        current_consume_readback = consume_readback
        current_handoff = handoff
        current_submission = submission
        current_progress_guard = next_progress_guard
        current_stage_closure_decision = stage_closure_decision
        if _paper_mission_route_back_budget_exhausted(next_progress_guard):
            non_advancing_route_back = next_progress_guard
            break
    mas_executor_delta = _paper_mission_mas_owned_executor_delta_checkpoint(
        package_readback=current_package_readback,
        consume_readback=current_consume_readback,
        handoff=current_handoff,
        progress_guard=current_progress_guard,
    )
    stop_reason = (
        "mas_owned_executor_delta_ready"
        if mas_executor_delta is not None and not non_advancing_route_back
        else _paper_mission_followthrough_stop_reason(
            consume_readback=current_consume_readback,
            opl_runtime_submission=current_submission,
            exhausted=len(rounds) >= DEFAULT_PAPER_MISSION_DRIVE_FOLLOWTHROUGH_LIMIT
            and _paper_mission_followthrough_trigger(
                consume_readback=current_consume_readback,
                opl_runtime_submission=current_submission,
            )
            is not None,
            non_advancing_route_back=non_advancing_route_back is not None,
        )
    )
    final_drive_result = _paper_mission_drive_result(
        consume_readback=current_consume_readback,
        handoff=current_handoff,
        opl_runtime_submission=current_submission,
        mas_owned_executor_delta=mas_executor_delta,
        stage_closure_decision=current_stage_closure_decision,
    )
    return {
        "surface_kind": "paper_mission_drive_followthrough_readback",
        "schema_version": 1,
        "attempted": bool(rounds),
        "round_count": len(rounds),
        "max_rounds": DEFAULT_PAPER_MISSION_DRIVE_FOLLOWTHROUGH_LIMIT,
        "rounds": rounds,
        "stop_reason": stop_reason,
        "semantic_progress_guard": current_progress_guard,
        "stage_closure_decision": current_stage_closure_decision,
        "stage_closure_decision_ref": current_stage_closure_decision.get("decision_ref"),
        "stage_closure_outcome": _mapping(
            current_stage_closure_decision.get("outcome")
        ).get("kind"),
        "non_advancing_route_back": non_advancing_route_back,
        "route_back_budget_ledger": current_route_back_budget_ledger,
        "route_back_budget_ledger_ref": str(route_back_budget_ledger_ref),
        "mas_owned_executor_delta": mas_executor_delta,
        "mas_owned_executor_stage": _mapping(mas_executor_delta).get(
            "mas_owned_executor_stage"
        ),
        "requires_mas_owned_executor_delta": non_advancing_route_back is not None,
        "final_drive_result": final_drive_result,
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
            "writes_runtime_queue": bool(
                [
                    item
                    for item in (
                        [initial_opl_runtime_submission]
                        + [round_item["opl_runtime_submission"] for round_item in rounds]
                    )
                    if _optional_text(_mapping(item).get("status"))
                    in {"submitted", "idempotent_noop"}
                ]
            ),
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
        },
    }


__all__ = ["build_paper_mission_drive_readback"]
