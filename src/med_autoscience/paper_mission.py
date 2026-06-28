from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.paper_mission_authority import consume_paper_mission_candidate
from med_autoscience.paper_mission_run import CONTRACT_VERSION, PaperMissionRun
from med_autoscience.paper_mission_transaction import (
    build_paper_mission_transaction,
    stage_terminal_decision_for_consume_result,
)


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

_FORBIDDEN_WRITES = (
    "/Users/gaofeng/workspace/Yang/**",
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner_receipt",
    "typed_blocker",
    "human_gate",
    "current_package",
    "runtime_queue",
    "provider_attempt",
    "provider_start",
    "hydrate",
    "tick",
    "redrive",
    "apply",
)
_PAPER_AUDIT_PACK_FAMILIES = (
    "analysis_rationale_log",
    "decision_trace",
    "evidence_ledger_delta",
    "review_ledger_delta",
    "revision_log_delta",
    "failed_path_ledger",
    "artifact_lineage",
    "reproducibility_refs",
)
_PAPER_MISSION_RUN_BLOCKED_PATHS = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "current_package",
    "runtime queue/provider attempts",
    "/Users/gaofeng/workspace/Yang/**",
)
_FORBIDDEN_AUTHORITY_CLAIMS = (
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


def paper_mission_canary_candidate_manifest(
    mission: Mapping[str, Any],
    *,
    requested_outcome: str | None = None,
) -> dict[str, Any]:
    readback = _mapping(mission.get("canary_import_readback"))
    mission_objective = _mapping(readback.get("mission_objective"))
    current_blocker = _mapping(readback.get("current_blocker"))
    requirement = _mapping(readback.get("owner_decision_packet_requirement"))
    selected_outcome = requested_outcome or _candidate_requested_outcome(
        current_blocker=current_blocker,
        requirement=requirement,
    )
    candidate_id = (
        "paper-mission-candidate::"
        f"{_text(mission.get('study_id')) or 'unknown-study'}::"
        f"{_text(mission_objective.get('objective_id')) or 'canary-import'}"
    )
    source_refs = _mapping_list(mission.get("source_refs"))
    source_uris = [_text(source_ref.get("uri")) for source_ref in source_refs]
    source_readiness_refs = _dedupe(
        [
            item
            for item in (
                [
                    f"study-progress:{_text(mission.get('study_id')) or 'unknown-study'}",
                    f"mission-objective:{_text(mission_objective.get('objective_id')) or 'unknown'}",
                ]
                + [uri for uri in source_uris if uri]
            )
            if item
        ]
    )
    return {
        "candidate_id": candidate_id,
        "mission_id": _text(mission.get("mission_id")) or "unknown_mission",
        "study_id": _text(mission.get("study_id")) or "unknown_study",
        "requested_outcome": selected_outcome,
        "candidate_manifest_ref": f"mission://{candidate_id}/manifest.json",
        "candidate_artifact_refs": [
            _text(item.get("artifact_ref"))
            for item in _mapping_list(mission.get("artifact_delta_ledger"))
            if _text(item.get("artifact_ref"))
        ],
        "source_readiness_refs": source_readiness_refs,
        "quality_auditor_requirement": {
            "independent_auditor_required": True,
            "owner": "MedAutoScience",
            "requirement_ref": (
                "paper-mission-quality-audit::"
                f"{_text(mission.get('study_id')) or 'unknown-study'}::"
                f"{_text(mission_objective.get('objective_id')) or 'canary-import'}"
            ),
        },
        "artifact_authority_boundary": {
            "artifact_authority_owner": "MedAutoScience",
            "candidate_is_authority": False,
            "can_update_current_package": False,
            "can_write_paper_body": False,
        },
        "next_owner": _text(requirement.get("owner"))
        or _text(current_blocker.get("owner"))
        or "mas_authority_kernel",
        "resume_condition": (
            "MAS authority kernel consumes, routes back, records a human-gate request, "
            "or records a typed-blocker request for this paper mission candidate"
        ),
        **_candidate_outcome_request_payload(
            selected_outcome=selected_outcome,
            candidate_id=candidate_id,
            current_blocker=current_blocker,
            requirement=requirement,
        ),
    }


def paper_mission_candidate_artifact_delta(mission: Mapping[str, Any]) -> dict[str, Any]:
    readback = _mapping(mission.get("one_shot_migration_readback"))
    legacy = _mapping(readback.get("legacy_truth_import_pack"))
    required_output = _mapping(readback.get("required_output"))
    current_mission = _mapping(readback.get("current_mission"))
    deltas = _mapping_list(mission.get("artifact_delta_ledger"))
    delta = deltas[0] if deltas else {}
    return {
        "surface_kind": "paper_mission_candidate_artifact_delta",
        "schema_version": 1,
        "study_id": _text(mission.get("study_id")) or "unknown_study",
        "mission_id": _text(mission.get("mission_id")) or "unknown_mission",
        "delta_id": _text(delta.get("delta_id"))
        or f"delta::{_text(mission.get('study_id')) or 'unknown-study'}::candidate",
        "artifact_ref": _text(delta.get("artifact_ref"))
        or f"mission://{_text(mission.get('study_id')) or 'unknown-study'}/candidate",
        "delta_kind": _text(delta.get("delta_kind"))
        or "formal_paper_mission_owner_decision_packet",
        "status": _text(delta.get("status")) or "candidate",
        "counts_as_paper_progress": True,
        "candidate_is_authority": False,
        "current_mission": dict(current_mission),
        "objective_kind": _text(current_mission.get("objective_kind")),
        "required_output": dict(required_output),
        "source_ref_families": {
            "current_artifact_refs": _text_items(legacy.get("current_artifact_refs")),
            "publication_eval_refs": _text_items(legacy.get("publication_eval_refs")),
            "controller_decision_refs": _text_items(legacy.get("controller_decision_refs")),
            "evidence_and_review_ledger_refs": _text_items(
                legacy.get("evidence_and_review_ledger_refs")
            ),
            "legacy_owner_state_refs": _text_items(legacy.get("legacy_owner_state_refs")),
            "opl_current_control_refs": _text_items(legacy.get("opl_current_control_refs")),
        },
        "forbidden_write_acknowledgement": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "forbidden_writes": list(_FORBIDDEN_WRITES),
            "forbidden_authority_claims": list(_FORBIDDEN_AUTHORITY_CLAIMS),
        },
        "authority_boundary": _authority_boundary(),
    }


