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
from med_autoscience.paper_mission_opl_carrier import (
    paper_mission_opl_runtime_carrier,
)
from med_autoscience.paper_mission_transaction import (
    PaperMissionTransactionContractError,
)
from med_autoscience.paper_mission_consumption_ledger import (
    write_paper_mission_consumption_ledger_outputs,
)
from med_autoscience.paper_mission_stage_closure_ledger import (
    write_paper_mission_stage_closure_decision,
)
from med_autoscience.paper_mission_terminal_owner_gate import (
    terminal_owner_gate_authority_readback as _terminal_owner_gate_authority_readback,
    terminal_owner_gate_from_carrier_readback as _terminal_owner_gate_from_carrier_readback,
)
from med_autoscience.paper_mission_owner_answer import (
    terminal_owner_gate_authority_consume_readback as _terminal_owner_gate_authority_consume_readback,
    terminal_owner_gate_owner_answer_readback as _terminal_owner_gate_owner_answer_readback,
)
from med_autoscience.cli_parts.paper_mission_output_roots import (
    _assert_safe_consumption_ledger_output_root,
    _assert_safe_stage_closure_output_root,
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
    _first_text,
    _load_optional_json_object,
    _mapping,
    _mapping_list,
    _optional_text,
)
from med_autoscience.cli_parts.paper_mission_command_parts.stage_closure_terminalizer import (
    FORBIDDEN_AUTHORITY_CLAIMS as STAGE_CLOSURE_FORBIDDEN_AUTHORITY_CLAIMS,
    STAGE_CLOSURE_FORBIDDEN_AUTHORITY_WRITES,
    latest_current_stage_closure_for_consumption as _latest_current_stage_closure_for_consumption,
    stage_closure_decision_requires_reterminalize as _stage_closure_decision_requires_reterminalize,
    stage_closure_source_readback_summary as _stage_closure_source_readback_summary,
    stage_closure_terminalizer_output_root as _stage_closure_terminalizer_output_root,
    terminalize_stage_closure_from_readback as _terminalize_stage_closure_from_readback,
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
from med_autoscience.controllers.paper_mission_receipt_owner_consumption import (
    align_carrier_readback_with_owner_consumption as _align_carrier_readback_with_owner_consumption,
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


def _build_stage_closure_terminalizer_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: str | Path | None,
    stage_packet: str | Path | None,
    dry_run: bool,
    source: str,
) -> dict[str, Any]:
    if stage_packet is not None:
        source_readback = _build_terminalizer_source_readback_from_stage_packet(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            stage_packet=stage_packet,
            source=f"{source}:terminalize-stage:stage-packet",
        )
    else:
        source_readback = _build_terminalizer_source_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            source=f"{source}:terminalize-stage:inspect",
        )
    existing_decision = _mapping(source_readback.get("stage_closure_decision"))
    if (
        existing_decision
        and not stage_closure_decision_missing(existing_decision)
        and not _stage_closure_decision_requires_reterminalize(
            existing_decision,
            current_package=_mapping(source_readback.get("current_package")),
        )
    ):
        decision = existing_decision
        terminalizer_status = "terminalizer_outcome_already_observed"
    else:
        decision = _terminalize_stage_closure_from_readback(source_readback)
        terminalizer_status = (
            "legacy_terminalizer_outcome_superseded"
            if existing_decision
            else "terminalizer_outcome_materialized"
        )
    output_manifest = None
    resolved_output_root = _stage_closure_terminalizer_output_root(
        profile=profile,
        output_root=output_root,
    )
    if not dry_run:
        root = resolved_output_root
        _assert_safe_stage_closure_output_root(root)
        output_manifest = write_paper_mission_stage_closure_decision(
            output_root=root,
            study_id=study_id,
            decision=decision,
            source_readback=source_readback,
            source=source,
            forbidden_authority_writes=STAGE_CLOSURE_FORBIDDEN_AUTHORITY_WRITES,
            forbidden_authority_claims=STAGE_CLOSURE_FORBIDDEN_AUTHORITY_CLAIMS,
        )
        decision = {
            **decision,
            "decision_ref": output_manifest["stage_closure_decision_ref"],
            "source_ref": output_manifest["stage_closure_decision_ref"],
        }
    return {
        "surface_kind": "paper_mission_stage_closure_terminalizer_readback",
        "schema_version": 1,
        "contract_ref": "contracts/mas-stage-closure-terminalizer.json",
        "paper_mission_command": "terminalize-stage",
        "action_intent": _action_intent("terminalize-stage"),
        "source": source,
        "dry_run": bool(dry_run),
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "study_id": study_id,
        "mission_id": source_readback.get("mission_id"),
        "materialized_mission_ref": source_readback.get("materialized_mission_ref"),
        "status": terminalizer_status,
        "stage_closure_decision": decision,
        "stage_closure_decision_ref": decision.get("decision_ref"),
        "stage_closure_outcome": _mapping(decision.get("outcome")).get("kind"),
        "source_readback_summary": _stage_closure_source_readback_summary(
            source_readback
        ),
        **_stage_closure_receipt_passthrough(source_readback),
        **({"output_manifest": output_manifest} if output_manifest is not None else {}),
        "authority_boundary": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_runtime_queue_or_provider_attempt": False,
        },
        "forbidden_authority_writes": list(STAGE_CLOSURE_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(STAGE_CLOSURE_FORBIDDEN_AUTHORITY_CLAIMS),
        "required_next_owner": _mapping(decision.get("outcome")).get("next_owner"),
        "required_next_action": _mapping(decision.get("outcome")).get("next_action"),
    }


