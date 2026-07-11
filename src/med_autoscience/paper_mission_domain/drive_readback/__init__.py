from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_domain.candidate_package_readback import (
    build_materialized_candidate_package_readback as _build_materialized_candidate_package_readback,
)
from med_autoscience.paper_mission_domain.command_metadata import (
    FORBIDDEN_AUTHORITY_WRITES,
    PAPER_MISSION_CONTRACT_REF,
    PAPER_MISSION_CONTRACT_VERSION,
    action_intent as _action_intent,
)
from med_autoscience.paper_mission_domain.common import _mapping, _optional_text
from .direct_next_action import (
    drive_direct_next_action_handoff as _drive_direct_next_action_handoff,
    drive_direct_next_action_result as _drive_direct_next_action_result,
    drive_next_action_has_submit_authority as _drive_next_action_has_submit_authority,
    drive_readback_has_submission_route_checkpoint as _drive_readback_has_submission_route_checkpoint,
    drive_should_submit_direct_next_action as _drive_should_submit_direct_next_action,
)
from .domain_transition_redrive_stop import (
    drive_domain_transition_redrive_block_payload as _drive_domain_transition_redrive_block_payload,
    drive_domain_transition_redrive_stop_readback as _drive_domain_transition_redrive_stop_readback,
)
from med_autoscience.paper_mission_domain.drive_helpers import (
    paper_mission_drive_output_roots as _paper_mission_drive_output_roots,
    paper_mission_drive_result as _paper_mission_drive_result,
)
from med_autoscience.paper_mission_domain.opl_runtime_submission import (
    opl_runtime_submission_readback as _opl_runtime_submission_readback,
    refresh_consume_readback_after_opl_submission as _refresh_consume_readback_after_opl_submission,
    stage_closure_missing_runtime_submission as _stage_closure_missing_runtime_submission,
)
from med_autoscience.paper_mission_domain.stage_closure_terminalizer import (
    materialize_stage_closure_for_drive_readback as _materialize_stage_closure_for_drive_readback,
)
from med_autoscience.paper_mission_output_roots import (
    _is_yang_ops_candidate_package_root,
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
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    output_roots = _paper_mission_drive_output_roots(
        profile=profile,
        output_root=output_root,
        run_id=run_id,
    )
    root = output_roots["root"]
    package_root = output_roots["candidate_package"]
    next_action_source_readback = _drive_next_action_source_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        source=source,
        consume_candidate_readback_builder=consume_candidate_readback_builder,
        enable_opl_live_probe=submit_opl_runtime is not False,
    )
    domain_transition_stop = _drive_domain_transition_redrive_stop_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        output_root=root,
        source=source,
        inspect_readback=next_action_source_readback,
        forbidden_authority_claims=forbidden_authority_claims,
    )
    if domain_transition_stop is not None:
        return domain_transition_stop
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
    package_readback = _build_materialized_candidate_package_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        output_root=package_root,
        source=f"{source}:drive:package-candidate",
        source_readback_override=source_readback_override,
    )
    candidate_ref = package_readback["output_manifest"]["package_manifest_ref"]
    consume_readback = consume_candidate_readback_builder(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="consume-candidate",
        candidate=candidate_ref,
        source=f"{source}:drive:consume-candidate",
        enable_opl_live_probe=True,
    )
    handoff = _mapping(consume_readback.get("opl_route_handoff"))
    runtime_submit_requested = submit_opl_runtime is not False
    initial_stage_closure_decision = stage_closure_decision_projection(
        readback=consume_readback,
        handoff=handoff,
    )
    if stage_closure_decision_missing(initial_stage_closure_decision):
        consume_readback = _materialize_stage_closure_for_drive_readback(
            consume_readback=consume_readback,
        )
        initial_stage_closure_decision = stage_closure_decision_projection(
            readback=consume_readback,
            handoff=handoff,
        )
    if stage_closure_decision_missing(initial_stage_closure_decision):
        opl_runtime_submission = _stage_closure_missing_runtime_submission(
            initial_stage_closure_decision
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
        handoff = _mapping(consume_readback.get("opl_route_handoff")) or handoff
    stage_closure_decision = stage_closure_decision_projection(
        readback=consume_readback,
        handoff=handoff,
        opl_runtime_submission=opl_runtime_submission,
    )
    drive_result = _paper_mission_drive_result(
        consume_readback=consume_readback,
        handoff=handoff,
        opl_runtime_submission=opl_runtime_submission,
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
        "carry_forward_risk_receipt_ref": consume_readback.get(
            "carry_forward_risk_receipt_ref"
        ),
        "opl_route_handoff": handoff or None,
        "opl_runtime_submission": opl_runtime_submission,
        "stage_closure_decision": stage_closure_decision,
        "stage_closure_decision_ref": stage_closure_decision.get("decision_ref"),
        "stage_closure_outcome": _mapping(stage_closure_decision.get("outcome")).get(
            "kind"
        ),
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
            "writes_paper_body": False,
            "writes_candidate_workspace": True,
            "dry_run_only": False,
            "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        },
        "output_manifest": {
            "mode": "paper_mission_drive",
            "output_root": str(root),
            "candidate_package": package_readback["output_manifest"],
            "writes_authority": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "writes_runtime": runtime_submit_requested
            and opl_runtime_submission.get("status") == "submitted",
        },
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "drive_result": drive_result,
    }


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
        },
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "drive_result": drive_result,
    }


