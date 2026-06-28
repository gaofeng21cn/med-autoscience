from __future__ import annotations

from .. import shared as _shared
from tests.reviewer_os_fixture_helpers import (
    claim_evidence_alignment_digest,
    ready_claim_evidence_alignment_gate,
)

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__") and name != "__all__"
})


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _patch_canonical_current_work_unit(
    monkeypatch,
    *,
    study_id: str,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str | None,
    owner: str,
    source: str = "canonical_current_work_unit",
) -> None:
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")

    def _read_study_progress(**_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": owner,
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "truth_epoch": "truth-event-000024-daa5883571a64a07",
                    "runtime_health_epoch": "runtime-health-event-canonical-test",
                },
                **(
                    {
                        "work_unit_fingerprint": work_unit_fingerprint,
                        "action_fingerprint": work_unit_fingerprint,
                    }
                    if work_unit_fingerprint is not None
                    else {}
                ),
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": owner,
                "next_work_unit": work_unit_id,
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": source,
                "next_owner": owner,
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "allowed_actions": [action_type],
                **(
                    {"work_unit_fingerprint": work_unit_fingerprint}
                    if work_unit_fingerprint is not None
                    else {}
                ),
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", _read_study_progress)


def _owner_route(
    *,
    study_id: str,
    next_owner: str,
    owner_reason: str,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    runtime_health_epoch: str,
    blocked_actions: list[str],
) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": study_id,
        "truth_epoch": "truth-event-000024-daa5883571a64a07",
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": work_unit_fingerprint,
        "route_epoch": "truth-event-000024-daa5883571a64a07",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "allowed_actions": [action_type],
        "blocked_actions": blocked_actions,
        "source_refs": {
            "runtime_health_epoch": runtime_health_epoch,
            "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
            "work_unit_id": work_unit_id,
            "blocked_reason": owner_reason,
        },
        "idempotency_key": f"owner-route::{study_id}::{work_unit_fingerprint}",
    }