def _stage_closure_receipt_passthrough(
    source_readback: Mapping[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in (
        "current_package",
        "opl_runtime_carrier_readback",
        "current_opl_runtime_carrier_readback",
    ):
        value = _mapping(source_readback.get(key))
        if value:
            result[key] = value
    return result


def _build_terminalizer_source_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    source: str,
    allow_stage_packet_autodiscovery: bool = True,
) -> dict[str, Any]:
    source_readback = _build_materialized_mission_readback_if_available(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        source=source,
        enable_opl_live_probe=True,
        opl_bin=None,
    )
    if source_readback is not None:
        if allow_stage_packet_autodiscovery:
            stage_attempt_source = _latest_stage_attempt_route_back_source_readback(
                profile=profile,
                profile_ref=profile_ref,
                study_id=study_id,
                source_readback=source_readback,
                source=source,
            )
            if (
                stage_attempt_source is not None
                and _terminal_source_readback_newer(
                    candidate=stage_attempt_source,
                    current=source_readback,
                    workspace_root=Path(profile.workspace_root),
                )
            ):
                return stage_attempt_source
        if _stage_closure_matches_current_transaction_with_terminal_closeout(
            source_readback,
            workspace_root=Path(profile.workspace_root),
        ):
            return source_readback
        direct_stage_attempt = _domain_transition_direct_terminal_source_readback(
            materialized_readback=source_readback,
            study_root=Path(profile.studies_root) / study_id,
            profile=profile,
            study_id=study_id,
            enable_opl_live_probe=True,
            opl_bin=None,
        )
        if direct_stage_attempt is not None:
            if allow_stage_packet_autodiscovery:
                stage_attempt_source = _latest_stage_attempt_route_back_source_readback(
                    profile=profile,
                    profile_ref=profile_ref,
                    study_id=study_id,
                    source_readback=direct_stage_attempt,
                    source=source,
                )
                if (
                    stage_attempt_source is not None
                    and _terminal_source_readback_newer(
                        candidate=stage_attempt_source,
                        current=direct_stage_attempt,
                        workspace_root=Path(profile.workspace_root),
                    )
                ):
                    return stage_attempt_source
            return direct_stage_attempt
    generic_source_readback = None
    if source_readback is None:
        generic_source_readback = build_paper_mission_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command="inspect",
            dry_run=False,
            source=source,
            enable_opl_live_probe=True,
        )
        direct_stage_attempt = _domain_transition_direct_terminal_source_readback(
            materialized_readback=generic_source_readback,
            study_root=Path(profile.studies_root) / study_id,
            profile=profile,
            study_id=study_id,
            enable_opl_live_probe=True,
            opl_bin=None,
        )
        if direct_stage_attempt is not None:
            if allow_stage_packet_autodiscovery:
                stage_attempt_source = _latest_stage_attempt_route_back_source_readback(
                    profile=profile,
                    profile_ref=profile_ref,
                    study_id=study_id,
                    source_readback=direct_stage_attempt,
                    source=source,
                )
                if (
                    stage_attempt_source is not None
                    and _terminal_source_readback_newer(
                        candidate=stage_attempt_source,
                        current=direct_stage_attempt,
                        workspace_root=Path(profile.workspace_root),
                    )
                ):
                    return stage_attempt_source
            return direct_stage_attempt
    if allow_stage_packet_autodiscovery:
        stage_attempt_source = _latest_stage_attempt_route_back_source_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            source_readback=source_readback or generic_source_readback or {},
            source=source,
        )
        if stage_attempt_source is not None:
            return stage_attempt_source
    consumption_readback = latest_paper_mission_consumption_transaction_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=study_id,
    )
    if consumption_readback is not None:
        return attach_opl_runtime_carrier_readback(
            readback={
                **consumption_readback,
                "paper_mission_command": "terminalize-stage",
                "source": "paper_mission_consumption_ledger",
            },
            study_root=Path(profile.studies_root) / study_id,
            enable_opl_live_probe=True,
            opl_bin=None,
        )
    if source_readback is not None:
        materialized_run_stage_attempt = (
            _materialized_run_terminal_source_readback(
                materialized_readback=source_readback,
                study_root=Path(profile.studies_root) / study_id,
            )
        )
        if materialized_run_stage_attempt is not None:
            return materialized_run_stage_attempt
        return source_readback
    if generic_source_readback is not None:
        return generic_source_readback
    return build_paper_mission_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        source=source,
        enable_opl_live_probe=True,
    )


def _terminal_source_readback_newer(
    *,
    candidate: Mapping[str, Any],
    current: Mapping[str, Any],
    workspace_root: Path,
) -> bool:
    candidate_closeout = _mapping(
        _mapping(candidate.get("opl_runtime_carrier_readback")).get("terminal_closeout")
    )
    current_closeout = _mapping(
        _mapping(current.get("opl_runtime_carrier_readback")).get("terminal_closeout")
    )
    return _terminal_closeout_newer(
        candidate=candidate_closeout,
        current=current_closeout,
        workspace_root=workspace_root,
    )


