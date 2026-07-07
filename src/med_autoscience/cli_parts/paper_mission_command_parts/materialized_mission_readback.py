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
    _first_text,
    _dedupe_optional_texts,
    _load_json_object,
    _mapping,
    _mapping_list,
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
from med_autoscience.cli_parts.paper_mission_command_parts.materialized_mission_readback_parts.owner_consumption import (
    _align_current_carrier_owner_consumption,
    _add_stage_attempt_identity,
    _carrier_matches_owner_consumed_stage_attempt,
    _carrier_stage_attempt_identities,
    _consumption_is_non_advancing_route_back,
    _path_mtime,
    _preserve_direct_successor_runtime_readback,
    _receipt_is_consumed_typed_blocker,
    _receipt_owner_consumption_stage_attempt_identities,
    _receipt_superseded_by_consumption,
)
from med_autoscience.cli_parts.paper_mission_command_parts.stage_closure_terminalizer_readback_parts.owner_consumption_alignment import (
    _receipt_owner_consumed_route_checkpoint,
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
)
from med_autoscience.controllers import study_domain_transition_table
from med_autoscience.controllers.study_progress_parts.canonical_next_action_selection import (
    domain_transition_canonical_next_action as _domain_transition_canonical_next_action,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_missing,
    stage_closure_decision_projection,
)
from med_autoscience.controllers.study_transition_receipt_consumption import (
    mas_owner_apply_receipt_consumption as _mas_owner_apply_receipt_consumption,
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
        authority_consume_readback=(
            dict(consumption_ledger_readback)
            if consumption_ledger_readback is not None
            else None
        ),
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
    owner_repair_receipt_readback = _owner_repair_receipt_consumption_readback(
        study_root=resolved_study_root,
        study_id=resolved_study_id,
    )
    if _owner_repair_receipt_is_newer(
        candidate=owner_repair_receipt_readback,
        current=receipt_owner_consumption_readback,
    ):
        receipt_owner_consumption_readback = owner_repair_receipt_readback
    stage_closure_ledger_readback_for_output = _stage_closure_ledger_readback_for_output(
        stage_closure_ledger_readback=stage_closure_ledger_readback,
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
    )
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
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
    )
    canonical_next_action_source = None
    stage_closure_suppresses_domain_transition = _stage_closure_suppresses_domain_transition_next_action(stage_closure_decision=stage_closure_decision, next_action=next_action_override, domain_transition_next_action=domain_transition_next_action, receipt_owner_consumption_readback=receipt_owner_consumption_readback)
    if (
        domain_transition_next_action
        and not _terminalizer_readback_helpers()._typed_blocker_resolution_should_own_next_action(
            stage_closure_decision=stage_closure_decision,
            typed_blocker_resolution_readback=typed_blocker_resolution_readback,
            domain_transition_next_action=domain_transition_next_action,
        )
        and not _stage_closure_next_action_should_own_next_action(
            stage_closure_decision=stage_closure_decision,
            next_action=next_action_override,
            domain_transition_next_action=domain_transition_next_action,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
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
    if _stage_closure_owner_receipt_suppresses_transaction_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action_override=next_action_override,
    ):
        transaction_output_fields.pop("next_action", None)
        transaction_output_fields.pop("canonical_next_action_source", None)
    transaction_output_fields = (
        suppress_consumed_route_checkpoint_transaction_next_action(
            transaction_output_fields=transaction_output_fields,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
        )
    )
    if next_action_override is not None:
        transaction_output_fields = _transaction_output_fields_with_next_action(
            transaction_output_fields=transaction_output_fields,
            transaction_readback=transaction_readback,
            next_action=next_action_override,
            canonical_next_action_source=canonical_next_action_source,
        )
        (
            stage_closure_decision,
            next_action_override,
            canonical_next_action_source,
            transaction_output_fields,
        ) = _apply_direct_next_action_runtime(
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            mission=mission,
            transaction_output_fields=transaction_output_fields,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
            next_action=next_action_override,
            next_action_override=next_action_override,
            canonical_next_action_source=canonical_next_action_source,
            stage_closure_decision=stage_closure_decision,
            transaction_readback=transaction_readback,
            typed_blocker_resolution_readback=typed_blocker_resolution_readback,
            enable_opl_live_probe=enable_opl_live_probe,
            opl_bin=opl_bin,
        )
    if (
        "domain_transition_direct_stage_attempt" not in transaction_output_fields
        and stage_closure_suppresses_domain_transition
        and domain_transition_next_action
    ):
        (
            stage_closure_decision,
            next_action_override,
            canonical_next_action_source,
            transaction_output_fields,
        ) = _apply_direct_next_action_runtime(
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            mission=mission,
            transaction_output_fields=transaction_output_fields,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
            next_action=domain_transition_next_action,
            next_action_override=next_action_override,
            canonical_next_action_source="domain_transition.next_action",
            stage_closure_decision=stage_closure_decision,
            transaction_readback=transaction_readback,
            typed_blocker_resolution_readback=typed_blocker_resolution_readback,
            enable_opl_live_probe=enable_opl_live_probe,
            opl_bin=opl_bin,
        )
    if receipt_owner_consumption_readback is not None:
        transaction_output_fields = _align_current_carrier_owner_consumption(
            transaction_output_fields=transaction_output_fields,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
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
    receipt_owner_fields = {} if receipt_owner_consumption_readback is None else {
        "receipt_owner_consumption_readback": receipt_owner_consumption_readback,
        "receipt_evidence": receipt_owner_consumption_readback.get("receipt_evidence"),
        "mas_receipt_consumption": receipt_owner_consumption_readback.get("mas_receipt_consumption"),
    }
    consumption_fields = {} if consumption_ledger_readback is None else {
        "paper_mission_consumption_ledger_readback": consumption_ledger_readback,
        "paper_mission_current_transaction_source": "paper_mission_consumption_ledger",
    }
    stage_closure_fields = {} if stage_closure_ledger_readback_for_output is None else {
        "paper_mission_stage_closure_ledger_readback": stage_closure_ledger_readback_for_output
    }
    return {
        "surface_kind": "paper_mission_materialized_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": paper_mission_command,
        "action_intent": _action_intent(paper_mission_command),
        "source": source,
        "dry_run": bool(dry_run),
        "profile": {"profile_name": str(getattr(profile, "name", "")), "profile_ref": str(profile_ref)},
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
        **receipt_owner_fields,
        **({"typed_blocker_resolution_readback": typed_blocker_resolution_readback} if typed_blocker_resolution_readback is not None else {}),
        **({"submission_authority_owner_gate_readback": submission_gate_readback} if submission_gate_readback is not None else {}),
        **paper_facing_action_fields,
        **({"candidate_manifest_ref": str(candidate_manifest_path)} if candidate_manifest_path.exists() else {}),
        "paper_mission_run": mission,
        "paper_mission_transaction": transaction_readback["paper_mission_transaction"],
        "stage_terminal_decision": transaction_readback["stage_terminal_decision"],
        "opl_route_command": transaction_readback["opl_route_command"],
        "stage_closure_decision": stage_closure_decision,
        "stage_closure_decision_ref": stage_closure_decision.get("decision_ref"),
        "stage_closure_outcome": _mapping(stage_closure_decision.get("outcome")).get("kind"),
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
        **({"candidate_manifest": candidate_manifest} if candidate_manifest is not None else {}),
        **consumption_fields,
        **stage_closure_fields,
        "consume_candidate_status": consume_candidate_status,
        "mutation_policy": {
            **_false_fields("writes_authority", "writes_runtime", "writes_yang", "writes_yang_authority", "writes_paper_body", "writes_candidate_workspace"),
            "dry_run_only": True,
            "forbidden_authority_writes": list(ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES),
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
            "stage_terminal_decision_present": bool(_materialized_stage_terminal_decision(mission)),
            "opl_route_command_present": bool(_materialized_opl_route_command(mission)),
            "legacy_blocker_controls_default_execution": False,
            "authority_materialized": False,
        },
    }


def _false_fields(*keys: str) -> dict[str, bool]:
    return dict.fromkeys(keys, False)


def _terminalizer_readback_helpers() -> Any:
    from med_autoscience.cli_parts.paper_mission_command_parts import stage_closure_terminalizer_readback
    return stage_closure_terminalizer_readback


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
    if canonical_next_action_source not in {
        "domain_transition.next_action",
        "paper_mission_next_action_envelope",
    }:
        return {}
    if not _terminalizer_readback_helpers()._domain_transition_next_action_requests_stage_attempt(next_action):
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
            **_false_fields("writes_authority_surface", "writes_publication_eval", "writes_controller_decision", "writes_owner_receipt", "writes_typed_blocker", "writes_human_gate", "writes_current_package", "writes_runtime_queue", "writes_provider_attempt", "writes_yang_authority", "writes_paper_body", "can_claim_paper_progress", "can_claim_runtime_ready"),
        },
    }


