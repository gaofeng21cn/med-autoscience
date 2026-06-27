from __future__ import annotations

import json
from pathlib import Path


def _base_candidate(**overrides):
    candidate = {
        "candidate_id": "pmc-001",
        "mission_id": "mission-001",
        "study_id": "study-001",
        "requested_outcome": "accepted_candidate",
        "candidate_manifest_ref": "artifacts/paper_mission/mission-001/candidates/pmc-001.json",
        "candidate_artifact_refs": [
            "artifacts/paper_mission/mission-001/candidates/patch_plan.md",
        ],
        "source_readiness_refs": [
            "source-readiness:study-001:20260623",
        ],
        "quality_auditor_requirement": {
            "independent_auditor_required": True,
            "owner": "MedAutoScience",
            "requirement_ref": "quality-auditor:study-001:mission-001",
        },
        "artifact_authority_boundary": {
            "artifact_authority_owner": "MedAutoScience",
            "candidate_is_authority": False,
            "can_update_current_package": False,
            "can_write_paper_body": False,
        },
        "next_owner": "mas_authority_kernel",
        "resume_condition": "independent auditor consumes the accepted mission candidate",
    }
    candidate.update(overrides)
    return candidate


def test_accepts_candidate_with_required_refs_and_no_authority_claims() -> None:
    from med_autoscience.paper_mission_authority import consume_paper_mission_candidate

    result = consume_paper_mission_candidate(_base_candidate())

    assert result["surface_kind"] == "mas_paper_mission_candidate_consume_readback"
    assert result["status"] == "accepted_candidate"
    assert result["selected_outcome"] == "accepted_candidate"
    assert result["consume_result"] == {
        "status": "accepted",
        "outcome": "accepted_candidate",
        "authority_materialized": False,
    }
    assert result["allowed_outcomes"] == [
        "accepted_candidate",
        "rejected_candidate",
        "route_back",
        "typed_blocker_required",
        "human_gate_required",
    ]
    assert result["accepted_candidate"] == {
        "candidate_id": "pmc-001",
        "mission_id": "mission-001",
        "study_id": "study-001",
        "candidate_manifest_ref": "artifacts/paper_mission/mission-001/candidates/pmc-001.json",
        "candidate_artifact_refs": [
            "artifacts/paper_mission/mission-001/candidates/patch_plan.md",
        ],
        "authority_materialized": False,
    }
    assert result["source_readiness_refs"] == ["source-readiness:study-001:20260623"]
    assert result["quality_auditor_requirement"]["independent_auditor_required"] is True
    assert result["artifact_authority_boundary"]["can_update_current_package"] is False
    assert result["next_owner"] == "mas_authority_kernel"
    assert result["resume_condition"] == (
        "independent auditor consumes the accepted mission candidate"
    )
    assert result["write_plan"]["written_files"] == []
    assert result["authority_boundary"]["can_write_owner_receipt"] is False
    assert result["authority_boundary"]["can_write_typed_blocker"] is False
    assert result["authority_boundary"]["can_write_current_package"] is False
    assert result["authority_boundary"]["can_authorize_publication_ready"] is False


def test_accepts_candidate_manifest_path_as_read_only_payload(tmp_path: Path) -> None:
    from med_autoscience.paper_mission_authority import consume_paper_mission_candidate

    manifest = tmp_path / "candidate.json"
    manifest.write_text(json.dumps(_base_candidate()), encoding="utf-8")

    result = consume_paper_mission_candidate(manifest)

    assert result["status"] == "accepted_candidate"
    assert result["selected_outcome"] == "accepted_candidate"
    assert result["consume_result"]["status"] == "accepted"
    assert result["candidate_manifest_input"]["path"] == str(manifest)
    assert result["candidate_manifest_input"]["loaded"] is True
    assert result["write_plan"]["written_files"] == []