def _stage_closure_matches_current_transaction_with_terminal_closeout(
    readback: Mapping[str, Any],
    *,
    workspace_root: Path,
) -> bool:
    if _optional_text(readback.get("consume_candidate_status")) in {
        "not_consumed",
        "not_applicable",
    }:
        return False
    if _optional_text(readback.get("mission_state")) in {"planned", "draft"}:
        return False
    stage_closure = _mapping(readback.get("stage_closure_decision"))
    transaction = _mapping(readback.get("paper_mission_transaction"))
    transaction_ref = _optional_text(transaction.get("transaction_id"))
    closure_ref = _optional_text(
        _mapping(stage_closure.get("identity")).get("paper_mission_transaction_ref")
    ) or _optional_text(stage_closure.get("paper_mission_transaction_ref"))
    if transaction_ref is None or closure_ref != transaction_ref:
        return False
    opl_closeout = _mapping(stage_closure.get("opl_closeout"))
    stage_attempt_id = _optional_text(opl_closeout.get("stage_attempt_id"))
    live_terminal_closeout = _mapping(
        _mapping(readback.get("opl_runtime_carrier_readback")).get("terminal_closeout")
    )
    live_stage_attempt_id = _optional_text(live_terminal_closeout.get("stage_attempt_id"))
    if not _terminal_closeout_uses_stage_attempt_packet(live_terminal_closeout):
        return False
    direct_terminal_closeout = _mapping(
        _mapping(readback.get("current_opl_runtime_carrier_readback")).get(
            "terminal_closeout"
        )
    )
    if _terminal_closeout_newer(
        candidate=direct_terminal_closeout,
        current=live_terminal_closeout,
        workspace_root=workspace_root,
    ):
        return False
    return (
        stage_attempt_id is not None
        and stage_attempt_id == live_stage_attempt_id
        and _optional_text(opl_closeout.get("status"))
        == "opl_runtime_terminal_readback_observed"
    )


def _terminal_closeout_uses_stage_attempt_packet(closeout: Mapping[str, Any]) -> bool:
    refs = [_optional_text(closeout.get("closeout_ref"))]
    closeout_refs = closeout.get("closeout_refs")
    if isinstance(closeout_refs, (list, tuple)):
        refs.extend(_optional_text(item) for item in closeout_refs)
    return any(
        ref is not None
        and "paper_mission_stage_attempts" in ref
        and ref.endswith("stage_attempt_closeout_packet.json")
        for ref in refs
    )


def _terminal_closeout_newer(
    *,
    candidate: Mapping[str, Any],
    current: Mapping[str, Any],
    workspace_root: Path,
) -> bool:
    candidate_mtime = _terminal_closeout_mtime(candidate, workspace_root=workspace_root)
    current_mtime = _terminal_closeout_mtime(current, workspace_root=workspace_root)
    if candidate_mtime is None:
        return False
    if current_mtime is None:
        return True
    return candidate_mtime > current_mtime


def _terminal_closeout_mtime(
    closeout: Mapping[str, Any],
    *,
    workspace_root: Path,
) -> float | None:
    refs = [_optional_text(closeout.get("closeout_ref"))]
    closeout_refs = closeout.get("closeout_refs")
    if isinstance(closeout_refs, (list, tuple)):
        refs.extend(_optional_text(item) for item in closeout_refs)
    for ref in refs:
        if ref is None or ref.startswith(("opl://", "temporal://")):
            continue
        path = Path(ref).expanduser()
        if not path.is_absolute():
            path = workspace_root.expanduser().resolve() / path
        try:
            return path.stat().st_mtime
        except OSError:
            continue
    return None


def _domain_transition_direct_terminal_source_readback(
    *,
    materialized_readback: Mapping[str, Any] | None,
    study_root: Path,
    profile: Any | None = None,
    study_id: str | None = None,
    enable_opl_live_probe: bool = False,
    opl_bin: str | Path | None = None,
) -> dict[str, Any] | None:
    readback = _mapping(materialized_readback)
    direct = _mapping(readback.get("domain_transition_direct_stage_attempt"))
    if not direct and profile is not None and study_id:
        next_action = _mapping(readback.get("next_action"))
        canonical_next_action_source = _optional_text(
            readback.get("canonical_next_action_source")
        )
        domain_transition = _mapping(readback.get("domain_transition"))
        stage_closure_outcome = _mapping(
            _mapping(readback.get("stage_closure_decision")).get("outcome")
        )
        if (
            canonical_next_action_source != "domain_transition.next_action"
            and stage_closure_outcome.get("kind") != "typed_blocker"
        ):
            domain_transition_next_action = _domain_transition_canonical_next_action(
                {"domain_transition": domain_transition}
            )
            if not domain_transition_next_action and readback:
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
            if domain_transition_next_action:
                next_action = domain_transition_next_action
                canonical_next_action_source = "domain_transition.next_action"
        direct = _build_domain_transition_direct_next_action_runtime_readback(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            inspect_readback=readback,
            next_action=next_action,
            canonical_next_action_source=canonical_next_action_source,
            enable_opl_live_probe=enable_opl_live_probe,
            opl_bin=opl_bin,
        )
    if not direct:
        return None
    direct = attach_opl_runtime_carrier_readback(
        readback=direct,
        study_root=study_root,
        enable_opl_live_probe=True,
        opl_bin=None,
    )
    if _optional_text(direct.get("opl_runtime_readback_status")) != (
        "opl_runtime_terminal_readback_observed"
    ):
        return None
    return {
        **direct,
        "paper_mission_command": "terminalize-stage",
        "source": "paper_mission_domain_transition_direct_stage_attempt",
        "study_id": _optional_text(direct.get("study_id"))
        or _optional_text(readback.get("study_id")),
        "mission_id": _optional_text(direct.get("mission_id"))
        or _optional_text(readback.get("mission_id")),
        "objective": _optional_text(readback.get("objective")),
        "current_package": _mapping(readback.get("current_package")),
        "domain_transition": _mapping(readback.get("domain_transition")),
        "source_ref": _optional_text(
            _mapping(direct.get("next_action")).get("outcome_ref")
        )
        or _optional_text(_mapping(direct.get("next_action")).get("action_id")),
    }