def paper_mission_owner_decision_packet(mission: Mapping[str, Any]) -> dict[str, Any]:
    readback = _mapping(mission.get("one_shot_migration_readback"))
    legacy = _mapping(readback.get("legacy_truth_import_pack"))
    required_output = _mapping(readback.get("required_output"))
    decision_constraints = _mapping(readback.get("decision_constraints"))
    artifact_delta = paper_mission_candidate_artifact_delta(mission)
    return {
        "surface_kind": "paper_mission_owner_decision_packet",
        "schema_version": 1,
        "study_id": artifact_delta["study_id"],
        "mission_id": artifact_delta["mission_id"],
        "packet_id": f"owner-decision::{artifact_delta['study_id']}::{artifact_delta['delta_id']}",
        "packet_status": "candidate_ready_for_mas_consume",
        "candidate_is_authority": False,
        "next_owner": _text(required_output.get("next_owner")) or "mas_authority_kernel",
        "required_output_kind": _text(required_output.get("kind"))
        or "owner_decision_packet_or_consumable_artifact_delta",
        "accepted_terminal_results": _text_items(
            required_output.get("accepted_terminal_results")
        ),
        "artifact_delta_ref": artifact_delta["artifact_ref"],
        "consume_path": {
            "surface": "MAS authority consume path",
            "allowed_results": [
                "accepted_owner_decision_packet",
                "route_back",
                "human_gate",
                "stable_typed_blocker",
            ],
            "authority_materialized_by_this_packet": False,
        },
        "legacy_constraints": _mapping(legacy.get("legacy_constraints")),
        "decision_constraints": decision_constraints,
        "non_degradation_evidence": _mapping(legacy.get("non_degradation_evidence")),
        "forbidden_write_acknowledgement": artifact_delta[
            "forbidden_write_acknowledgement"
        ],
        "authority_boundary": _authority_boundary(),
    }