def _transaction_output_fields_with_next_action(
    *,
    transaction_output_fields: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    next_action: Mapping[str, Any],
    canonical_next_action_source: str | None,
) -> dict[str, Any]:
    fields = dict(transaction_output_fields)
    fields["next_action"] = next_action
    if canonical_next_action_source is not None:
        fields["canonical_next_action_source"] = canonical_next_action_source
    fields["paper_mission_transaction_readback"] = {
        **transaction_readback,
        "next_action": next_action,
    }
    return fields


def _apply_direct_next_action_runtime(
    *,
    profile: Any,
    study_id: str,
    study_root: Path,
    mission: Mapping[str, Any],
    transaction_output_fields: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any] | None,
    next_action: Mapping[str, Any],
    next_action_override: Mapping[str, Any] | None,
    canonical_next_action_source: str | None,
    stage_closure_decision: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    typed_blocker_resolution_readback: Mapping[str, Any] | None,
    enable_opl_live_probe: bool,
    opl_bin: str | Path | None,
) -> tuple[Mapping[str, Any], Mapping[str, Any] | None, str | None, dict[str, Any]]:
    fields = dict(transaction_output_fields)
    direct = _domain_transition_direct_next_action_runtime_readback(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        inspect_readback={
            **mission,
            **fields,
            "receipt_owner_consumption_readback": receipt_owner_consumption_readback,
        },
        next_action=next_action,
        canonical_next_action_source=canonical_next_action_source,
        enable_opl_live_probe=enable_opl_live_probe,
        opl_bin=opl_bin,
    )
    if not direct:
        return stage_closure_decision, next_action_override, canonical_next_action_source, fields
    fields.update(
        domain_transition_direct_stage_attempt=direct,
        current_opl_runtime_carrier=direct["opl_runtime_carrier"],
        current_opl_runtime_carrier_readback=direct["opl_runtime_carrier_readback"],
        current_opl_runtime_readback_status=direct["opl_runtime_readback_status"],
    )
    stage_closure_decision, next_action_override, canonical_next_action_source = (
        _override_next_action_from_direct_terminal_closeout(
            direct_next_action_runtime=direct,
            stage_closure_decision=stage_closure_decision,
            transaction_readback=transaction_readback,
            typed_blocker_resolution_readback=typed_blocker_resolution_readback,
            next_action_override=next_action_override,
            canonical_next_action_source=canonical_next_action_source,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
        )
    )
    if next_action_override is not None:
        fields = _transaction_output_fields_with_next_action(
            transaction_output_fields=fields,
            transaction_readback=transaction_readback,
            next_action=next_action_override,
            canonical_next_action_source=canonical_next_action_source,
        )
    return stage_closure_decision, next_action_override, canonical_next_action_source, fields