def test_submission_milestone_package_acceptance_exposes_canonical_paper_delta(
    tmp_path: Path,
) -> None:
    from med_autoscience.paper_mission_authority import consume_paper_mission_candidate

    package_root = tmp_path / "package"
    package_root.mkdir()
    candidate_manifest = package_root / "candidate_manifest.json"
    paper_delta = package_root / "paper_facing_candidate_delta.json"
    candidate_manifest.write_text(
        json.dumps(
            _base_candidate(
                candidate_manifest_ref=str(candidate_manifest),
                candidate_artifact_refs=[str(paper_delta)],
            )
        ),
        encoding="utf-8",
    )
    paper_delta.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_paper_facing_candidate_delta",
                "candidate_is_authority": False,
            }
        ),
        encoding="utf-8",
    )
    package_manifest = package_root / "package_manifest.json"
    package_manifest.write_text(
        json.dumps(
            {
                "surface_kind": "paper_mission_foreground_candidate_package_manifest",
                "mode": "non_authority_candidate_package",
                "milestone_kind": "submission_milestone_candidate",
                "study_id": "study-001",
                "mission_id": "mission-001",
                "counts_as_paper_progress": True,
                "candidate_is_authority": False,
                "writes_authority": False,
                "writes_runtime": False,
                "writes_paper_body": False,
                "can_claim_submission_ready": False,
                "can_claim_publication_ready": False,
                "artifact_refs": {
                    "candidate_manifest": str(candidate_manifest),
                    "paper_facing_candidate_delta": str(paper_delta),
                },
                "paper_facing_candidate_delta_ref": str(paper_delta),
            }
        ),
        encoding="utf-8",
    )

    result = consume_paper_mission_candidate(package_manifest)

    assert result["status"] == "accepted_candidate"
    assert result["consume_result"]["status"] == "accepted"
    assert result["consume_result"]["canonical_paper_or_artifact_delta_ref"] == str(
        paper_delta
    )
    assert result["consume_result"]["paper_facing_delta_ref"] == str(paper_delta)
    assert result["consume_result"]["authority_materialized"] is False
    assert result["accepted_candidate"]["canonical_paper_or_artifact_delta_ref"] == str(
        paper_delta
    )
    assert result["authority_boundary"]["can_write_owner_receipt"] is False


def test_rejects_candidate_that_claims_publication_or_owner_authority() -> None:
    from med_autoscience.paper_mission_authority import consume_paper_mission_candidate

    result = consume_paper_mission_candidate(
        _base_candidate(
            publication_ready=True,
            owner_receipt_written=True,
            typed_blocker_written=True,
            current_package_updated=True,
        )
    )

    assert result["status"] == "rejected_candidate"
    assert result["consume_result"]["status"] == "rejected"
    assert result["consume_result"]["outcome"] == "rejected_candidate"
    assert result["rejected_candidate"]["reason_code"] == "forbidden_authority_claim"
    assert set(result["rejected_candidate"]["violations"]) == {
        "publication_ready",
        "owner_receipt_written",
        "typed_blocker_written",
        "current_package_updated",
    }
    assert result["accepted_candidate"] is None
    assert result["write_plan"]["written_files"] == []
    assert result["authority_boundary"]["can_write_publication_eval"] is False


def test_routes_back_candidate_with_authority_write_path_without_writing(tmp_path: Path) -> None:
    from med_autoscience.paper_mission_authority import consume_paper_mission_candidate

    forbidden_target = tmp_path / "artifacts" / "publication_eval" / "latest.json"
    result = consume_paper_mission_candidate(
        _base_candidate(
            requested_outcome="accepted_candidate",
            proposed_write_paths=[str(forbidden_target)],
        )
    )

    assert result["status"] == "route_back"
    assert result["consume_result"]["status"] == "route_back"
    assert result["consume_result"]["outcome"] == "route_back"
    assert result["route_back"]["reason_code"] == "forbidden_authority_write_path"
    assert result["route_back"]["next_owner"] == "mission_executor"
    assert result["route_back"]["resume_condition"] == (
        "remove forbidden authority write paths and resubmit as refs-only candidate"
    )
    assert result["forbidden_write_path_matches"][0]["category"] == "publication_eval_latest"
    assert not forbidden_target.exists()
    assert result["write_plan"]["written_files"] == []


