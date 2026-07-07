from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.paper_mission_authority import consume_paper_mission_candidate
from .candidate_outputs import (
    consume_paper_mission_canary_candidate,
    mission_state_for_consume_status as _mission_state_for_consume_status,
    one_shot_required_output as _one_shot_required_output,
    paper_mission_candidate_artifact_delta,
    paper_mission_canary_candidate_manifest,
    paper_mission_owner_decision_packet,
)
from .audit_pack import (
    authority_touchpoints as _authority_touchpoints,
    paper_audit_pack as _paper_audit_pack,
    source_ref_payloads as _source_ref_payloads,
)
from .authority_boundary import (
    FORBIDDEN_AUTHORITY_CLAIMS as _FORBIDDEN_AUTHORITY_CLAIMS,
    FORBIDDEN_WRITES as _FORBIDDEN_WRITES,
    PAPER_MISSION_RUN_BLOCKED_PATHS as _PAPER_MISSION_RUN_BLOCKED_PATHS,
    authority_boundary as _authority_boundary,
)
from .payload_helpers import (
    compact_mapping as _compact_mapping,
    dedupe as _dedupe,
    first_mapping as _first_mapping,
    first_non_empty as _first_non_empty,
    first_text as _first_text,
    int_or_zero as _int_or_zero,
    mapping as _mapping,
    mapping_list as _mapping_list,
    text as _text,
    text_items as _text_items,
)
from .transaction_payload import (
    paper_mission_transaction_payload as _paper_mission_transaction_payload,
    platform_count as _platform_count,
    progress_payloads_by_study as _progress_payloads_by_study,
    refs_with_kinds as _refs_with_kinds,
    work_unit_ids as _work_unit_ids,
)
from med_autoscience.paper_mission_run import CONTRACT_VERSION, PaperMissionRun


DM002_STUDY_ID = "002-dm-china-us-mortality-attribution"
DM003_STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"

_DM_MISSION_OBJECTIVES: dict[str, dict[str, Any]] = {
    DM002_STUDY_ID: {
        "objective_id": "dm002_gate_clearing_claim_evidence_repair",
        "objective_kind": "gate_clearing_claim_evidence_repair",
        "summary": (
            "Prepare a no-write paper mission for gate-clearing and "
            "claim/evidence repair before MAS authority consumption."
        ),
        "target_delta": (
            "owner decision packet or consumable artifact-delta plan for "
            "gate-clearing; no publication, controller, owner receipt, typed "
            "blocker, human gate, current package, queue, or provider writes"
        ),
    },
    DM003_STUDY_ID: {
        "objective_id": "dm003_medical_prose_write_repair_publication_gate_replay",
        "objective_kind": "medical_prose_write_repair_publication_gate_replay",
        "summary": (
            "Prepare a no-write paper mission for medical prose repair and "
            "publication gate replay decision."
        ),
        "target_delta": (
            "owner decision packet or consumable prose-repair plan; no "
            "publication, controller, owner receipt, typed blocker, human gate, "
            "current package, queue, or provider writes"
        ),
    },
}

