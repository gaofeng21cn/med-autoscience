from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_authority import consume_paper_mission_candidate
from med_autoscience.paper_mission_parts.authority_boundary import (
    FORBIDDEN_AUTHORITY_CLAIMS,
    FORBIDDEN_WRITES,
    authority_boundary,
)
from med_autoscience.paper_mission_parts.payload_helpers import (
    dedupe,
    mapping,
    mapping_list,
    text,
    text_items,
)


def paper_mission_canary_candidate_manifest(
    mission: Mapping[str, Any],
    *,
    requested_outcome: str | None = None,
) -> dict[str, Any]:
    readback = mapping(mission.get("canary_import_readback"))
    mission_objective = mapping(readback.get("mission_objective"))
    current_blocker = mapping(readback.get("current_blocker"))
    requirement = mapping(readback.get("owner_decision_packet_requirement"))
    selected_outcome = requested_outcome or _candidate_requested_outcome(
        current_blocker=current_blocker,
        requirement=requirement,
    )
    candidate_id = (
        "paper-mission-candidate::"
        f"{text(mission.get('study_id')) or 'unknown-study'}::"
        f"{text(mission_objective.get('objective_id')) or 'canary-import'}"
    )
    source_refs = mapping_list(mission.get("source_refs"))
    source_uris = [text(source_ref.get("uri")) for source_ref in source_refs]
    source_readiness_refs = dedupe(
        [
            item
            for item in (
                [
                    f"study-progress:{text(mission.get('study_id')) or 'unknown-study'}",
                    f"mission-objective:{text(mission_objective.get('objective_id')) or 'unknown'}",
                ]
                + [uri for uri in source_uris if uri]
            )
            if item
        ]
    )
    return {
        "candidate_id": candidate_id,
        "mission_id": text(mission.get("mission_id")) or "unknown_mission",
        "study_id": text(mission.get("study_id")) or "unknown_study",
        "requested_outcome": selected_outcome,
        "candidate_manifest_ref": f"mission://{candidate_id}/manifest.json",
        "candidate_artifact_refs": [
            text(item.get("artifact_ref"))
            for item in mapping_list(mission.get("artifact_delta_ledger"))
            if text(item.get("artifact_ref"))
        ],
        "source_readiness_refs": source_readiness_refs,
        "quality_auditor_requirement": {
            "independent_auditor_required": True,
            "owner": "MedAutoScience",
            "requirement_ref": (
                "paper-mission-quality-audit::"
                f"{text(mission.get('study_id')) or 'unknown-study'}::"
                f"{text(mission_objective.get('objective_id')) or 'canary-import'}"
            ),
        },
        "artifact_authority_boundary": {
            "artifact_authority_owner": "MedAutoScience",
            "candidate_is_authority": False,
            "can_update_current_package": False,
            "can_write_paper_body": False,
        },
        "next_owner": text(requirement.get("owner"))
        or text(current_blocker.get("owner"))
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
    readback = mapping(mission.get("one_shot_migration_readback"))
    legacy = mapping(readback.get("legacy_truth_import_pack"))
    required_output = mapping(readback.get("required_output"))
    current_mission = mapping(readback.get("current_mission"))
    deltas = mapping_list(mission.get("artifact_delta_ledger"))
    delta = deltas[0] if deltas else {}
    return {
        "surface_kind": "paper_mission_candidate_artifact_delta",
        "schema_version": 1,
        "study_id": text(mission.get("study_id")) or "unknown_study",
        "mission_id": text(mission.get("mission_id")) or "unknown_mission",
        "delta_id": text(delta.get("delta_id"))
        or f"delta::{text(mission.get('study_id')) or 'unknown-study'}::candidate",
        "artifact_ref": text(delta.get("artifact_ref"))
        or f"mission://{text(mission.get('study_id')) or 'unknown-study'}/candidate",
        "delta_kind": text(delta.get("delta_kind"))
        or "formal_paper_mission_owner_decision_packet",
        "status": text(delta.get("status")) or "candidate",
        "counts_as_paper_progress": True,
        "candidate_is_authority": False,
        "current_mission": dict(current_mission),
        "objective_kind": text(current_mission.get("objective_kind")),
        "required_output": dict(required_output),
        "source_ref_families": {
            "current_artifact_refs": text_items(legacy.get("current_artifact_refs")),
            "publication_eval_refs": text_items(legacy.get("publication_eval_refs")),
            "controller_decision_refs": text_items(legacy.get("controller_decision_refs")),
            "evidence_and_review_ledger_refs": text_items(
                legacy.get("evidence_and_review_ledger_refs")
            ),
            "legacy_owner_state_refs": text_items(legacy.get("legacy_owner_state_refs")),
            "opl_current_control_refs": text_items(legacy.get("opl_current_control_refs")),
        },
        "forbidden_write_acknowledgement": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "forbidden_writes": list(FORBIDDEN_WRITES),
            "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        },
        "authority_boundary": authority_boundary(),
    }


def paper_mission_owner_decision_packet(mission: Mapping[str, Any]) -> dict[str, Any]:
    readback = mapping(mission.get("one_shot_migration_readback"))
    legacy = mapping(readback.get("legacy_truth_import_pack"))
    required_output = mapping(readback.get("required_output"))
    decision_constraints = mapping(readback.get("decision_constraints"))
    artifact_delta = paper_mission_candidate_artifact_delta(mission)
    return {
        "surface_kind": "paper_mission_owner_decision_packet",
        "schema_version": 1,
        "study_id": artifact_delta["study_id"],
        "mission_id": artifact_delta["mission_id"],
        "packet_id": f"owner-decision::{artifact_delta['study_id']}::{artifact_delta['delta_id']}",
        "packet_status": "candidate_ready_for_mas_consume",
        "candidate_is_authority": False,
        "next_owner": text(required_output.get("next_owner")) or "mas_authority_kernel",
        "required_output_kind": text(required_output.get("kind"))
        or "owner_decision_packet_or_consumable_artifact_delta",
        "accepted_terminal_results": text_items(
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
        "legacy_constraints": mapping(legacy.get("legacy_constraints")),
        "decision_constraints": decision_constraints,
        "non_degradation_evidence": mapping(legacy.get("non_degradation_evidence")),
        "forbidden_write_acknowledgement": artifact_delta[
            "forbidden_write_acknowledgement"
        ],
        "authority_boundary": authority_boundary(),
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
        "study_id": text(mission.get("study_id")) or "unknown_study",
        "mission_id": text(mission.get("mission_id")) or "unknown_mission",
        "candidate_manifest": candidate,
        "authority_consume_readback": consume_paper_mission_candidate(candidate),
    }


def one_shot_required_output(
    *,
    mission_objective: Mapping[str, Any],
    legacy_import: Mapping[str, Any],
    current_blocker: Mapping[str, Any],
) -> dict[str, Any]:
    constraints = mapping(legacy_import.get("decision_constraints"))
    accepted = text_items(constraints.get("candidate_can_be")) or [
        "accepted_owner_decision_packet",
        "route_back",
        "human_gate",
        "stable_typed_blocker",
    ]
    return {
        "kind": "owner_decision_packet_or_consumable_artifact_delta",
        "objective_id": text(mission_objective.get("objective_id")),
        "objective_kind": text(mission_objective.get("objective_kind")),
        "target_delta": text(mission_objective.get("target_delta")),
        "next_owner": text(current_blocker.get("owner")) or "mas_authority_kernel",
        "work_unit_id": text(current_blocker.get("work_unit_id")),
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


def mission_state_for_consume_status(status: str) -> str:
    if status == "accepted":
        return "consumed"
    if status == "typed_blocker":
        return "stable_blocker"
    if status == "human_gate":
        return "waiting_human_decision"
    if status == "route_back":
        return "route_back"
    return "candidate_ready_for_consumption"


def _candidate_requested_outcome(
    *,
    current_blocker: Mapping[str, Any],
    requirement: Mapping[str, Any],
) -> str:
    if current_blocker.get("status") == "typed_blocker":
        return "typed_blocker_required"
    accepted = text_items(requirement.get("accepted_terminal_results"))
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
                "blocker_id": text(current_blocker.get("blocker_id"))
                or "paper_mission_typed_blocker_requested",
                "blocker_ref": text(requirement.get("existing_owner_answer_ref"))
                or f"typed-blocker-request:{candidate_id}",
                "next_owner": text(current_blocker.get("owner")) or "mas_authority_kernel",
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
                text(current_blocker.get("blocker_id"))
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