def _drive_next_action_source_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    source: str,
    consume_candidate_readback_builder: Callable[..., dict[str, Any]],
    enable_opl_live_probe: bool = False,
) -> dict[str, Any] | None:
    inspect_readback = consume_candidate_readback_builder(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="inspect",
        source=f"{source}:drive:canonical-next-action-inspect",
        enable_opl_live_probe=enable_opl_live_probe,
    )
    if _drive_domain_transition_redrive_block_payload(inspect_readback) is not None:
        return inspect_readback
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
        enable_opl_live_probe=False,
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
    current_opl_owner_consumption = _drive_current_opl_owner_consumption(readback)
    if _drive_should_submit_direct_next_action(readback):
        return None
    if can_package_from_next_action:
        return None
    has_owner_stop = (
        bool(current_opl_owner_consumption)
        or _drive_has_terminal_owner_consumption_action(readback)
        or (bool(_mapping(readback.get("typed_blocker_resolution_readback"))))
    )
    if not has_owner_stop:
        return None
    current_action = _mapping(readback.get("current_executable_owner_action"))
    reason = _drive_owner_action_stop_reason(readback)
    drive_result = {
        "surface_kind": "paper_mission_drive_result",
        "status": "owner_action_ready_no_redrive",
        "reason": reason,
        "next_legal_action": _optional_text(
            current_opl_owner_consumption.get("next_legal_action")
        )
        or _optional_text(next_action.get("action_type")),
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
        **(
            {"current_opl_owner_consumption": dict(current_opl_owner_consumption)}
            if current_opl_owner_consumption
            else {}
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
    owner_answer = _mapping(readback.get("terminal_owner_gate_owner_answer_readback"))
    consume_result = _mapping(owner_answer.get("consume_result"))
    owner_answer_route_back = (
        _optional_text(consume_result.get("outcome")) == "route_back_evidence_ref"
    )
    next_action = _mapping(readback.get("next_action"))
    if _optional_text(next_action.get("action_family")) == (
        "paper.stage_closure.owner_consumption"
    ):
        return True
    if _optional_text(next_action.get("action_type")) == "request_opl_stage_attempt":
        return False
    outcome = _mapping(_mapping(readback.get("stage_closure_decision")).get("outcome"))
    if outcome.get("transition_kind") == "route_back_candidate_checkpoint":
        return True
    if owner_answer_route_back:
        return True
    authority = _mapping(readback.get("terminal_owner_gate_authority_readback"))
    if _optional_text(authority.get("status")) in {
        "owner_answer_required",
        "typed_blocker_required",
        "owner_gate_required",
    }:
        return True
    return False


def _drive_current_opl_owner_consumption(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    current_readback = _drive_runtime_carrier_readback(readback)
    consumption = _mapping(current_readback.get("mas_receipt_consumption"))
    if _optional_text(consumption.get("status")) != "requires_mas_owner_consumption":
        return {}
    next_legal_action = _optional_text(consumption.get("next_legal_action"))
    if next_legal_action not in {
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
        "record_typed_blocker",
        "consume_opl_transition_receipt",
    }:
        return {}
    return dict(consumption)


def _drive_runtime_carrier_readback(readback: Mapping[str, Any]) -> Mapping[str, Any]:
    current_readback = _mapping(readback.get("current_opl_runtime_carrier_readback"))
    if current_readback:
        return current_readback
    return _mapping(readback.get("opl_runtime_carrier_readback"))


def _drive_owner_action_stop_reason(readback: Mapping[str, Any]) -> str:
    current_consumption = _drive_current_opl_owner_consumption(readback)
    if current_consumption:
        next_legal_action = _optional_text(current_consumption.get("next_legal_action"))
        if next_legal_action == (
            "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
        ):
            return "current_opl_route_back_checkpoint_requires_owner_consumption"
        if next_legal_action == "record_typed_blocker":
            return "current_opl_terminal_closeout_requires_typed_blocker"
        return "current_opl_transition_receipt_requires_owner_consumption"
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


__all__ = ["build_paper_mission_drive_readback"]
