from __future__ import annotations

from .. import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__") and name != "__all__"
})


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