def _override_next_action_from_direct_terminal_closeout(
    *,
    direct_next_action_runtime: Mapping[str, Any],
    stage_closure_decision: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    typed_blocker_resolution_readback: Mapping[str, Any] | None,
    next_action_override: Mapping[str, Any] | None,
    canonical_next_action_source: str | None,
    receipt_owner_consumption_readback: Mapping[str, Any] | None = None,
) -> tuple[Mapping[str, Any], Mapping[str, Any] | None, str | None]:
    direct = _mapping(direct_next_action_runtime)
    if _optional_text(direct.get("opl_runtime_readback_status")) != (
        "opl_runtime_terminal_readback_observed"
    ):
        return stage_closure_decision, next_action_override, canonical_next_action_source
    receipt_owner_consumption = _mapping(receipt_owner_consumption_readback)
    if (
        _optional_text(receipt_owner_consumption.get("status"))
        == "owner_consumption_applied"
        and _optional_text(
            _mapping(receipt_owner_consumption.get("mas_receipt_consumption")).get(
                "status"
            )
        )
        == "owner_consumed_route_checkpoint"
    ):
        handoff = _mapping(direct.get("opl_route_handoff"))
        applied_owner_consumption_ref = _first_text(
            receipt_owner_consumption.get("source_ref"),
            receipt_owner_consumption.get("decision_ref"),
        )
        if applied_owner_consumption_ref is not None and _optional_text(
            handoff.get("owner_consumption_readback_ref")
        ) == applied_owner_consumption_ref:
            return (
                stage_closure_decision,
                next_action_override,
                canonical_next_action_source,
            )
    carrier_readback = _mapping(direct.get("opl_runtime_carrier_readback"))
    if _optional_text(_mapping(carrier_readback.get("mas_receipt_consumption")).get("status")) != (
        "requires_mas_owner_consumption"
    ):
        return stage_closure_decision, next_action_override, canonical_next_action_source
    refreshed_stage_closure_decision = _terminalize_stage_closure_from_readback(direct)
    refreshed_next_action = _next_action_for_stage_closure_decision(
        stage_closure_decision=refreshed_stage_closure_decision,
        transaction_readback=transaction_readback,
        typed_blocker_resolution_readback=typed_blocker_resolution_readback,
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
    )
    return (
        refreshed_stage_closure_decision,
        refreshed_next_action,
        "stage_closure.next_action" if refreshed_next_action is not None else canonical_next_action_source,
    )