def consume_paper_mission_canary_candidate(
    mission: Mapping[str, Any],
    *,
    requested_outcome: str | None = None,
) -> dict[str, Any]:
    candidate = paper_mission_canary_candidate_manifest(
        mission,
        requested_outcome=requested_outcome,
    )
    return {
        "surface_kind": "paper_mission_canary_candidate_consume_readback",
        "schema_version": 1,
        "study_id": _text(mission.get("study_id")) or "unknown_study",
        "mission_id": _text(mission.get("mission_id")) or "unknown_mission",
        "candidate_manifest": candidate,
        "authority_consume_readback": consume_paper_mission_candidate(candidate),
    }


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
        "touchpoints": _touchpoints(
            progress=progress,
            current_work_unit=current_work_unit,
            current_owner_action=current_owner_action,
            execution_envelope=execution_envelope,
            route_back_checklist=route_back_checklist,
        ),
        "current_blocker": current_blocker,
        "owner_decision_packet_requirement": _owner_decision_packet_requirement(
            mission_objective=mission_objective,
            current_blocker=current_blocker,
            current_work_unit=current_work_unit,
            typed_blocker=typed_blocker,
            route_back_checklist=route_back_checklist,
        ),
        "platform_diagnostics": platform_diagnostics,
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
            "platform_diagnostics_count_as_paper_progress": False,
        },
        "authority_boundary": _authority_boundary(),
        "platform_diagnostics": platform_diagnostics,
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


def _source_ref_payloads(refs: list[str]) -> list[dict[str, str]]:
    payloads = [
        {
            "ref_id": f"source_ref::{index}",
            "ref_kind": _ref_kind(ref),
            "uri": ref,
        }
        for index, ref in enumerate(refs, start=1)
    ]
    if payloads:
        return payloads
    return [
        {
            "ref_id": "source_ref::missing",
            "ref_kind": "missing_readback_ref",
            "uri": "mission://source-refs/missing",
        }
    ]


