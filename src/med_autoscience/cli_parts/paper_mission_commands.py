from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

from med_autoscience.paper_mission import (
    paper_mission_candidate_artifact_delta,
    paper_mission_canary_candidate_manifest,
    paper_mission_owner_decision_packet,
)
from med_autoscience.paper_mission_authority import consume_paper_mission_candidate
from med_autoscience.paper_mission_candidate_materializer import (
    materialized_paper_facing_candidate_delta,
)
from med_autoscience.paper_mission_candidate_package import (
    paper_mission_owner_blocker_packet,
    paper_mission_owner_consumption_request,
)
from med_autoscience.paper_mission_consumption_readback import (
    latest_paper_mission_consumption_transaction_readback,
)
from med_autoscience.paper_mission_consumption_ledger import (
    write_paper_mission_consumption_ledger_outputs,
)
from med_autoscience.paper_mission_stage_closure_ledger import (
    latest_paper_mission_stage_closure_decision_readback,
    write_paper_mission_stage_closure_decision,
)
from med_autoscience.paper_mission_opl_carrier import (
    paper_mission_opl_runtime_carrier,
)
from med_autoscience.paper_mission_opl_readback import (
    attach_opl_runtime_carrier_readback,
    attach_paper_mission_next_action,
)
from med_autoscience.controllers.next_action_envelope import compile_next_action_envelope
from med_autoscience.cli_parts.paper_mission_output_roots import (
    PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH,
    PAPER_MISSION_CONSUMPTION_LEDGER_RELPATH,
    PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH,
    PAPER_MISSION_STAGE_CLOSURE_RELPATH,
    YANG_WORKSPACE_ROOT,
    _assert_safe_candidate_output_root,
    _assert_safe_candidate_package_output_root,
    _assert_safe_consumption_ledger_output_root,
    _assert_safe_one_shot_output_root,
    _assert_safe_receipt_owner_consumption_output_root,
    _assert_safe_stage_closure_output_root,
    _is_yang_ops_candidate_package_root,
    _is_yang_ops_candidate_root,
    _is_yang_ops_consumption_ledger_root,
    _is_yang_ops_non_authority_candidate_root,
    _is_yang_ops_root,
    _is_under_yang_workspace,
)
from med_autoscience.cli_parts.paper_mission_command_parts.receipt_owner_consumption import (
    build_receipt_owner_consumption_readback as _build_receipt_owner_consumption_readback,
    latest_receipt_owner_consumption_readback,
    receipt_owner_consumption_apply_mode as _receipt_owner_consumption_apply_mode,
)
from med_autoscience.cli_parts.paper_mission_command_parts.candidate_package_context import (
    foreground_owner_decision_summary as _candidate_foreground_owner_decision_summary,
    mission_executor_handoff as _candidate_mission_executor_handoff,
)
from med_autoscience.cli_parts.paper_mission_command_parts.candidate_package_outputs import (
    write_materialized_candidate_package_outputs as _candidate_write_materialized_candidate_package_outputs,
)
from med_autoscience.cli_parts.paper_mission_command_parts.domain_handler_dispatch import (
    paper_mission_domain_handler_dispatch_receipt as _paper_mission_domain_handler_dispatch_receipt,
)
from med_autoscience.cli_parts.paper_mission_command_parts.followthrough_materialized_readback import (
    followthrough_transaction_for_readback as _followthrough_transaction_for_readback_impl,
    paper_mission_followthrough_source_readback as _paper_mission_followthrough_source_readback_impl,
)
from med_autoscience.cli_parts.paper_mission_command_parts.materialized_readback_context import (
    consume_candidate_status as _consume_candidate_status,
    dispatch_execution_policy as _dispatch_execution_policy,
    materialized_mission_path_matches as _materialized_mission_path_matches,
    materialized_opl_route_command as _materialized_opl_route_command,
    materialized_stage_terminal_decision as _materialized_stage_terminal_decision,
    materialized_study_id as _materialized_study_id,
    materialized_study_root as _materialized_study_root,
    normalize_materialized_mission_for_cli_readback as _normalize_materialized_mission_for_cli_readback,
    paper_audit_pack_for_cli_readback as _paper_audit_pack_for_cli_readback,
    paper_facing_action_fields as _paper_facing_action_fields,
    recommended_domain_command as _recommended_domain_command,
)
from med_autoscience.cli_parts.paper_mission_command_parts.parser_registration import (
    register_paper_mission_parsers,
)
from med_autoscience.cli_parts.paper_mission_command_parts.one_shot_migration import (
    ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES,
    build_one_shot_migration_cli_readback as _build_one_shot_migration_cli_readback_impl,
)
from med_autoscience.cli_parts.paper_mission_command_parts.opl_runtime_submission import (
    drive_result_status as _paper_mission_drive_result_status,
    opl_runtime_submission_readback as _opl_runtime_submission_readback,
    refresh_consume_readback_after_opl_submission as _refresh_consume_readback_after_opl_submission,
    semantic_progress_guard as _paper_mission_semantic_progress_guard,
    stage_closure_missing_runtime_submission as _stage_closure_missing_runtime_submission,
)
from med_autoscience.cli_parts.paper_mission_command_parts.route_back_budget import (
    _canonicalize_followthrough_transaction_identity,
    _empty_paper_mission_route_back_budget_ledger,
    _paper_mission_canonical_followthrough_identity,
    _paper_mission_mas_owned_executor_stage_packet,
    _paper_mission_route_back_budget_exhausted,
    _paper_mission_route_back_budget_ledger_path,
    _record_paper_mission_route_back_budget_ledger,
    _load_paper_mission_route_back_budget_ledger,
)
from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _compact_mapping,
    _compact_non_null_mapping,
    _dedupe_optional_texts,
    _first_mapping,
    _first_text,
    _first_text_item,
    _is_relative_to,
    _load_json_object,
    _load_optional_json_object,
    _mapping,
    _mapping_list,
    _optional_text,
    _paper_mission_sorted_mapping,
    _slug,
    _stable_sha256,
    _text_list,
)
from med_autoscience.cli_parts.paper_mission_command_parts.stage_closure_terminalizer import (
    current_package_is_submission_ready_clear as _current_package_is_submission_ready_clear,
    stage_closure_decision_requires_reterminalize as _stage_closure_decision_requires_reterminalize,
    stage_closure_delivery_readback as _stage_closure_delivery_readback,
    stage_closure_opl_closeout as _stage_closure_opl_closeout,
    stage_closure_readback_blockers as _stage_closure_readback_blockers,
    stage_closure_semantic_delta as _stage_closure_semantic_delta,
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
    _consume_result_for_consumption_ledger_readback,
    _durable_mission_stop_guard,
    _mission_state_for_materialized_readback,
    _next_owner_decision_for_consumption_ledger_readback,
    _paper_mission_run_candidate,
    _paper_mission_transaction_readback as _paper_mission_transaction_readback_impl,
    _transaction_readback_output_fields,
)
from med_autoscience.paper_mission_owner_answer import (
    terminal_owner_gate_authority_consume_readback,
    terminal_owner_gate_owner_answer_next_decision,
    terminal_owner_gate_owner_answer_readback,
)
from med_autoscience.paper_mission_terminal_owner_gate import (
    stage_terminal_next_owner_or_human_decision,
    terminal_owner_gate_authority_readback,
    terminal_owner_gate_from_carrier_readback,
    terminal_owner_gate_from_stage_terminal_decision,
    terminal_owner_gate_next_decision,
)
from med_autoscience.paper_mission_transaction import (
    stage_terminal_decision_for_consume_result,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_missing,
    stage_closure_decision_projection,
    stage_closure_signature,
    terminalize_stage_closure,
)
from med_autoscience.controllers.study_interventions import read_intervention_events
from med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection import (
    submission_authority_owner_gate_readback,
)
PAPER_MISSION_CONTRACT_REF = "contracts/paper_mission_run_contract.json"
PAPER_MISSION_CONTRACT_VERSION = "paper-mission-run.v1"
PAPER_MISSION_CONTRACT_COMMIT = "a410db5c0c874187c8b1ddecee79c2e00c8fe691"
PAPER_MISSION_START_OR_RESUME_TASK_KIND = "paper_mission/start_or_resume"
DEFAULT_PAPER_MISSION_DRIVE_FOLLOWTHROUGH_LIMIT = 2

FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "/Users/gaofeng/workspace/Yang/**",
)
CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "Yang study truth surfaces",
    "Yang runtime authority surfaces",
    "Yang output outside ops/medautoscience/paper_mission_candidate_package",
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
STAGE_CLOSURE_FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "Yang study truth surfaces",
    "Yang runtime authority surfaces",
    "Yang output outside ops/medautoscience/paper_mission_stage_closure",
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
PAPER_AUDIT_PACK_FAMILIES = (
    "analysis_rationale_log",
    "decision_trace",
    "evidence_ledger_delta",
    "review_ledger_delta",
    "revision_log_delta",
    "failed_path_ledger",
    "artifact_lineage",
    "reproducibility_refs",
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
        )
    if paper_mission_command == "terminalize-stage":
        return _build_stage_closure_terminalizer_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            output_root=output_root,
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
    submission_gate_readback = _submission_authority_owner_gate_readback(
        study_root=Path(profile.studies_root) / study_id,
        study_id=study_id,
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


def _build_paper_mission_drive_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: str | Path | None,
    run_id: str | None,
    submit_opl_runtime: bool | None,
    opl_bin: str | Path | None,
    source: str,
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
    package_readback = _build_materialized_candidate_package_readback(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        output_root=package_root,
        source=f"{source}:drive:package-candidate",
    )
    candidate_ref = package_readback["output_manifest"]["package_manifest_ref"]
    consume_readback = build_paper_mission_readback(
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
        "dry_run": False,
        "profile": package_readback["profile"],
        "requested_study_id": package_readback["requested_study_id"],
        "study_id": package_readback["study_id"],
        "study_root": package_readback["study_root"],
        "study_root_exists": package_readback["study_root_exists"],
        "mission_id": consume_readback["mission_id"],
        "objective": consume_readback["objective"],
        "output_root": str(root),
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
        "stage_closure_outcome": _mapping(
            stage_closure_decision.get("outcome")
        ).get("kind"),
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
            "forbidden_authority_writes": list(CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES),
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
        "forbidden_authority_writes": list(CONSUMPTION_LEDGER_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "drive_result": drive_result,
    }


def _materialize_stage_closure_for_drive_readback(
    *,
    profile: Any,
    study_id: str,
    consume_readback: Mapping[str, Any],
    source: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    decision = _terminalize_stage_closure_from_readback(consume_readback)
    root = _stage_closure_terminalizer_output_root(
        profile=profile,
        output_root=None,
    )
    _assert_safe_stage_closure_output_root(root)
    output_manifest = write_paper_mission_stage_closure_decision(
        output_root=root,
        study_id=study_id,
        decision=decision,
        source_readback=consume_readback,
        source=source,
        forbidden_authority_writes=STAGE_CLOSURE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )
    refreshed = _attach_stage_closure_ledger_to_drive_readback(
        profile=profile,
        consume_readback=consume_readback,
    )
    return refreshed, output_manifest


def _attach_stage_closure_ledger_to_drive_readback(
    *,
    profile: Any,
    consume_readback: Mapping[str, Any],
) -> dict[str, Any]:
    transaction = _mapping(consume_readback.get("paper_mission_transaction"))
    transaction_ref = _optional_text(transaction.get("transaction_id"))
    stage_closure_ledger_readback = latest_paper_mission_stage_closure_decision_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=str(consume_readback.get("study_id") or transaction.get("study_id") or ""),
        transaction_ref=transaction_ref,
    )
    if stage_closure_ledger_readback is None and transaction_ref is not None:
        stage_closure_ledger_readback = (
            latest_paper_mission_stage_closure_decision_readback(
                workspace_root=Path(profile.workspace_root),
                study_id=str(
                    consume_readback.get("study_id") or transaction.get("study_id") or ""
                ),
                transaction_ref=None,
            )
        )
    if stage_closure_ledger_readback is None:
        return dict(consume_readback)
    return {
        **dict(consume_readback),
        "stage_closure_decision": stage_closure_ledger_readback,
        "stage_closure_decision_ref": stage_closure_ledger_readback.get("decision_ref"),
        "stage_closure_outcome": _mapping(
            stage_closure_ledger_readback.get("outcome")
        ).get("kind"),
        "paper_mission_stage_closure_ledger_readback": stage_closure_ledger_readback,
    }


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
        consume_readback = build_paper_mission_readback(
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


def _paper_mission_drive_followthrough_empty(
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


def _build_stage_closure_terminalizer_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: str | Path | None,
    dry_run: bool,
    source: str,
) -> dict[str, Any]:
    source_readback = _build_materialized_mission_readback_if_available(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        paper_mission_command="inspect",
        dry_run=False,
        source=f"{source}:terminalize-stage:inspect",
        enable_opl_live_probe=True,
        opl_bin=None,
    )
    if source_readback is None:
        source_readback = build_paper_mission_readback(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command="inspect",
            dry_run=False,
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
            forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
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
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "required_next_owner": _mapping(decision.get("outcome")).get("next_owner"),
        "required_next_action": _mapping(decision.get("outcome")).get("next_action"),
    }



def _paper_mission_mas_owned_executor_delta_checkpoint(
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


def _paper_mission_followthrough_trigger(
    *,
    consume_readback: Mapping[str, Any],
    opl_runtime_submission: Mapping[str, Any],
) -> str | None:
    drive_result = _paper_mission_drive_result(
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


def _paper_mission_followthrough_stop_reason(
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
    trigger = _paper_mission_followthrough_trigger(
        consume_readback=consume_readback,
        opl_runtime_submission=opl_runtime_submission,
    )
    if trigger is not None:
        return "followthrough_available"
    drive_status = _paper_mission_drive_result(
        consume_readback=consume_readback,
        handoff=_mapping(
            _mapping(consume_readback.get("consume_output_manifest")).get(
                "opl_route_handoff"
            )
        ),
        opl_runtime_submission=opl_runtime_submission,
    ).get("status")
    return _optional_text(drive_status) or "no_followthrough_needed"


def _paper_mission_drive_output_roots(
    *,
    profile: Any,
    output_root: str | Path | None,
    run_id: str | None,
) -> dict[str, Path]:
    if output_root is not None:
        root = Path(output_root).expanduser().resolve()
        if _is_under_yang_workspace(root):
            selected_run_id = _optional_text(run_id) or root.name or "paper_mission_drive"
            workspace_root = _yang_workspace_root_for_path(root)
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
    else:
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


def _yang_workspace_root_for_path(path: Path) -> Path:
    normalized = path.expanduser().resolve()
    relative = normalized.relative_to(YANG_WORKSPACE_ROOT)
    return YANG_WORKSPACE_ROOT / relative.parts[0]


def _paper_mission_drive_result(
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


def _consume_candidate_missing_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    paper_mission_command: str,
    source: str,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "surface_kind": "paper_mission_consume_candidate_missing_readback",
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
        "status": "candidate_package_missing",
        "required_next_command": (
            "paper-mission package-candidate --output-root "
            f"{Path(profile.workspace_root) / PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH / '<run_id>'}"
        ),
        "authority_consume_readback": {
            "surface_kind": "mas_paper_mission_candidate_consume_readback",
            "schema_version": 1,
            "status": "route_back",
            "selected_outcome": "route_back",
            "consume_result": {
                "status": "route_back",
                "outcome": "route_back",
                "authority_materialized": False,
            },
            "candidate_is_authority": False,
            "route_back": {
                "reason_code": "candidate_package_missing",
                "next_owner": "mission_executor",
                "resume_condition": (
                    "generate a submission_milestone_candidate package before "
                    "MAS authority consumption"
                ),
            },
            "write_plan": {
                "mode": "readback_only",
                "written_files": [],
            },
        },
        "mutation_policy": _mutation_policy(paper_mission_command=paper_mission_command),
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "dispatch_plan": {
            "default_action_intent": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_task_kind": PAPER_MISSION_START_OR_RESUME_TASK_KIND,
            "domain_handler_dispatch_mode": "candidate_package_missing_no_write",
            "old_owner_callable_dispatch_role": "diagnostic_or_migration_only",
        },
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


def _build_materialized_mission_readback_if_available(
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
    stage_closure_ledger_readback = latest_paper_mission_stage_closure_decision_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=resolved_study_id,
        transaction_ref=_optional_text(
            transaction_readback["paper_mission_transaction"].get("transaction_id")
        ),
    )
    receipt_owner_consumption_readback = latest_receipt_owner_consumption_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=resolved_study_id,
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


def _paper_mission_inspect_projection_fields(
    *,
    stage_closure_decision: Mapping[str, Any],
    projection_fields: Mapping[str, Any],
) -> dict[str, Any]:
    decision = _mapping(stage_closure_decision)
    outcome = _mapping(decision.get("outcome"))
    return _compact_mapping(
        {
            "repair_budget": _first_mapping(
                _mapping(decision.get("repair_budget")),
                _mapping(projection_fields.get("repair_budget")),
                _mapping(projection_fields.get("route_back_budget")),
            )
            or None,
            "stage_closure": _compact_mapping(
                {
                    "projection_status": decision.get("projection_status"),
                    "decision_ref": decision.get("decision_ref"),
                    "outcome": outcome or None,
                    "outcome_kind": _first_text(
                        decision.get("outcome_kind"),
                        outcome.get("kind"),
                    ),
                    "next_transition": _first_text(
                        _mapping(outcome.get("next_transition")).get("transition_kind"),
                        outcome.get("transition_kind"),
                        outcome.get("next_action"),
                    ),
                    "package_kind": _first_text(
                        decision.get("package_kind"),
                        outcome.get("package_kind"),
                    ),
                    "known_blockers": _text_list(decision.get("known_blockers")),
                    "repair_budget": _first_mapping(
                        _mapping(decision.get("repair_budget")),
                        _mapping(projection_fields.get("repair_budget")),
                        _mapping(projection_fields.get("route_back_budget")),
                    )
                    or None,
                }
            )
            or None,
            "current_package": _paper_mission_current_package_projection(projection_fields),
        }
    )


def _merge_stage_closure_typed_blocker_gate_fields(
    *,
    transaction_output_fields: Mapping[str, Any],
    stage_closure_decision: Mapping[str, Any],
    next_action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    gate = _terminal_owner_gate_from_stage_closure_decision(
        stage_closure_decision=stage_closure_decision,
        next_action=next_action,
    )
    if not gate:
        return dict(transaction_output_fields)
    merged = dict(transaction_output_fields)
    merged["terminal_owner_gate"] = gate
    authority_readback = terminal_owner_gate_authority_readback(gate)
    merged["terminal_owner_gate_authority_readback"] = authority_readback or None
    merged["next_owner_or_human_decision"] = terminal_owner_gate_next_decision(gate)
    readback = _mapping(merged.get("paper_mission_transaction_readback"))
    if readback:
        merged["paper_mission_transaction_readback"] = {
            **readback,
            "terminal_owner_gate": gate,
            "terminal_owner_gate_authority_readback": authority_readback or None,
            "next_owner_or_human_decision": merged["next_owner_or_human_decision"],
        }
    return merged


def _terminal_owner_gate_from_stage_closure_decision(
    *,
    stage_closure_decision: Mapping[str, Any],
    next_action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    decision = _mapping(stage_closure_decision)
    outcome = _mapping(decision.get("outcome"))
    if outcome.get("kind") != "typed_blocker":
        return {}
    action = _mapping(next_action)
    typed_blocker_ref = _first_text(
        outcome.get("typed_blocker_ref"),
        outcome.get("typed_blocker_evidence_ref"),
        decision.get("decision_ref"),
        action.get("outcome_ref"),
    )
    return _compact_mapping(
        {
            "surface_kind": "paper_mission_terminal_owner_gate",
            "owner": "mas_authority_kernel",
            "gate_kind": "typed_blocker",
            "blocked_reason": _first_text(
                outcome.get("blocker_id"),
                outcome.get("reason"),
                "typed_blocker",
            ),
            "typed_blocker_ref": typed_blocker_ref,
            "closeout_ref": _first_text(decision.get("decision_ref"), action.get("outcome_ref")),
            "stage_attempt_id": _first_text(
                outcome.get("stage_attempt_id"),
                decision.get("stage_attempt_id"),
            ),
            "work_unit_id": _first_text(
                outcome.get("work_unit_id"),
                decision.get("work_unit_id"),
                action.get("work_unit_id"),
            ),
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "authority_materialized": False,
            "legal_next_action": "route_to_owner_or_human_gate",
        }
    )


def _next_action_for_stage_closure_decision(
    *,
    stage_closure_decision: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    typed_blocker_resolution_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    decision = _mapping(stage_closure_decision)
    outcome = _mapping(decision.get("outcome"))
    resolution = _mapping(typed_blocker_resolution_readback)
    if resolution:
        action = _mapping(resolution.get("next_owner_action"))
        if action:
            source_ref = _first_text(resolution.get("source_ref"), resolution.get("decision_ref"))
            action_type = _first_text(
                action.get("action_type"),
                action.get("next_action"),
                _first_text_item(action.get("allowed_actions")),
            )
            return compile_next_action_envelope(
                stage_outcome={
                    "kind": "next_stage_transition",
                    "study_id": _first_text(decision.get("study_id"), action.get("study_id")),
                    "stage_id": _first_text(
                        decision.get("stage_id"),
                        "submission_milestone_candidate",
                    ),
                    "work_unit_id": action.get("work_unit_id"),
                    "work_unit_fingerprint": action.get("work_unit_fingerprint"),
                    "action_family": "paper.package.submission_minimal",
                    "next_action": action_type,
                    "decision_signature": action.get("work_unit_fingerprint"),
                    "required_input_refs": action.get("acceptance_refs"),
                },
                study_id=_first_text(decision.get("study_id"), action.get("study_id")),
                stage_id=_first_text(
                    decision.get("stage_id"),
                    "submission_milestone_candidate",
                ),
                outcome_ref=source_ref,
                owner_route={
                    "next_owner": action.get("next_owner") or "mas_authority_kernel",
                    "allowed_actions": action.get("allowed_actions"),
                    "action_type": action_type,
                    "idempotency_key": action.get("work_unit_fingerprint"),
                    "action_family": "paper.package.submission_minimal",
                    "paper_facing_delta": action.get("paper_facing_delta"),
                    "accepted_answer_shape": action.get("accepted_answer_shape"),
                    "route_back": action.get("route_back"),
                    "verification": action.get("verification"),
                    "executable_owner_route": action.get("executable_owner_route"),
                },
                authority_boundary={
                    "projection_only": True,
                    "can_claim_stage_complete": False,
                    "can_claim_submission_ready": False,
                    "can_claim_publication_ready": False,
                },
                diagnostic_refs=[
                    {"role": "typed_blocker_resolution", "ref": source_ref}
                ]
                if source_ref is not None
                else [],
            )
    if outcome.get("kind") == "typed_blocker":
        transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
        return compile_next_action_envelope(
            stage_outcome={
                **outcome,
                "study_id": _first_text(decision.get("study_id"), transaction.get("study_id")),
                "stage_id": _first_text(decision.get("stage_id"), transaction.get("stage_id")),
                "work_unit_id": "paper_mission_typed_blocker_resolution",
                "work_unit_fingerprint": _first_text(
                    outcome.get("typed_blocker_evidence_ref"),
                    decision.get("decision_signature"),
                ),
                "stage_closure_decision_ref": decision.get("decision_ref"),
                "action_family": "blocked.typed",
            },
            study_id=_first_text(decision.get("study_id"), transaction.get("study_id")),
            stage_id=_first_text(decision.get("stage_id"), transaction.get("stage_id")),
            outcome_ref=decision.get("decision_ref"),
            owner_route={
                "next_owner": "mas_authority_kernel",
                "allowed_actions": ["materialize_typed_blocker_or_route_redesign"],
                "action_family": "blocked.typed",
            },
            authority_boundary={
                "projection_only": True,
                "can_claim_stage_complete": False,
                "can_claim_submission_ready": False,
                "can_claim_publication_ready": False,
            },
            diagnostic_refs=_stage_closure_next_action_diagnostic_refs(
                stage_closure_decision=decision,
                transaction_readback=transaction_readback,
            ),
        )
    if outcome.get("kind") != "owner_receipt":
        return None
    if outcome.get("package_kind") != "submission_ready_package":
        return None
    if outcome.get("can_submit") is not True:
        return None
    if _text_list(outcome.get("known_blockers")) or _text_list(
        decision.get("known_blockers")
    ):
        return None
    transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
    return compile_next_action_envelope(
        stage_outcome={
            **outcome,
            "study_id": decision.get("study_id"),
            "stage_id": decision.get("stage_id"),
            "work_unit_id": decision.get("work_unit_id"),
            "work_unit_fingerprint": decision.get("work_unit_fingerprint"),
            "stage_closure_decision_ref": decision.get("decision_ref"),
            "decision_signature": decision.get("decision_signature"),
            "required_input_refs": [
                ref
                for ref in _text_list(
                    _mapping(decision.get("semantic_delta")).get("delivery_delta_refs")
                )
            ],
        },
        study_id=_first_text(decision.get("study_id"), transaction.get("study_id")),
        stage_id=_first_text(decision.get("stage_id"), transaction.get("stage_id")),
        outcome_ref=decision.get("decision_ref"),
        authority_boundary={
            "projection_only": True,
            "can_claim_stage_complete": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
        },
        diagnostic_refs=_stage_closure_next_action_diagnostic_refs(
            stage_closure_decision=decision,
            transaction_readback=transaction_readback,
        ),
    )


def _stage_closure_next_action_diagnostic_refs(
    *,
    stage_closure_decision: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for role, ref in (
        ("stage_closure_decision", stage_closure_decision.get("decision_ref")),
        (
            "paper_mission_transaction",
            _mapping(transaction_readback.get("paper_mission_transaction")).get(
                "transaction_id"
            ),
        ),
    ):
        text = _optional_text(ref)
        if text is not None:
            refs.append({"role": role, "ref": text})
    for ref in _text_list(
        _mapping(stage_closure_decision.get("semantic_delta")).get("delivery_delta_refs")
    ):
        refs.append({"role": "delivery_delta_ref", "ref": ref})
    return refs


def _paper_mission_current_package_projection(
    projection_fields: Mapping[str, Any],
) -> dict[str, Any]:
    current = _mapping(projection_fields.get("current_package"))
    if current:
        return current
    return {
        "status": "missing",
        "package_kind": "current_package",
        "can_submit": False,
        "known_blockers": ["current_package_missing"],
    }


def _paper_mission_delivery_projection_fields(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_root: Path,
) -> dict[str, Any]:
    from med_autoscience.controllers.study_progress_parts.delivery_inspection import (
        read_delivery_inspection_projection,
    )

    delivery = read_delivery_inspection_projection(
        profile=profile,
        profile_ref=profile_ref,
        study_root=study_root,
    )
    current_package = _mapping(_mapping(delivery).get("current_package"))
    return {"current_package": current_package} if current_package else {}


def _paper_mission_materialized_projection_fields(
    *,
    transaction_readback: Mapping[str, Any],
) -> dict[str, Any]:
    transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
    decision = _mapping(transaction_readback.get("stage_terminal_decision"))
    owner_answer = _mapping(
        transaction_readback.get("terminal_owner_gate_owner_answer_readback")
    )
    next_decision = _mapping(transaction_readback.get("next_owner_or_human_decision"))
    artifact_delta_refs = _mapping_list(transaction.get("artifact_delta_refs"))
    return _compact_non_null_mapping(
        {
            "artifact_delta_refs": artifact_delta_refs or None,
            "owner_answer_shape": _first_text(
                owner_answer.get("owner_answer_shape"),
                decision.get("owner_answer_shape"),
                decision.get("decision_kind"),
            ),
            "paper_facing_delta_ref": _first_text(
                owner_answer.get("paper_facing_delta_ref"),
                decision.get("paper_facing_delta_ref"),
            ),
            "semantic_progress_signature": owner_answer.get(
                "semantic_progress_signature"
            ),
            "route_back_budget": owner_answer.get("route_back_budget"),
            "mission_executor_fallback_action": owner_answer.get(
                "mission_executor_fallback_action"
            ),
            "carry_forward_risk_receipt_ref": owner_answer.get(
                "carry_forward_risk_receipt_ref"
            ),
            "next_owner": _first_text(
                next_decision.get("next_owner"),
                decision.get("next_owner"),
            ),
        }
    )


def _latest_materialized_mission_path(
    *,
    workspace_root: Path,
    study_id: str,
) -> Path | None:
    root = (
        workspace_root.expanduser().resolve()
        / PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH
    )
    if not root.exists():
        return None
    candidates = sorted(
        (
            path
            for path in root.glob("*/*/paper_mission_run.json")
            if path.is_file()
            and _materialized_mission_path_matches(
                path,
                requested_study_id=study_id,
                load_json_object=_load_json_object,
            )
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _latest_candidate_package_manifest_path(
    *,
    workspace_root: Path,
    study_id: str,
) -> Path | None:
    root = (
        workspace_root.expanduser().resolve()
        / PAPER_MISSION_CANDIDATE_PACKAGE_RELPATH
    )
    if not root.exists():
        return None
    candidates = sorted(
        (
            path
            for path in root.glob("*/**/package_manifest.json")
            if path.is_file()
            and _materialized_mission_path_matches(
                path,
                requested_study_id=study_id,
                load_json_object=_load_json_object,
            )
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _resolve_consume_candidate_ref(
    *,
    profile: Any,
    study_id: str,
    candidate: str | Path | None,
) -> str | None:
    explicit = _optional_text(candidate)
    if explicit is not None:
        return explicit
    candidate_package = _latest_candidate_package_manifest_path(
        workspace_root=Path(profile.workspace_root),
        study_id=study_id,
    )
    return str(candidate_package) if candidate_package is not None else None


def _build_materialized_candidate_package_readback(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    output_root: str | Path | None,
    source: str,
    source_readback_override: Mapping[str, Any] | None = None,
    paper_facing_delta_ref: str | Path | None = None,
) -> dict[str, Any]:
    if output_root is None:
        raise ValueError("--output-root is required for package-candidate")
    readback = (
        _paper_mission_followthrough_source_readback(
            readback=source_readback_override,
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            source=source,
        )
        if source_readback_override is not None
        else None
    )
    if readback is None:
        readback = _build_materialized_mission_readback_if_available(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            paper_mission_command="package-candidate",
            dry_run=False,
            source=source,
        )
        if readback is None:
            raise ValueError(
                "package-candidate requires a materialized PaperMissionRun under "
                "ops/medautoscience/paper_mission_one_shot_migration"
            )
    mission = dict(readback["paper_mission_run"])
    candidate_manifest = (
        dict(readback["candidate_manifest"])
        if isinstance(readback.get("candidate_manifest"), Mapping)
        else paper_mission_canary_candidate_manifest(mission)
    )
    candidate_artifact_delta = paper_mission_candidate_artifact_delta(mission)
    owner_decision_packet = paper_mission_owner_decision_packet(mission)
    summary = _foreground_owner_decision_summary(
        readback=readback,
        candidate_manifest=candidate_manifest,
        candidate_artifact_delta=candidate_artifact_delta,
        owner_decision_packet=owner_decision_packet,
    )
    mission_executor_handoff = _mission_executor_handoff(
        readback=readback,
        foreground_owner_decision_summary=summary,
    )
    paper_facing_candidate_delta = materialized_paper_facing_candidate_delta(
        readback=readback,
        candidate_artifact_delta=candidate_artifact_delta,
        owner_decision_packet=owner_decision_packet,
        mission_executor_handoff=mission_executor_handoff,
        forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )
    owner_blocker_packet = paper_mission_owner_blocker_packet(
        readback=readback,
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=mission_executor_handoff,
        forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )
    owner_consumption_request = paper_mission_owner_consumption_request(
        readback=readback,
        candidate_manifest=candidate_manifest,
        owner_decision_packet=owner_decision_packet,
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=mission_executor_handoff,
        paper_facing_candidate_delta=paper_facing_candidate_delta,
        owner_blocker_packet=owner_blocker_packet,
        candidate_refs={},
        forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )
    output_manifest = _write_materialized_candidate_package_outputs(
        output_root=Path(output_root),
        study_id=str(readback["study_id"]),
        paper_mission_readback=readback,
        candidate_manifest=candidate_manifest,
        candidate_artifact_delta=candidate_artifact_delta,
        owner_decision_packet=owner_decision_packet,
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=mission_executor_handoff,
        paper_facing_candidate_delta=paper_facing_candidate_delta,
        owner_consumption_request=owner_consumption_request,
        owner_blocker_packet=owner_blocker_packet,
        adopted_external_paper_delta_ref=(
            str(Path(paper_facing_delta_ref).expanduser().resolve())
            if paper_facing_delta_ref is not None
            else None
        ),
    )
    return {
        "surface_kind": "paper_mission_candidate_package_write_readback",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_CONTRACT_REF,
        "contract_version": PAPER_MISSION_CONTRACT_VERSION,
        "paper_mission_command": "package-candidate",
        "action_intent": _action_intent("package-candidate"),
        "source": source,
        "dry_run": False,
        "profile": readback["profile"],
        "requested_study_id": readback["requested_study_id"],
        "study_id": readback["study_id"],
        "study_root": readback["study_root"],
        "study_root_exists": readback["study_root_exists"],
        "mission_id": readback["mission_id"],
        "objective": readback["objective"],
        "materialized_mission_ref": readback["materialized_mission_ref"],
        "stage_terminal_decision": readback["stage_terminal_decision"],
        "opl_route_command": readback["opl_route_command"],
        "opl_runtime_readback_status": readback["opl_runtime_readback_status"],
        "terminal_owner_gate": readback.get("terminal_owner_gate"),
        "terminal_owner_gate_authority_readback": readback.get(
            "terminal_owner_gate_authority_readback"
        ),
        "next_owner_or_human_decision": readback["next_owner_or_human_decision"],
        "transaction_state": readback["transaction_state"],
        "consume_candidate_status": readback["consume_candidate_status"],
        "candidate_manifest": candidate_manifest,
        "mission_candidate_artifact_delta": candidate_artifact_delta,
        "owner_decision_packet": owner_decision_packet,
        "foreground_owner_decision_summary": summary,
        "mission_executor_handoff": mission_executor_handoff,
        "paper_facing_candidate_delta": paper_facing_candidate_delta,
        "owner_consumption_request": owner_consumption_request,
        "owner_blocker_packet": owner_blocker_packet,
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_yang_ops_candidate_package": _is_yang_ops_candidate_package_root(
                output_root
            ),
            "writes_paper_body": False,
            "writes_candidate_workspace": True,
            "dry_run_only": False,
            "forbidden_authority_writes": list(
                CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES
            ),
        },
        "forbidden_authority_writes": list(CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "output_manifest": output_manifest,
    }


def _paper_mission_followthrough_source_readback(
    *,
    readback: Mapping[str, Any] | None,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    source: str,
) -> dict[str, Any] | None:
    return _paper_mission_followthrough_source_readback_impl(
        readback=readback,
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        source=source,
        contract_ref=PAPER_MISSION_CONTRACT_REF,
        contract_version=PAPER_MISSION_CONTRACT_VERSION,
        candidate_package_forbidden_authority_writes=(
            CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES
        ),
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
        action_intent=_action_intent,
        paper_mission_transaction_readback=_paper_mission_transaction_readback,
        transaction_readback_output_fields=_transaction_readback_output_fields,
    )


def _followthrough_transaction_for_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    return _followthrough_transaction_for_readback_impl(readback)


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


def _write_materialized_candidate_package_outputs(
    *,
    output_root: Path,
    study_id: str,
    paper_mission_readback: dict[str, Any],
    candidate_manifest: dict[str, Any],
    candidate_artifact_delta: dict[str, Any],
    owner_decision_packet: dict[str, Any],
    foreground_owner_decision_summary: dict[str, Any],
    mission_executor_handoff: dict[str, Any],
    paper_facing_candidate_delta: dict[str, Any],
    owner_consumption_request: dict[str, Any],
    owner_blocker_packet: dict[str, Any],
    adopted_external_paper_delta_ref: str | None = None,
) -> dict[str, Any]:
    return _candidate_write_materialized_candidate_package_outputs(
        output_root=output_root,
        study_id=study_id,
        paper_mission_readback=paper_mission_readback,
        candidate_manifest=candidate_manifest,
        candidate_artifact_delta=candidate_artifact_delta,
        owner_decision_packet=owner_decision_packet,
        foreground_owner_decision_summary=foreground_owner_decision_summary,
        mission_executor_handoff=mission_executor_handoff,
        paper_facing_candidate_delta=paper_facing_candidate_delta,
        owner_consumption_request=owner_consumption_request,
        owner_blocker_packet=owner_blocker_packet,
        candidate_package_forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
        adopted_external_paper_delta_ref=adopted_external_paper_delta_ref,
    )


def _mission_executor_handoff(
    *,
    readback: Mapping[str, Any],
    foreground_owner_decision_summary: Mapping[str, Any],
) -> dict[str, Any]:
    return _candidate_mission_executor_handoff(
        readback=readback,
        foreground_owner_decision_summary=foreground_owner_decision_summary,
        candidate_package_forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
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


def _foreground_owner_decision_summary(
    *,
    readback: Mapping[str, Any],
    candidate_manifest: Mapping[str, Any],
    candidate_artifact_delta: Mapping[str, Any],
    owner_decision_packet: Mapping[str, Any],
) -> dict[str, Any]:
    return _candidate_foreground_owner_decision_summary(
        readback=readback,
        candidate_manifest=candidate_manifest,
        candidate_artifact_delta=candidate_artifact_delta,
        owner_decision_packet=owner_decision_packet,
        candidate_package_forbidden_authority_writes=CANDIDATE_PACKAGE_FORBIDDEN_AUTHORITY_WRITES,
        forbidden_authority_claims=FORBIDDEN_AUTHORITY_CLAIMS,
    )


def _no_write_output_manifest() -> dict[str, Any]:
    return {
        "mode": "readback_only",
        "written_files": [],
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_yang_ops_candidate_package": False,
        "writes_yang_ops_consumption_ledger": False,
    }


def _action_intent(paper_mission_command: str) -> str:
    if paper_mission_command in {"start", "resume"}:
        return PAPER_MISSION_START_OR_RESUME_TASK_KIND
    if paper_mission_command == "consume-candidate":
        return "paper_mission/consume_candidate"
    if paper_mission_command == "package-candidate":
        return "paper_mission/package_candidate"
    if paper_mission_command == "drive":
        return "paper_mission/drive"
    if paper_mission_command == "terminalize-stage":
        return "paper_mission/terminalize_stage"
    if paper_mission_command == "typed-blocker-resolution":
        return "paper_mission/typed_blocker_resolution"
    return "paper_mission/inspect"


def _objective_for_command(*, paper_mission_command: str, objective: str | None) -> str:
    explicit = _optional_text(objective)
    if explicit:
        return explicit
    defaults = {
        "inspect": "inspect current paper mission entry",
        "start": "start or resume next paper-facing mission objective",
        "resume": "resume current paper-facing mission objective",
        "consume-candidate": "consume candidate paper mission output",
        "drive": "drive current paper mission to terminal decision and OPL route handoff",
    }
    return defaults.get(paper_mission_command, "paper mission no-write plan")


def _mission_id(
    *,
    mission_id: str | None,
    study_id: str,
    objective: str,
    paper_mission_command: str,
) -> str:
    explicit = _optional_text(mission_id)
    if explicit:
        return explicit
    return f"paper-mission::{study_id}::{_slug(objective)}::{paper_mission_command}-dry-run"


def _paper_mission_transaction_readback(**kwargs) -> dict[str, Any]:
    return _paper_mission_transaction_readback_impl(
        **kwargs,
        attach_runtime_readback=attach_opl_runtime_carrier_readback,
        attach_next_action=attach_paper_mission_next_action,
    )


def _submission_authority_owner_gate_readback(
    *,
    study_root: Path,
    study_id: str,
    next_action: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not next_action:
        return None
    return submission_authority_owner_gate_readback(
        {
            "study_id": study_id,
            "study_intervention_events": read_intervention_events(study_root=study_root),
        },
        next_action=next_action,
    )


def _mutation_policy(*, paper_mission_command: str) -> dict[str, Any]:
    return {
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang": False,
        "writes_paper_body": False,
        "writes_candidate_workspace": False,
        "dry_run_only": paper_mission_command != "inspect",
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }


def _validate_with_contract_if_available(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        from med_autoscience.paper_mission_run import PaperMissionRun
    except ModuleNotFoundError:
        return {
            "status": "pending_contract_module_not_available",
            "required_commit": PAPER_MISSION_CONTRACT_COMMIT,
            "validator": "med_autoscience.paper_mission_run.PaperMissionRun",
        }
    try:
        PaperMissionRun.from_payload(payload)
    except Exception as exc:  # pragma: no cover - exact error type lives in contract lane.
        return {
            "status": "failed",
            "validator": "med_autoscience.paper_mission_run.PaperMissionRun",
            "error": str(exc),
        }
    return {
        "status": "validated",
        "validator": "med_autoscience.paper_mission_run.PaperMissionRun",
    }


__all__ = [
    "PAPER_MISSION_START_OR_RESUME_TASK_KIND",
    "build_paper_mission_readback",
    "handle_paper_mission_command",
    "paper_mission_domain_handler_dispatch_receipt",
    "register_paper_mission_parsers",
]
