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
)
from med_autoscience.paper_mission_consumption_ledger import (
    write_paper_mission_consumption_ledger_outputs,
)
from med_autoscience.paper_mission_stage_closure_ledger import (
    write_paper_mission_stage_closure_decision,
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
    FORBIDDEN_AUTHORITY_CLAIMS as STAGE_CLOSURE_FORBIDDEN_AUTHORITY_CLAIMS,
    STAGE_CLOSURE_FORBIDDEN_AUTHORITY_WRITES,
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
    receipt_owner_consumption_superseded_by_consumption as _receipt_superseded_by_consumption,
)
from med_autoscience.controllers import study_domain_transition_table
from med_autoscience.controllers.study_progress_parts.canonical_next_action_selection import (
    domain_transition_canonical_next_action as _domain_transition_canonical_next_action,
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
    if (
        domain_transition_next_action
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
        authority_consume_readback=None,
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
    receipt_owner_consumption = _latest_receipt_owner_consumption_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=study_id,
    )
    if receipt_owner_consumption is not None and _receipt_superseded_by_consumption(
        receipt_owner_consumption_readback=receipt_owner_consumption,
        consumption_ledger_readback=consumption_readback,
    ):
        receipt_owner_consumption = None
    if receipt_owner_consumption is None:
        route_back_projection = _consumption_ledger_route_back_projection(
            transaction_readback=transaction_readback,
            consumption_readback=consumption_readback,
            base_readback=base,
        )
        if route_back_projection is not None:
            return route_back_projection
        return {
            **base,
            **_transaction_readback_output_fields(transaction_readback),
        }
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
    next_action_override = _next_action_for_stage_closure_decision(
        stage_closure_decision=stage_closure_decision,
        transaction_readback=transaction_readback,
        typed_blocker_resolution_readback=typed_blocker_resolution_readback,
    )
    transaction_output_fields = _transaction_readback_output_fields(transaction_readback)
    if next_action_override is not None:
        transaction_output_fields["next_action"] = next_action_override
        transaction_output_fields["paper_mission_transaction_readback"] = {
            **transaction_readback,
            "next_action": next_action_override,
        }
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
    return {
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
    }


def _consumption_ledger_route_back_projection(
    *,
    transaction_readback: Mapping[str, Any],
    consumption_readback: Mapping[str, Any],
    base_readback: Mapping[str, Any],
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
    direct_stage_attempt = _domain_transition_direct_terminal_source_readback(
        materialized_readback=source_readback,
    )
    if direct_stage_attempt is not None:
        return direct_stage_attempt
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
        return source_readback
    return build_paper_mission_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        source=source,
        enable_opl_live_probe=True,
    )


def _domain_transition_direct_terminal_source_readback(
    *,
    materialized_readback: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    readback = _mapping(materialized_readback)
    direct = _mapping(readback.get("domain_transition_direct_stage_attempt"))
    if not direct:
        return None
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
    )
    route_back = _load_stage_packet_route_back_evidence(
        workspace_root=Path(profile.workspace_root).expanduser().resolve(),
        packet=packet,
    )
    stage_attempt_id = _optional_text(packet.get("stage_attempt_id"))
    work_unit_id = _optional_text(packet.get("work_unit_id")) or _optional_text(
        route_back.get("work_unit_id")
    )
    stage_id = _optional_text(packet.get("stage_id")) or _optional_text(
        route_back.get("stage_id")
    )
    stage_packet_ref = _optional_text(packet.get("stage_packet_ref")) or str(packet_ref)
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
    return (
        outcome.get("kind") == "next_stage_transition"
        and outcome.get("transition_kind") == "route_back_candidate_checkpoint"
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