def _owner_repair_receipt_consumption_readback(
    *,
    study_root: Path,
    study_id: str,
) -> dict[str, Any] | None:
    consumption = _mas_owner_apply_receipt_consumption(study_root=study_root)
    if _optional_text(consumption.get("apply_result")) != "artifact_delta":
        return None
    if _optional_text(consumption.get("receipt_surface")) not in {
        "paper_repair_owner_receipt",
        "paper_story_repair_owner_receipt",
    }:
        return None
    receipt_ref = _optional_text(consumption.get("receipt_ref"))
    evidence_ref = _optional_text(consumption.get("evidence_ref"))
    if receipt_ref is None or evidence_ref is None:
        return None
    receipt_path = (study_root / receipt_ref).expanduser().resolve()
    evidence_path = (study_root / evidence_ref).expanduser().resolve()
    story_refs = _mapping_list(consumption.get("story_surface_delta_refs"))
    paper_delta_refs = _story_surface_delta_ref_texts(story_refs)
    owner_decision_refs = _dedupe_optional_texts([str(receipt_path), str(evidence_path)])
    source_ref = str(evidence_path if evidence_path.exists() else receipt_path)
    work_unit_id = _optional_text(consumption.get("work_unit_id")) or "medical_prose_write_repair"
    stage_closure_decision = {
        "surface_kind": "mas_stage_closure_decision",
        "schema_version": 1,
        "source": "study_controller_owner_repair_receipt",
        "source_surface_kind": "paper_mission_receipt_owner_consumption",
        "study_id": study_id,
        "stage_id": "write",
        "work_unit_id": work_unit_id,
        "source_ref": source_ref,
        "decision_ref": source_ref,
        "authority_materialized": True,
        "counts_as_stage_closure_terminalizer_evidence": True,
        "counts_as_owner_receipt": True,
        "can_claim_paper_progress": bool(paper_delta_refs),
        **_false_fields("writes_authority", "writes_runtime", "writes_yang_authority", "counts_as_typed_blocker", "counts_as_human_gate", "counts_as_current_package", "counts_as_runtime_truth", "can_claim_submission_ready", "can_claim_publication_ready", "can_claim_runtime_ready"),
        "receipt_evidence_ref": str(receipt_path),
        "repair_execution_evidence_ref": str(evidence_path),
        "semantic_delta": {
            "paper_delta_refs": paper_delta_refs,
            "owner_decision_refs": owner_decision_refs,
            "reviewer_delta_refs": [],
            "gate_delta_refs": [],
            "delivery_delta_refs": [],
        },
        "known_blockers": [],
        "outcome": {
            "kind": "owner_receipt",
            "next_owner": "MedAutoScience",
            "next_action": _optional_text(consumption.get("next_action")),
            "can_submit": False,
            "package_kind": None,
            "known_blockers": [],
            "authority_materialized": True,
            "resume_condition": "continue via MAS guarded apply, gate replay, or reviewer recheck surfaces",
        },
        "authority_boundary": {
            "surface_role": "paper_mission_receipt_owner_consumption",
            "authority_materialized": True,
            **_false_fields("writes_receipt_owner_consumption", "writes_owner_receipt", "writes_typed_blocker", "writes_human_gate", "writes_current_package", "writes_submission_ready_package", "writes_runtime_queue_or_provider_attempt"),
        },
    }
    return {
        "surface_kind": "paper_mission_receipt_owner_consumption",
        "schema_version": 1,
        "status": "owner_consumption_applied",
        "study_id": study_id,
        "source": "study_controller_owner_repair_receipt",
        "source_ref": source_ref,
        "decision_ref": source_ref,
        "apply_mode": "mas_owner_repair_receipt",
        "authority_materialized": True,
        "receipt_evidence": {
            "source_kind": "mas_owner_repair_execution_evidence",
            "receipt_ref": str(receipt_path),
            "evidence_ref": str(evidence_path),
            "story_surface_delta_refs": story_refs,
            "paper_delta_refs": paper_delta_refs,
        },
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "schema_version": 1,
            "status": "owner_consumed_mas_repair_delta",
            "owner_result_kind": "artifact_delta",
            "receipt_kind": consumption.get("receipt_kind"),
            "receipt_surface": consumption.get("receipt_surface"),
            "receipt_execution_status": consumption.get("receipt_execution_status"),
            "receipt_ref": str(receipt_path),
            "evidence_ref": str(evidence_path),
            "story_surface_delta_ref_count": consumption.get("story_surface_delta_ref_count"),
            "story_surface_delta_refs": story_refs,
            "next_legal_action": consumption.get("next_action"),
            "can_claim_paper_progress": bool(paper_delta_refs),
            "can_claim_publication_ready": False,
            "can_claim_submission_ready": False,
            "can_claim_runtime_ready": False,
        },
        "stage_closure_decision": stage_closure_decision,
    }


