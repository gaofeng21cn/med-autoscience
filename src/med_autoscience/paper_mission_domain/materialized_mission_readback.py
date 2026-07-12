from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_domain.command_metadata import (
    PAPER_MISSION_CONTRACT_REF,
    PAPER_MISSION_CONTRACT_VERSION,
    DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
    action_intent as _action_intent,
    validate_with_contract_if_available as _validate_with_contract_if_available,
)
from med_autoscience.paper_mission_domain.common import (
    _first_text,
    _load_json_object,
    _mapping,
    _optional_text,
)
from med_autoscience.paper_mission_domain.domain_transition_runtime_readback import (
    _domain_transition_direct_next_action_runtime_readback,
    _override_next_action_from_direct_terminal_closeout as _shared_override_next_action_from_direct_terminal_closeout,
    _typed_blocker_resolution_should_own_next_action,
)
from med_autoscience.paper_mission_domain.materialized_readback_context import (
    consume_candidate_status as _consume_candidate_status,
    materialized_ai_route_context as _materialized_ai_route_context,
    materialized_stage_terminal_decision as _materialized_stage_terminal_decision,
    materialized_study_id as _materialized_study_id,
    materialized_study_root as _materialized_study_root,
    normalize_materialized_mission_for_cli_readback as _normalize_materialized_mission_for_cli_readback,
    paper_facing_action_fields as _paper_facing_action_fields,
)
from med_autoscience.paper_mission_domain.one_shot_migration import (
    ONE_SHOT_MIGRATION_FORBIDDEN_AUTHORITY_WRITES,
)
from med_autoscience.paper_mission_domain.projection_fields import (
    latest_materialized_mission_path as _latest_materialized_mission_path,
    paper_mission_delivery_projection_fields as _paper_mission_delivery_projection_fields,
    paper_mission_inspect_projection_fields as _paper_mission_inspect_projection_fields,
    paper_mission_materialized_projection_fields as _paper_mission_materialized_projection_fields,
)
from med_autoscience.paper_mission_domain.readback_next_action_precedence import (
    _stage_closure_next_action_should_own_next_action,
    _stage_closure_owner_receipt_suppresses_transaction_next_action,
    _stage_closure_suppresses_domain_transition_next_action,
)
from med_autoscience.paper_mission_domain.stage_closure_next_action import (
    merge_stage_closure_typed_blocker_gate_fields as _merge_stage_closure_typed_blocker_gate_fields,
    next_action_for_stage_closure_decision as _next_action_for_stage_closure_decision,
)
from med_autoscience.paper_mission_domain.stage_closure_terminalizer import (
    stage_closure_decision_requires_reterminalize as _stage_closure_decision_requires_reterminalize,
    terminalize_stage_closure_from_readback as _terminalize_stage_closure_from_readback,
)
from med_autoscience.paper_mission_domain.transaction_readback import (
    FORBIDDEN_AUTHORITY_CLAIMS,
    PAPER_AUDIT_PACK_FAMILIES,
    _durable_mission_stop_guard,
    _mission_state_for_materialized_readback,
    _paper_mission_transaction_readback,
    _submission_authority_owner_gate_readback,
    _transaction_readback_output_fields,
)
from med_autoscience.paper_mission_domain.typed_blocker_resolution import (
    latest_typed_blocker_resolution_readback,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_missing,
    stage_closure_decision_projection,
)


def _override_next_action_from_direct_terminal_closeout(**kwargs: Any) -> tuple[Mapping[str, Any], Mapping[str, Any] | None, str | None]:
    return _shared_override_next_action_from_direct_terminal_closeout(
        **kwargs,
        terminalize_stage_closure_from_readback=_terminalize_stage_closure_from_readback,
        next_action_for_stage_closure_decision=_next_action_for_stage_closure_decision,
    )