def test_human_gate_required_is_allowed_but_not_materialized() -> None:
    from med_autoscience.paper_mission_authority import consume_paper_mission_candidate

    result = consume_paper_mission_candidate(
        _base_candidate(
            requested_outcome="human_gate_required",
            human_gate_request={
                "decision_packet_ref": "paper-mission:mission-001:human-decision",
                "question": "Should the current limitation be disclosed in the abstract?",
            },
        )
    )

    assert result["status"] == "human_gate_required"
    assert result["consume_result"]["status"] == "human_gate"
    assert result["consume_result"]["outcome"] == "human_gate_required"
    assert result["human_gate_required"] == {
        "candidate_id": "pmc-001",
        "materialized": False,
        "decision_packet_ref": "paper-mission:mission-001:human-decision",
        "next_owner": "human_owner",
        "resume_condition": "human decision ref is returned to MAS authority kernel",
    }
    assert result["write_plan"]["can_write_human_gate_authority_records"] is False


def test_typed_blocker_required_is_allowed_but_not_written() -> None:
    from med_autoscience.paper_mission_authority import consume_paper_mission_candidate

    result = consume_paper_mission_candidate(
        _base_candidate(
            requested_outcome="typed_blocker_required",
            typed_blocker_request={
                "blocker_id": "source_readiness_missing_raw_table",
                "blocker_ref": "typed-blocker-request:mission-001:source",
            },
        )
    )

    assert result["status"] == "typed_blocker_required"
    assert result["consume_result"]["status"] == "typed_blocker"
    assert result["consume_result"]["outcome"] == "typed_blocker_required"
    assert result["typed_blocker_required"] == {
        "candidate_id": "pmc-001",
        "materialized": False,
        "blocker_id": "source_readiness_missing_raw_table",
        "blocker_ref": "typed-blocker-request:mission-001:source",
        "next_owner": "mas_authority_kernel",
        "resume_condition": "MAS authority kernel records or rejects the typed blocker request",
    }
    assert result["write_plan"]["can_write_typed_blockers"] is False


def test_missing_non_degradation_fields_route_back_to_candidate_owner() -> None:
    from med_autoscience.paper_mission_authority import consume_paper_mission_candidate

    candidate = _base_candidate()
    candidate.pop("source_readiness_refs")
    candidate.pop("quality_auditor_requirement")

    result = consume_paper_mission_candidate(candidate)

    assert result["status"] == "route_back"
    assert result["consume_result"]["status"] == "route_back"
    assert result["consume_result"]["outcome"] == "route_back"
    assert result["route_back"]["reason_code"] == "missing_required_non_degradation_refs"
    assert result["route_back"]["missing_fields"] == [
        "source_readiness_refs",
        "quality_auditor_requirement",
    ]
    assert result["next_owner"] == "mission_executor"
    assert result["resume_condition"] == "supply missing mission authority refs and resubmit"
    assert result["write_plan"]["written_files"] == []


