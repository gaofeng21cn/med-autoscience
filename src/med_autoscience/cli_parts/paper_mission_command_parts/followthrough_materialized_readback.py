from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _first_mapping,
    _first_text,
    _first_text_item,
    _mapping,
    _mapping_list,
    _optional_text,
    _slug,
    _stable_sha256,
    _text_list,
)
from med_autoscience.cli_parts.paper_mission_command_parts.route_back_budget import (
    _canonicalize_followthrough_transaction_identity,
    _paper_mission_canonical_followthrough_identity,
)
from med_autoscience.paper_mission_candidate_materializer import (
    CONCRETE_NON_AUTHORITY_PAPER_DELTA_KIND,
)
from med_autoscience.paper_mission_transaction import (
    PaperMissionTransaction,
    build_paper_mission_transaction,
)


def paper_mission_followthrough_source_readback(
    *,
    readback: Mapping[str, Any] | None,
    profile: Any,
    profile_ref: str | Path,
    study_id: str,
    source: str,
    contract_ref: str,
    contract_version: str,
    candidate_package_forbidden_authority_writes: Sequence[str],
    forbidden_authority_claims: Sequence[str],
    action_intent: Callable[[str], str],
    paper_mission_transaction_readback: Callable[..., dict[str, Any]],
    transaction_readback_output_fields: Callable[[Mapping[str, Any]], dict[str, Any]],
) -> dict[str, Any] | None:
    source_readback = _mapping(readback)
    if not source_readback:
        return None
    transaction = followthrough_transaction_for_readback(source_readback)
    if not transaction:
        return None
    resolved_study_id = _first_text(transaction.get("study_id"), study_id) or study_id
    mission_id = (
        _first_text(transaction.get("mission_id"), source_readback.get("mission_id"))
        or f"paper-mission::{resolved_study_id}::followthrough"
    )
    objective = (
        _first_text(
            source_readback.get("objective"),
            _mapping(transaction.get("stage_terminal_decision")).get("next_work_unit"),
            _mapping(transaction.get("stage_terminal_decision")).get("repair_scope"),
        )
        or "PaperMission terminal route-back followthrough"
    )
    study_root = Path(getattr(profile, "studies_root")) / resolved_study_id
    transaction_readback = paper_mission_transaction_readback(
        mission_id=mission_id,
        study_id=resolved_study_id,
        objective=objective,
        paper_mission_command="package-candidate",
        study_root=study_root,
        mission=None,
        transaction_override=transaction,
        transaction_source_override="paper_mission_drive_followthrough",
        authority_consume_readback=None,
        enable_opl_live_probe=False,
    )
    candidate_manifest = _followthrough_candidate_manifest(
        readback=source_readback,
        transaction=transaction,
        mission_id=mission_id,
        study_id=resolved_study_id,
    )
    paper_mission_run = {
        "schema_version": contract_version,
        "mission_id": mission_id,
        "study_id": resolved_study_id,
        "objective": objective,
        "mission_state": "candidate_ready_for_consumption",
        "artifact_delta_ledger": [
            {
                "delta_id": "terminal_route_back_followthrough_candidate",
                "artifact_ref": (
                    "paper-mission-followthrough://"
                    f"{resolved_study_id}/{_slug(mission_id)}"
                ),
                "delta_kind": CONCRETE_NON_AUTHORITY_PAPER_DELTA_KIND,
                "status": "candidate",
            }
        ],
        "source_refs": _followthrough_source_refs(source_readback),
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": _mapping(transaction.get("stage_terminal_decision")),
        "opl_route_command": _mapping(transaction.get("opl_route_command")),
        "consume_result": {"status": "accepted"},
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
        },
    }
    return {
        "surface_kind": "paper_mission_followthrough_materialized_readback",
        "schema_version": 1,
        "contract_ref": contract_ref,
        "contract_version": contract_version,
        "paper_mission_command": "package-candidate",
        "action_intent": action_intent("package-candidate"),
        "source": source,
        "dry_run": False,
        "profile": {
            "profile_name": str(getattr(profile, "name", "")),
            "profile_ref": str(profile_ref),
        },
        "requested_study_id": study_id,
        "study_id": resolved_study_id,
        "study_root": str(study_root),
        "study_root_exists": study_root.exists(),
        "mission_id": mission_id,
        "objective": objective,
        "mission_state": "candidate_ready_for_consumption",
        "materialized_mission_ref": _optional_text(
            source_readback.get("materialized_mission_ref")
        )
        or "paper_mission_drive_followthrough",
        **transaction_readback_output_fields(transaction_readback),
        "candidate_manifest": candidate_manifest,
        "paper_mission_run": paper_mission_run,
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": _mapping(transaction.get("stage_terminal_decision")),
        "opl_route_command": _mapping(transaction.get("opl_route_command")),
        "consume_candidate_status": "accepted_candidate",
        "mutation_policy": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "writes_candidate_workspace": False,
            "dry_run_only": True,
            "forbidden_authority_writes": list(
                candidate_package_forbidden_authority_writes
            ),
        },
        "forbidden_authority_writes": list(
            candidate_package_forbidden_authority_writes
        ),
        "forbidden_authority_claims": list(forbidden_authority_claims),
    }


