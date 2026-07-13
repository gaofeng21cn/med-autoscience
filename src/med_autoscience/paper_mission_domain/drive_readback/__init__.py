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
from med_autoscience.domain_route_profile import (
    build_domain_route_handoff_intake_readback,
)
from med_autoscience.paper_mission_stage_run_readback import (
    paper_mission_stage_run_context_readback,
)


def build_paper_mission_drive_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: str | Path | None,
    run_id: str | None,
    opl_runtime_payload: Mapping[str, Any] | None,
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
            opl_runtime_payload=opl_runtime_payload,
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
        opl_runtime_payload=opl_runtime_payload,
    )
    handoff = _mapping(consume_readback.get("opl_route_handoff"))
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
    opl_runtime_handoff = _opl_runtime_handoff_readback(
        handoff=handoff,
        stage_closure_decision=initial_stage_closure_decision,
    )
    stage_closure_decision = stage_closure_decision_projection(
        readback=consume_readback,
        handoff=handoff,
    )
    drive_result = _paper_mission_drive_result(
        consume_readback=consume_readback,
        handoff=handoff,
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
        "drive_mode": "package_consume_and_handoff",
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
        "ai_route_context": consume_readback["ai_route_context"],
        "opl_stage_run_context": consume_readback["opl_stage_run_context"],
        "opl_stage_attempt_readback": consume_readback[
            "opl_stage_attempt_readback"
        ],
        "opl_stage_attempt_readback_status": consume_readback[
            "opl_stage_attempt_readback_status"
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
        "opl_runtime_handoff": opl_runtime_handoff,
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
            "writes_runtime": False,
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
            "writes_runtime": False,
        },
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "drive_result": drive_result,
    }


def _opl_runtime_handoff_readback(
    *,
    handoff: Mapping[str, Any],
    stage_closure_decision: Mapping[str, Any],
) -> dict[str, Any]:
    if stage_closure_decision_missing(stage_closure_decision):
        return {
            "status": "blocked",
            "reason": "stage_closure_decision_missing",
            "writes_runtime": False,
            "next_owner": "MedAutoScience.stage_closure_terminalizer",
        }
    route_intake = build_domain_route_handoff_intake_readback(handoff)
    return {
        "surface_kind": "mas_opl_runtime_handoff",
        "schema_version": 1,
        "status": "handoff_required",
        "next_owner": "one-person-lab",
        "required_next_action": "submit_typed_domain_route_request",
        "writes_runtime": False,
        "opl_stage_run_context": _mapping(handoff.get("opl_stage_run_context")),
        "route_command": _mapping(handoff.get("ai_route_context")),
        "runtime_request": _mapping(route_intake.get("runtime_request")),
        "blockers": route_intake.get("blockers") or [],
    }


def _drive_direct_next_action_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: Path,
    opl_runtime_payload: Mapping[str, Any] | None,
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
    carrier = _mapping(handoff.get("opl_stage_run_context"))
    carrier_readback = paper_mission_stage_run_context_readback(
        carrier=carrier,
        study_root=Path(profile.studies_root) / study_id,
        opl_runtime_payload=opl_runtime_payload,
    )
    drive_result = _drive_direct_next_action_result(
        handoff=handoff,
        carrier_readback=carrier_readback,
    )
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
        "ai_route_context": handoff["ai_route_context"],
        "opl_stage_run_context": carrier,
        "opl_stage_attempt_readback": carrier_readback,
        "opl_stage_attempt_readback_status": carrier_readback["carrier_status"],
        "opl_route_handoff": handoff,
        "opl_runtime_handoff": _opl_runtime_handoff_readback(
            handoff=handoff,
            stage_closure_decision={},
        ),
        "transaction_state": "domain_transition_direct_stage_attempt",
        "consume_candidate_status": "not_applicable_domain_transition_direct",
        "next_owner_or_human_decision": {
            "kind": "owner_or_route",
            "next_owner": _optional_text(next_action.get("owner"))
            or _optional_text(next_action.get("stage_id")),
            "human_decision_required": False,
            "summary": "MAS domain transition selected a concrete OPL stage attempt.",
            "can_execute": False,
            "can_authorize_provider_attempt": False,
        },
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": False,
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
            "writes_runtime": False,
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
) -> dict[str, Any] | None:
    inspect_readback = consume_candidate_readback_builder(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="inspect",
        source=f"{source}:drive:canonical-next-action-inspect",
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
    # Owner-consumption/readback shapes are optional evidence. Codex may route
    # forward or back without waiting for this legacy no-redrive projection.
    return None

__all__ = ["build_paper_mission_drive_readback"]
