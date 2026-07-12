from __future__ import annotations

from med_autoscience.paper_mission_candidate_package import (
    AI_OWNER_DECISION_SIDECAR_REFS,
    REQUIRED_AUTHORITY_MATERIALIZATION_REFS,
    REQUIRED_QUALITY_GATE_REFS,
    paper_mission_owner_blocker_packet,
    paper_mission_owner_consumption_request,
    paper_mission_submission_milestone_checklist,
)


def test_submission_milestone_checklist_exposes_pending_owner_authority_refs() -> None:
    checklist = paper_mission_submission_milestone_checklist(
        output_kinds=[
            "manuscript_patch_plan",
            "reviewer_gate_response_draft",
            "owner_decision_packet",
        ],
        owner_blocker_context=True,
    )

    assert checklist["authority_materialized"] is False
    assert {
        item["ref_kind"]
        for item in checklist["required_authority_materialization_refs"]
    } == set(REQUIRED_AUTHORITY_MATERIALIZATION_REFS)
    assert {
        item["ref_kind"] for item in checklist["required_quality_gate_refs"]
    } == set(REQUIRED_QUALITY_GATE_REFS)
    assert all(
        item["candidate_package_can_satisfy_without_authority"] is False
        for item in checklist["required_authority_materialization_refs"]
    )


def test_owner_packets_keep_authority_and_reviewer_gaps_explicit() -> None:
    readback = {
        "study_id": "study-1",
        "mission_id": "mission-1",
        "stage_terminal_decision": {
            "decision_kind": "typed_blocker",
            "status": "blocked",
            "reason": "missing_opl_runtime_readback",
            "blocker_id": "typed-blocker:demo",
        },
        "ai_route_context": {
            "command_kind": "stop_with_typed_blocker",
            "target": "one-person-lab",
        },
        "next_owner_or_human_decision": {"next_owner": "one-person-lab"},
        "opl_stage_attempt_readback_status": "optional_stage_attempt_readback_missing",
    }
    summary = {"next_owner": "one-person-lab"}
    handoff = {"status": "not_routed_to_mission_executor"}

    owner_blocker = paper_mission_owner_blocker_packet(
        readback=readback,
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=handoff,
        forbidden_authority_writes=["owner_receipt"],
        forbidden_authority_claims=["publication_ready"],
    )
    owner_request = paper_mission_owner_consumption_request(
        readback=readback,
        candidate_manifest={"next_owner": "one-person-lab"},
        owner_decision_packet={"packet_id": "packet-1"},
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=handoff,
        paper_facing_candidate_delta={"status": "candidate_ready"},
        owner_blocker_packet=owner_blocker,
        candidate_refs={"package_manifest": "candidate_manifest.json"},
        forbidden_authority_writes=["owner_receipt"],
        forbidden_authority_claims=["publication_ready"],
    )

    assert owner_blocker["authority_materialized"] is False
    assert owner_blocker["typed_blocker_authority_materialized"] is False
    assert owner_blocker["human_gate_materialized"] is False
    assert {
        item["ref_kind"]
        for item in owner_blocker["required_authority_materialization_refs"]
    } == set(REQUIRED_AUTHORITY_MATERIALIZATION_REFS)
    assert {
        item["ref_kind"] for item in owner_blocker["required_quality_gate_refs"]
    } == set(REQUIRED_QUALITY_GATE_REFS)
    assert owner_request["consume_path"][
        "authority_materialized_by_this_request"
    ] is False
    assert set(
        owner_request["consume_path"]["required_authority_materialization_refs"]
    ) == set(REQUIRED_AUTHORITY_MATERIALIZATION_REFS)
    assert set(owner_request["consume_path"]["required_quality_gate_refs"]) == set(
        REQUIRED_QUALITY_GATE_REFS
    )


def test_route_back_owner_fallback_exposes_ai_owner_decision_sidecars() -> None:
    readback = {
        "study_id": "study-1",
        "mission_id": "mission-1",
        "stage_terminal_decision": {
            "decision_kind": "route_back",
            "status": "route_back",
            "reason": "claim_evidence_alignment_gap",
            "route_back_evidence_ref": "route-back:study-1:mission-1",
            "target_stage_id": "paper-write",
        },
        "ai_route_context": {
            "command_kind": "route_back",
            "target": "mission_executor",
        },
        "next_owner_or_human_decision": {
            "next_owner": "mission_executor",
            "route_back_evidence_ref": "route-back:study-1:mission-1",
        },
        "opl_stage_attempt_readback_status": "route_back",
    }
    summary = {
        "next_owner": "mission_executor",
        "blocked_reason": "claim_evidence_alignment_gap",
    }
    handoff = {"status": "ready_for_mission_executor"}

    owner_blocker = paper_mission_owner_blocker_packet(
        readback=readback,
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=handoff,
        forbidden_authority_writes=["owner_receipt"],
        forbidden_authority_claims=["publication_ready"],
    )
    owner_request = paper_mission_owner_consumption_request(
        readback=readback,
        candidate_manifest={"next_owner": "mission_executor"},
        owner_decision_packet={"packet_id": "packet-1"},
        foreground_owner_decision_summary=summary,
        mission_executor_handoff=handoff,
        paper_facing_candidate_delta={"status": "candidate_ready"},
        owner_blocker_packet=owner_blocker,
        candidate_refs={"package_manifest": "package_manifest.json"},
        forbidden_authority_writes=["owner_receipt"],
        forbidden_authority_claims=["publication_ready"],
    )

    assert owner_blocker["ai_owner_decision_sidecar_refs"] == (
        AI_OWNER_DECISION_SIDECAR_REFS
    )
    assert owner_request["ai_owner_decision_sidecar_refs"] == (
        AI_OWNER_DECISION_SIDECAR_REFS
    )
    assert owner_request["consume_path"]["ai_owner_decision_sidecar_refs"] == (
        AI_OWNER_DECISION_SIDECAR_REFS
    )
    sidecars = owner_request["ai_owner_decision_sidecars"]
    assert set(sidecars) == set(AI_OWNER_DECISION_SIDECAR_REFS)
    assert all(
        item["candidate_is_authority"] is False
        and item["authority_materialized"] is False
        and item["authority_boundary"]["writes_authority"] is False
        and item["authority_boundary"]["writes_runtime"] is False
        for item in sidecars.values()
    )
    assert sidecars["claim_strength_adjustment"]["decision_kind"] == (
        "claim_strength_adjustment"
    )
    assert sidecars["scope_reduction"]["decision_kind"] == "scope_reduction"
    assert sidecars["evidence_substitution"]["decision_kind"] == (
        "evidence_substitution"
    )
    assert sidecars["research_pivot"]["decision_kind"] == "research_pivot"
    assert sidecars["carry_forward_risk_receipt"]["decision_kind"] == (
        "carry_forward_risk_receipt"
    )
    assert sidecars["carry_forward_risk_receipt"]["receipt_ref"] == (
        owner_request["carry_forward_risk_receipt"]["receipt_ref"]
    )
