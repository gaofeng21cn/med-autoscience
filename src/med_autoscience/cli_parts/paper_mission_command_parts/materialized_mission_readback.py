from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping
from typing import Any

from med_autoscience.cli_parts.paper_mission_command_parts.command_metadata import (
    PAPER_MISSION_CONTRACT_REF,
    PAPER_MISSION_CONTRACT_VERSION,
    PAPER_MISSION_START_OR_RESUME_TASK_KIND,
    action_intent as _action_intent,
    validate_with_contract_if_available as _validate_with_contract_if_available,
)
from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _load_json_object,
    _mapping,
    _optional_text,
)
from med_autoscience.cli_parts.paper_mission_command_parts.direct_next_action_handoff import (
    build_direct_next_action_handoff,
)
from med_autoscience.cli_parts.paper_mission_command_parts.materialized_readback_context import (
    consume_candidate_status as _consume_candidate_status,
    materialized_opl_route_command as _materialized_opl_route_command,
    materialized_stage_terminal_decision as _materialized_stage_terminal_decision,
    materialized_study_id as _materialized_study_id,
    materialized_study_root as _materialized_study_root,
    normalize_materialized_mission_for_cli_readback as _normalize_materialized_mission_for_cli_readback,
    paper_facing_action_fields as _paper_facing_action_fields,
)
from med_autoscience.cli_parts.paper_mission_command_parts.one_shot_migration import (
    ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES,
)
from med_autoscience.cli_parts.paper_mission_command_parts.projection_fields import (
    latest_materialized_mission_path as _latest_materialized_mission_path,
    paper_mission_delivery_projection_fields as _paper_mission_delivery_projection_fields,
    paper_mission_inspect_projection_fields as _paper_mission_inspect_projection_fields,
    paper_mission_materialized_projection_fields as _paper_mission_materialized_projection_fields,
)
from med_autoscience.cli_parts.paper_mission_command_parts.receipt_owner_consumption import (
    latest_receipt_owner_consumption_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts.stage_closure_next_action import (
    merge_stage_closure_typed_blocker_gate_fields as _merge_stage_closure_typed_blocker_gate_fields,
    next_action_for_stage_closure_decision as _next_action_for_stage_closure_decision,
)
from med_autoscience.cli_parts.paper_mission_command_parts.stage_closure_terminalizer import (
    latest_current_stage_closure_for_consumption as _latest_current_stage_closure_for_consumption,
    stage_closure_decision_requires_reterminalize as _stage_closure_decision_requires_reterminalize,
    terminalize_stage_closure_from_readback as _terminalize_stage_closure_from_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts.transaction_readback import (
    FORBIDDEN_AUTHORITY_CLAIMS,
    PAPER_AUDIT_PACK_FAMILIES,
    _consume_result_for_consumption_ledger_readback,
    _durable_mission_stop_guard,
    _mission_state_for_materialized_readback,
    _next_owner_decision_for_consumption_ledger_readback,
    _paper_mission_transaction_readback,
    _submission_authority_owner_gate_readback,
    _transaction_readback_output_fields,
)
from med_autoscience.cli_parts.paper_mission_command_parts.typed_blocker_resolution import (
    latest_typed_blocker_resolution_readback,
)
from med_autoscience.controllers.paper_mission_currentness import (
    receipt_owner_consumption_superseded_by_stage_closure as _receipt_superseded_by_stage_closure,
    receipt_owner_consumption_superseded_by_consumption as _receipt_superseded_by_consumption,
)
from med_autoscience.controllers import study_domain_transition_table
from med_autoscience.controllers.study_progress_parts.canonical_next_action_selection import (
    domain_transition_canonical_next_action as _domain_transition_canonical_next_action,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_missing,
    stage_closure_decision_projection,
)
from med_autoscience.paper_mission_consumption_readback import (
    latest_paper_mission_consumption_transaction_readback,
)
from med_autoscience.paper_mission_opl_readback import (
    paper_mission_opl_runtime_carrier_readback,
)


def build_materialized_mission_readback_if_available(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    paper_mission_command: str,
    dry_run: bool,
    source: str,
    enable_opl_live_probe: bool = False,
    opl_bin: str | Path | None = None,
) -> dict[str, Any] | None:
    mission_path = _latest_materialized_mission_path(
        workspace_root=Path(profile.workspace_root),
        study_id=study_id,
    )
    if mission_path is None:
        return None
    mission = _normalize_materialized_mission_for_cli_readback(
        mission=_load_json_object(mission_path),
        study_id=study_id,
        paper_mission_command=paper_mission_command,
        paper_audit_pack_families=PAPER_AUDIT_PACK_FAMILIES,
    )
    default_readback = (
        dict(mission["one_shot_migration_readback"])
        if isinstance(mission.get("one_shot_migration_readback"), dict)
        else {}
    )
    candidate_manifest_path = mission_path.parent / "candidate_manifest.json"
    candidate_manifest = (
        _load_json_object(candidate_manifest_path)
        if candidate_manifest_path.exists()
        else None
    )
    resolved_study_id = _materialized_study_id(
        mission=mission,
        requested_study_id=study_id,
    )
    resolved_study_root = _materialized_study_root(
        profile=profile,
        requested_study_id=study_id,
        mission=mission,
        mission_path=mission_path,
    )
    consumption_ledger_readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=resolved_study_id,
    )
    transaction_readback = _paper_mission_transaction_readback(
        mission_id=str(mission["mission_id"]),
        study_id=resolved_study_id,
        objective=str(mission["objective"]),
        paper_mission_command=paper_mission_command,
        study_root=resolved_study_root,
        mission=mission,
        transaction_override=_mapping(
            (consumption_ledger_readback or {}).get("paper_mission_transaction")
        ),
        transaction_source_override=(
            "paper_mission_consumption_ledger"
            if consumption_ledger_readback is not None
            else None
        ),
        authority_consume_readback=None,
        enable_opl_live_probe=enable_opl_live_probe,
        opl_bin=opl_bin,
    )
    if consumption_ledger_readback is not None:
        transaction_readback["next_owner_or_human_decision"] = (
            _next_owner_decision_for_consumption_ledger_readback(
                readback=consumption_ledger_readback,
                fallback=_mapping(transaction_readback.get("next_owner_or_human_decision")),
            )
        )
    mission = {
        **mission,
        "mission_state": _mission_state_for_materialized_readback(
            mission=mission,
            transaction_readback=transaction_readback,
            consumption_ledger_readback=consumption_ledger_readback,
        ),
        "paper_mission_transaction": transaction_readback[
            "paper_mission_transaction"
        ],
        **(
            {
                "consume_result": _consume_result_for_consumption_ledger_readback(
                    consumption_ledger_readback
                )
            }
            if consumption_ledger_readback is not None
            else {}
        ),
    }
    validation = _validate_with_contract_if_available(mission)
    projection_fields = _paper_mission_materialized_projection_fields(
        transaction_readback=transaction_readback
    )
    projection_fields = {
        **projection_fields,
        **_paper_mission_delivery_projection_fields(
            profile=profile,
            profile_ref=profile_ref,
            study_root=resolved_study_root,
        ),
    }
    consume_candidate_status = (
        transaction_readback.get("consume_candidate_status_override")
        or _optional_text((consumption_ledger_readback or {}).get("consume_candidate_status"))
        or _consume_candidate_status(mission, default_readback)
    )
    stage_closure_ledger_readback = _latest_current_stage_closure_for_consumption(
        workspace_root=Path(profile.workspace_root),
        study_id=resolved_study_id,
        transaction_ref=_optional_text(
            transaction_readback["paper_mission_transaction"].get("transaction_id")
        ),
        consume_readback=consumption_ledger_readback or transaction_readback,
    )
    receipt_owner_consumption_readback = latest_receipt_owner_consumption_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=resolved_study_id,
    )
    if receipt_owner_consumption_readback is not None and _receipt_superseded_by_consumption(
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
        consumption_ledger_readback=consumption_ledger_readback,
    ):
        receipt_owner_consumption_readback = None
    if receipt_owner_consumption_readback is not None and _receipt_superseded_by_stage_closure(
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
        stage_closure_ledger_readback=stage_closure_ledger_readback,
    ):
        receipt_owner_consumption_readback = None
    typed_blocker_resolution_readback = latest_typed_blocker_resolution_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=resolved_study_id,
    )
    effective_consume_candidate_status = (
        "typed_blocker"
        if receipt_owner_consumption_readback is not None
        else consume_candidate_status
    )
    stage_closure_decision = stage_closure_decision_projection(
        readback={
            **transaction_readback,
            **(
                {
                    "stage_closure_decision": receipt_owner_consumption_readback[
                        "stage_closure_decision"
                    ]
                }
                if receipt_owner_consumption_readback is not None
                else {"stage_closure_decision": stage_closure_ledger_readback}
                if stage_closure_ledger_readback is not None
                else {}
            ),
            "consume_candidate_status": effective_consume_candidate_status,
            "route_back_budget": projection_fields.get("route_back_budget"),
            "current_package": projection_fields.get("current_package"),
        },
        handoff=_mapping(
            (consumption_ledger_readback or {}).get("opl_route_handoff")
        ),
        consumption_ledger_readback=consumption_ledger_readback,
    )
    if stage_closure_decision_missing(
        stage_closure_decision
    ) or _stage_closure_decision_requires_reterminalize(
        stage_closure_decision,
        current_package=projection_fields.get("current_package"),
    ):
        stage_closure_decision = _terminalize_stage_closure_from_readback(
            {
                **transaction_readback,
                "consume_candidate_status": consume_candidate_status,
                "route_back_budget": projection_fields.get("route_back_budget"),
                "current_package": projection_fields.get("current_package"),
                **(
                    {
                        "stage_closure_decision": receipt_owner_consumption_readback[
                            "stage_closure_decision"
                        ]
                    }
                    if receipt_owner_consumption_readback is not None
                    else {"stage_closure_decision": stage_closure_ledger_readback}
                    if stage_closure_ledger_readback is not None
                    else {}
                ),
            }
        )
    domain_transition = study_domain_transition_table.project_domain_transition(
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )
    domain_transition_next_action = _domain_transition_canonical_next_action(
        {"domain_transition": domain_transition}
    )
    next_action_override = _next_action_for_stage_closure_decision(
        stage_closure_decision=stage_closure_decision,
        transaction_readback=transaction_readback,
        typed_blocker_resolution_readback=typed_blocker_resolution_readback,
    )
    canonical_next_action_source = None
    stage_closure_suppresses_domain_transition = (
        _stage_closure_suppresses_domain_transition_next_action(
            stage_closure_decision=stage_closure_decision,
            next_action=next_action_override,
            domain_transition_next_action=domain_transition_next_action,
        )
    )
    if (
        domain_transition_next_action
        and not _typed_blocker_resolution_should_own_next_action(
            stage_closure_decision=stage_closure_decision,
            typed_blocker_resolution_readback=typed_blocker_resolution_readback,
            domain_transition_next_action=domain_transition_next_action,
        )
        and not _stage_closure_next_action_should_own_next_action(
            stage_closure_decision=stage_closure_decision,
            next_action=next_action_override,
            domain_transition_next_action=domain_transition_next_action,
        )
        and not stage_closure_suppresses_domain_transition
    ):
        next_action_override = domain_transition_next_action
        canonical_next_action_source = "domain_transition.next_action"
        typed_blocker_resolution_readback = None
    elif stage_closure_suppresses_domain_transition:
        next_action_override = None
        typed_blocker_resolution_readback = None
    elif next_action_override is not None:
        canonical_next_action_source = "stage_closure.next_action"
    transaction_output_fields = _transaction_readback_output_fields(transaction_readback)
    if next_action_override is not None:
        transaction_output_fields["next_action"] = next_action_override
        if canonical_next_action_source is not None:
            transaction_output_fields["canonical_next_action_source"] = (
                canonical_next_action_source
            )
        transaction_output_fields["paper_mission_transaction_readback"] = {
            **transaction_readback,
            "next_action": next_action_override,
        }
        direct_next_action_runtime = (
            _domain_transition_direct_next_action_runtime_readback(
                profile=profile,
                study_id=resolved_study_id,
                study_root=resolved_study_root,
                inspect_readback={**mission, **transaction_output_fields},
                next_action=next_action_override,
                canonical_next_action_source=canonical_next_action_source,
                enable_opl_live_probe=enable_opl_live_probe,
                opl_bin=opl_bin,
            )
        )
        if direct_next_action_runtime:
            transaction_output_fields["domain_transition_direct_stage_attempt"] = (
                direct_next_action_runtime
            )
            transaction_output_fields["current_opl_runtime_carrier"] = (
                direct_next_action_runtime["opl_runtime_carrier"]
            )
            transaction_output_fields["current_opl_runtime_carrier_readback"] = (
                direct_next_action_runtime["opl_runtime_carrier_readback"]
            )
            transaction_output_fields["current_opl_runtime_readback_status"] = (
                direct_next_action_runtime["opl_runtime_readback_status"]
            )
    transaction_output_fields = _merge_stage_closure_typed_blocker_gate_fields(
        transaction_output_fields=transaction_output_fields,
        stage_closure_decision=stage_closure_decision,
        next_action=next_action_override,
    )
    submission_gate_readback = _submission_authority_owner_gate_readback(
        study_root=Path(profile.studies_root) / resolved_study_id,
        study_id=resolved_study_id,
        next_action=_mapping(transaction_output_fields.get("next_action")),
    )
    if submission_gate_readback is not None:
        transaction_output_fields.pop("next_action", None)
        readback_payload = _mapping(
            transaction_output_fields.get("paper_mission_transaction_readback")
        )
        if readback_payload:
            readback_payload.pop("next_action", None)
            transaction_output_fields["paper_mission_transaction_readback"] = readback_payload
        if typed_blocker_resolution_readback is not None:
            typed_blocker_resolution_readback = {
                **typed_blocker_resolution_readback,
                "next_owner_action": None,
                "submission_authority_owner_gate_readback": submission_gate_readback,
            }
    paper_facing_action_fields = _paper_facing_action_fields(
        readback={
            "study_id": resolved_study_id,
            **transaction_output_fields,
            "typed_blocker_resolution_readback": typed_blocker_resolution_readback,
            "submission_authority_owner_gate_readback": submission_gate_readback,
        }
    )
    return {
        "surface_kind": "paper_mission_materialized_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": paper_mission_command,
        "action_intent": _action_intent(paper_mission_command),
        "source": source,
        "dry_run": bool(dry_run),
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "requested_study_id": study_id,
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "study_root_exists": resolved_study_root.exists(),
        "mission_id": mission["mission_id"],
        "objective": mission["objective"],
        "mission_state": mission["mission_state"],
        "materialized_mission_ref": str(mission_path),
        **transaction_output_fields,
        **projection_fields,
        **(
            {
                "receipt_owner_consumption_readback": (
                    receipt_owner_consumption_readback
                ),
                "receipt_evidence": receipt_owner_consumption_readback.get(
                    "receipt_evidence"
                ),
                "mas_receipt_consumption": receipt_owner_consumption_readback.get(
                    "mas_receipt_consumption"
                ),
            }
            if receipt_owner_consumption_readback is not None
            else {}
        ),
        **(
            {"typed_blocker_resolution_readback": typed_blocker_resolution_readback}
            if typed_blocker_resolution_readback is not None
            else {}
        ),
        **(
            {"submission_authority_owner_gate_readback": submission_gate_readback}
            if submission_gate_readback is not None
            else {}
        ),
        **paper_facing_action_fields,
        **(
            {"candidate_manifest_ref": str(candidate_manifest_path)}
            if candidate_manifest_path.exists()
            else {}
        ),
        "paper_mission_run": mission,
        "paper_mission_transaction": transaction_readback[
            "paper_mission_transaction"
        ],
        "stage_terminal_decision": transaction_readback["stage_terminal_decision"],
        "opl_route_command": transaction_readback["opl_route_command"],
        "stage_closure_decision": stage_closure_decision,
        "stage_closure_decision_ref": stage_closure_decision.get("decision_ref"),
        "stage_closure_outcome": _mapping(
            stage_closure_decision.get("outcome")
        ).get("kind"),
        "domain_transition": domain_transition,
        **_paper_mission_inspect_projection_fields(
            stage_closure_decision=stage_closure_decision,
            projection_fields=projection_fields,
        ),
        "durable_mission_stop_guard": _durable_mission_stop_guard(
            consume_candidate_status=effective_consume_candidate_status,
            stage_closure_decision=stage_closure_decision,
        ),
        "default_readback": default_readback,
        **(
            {"candidate_manifest": candidate_manifest}
            if candidate_manifest is not None
            else {}
        ),
        **(
            {
                "paper_mission_consumption_ledger_readback": (
                    consumption_ledger_readback
                ),
                "paper_mission_current_transaction_source": (
                    "paper_mission_consumption_ledger"
                ),
            }
            if consumption_ledger_readback is not None
            else {}
        ),
        **(
            {"paper_mission_stage_closure_ledger_readback": stage_closure_ledger_readback}
            if stage_closure_ledger_readback is not None
            else {}
        ),
        "consume_candidate_status": consume_candidate_status,
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "writes_candidate_workspace": False,
            "dry_run_only": True,
            "forbidden_authority_writes": list(
                ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES
            ),
        },
        "forbidden_authority_writes": list(ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "contract_validation": validation,
        "dispatch_plan": {
            "default_action_intent": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_task_kind": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_dispatch_mode": "materialized_mission_readback_no_write",
            "old_owner_callable_dispatch_role": "diagnostic_or_migration_only",
            "opl_consumes": "paper_mission_transaction.opl_route_command",
            "mas_terminalizes": "paper_mission_transaction.stage_terminal_decision",
        },
        "cutover_proof": {
            "default_readback_surface": "PaperMissionRun",
            "terminalizer_surface": "PaperMissionTransaction",
            "materialized_paper_mission_run_loaded": True,
            "stage_terminal_decision_present": bool(
                _materialized_stage_terminal_decision(mission)
            ),
            "opl_route_command_present": bool(_materialized_opl_route_command(mission)),
            "legacy_blocker_controls_default_execution": False,
            "authority_materialized": False,
        },
    }


