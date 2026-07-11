from __future__ import annotations

import importlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

from med_autoscience.paper_mission_authority import consume_paper_mission_candidate
from med_autoscience.paper_mission_consumption_readback import (
    latest_paper_mission_consumption_transaction_readback,
)
from med_autoscience.paper_mission_consumption_ledger import (
    write_paper_mission_consumption_ledger_outputs,
)
from med_autoscience.paper_mission_terminal_owner_gate import (
    terminal_owner_gate_authority_readback as _terminal_owner_gate_authority_readback,
    terminal_owner_gate_from_carrier_readback as _terminal_owner_gate_from_carrier_readback,
)
from med_autoscience.paper_mission_output_roots import (
    _assert_safe_consumption_ledger_output_root,
    _is_yang_ops_consumption_ledger_root,
)
from .receipt_owner_consumption import (
    build_receipt_owner_consumption_readback as _build_receipt_owner_consumption_readback,
    latest_receipt_owner_consumption_readback as _latest_receipt_owner_consumption_readback,
    receipt_owner_consumption_apply_mode as _receipt_owner_consumption_apply_mode,
)
from .candidate_package_readback import (
    build_materialized_candidate_package_readback as _build_materialized_candidate_package_readback,
    consume_candidate_missing_readback as _consume_candidate_missing_readback,
)
from .command_metadata import (
    FORBIDDEN_AUTHORITY_WRITES,
    PAPER_MISSION_CONTRACT_REF,
    PAPER_MISSION_CONTRACT_VERSION,
    DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
    action_intent as _action_intent,
    mission_id as _mission_id,
    mutation_policy as _mutation_policy,
    no_write_output_manifest as _no_write_output_manifest,
    objective_for_command as _objective_for_command,
    validate_with_contract_if_available as _validate_with_contract_if_available,
)
from .domain_handler_dispatch import (
    paper_mission_domain_handler_dispatch_receipt as _paper_mission_domain_handler_dispatch_receipt,
)
from .drive_readback import (
    build_paper_mission_drive_readback as _build_paper_mission_drive_readback,
)
from .materialized_mission_readback import (
    build_materialized_mission_readback_if_available as _build_materialized_mission_readback_if_available,
    _domain_transition_direct_next_action_runtime_readback as _build_domain_transition_direct_next_action_runtime_readback,
    suppress_consumed_route_checkpoint_transaction_next_action as _suppress_consumed_route_checkpoint_transaction_next_action,
)
from .materialized_readback_context import (
    dispatch_execution_policy as _dispatch_execution_policy,
    paper_facing_action_fields as _paper_facing_action_fields,
    recommended_domain_invocation as _recommended_domain_invocation,
)
from .projection_fields import (
    resolve_consume_candidate_ref as _resolve_consume_candidate_ref,
)
from .one_shot_migration import (
    build_one_shot_migration_cli_readback as _build_one_shot_migration_cli_readback_impl,
)
from .opl_runtime_submission import (
    semantic_progress_guard as _paper_mission_semantic_progress_guard,
)
from .stage_closure_next_action import (
    merge_stage_closure_typed_blocker_gate_fields as _merge_stage_closure_typed_blocker_gate_fields,
    next_action_for_stage_closure_decision as _next_action_for_stage_closure_decision,
)
from .submission_gate_readback import (
    apply_submission_authority_owner_gate_readback as _apply_submission_authority_owner_gate_readback,
)
from .common import (
    _load_optional_json_object,
    _mapping,
    _optional_text,
)
from .stage_closure_terminalizer import (
    stage_closure_decision_requires_reterminalize as _stage_closure_decision_requires_reterminalize,
    terminalize_stage_closure_from_readback as _terminalize_stage_closure_from_readback,
)
from . import (
    stage_closure_terminalizer_readback as _stage_closure_terminalizer_readback,
)
from .typed_blocker_resolution import (
    build_typed_blocker_resolution_readback as _build_typed_blocker_resolution_readback,
    latest_typed_blocker_resolution_readback,
    typed_blocker_resolution_apply_mode as _typed_blocker_resolution_apply_mode,
)
from .transaction_readback import (
    FORBIDDEN_AUTHORITY_CLAIMS as _TRANSACTION_FORBIDDEN_AUTHORITY_CLAIMS,
    _candidate_manifest_transaction,
    _candidate_mission_id_for_readback,
    _consume_candidate_status_for_transaction_readback,
    _durable_mission_stop_guard,
    _paper_mission_run_candidate,
    _paper_mission_transaction_readback,
    _transaction_readback_output_fields,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_projection,
)
from med_autoscience.controllers import study_domain_transition_table
from med_autoscience.controllers.study_progress.canonical_next_action_selection import (
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


FORBIDDEN_AUTHORITY_CLAIMS = _TRANSACTION_FORBIDDEN_AUTHORITY_CLAIMS


def _consumption_ledger_readback_module() -> Any:
    return importlib.import_module(
        "med_autoscience.paper_mission_domain.consumption_ledger_readback"
    )


def _sync_consumption_ledger_readback_deps() -> Any:
    module = _consumption_ledger_readback_module()
    module._latest_receipt_owner_consumption_readback = (
        _latest_receipt_owner_consumption_readback
    )
    module._study_progress_paper_mission_overlay = (
        _study_progress_paper_mission_overlay
    )
    module._consumption_ledger_route_back_projection = (
        _consumption_ledger_route_back_projection
    )
    module._paper_mission_semantic_progress_readback = (
        _paper_mission_semantic_progress_readback
    )
    return module


def _consumption_ledger_inspect_readback(**kwargs: Any) -> dict[str, Any]:
    module = _sync_consumption_ledger_readback_deps()
    return module._consumption_ledger_inspect_readback(**kwargs)


def _study_progress_paper_mission_overlay(**kwargs: Any) -> dict[str, Any]:
    return _consumption_ledger_readback_module()._study_progress_paper_mission_overlay(
        **kwargs
    )


def _merge_study_progress_overlay(
    readback: Mapping[str, Any],
    overlay: Mapping[str, Any],
) -> dict[str, Any]:
    return _consumption_ledger_readback_module()._merge_study_progress_overlay(
        readback, overlay
    )


def _consumption_ledger_route_back_projection(**kwargs: Any) -> dict[str, Any] | None:
    return _consumption_ledger_readback_module()._consumption_ledger_route_back_projection(
        **kwargs
    )


def _transaction_readback_has_route_back_owner_answer(
    transaction_readback: Mapping[str, Any],
) -> bool:
    return (
        _consumption_ledger_readback_module()._transaction_readback_has_route_back_owner_answer(
            transaction_readback
        )
    )


def _receipt_owner_consumption_status(receipt_owner_consumption: Mapping[str, Any]) -> str:
    return _consumption_ledger_readback_module()._receipt_owner_consumption_status(
        receipt_owner_consumption
    )


def _consumption_ledger_current_route_next_action(**kwargs: Any) -> dict[str, Any] | None:
    return _consumption_ledger_readback_module()._consumption_ledger_current_route_next_action(
        **kwargs
    )


def _consumption_ledger_has_current_route_handoff(
    consumption_readback: Mapping[str, Any],
) -> bool:
    return _consumption_ledger_readback_module()._consumption_ledger_has_current_route_handoff(
        consumption_readback
    )


def _paper_mission_consume_non_advancing_fields(**kwargs: Any) -> dict[str, Any]:
    module = _sync_consumption_ledger_readback_deps()
    return module._paper_mission_consume_non_advancing_fields(**kwargs)


def _paper_mission_semantic_progress_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    return _consumption_ledger_readback_module()._paper_mission_semantic_progress_readback(
        readback
    )

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
    receipt_owner_consumption = _latest_receipt_owner_consumption_readback(
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
        receipt_owner_consumption_readback=receipt_owner_consumption,
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
    transaction_output_fields = _suppress_consumed_route_checkpoint_transaction_next_action(
        transaction_output_fields=transaction_output_fields,
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
            "default_action_intent": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
            "domain_handler_task_kind": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
            "domain_handler_dispatch_mode": (
                "governed_consume_record"
                if consume_output_manifest is not None
                else "dry_run_no_write"
            ),
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
        start_or_resume_task_kind=DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
        forbidden_authority_writes=FORBIDDEN_AUTHORITY_WRITES,
        dispatch_execution_policy=_dispatch_execution_policy,
        recommended_domain_invocation=_recommended_domain_invocation,
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
    "DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND",
    "build_paper_mission_readback",
    "paper_mission_domain_handler_dispatch_receipt",
]