def _materialized_run_terminal_source_readback(
    *,
    materialized_readback: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any] | None:
    materialized_ref = _optional_text(materialized_readback.get("materialized_mission_ref"))
    raw_materialized = (
        _mapping(_load_optional_json_object(Path(materialized_ref)))
        if materialized_ref is not None
        else {}
    )
    paper_mission_run = _mapping(raw_materialized) or _mapping(
        materialized_readback.get("paper_mission_run")
    )
    run_transaction = _mapping(paper_mission_run.get("paper_mission_transaction"))
    if not run_transaction:
        return None
    if _optional_text(run_transaction.get("transaction_id")) == _optional_text(
        _mapping(materialized_readback.get("paper_mission_transaction")).get(
            "transaction_id"
        )
    ):
        return None
    try:
        carrier = paper_mission_opl_runtime_carrier(run_transaction)
    except (KeyError, TypeError, ValueError, PaperMissionTransactionContractError):
        return None
    readback = attach_opl_runtime_carrier_readback(
        readback={"opl_runtime_carrier": carrier},
        study_root=study_root,
        enable_opl_live_probe=True,
        opl_bin=None,
    )
    if _optional_text(readback.get("opl_runtime_readback_status")) != (
        "opl_runtime_terminal_readback_observed"
    ):
        return None
    return {
        **dict(materialized_readback),
        "paper_mission_command": "terminalize-stage",
        "source": "paper_mission_run_legacy_transaction",
        "opl_runtime_carrier": carrier,
        "opl_runtime_carrier_readback": _mapping(
            readback.get("opl_runtime_carrier_readback")
        ),
        "opl_runtime_readback_status": _optional_text(
            readback.get("opl_runtime_readback_status")
        ),
    }


def _build_terminalizer_source_readback_from_stage_packet(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    stage_packet: str | Path,
    source: str,
) -> dict[str, Any]:
    packet_ref = Path(stage_packet).expanduser()
    if not packet_ref.is_absolute():
        packet_ref = Path(profile.workspace_root).expanduser().resolve() / packet_ref
    packet = _load_json_object(packet_ref)
    packet_study_id = _optional_text(packet.get("study_id"))
    if packet_study_id is not None and packet_study_id != study_id:
        raise ValueError(
            f"stage packet study_id mismatch: expected {study_id}, got {packet_study_id}"
        )
    base_readback = _build_terminalizer_source_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        source=f"{source}:base-current-package",
        allow_stage_packet_autodiscovery=False,
    )
    route_back = _load_stage_packet_route_back_evidence(
        workspace_root=Path(profile.workspace_root).expanduser().resolve(),
        packet=packet,
    )
    stage_attempt_id = _optional_text(packet.get("stage_attempt_id"))
    work_unit_id = _optional_text(packet.get("work_unit_id")) or _optional_text(
        route_back.get("work_unit_id")
    )
    stage_packet_ref = _first_non_empty_text(
        packet.get("stage_packet_ref"),
        route_back.get("stage_packet_ref"),
        _mapping(route_back.get("source_evidence")).get("paper_mission_transaction_ref"),
    )
    stage_id = _stage_packet_route_stage_id(
        study_id=study_id,
        packet=packet,
        route_back=route_back,
        stage_packet_ref=stage_packet_ref,
    )
    if stage_packet_ref is None:
        stage_packet_ref = str(packet_ref)
    route_back_ref = _optional_text(packet.get("route_back_evidence_ref"))
    candidate_ref = _optional_text(packet.get("owner_answer_ref")) or _optional_text(
        route_back.get("owner_answer_ref")
    )
    provider_attempt_ref = _optional_text(packet.get("provider_attempt_ref")) or (
        f"opl://stage-attempts/{stage_attempt_id}" if stage_attempt_id else None
    )
    closeout_ref = str(packet_ref)
    return {
        **base_readback,
        "surface_kind": "paper_mission_stage_attempt_closeout_readback",
        "source": source,
        "source_ref": closeout_ref,
        "study_id": study_id,
        "mission_id": base_readback.get("mission_id"),
        "candidate_ref": candidate_ref,
        "candidate_manifest_ref": candidate_ref,
        "route_back_evidence_ref": route_back_ref,
        "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
        "stage_closure_decision": {},
        "stage_closure_decision_ref": None,
        "stage_closure_outcome": None,
        "paper_mission_transaction": {
            "schema_version": "paper-mission-transaction.v1",
            "transaction_id": stage_packet_ref,
            "mission_id": base_readback.get("mission_id"),
            "study_id": study_id,
            "stage_id": stage_id,
            "work_unit_id": work_unit_id,
            "stage_terminal_decision": {
                "decision_kind": "route_back",
                "status": "route_back_evidence_observed",
                "reason": "paper_mission_stage_route_domain_gate_pending",
                "next_owner": "MedAutoScience",
                "next_work_unit": work_unit_id,
                "source_route_back_evidence_ref": route_back_ref,
                "route_back_evidence_ref": route_back_ref,
            },
            "transaction_state": "route_back",
        },
        "stage_terminal_decision": {
            "decision_kind": "route_back",
            "status": "route_back_evidence_observed",
            "reason": "paper_mission_stage_route_domain_gate_pending",
            "next_owner": "MedAutoScience",
            "next_work_unit": work_unit_id,
            "source_route_back_evidence_ref": route_back_ref,
            "route_back_evidence_ref": route_back_ref,
        },
        "transaction_state": "route_back",
        "consume_candidate_status": "route_back",
        "opl_runtime_readback_status": "opl_runtime_terminal_readback_observed",
        "opl_runtime_carrier_readback": _stage_packet_opl_runtime_carrier_readback(
            packet=packet,
            route_back=route_back,
            stage_attempt_id=stage_attempt_id,
            stage_id=stage_id,
            work_unit_id=work_unit_id,
            provider_attempt_ref=provider_attempt_ref,
            closeout_ref=closeout_ref,
        ),
        "stage_attempt_closeout_packet": packet,
    }