def _receipt_superseded_by_consumption(
    *,
    receipt_owner_consumption_readback: dict[str, Any],
    consumption_ledger_readback: dict[str, Any] | None,
) -> bool:
    if consumption_ledger_readback is None:
        return False
    receipt_mtime = _path_mtime(
        _optional_text(receipt_owner_consumption_readback.get("source_ref"))
    )
    consume_mtime = _path_mtime(
        _optional_text(consumption_ledger_readback.get("source_ref"))
    )
    if receipt_mtime is None or consume_mtime is None or consume_mtime <= receipt_mtime:
        return False
    if _receipt_is_consumed_typed_blocker(
        receipt_owner_consumption_readback
    ) and _consumption_is_non_advancing_route_back(consumption_ledger_readback):
        return False
    if (
        _optional_text(consumption_ledger_readback.get("route_handoff_status"))
        == "ready_for_opl_route_command"
    ):
        return True
    handoff = _mapping(consumption_ledger_readback.get("opl_route_handoff"))
    return (
        _optional_text(handoff.get("handoff_status")) == "ready_for_opl_route_command"
        and handoff.get("can_submit_to_opl_runtime") is True
    )


def _receipt_is_consumed_typed_blocker(receipt: Mapping[str, Any]) -> bool:
    if _optional_text(receipt.get("status")) != "owner_consumption_applied":
        return False
    consumption = _mapping(receipt.get("mas_receipt_consumption"))
    if _optional_text(consumption.get("status")) == "owner_consumed_typed_blocker":
        return True
    decision = _mapping(receipt.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    return _optional_text(outcome.get("kind")) == "typed_blocker"


def _consumption_is_non_advancing_route_back(
    consumption_ledger_readback: Mapping[str, Any],
) -> bool:
    stage_decision = _mapping(consumption_ledger_readback.get("stage_terminal_decision"))
    handoff = _mapping(consumption_ledger_readback.get("opl_route_handoff"))
    handoff_decision = _mapping(handoff.get("stage_terminal_decision"))
    opl_route_command = _mapping(consumption_ledger_readback.get("opl_route_command")) or _mapping(
        handoff.get("opl_route_command")
    )
    route_command_kind = _optional_text(opl_route_command.get("command_kind")) or _optional_text(
        handoff.get("route_command_kind")
    )
    transaction_state = _optional_text(consumption_ledger_readback.get("transaction_state")) or _optional_text(
        handoff.get("transaction_state")
    )
    decision_kind = _optional_text(stage_decision.get("decision_kind")) or _optional_text(
        handoff_decision.get("decision_kind")
    )
    decision_status = _optional_text(stage_decision.get("status")) or _optional_text(
        handoff_decision.get("status")
    )
    reason = _optional_text(stage_decision.get("reason")) or _optional_text(
        handoff_decision.get("reason")
    )
    if route_command_kind == "route_back":
        return True
    if transaction_state == "route_back":
        return True
    if decision_kind == "route_back" or decision_status == "route_back":
        return True
    return reason == "paper_mission_stage_route_domain_gate_pending"


def _typed_blocker_resolution_should_own_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    typed_blocker_resolution_readback: Mapping[str, Any] | None,
    domain_transition_next_action: Mapping[str, Any] | None = None,
) -> bool:
    if not typed_blocker_resolution_readback:
        return False
    outcome = _mapping(stage_closure_decision.get("outcome"))
    if outcome.get("kind") != "typed_blocker":
        return False
    return bool(_mapping(typed_blocker_resolution_readback.get("next_owner_action")))