def followthrough_transaction_for_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    typed_blocker_followthrough = _typed_blocker_resolution_followthrough_transaction(
        readback
    )
    if typed_blocker_followthrough:
        return typed_blocker_followthrough
    owner_answer = _mapping(readback.get("terminal_owner_gate_owner_answer_readback"))
    transaction = _first_mapping(
        _canonicalize_followthrough_transaction_identity(
            _mapping(readback.get("stage_route_submission_source_transaction"))
        ),
        _canonicalize_followthrough_transaction_identity(
            _mapping(owner_answer.get("paper_mission_transaction"))
        ),
        _canonicalize_followthrough_transaction_identity(
            _mapping(readback.get("paper_mission_transaction"))
        ),
    )
    decision = _mapping(transaction.get("stage_terminal_decision"))
    decision_kind = _optional_text(decision.get("decision_kind"))
    terminal_closeout_observed = _optional_text(
        readback.get("opl_runtime_readback_status")
    ) == "opl_runtime_terminal_readback_observed" or _optional_text(
        _mapping(readback.get("opl_runtime_carrier_readback")).get("carrier_status")
    ) == "opl_runtime_terminal_readback_observed"
    accepted_submission_candidate = _optional_text(
        readback.get("consume_candidate_status")
    ) == "accepted_submission_milestone_candidate"
    runtime_opl_route_ready = (
        _optional_text(_mapping(readback.get("next_action")).get("action_family"))
        == "runtime.opl_route"
    )
    canonical_next_action_route = _canonical_next_action_followthrough_route(readback)
    if decision_kind != "route_back" and not (
        decision_kind == "continue_same_stage" and terminal_closeout_observed
    ) and not (
        decision_kind == "continue_same_stage"
        and accepted_submission_candidate
        and (runtime_opl_route_ready or canonical_next_action_route)
    ):
        return {}
    study_id = _optional_text(transaction.get("study_id"))
    mission_id = _paper_mission_canonical_followthrough_identity(
        _optional_text(transaction.get("mission_id"))
    )
    if study_id is None or mission_id is None:
        return {}
    target_stage = _first_text(
        canonical_next_action_route.get("stage_id"),
        canonical_next_action_route.get("owner"),
    ) or (
        _first_text(
            decision.get("target_stage_id"),
            decision.get("route_target"),
            decision.get("next_stage_id"),
            transaction.get("stage_id"),
        )
        or "submission_milestone_candidate"
    )
    next_work_unit = _first_text(
        canonical_next_action_route.get("work_unit_id"),
        canonical_next_action_route.get("stage_id"),
    ) or (
        _first_text(
            decision.get("target_stage_id"),
            decision.get("route_target"),
            decision.get("next_work_unit"),
            decision.get("work_unit_id"),
            decision.get("repair_scope"),
            "continue paper-facing submission milestone work",
        )
        or "continue paper-facing submission milestone work"
    )
    next_owner = _first_text(canonical_next_action_route.get("owner"), "mission_executor")
    reason = (
        "MAS canonical next action supersedes the stale PaperMission followthrough "
        "route and requests the current owner work unit."
        if canonical_next_action_route
        else (
            "MAS mission executor consumed the terminal closeout/route-back as a "
            "fresh paper-facing candidate and is continuing the same PaperMission "
            "stage."
        )
    )
    terminal_decision = {
        "decision_kind": "continue_same_stage",
        "status": "accepted_submission_milestone_candidate",
        "reason": reason,
        "next_owner": next_owner,
        "next_work_unit": next_work_unit,
        "source_route_back_evidence_ref": _optional_text(
            decision.get("route_back_evidence_ref")
        ),
    }
    if canonical_next_action_route:
        terminal_decision.update(
            {
                "recommended_next_action": _optional_text(
                    canonical_next_action_route.get("action_type")
                )
                or "request_opl_stage_attempt",
                "work_unit_fingerprint": _optional_text(
                    canonical_next_action_route.get("work_unit_fingerprint")
                ),
                "source_next_action_ref": _optional_text(
                    canonical_next_action_route.get("outcome_ref")
                ),
            }
        )
    source_transaction_id = _optional_text(transaction.get("transaction_id")) or mission_id
    identity_suffix = _first_text(
        canonical_next_action_route.get("work_unit_fingerprint"),
        next_work_unit,
    )
    followthrough_basis = (
        "terminal-route-back-followthrough::"
        f"{_slug(mission_id)}::{_slug(source_transaction_id)}"
        f"::{_slug(identity_suffix)}"
    )
    stage_run_ref = (
        f"paper-mission-followthrough://{study_id}/"
        f"{_slug(target_stage)}/{_slug(next_work_unit)}"
    )
    return _paper_mission_followthrough_transaction_instance(
        build_paper_mission_transaction(
            mission_id=mission_id,
            study_id=study_id,
            stage_id=target_stage,
            stage_run_ref=stage_run_ref,
            terminal_decision=terminal_decision,
            artifact_delta_refs=_mapping_list(transaction.get("artifact_delta_refs")),
            paper_audit_pack_refs=_mapping(transaction.get("paper_audit_pack_refs")),
            idempotency_basis=followthrough_basis,
        ),
        instance_basis=followthrough_basis,
    )