def build_paper_mission_canary_import_pack(
    *,
    study_progress_payloads: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    runtime_readback_payload: Mapping[str, Any] | None = None,
    profile_ref: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    progress_by_study = _progress_payloads_by_study(study_progress_payloads)
    domain_diagnostic = _mapping(runtime_readback_payload)
    mission_payloads = [
        _build_mission(
            study_id=study_id,
            progress=progress,
            domain_diagnostic=domain_diagnostic,
        )
        for study_id, progress in progress_by_study.items()
    ]
    source_generated = generated_at or _first_text(
        (progress.get("generated_at") for progress in progress_by_study.values())
    )
    return {
        "surface_kind": "paper_mission_canary_import_pack",
        "schema_version": 1,
        "mode": "no_write_import_inspect",
        "generated_at": source_generated,
        "profile_ref": profile_ref,
        "source_surfaces": {
            "study_progress": [
                {
                    "study_id": study_id,
                    "generated_at": _text(progress.get("generated_at")),
                    "truth_epoch": _text(progress.get("truth_epoch")),
                    "runtime_health_epoch": _text(progress.get("runtime_health_epoch")),
                }
                for study_id, progress in progress_by_study.items()
            ],
            "runtime_readback": {
                "available": bool(domain_diagnostic),
                "scanned_at": _text(domain_diagnostic.get("scanned_at")),
                "dry_run_written": bool(domain_diagnostic.get("written")),
            },
        },
        "paper_progress_accounting": {
            "import_pack_counts_as_paper_progress": False,
            "runtime_readback_counts_as_paper_progress": False,
            "paper_progress_requires": [
                "paper_facing_artifact_delta",
                "accepted_owner_decision_packet",
                "owner_receipt",
                "route_back",
                "human_gate",
                "stable_typed_blocker",
            ],
        },
        "authority_boundary": _authority_boundary(),
        "missions": mission_payloads,
    }


def build_dm_paper_mission_canary_import_pack(
    *,
    dm002_progress: Mapping[str, Any],
    dm003_progress: Mapping[str, Any],
    runtime_readback_payload: Mapping[str, Any] | None = None,
    profile_ref: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    return build_paper_mission_canary_import_pack(
        study_progress_payloads=(dm002_progress, dm003_progress),
        runtime_readback_payload=runtime_readback_payload,
        profile_ref=profile_ref,
        generated_at=generated_at,
    )


def build_dm_paper_mission_one_shot_migration_pack(
    *,
    dm002_progress: Mapping[str, Any],
    dm003_progress: Mapping[str, Any],
    runtime_readback_payload: Mapping[str, Any] | None = None,
    profile_ref: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    return build_paper_mission_one_shot_migration_pack(
        study_progress_payloads=(dm002_progress, dm003_progress),
        runtime_readback_payload=runtime_readback_payload,
        profile_ref=profile_ref,
        generated_at=generated_at,
    )


def build_paper_mission_one_shot_migration_pack(
    *,
    study_progress_payloads: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    runtime_readback_payload: Mapping[str, Any] | None = None,
    profile_ref: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    progress_by_study = _progress_payloads_by_study(study_progress_payloads)
    domain_diagnostic = _mapping(runtime_readback_payload)
    missions = [
        _build_one_shot_mission(
            study_id=study_id,
            progress=progress,
            domain_diagnostic=domain_diagnostic,
        )
        for study_id, progress in progress_by_study.items()
    ]
    source_generated = generated_at or _first_text(
        (progress.get("generated_at") for progress in progress_by_study.values())
    )
    return {
        "surface_kind": "paper_mission_one_shot_migration_pack",
        "schema_version": 1,
        "mode": "legacy_truth_import_to_formal_paper_mission_run",
        "generated_at": source_generated,
        "profile_ref": profile_ref,
        "authority_boundary": _authority_boundary(),
        "paper_progress_accounting": {
            "legacy_import_counts_as_paper_progress": False,
            "new_mission_counts_as_default_execution_state": True,
            "old_blockers_count_as_default_execution_state": False,
            "paper_progress_requires": [
                "mission_artifact_delta",
                "accepted_owner_decision_packet",
                "route_back",
                "human_gate",
                "stable_typed_blocker",
            ],
        },
        "missions": missions,
    }


def paper_mission_by_study(import_pack: Mapping[str, Any], study_id: str) -> dict[str, Any]:
    for mission in _mapping_list(import_pack.get("missions")):
        if mission.get("study_id") == study_id:
            return mission
    raise KeyError(study_id)


def _build_one_shot_mission(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    domain_diagnostic: Mapping[str, Any],
) -> dict[str, Any]:
    action = _domain_diagnostic_action_for_study(domain_diagnostic, study_id=study_id)
    current_work_unit = _first_mapping(
        action.get("current_work_unit"),
        _mapping(progress.get("current_work_unit")),
    )
    current_owner_action = _first_mapping(
        action.get("current_executable_owner_action"),
        _mapping(progress.get("current_executable_owner_action")),
    )
    execution_envelope = _first_mapping(
        action.get("current_execution_envelope"),
        _domain_diagnostic_current_execution_envelope(domain_diagnostic, study_id=study_id),
        _mapping(progress.get("current_execution_envelope")),
    )
    typed_blocker = _first_mapping(
        execution_envelope.get("typed_blocker"),
        _mapping(current_work_unit.get("typed_blocker")),
    )
    intervention_lane = _mapping(progress.get("intervention_lane"))
    route_back_checklist = _mapping(intervention_lane.get("route_back_checklist"))
    mission_objective = _mission_objective(
        study_id=study_id,
        progress=progress,
        route_back_checklist=route_back_checklist,
    )
    legacy_import = _legacy_truth_import_pack(
        study_id=study_id,
        progress=progress,
        domain_diagnostic=domain_diagnostic,
        action=action,
        current_work_unit=current_work_unit,
        current_owner_action=current_owner_action,
        execution_envelope=execution_envelope,
        typed_blocker=typed_blocker,
        route_back_checklist=route_back_checklist,
        intervention_lane=intervention_lane,
    )
    current_blocker = _current_blocker(
        progress=progress,
        current_work_unit=current_work_unit,
        current_owner_action=current_owner_action,
        execution_envelope=execution_envelope,
        typed_blocker=typed_blocker,
        intervention_lane=intervention_lane,
    )
    platform_diagnostics = _platform_diagnostics(
        study_id=study_id,
        action=action,
        domain_diagnostic=domain_diagnostic,
    )
    mission = _formal_one_shot_mission_payload(
        study_id=study_id,
        mission_objective=mission_objective,
        legacy_import=legacy_import,
        current_blocker=current_blocker,
        platform_diagnostics=platform_diagnostics,
    )
    candidate = paper_mission_canary_candidate_manifest(mission)
    consume_readback = consume_paper_mission_candidate(candidate)
    readback = dict(mission["one_shot_migration_readback"])
    readback["consume_candidate_status"] = consume_readback["consume_result"]["status"]
    readback["consume_candidate_readback"] = consume_readback
    mission["consume_result"] = {
        "status": consume_readback["consume_result"]["status"],
        "outcome": consume_readback["consume_result"]["outcome"],
        "authority_materialized": False,
    }
    mission["mission_state"] = _mission_state_for_consume_status(
        mission["consume_result"]["status"]
    )
    transaction = _paper_mission_transaction_payload(
        mission=mission,
        readback=readback,
        consume_result=mission["consume_result"],
    )
    readback["stage_terminal_decision"] = transaction["stage_terminal_decision"]
    readback["opl_route_command"] = transaction["opl_route_command"]
    readback["paper_mission_transaction_ref"] = transaction["transaction_id"]
    mission["one_shot_migration_readback"] = readback
    mission["paper_mission_transaction"] = transaction
    return PaperMissionRun.from_payload(mission).to_dict()


def _build_mission(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    domain_diagnostic: Mapping[str, Any],
) -> dict[str, Any]:
    action = _domain_diagnostic_action_for_study(domain_diagnostic, study_id=study_id)
    current_work_unit = _first_mapping(
        action.get("current_work_unit"),
        _mapping(progress.get("current_work_unit")),
    )
    current_owner_action = _first_mapping(
        action.get("current_executable_owner_action"),
        _mapping(progress.get("current_executable_owner_action")),
    )
    execution_envelope = _first_mapping(
        action.get("current_execution_envelope"),
        _domain_diagnostic_current_execution_envelope(domain_diagnostic, study_id=study_id),
        _mapping(progress.get("current_execution_envelope")),
    )
    typed_blocker = _first_mapping(
        execution_envelope.get("typed_blocker"),
        _mapping(current_work_unit.get("typed_blocker")),
    )
    intervention_lane = _mapping(progress.get("intervention_lane"))
    route_back_checklist = _mapping(intervention_lane.get("route_back_checklist"))
    mission_objective = _mission_objective(
        study_id=study_id,
        progress=progress,
        route_back_checklist=route_back_checklist,
    )
    artifact_refs = _artifact_refs(
        progress=progress,
        current_work_unit=current_work_unit,
        current_owner_action=current_owner_action,
        execution_envelope=execution_envelope,
        typed_blocker=typed_blocker,
        route_back_checklist=route_back_checklist,
    )
    platform_diagnostics = _platform_diagnostics(
        study_id=study_id,
        action=action,
        domain_diagnostic=domain_diagnostic,
    )
    current_blocker = _current_blocker(
        progress=progress,
        current_work_unit=current_work_unit,
        current_owner_action=current_owner_action,
        execution_envelope=execution_envelope,
        typed_blocker=typed_blocker,
        intervention_lane=intervention_lane,
    )
    readback = {
        "surface_kind": "paper_mission_canary_readback",
        "schema_version": 1,
        "mode": "no_write_import_inspect",
        "quest_id": _text(progress.get("quest_id")) or study_id,
        "mission_objective": mission_objective,
        "current_stage": _text(progress.get("current_stage")),
        "paper_stage": _text(progress.get("paper_stage")),
        "paper_progress": {
            "progress_delta_kind": "no_write_inspect_only",
            "mission_import_counts_as_paper_progress": False,
            "platform_diagnostics_count_as_paper_progress": False,
            "meaningful_artifact_delta_observed_in_source": bool(
                progress.get("meaningful_artifact_delta")
            ),
        },
        "artifact_refs": artifact_refs,
        "current_blocker": current_blocker,
        "owner_decision_packet_requirement": _owner_decision_packet_requirement(
            mission_objective=mission_objective,
            current_blocker=current_blocker,
            current_work_unit=current_work_unit,
            typed_blocker=typed_blocker,
            route_back_checklist=route_back_checklist,
        ),
        "authority_boundary": _authority_boundary(),
    }
    payload = _paper_mission_run_payload(
        study_id=study_id,
        mission_objective=mission_objective,
        artifact_refs=artifact_refs,
        readback=readback,
        current_blocker=current_blocker,
        platform_diagnostics=platform_diagnostics,
    )
    transaction = _paper_mission_transaction_payload(
        mission=payload,
        readback=readback,
        consume_result=payload["consume_result"],
    )
    readback["stage_terminal_decision"] = transaction["stage_terminal_decision"]
    readback["opl_route_command"] = transaction["opl_route_command"]
    readback["paper_mission_transaction_ref"] = transaction["transaction_id"]
    payload["canary_import_readback"] = dict(readback)
    payload["paper_mission_transaction"] = transaction
    return PaperMissionRun.from_payload(payload).to_dict()


def _paper_mission_run_payload(
    *,
    study_id: str,
    mission_objective: Mapping[str, Any],
    artifact_refs: list[str],
    readback: Mapping[str, Any],
    current_blocker: Mapping[str, Any],
    platform_diagnostics: Mapping[str, Any],
) -> dict[str, Any]:
    objective_id = _text(mission_objective.get("objective_id")) or "paper_mission_import"
    objective_kind = _text(mission_objective.get("objective_kind")) or "paper_mission_import"
    objective = _text(mission_objective.get("summary")) or objective_id
    source_refs = _source_ref_payloads(artifact_refs)
    payload = {
        "schema_version": CONTRACT_VERSION,
        "mission_id": f"paper-mission::{study_id}::{objective_kind}::canary-import-readback",
        "study_id": study_id,
        "objective": objective,
        "mission_state": "planned",
        "artifact_delta_ledger": [
            {
                "delta_id": f"delta::{study_id}::{objective_id}",
                "artifact_ref": f"mission://{study_id}/canary/{objective_id}",
                "delta_kind": "owner_decision_packet_requirement",
                "status": "planned_no_write",
            }
        ],
        "source_refs": source_refs,
        "paper_audit_pack": _paper_audit_pack(
            study_id=study_id,
            objective_id=objective_id,
            objective_kind=objective_kind,
            artifact_refs=artifact_refs,
            source_refs=source_refs,
            readback=readback,
            current_blocker=current_blocker,
            platform_diagnostics=platform_diagnostics,
        ),
        "authority_touchpoints": _authority_touchpoints(
            study_id=study_id,
            source_refs=source_refs,
            platform_diagnostics=platform_diagnostics,
        ),
        "forbidden_write_guard": {
            "blocked_paths": list(_PAPER_MISSION_RUN_BLOCKED_PATHS),
            "forbidden_claims": list(_FORBIDDEN_AUTHORITY_CLAIMS),
            "candidate_writes_authority": False,
        },
        "consume_result": {
            "status": "not_consumed",
            "reason": "no_write_canary_import_inspect",
        },
        "claim_permissions": {
            "can_claim_artifact_delta": False,
            "can_claim_owner_handoff": bool(_text(current_blocker.get("owner"))),
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
            "claims": [
                "canary_import_readback",
                "owner_decision_packet_required",
            ],
        },
        "canary_import_readback": dict(readback),
    }
    transaction = _paper_mission_transaction_payload(
        mission=payload,
        readback=readback,
        consume_result=payload["consume_result"],
    )
    payload["canary_import_readback"] = {
        **dict(readback),
        "stage_terminal_decision": transaction["stage_terminal_decision"],
        "opl_route_command": transaction["opl_route_command"],
        "paper_mission_transaction_ref": transaction["transaction_id"],
    }
    payload["paper_mission_transaction"] = transaction
    return payload


def _formal_one_shot_mission_payload(
    *,
    study_id: str,
    mission_objective: Mapping[str, Any],
    legacy_import: Mapping[str, Any],
    current_blocker: Mapping[str, Any],
    platform_diagnostics: Mapping[str, Any],
) -> dict[str, Any]:
    objective_id = _text(mission_objective.get("objective_id")) or "paper_mission"
    objective_kind = _text(mission_objective.get("objective_kind")) or "paper_mission"
    mission_id = f"paper-mission::{study_id}::{objective_kind}::one-shot-migration"
    artifact_refs = _text_items(legacy_import.get("current_artifact_refs"))
    source_refs = _source_ref_payloads(_text_items(legacy_import.get("all_source_refs")))
    required_output = _one_shot_required_output(
        mission_objective=mission_objective,
        legacy_import=legacy_import,
        current_blocker=current_blocker,
    )
    readback = {
        "surface_kind": "paper_mission_one_shot_migration_readback",
        "schema_version": 1,
        "mode": "formal_mission_default_readback",
        "current_mission": {
            "mission_id": mission_id,
            "study_id": study_id,
            "objective_id": objective_id,
            "objective_kind": objective_kind,
            "legacy_blocker_is_default_execution_state": False,
        },
        "next_owner": required_output["next_owner"],
        "required_output": required_output,
        "consume_candidate_status": "not_consumed",
        "legacy_truth_import_pack": dict(legacy_import),
        "mission_input": {
            "legacy_truth_import_ref": f"mission://{study_id}/legacy-truth-import-pack",
            "legacy_blocker": _mapping(legacy_import.get("legacy_constraints")).get("old_blocker"),
            "source_refs": source_refs,
            "non_degradation_evidence": _mapping(
                legacy_import.get("non_degradation_evidence")
            ),
        },
        "decision_constraints": _mapping(legacy_import.get("decision_constraints")),
        "paper_progress_accounting": {
            "legacy_import_counts_as_paper_progress": False,
            "old_blocker_counts_as_default_execution_state": False,
            "new_mission_is_default_execution_state": True,
        },
        "authority_boundary": _authority_boundary(),
    }
    payload = {
        "schema_version": CONTRACT_VERSION,
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": _text(mission_objective.get("summary")) or objective_id,
        "mission_state": "candidate_ready_for_consumption",
        "artifact_delta_ledger": [
            {
                "delta_id": f"delta::{study_id}::{objective_id}::one-shot",
                "artifact_ref": f"mission://{study_id}/one-shot/{objective_id}",
                "delta_kind": "formal_paper_mission_owner_decision_packet",
                "status": "candidate",
            }
        ],
        "source_refs": source_refs,
        "paper_audit_pack": _paper_audit_pack(
            study_id=study_id,
            objective_id=objective_id,
            objective_kind=objective_kind,
            artifact_refs=artifact_refs,
            source_refs=source_refs,
            readback=readback,
            current_blocker=current_blocker,
            platform_diagnostics=platform_diagnostics,
            legacy_import=legacy_import,
        ),
        "authority_touchpoints": _authority_touchpoints(
            study_id=study_id,
            source_refs=source_refs,
            platform_diagnostics=platform_diagnostics,
        ),
        "forbidden_write_guard": {
            "blocked_paths": list(_PAPER_MISSION_RUN_BLOCKED_PATHS),
            "forbidden_claims": list(_FORBIDDEN_AUTHORITY_CLAIMS),
            "candidate_writes_authority": False,
        },
        "consume_result": {
            "status": "not_consumed",
            "reason": "one_shot_migration_candidate_not_consumed",
        },
        "claim_permissions": {
            "can_claim_artifact_delta": True,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
            "claims": [
                "legacy_truth_import_pack",
                "formal_paper_mission_run",
                "owner_decision_packet_candidate",
            ],
        },
        "one_shot_migration_readback": readback,
        "canary_import_readback": {
            "mission_objective": dict(mission_objective),
            "current_blocker": dict(current_blocker),
            "owner_decision_packet_requirement": {
                "required": True,
                "owner": required_output["next_owner"],
                "objective_id": objective_id,
                "work_unit_id": required_output["work_unit_id"],
                "accepted_terminal_results": [
                    "owner_receipt",
                    "typed_blocker",
                ],
                "authority_boundary": _authority_boundary(),
            },
        },
    }
    transaction = _paper_mission_transaction_payload(
        mission=payload,
        readback=readback,
        consume_result=payload["consume_result"],
    )
    payload["one_shot_migration_readback"] = {
        **readback,
        "stage_terminal_decision": transaction["stage_terminal_decision"],
        "opl_route_command": transaction["opl_route_command"],
        "paper_mission_transaction_ref": transaction["transaction_id"],
    }
    payload["paper_mission_transaction"] = transaction
    return payload


def _legacy_truth_import_pack(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    domain_diagnostic: Mapping[str, Any],
    action: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_owner_action: Mapping[str, Any],
    execution_envelope: Mapping[str, Any],
    typed_blocker: Mapping[str, Any],
    route_back_checklist: Mapping[str, Any],
    intervention_lane: Mapping[str, Any],
) -> dict[str, Any]:
    current_refs = _artifact_refs(
        progress=progress,
        current_work_unit=current_work_unit,
        current_owner_action=current_owner_action,
        execution_envelope=execution_envelope,
        typed_blocker=typed_blocker,
        route_back_checklist=route_back_checklist,
    )
    publication_eval_refs = _refs_with_kinds(current_refs, {"publication_eval"})
    controller_refs = _refs_with_kinds(current_refs, {"controller_decision"})
    evidence_refs = _dedupe(
        _text_items(route_back_checklist.get("evidence_refs"))
        + _text_items(current_work_unit.get("input_refs"))
        + _text_items(current_owner_action.get("acceptance_refs"))
        + _text_items(typed_blocker.get("closeout_refs"))
    )
    legacy_owner_refs = _dedupe(
        _text_items(
            (
                typed_blocker.get("typed_blocker_ref"),
                typed_blocker.get("latest_owner_answer_ref"),
                typed_blocker.get("source_ref"),
                intervention_lane.get("handoff_source"),
            )
        )
        + _text_items(typed_blocker.get("closeout_refs"))
    )
    opl_refs = _dedupe(
        _text_items(
            (
                "provider_admission_pending_count="
                f"{_platform_count(domain_diagnostic, 'provider_admission_pending_count')}",
                "transition_request_pending_count="
                f"{_platform_count(domain_diagnostic, 'transition_request_pending_count')}",
                "opl_current_control_state.next_owner",
                _text(_mapping(action.get("runtime_health_snapshot")).get("runtime_health_epoch")),
            )
        )
    )
    old_blocker = {
        "current_blockers": _text_items(progress.get("current_blockers")),
        "why_not_progressing": _text(progress.get("why_not_progressing")),
        "current_work_unit_status": _text(current_work_unit.get("status")),
        "typed_blocker": _compact_mapping(
            typed_blocker,
            (
                "blocker_id",
                "blocker_type",
                "blocked_reason",
                "owner",
                "required_input",
                "work_unit_id",
                "work_unit_fingerprint",
            ),
        ),
        "current_owner_action": _compact_mapping(
            current_owner_action,
            (
                "status",
                "next_owner",
                "action_type",
                "work_unit_id",
                "work_unit_fingerprint",
            ),
        ),
    }
    legacy_constraints = {
        "old_blocker": old_blocker,
        "old_blocker_is_default_execution_state": False,
        "must_not_resume_legacy_owner_callable_adapter": True,
        "must_not_write_authority_surfaces": True,
        "must_not_update_current_package": True,
    }
    decision_constraints = {
        "must_consume_through": "MAS authority consume path",
        "candidate_can_be": [
            "accepted_owner_decision_packet",
            "route_back",
            "human_gate",
            "stable_typed_blocker",
        ],
        "forbidden_claims": list(_FORBIDDEN_AUTHORITY_CLAIMS),
        "forbidden_writes": list(_FORBIDDEN_WRITES),
        "legacy_blocker_may_inform_decision": True,
        "legacy_blocker_may_select_default_execution_state": False,
    }
    return {
        "surface_kind": "paper_mission_legacy_truth_import_pack",
        "schema_version": 1,
        "study_id": study_id,
        "current_artifact_refs": current_refs,
        "publication_eval_refs": publication_eval_refs,
        "controller_decision_refs": controller_refs,
        "evidence_and_review_ledger_refs": evidence_refs,
        "legacy_owner_state_refs": legacy_owner_refs,
        "opl_current_control_refs": opl_refs,
        "legacy_constraints": legacy_constraints,
        "decision_constraints": decision_constraints,
        "non_degradation_evidence": {
            "old_blocker_preserved_in_constraints": bool(
                old_blocker["current_blockers"]
                or old_blocker["why_not_progressing"]
                or old_blocker["typed_blocker"]
                or old_blocker["current_owner_action"]
            ),
            "publication_eval_refs_preserved": bool(publication_eval_refs),
            "controller_decision_refs_preserved": bool(controller_refs),
            "evidence_refs_preserved": bool(evidence_refs),
            "opl_current_control_refs_preserved": bool(opl_refs),
            "legacy_blocker_not_default_execution_state": True,
        },
        "all_source_refs": _dedupe(
            current_refs
            + publication_eval_refs
            + controller_refs
            + evidence_refs
            + legacy_owner_refs
            + opl_refs
        ),
    }


def _mission_objective(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    route_back_checklist: Mapping[str, Any],
) -> dict[str, Any]:
    objective = dict(
        _DM_MISSION_OBJECTIVES.get(
            study_id,
            {
                "objective_id": f"paper_mission_import::{study_id}",
                "objective_kind": "paper_mission_import",
                "summary": _text(progress.get("next_system_action"))
                or "Prepare a no-write paper mission inspect payload.",
                "target_delta": "owner decision packet or consumable artifact-delta plan",
            },
        )
    )
    objective["basis"] = {
        "next_system_action": _text(progress.get("next_system_action")),
        "route_back_decision_type": _text(route_back_checklist.get("decision_type")),
        "route_back_required": bool(route_back_checklist.get("route_back_required")),
        "next_work_units": _work_unit_ids(route_back_checklist.get("next_work_units")),
    }
    return objective


def _artifact_refs(
    *,
    progress: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_owner_action: Mapping[str, Any],
    execution_envelope: Mapping[str, Any],
    typed_blocker: Mapping[str, Any],
    route_back_checklist: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    for event in _mapping_list(progress.get("latest_events")):
        refs.extend(_text_items((event.get("artifact_path"),)))
    refs.extend(_text_items(route_back_checklist.get("evidence_refs")))
    refs.extend(_text_items(current_work_unit.get("input_refs")))
    refs.extend(_text_items(current_owner_action.get("acceptance_refs")))
    refs.extend(_text_items(execution_envelope.get("source_refs")))
    refs.extend(_text_items(typed_blocker.get("closeout_refs")))
    refs.extend(
        _text_items(
            (
                typed_blocker.get("typed_blocker_ref"),
                typed_blocker.get("latest_owner_answer_ref"),
                typed_blocker.get("source_ref"),
            )
        )
    )
    return _dedupe(refs)


def _current_blocker(
    *,
    progress: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_owner_action: Mapping[str, Any],
    execution_envelope: Mapping[str, Any],
    typed_blocker: Mapping[str, Any],
    intervention_lane: Mapping[str, Any],
) -> dict[str, Any]:
    if typed_blocker:
        return {
            "status": "typed_blocker",
            "blocker_id": _text(typed_blocker.get("blocker_id"))
            or _text(typed_blocker.get("blocker_type"))
            or _text(typed_blocker.get("blocked_reason")),
            "owner": _text(typed_blocker.get("owner")) or _text(execution_envelope.get("owner")),
            "action_type": _text(typed_blocker.get("action_type")),
            "work_unit_id": _text(typed_blocker.get("work_unit_id")),
            "work_unit_fingerprint": _text(typed_blocker.get("work_unit_fingerprint")),
            "reason": _text(typed_blocker.get("reason")),
            "required_input": _text(typed_blocker.get("required_input")),
            "source_ref": _text(typed_blocker.get("typed_blocker_ref"))
            or _text(typed_blocker.get("source_ref")),
        }
    if current_owner_action:
        return {
            "status": "owner_action_ready",
            "blocker_id": _first_non_empty(
                progress.get("why_not_progressing"),
                intervention_lane.get("route_key_question"),
            ),
            "owner": _first_non_empty(
                current_owner_action.get("next_owner"),
                current_work_unit.get("owner"),
                intervention_lane.get("route_target"),
            ),
            "action_type": _first_non_empty(
                current_owner_action.get("action_type"),
                current_work_unit.get("action_type"),
            ),
            "work_unit_id": _first_non_empty(
                current_owner_action.get("work_unit_id"),
                current_work_unit.get("work_unit_id"),
                intervention_lane.get("work_unit_id"),
            ),
            "work_unit_fingerprint": _first_non_empty(
                current_owner_action.get("work_unit_fingerprint"),
                current_work_unit.get("work_unit_fingerprint"),
            ),
            "reason": _text(progress.get("next_system_action")),
            "required_input": None,
            "source_ref": None,
        }
    return {
        "status": "unresolved",
        "blocker_id": _first_non_empty(
            progress.get("why_not_progressing"),
            intervention_lane.get("route_key_question"),
        ),
        "owner": _first_non_empty(intervention_lane.get("route_target"), intervention_lane.get("owner")),
        "action_type": _text(intervention_lane.get("action_type")),
        "work_unit_id": _text(intervention_lane.get("work_unit_id")),
        "work_unit_fingerprint": None,
        "reason": _text(progress.get("next_system_action")),
        "required_input": None,
        "source_ref": None,
    }


def _owner_decision_packet_requirement(
    *,
    mission_objective: Mapping[str, Any],
    current_blocker: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    typed_blocker: Mapping[str, Any],
    route_back_checklist: Mapping[str, Any],
) -> dict[str, Any]:
    required_output_contract = _mapping(current_work_unit.get("required_output_contract"))
    accepted_terminal_results = _text_items(
        required_output_contract.get("accepted_terminal_results")
    ) or [
        "owner_receipt",
        "typed_blocker",
        "route_back",
        "human_gate",
    ]
    requirement = {
        "required": True,
        "owner": _text(current_blocker.get("owner")),
        "objective_id": _text(mission_objective.get("objective_id")),
        "work_unit_id": _text(current_blocker.get("work_unit_id")),
        "accepted_terminal_results": _dedupe(accepted_terminal_results),
        "must_include": [
            "mission_objective",
            "current_work_unit_identity",
            "artifact_refs",
            "source_refs",
            "currentness_basis",
            "forbidden_write_acknowledgement",
            "consume_path_request",
        ],
        "authority_boundary": _authority_boundary(),
    }
    if typed_blocker:
        requirement["typed_blocker_input_required"] = _text(typed_blocker.get("required_input"))
        requirement["existing_owner_answer_ref"] = _first_non_empty(
            typed_blocker.get("latest_owner_answer_ref"),
            typed_blocker.get("typed_blocker_ref"),
            typed_blocker.get("source_ref"),
        )
    next_units = _work_unit_ids(route_back_checklist.get("next_work_units"))
    if next_units:
        requirement["route_back_next_work_units"] = next_units
    return requirement


def _platform_diagnostics(
    *,
    study_id: str,
    action: Mapping[str, Any],
    domain_diagnostic: Mapping[str, Any],
) -> dict[str, Any]:
    provider_state = _mapping(domain_diagnostic.get("provider_admission_current_control_state"))
    action_queue = _mapping_list(provider_state.get("action_queue"))
    envelopes = _mapping(provider_state.get("current_execution_envelopes"))
    return {
        "counts_as_paper_progress": False,
        "runtime_readback_available": bool(domain_diagnostic),
        "domain_diagnostic_scanned_at": _text(domain_diagnostic.get("scanned_at")),
        "domain_diagnostic_written": bool(domain_diagnostic.get("written")),
        "running_provider_attempt": bool(action.get("running_provider_attempt")),
        "runtime_health": _compact_mapping(
            _mapping(action.get("runtime_health_snapshot")),
            (
                "runtime_health_epoch",
                "canonical_runtime_action",
                "attempt_state",
                "retry_budget_remaining",
                "blocking_reasons",
            ),
        ),
        "provider_admission_current_control": {
            "provider_admission_pending_count": _int_or_zero(
                provider_state.get("provider_admission_pending_count")
            ),
            "transition_request_pending_count": _int_or_zero(
                provider_state.get("transition_request_pending_count")
            ),
            "action_queue_count": len(action_queue),
            "current_execution_state_kind": _text(
                _mapping(envelopes.get(study_id)).get("state_kind")
            ),
        },
        "stage_route_arbiter": _compact_mapping(
            _mapping(provider_state.get("stage_route_arbiter")),
            (
                "surface_kind",
                "candidate_count",
                "pending_count",
                "decision_counts",
                "ordinary_planning_root",
            ),
        ),
    }


def _domain_diagnostic_action_for_study(domain_diagnostic: Mapping[str, Any], *, study_id: str) -> dict[str, Any]:
    for action in _mapping_list(domain_diagnostic.get("managed_study_actions")):
        if action.get("study_id") == study_id:
            return action
    return {}


def _domain_diagnostic_current_execution_envelope(
    domain_diagnostic: Mapping[str, Any],
    *,
    study_id: str,
) -> dict[str, Any]:
    provider_state = _mapping(domain_diagnostic.get("provider_admission_current_control_state"))
    envelopes = _mapping(provider_state.get("current_execution_envelopes"))
    return _mapping(envelopes.get(study_id))