def _domain_transition_direct_next_action_runtime_readback(
    *,
    profile: Any,
    study_id: str,
    study_root: Path,
    inspect_readback: Mapping[str, Any],
    next_action: Mapping[str, Any],
    canonical_next_action_source: str | None,
    enable_opl_live_probe: bool,
    opl_bin: str | Path | None,
) -> dict[str, Any]:
    if canonical_next_action_source != "domain_transition.next_action":
        return {}
    if not _domain_transition_next_action_requests_stage_attempt(next_action):
        return {}
    handoff = build_direct_next_action_handoff(
        profile=profile,
        study_id=study_id,
        inspect_readback=inspect_readback,
        next_action=next_action,
    )
    carrier = _mapping(handoff.get("opl_runtime_carrier"))
    carrier_readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=enable_opl_live_probe,
        opl_bin=opl_bin,
    )
    return {
        "surface_kind": "paper_mission_domain_transition_direct_stage_attempt_readback",
        "schema_version": 1,
        "canonical_next_action_source": canonical_next_action_source,
        "next_action": dict(next_action),
        "opl_route_handoff": handoff,
        "paper_mission_transaction": handoff["paper_mission_transaction"],
        "stage_terminal_decision": handoff["stage_terminal_decision"],
        "opl_route_command": handoff["opl_route_command"],
        "opl_runtime_carrier": carrier,
        "opl_runtime_carrier_readback": carrier_readback,
        "opl_runtime_readback_status": carrier_readback["carrier_status"],
        "transaction_state": "domain_transition_direct_stage_attempt",
        "consume_candidate_status": "not_applicable_domain_transition_direct",
        "authority_boundary": {
            "surface_role": "current_next_action_runtime_projection",
            "mas_authority_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "writes_authority_surface": False,
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_runtime_queue": False,
            "writes_provider_attempt": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
        },
    }