def _canonical_next_action_followthrough_route(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    next_action = _mapping(readback.get("next_action"))
    if _optional_text(next_action.get("surface_kind")) != "mas_next_action_envelope":
        return {}
    if _optional_text(next_action.get("action_type")) != "request_opl_stage_attempt":
        return {}
    work_unit_id = _optional_text(next_action.get("work_unit_id"))
    owner = _first_text(next_action.get("owner"), next_action.get("next_owner"))
    stage_id = _first_text(next_action.get("stage_id"), owner)
    if not work_unit_id or not stage_id:
        return {}
    return {
        "owner": owner or stage_id,
        "stage_id": stage_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": _optional_text(
            next_action.get("work_unit_fingerprint")
        )
        or _optional_text(next_action.get("action_fingerprint")),
        "action_type": _optional_text(next_action.get("action_type")),
        "outcome_ref": _optional_text(next_action.get("outcome_ref"))
        or _optional_text(next_action.get("action_id")),
    }


def _typed_blocker_resolution_followthrough_transaction(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    resolution = _mapping(readback.get("typed_blocker_resolution_readback"))
    action = _mapping(resolution.get("next_owner_action")) or _mapping(
        _mapping(readback.get("next_action")).get("executable_owner_route")
    )
    next_action = _mapping(readback.get("next_action"))
    if not resolution or not action:
        return {}
    if _optional_text(next_action.get("action_family")) != "paper.package.submission_minimal":
        return {}
    transaction = _canonicalize_followthrough_transaction_identity(
        _mapping(readback.get("paper_mission_transaction"))
    )
    study_id = _first_text(
        resolution.get("study_id"),
        action.get("study_id"),
        transaction.get("study_id"),
        readback.get("study_id"),
    )
    if study_id is None:
        return {}
    mission_id = (
        _paper_mission_canonical_followthrough_identity(
            _optional_text(transaction.get("mission_id"))
        )
        or f"paper-mission::{study_id}::typed-blocker-resolution-followthrough"
    )
    work_unit_id = (
        _first_text(
            action.get("work_unit_id"),
            next_action.get("work_unit_id"),
            "submission_blocker_degraded_handoff_or_quality_repair",
        )
        or "submission_blocker_degraded_handoff_or_quality_repair"
    )
    action_type = (
        _first_text(
            action.get("action_type"),
            next_action.get("action_type"),
            _first_text_item(action.get("allowed_actions")),
            "classify_quality_blockers_or_materialize_degraded_handoff_gate",
        )
        or "classify_quality_blockers_or_materialize_degraded_handoff_gate"
    )
    terminal_decision = {
        "decision_kind": "continue_same_stage",
        "status": "typed_blocker_resolution_candidate_ready",
        "reason": (
            "MAS typed-blocker resolution produced a quality-repair handoff "
            "candidate for continued paper-facing package materialization."
        ),
        "next_owner": _first_text(action.get("next_owner"), "mas_authority_kernel"),
        "next_work_unit": work_unit_id,
        "typed_blocker_resolution_ref": _first_text(
            resolution.get("source_ref"),
            resolution.get("decision_ref"),
            _first_text_item(
                [
                    ref.get("ref")
                    for ref in _mapping_list(next_action.get("diagnostic_refs"))
                    if ref.get("role") == "typed_blocker_resolution"
                ]
            ),
        ),
        "recommended_next_action": action_type,
    }
    stage_run_ref = f"paper-mission-followthrough://{study_id}/{_slug(work_unit_id)}"
    basis = (
        "typed-blocker-resolution-followthrough::"
        f"{study_id}::{_slug(work_unit_id)}::"
        f"{_first_text(action.get('work_unit_fingerprint'), next_action.get('work_unit_fingerprint'), action_type)}"
    )
    return _paper_mission_followthrough_transaction_instance(
        build_paper_mission_transaction(
            mission_id=mission_id,
            study_id=study_id,
            stage_id="submission_milestone_candidate",
            stage_run_ref=stage_run_ref,
            terminal_decision=terminal_decision,
            artifact_delta_refs=_mapping_list(transaction.get("artifact_delta_refs")),
            paper_audit_pack_refs=_mapping(transaction.get("paper_audit_pack_refs")),
            idempotency_basis=basis,
        ),
        instance_basis=basis,
    )


def _paper_mission_followthrough_transaction_instance(
    transaction: Mapping[str, Any],
    *,
    instance_basis: str,
) -> dict[str, Any]:
    payload = dict(transaction)
    suffix = f"::followthrough::{_stable_sha256(instance_basis)[:12]}"
    payload["transaction_id"] = f"{payload['transaction_id']}{suffix}"
    decision = dict(_mapping(payload.get("stage_terminal_decision")))
    route = dict(_mapping(payload.get("opl_route_command")))
    route["source_terminal_decision_ref"] = (
        f"{payload['transaction_id']}#stage_terminal_decision"
    )
    payload["stage_terminal_decision"] = decision
    payload["opl_route_command"] = route
    idempotency = dict(_mapping(payload.get("idempotency")))
    idempotency["idempotency_key"] = f"{idempotency['idempotency_key']}{suffix}"
    idempotency["transaction_fingerprint"] = (
        f"{idempotency['transaction_fingerprint']}{suffix}"
    )
    payload["idempotency"] = idempotency
    return PaperMissionTransaction.from_payload(payload).to_dict()


def _followthrough_candidate_manifest(
    *,
    readback: Mapping[str, Any],
    transaction: Mapping[str, Any],
    mission_id: str,
    study_id: str,
) -> dict[str, Any]:
    decision = _mapping(transaction.get("stage_terminal_decision"))
    return {
        "candidate_id": f"paper-mission-followthrough::{study_id}::{_slug(mission_id)}",
        "mission_id": mission_id,
        "study_id": study_id,
        "requested_outcome": "accepted_candidate",
        "candidate_manifest_ref": _optional_text(readback.get("candidate_ref")),
        "candidate_artifact_refs": [
            _optional_text(ref.get("uri")) or _optional_text(ref.get("ref_id"))
            for ref in _mapping_list(transaction.get("artifact_delta_refs"))
            if _optional_text(ref.get("uri")) or _optional_text(ref.get("ref_id"))
        ],
        "source_readiness_refs": _text_list(readback.get("source_readiness_refs")),
        "quality_auditor_requirement": {
            "independent_auditor_required": True,
            "owner": "MedAutoScience",
            "requirement_ref": f"paper-mission-followthrough::{study_id}",
        },
        "artifact_authority_boundary": {
            "artifact_authority_owner": "MedAutoScience",
            "candidate_is_authority": False,
            "can_update_current_package": False,
            "can_write_paper_body": False,
        },
        "next_owner": _first_text(decision.get("next_owner"), "mission_executor"),
        "resume_condition": _first_text(
            decision.get("reason"),
            "MAS consumes the followthrough candidate or routes it again.",
        ),
        "paper_mission_transaction": dict(transaction),
    }


def _followthrough_source_refs(readback: Mapping[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for key in (
        "candidate_ref",
        "materialized_mission_ref",
        "opl_runtime_readback_status",
    ):
        value = _optional_text(readback.get(key))
        if value is not None:
            refs.append({"ref_id": key, "ref_kind": key, "uri": value})
    consume_manifest = _mapping(readback.get("consume_output_manifest"))
    for key in (
        "output_root",
        "opl_route_handoff_ref",
        "paper_mission_transaction_ref",
    ):
        value = _optional_text(consume_manifest.get(key))
        if value is not None:
            refs.append({"ref_id": key, "ref_kind": key, "uri": value})
    return refs


__all__ = [
    "followthrough_transaction_for_readback",
    "paper_mission_followthrough_source_readback",
]