def _write_dispatch(
    *,
    workspace_root: Path,
    study_id: str,
    filename: str,
    action_type: str,
    next_owner: str,
    dispatch_authority: str,
    owner_route: dict[str, object],
    generated_at: str | None = None,
    allowed_write_surfaces: list[str] | None = None,
) -> None:
    dispatch_path = (
        workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / filename
    )
    payload = {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "dispatch_status": "ready",
        "dispatch_authority": dispatch_authority,
        "next_executable_owner": next_owner,
        "executor_kind": "codex_cli_default",
        "consumer_mutation_scope": "executor_dispatch_request_only",
        "owner_route": owner_route,
        "prompt_contract": {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "next_executable_owner": next_owner,
            "owner_route": owner_route,
            "allowed_write_surfaces": allowed_write_surfaces or ["paper/draft.md"],
            "forbidden_surfaces": [
                "paper/current_package/**",
                "manuscript/current_package/**",
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
        "refs": {
            "dispatch_path": str(dispatch_path),
            "source_eval_path": str(
                workspace_root / "studies" / study_id / "artifacts" / "publication_eval" / "latest.json"
            ),
        },
    }
    if generated_at is not None:
        payload["generated_at"] = generated_at
    _write_json(dispatch_path, payload)


def _opl_execution_authorization(label: str) -> dict[str, object]:
    return {
        "owner": "one-person-lab",
        "provider_attempt_ref": f"opl://stage-attempts/{label}",
        "stage_attempt_id": f"stage-attempt::{label}",
        "attempt_lease_ref": f"opl://stage-attempts/{label}/leases/current",
        "attempt_lease_status": "active",
        "execution_authorization_decision_ref": f"opl://stage-attempts/{label}/execution-authorizations/current",
    }


def _write_opl_production_proof(path: Path) -> None:
    checks = {
        "external_temporal_server_reachable": True,
        "managed_worker_ready": True,
        "worker_completed_attempt": True,
        "worker_restart_requery": True,
        "signal_history_preserved": True,
        "typed_closeout_required_for_completed": True,
        "missing_closeout_blocks_completion": True,
        "retry_or_dead_letter_boundary_observed": True,
        "domain_truth_boundary_preserved": True,
    }
    _write_json(
        path,
        {
            "family_runtime_residency_proof": {
                "surface_kind": "opl_temporal_production_residency_proof",
                "provider_kind": "temporal",
                "closeout_status": "production_residency_proven",
                "production_residency_proof": {
                    "surface_kind": "opl_temporal_external_production_residency_proof",
                    "provider_kind": "temporal",
                    "closeout_status": "production_residency_proven",
                    "runtime_snapshot": {
                        "address_source": "managed_local_service_state",
                        "lifecycle_status": "ready",
                        "server_reachable": True,
                        "worker_ready": True,
                        "task_queue": "opl-stage-attempts",
                    },
                    "proof_receipt": {
                        "receipt_kind": "temporal_production_residency_proof",
                        "receipt_status": "proven",
                        "completed_workflow_id": "wf-complete",
                        "blocked_workflow_id": "wf-blocked",
                    },
                    "checks": checks,
                },
            }
        },
    )


def assert_stable_blocker_reason(
    payload: dict[str, object],
    *,
    blocker_class: str,
    detail_reason: str,
) -> None:
    assert payload["payload_reason"] == blocker_class
    assert payload["payload_blocker_class"] == blocker_class
    assert payload["payload_detail_reason"] == detail_reason
    assert payload["details"]["blocker_class"] == blocker_class
    assert payload["details"]["detail_reason"] == detail_reason

    evidence_payload = payload["domain_dispatch_evidence_record_payload"]
    assert evidence_payload["reason"] == blocker_class
    assert evidence_payload["details"]["blocker_class"] == blocker_class
    assert evidence_payload["details"]["detail_reason"] == detail_reason

    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["blocker_class"] == blocker_class
    assert record_payload["details"]["blocker_class"] == blocker_class
    assert record_payload["details"]["detail_reason"] == detail_reason


def _ai_reviewer_blocking_eval(study_root: Path) -> dict[str, object]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    main_result_ref = str(quest_root / "artifacts" / "results" / "main_result.json")
    manuscript_ref = str(study_root / "paper" / "manuscript.md")
    study_charter_ref = str(study_root / "artifacts" / "controller" / "study_charter.json")
    review_ledger_ref = str(study_root / "paper" / "review" / "review_ledger.json")
    input_bundle = {
        "manuscript": manuscript_ref,
        "study_charter": study_charter_ref,
        "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "review_ledger": review_ledger_ref,
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }
    claim_alignment = ready_claim_evidence_alignment_gate(
        claim_evidence_map_ref=input_bundle["claim_evidence_map"],
        evidence_ledger_ref=input_bundle["evidence_ledger"],
    )
    request_digest = "sha256:" + "a" * 64
    manuscript_digest = "sha256:" + "b" * 64
    rubric_scores = {
        "clinical_significance": {
            "status": "ready",
            "rationale": "Clinical framing is stable.",
            "evidence_refs": [study_charter_ref],
        },
        "evidence_strength": {
            "status": "partial",
            "rationale": "Bounded sensitivity analysis is still missing.",
            "evidence_refs": [main_result_ref],
        },
        "novelty_positioning": {
            "status": "ready",
            "rationale": "Contribution boundary is defined.",
            "evidence_refs": [study_charter_ref],
        },
        "medical_journal_prose_quality": {
            "status": "partial",
            "rationale": "The discussion overstates observational evidence.",
            "evidence_refs": [manuscript_ref],
        },
        "human_review_readiness": {
            "status": "ready",
            "rationale": "Administrative human review can wait until repair is complete.",
            "evidence_refs": [review_ledger_ref],
        },
    }
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-05-10T00:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-05-10T00:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": study_charter_ref,
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
            "main_result_ref": main_result_ref,
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [manuscript_ref, main_result_ref],
            "ai_reviewer_required": False,
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Evidence strength and claim wording require repair.",
            "stop_loss_pressure": "watch",
        },
        "quality_assessment": {
            "clinical_significance": {
                "status": "ready",
                "summary": "Clinical framing is stable.",
                "evidence_refs": [study_charter_ref],
            },
            "evidence_strength": {
                "status": "partial",
                "summary": "Main result supports direction but not final claim strength.",
                "evidence_refs": [main_result_ref],
                "reviewer_revision_advice": "Add bounded sensitivity analysis before acceptance.",
            },
            "novelty_positioning": {
                "status": "ready",
                "summary": "Contribution boundary is defined.",
                "evidence_refs": [study_charter_ref],
            },
            "medical_journal_prose_quality": {
                "status": "partial",
                "summary": "Discussion wording is too strong for observational evidence.",
                "evidence_refs": [manuscript_ref],
                "reviewer_revision_advice": "Revise text to restrained association language.",
            },
            "human_review_readiness": {
                "status": "ready",
                "summary": "Human review can wait until evidence and prose repair are complete.",
                "evidence_refs": [review_ledger_ref],
            },
        },
        "reviewer_operating_system": {
            "contract_id": "medical_publication_ai_reviewer_os_v1",
            "input_bundle": input_bundle,
            "claim_evidence_alignment": claim_alignment,
            "rubric_scores": rubric_scores,
            "decision_matrix": [
                {
                    "dimension": dimension,
                    "status": score["status"],
                    "rationale": score["rationale"],
                }
                for dimension, score in rubric_scores.items()
            ],
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": request_digest,
                    "manuscript_ref": manuscript_ref,
                    "manuscript_digest": manuscript_digest,
                    "route_back_required": True,
                    "route_target": "write",
                },
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": manuscript_ref,
                    "manuscript_digest": manuscript_digest,
                },
                "source_eval": {
                    "status": "current",
                    "eval_id": "publication-eval::001-risk::quest-001::2026-05-10T00:00:00+00:00",
                },
                "current_package_freshness": {
                    "status": "fresh",
                    "source_eval_id": "publication-eval::001-risk::quest-001::2026-05-10T00:00:00+00:00",
                },
            },
            "publication_quality_readiness": {
                "surface_kind": "publication_quality_authority_kernel_v1",
                "status": "ready",
                "current_manuscript_digest": manuscript_digest,
                "review_request_digest": request_digest,
                "evidence_ledger_digest": "sha256:" + "c" * 64,
                "rubric_version": "medical_publication_critique_v1",
                "owner_attempt_id": (
                    "ai-reviewer-publication-eval::publication-eval::001-risk::quest-001::"
                    "2026-05-10T00:00:00+00:00"
                ),
                "claim_evidence_alignment_digest": claim_evidence_alignment_digest(claim_alignment),
                "fail_closed_when_missing": True,
                "missing_required_fields": [],
            },
            "future_facing_limitations_plan": [
                {
                    "limitation": "Evidence strength remains bounded by the current observational result.",
                    "impact_on_claim": "Claims must stay association-oriented until sensitivity analysis closes.",
                    "required_future_analysis_data_or_design": "Run bounded sensitivity analysis before acceptance.",
                    "current_manuscript_wording_must_be_restrained": True,
                }
            ],
            "provenance_checks": {
                "assessment_owner": "ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "ai_reviewer_required": False,
                "mechanical_projection_used_as_quality_authority": False,
            },
            "route_back_decision": {
                "recommended_action": "route_back_same_line",
                "route_target": "write",
                "rationale": "Repair before acceptance.",
            },
        },
        "gaps": [
            {
                "gap_id": "claim-strength",
                "gap_type": "claim",
                "severity": "must_fix",
                "summary": "Claim strength exceeds the current evidence ledger.",
                "evidence_refs": [main_result_ref],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "route-back-claim-strength",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "Repair claim wording within the same paper line.",
                "route_target": "write",
                "route_key_question": "Which claim sentence exceeds evidence strength?",
                "route_rationale": "AI reviewer requires same-line manuscript repair before package advance.",
                "evidence_refs": [main_result_ref],
                "requires_controller_decision": True,
            }
        ],
    }


__all__ = [name for name in globals() if not name.startswith("__")]