def _stage_closure_next_action_should_own_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    next_action: Mapping[str, Any] | None,
    domain_transition_next_action: Mapping[str, Any] | None = None,
) -> bool:
    action = _mapping(next_action)
    if not action:
        return False
    outcome = _mapping(stage_closure_decision.get("outcome"))
    if (
        _mapping(domain_transition_next_action)
        and outcome.get("kind") == "next_stage_transition"
        and outcome.get("transition_kind") == "route_back_candidate_checkpoint"
    ):
        return False
    if _optional_text(action.get("action_family")) == (
        "paper.stage_closure.owner_consumption"
    ):
        return True
    if _optional_text(action.get("action_family")) in {
        "paper.delivery.sync",
        "paper.delivery_sync",
    }:
        return True
    return (
        outcome.get("kind") == "next_stage_transition"
        and outcome.get("transition_kind")
        in {"route_back_candidate_checkpoint", "current_package_mirror_sync"}
    )


def _stage_closure_suppresses_domain_transition_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    next_action: Mapping[str, Any] | None,
    domain_transition_next_action: Mapping[str, Any] | None,
) -> bool:
    action_override = _mapping(next_action)
    if _stage_closure_next_action_should_own_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=action_override,
        domain_transition_next_action=domain_transition_next_action,
    ):
        return False
    action = _mapping(domain_transition_next_action)
    if not action:
        return False
    outcome = _mapping(stage_closure_decision.get("outcome"))
    if outcome.get("kind") != "owner_receipt":
        return False
    if (
        outcome.get("can_submit") is True
        and outcome.get("package_kind") == "submission_ready_package"
    ):
        return False
    decision_work_unit = _optional_text(stage_closure_decision.get("work_unit_id"))
    action_work_unit = _optional_text(action.get("work_unit_id"))
    if decision_work_unit is None or action_work_unit != decision_work_unit:
        return False
    decision_stage = _optional_text(stage_closure_decision.get("stage_id"))
    action_stage = _optional_text(action.get("stage_id"))
    return (
        decision_stage is None
        or action_stage is None
        or decision_stage == action_stage
    )


def _domain_transition_next_action_requests_stage_attempt(
    next_action: Mapping[str, Any] | None,
) -> bool:
    action = _mapping(next_action)
    if _optional_text(action.get("surface_kind")) != "mas_next_action_envelope":
        return False
    if _optional_text(action.get("action_type")) == "request_opl_stage_attempt":
        return True
    return (
        _optional_text(action.get("action_family")) is not None
        and _optional_text(action.get("owner")) is not None
        and _optional_text(action.get("work_unit_id")) is not None
    )


def _path_mtime(path_text: str | None) -> float | None:
    if path_text is None:
        return None
    try:
        return Path(path_text).expanduser().resolve().stat().st_mtime
    except OSError:
        return None