def _paper_audit_pack(
    *,
    study_id: str,
    objective_id: str,
    objective_kind: str,
    artifact_refs: list[str],
    source_refs: list[dict[str, str]],
    readback: Mapping[str, Any],
    current_blocker: Mapping[str, Any],
    platform_diagnostics: Mapping[str, Any],
    legacy_import: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    legacy = _mapping(legacy_import)
    family_refs = {
        "analysis_rationale_log": _audit_refs(
            family="analysis_rationale_log",
            refs=[
                f"mission://{study_id}/objective/{objective_id}",
                f"mission://{study_id}/readback/{_text(readback.get('surface_kind')) or 'paper_mission_readback'}",
            ],
        ),
        "decision_trace": _audit_refs(
            family="decision_trace",
            refs=_dedupe(
                [
                    f"mission://{study_id}/decision/{objective_kind}",
                    _text(current_blocker.get("source_ref")) or "",
                    _text(current_blocker.get("work_unit_id")) or "",
                ]
            ),
        ),
        "evidence_ledger_delta": _audit_refs(
            family="evidence_ledger_delta",
            refs=_dedupe(
                _text_items(legacy.get("evidence_and_review_ledger_refs"))
                + [item["uri"] for item in source_refs]
            ),
        ),
        "review_ledger_delta": _audit_refs(
            family="review_ledger_delta",
            refs=_dedupe(
                _text_items(legacy.get("legacy_owner_state_refs"))
                + [
                    f"mission://{study_id}/quality-audit/{objective_id}",
                    f"mission://{study_id}/authority-boundary/no-write",
                ]
            ),
        ),
        "revision_log_delta": _audit_refs(
            family="revision_log_delta",
            refs=[
                f"mission://{study_id}/revision-log/{objective_id}",
                f"mission://{study_id}/paper-progress/no-write-import",
            ],
        ),
        "failed_path_ledger": _audit_refs(
            family="failed_path_ledger",
            refs=_dedupe(
                [
                    _text(current_blocker.get("blocker_id")) or "",
                    _text(current_blocker.get("status")) or "",
                    f"mission://{study_id}/failed-path/legacy-owner-callable-not-authority",
                ]
            ),
        ),
        "artifact_lineage": _audit_refs(
            family="artifact_lineage",
            refs=_dedupe(
                artifact_refs
                + _text_items(legacy.get("current_artifact_refs"))
                + [f"mission://{study_id}/candidate/{objective_id}"]
            ),
        ),
        "reproducibility_refs": _audit_refs(
            family="reproducibility_refs",
            refs=_dedupe(
                _text_items(legacy.get("opl_current_control_refs"))
                + [
                    _text(platform_diagnostics.get("domain_diagnostic_scanned_at")) or "",
                    f"mission://{study_id}/runtime-diagnostics/read-only",
                ]
            ),
        ),
    }
    return {
        family: {
            "status": "candidate_ref_chain",
            "refs": refs,
        }
        for family, refs in family_refs.items()
    }


def _audit_refs(*, family: str, refs: list[str]) -> list[dict[str, str]]:
    clean_refs = _dedupe([ref for ref in refs if ref])
    if not clean_refs:
        clean_refs = [f"mission://audit-pack/{family}/missing"]
    return [
        {
            "ref_id": f"{family}::{index}",
            "ref_kind": _ref_kind(ref),
            "uri": ref,
        }
        for index, ref in enumerate(clean_refs, start=1)
    ]


def _authority_touchpoints(
    *,
    study_id: str,
    source_refs: list[dict[str, str]],
    platform_diagnostics: Mapping[str, Any],
) -> list[dict[str, str]]:
    touchpoints = [
        {
            "touchpoint_id": f"touchpoint::{study_id}::study-progress",
            "owner": "MedAutoScience",
            "surface": "study progress",
            "status": "read_only",
        },
        {
            "touchpoint_id": f"touchpoint::{study_id}::runtime-readback",
            "owner": "MedAutoScience",
            "surface": "runtime readback",
            "status": "read_only"
            if platform_diagnostics.get("runtime_readback_available")
            else "not_touched",
        },
        {
            "touchpoint_id": f"touchpoint::{study_id}::mas-authority-kernel",
            "owner": "MedAutoScience",
            "surface": "MAS Authority Kernel",
            "status": "not_touched",
        },
        {
            "touchpoint_id": f"touchpoint::{study_id}::opl-runtime",
            "owner": "one-person-lab",
            "surface": "OPL runtime/current-control",
            "status": "read_only"
            if platform_diagnostics.get("runtime_readback_available")
            else "not_touched",
        },
    ]
    for source_ref in source_refs:
        kind = source_ref["ref_kind"]
        if kind in {"publication_eval", "controller_decision", "owner_answer"}:
            touchpoints.append(
                {
                    "touchpoint_id": f"touchpoint::{study_id}::{kind}",
                    "owner": "MedAutoScience",
                    "surface": kind,
                    "status": "read_only",
                }
            )
    return touchpoints


def _ref_kind(ref: str) -> str:
    if "publication_eval/latest.json" in ref:
        return "publication_eval"
    if "controller_decisions/latest.json" in ref:
        return "controller_decision"
    if "runtime_readback" in ref:
        return "runtime_readback"
    if "runtime_status_summary.json" in ref:
        return "runtime_status_summary"
    if "closeout" in ref or "owner_answer" in ref:
        return "owner_answer"
    if ref.startswith("supervisor-decision::"):
        return "supervisor_decision"
    if ref.startswith("provider_admission_pending_count="):
        return "provider_admission_readback"
    return "artifact_ref"


def _touchpoints(
    *,
    progress: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_owner_action: Mapping[str, Any],
    execution_envelope: Mapping[str, Any],
    route_back_checklist: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "study_progress": {
            "generated_at": _text(progress.get("generated_at")),
            "truth_epoch": _text(progress.get("truth_epoch")),
            "runtime_health_epoch": _text(progress.get("runtime_health_epoch")),
            "study_root": _text(progress.get("study_root")),
            "quest_root": _text(progress.get("quest_root")),
            "why_not_progressing": _text(progress.get("why_not_progressing")),
        },
        "current_work_unit": _compact_mapping(
            current_work_unit,
            (
                "status",
                "owner",
                "action_type",
                "work_unit_id",
                "work_unit_fingerprint",
                "action_fingerprint",
            ),
        ),
        "current_executable_owner_action": _compact_mapping(
            current_owner_action,
            (
                "status",
                "next_owner",
                "action_type",
                "work_unit_id",
                "work_unit_fingerprint",
                "action_fingerprint",
                "required_delta_kind",
            ),
        ),
        "current_execution_envelope": _compact_mapping(
            execution_envelope,
            (
                "state_kind",
                "owner",
                "next_work_unit",
            ),
        ),
        "route_back_checklist": _compact_mapping(
            route_back_checklist,
            (
                "route_back_required",
                "decision_type",
                "route_target",
                "owner",
                "handoff_source",
            ),
        ),
    }


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


def _candidate_requested_outcome(
    *,
    current_blocker: Mapping[str, Any],
    requirement: Mapping[str, Any],
) -> str:
    if current_blocker.get("status") == "typed_blocker":
        return "typed_blocker_required"
    accepted = _text_items(requirement.get("accepted_terminal_results"))
    if "route_back" in accepted:
        return "route_back"
    return "accepted_candidate"


def _candidate_outcome_request_payload(
    *,
    selected_outcome: str,
    candidate_id: str,
    current_blocker: Mapping[str, Any],
    requirement: Mapping[str, Any],
) -> dict[str, Any]:
    if selected_outcome == "typed_blocker_required":
        return {
            "typed_blocker_request": {
                "blocker_id": _text(current_blocker.get("blocker_id"))
                or "paper_mission_typed_blocker_requested",
                "blocker_ref": _text(requirement.get("existing_owner_answer_ref"))
                or f"typed-blocker-request:{candidate_id}",
                "next_owner": _text(current_blocker.get("owner")) or "mas_authority_kernel",
                "resume_condition": (
                    "MAS authority kernel materializes or rejects the typed blocker request"
                ),
            }
        }
    if selected_outcome == "human_gate_required":
        return {
            "human_gate_request": {
                "decision_packet_ref": f"human-gate-request:{candidate_id}",
                "next_owner": "human_owner",
                "resume_condition": "human decision ref is returned to MAS authority kernel",
            }
        }
    if selected_outcome == "route_back":
        return {
            "route_back_reason_code": (
                _text(current_blocker.get("blocker_id"))
                or "paper_mission_owner_packet_requires_revision"
            ),
            "route_back_resume_condition": (
                "mission executor revises the paper-facing candidate with current work-unit "
                "identity, artifact refs, source refs, and forbidden-write acknowledgement"
            ),
        }
    if selected_outcome == "rejected_candidate":
        return {
            "rejection_reason_code": "paper_mission_candidate_rejected_by_canary_policy",
            "rejection_resume_condition": "mission executor submits a corrected candidate",
        }
    return {}


def _one_shot_required_output(
    *,
    mission_objective: Mapping[str, Any],
    legacy_import: Mapping[str, Any],
    current_blocker: Mapping[str, Any],
) -> dict[str, Any]:
    constraints = _mapping(legacy_import.get("decision_constraints"))
    accepted = _text_items(constraints.get("candidate_can_be")) or [
        "accepted_owner_decision_packet",
        "route_back",
        "human_gate",
        "stable_typed_blocker",
    ]
    return {
        "kind": "owner_decision_packet_or_consumable_artifact_delta",
        "objective_id": _text(mission_objective.get("objective_id")),
        "objective_kind": _text(mission_objective.get("objective_kind")),
        "target_delta": _text(mission_objective.get("target_delta")),
        "next_owner": _text(current_blocker.get("owner")) or "mas_authority_kernel",
        "work_unit_id": _text(current_blocker.get("work_unit_id")),
        "accepted_terminal_results": accepted,
        "must_include": [
            "legacy_truth_import_pack",
            "current_artifact_refs",
            "publication_eval_refs",
            "controller_decision_refs",
            "evidence_and_review_ledger_refs",
            "legacy_owner_state_refs",
            "opl_current_control_refs",
            "forbidden_write_acknowledgement",
        ],
    }


def _mission_state_for_consume_status(status: str) -> str:
    if status == "accepted":
        return "consumed"
    if status == "typed_blocker":
        return "stable_blocker"
    if status == "human_gate":
        return "waiting_human_decision"
    if status == "route_back":
        return "route_back"
    return "candidate_ready_for_consumption"


def _paper_mission_transaction_payload(
    *,
    mission: Mapping[str, Any],
    readback: Mapping[str, Any],
    consume_result: Mapping[str, Any],
) -> dict[str, Any]:
    current_mission = _mapping(readback.get("current_mission"))
    required_output = _mapping(readback.get("required_output"))
    mission_objective = _mapping(readback.get("mission_objective"))
    stage_id = _first_text((
        current_mission.get("objective_kind"),
        required_output.get("objective_kind"),
        mission_objective.get("objective_kind"),
        "paper_mission_stage",
    ))
    mission_id = _text(mission.get("mission_id")) or "paper-mission::unknown"
    study_id = _text(mission.get("study_id")) or "unknown_study"
    stage_run_ref = f"opl-stage-run://paper-mission-carrier/{study_id}/{stage_id}/{mission_id}"
    enriched_consume_result = _transaction_consume_result(
        consume_result=consume_result,
        readback=readback,
    )
    terminal_decision = stage_terminal_decision_for_consume_result(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        consume_result=enriched_consume_result,
        default_next_owner=_first_text((
            required_output.get("next_owner"),
            readback.get("next_owner"),
            "mas_authority_kernel",
        )),
        default_next_stage_id=_next_stage_id_for_terminal_decision(
            stage_id=stage_id,
            required_output=required_output,
        ),
        default_next_work_unit=_first_text((
            required_output.get("work_unit_id"),
            current_mission.get("objective_id"),
            stage_id,
        )),
        default_reason=_terminal_decision_reason(
            consume_result=enriched_consume_result,
            readback=readback,
        ),
    )
    return build_paper_mission_transaction(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        stage_run_ref=stage_run_ref,
        terminal_decision=terminal_decision,
        artifact_delta_refs=_transaction_artifact_delta_refs(mission),
        paper_audit_pack_refs=_transaction_audit_pack_refs(mission),
        idempotency_basis=_first_text((
            enriched_consume_result.get("outcome"),
            enriched_consume_result.get("status"),
            stage_id,
        )),
    )


def _transaction_consume_result(
    *,
    consume_result: Mapping[str, Any],
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    enriched = dict(consume_result)
    consume_readback = _mapping(readback.get("consume_candidate_readback"))
    if not enriched.get("resume_condition"):
        enriched["resume_condition"] = _first_text((
            consume_readback.get("resume_condition"),
            _mapping(consume_readback.get("route_back")).get("resume_condition"),
            _mapping(consume_readback.get("typed_blocker_required")).get("resume_condition"),
            _mapping(consume_readback.get("human_gate_required")).get("resume_condition"),
        ))
    typed_blocker = _mapping(consume_readback.get("typed_blocker_required"))
    if typed_blocker:
        enriched["blocker_id"] = _first_text((
            typed_blocker.get("blocker_id"),
            enriched.get("blocker_id"),
        ))
        enriched["unblock_condition"] = _first_text((
            typed_blocker.get("resume_condition"),
            enriched.get("unblock_condition"),
            enriched.get("resume_condition"),
        ))
    human_gate = _mapping(consume_readback.get("human_gate_required"))
    if human_gate:
        enriched["question"] = _first_text((
            human_gate.get("question"),
            enriched.get("question"),
        ))
        enriched["required_receipt"] = _first_text((
            human_gate.get("decision_packet_ref"),
            enriched.get("required_receipt"),
        ))
    return enriched


def _terminal_decision_reason(
    *,
    consume_result: Mapping[str, Any],
    readback: Mapping[str, Any],
) -> str:
    return _first_text((
        consume_result.get("reason"),
        consume_result.get("outcome"),
        readback.get("consume_candidate_status"),
        "mas_stage_terminalized_from_paper_mission_candidate",
    ))


def _next_stage_id_for_terminal_decision(
    *,
    stage_id: str,
    required_output: Mapping[str, Any],
) -> str:
    objective_kind = _text(required_output.get("objective_kind")) or stage_id
    if objective_kind == "gate_clearing_claim_evidence_repair":
        return "publication_gate_replay"
    if objective_kind == "medical_prose_write_repair_publication_gate_replay":
        return "publication_quality_recheck"
    return f"{stage_id}::next"


def _transaction_artifact_delta_refs(mission: Mapping[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for index, delta in enumerate(_mapping_list(mission.get("artifact_delta_ledger")), start=1):
        uri = _text(delta.get("artifact_ref"))
        if not uri:
            continue
        refs.append(
            {
                "ref_id": _text(delta.get("delta_id")) or f"artifact_delta::{index}",
                "ref_kind": _text(delta.get("delta_kind")) or "artifact_delta",
                "uri": uri,
            }
        )
    if refs:
        return refs
    return [
        {
            "ref_id": "artifact_delta::missing",
            "ref_kind": "missing_artifact_delta",
            "uri": "mission://artifact-delta/missing",
        }
    ]


def _transaction_audit_pack_refs(mission: Mapping[str, Any]) -> dict[str, list[dict[str, str]]]:
    audit_pack = _mapping(mission.get("paper_audit_pack"))
    refs_by_family: dict[str, list[dict[str, str]]] = {}
    for family in _PAPER_AUDIT_PACK_FAMILIES:
        family_payload = _mapping(audit_pack.get(family))
        refs = [
            {
                "ref_id": _text(ref.get("ref_id")) or f"{family}::{index}",
                "ref_kind": _text(ref.get("ref_kind")) or "artifact_ref",
                "uri": _text(ref.get("uri")) or f"mission://audit-pack/{family}/missing",
            }
            for index, ref in enumerate(_mapping_list(family_payload.get("refs")), start=1)
        ]
        if not refs:
            refs = [
                {
                    "ref_id": f"{family}::missing",
                    "ref_kind": "missing_audit_ref",
                    "uri": f"mission://audit-pack/{family}/missing",
                }
            ]
        refs_by_family[family] = refs
    return refs_by_family


def _refs_with_kinds(refs: list[str], kinds: set[str]) -> list[str]:
    return [ref for ref in refs if _ref_kind(ref) in kinds]


def _platform_count(domain_diagnostic: Mapping[str, Any], key: str) -> int:
    provider_state = _mapping(domain_diagnostic.get("provider_admission_current_control_state"))
    return _int_or_zero(provider_state.get(key))


def _progress_payloads_by_study(
    payloads: Mapping[str, Any] | Iterable[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    if isinstance(payloads, Mapping) and isinstance(payloads.get("study_id"), str):
        study_id = str(payloads["study_id"])
        return {study_id: payloads}
    if isinstance(payloads, Mapping):
        by_study: dict[str, Mapping[str, Any]] = {}
        for key, value in payloads.items():
            mapping = _mapping(value)
            study_id = _text(mapping.get("study_id")) or str(key)
            by_study[study_id] = mapping
        return by_study
    by_study = {}
    for payload in payloads:
        mapping = _mapping(payload)
        study_id = _text(mapping.get("study_id"))
        if not study_id:
            raise ValueError("study progress payload missing study_id")
        by_study[study_id] = mapping
    return by_study


def _authority_boundary() -> dict[str, Any]:
    return {
        "write_mode": "no_write",
        "can_write_yang_workspace": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
        "can_write_current_package": False,
        "can_write_runtime_queue_or_provider_attempt": False,
        "forbidden_writes": list(_FORBIDDEN_WRITES),
    }


def _compact_mapping(payload: Mapping[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in keys:
        if key in payload:
            result[key] = payload[key]
    return result


def _work_unit_ids(items: object) -> list[str]:
    ids: list[str] = []
    for item in _mapping_list(items):
        ids.extend(_text_items((item.get("unit_id"), item.get("work_unit_id"))))
    return _dedupe(ids)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [_mapping(item) for item in value if isinstance(item, Mapping)]


def _first_mapping(*values: object) -> dict[str, Any]:
    for value in values:
        mapping = _mapping(value)
        if mapping:
            return mapping
    return {}


def _text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, Iterable):
        return []
    items: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            items.append(item.strip())
    return items


def _first_text(values: Iterable[object]) -> str | None:
    for value in values:
        text = _text(value)
        if text:
            return text
    return None


def _first_non_empty(*values: object) -> str | None:
    return _first_text(values)


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _int_or_zero(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return 0