def build_materialized_mission_readback_if_available(
    *,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    paper_mission_command: str,
    dry_run: bool,
    source: str,
    opl_runtime_payload: Mapping[str, Any] | None = None,
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
    transaction_readback = _paper_mission_transaction_readback(
        mission_id=str(mission["mission_id"]),
        study_id=resolved_study_id,
        objective=str(mission["objective"]),
        paper_mission_command=paper_mission_command,
        study_root=resolved_study_root,
        mission=mission,
        opl_runtime_payload=opl_runtime_payload,
    )
    mission = {
        **mission,
        "mission_state": _mission_state_for_materialized_readback(
            mission=mission,
            transaction_readback=transaction_readback,
        ),
        "paper_mission_transaction": transaction_readback[
            "paper_mission_transaction"
        ],
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
        or _consume_candidate_status(mission, default_readback)
    )
    stage_closure_readback = _mapping(
        transaction_readback.get("stage_closure_decision")
    ) or None
    typed_blocker_resolution_readback = latest_typed_blocker_resolution_readback(
        workspace_root=Path(profile.workspace_root),
        study_id=resolved_study_id,
    )
    effective_consume_candidate_status = consume_candidate_status
    stage_closure_decision = stage_closure_decision_projection(
        readback={
            **transaction_readback,
            **(
                {"stage_closure_decision": stage_closure_readback}
                if stage_closure_readback is not None
                else {}
            ),
            "consume_candidate_status": effective_consume_candidate_status,
            "current_package": projection_fields.get("current_package"),
        },
        handoff=_mapping(transaction_readback.get("opl_route_handoff")),
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
                "current_package": projection_fields.get("current_package"),
                **(
                    {"stage_closure_decision": stage_closure_readback}
                    if stage_closure_readback is not None
                    else {}
                ),
            }
        )
    domain_transition = {
        "surface_kind": "mas_ai_route_context",
        "semantic_route_owner": "codex_cli",
        "program_recommendation_can_execute_or_block_route": False,
        "readable_artifact_allows_any_declared_stage": True,
    }
    domain_transition_next_action = None
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
    if _stage_closure_owner_receipt_suppresses_transaction_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action_override=next_action_override,
    ):
        transaction_output_fields.pop("next_action", None)
        transaction_output_fields.pop("canonical_next_action_source", None)
    transaction_output_fields = (
        suppress_consumed_route_checkpoint_transaction_next_action(
            transaction_output_fields=transaction_output_fields,
        )
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
            _domain_transition_direct_next_action_runtime_readback(
                profile=profile,
                study_id=resolved_study_id,
                study_root=resolved_study_root,
                inspect_readback={
                    **mission,
                    **transaction_output_fields,
                },
                next_action=next_action_override,
                canonical_next_action_source=canonical_next_action_source,
                opl_runtime_payload=opl_runtime_payload,
            )
        )
        if direct_next_action_runtime:
            transaction_output_fields["domain_transition_direct_stage_attempt"] = (
                direct_next_action_runtime
            )
            transaction_output_fields["current_opl_stage_run_context"] = (
                direct_next_action_runtime["opl_stage_run_context"]
            )
            transaction_output_fields["current_opl_stage_attempt_readback"] = (
                direct_next_action_runtime["opl_stage_attempt_readback"]
            )
            transaction_output_fields["current_opl_stage_attempt_readback_status"] = (
                direct_next_action_runtime["opl_stage_attempt_readback_status"]
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
    if (
        "domain_transition_direct_stage_attempt" not in transaction_output_fields
        and stage_closure_suppresses_domain_transition
        and domain_transition_next_action
    ):
        direct_next_action_runtime = (
            _domain_transition_direct_next_action_runtime_readback(
                profile=profile,
                study_id=resolved_study_id,
                study_root=resolved_study_root,
                inspect_readback={
                    **mission,
                    **transaction_output_fields,
                },
                next_action=domain_transition_next_action,
                canonical_next_action_source="domain_transition.next_action",
                opl_runtime_payload=opl_runtime_payload,
            )
        )
        if direct_next_action_runtime:
            transaction_output_fields["domain_transition_direct_stage_attempt"] = (
                direct_next_action_runtime
            )
            transaction_output_fields["current_opl_stage_run_context"] = (
                direct_next_action_runtime["opl_stage_run_context"]
            )
            transaction_output_fields["current_opl_stage_attempt_readback"] = (
                direct_next_action_runtime["opl_stage_attempt_readback"]
            )
            transaction_output_fields["current_opl_stage_attempt_readback_status"] = (
                direct_next_action_runtime["opl_stage_attempt_readback_status"]
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
        "ai_route_context": transaction_readback["ai_route_context"],
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
            "default_action_intent": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
            "domain_handler_task_kind": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
            "domain_handler_dispatch_mode": "materialized_mission_readback_no_write",
            "old_owner_callable_dispatch_role": "diagnostic_or_migration_only",
            "opl_consumes": "paper_mission_transaction.ai_route_context",
            "mas_terminalizes": "paper_mission_transaction.stage_terminal_decision",
        },
        "cutover_proof": {
            "default_readback_surface": "PaperMissionRun",
            "terminalizer_surface": "PaperMissionTransaction",
            "materialized_paper_mission_run_loaded": True,
            "stage_terminal_decision_present": bool(
                _materialized_stage_terminal_decision(mission)
            ),
            "ai_route_context_present": bool(_materialized_ai_route_context(mission)),
            "legacy_blocker_controls_default_execution": False,
            "authority_materialized": False,
        },
    }
