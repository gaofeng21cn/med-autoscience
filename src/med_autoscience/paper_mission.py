from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.paper_mission_authority import consume_paper_mission_candidate
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
        "objective_id": "dm003_medical_prose_write_repair",
        "objective_kind": "medical_prose_write_repair",
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
    domain_health_diagnostic_payload: Mapping[str, Any] | None = None,
    profile_ref: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    progress_by_study = _progress_payloads_by_study(study_progress_payloads)
    dhd = _mapping(domain_health_diagnostic_payload)
    mission_payloads = [
        _build_mission(
            study_id=study_id,
            progress=progress,
            dhd=dhd,
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
            "domain_health_diagnostic": {
                "available": bool(dhd),
                "scanned_at": _text(dhd.get("scanned_at")),
                "dry_run_written": bool(dhd.get("written")),
            },
        },
        "paper_progress_accounting": {
            "import_pack_counts_as_paper_progress": False,
            "dhd_diagnostics_count_as_paper_progress": False,
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
    domain_health_diagnostic_payload: Mapping[str, Any] | None = None,
    profile_ref: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    return build_paper_mission_canary_import_pack(
        study_progress_payloads=(dm002_progress, dm003_progress),
        domain_health_diagnostic_payload=domain_health_diagnostic_payload,
        profile_ref=profile_ref,
        generated_at=generated_at,
    )


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


def _build_mission(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    dhd: Mapping[str, Any],
) -> dict[str, Any]:
    action = _dhd_action_for_study(dhd, study_id=study_id)
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
        _dhd_current_execution_envelope(dhd, study_id=study_id),
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
        dhd=dhd,
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
    return {
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
            "touchpoint_id": f"touchpoint::{study_id}::domain-health-diagnostic",
            "owner": "MedAutoScience",
            "surface": "domain-health-diagnostic dry-run",
            "status": "read_only"
            if platform_diagnostics.get("dhd_available")
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
            if platform_diagnostics.get("dhd_available")
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
    if "domain_health_diagnostic" in ref:
        return "domain_health_diagnostic"
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
    dhd: Mapping[str, Any],
) -> dict[str, Any]:
    provider_state = _mapping(dhd.get("provider_admission_current_control_state"))
    action_queue = _mapping_list(provider_state.get("action_queue"))
    envelopes = _mapping(provider_state.get("current_execution_envelopes"))
    return {
        "counts_as_paper_progress": False,
        "dhd_available": bool(dhd),
        "dhd_scanned_at": _text(dhd.get("scanned_at")),
        "dhd_written": bool(dhd.get("written")),
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


def _dhd_action_for_study(dhd: Mapping[str, Any], *, study_id: str) -> dict[str, Any]:
    for action in _mapping_list(dhd.get("managed_study_actions")):
        if action.get("study_id") == study_id:
            return action
    return {}


def _dhd_current_execution_envelope(
    dhd: Mapping[str, Any],
    *,
    study_id: str,
) -> dict[str, Any]:
    provider_state = _mapping(dhd.get("provider_admission_current_control_state"))
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