def _latest_stage_attempt_route_back_source_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    source_readback: Mapping[str, Any],
    source: str,
) -> dict[str, Any] | None:
    packets_root = (
        Path(profile.workspace_root).expanduser().resolve()
        / "ops"
        / "medautoscience"
        / "paper_mission_stage_attempts"
    )
    if not packets_root.exists():
        return None
    expected = _expected_stage_attempt_identity(source_readback)
    current_transaction_ref = _optional_text(
        _mapping(source_readback.get("paper_mission_transaction")).get("transaction_id")
    )
    preferred_stage_attempt_ids = _preferred_terminal_stage_attempt_ids(source_readback)
    candidates: list[tuple[int, int, int, float, str, Path]] = []
    for packet_ref in packets_root.glob("**/stage_attempt_closeout_packet.json"):
        packet = _load_optional_json_object(packet_ref)
        if not isinstance(packet, Mapping):
            continue
        if _optional_text(packet.get("study_id")) != study_id:
            continue
        route_back = _load_stage_packet_route_back_evidence(
            workspace_root=Path(profile.workspace_root).expanduser().resolve(),
            packet=packet,
        )
        route_ref = _optional_text(packet.get("route_back_evidence_ref")) or _optional_text(
            route_back.get("route_back_evidence_ref")
        )
        if route_ref is None and _optional_text(packet.get("owner_answer_kind")) != (
            "route_back_evidence_ref"
        ):
            continue
        stage_packet_ref = _first_non_empty_text(
            packet.get("stage_packet_ref"),
            route_back.get("stage_packet_ref"),
            _mapping(route_back.get("source_evidence")).get(
                "paper_mission_transaction_ref"
            ),
        )
        stage_id = _stage_packet_route_stage_id(
            study_id=study_id,
            packet=packet,
            route_back=route_back,
            stage_packet_ref=stage_packet_ref,
        )
        work_unit_id = _first_non_empty_text(
            packet.get("work_unit_id"),
            route_back.get("work_unit_id"),
        )
        stage_attempt_id = _optional_text(packet.get("stage_attempt_id"))
        transaction_priority = _stage_packet_transaction_priority(
            stage_packet_ref=stage_packet_ref,
            current_transaction_ref=current_transaction_ref,
            study_id=study_id,
        )
        bucket_priority = 0
        if (
            preferred_stage_attempt_ids
            and stage_attempt_id is not None
            and stage_attempt_id in preferred_stage_attempt_ids
        ):
            bucket_priority = 2
        elif (
            (
                not expected["stage_ids"]
                or stage_id in expected["stage_ids"]
            )
            and (
                not expected["work_unit_ids"]
                or work_unit_id in expected["work_unit_ids"]
            )
        ):
            bucket_priority = 1
        semantic_priority = _stage_packet_route_back_semantic_priority(
            packet=packet,
            route_back=route_back,
        )
        candidates.append(
            (
                transaction_priority,
                semantic_priority,
                bucket_priority,
                packet_ref.stat().st_mtime,
                str(packet_ref),
                packet_ref,
            )
        )
    if not candidates:
        return None
    packet_ref = max(
        candidates,
        key=lambda item: (item[0], item[1], item[2], item[3], item[4]),
    )[5]
    return _build_terminalizer_source_readback_from_stage_packet(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        stage_packet=packet_ref,
        source=f"{source}:autodiscovered-stage-packet",
    )

def _preferred_terminal_stage_attempt_ids(
    readback: Mapping[str, Any],
) -> set[str]:
    stage_attempt_ids = set()
    for carrier_key in (
        "opl_runtime_carrier_readback",
        "current_opl_runtime_carrier_readback",
    ):
        terminal_closeout = _mapping(
            _mapping(readback.get(carrier_key)).get("terminal_closeout")
        )
        stage_attempt_id = _optional_text(terminal_closeout.get("stage_attempt_id"))
        if stage_attempt_id is not None and (
            carrier_key == "current_opl_runtime_carrier_readback"
            or _terminal_closeout_is_live_runtime_observed(terminal_closeout)
        ):
            stage_attempt_ids.add(stage_attempt_id)
    return stage_attempt_ids


def _terminal_closeout_is_live_runtime_observed(
    closeout: Mapping[str, Any],
) -> bool:
    closeout_ref = _optional_text(closeout.get("closeout_ref"))
    if closeout_ref is not None and closeout_ref.startswith(
        "opl://family-runtime/tasks/"
    ):
        return True
    return _optional_text(closeout.get("runtime_readback_source")) in {
        "opl_family_runtime_queue_inspect",
        "opl_family_runtime_queue_list",
    }