def test_terminal_owner_answer_materializes_paper_facing_delta_when_route_back_has_no_artifact_delta() -> None:
    from med_autoscience.paper_mission_owner_answer import (
        terminal_owner_gate_owner_answer_readback,
    )

    result = terminal_owner_gate_owner_answer_readback(
        terminal_owner_gate={
            "surface_kind": "paper_mission_terminal_owner_gate",
            "owner": "mas_authority_kernel",
            "gate_kind": "domain_gate",
            "blocked_reason": "domain_gate_pending",
            "closeout_ref": "closeout.json",
            "stage_attempt_id": "sat-terminal",
            "work_unit_id": "paper-stage::gate-clearing",
        },
        paper_mission_transaction={
            "transaction_id": "paper-mission-transaction::study-001::paper-stage::gate-clearing::mission-001",
            "mission_id": "mission-001",
            "study_id": "study-001",
            "stage_id": "paper-stage::gate-clearing",
            "stage_run_ref": "opl-stage-run://study-001/paper-stage::gate-clearing",
        },
        artifact_delta_refs=[],
        paper_audit_pack_refs=_paper_audit_pack_refs(),
    )

    assert result["status"] == "route_back"
    assert result["owner_answer_shape"] == "paper_facing_delta_ref"
    assert result["selected_outcome"] == "paper_facing_delta_ref"
    assert result["paper_facing_delta_ref"].startswith(
        "paper-facing-delta:owner-answer:study-001:"
    )
    transaction = result["paper_mission_transaction"]
    assert transaction["artifact_delta_refs"] == [
        {
            "ref_id": "paper_facing_delta_ref",
            "ref_kind": "paper_facing_delta_ref",
            "uri": result["paper_facing_delta_ref"],
        }
    ]
    assert result["consume_result"]["status"] == "route_back"
    assert result["consume_result"]["outcome"] == "paper_facing_delta_ref"
    assert result["route_back_budget"]["opl_redrive_budget_remaining"] == 0
    assert result["route_back_budget"]["next_mode"] == (
        "mas_mission_executor_fallback"
    )
    assert result["semantic_progress_signature"]["identity"]["study_id"] == "study-001"
    assert result["mission_executor_fallback_action"]["default_action"] == (
        "materialize_submission_milestone_candidate"
    )
    assert result["mission_executor_fallback_action"]["recommended_cli"] == (
        "paper-mission package-candidate"
    )
    assert result["carry_forward_risk_receipt_ref"].startswith(
        "carry-forward-risk:paper-mission-owner-fallback:study-001:"
    )
    assert result["write_plan"]["written_files"] == []


def test_terminal_owner_gate_authority_readback_is_readback_only() -> None:
    from med_autoscience.paper_mission_terminal_owner_gate import (
        terminal_owner_gate_authority_readback,
    )

    result = terminal_owner_gate_authority_readback(
        {
            "surface_kind": "paper_mission_terminal_owner_gate",
            "owner": "one-person-lab",
            "gate_kind": "typed_blocker",
            "blocked_reason": "opl_runtime_lifecycle_readback_required",
            "typed_blocker_ref": "closeout.json#domain_blocker",
            "closeout_ref": "closeout.json",
            "stage_attempt_id": "sat-terminal",
            "work_unit_id": "gate_clearing_claim_evidence_repair",
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "authority_materialized": False,
        }
    )

    assert result["surface_kind"] == "mas_terminal_owner_gate_authority_readback"
    assert result["status"] == "typed_blocker_required"
    assert result["selected_outcome"] == "typed_blocker_required"
    assert result["next_owner"] == "one-person-lab"
    assert result["resume_condition"] == "opl_runtime_lifecycle_readback_required"
    assert result["owner_answer_contract"]["required_surface"] == "typed_blocker_ref"
    assert result["owner_answer_contract"]["typed_blocker_ref"] == (
        "closeout.json#domain_blocker"
    )
    assert result["owner_answer_contract"]["accepted_shapes"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "paper_facing_delta_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert result["consume_result"] == {
        "status": "typed_blocker",
        "outcome": "typed_blocker_required",
        "authority_materialized": False,
    }
    assert result["write_plan"]["written_files"] == []
    assert result["authority_boundary"]["can_claim_paper_progress"] is False
    assert result["authority_boundary"]["can_authorize_provider_admission"] is False


def _paper_audit_pack_refs() -> dict[str, list[dict[str, str]]]:
    families = (
        "analysis_rationale_log",
        "decision_trace",
        "evidence_ledger_delta",
        "review_ledger_delta",
        "revision_log_delta",
        "failed_path_ledger",
        "artifact_lineage",
        "reproducibility_refs",
    )
    return {
        family: [
            {
                "ref_id": f"{family}::test",
                "ref_kind": "test_ref",
                "uri": f"test://paper-audit-pack/{family}",
            }
        ]
        for family in families
    }
