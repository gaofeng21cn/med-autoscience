from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

from med_autoscience.paper_mission_authority import consume_paper_mission_candidate
from med_autoscience.paper_mission_consumption_readback import (
    latest_paper_mission_consumption_transaction_readback,
)
from med_autoscience.paper_mission_opl_readback import (
    attach_opl_runtime_carrier_readback,
    paper_mission_next_action_envelope as _paper_mission_next_action_envelope,
)
from med_autoscience.paper_mission_consumption_ledger import (
    write_paper_mission_consumption_ledger_outputs,
)
from med_autoscience.paper_mission_terminal_owner_gate import (
    terminal_owner_gate_authority_readback as _terminal_owner_gate_authority_readback,
    terminal_owner_gate_from_carrier_readback as _terminal_owner_gate_from_carrier_readback,
)
from med_autoscience.cli_parts.paper_mission_output_roots import (
    _assert_safe_consumption_ledger_output_root,
    _is_yang_ops_consumption_ledger_root,
)
from med_autoscience.cli_parts.paper_mission_command_parts.receipt_owner_consumption import (
    build_receipt_owner_consumption_readback as _build_receipt_owner_consumption_readback,
    latest_receipt_owner_consumption_readback as _latest_receipt_owner_consumption_readback,
    receipt_owner_consumption_apply_mode as _receipt_owner_consumption_apply_mode,
)
from med_autoscience.cli_parts.paper_mission_command_parts.candidate_package_readback import (
    build_materialized_candidate_package_readback as _build_materialized_candidate_package_readback,
    consume_candidate_missing_readback as _consume_candidate_missing_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts.command_metadata import (
    FORBIDDEN_AUTHORITY_WRITES,
    PAPER_MISSION_CONTRACT_REF,
    PAPER_MISSION_CONTRACT_VERSION,
    PAPER_MISSION_START_OR_RESUME_TASK_KIND,
    action_intent as _action_intent,
    mission_id as _mission_id,
    mutation_policy as _mutation_policy,
    no_write_output_manifest as _no_write_output_manifest,
    objective_for_command as _objective_for_command,
    validate_with_contract_if_available as _validate_with_contract_if_available,
)
from med_autoscience.cli_parts.paper_mission_command_parts.domain_handler_dispatch import (
    paper_mission_domain_handler_dispatch_receipt as _paper_mission_domain_handler_dispatch_receipt,
)
from med_autoscience.cli_parts.paper_mission_command_parts.drive_readback import (
    build_paper_mission_drive_readback as _build_paper_mission_drive_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts.materialized_mission_readback import (
    build_materialized_mission_readback_if_available as _build_materialized_mission_readback_if_available,
    _domain_transition_direct_next_action_runtime_readback as _build_domain_transition_direct_next_action_runtime_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts.materialized_readback_context import (
    dispatch_execution_policy as _dispatch_execution_policy,
    paper_facing_action_fields as _paper_facing_action_fields,
    recommended_domain_command as _recommended_domain_command,
)
from med_autoscience.cli_parts.paper_mission_command_parts.parser_registration import (
    register_paper_mission_parsers,
)
from med_autoscience.cli_parts.paper_mission_command_parts.projection_fields import (
    resolve_consume_candidate_ref as _resolve_consume_candidate_ref,
)
from med_autoscience.cli_parts.paper_mission_command_parts.one_shot_migration import (
    build_one_shot_migration_cli_readback as _build_one_shot_migration_cli_readback_impl,
)
from med_autoscience.cli_parts.paper_mission_command_parts.opl_runtime_submission import (
    semantic_progress_guard as _paper_mission_semantic_progress_guard,
)
from med_autoscience.cli_parts.paper_mission_command_parts.stage_closure_next_action import (
    merge_stage_closure_typed_blocker_gate_fields as _merge_stage_closure_typed_blocker_gate_fields,
    next_action_for_stage_closure_decision as _next_action_for_stage_closure_decision,
)
from med_autoscience.cli_parts.paper_mission_command_parts.submission_gate_readback import (
    apply_submission_authority_owner_gate_readback as _apply_submission_authority_owner_gate_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _load_optional_json_object,
    _mapping,
    _optional_text,
)
from med_autoscience.cli_parts.paper_mission_command_parts.stage_closure_terminalizer import (
    latest_current_stage_closure_for_consumption as _latest_current_stage_closure_for_consumption,
    stage_closure_decision_requires_reterminalize as _stage_closure_decision_requires_reterminalize,
    terminalize_stage_closure_from_readback as _terminalize_stage_closure_from_readback,
)
from med_autoscience.cli_parts.paper_mission_commands_parts import (
    stage_closure_terminalizer_readback as _stage_closure_terminalizer_readback,
)
from med_autoscience.cli_parts.paper_mission_command_parts.typed_blocker_resolution import (
    build_typed_blocker_resolution_readback as _build_typed_blocker_resolution_readback,
    latest_typed_blocker_resolution_readback,
    typed_blocker_resolution_apply_mode as _typed_blocker_resolution_apply_mode,
)
from med_autoscience.cli_parts.paper_mission_command_parts.transaction_readback import (
    _candidate_manifest_transaction,
    _candidate_mission_id_for_readback,
    _consume_candidate_status_for_transaction_readback,
    _durable_mission_stop_guard,
    _paper_mission_run_candidate,
    _paper_mission_transaction_readback,
    _transaction_readback_output_fields,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_missing,
    stage_closure_decision_projection,
)
from med_autoscience.controllers.paper_mission_currentness import (
    receipt_owner_consumption_superseded_by_stage_closure as _receipt_superseded_by_stage_closure,
    receipt_owner_consumption_superseded_by_consumption as _receipt_superseded_by_consumption,
)
from med_autoscience.controllers import study_domain_transition_table
from med_autoscience.controllers import study_progress as _study_progress
from med_autoscience.controllers.study_progress_parts.canonical_next_action_selection import (
    domain_transition_canonical_next_action as _domain_transition_canonical_next_action,
)
from med_autoscience.mcp_server_parts.projection_adapters import (
    serialize_study_runtime_result as _serialize_study_runtime_result,
)
from med_autoscience.cli_parts.study_read_commands import (
    _progress_first_status_payload as _study_progress_status_payload,
)

CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "Yang study truth surfaces",
    "Yang runtime authority surfaces",
    "Yang output outside ops/medautoscience/paper_mission_consumption_ledger",
)
FORBIDDEN_AUTHORITY_CLAIMS = (
    "publication_ready",
    "submission_ready",
    "current_package",
    "owner_receipt_written",
    "typed_blocker_written",
    "human_gate_written",
    "controller_decision_written",
    "publication_eval_written",
    "quality_verdict",
    "artifact_authority",
    "runtime_queue_written",
    "provider_attempt_written",
    "yang_workspace_written",
)


_stage_closure_receipt_passthrough = _stage_closure_terminalizer_readback._stage_closure_receipt_passthrough
_terminal_source_readback_newer = _stage_closure_terminalizer_readback._terminal_source_readback_newer
_stage_closure_matches_current_transaction_with_terminal_closeout = (
    _stage_closure_terminalizer_readback._stage_closure_matches_current_transaction_with_terminal_closeout
)
_terminal_closeout_uses_stage_attempt_packet = _stage_closure_terminalizer_readback._terminal_closeout_uses_stage_attempt_packet
_terminal_closeout_newer = _stage_closure_terminalizer_readback._terminal_closeout_newer
_terminal_closeout_mtime = _stage_closure_terminalizer_readback._terminal_closeout_mtime
_domain_transition_direct_terminal_source_readback = _stage_closure_terminalizer_readback._domain_transition_direct_terminal_source_readback
_materialized_run_terminal_source_readback = _stage_closure_terminalizer_readback._materialized_run_terminal_source_readback
_build_terminalizer_source_readback_from_stage_packet = (
    _stage_closure_terminalizer_readback._build_terminalizer_source_readback_from_stage_packet
)
_preferred_terminal_stage_attempt_ids = _stage_closure_terminalizer_readback._preferred_terminal_stage_attempt_ids
_terminal_closeout_is_live_runtime_observed = _stage_closure_terminalizer_readback._terminal_closeout_is_live_runtime_observed
_expected_stage_attempt_identity = _stage_closure_terminalizer_readback._expected_stage_attempt_identity
_load_stage_packet_route_back_evidence = _stage_closure_terminalizer_readback._load_stage_packet_route_back_evidence
_stage_packet_route_stage_id = _stage_closure_terminalizer_readback._stage_packet_route_stage_id
_paper_mission_transaction_stage_id = _stage_closure_terminalizer_readback._paper_mission_transaction_stage_id
_stage_packet_transaction_priority = _stage_closure_terminalizer_readback._stage_packet_transaction_priority
_stage_packet_route_back_semantic_priority = _stage_closure_terminalizer_readback._stage_packet_route_back_semantic_priority
_first_non_empty_text = _stage_closure_terminalizer_readback._first_non_empty_text
_stage_packet_opl_runtime_carrier_readback = _stage_closure_terminalizer_readback._stage_packet_opl_runtime_carrier_readback
_load_json_object = _stage_closure_terminalizer_readback._load_json_object
_typed_blocker_resolution_should_own_next_action = _stage_closure_terminalizer_readback._typed_blocker_resolution_should_own_next_action
_stage_closure_next_action_should_own_next_action = _stage_closure_terminalizer_readback._stage_closure_next_action_should_own_next_action
_receipt_owner_consumed_route_checkpoint = _stage_closure_terminalizer_readback._receipt_owner_consumed_route_checkpoint
_align_current_carrier_owner_consumption = _stage_closure_terminalizer_readback._align_current_carrier_owner_consumption
_preserve_direct_successor_runtime_readback = _stage_closure_terminalizer_readback._preserve_direct_successor_runtime_readback
_route_checkpoint_matches_domain_transition = _stage_closure_terminalizer_readback._route_checkpoint_matches_domain_transition
_owner_consumed_route_checkpoint_yields_to_domain_transition = _stage_closure_terminalizer_readback._owner_consumed_route_checkpoint_yields_to_domain_transition
_route_checkpoint_identity_matches_domain_transition = _stage_closure_terminalizer_readback._route_checkpoint_identity_matches_domain_transition
_domain_transition_next_action_requests_stage_attempt = _stage_closure_terminalizer_readback._domain_transition_next_action_requests_stage_attempt

def _sync_stage_closure_terminalizer_readback_deps() -> None:
    _stage_closure_terminalizer_readback._build_materialized_mission_readback_if_available = (
        _build_materialized_mission_readback_if_available
    )
    _stage_closure_terminalizer_readback._domain_transition_direct_terminal_source_readback = (
        _domain_transition_direct_terminal_source_readback
    )
    _stage_closure_terminalizer_readback.latest_paper_mission_consumption_transaction_readback = (
        latest_paper_mission_consumption_transaction_readback
    )
    _stage_closure_terminalizer_readback._next_action_for_stage_closure_decision = (
        _next_action_for_stage_closure_decision
    )
    _stage_closure_terminalizer_readback._terminalize_stage_closure_from_readback = (
        _terminalize_stage_closure_from_readback
    )


def _build_stage_closure_terminalizer_readback(**kwargs: Any) -> dict[str, Any]:
    _sync_stage_closure_terminalizer_readback_deps()
    return _stage_closure_terminalizer_readback._build_stage_closure_terminalizer_readback(
        **kwargs
    )


def _build_terminalizer_source_readback(**kwargs: Any) -> dict[str, Any]:
    _sync_stage_closure_terminalizer_readback_deps()
    return _stage_closure_terminalizer_readback._build_terminalizer_source_readback(**kwargs)


def _latest_stage_attempt_route_back_source_readback(
    **kwargs: Any,
) -> dict[str, Any] | None:
    _sync_stage_closure_terminalizer_readback_deps()
    return _stage_closure_terminalizer_readback._latest_stage_attempt_route_back_source_readback(
        **kwargs
    )


def _override_next_action_from_direct_terminal_closeout(**kwargs: Any) -> tuple[Any, Any, Any]:
    _sync_stage_closure_terminalizer_readback_deps()
    return _stage_closure_terminalizer_readback._override_next_action_from_direct_terminal_closeout(
        **kwargs
    )

def handle_paper_mission_command(
    args: argparse.Namespace,
    *,
    load_profile: Callable[[str | Path], Any],
) -> int | None:
    if args.command != "paper-mission":
        return None
    profile_ref = Path(args.profile)
    profile = load_profile(profile_ref)
    result = build_paper_mission_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=args.study_id,
        paper_mission_command=args.paper_mission_command,
        objective=getattr(args, "objective", None),
        mission_id=getattr(args, "mission_id", None),
        candidate=getattr(args, "candidate", None),
        run_id=getattr(args, "run_id", None),
        submit_opl_runtime=getattr(args, "submit_opl_runtime", None),
        opl_bin=getattr(args, "opl_bin", None),
        one_shot_migration=bool(getattr(args, "one_shot_migration", False)),
        study_progress_payload=getattr(args, "study_progress_payload", None),
        runtime_readback_payload=getattr(
            args,
            "runtime_readback_payload",
            None,
        ),
        output_root=getattr(args, "output_root", None),
        paper_facing_delta_ref=getattr(args, "paper_facing_delta_ref", None),
        paper_mission_readback_file=getattr(
            args,
            "paper_mission_readback_file",
            None,
        ),
        stage_packet=getattr(args, "stage_packet", None),
        receipt_apply_typed_blocker=bool(
            getattr(args, "apply_typed_blocker", False)
        ),
        receipt_apply_route_checkpoint=bool(
            getattr(args, "apply_route_checkpoint", False)
        ),
        typed_resolution_apply_owner_decision=bool(
            getattr(args, "apply_owner_decision", False)
        ),
        typed_resolution_apply_human_gate=bool(
            getattr(args, "apply_human_gate", False)
        ),
        typed_resolution_apply_route_redesign=bool(
            getattr(args, "apply_route_redesign", False)
        ),
        dry_run=bool(getattr(args, "dry_run", False)),
        source="cli",
        enable_opl_live_probe=bool(
            getattr(args, "request_opl_runtime_readback", False)
        ),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_paper_mission_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    paper_mission_command: str,
    objective: str | None = None,
    mission_id: str | None = None,
    candidate: str | Path | None = None,
    run_id: str | None = None,
    submit_opl_runtime: bool | None = None,
    opl_bin: str | Path | None = None,
    one_shot_migration: bool = False,
    study_progress_payload: str | Path | None = None,
    runtime_readback_payload: str | Path | None = None,
    output_root: str | Path | None = None,
    paper_facing_delta_ref: str | Path | None = None,
    paper_mission_readback_file: str | Path | None = None,
    stage_packet: str | Path | None = None,
    receipt_apply_typed_blocker: bool = False,
    receipt_apply_route_checkpoint: bool = False,
    typed_resolution_apply_owner_decision: bool = False,
    typed_resolution_apply_human_gate: bool = False,
    typed_resolution_apply_route_redesign: bool = False,
    dry_run: bool = False,
    source: str = "unknown",
    enable_opl_live_probe: bool = False,
) -> dict[str, Any]:
    if one_shot_migration:
        return _build_one_shot_migration_cli_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            study_progress_payload=study_progress_payload,
            runtime_readback_payload=runtime_readback_payload,
            output_root=output_root,
            source=source,
        )
    if paper_mission_command == "package-candidate":
        return _build_materialized_candidate_package_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            output_root=output_root,
            paper_facing_delta_ref=paper_facing_delta_ref,
            inspect_readback_builder=build_paper_mission_readback,
            enable_opl_live_probe=enable_opl_live_probe,
            opl_bin=opl_bin,
            source=source,
        )
    if paper_mission_command == "drive":
        return _build_paper_mission_drive_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            output_root=output_root,
            run_id=run_id,
            submit_opl_runtime=submit_opl_runtime,
            opl_bin=opl_bin,
            source=source,
            consume_candidate_readback_builder=build_paper_mission_readback,
            consumption_ledger_forbidden_authority_writes=CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES,
            forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
        )
    if paper_mission_command == "terminalize-stage":
        return _build_stage_closure_terminalizer_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            output_root=output_root,
            stage_packet=stage_packet,
            dry_run=dry_run,
            source=source,
        )
    if paper_mission_command == "receipt-owner-consumption":
        return _build_receipt_owner_consumption_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_readback_file=paper_mission_readback_file,
            output_root=output_root,
            apply_mode=_receipt_owner_consumption_apply_mode(
                apply_typed_blocker=receipt_apply_typed_blocker,
                apply_route_checkpoint=receipt_apply_route_checkpoint,
            ),
            source=source,
        )
    if paper_mission_command == "typed-blocker-resolution":
        return _build_typed_blocker_resolution_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_readback_file=paper_mission_readback_file,
            output_root=output_root,
            apply_mode=_typed_blocker_resolution_apply_mode(
                apply_owner_decision=typed_resolution_apply_owner_decision,
                apply_human_gate=typed_resolution_apply_human_gate,
                apply_route_redesign=typed_resolution_apply_route_redesign,
            ),
            source=source,
        )
    if paper_mission_command in {"inspect", "start", "resume"}:
        materialized = _build_materialized_mission_readback_if_available(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command=paper_mission_command,
            dry_run=dry_run,
            source=source,
            enable_opl_live_probe=enable_opl_live_probe,
            opl_bin=opl_bin,
        )
        if materialized is not None:
            return materialized
        consumption_readback = latest_paper_mission_consumption_transaction_readback(
            workspace_root=Path(profile.workspace_root),
            study_id=study_id,
        )
        if consumption_readback is not None:
            return _consumption_ledger_inspect_readback(
                profile=profile,
                profile_ref=profile_ref,
                study_id=study_id,
                paper_mission_command=paper_mission_command,
                dry_run=dry_run,
                consumption_readback=consumption_readback,
                study_root=Path(profile.studies_root) / study_id,
                enable_opl_live_probe=enable_opl_live_probe,
                opl_bin=opl_bin,
            )
    selected_objective = _objective_for_command(
        paper_mission_command=paper_mission_command,
        objective=objective,
    )
    selected_mission_id = _mission_id(
        mission_id=mission_id,
        study_id=study_id,
        objective=selected_objective,
        paper_mission_command=paper_mission_command,
    )
    candidate_ref = _resolve_consume_candidate_ref(
        profile=profile,
        study_id=study_id,
        candidate=candidate,
    ) if paper_mission_command == "consume-candidate" else (
        str(candidate) if candidate is not None else None
    )
    authority_consume_readback = (
        consume_paper_mission_candidate(candidate_ref)
        if paper_mission_command == "consume-candidate" and candidate_ref is not None
        else None
    )
    if paper_mission_command == "consume-candidate" and authority_consume_readback is None:
        return _consume_candidate_missing_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command=paper_mission_command,
            source=source,
            dry_run=dry_run,
        )
    previous_consumption_readback = (
        latest_paper_mission_consumption_transaction_readback(
            workspace_root=Path(profile.workspace_root),
            study_id=study_id,
        )
        if paper_mission_command == "consume-candidate"
        else None
    )
    transaction_readback = _paper_mission_transaction_readback(
        mission_id=selected_mission_id,
        study_id=study_id,
        objective=selected_objective,
        paper_mission_command=paper_mission_command,
        study_root=Path(profile.studies_root) / study_id,
        mission=None,
        candidate=candidate_ref,
        authority_consume_readback=authority_consume_readback,
        enable_opl_live_probe=enable_opl_live_probe,
    )
    candidate_mission_id = _candidate_mission_id_for_readback(
        selected_mission_id=selected_mission_id,
        transaction_readback=transaction_readback,
        authority_consume_readback=authority_consume_readback,
    )
    if (
        transaction_readback["source"] == "placeholder_no_write"
        and candidate_mission_id != selected_mission_id
    ):
        transaction_readback = _paper_mission_transaction_readback(
            mission_id=candidate_mission_id,
            study_id=study_id,
            objective=selected_objective,
            paper_mission_command=paper_mission_command,
            study_root=Path(profile.studies_root) / study_id,
            mission=None,
            candidate=candidate_ref,
            authority_consume_readback=authority_consume_readback,
            enable_opl_live_probe=enable_opl_live_probe,
        )
    if authority_consume_readback is not None:
        transaction_readback["authority_consume_readback"] = authority_consume_readback
    mission_candidate = _paper_mission_run_candidate(
        mission_id=candidate_mission_id,
        study_id=study_id,
        objective=selected_objective,
        paper_mission_command=paper_mission_command,
        profile_ref=profile_ref,
        study_root=Path(profile.studies_root) / study_id,
        candidate_ref=candidate_ref,
        authority_consume_readback=authority_consume_readback,
        paper_mission_transaction=transaction_readback["paper_mission_transaction"],
    )
    consume_output_manifest = (
        _write_paper_mission_consumption_ledger_outputs(
            output_root=Path(output_root),
            study_id=study_id,
            candidate_ref=str(candidate_ref),
            authority_consume_readback=authority_consume_readback,
            transaction_readback=transaction_readback,
            mission_candidate=mission_candidate,
            source=source,
        )
        if (
            paper_mission_command == "consume-candidate"
            and output_root is not None
            and candidate_ref is not None
            and authority_consume_readback is not None
        )
        else None
    )
    candidate_source_transaction = (
        _candidate_manifest_transaction(candidate_ref)
        if paper_mission_command == "consume-candidate"
        else {}
    )
    consumption_ledger_readback = (
        _load_optional_json_object(
            _mapping(consume_output_manifest).get("consume_readback_ref")
        )
        if consume_output_manifest is not None
        else None
    )
    stage_closure_decision = stage_closure_decision_projection(
        readback={
            **transaction_readback,
            "consume_candidate_status": _consume_candidate_status_for_transaction_readback(
                transaction_readback=transaction_readback,
                authority_consume_readback=authority_consume_readback,
            ),
        },
        handoff=_mapping(transaction_readback.get("opl_route_handoff")),
        consumption_ledger_readback=consumption_ledger_readback,
    )
    typed_blocker_resolution_readback = latest_typed_blocker_resolution_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=study_id,
    )
    receipt_owner_consumption = None
    study_root = Path(profile.studies_root) / study_id
    domain_transition = study_domain_transition_table.project_domain_transition(
        study_id=study_id,
        study_root=study_root,
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
    current_handoff_next_action = _consumption_ledger_current_route_next_action(
        transaction_readback=transaction_readback,
        consumption_readback=consumption_ledger_readback or {},
    )
    if _receipt_owner_consumed_route_checkpoint(receipt_owner_consumption):
        current_handoff_next_action = None
    if (
        domain_transition_next_action
        and current_handoff_next_action is None
        and not _typed_blocker_resolution_should_own_next_action(
            stage_closure_decision=stage_closure_decision,
            typed_blocker_resolution_readback=typed_blocker_resolution_readback,
        )
        and not _stage_closure_next_action_should_own_next_action(
            stage_closure_decision=stage_closure_decision,
            next_action=next_action_override,
            domain_transition_next_action=domain_transition_next_action,
        )
    ):
        next_action_override = domain_transition_next_action
        canonical_next_action_source = "domain_transition.next_action"
        typed_blocker_resolution_readback = None
    elif next_action_override is not None and canonical_next_action_source is None:
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
            _build_domain_transition_direct_next_action_runtime_readback(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                inspect_readback={
                    **mission_candidate,
                    **transaction_output_fields,
                    "receipt_owner_consumption_readback": receipt_owner_consumption,
                },
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
            direct_terminal_owner_gate = _terminal_owner_gate_from_carrier_readback(
                direct_next_action_runtime["opl_runtime_carrier_readback"]
            )
            if direct_terminal_owner_gate:
                transaction_output_fields["terminal_owner_gate"] = (
                    direct_terminal_owner_gate
                )
                transaction_output_fields["terminal_owner_gate_authority_readback"] = (
                    _terminal_owner_gate_authority_readback(direct_terminal_owner_gate)
                )
            (
                stage_closure_decision,
                next_action_override,
                canonical_next_action_source,
            ) = _override_next_action_from_direct_terminal_closeout(
                direct_next_action_runtime=direct_next_action_runtime,
                stage_closure_decision=stage_closure_decision,
                transaction_readback=transaction_readback,
                typed_blocker_resolution_readback=typed_blocker_resolution_readback,
                next_action_override=next_action_override,
                canonical_next_action_source=canonical_next_action_source,
                receipt_owner_consumption_readback=receipt_owner_consumption,
            )
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
    transaction_output_fields = _align_current_carrier_owner_consumption(
        transaction_output_fields=transaction_output_fields,
        receipt_owner_consumption_readback=receipt_owner_consumption,
    )
    transaction_output_fields = _merge_stage_closure_typed_blocker_gate_fields(
        transaction_output_fields=transaction_output_fields,
        stage_closure_decision=stage_closure_decision,
        next_action=next_action_override,
    )
    (
        transaction_output_fields,
        typed_blocker_resolution_readback,
        submission_gate_readback,
    ) = _apply_submission_authority_owner_gate_readback(
        study_root=Path(profile.studies_root) / study_id,
        study_id=study_id,
        transaction_output_fields=transaction_output_fields,
        typed_blocker_resolution_readback=typed_blocker_resolution_readback,
    )
    paper_facing_action_fields = _paper_facing_action_fields(
        readback={
            "study_id": study_id,
            **transaction_output_fields,
            "typed_blocker_resolution_readback": typed_blocker_resolution_readback,
            "submission_authority_owner_gate_readback": submission_gate_readback,
        }
    )
    return {
        "surface_kind": "paper_mission_no_write_readback",
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
        "study_id": study_id,
        "study_root": str(Path(profile.studies_root) / study_id),
        "study_root_exists": (Path(profile.studies_root) / study_id).exists(),
        "mission_id": candidate_mission_id,
        "objective": selected_objective,
        **({"candidate_ref": candidate_ref} if candidate_ref is not None else {}),
        **transaction_output_fields,
        **(
            {"candidate_source_transaction": candidate_source_transaction}
            if candidate_source_transaction
            else {}
        ),
        "consume_candidate_status": _consume_candidate_status_for_transaction_readback(
            transaction_readback=transaction_readback,
            authority_consume_readback=authority_consume_readback,
        ),
        "stage_closure_decision": stage_closure_decision,
        "stage_closure_decision_ref": stage_closure_decision.get("decision_ref"),
        "stage_closure_outcome": _mapping(
            stage_closure_decision.get("outcome")
        ).get("kind"),
        "domain_transition": domain_transition,
        "durable_mission_stop_guard": _durable_mission_stop_guard(
            consume_candidate_status=_consume_candidate_status_for_transaction_readback(
                transaction_readback=transaction_readback,
                authority_consume_readback=authority_consume_readback,
            ),
            stage_closure_decision=stage_closure_decision,
        ),
        "mutation_policy": _mutation_policy(paper_mission_command=paper_mission_command),
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "paper_mission_run_candidate": mission_candidate,
        **(
            {"authority_consume_readback": authority_consume_readback}
            if authority_consume_readback is not None
            else {}
        ),
        **(
            {"consume_output_manifest": consume_output_manifest}
            if consume_output_manifest is not None
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
        **_paper_mission_consume_non_advancing_fields(
            paper_mission_command=paper_mission_command,
            transaction_readback=transaction_readback,
            consume_output_manifest=consume_output_manifest,
            previous_consumption_readback=previous_consumption_readback,
        ),
        "contract_validation": _validate_with_contract_if_available(mission_candidate),
        "dispatch_plan": {
            "default_action_intent": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_task_kind": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_dispatch_mode": (
                "governed_consume_record"
                if consume_output_manifest is not None
                else "dry_run_no_write"
            ),
            "old_owner_callable_dispatch_role": "diagnostic_or_migration_only",
        },
    }


def _consumption_ledger_inspect_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    paper_mission_command: str,
    dry_run: bool,
    consumption_readback: Mapping[str, Any],
    study_root: Path,
    enable_opl_live_probe: bool,
    opl_bin: str | Path | None,
) -> dict[str, Any]:
    transaction_readback = _paper_mission_transaction_readback(
        mission_id=str(consumption_readback.get("mission_id") or ""),
        study_id=study_id,
        objective=str(
            consumption_readback.get("selected_outcome")
            or consumption_readback.get("consume_candidate_status")
            or "paper mission consumption ledger readback"
        ),
        paper_mission_command=paper_mission_command,
        study_root=study_root,
        mission=None,
        transaction_override=_mapping(
            consumption_readback.get("paper_mission_transaction")
        ),
        transaction_source_override="paper_mission_consumption_ledger",
        authority_consume_readback=dict(consumption_readback),
        enable_opl_live_probe=enable_opl_live_probe,
        opl_bin=opl_bin,
    )
    base = attach_opl_runtime_carrier_readback(
        readback={
            **consumption_readback,
            "paper_mission_command": paper_mission_command,
            "action_intent": _action_intent(paper_mission_command),
            "dry_run": bool(dry_run),
            "profile": {
                "profile_name": str(getattr(profile, "name", "")),
                "profile_ref": str(profile_ref),
            },
            "study_root": str(study_root),
            "study_root_exists": study_root.exists(),
            "paper_mission_current_transaction_source": (
                "paper_mission_consumption_ledger"
            ),
            "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
            "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
            "mutation_policy": _mutation_policy(paper_mission_command=paper_mission_command),
        },
        study_root=study_root,
        enable_opl_live_probe=enable_opl_live_probe,
        opl_bin=opl_bin,
    )
    progress_overlay = _study_progress_paper_mission_overlay(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
    )
    receipt_owner_consumption = _latest_receipt_owner_consumption_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=study_id,
    )
    transaction_ref = _optional_text(
        _mapping(transaction_readback.get("paper_mission_transaction")).get(
            "transaction_id"
        )
    )
    stage_closure_ledger_readback = _latest_current_stage_closure_for_consumption(
        workspace_root=Path(profile.workspace_root),
        study_id=study_id,
        transaction_ref=transaction_ref,
        consume_readback=consumption_readback,
    )
    if receipt_owner_consumption is not None and _receipt_superseded_by_consumption(
        receipt_owner_consumption_readback=receipt_owner_consumption,
        consumption_ledger_readback=consumption_readback,
    ):
        receipt_owner_consumption = None
    if receipt_owner_consumption is not None and _receipt_superseded_by_stage_closure(
        receipt_owner_consumption_readback=receipt_owner_consumption,
        stage_closure_ledger_readback=stage_closure_ledger_readback,
    ):
        receipt_owner_consumption = None
    if receipt_owner_consumption is None:
        route_back_projection = _consumption_ledger_route_back_projection(
            transaction_readback=transaction_readback,
            consumption_readback=consumption_readback,
            base_readback=base,
            stage_closure_ledger_readback=stage_closure_ledger_readback,
        )
        if route_back_projection is not None:
            return _merge_study_progress_overlay(
                route_back_projection, progress_overlay
            )
        transaction_output_fields = _transaction_readback_output_fields(
            transaction_readback
        )
        if stage_closure_ledger_readback is not None:
            transaction_output_fields = {
                **transaction_output_fields,
                "stage_closure_decision": stage_closure_ledger_readback,
                "stage_closure_decision_ref": stage_closure_ledger_readback.get(
                    "decision_ref"
                ),
                "stage_closure_outcome": _mapping(
                    stage_closure_ledger_readback.get("outcome")
                ).get("kind"),
                "paper_mission_stage_closure_ledger_readback": (
                    stage_closure_ledger_readback
                ),
                "durable_mission_stop_guard": _durable_mission_stop_guard(
                    consume_candidate_status=str(
                        consumption_readback.get("consume_candidate_status") or ""
                    ),
                    stage_closure_decision=stage_closure_ledger_readback,
                ),
            }
        return _merge_study_progress_overlay(
            {
                **base,
                **transaction_output_fields,
            },
            progress_overlay,
        )
    receipt_consume_candidate_status = _receipt_owner_consumption_status(
        receipt_owner_consumption
    )
    stage_closure_decision = stage_closure_decision_projection(
        readback={
            **transaction_readback,
            "stage_closure_decision": receipt_owner_consumption["stage_closure_decision"],
            "consume_candidate_status": receipt_consume_candidate_status,
        },
        handoff=_mapping(consumption_readback.get("opl_route_handoff")),
        consumption_ledger_readback=consumption_readback,
    )
    typed_blocker_resolution_readback = latest_typed_blocker_resolution_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=study_id,
    )
    domain_transition = study_domain_transition_table.project_domain_transition(
        study_id=study_id,
        study_root=study_root,
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
    current_handoff_next_action = _consumption_ledger_current_route_next_action(
        transaction_readback=transaction_readback,
        consumption_readback=consumption_readback,
    )
    if _receipt_owner_consumed_route_checkpoint(receipt_owner_consumption):
        current_handoff_next_action = None
    if (
        domain_transition_next_action
        and current_handoff_next_action is None
        and not _typed_blocker_resolution_should_own_next_action(
            stage_closure_decision=stage_closure_decision,
            typed_blocker_resolution_readback=typed_blocker_resolution_readback,
        )
        and not _stage_closure_next_action_should_own_next_action(
            stage_closure_decision=stage_closure_decision,
            next_action=next_action_override,
            domain_transition_next_action=domain_transition_next_action,
            receipt_owner_consumption_readback=receipt_owner_consumption,
        )
    ):
        next_action_override = domain_transition_next_action
        canonical_next_action_source = "domain_transition.next_action"
        typed_blocker_resolution_readback = None
    elif next_action_override is not None and canonical_next_action_source is None:
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
            _build_domain_transition_direct_next_action_runtime_readback(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                inspect_readback={
                    **base,
                    **transaction_output_fields,
                    "receipt_owner_consumption_readback": receipt_owner_consumption,
                },
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
            direct_terminal_owner_gate = _terminal_owner_gate_from_carrier_readback(
                direct_next_action_runtime["opl_runtime_carrier_readback"]
            )
            if direct_terminal_owner_gate:
                transaction_output_fields["terminal_owner_gate"] = (
                    direct_terminal_owner_gate
                )
                transaction_output_fields["terminal_owner_gate_authority_readback"] = (
                    _terminal_owner_gate_authority_readback(direct_terminal_owner_gate)
                )
            (
                stage_closure_decision,
                next_action_override,
                canonical_next_action_source,
            ) = _override_next_action_from_direct_terminal_closeout(
                direct_next_action_runtime=direct_next_action_runtime,
                stage_closure_decision=stage_closure_decision,
                transaction_readback=transaction_readback,
                typed_blocker_resolution_readback=typed_blocker_resolution_readback,
                next_action_override=next_action_override,
                canonical_next_action_source=canonical_next_action_source,
                receipt_owner_consumption_readback=receipt_owner_consumption,
            )
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
    transaction_output_fields = _align_current_carrier_owner_consumption(
        transaction_output_fields=transaction_output_fields,
        receipt_owner_consumption_readback=receipt_owner_consumption,
    )
    transaction_output_fields = _merge_stage_closure_typed_blocker_gate_fields(
        transaction_output_fields=transaction_output_fields,
        stage_closure_decision=stage_closure_decision,
        next_action=next_action_override,
    )
    (
        transaction_output_fields,
        typed_blocker_resolution_readback,
        submission_gate_readback,
    ) = _apply_submission_authority_owner_gate_readback(
        study_root=Path(profile.studies_root) / study_id,
        study_id=study_id,
        transaction_output_fields=transaction_output_fields,
        typed_blocker_resolution_readback=typed_blocker_resolution_readback,
    )
    return _merge_study_progress_overlay(
        {
        **base,
        **transaction_output_fields,
        "receipt_owner_consumption_readback": receipt_owner_consumption,
        "receipt_evidence": receipt_owner_consumption.get("receipt_evidence"),
        "mas_receipt_consumption": receipt_owner_consumption.get(
            "mas_receipt_consumption"
        ),
        "consume_candidate_status": receipt_consume_candidate_status,
        "mission_state": (
            "stable_blocker"
            if receipt_consume_candidate_status == "typed_blocker"
            else "route_back"
            if receipt_consume_candidate_status == "route_back"
            else "consumed"
        ),
        "stage_closure_decision": stage_closure_decision,
        "stage_closure_decision_ref": stage_closure_decision.get("decision_ref"),
        "stage_closure_outcome": _mapping(stage_closure_decision.get("outcome")).get(
            "kind"
        ),
        "domain_transition": domain_transition,
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
        "durable_mission_stop_guard": _durable_mission_stop_guard(
            consume_candidate_status=receipt_consume_candidate_status,
            stage_closure_decision=stage_closure_decision,
        ),
        },
        progress_overlay,
    )


def _study_progress_paper_mission_overlay(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
) -> dict[str, Any]:
    try:
        result = _study_progress.read_study_progress(
            profile=profile,
            profile_ref=Path(profile_ref),
            study_id=study_id,
            study_root=None,
            entry_mode=None,
            sync_runtime_summary=False,
            materialize_read_model_artifacts=False,
            enable_opl_live_provider_attempt_probe=False,
        )
        payload = _study_progress_status_payload(
            _serialize_study_runtime_result(result)
        )
    except Exception:
        return {}
    paper_mission_run = _mapping(payload.get("paper_mission_run"))
    if not paper_mission_run:
        paper_mission_run = _mapping(
            _mapping(payload.get("artifact_first_mission_summary")).get(
                "paper_mission_run"
            )
        )
    if not paper_mission_run:
        return {}
    return {
        "paper_mission_run": paper_mission_run,
        "current_objective": _mapping(payload.get("current_objective"))
        or _mapping(paper_mission_run.get("current_objective")),
        "next_owner_or_human_decision": _mapping(
            payload.get("next_owner_or_human_decision")
        )
        or _mapping(paper_mission_run.get("next_owner_or_human_decision")),
        "stage_closure_decision": _mapping(payload.get("stage_closure_decision")),
        "current_stage": _optional_text(payload.get("current_stage")),
        "current_work_unit": _optional_text(payload.get("current_work_unit")),
        "current_executable_owner_action": _mapping(
            payload.get("current_executable_owner_action")
        ),
    }


def _merge_study_progress_overlay(
    readback: Mapping[str, Any],
    overlay: Mapping[str, Any],
) -> dict[str, Any]:
    if not overlay:
        return dict(readback)
    merged = dict(readback)
    paper_mission_run = _mapping(overlay.get("paper_mission_run"))
    if paper_mission_run and not _mapping(merged.get("paper_mission_run")):
        merged["paper_mission_run"] = paper_mission_run
        if not _optional_text(merged.get("mission_state")):
            merged["mission_state"] = _optional_text(paper_mission_run.get("mission_state"))
    for key in ("current_objective", "next_owner_or_human_decision"):
        if _mapping(overlay.get(key)):
            merged[key] = overlay[key]
    for key in ("stage_closure_decision", "current_executable_owner_action"):
        if not _mapping(merged.get(key)) and _mapping(overlay.get(key)):
            merged[key] = overlay[key]
    for key in ("current_stage", "current_work_unit"):
        if not _optional_text(merged.get(key)) and _optional_text(overlay.get(key)):
            merged[key] = overlay[key]
    if (
        not _optional_text(merged.get("stage_closure_decision_ref"))
        and _mapping(merged.get("stage_closure_decision"))
    ):
        merged["stage_closure_decision_ref"] = _mapping(
            merged.get("stage_closure_decision")
        ).get("decision_ref")
    if (
        not _optional_text(merged.get("stage_closure_outcome"))
        and _mapping(merged.get("stage_closure_decision"))
    ):
        merged["stage_closure_outcome"] = _mapping(
            _mapping(merged.get("stage_closure_decision")).get("outcome")
        ).get("kind")
    return merged


def _consumption_ledger_route_back_projection(
    *,
    transaction_readback: Mapping[str, Any],
    consumption_readback: Mapping[str, Any],
    base_readback: Mapping[str, Any],
    stage_closure_ledger_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not _transaction_readback_has_route_back_owner_answer(transaction_readback):
        return None
    consume_candidate_status = (
        transaction_readback.get("consume_candidate_status_override")
        or consumption_readback.get("consume_candidate_status")
    )
    stage_closure_input = {
        **dict(transaction_readback),
        **{
            key: value
            for key, value in dict(base_readback).items()
            if key in {"current_package", "candidate_manifest", "output_manifest"}
        },
        "consume_candidate_status": consume_candidate_status,
        **(
            {"stage_closure_decision": stage_closure_ledger_readback}
            if stage_closure_ledger_readback
            else {}
        ),
    }
    stage_closure_decision = stage_closure_decision_projection(
        readback=stage_closure_input,
        handoff=_mapping(consumption_readback.get("opl_route_handoff")),
        consumption_ledger_readback=consumption_readback,
    )
    if stage_closure_decision_missing(
        stage_closure_decision
    ) or _stage_closure_decision_requires_reterminalize(stage_closure_decision):
        stage_closure_decision = _terminalize_stage_closure_from_readback(
            stage_closure_input
        )
    next_action_override = _next_action_for_stage_closure_decision(
        stage_closure_decision=stage_closure_decision,
        transaction_readback=transaction_readback,
    )
    transaction_output_fields = _transaction_readback_output_fields(transaction_readback)
    if next_action_override is not None:
        transaction_output_fields["next_action"] = next_action_override
        transaction_output_fields["canonical_next_action_source"] = (
            "stage_closure.next_action"
        )
        transaction_output_fields["paper_mission_transaction_readback"] = {
            **dict(transaction_readback),
            "next_action": next_action_override,
        }
    transaction_output_fields = _merge_stage_closure_typed_blocker_gate_fields(
        transaction_output_fields=transaction_output_fields,
        stage_closure_decision=stage_closure_decision,
        next_action=next_action_override,
    )
    return {
        **dict(base_readback),
        **transaction_output_fields,
        "stage_closure_decision": stage_closure_decision,
        "stage_closure_decision_ref": stage_closure_decision.get("decision_ref"),
        "stage_closure_outcome": _mapping(stage_closure_decision.get("outcome")).get(
            "kind"
        ),
        "durable_mission_stop_guard": _durable_mission_stop_guard(
            consume_candidate_status=str(consume_candidate_status or ""),
            stage_closure_decision=stage_closure_decision,
        ),
    }


def _transaction_readback_has_route_back_owner_answer(
    transaction_readback: Mapping[str, Any],
) -> bool:
    owner_answer = _mapping(
        transaction_readback.get("terminal_owner_gate_owner_answer_readback")
    )
    consume_result = _mapping(owner_answer.get("consume_result"))
    return (
        _optional_text(owner_answer.get("owner_answer_shape"))
        == "route_back_evidence_ref"
        or _optional_text(owner_answer.get("selected_outcome"))
        == "route_back_evidence_ref"
        or _optional_text(consume_result.get("outcome"))
        == "route_back_evidence_ref"
    )


def _receipt_owner_consumption_status(
    receipt_owner_consumption: Mapping[str, Any],
) -> str:
    consumption_status = _optional_text(
        _mapping(receipt_owner_consumption.get("mas_receipt_consumption")).get(
            "status"
        )
    )
    if consumption_status == "owner_consumed_typed_blocker":
        return "typed_blocker"
    if consumption_status == "owner_consumed_route_checkpoint":
        return "route_back"
    return "accepted"


def _consumption_ledger_current_route_next_action(
    *,
    transaction_readback: Mapping[str, Any],
    consumption_readback: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not _consumption_ledger_has_current_route_handoff(consumption_readback):
        return None
    envelope = _paper_mission_next_action_envelope(
        transaction=_mapping(transaction_readback.get("paper_mission_transaction")),
        stage_terminal_decision=_mapping(consumption_readback.get("stage_terminal_decision")),
        opl_route_command=_mapping(consumption_readback.get("opl_route_command")),
        opl_runtime_carrier=_mapping(consumption_readback.get("opl_runtime_carrier")),
        opl_route_handoff=_mapping(consumption_readback.get("opl_route_handoff")),
        diagnostic_refs=[
            ref
            for ref in (_optional_text(consumption_readback.get("source_ref")),)
            if ref is not None
        ],
    )
    action = _mapping(envelope)
    if (
        _optional_text(action.get("surface_kind")) != "mas_next_action_envelope"
        or _optional_text(action.get("owner")) is None
        or _optional_text(action.get("work_unit_id")) is None
    ):
        return None
    return dict(action)


def _consumption_ledger_has_current_route_handoff(
    consumption_readback: Mapping[str, Any],
) -> bool:
    handoff = _mapping(consumption_readback.get("opl_route_handoff"))
    stage_terminal_decision = _mapping(
        consumption_readback.get("stage_terminal_decision")
    ) or _mapping(handoff.get("stage_terminal_decision"))
    opl_route_command = _mapping(consumption_readback.get("opl_route_command")) or _mapping(
        handoff.get("opl_route_command")
    )
    if _optional_text(handoff.get("handoff_status")) == "ready_for_opl_route_command":
        return True
    if handoff.get("can_submit_to_opl_runtime") is not True:
        return False
    if _optional_text(opl_route_command.get("command_kind")) in {
        "resume_stage",
        "advance_stage",
        "submit_to_opl_runtime",
    } and _optional_text(opl_route_command.get("target")) is not None:
        return True
    return (
        _optional_text(stage_terminal_decision.get("recommended_next_action"))
        == "request_opl_stage_attempt"
        and _optional_text(stage_terminal_decision.get("next_work_unit")) is not None
    )


def _paper_mission_consume_non_advancing_fields(
    *,
    paper_mission_command: str,
    transaction_readback: Mapping[str, Any],
    consume_output_manifest: Mapping[str, Any] | None,
    previous_consumption_readback: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if paper_mission_command != "consume-candidate" or previous_consumption_readback is None:
        return {}
    handoff = _mapping(_mapping(consume_output_manifest).get("opl_route_handoff"))
    if not handoff:
        handoff = _mapping(transaction_readback.get("opl_route_handoff"))
    current_readback = _paper_mission_semantic_progress_readback(transaction_readback)
    previous_readback = _paper_mission_semantic_progress_readback(
        previous_consumption_readback
    )
    guard = _paper_mission_semantic_progress_guard(
        consume_readback=current_readback,
        handoff=handoff,
        previous_guard=_paper_mission_semantic_progress_guard(
            consume_readback=previous_readback,
            handoff=_mapping(previous_consumption_readback.get("opl_route_handoff")),
        ),
    )
    if guard.get("status") != "non_advancing_route_back":
        return {}
    return {
        "semantic_progress_guard": guard,
        "non_advancing_route_back": guard,
        "requires_mas_owned_executor_delta": True,
    }


def _paper_mission_semantic_progress_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    transaction = _mapping(readback.get("paper_mission_transaction"))
    return {
        **dict(readback),
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": _mapping(
            readback.get("stage_terminal_decision")
        )
        or _mapping(transaction.get("stage_terminal_decision")),
        "opl_route_command": _mapping(readback.get("opl_route_command"))
        or _mapping(transaction.get("opl_route_command")),
        "next_owner_or_human_decision": _mapping(
            readback.get("next_owner_or_human_decision")
        ),
        "authority_consume_readback": _mapping(
            readback.get("authority_consume_readback")
        ),
        "terminal_owner_gate": _mapping(readback.get("terminal_owner_gate")),
        "terminal_owner_gate_owner_answer_readback": _mapping(
            readback.get("terminal_owner_gate_owner_answer_readback")
        ),
    }





def paper_mission_domain_handler_dispatch_receipt(
    *,
    task: dict[str, Any],
    task_path: Path,
    load_profile: Callable[[str | Path], Any],
) -> dict[str, Any]:
    return _paper_mission_domain_handler_dispatch_receipt(
        task=task,
        task_path=task_path,
        load_profile=load_profile,
        build_readback=build_paper_mission_readback,
        start_or_resume_task_kind=PAPER_MISSION_START_OR_RESUME_TASK_KIND,
        forbidden_authority_writes=FORBIDDEN_AUTHORITY_WRITES,
        dispatch_execution_policy=_dispatch_execution_policy,
        recommended_domain_command=_recommended_domain_command,
    )


def _build_one_shot_migration_cli_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    study_progress_payload: str | Path | None,
    runtime_readback_payload: str | Path | None,
    output_root: str | Path | None,
    source: str,
) -> dict[str, Any]:
    return _build_one_shot_migration_cli_readback_impl(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_progress_payload=study_progress_payload,
        runtime_readback_payload=runtime_readback_payload,
        output_root=output_root,
        source=source,
        contract_ref=PAPER_MISSION_CONTRACT_REF,
        contract_version=PAPER_MISSION_CONTRACT_VERSION,
        no_write_output_manifest=_no_write_output_manifest,
        paper_mission_transaction_readback=_paper_mission_transaction_readback,
        transaction_readback_output_fields=_transaction_readback_output_fields,
        validate_with_contract=_validate_with_contract_if_available,
    )


def _write_paper_mission_consumption_ledger_outputs(
    *,
    output_root: Path,
    study_id: str,
    candidate_ref: str,
    authority_consume_readback: dict[str, Any],
    transaction_readback: dict[str, Any],
    mission_candidate: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    root = output_root.expanduser().resolve()
    _assert_safe_consumption_ledger_output_root(root)
    return write_paper_mission_consumption_ledger_outputs(
        output_root=root,
        study_id=study_id,
        candidate_ref=candidate_ref,
        authority_consume_readback=authority_consume_readback,
        transaction_readback=transaction_readback,
        mission_candidate=mission_candidate,
        source=source,
        writes_yang_ops_consumption_ledger=_is_yang_ops_consumption_ledger_root(root),
        forbidden_authority_writes=CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )


__all__ = [
    "PAPER_MISSION_START_OR_RESUME_TASK_KIND",
    "build_paper_mission_readback",
    "handle_paper_mission_command",
    "paper_mission_domain_handler_dispatch_receipt",
    "register_paper_mission_parsers",
]
