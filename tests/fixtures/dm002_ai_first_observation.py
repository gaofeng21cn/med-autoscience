from __future__ import annotations

from pathlib import Path


def dm002_minimal_observation_progress_snapshot(tmp_path: Path) -> dict[str, object]:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    delivery_manifest_path = study_root / "manuscript" / "delivery_manifest.json"
    return {
        "study_id": "002-dm-china-us-mortality-attribution",
        "study_root": str(study_root),
        "current_stage": "publication_supervision",
        "current_blockers": [
            "publication_eval is blocked by mechanical projection and reviewer-first concerns.",
            "delivery mirror requires canonical refresh before submission use.",
        ],
        "next_system_action": "Return to AI reviewer workflow and canonical artifact proof before any submission route.",
        "needs_user_decision": False,
        "needs_physician_decision": False,
        "progress_freshness": {"status": "fresh", "summary": "DM002 observation fixture uses repo-level sanitized fields."},
        "study_yaml_observation": {
            "study_id": "002-dm-china-us-mortality-attribution",
            "title": "China-US diabetes mortality transportability and attribution shift",
            "status": "boundary_locked",
            "execution_status": "startup_ready",
            "primary_endpoint": "5-year all-cause mortality",
            "secondary_endpoint": "broad_cvd_attribution_shift",
        },
        "publication_eval_observation": {
            "surface": "publication_eval/latest.json",
            "owner": "mechanical_projection",
            "source_kind": "publication_gate_report",
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "ai_reviewer_required": True,
            "gap_summaries": [
                "stale_submission_minimal_authority",
                "stale_study_delivery_mirror",
                "medical_publication_surface_blocked",
                "reviewer_first_concerns_unresolved",
                "claim_evidence_consistency_failed",
                "submission_hardening_incomplete",
                "submission_surface_qc_failure_present",
            ],
            "recommended_route": "return_to_write",
        },
        "delivery_manifest_observation": {
            "surface": "manuscript/delivery_manifest.json",
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "generated_at": "2026-04-26T21:16:21+00:00",
        },
        "ai_first_default_entry_state": {
            "surface": "ai_first_default_entry_state",
            "status": "review_required",
            "recommended_next_step": "Return to AI reviewer workflow and canonical artifact proof before any submission route.",
            "human_review_required": True,
            "pre_draft": {
                "surface": "pre_draft_quality_runtime",
                "draft_ready": True,
                "route_back_required": False,
                "summary": "DM002 paper framing is boundary-locked; observation baseline does not add a new pre-draft gate.",
            },
            "ai_reviewer_workflow": {
                "surface": "ai_reviewer_runtime_workflow",
                "authority_state": "projection_only",
                "trace_complete": False,
                "finalize_authorized": False,
                "submission_authorized": False,
                "summary": "DM002 publication_eval is mechanical projection and still requires AI reviewer authority.",
                "prompt": "DM002_INTERNAL_PROMPT_SHOULD_NOT_LEAK",
                "full_prompt": "DM002_FULL_PROMPT_SHOULD_NOT_LEAK",
                "token_count": "DM002_TOKEN_CANARY",
            },
            "artifact_proof": {
                "surface": "artifact_runtime_proof",
                "rebuild_pending": True,
                "current_package_from_canonical_source": False,
                "summary": "DM002 delivery mirror requires canonical artifact refresh before submission use.",
                "raw_terminal_log": "DM002_RAW_LOG_SHOULD_NOT_LEAK",
                "log_path": "/tmp/DM002_RAW_LOG_SHOULD_NOT_LEAK.log",
            },
            "route_back": {
                "required": True,
                "reason": "dm002_publication_eval_requires_ai_reviewer_and_canonical_refresh",
                "ai_reviewer_target": "write",
            },
        },
        "ai_first_operations_dashboard": {
            "surface": "ai_first_operations_dashboard_summary",
            "read_model": "ai_first_operations_dashboard_read_model",
            "maintainer_view": {
                "ai_reviewer_trace": {"complete": False, "authority": "mechanical_projection"},
                "route_back": {"count": 1, "target": "write"},
                "artifact_stale": {
                    "stale_artifact_count": 1,
                    "current_package_from_canonical_source": False,
                },
            },
            "authority": {
                "observability_can_authorize_quality": False,
                "observability_can_authorize_finalize": False,
                "observability_can_authorize_submission": False,
                "observability_can_mutate_runtime": False,
            },
        },
        "refs": {
            "publication_eval_path": str(publication_eval_path),
            "ai_first_observability_delivery_manifest_path": str(delivery_manifest_path),
        },
    }