def _expected_stage_attempt_identity(readback: Mapping[str, Any]) -> dict[str, set[str]]:
    next_action = _mapping(readback.get("next_action"))
    domain_transition = _mapping(readback.get("domain_transition"))
    transition_work_unit = _mapping(domain_transition.get("next_work_unit"))
    stage_decision = _mapping(readback.get("stage_terminal_decision"))
    transaction = _mapping(readback.get("paper_mission_transaction"))
    return {
        "stage_ids": {
            value
            for value in (
                _optional_text(next_action.get("stage_id")),
                _optional_text(domain_transition.get("route_target")),
                _optional_text(transaction.get("stage_id")),
                _optional_text(stage_decision.get("target_stage_id")),
            )
            if value is not None
        },
        "work_unit_ids": {
            value
            for value in (
                _optional_text(next_action.get("work_unit_id")),
                _optional_text(transition_work_unit.get("unit_id")),
                _optional_text(transaction.get("work_unit_id")),
                _optional_text(stage_decision.get("next_work_unit")),
                _optional_text(stage_decision.get("target_work_unit_id")),
            )
            if value is not None
        },
    }


def _load_stage_packet_route_back_evidence(
    *,
    workspace_root: Path,
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    ref = _optional_text(packet.get("route_back_evidence_ref"))
    if ref is None:
        return {}
    path = Path(ref).expanduser()
    if not path.is_absolute():
        path = workspace_root / path
    if not path.exists():
        return {}
    return _load_json_object(path)


def _stage_packet_route_stage_id(
    *,
    study_id: str,
    packet: Mapping[str, Any],
    route_back: Mapping[str, Any],
    stage_packet_ref: str | None,
) -> str | None:
    derived = _paper_mission_transaction_stage_id(
        stage_packet_ref,
        study_id=study_id,
    )
    packet_stage_id = _optional_text(packet.get("stage_id"))
    route_stage_id = _optional_text(route_back.get("stage_id"))
    route_work_unit_id = _optional_text(route_back.get("work_unit_id"))
    return (
        derived
        or (
            route_stage_id
            if packet_stage_id is not None
            and route_work_unit_id is not None
            and packet_stage_id == route_work_unit_id
            else None
        )
        or packet_stage_id
        or route_stage_id
    )


def _paper_mission_transaction_stage_id(
    transaction_ref: str | None,
    *,
    study_id: str,
) -> str | None:
    if transaction_ref is None:
        return None
    prefix = f"paper-mission-transaction::{study_id}::"
    suffix = "::paper-mission::"
    if not transaction_ref.startswith(prefix) or suffix not in transaction_ref:
        return None
    stage_segment = transaction_ref[len(prefix) : transaction_ref.index(suffix)]
    if not stage_segment:
        return None
    return stage_segment.split("::followthrough::", 1)[0] or None


def _stage_packet_transaction_priority(
    *,
    stage_packet_ref: str | None,
    current_transaction_ref: str | None,
    study_id: str,
) -> int:
    if stage_packet_ref is None or current_transaction_ref is None:
        return 0
    if stage_packet_ref == current_transaction_ref:
        return 1
    if stage_packet_ref.startswith(f"{current_transaction_ref}::followthrough::"):
        return 2
    if current_transaction_ref.startswith(f"{stage_packet_ref}::followthrough::"):
        return 1
    current_stage = _paper_mission_transaction_stage_id(
        current_transaction_ref,
        study_id=study_id,
    )
    stage_packet_stage = _paper_mission_transaction_stage_id(
        stage_packet_ref,
        study_id=study_id,
    )
    if current_stage is None or stage_packet_stage is None:
        return 0
    if stage_packet_stage.startswith(f"{current_stage}::followthrough::"):
        return 2
    if current_stage.startswith(f"{stage_packet_stage}::followthrough::"):
        return 1
    return 0


def _stage_packet_route_back_semantic_priority(
    *,
    packet: Mapping[str, Any],
    route_back: Mapping[str, Any],
) -> int:
    route_impact = _mapping(packet.get("route_impact"))
    priority = 0
    if _first_non_empty_text(
        packet.get("paper_facing_delta_ref"),
        route_impact.get("paper_facing_delta_ref"),
        route_back.get("paper_facing_delta_ref"),
    ) is not None:
        priority += 2
    if _first_non_empty_text(
        packet.get("progress_events_ref"),
        route_back.get("progress_events_ref"),
    ) is not None:
        priority += 1
    if _first_non_empty_text(
        route_impact.get("stage_log_summary"),
        route_impact.get("user_stage_log"),
        route_impact.get("human_stage_log"),
    ) is not None:
        priority += 1
    if _first_non_empty_text(
        route_back.get("owner_gate_verdict"),
        route_back.get("next_forced_paper_action"),
        route_back.get("source_readiness_checklist_ref"),
        route_back.get("remaining_blocker"),
    ) is not None:
        priority += 1
    if _mapping(route_back.get("source_evidence")):
        priority += 1
    return priority


def _first_non_empty_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _stage_packet_opl_runtime_carrier_readback(
    *,
    packet: Mapping[str, Any],
    route_back: Mapping[str, Any],
    stage_attempt_id: str | None,
    stage_id: str | None,
    work_unit_id: str | None,
    provider_attempt_ref: str | None,
    closeout_ref: str,
) -> dict[str, Any]:
    closeout_receipt_status = (
        _optional_text(packet.get("closeout_receipt_status"))
        or "accepted_stage_attempt_closeout"
    )
    blocked_reason = (
        _optional_text(packet.get("blocked_reason"))
        or "paper_mission_stage_route_domain_gate_pending"
    )
    receipt_ref = provider_attempt_ref or closeout_ref
    receipt_evidence = {
        "receipt_kind": "opl_transition_receipt",
        "receipt_ref": receipt_ref,
        "runtime_closeout_ref": closeout_ref,
        "stage_attempt_ref": receipt_ref,
        "can_claim_paper_progress": False,
    }
    return {
        "surface_kind": "paper_mission_opl_runtime_carrier_readback",
        "schema_version": 1,
        "carrier_status": "opl_runtime_terminal_readback_observed",
        "runtime_readback_status": "terminal_closeout_observed",
        "dispatch_status": "terminal_closeout_observed",
        "domain_ready_verdict": "domain_gate_pending",
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
        "request_carrier_preserved": True,
        "terminal_closeout": {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": _optional_text(packet.get("status")) or "completed",
            "study_id": _optional_text(packet.get("study_id"))
            or _optional_text(route_back.get("study_id")),
            "stage_id": stage_id,
            "stage_attempt_id": stage_attempt_id,
            "work_unit_id": work_unit_id,
            "provider_attempt_ref": provider_attempt_ref,
            "blocked_reason": blocked_reason,
            "closeout_refs": [closeout_ref],
            "closeout_receipt_status": closeout_receipt_status,
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
            "domain_completion_claimed": False,
            "domain_ready_claimed": False,
        },
        "opl_transition_receipt": {
            "surface_kind": "opl_transition_receipt",
            "receipt_status": "terminal_closeout_observed",
            "role": "transport_receipt_only",
            "stage_attempt_id": stage_attempt_id,
            "stage_attempt_ref": receipt_ref,
            "closeout_receipt_status": closeout_receipt_status,
            "blocked_reason": blocked_reason,
            "can_claim_paper_progress": False,
        },
        "receipt_evidence": receipt_evidence,
        "mas_receipt_consumption": {
            "surface_kind": "mas_receipt_consumption_projection",
            "status": "requires_mas_owner_consumption",
            "next_legal_action": (
                "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
            ),
            "forbidden_next_action": "synonymous_route_back_redrive",
            "receipt_ref": receipt_ref,
            "runtime_closeout_ref": closeout_ref,
            "durable_stop_allowed": False,
        },
    }


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"Expected JSON object at {path}")
    return dict(payload)