def _stage_closure_ledger_readback_for_output(
    *,
    stage_closure_ledger_readback: Mapping[str, Any] | None,
    receipt_owner_consumption_readback: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    if not _receipt_owner_consumption_is_owner_repair_delta(receipt_owner_consumption_readback):
        return stage_closure_ledger_readback
    receipt_decision = _mapping(receipt_owner_consumption_readback.get("stage_closure_decision"))
    if not receipt_decision:
        return stage_closure_ledger_readback
    if _route_checkpoint_without_semantic_delta(stage_closure_ledger_readback):
        return receipt_decision
    if _owner_repair_receipt_is_newer(
        candidate=receipt_owner_consumption_readback,
        current=stage_closure_ledger_readback,
    ):
        return receipt_decision
    return stage_closure_ledger_readback


def _receipt_owner_consumption_is_owner_repair_delta(
    receipt_owner_consumption_readback: Mapping[str, Any] | None,
) -> bool:
    receipt = _mapping(receipt_owner_consumption_readback)
    if _optional_text(receipt.get("source")) == "study_controller_owner_repair_receipt":
        return True
    mas_consumption = _mapping(receipt.get("mas_receipt_consumption"))
    return _optional_text(mas_consumption.get("status")) == "owner_consumed_mas_repair_delta"


def _route_checkpoint_without_semantic_delta(
    stage_closure_ledger_readback: Mapping[str, Any] | None,
) -> bool:
    stage_closure = _mapping(stage_closure_ledger_readback)
    outcome = _mapping(stage_closure.get("outcome"))
    if (
        _optional_text(outcome.get("kind")) != "next_stage_transition"
        or _optional_text(outcome.get("transition_kind"))
        != "route_back_candidate_checkpoint"
    ):
        return False
    return not _semantic_delta_has_refs(_mapping(stage_closure.get("semantic_delta")))


def _semantic_delta_has_refs(semantic_delta: Mapping[str, Any]) -> bool:
    for key in (
        "paper_delta_refs",
        "owner_decision_refs",
        "reviewer_delta_refs",
        "gate_delta_refs",
        "delivery_delta_refs",
        "semantic_delta_refs",
    ):
        value = semantic_delta.get(key)
        if isinstance(value, list | tuple) and len(value) > 0:
            return True
    return False


def _owner_repair_receipt_is_newer(
    *,
    candidate: Mapping[str, Any] | None,
    current: Mapping[str, Any] | None,
) -> bool:
    if candidate is None:
        return False
    if current is None:
        return True
    candidate_mtime = _path_mtime(_optional_text(candidate.get("source_ref")))
    current_mtime = _path_mtime(_optional_text(current.get("source_ref")))
    return candidate_mtime is not None and (current_mtime is None or candidate_mtime > current_mtime)


def _story_surface_delta_ref_texts(refs: list[Mapping[str, Any]]) -> list[str]:
    return _dedupe_optional_texts(
        [_first_text(ref.get("path"), ref.get("artifact_ref"), ref.get("ref")) for ref in refs]
    )


def _stage_closure_next_action_should_own_next_action(**kwargs: Any) -> bool:
    return _terminalizer_readback_helpers()._stage_closure_next_action_should_own_next_action(**kwargs)


def _stage_closure_owner_receipt_suppresses_transaction_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    next_action_override: Mapping[str, Any] | None,
) -> bool:
    if next_action_override is not None:
        return False
    outcome = _mapping(stage_closure_decision.get("outcome"))
    return _optional_text(outcome.get("kind")) == "owner_receipt" and not (
        _optional_text(outcome.get("package_kind")) == "submission_ready_package"
        and outcome.get("can_submit") is True
    )


def suppress_consumed_route_checkpoint_transaction_next_action(
    *,
    transaction_output_fields: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not _receipt_owner_consumed_route_checkpoint(receipt_owner_consumption_readback):
        return dict(transaction_output_fields)
    action = _mapping(transaction_output_fields.get("next_action"))
    if _optional_text(action.get("action_family")) != (
        "paper.stage_closure.owner_consumption"
    ):
        return dict(transaction_output_fields)
    suppressed = dict(transaction_output_fields)
    suppressed.pop("next_action", None)
    suppressed.pop("canonical_next_action_source", None)
    nested = _mapping(suppressed.get("paper_mission_transaction_readback"))
    if nested:
        nested = dict(nested)
        nested.pop("next_action", None)
        suppressed["paper_mission_transaction_readback"] = nested
    return suppressed


def _stage_closure_suppresses_domain_transition_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    next_action: Mapping[str, Any] | None,
    domain_transition_next_action: Mapping[str, Any] | None,
    receipt_owner_consumption_readback: Mapping[str, Any] | None = None,
) -> bool:
    if _stage_closure_next_action_should_own_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=_mapping(next_action),
        domain_transition_next_action=domain_transition_next_action,
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
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
    return decision_stage is None or action_stage is None or decision_stage == action_stage