def _typed_blocker_resolution_should_own_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    typed_blocker_resolution_readback: Mapping[str, Any] | None,
) -> bool:
    if not typed_blocker_resolution_readback:
        return False
    outcome = _mapping(stage_closure_decision.get("outcome"))
    if outcome.get("kind") != "typed_blocker":
        return False
    return bool(_mapping(typed_blocker_resolution_readback.get("next_owner_action")))


def _stage_closure_next_action_should_own_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    next_action: Mapping[str, Any] | None,
    domain_transition_next_action: Mapping[str, Any] | None = None,
    receipt_owner_consumption_readback: Mapping[str, Any] | None = None,
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
        if _receipt_owner_consumed_route_checkpoint(receipt_owner_consumption_readback):
            return not _owner_consumed_route_checkpoint_yields_to_domain_transition(
                stage_closure_decision=stage_closure_decision,
                domain_transition_next_action=domain_transition_next_action,
            )
        return _route_checkpoint_matches_domain_transition(
            stage_closure_decision=stage_closure_decision,
            outcome=outcome,
            domain_transition_next_action=domain_transition_next_action,
        )
    if _optional_text(action.get("action_family")) == (
        "paper.stage_closure.owner_consumption"
    ):
        return True
    return (
        outcome.get("kind") == "next_stage_transition"
        and outcome.get("transition_kind") == "route_back_candidate_checkpoint"
    )


def _receipt_owner_consumed_route_checkpoint(
    readback: Mapping[str, Any] | None,
) -> bool:
    payload = _mapping(readback)
    if _optional_text(payload.get("status")) != "owner_consumption_applied":
        return False
    consumption = _mapping(payload.get("mas_receipt_consumption"))
    return _optional_text(consumption.get("status")) == "owner_consumed_route_checkpoint"


def _align_current_carrier_owner_consumption(
    *,
    transaction_output_fields: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any],
) -> dict[str, Any]:
    fields = dict(transaction_output_fields)
    changed = False
    current = _mapping(fields.get("current_opl_runtime_carrier_readback"))
    aligned_current = current
    preserve_direct_successor = _preserve_direct_successor_runtime_readback(
        transaction_output_fields=fields,
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
    )
    if current and not preserve_direct_successor:
        aligned_current = _align_carrier_readback_with_owner_consumption(
            carrier_readback=current,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
        )
        if aligned_current != current:
            fields["current_opl_runtime_carrier_readback"] = aligned_current
            changed = True
    direct = _mapping(fields.get("domain_transition_direct_stage_attempt"))
    if direct and aligned_current != current:
        fields["domain_transition_direct_stage_attempt"] = {
            **direct,
            "opl_runtime_carrier_readback": aligned_current,
        }
    carrier = _mapping(fields.get("opl_runtime_carrier_readback"))
    if carrier:
        aligned_carrier = _align_carrier_readback_with_owner_consumption(
            carrier_readback=carrier,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
        )
        if aligned_carrier != carrier:
            fields["opl_runtime_carrier_readback"] = aligned_carrier
            changed = True
            aligned_gate = _terminal_owner_gate_from_carrier_readback(aligned_carrier)
            owner_answer_readback = {}
            transaction_readback = _mapping(fields.get("paper_mission_transaction_readback"))
            if transaction_readback:
                paper_mission_transaction = _mapping(
                    transaction_readback.get("paper_mission_transaction")
                )
                if paper_mission_transaction and aligned_gate:
                    owner_answer_readback = _terminal_owner_gate_owner_answer_readback(
                        terminal_owner_gate=aligned_gate,
                        paper_mission_transaction=paper_mission_transaction,
                        artifact_delta_refs=_mapping_list(
                            transaction_readback.get("artifact_delta_refs")
                        )
                        or _mapping_list(
                            paper_mission_transaction.get("artifact_delta_refs")
                        ),
                        paper_audit_pack_refs=_mapping(
                            transaction_readback.get("paper_audit_pack_refs")
                        )
                        or _mapping(
                            paper_mission_transaction.get("paper_audit_pack_refs")
                        ),
                    )
                authority_readback = _terminal_owner_gate_authority_readback(aligned_gate)
                if owner_answer_readback:
                    authority_readback = _terminal_owner_gate_authority_consume_readback(
                        terminal_owner_gate_authority_readback=authority_readback,
                        owner_answer_readback=owner_answer_readback,
                    )
                fields["paper_mission_transaction_readback"] = {
                    **transaction_readback,
                    "opl_runtime_carrier_readback": aligned_carrier,
                    "terminal_owner_gate": aligned_gate or None,
                    "terminal_owner_gate_authority_readback": authority_readback or None,
                    "terminal_owner_gate_owner_answer_readback": (
                        owner_answer_readback or None
                    ),
                }
            if aligned_gate:
                fields["terminal_owner_gate"] = aligned_gate
                authority_readback = _terminal_owner_gate_authority_readback(aligned_gate)
                if owner_answer_readback:
                    authority_readback = _terminal_owner_gate_authority_consume_readback(
                        terminal_owner_gate_authority_readback=authority_readback,
                        owner_answer_readback=owner_answer_readback,
                    )
                fields["terminal_owner_gate_authority_readback"] = authority_readback or None
                fields["terminal_owner_gate_owner_answer_readback"] = (
                    owner_answer_readback or None
                )
    return fields if changed else transaction_output_fields


def _preserve_direct_successor_runtime_readback(
    *,
    transaction_output_fields: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any],
) -> bool:
    direct = _mapping(transaction_output_fields.get("domain_transition_direct_stage_attempt"))
    if not direct:
        return False
    handoff = _mapping(direct.get("opl_route_handoff"))
    successor_owner_consumption_ref = _optional_text(
        handoff.get("owner_consumption_readback_ref")
    )
    if successor_owner_consumption_ref is None:
        return False
    applied_owner_consumption_ref = _first_text(
        receipt_owner_consumption_readback.get("source_ref"),
        receipt_owner_consumption_readback.get("decision_ref"),
    )
    if successor_owner_consumption_ref != applied_owner_consumption_ref:
        return False
    carrier_readback = _mapping(direct.get("opl_runtime_carrier_readback"))
    carrier_status = _optional_text(carrier_readback.get("carrier_status"))
    return carrier_status in {
        "opl_runtime_attempt_running_observed",
        "opl_runtime_terminal_readback_observed",
    }


def _route_checkpoint_matches_domain_transition(
    *,
    stage_closure_decision: Mapping[str, Any],
    outcome: Mapping[str, Any],
    domain_transition_next_action: Mapping[str, Any] | None,
) -> bool:
    if not _route_checkpoint_identity_matches_domain_transition(
        stage_closure_decision=stage_closure_decision,
        domain_transition_next_action=domain_transition_next_action,
    ):
        return False
    return (
        stage_closure_decision.get("authority_materialized") is True
        or _optional_text(outcome.get("route_checkpoint_evidence_ref")) is not None
        or _optional_text(
            _mapping(stage_closure_decision.get("opl_closeout")).get("stage_attempt_id")
        )
        is not None
    )


def _owner_consumed_route_checkpoint_yields_to_domain_transition(
    *,
    stage_closure_decision: Mapping[str, Any],
    domain_transition_next_action: Mapping[str, Any] | None,
) -> bool:
    if _route_checkpoint_identity_matches_domain_transition(
        stage_closure_decision=stage_closure_decision,
        domain_transition_next_action=domain_transition_next_action,
    ):
        return True
    action = _mapping(domain_transition_next_action)
    if _optional_text(action.get("surface_kind")) != "mas_next_action_envelope":
        return False
    if _optional_text(action.get("action_type")) != "request_opl_stage_attempt":
        return False
    decision_stage = _optional_text(stage_closure_decision.get("stage_id"))
    action_stage = _optional_text(action.get("stage_id"))
    if decision_stage is None or action_stage is None:
        return False
    return decision_stage == action_stage


def _route_checkpoint_identity_matches_domain_transition(
    *,
    stage_closure_decision: Mapping[str, Any],
    domain_transition_next_action: Mapping[str, Any] | None,
) -> bool:
    action = _mapping(domain_transition_next_action)
    if not action:
        return False
    decision_work_unit = _optional_text(stage_closure_decision.get("work_unit_id"))
    action_work_unit = _optional_text(action.get("work_unit_id"))
    if (
        decision_work_unit is not None
        and action_work_unit is not None
        and decision_work_unit != action_work_unit
    ):
        return False
    decision_stage = _optional_text(stage_closure_decision.get("stage_id"))
    action_stage = _optional_text(action.get("stage_id"))
    if (
        decision_stage is not None
        and action_stage is not None
        and decision_stage != action_stage
    ):
        return False
    return True
    return True


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
    )
    return (
        refreshed_stage_closure_decision,
        refreshed_next_action,
        "stage_closure.next_action"
        if refreshed_next_action is not None
        else canonical_next_action_source,
    )



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
