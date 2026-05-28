from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_clears_stale_ai_reviewer_lifecycle_after_reviewer_eval_materialized(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dm")
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    ai_reviewer_eval = {
        "schema_version": 1,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        },
        "recommended_actions": [],
    }
    _write_json(publication_eval_path, ai_reviewer_eval)
    lifecycle_path = study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json"
    _write_json(
        lifecycle_path,
        {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": "quest-dm",
            "state": "blocked",
            "blocked_reason": "ai_reviewer_assessment_required",
            "next_owner": "ai_reviewer",
            "external_supervisor_required": False,
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_root": str(profile.runtime_root / "quest-dm"),
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "active_run_id": "run-live",
            "runtime_liveness_audit": {
                "active_run_id": "run-live",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-live"},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "observe_runtime",
                "attempt_state": "live",
                "retry_budget_remaining": 3,
            },
            "publication_eval": ai_reviewer_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-current",
                "source_signature": "truth-source-current",
                "canonical_next_action": "supervise_runtime",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "publication_supervision",
            "paper_stage": "write",
            "refs": {"publication_eval_path": str(publication_eval_path)},
            "supervision": {"active_run_id": "run-live", "health_status": "live"},
            "quality_review_loop": {"closure_state": "review_required"},
            "ai_repair_lifecycle": {
                "state": "blocked",
                "blocked_reason": "ai_reviewer_assessment_required",
                "next_owner": "ai_reviewer",
                "external_supervisor_required": False,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"] == {
        "present": True,
        "owner": "ai_reviewer",
        "required": False,
        "missing": False,
    }
    assert study["action_queue"] == []
    assert study["ai_repair_lifecycle"] is None
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["next_owner"] is None
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["owner_reason"] is None
    assert study["owner_route"]["allowed_actions"] == []
    assert not lifecycle_path.exists()


def test_scan_domain_routes_clears_stale_record_lifecycle_after_current_ai_reviewer_eval_materialized(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text("Current manuscript body.\n", encoding="utf-8")
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    ai_reviewer_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::002::current-ai-reviewer",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "manuscript_path": str(manuscript_path),
                }
            }
        },
        "recommended_actions": [],
    }
    _write_json(publication_eval_path, ai_reviewer_eval)
    lifecycle_path = study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json"
    _write_json(
        lifecycle_path,
        {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "state": "blocked",
            "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
            "next_owner": "ai_reviewer",
            "external_supervisor_required": False,
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_root": str(profile.runtime_root / study_id),
            "quest_status": "waiting_for_user",
            "decision": "resume",
            "reason": "domain_transition_ai_reviewer_re_eval",
            "active_run_id": None,
            "publication_eval": ai_reviewer_eval,
            "runtime_health_snapshot": {
                "canonical_runtime_action": "continue_supervising_runtime",
                "attempt_state": "idle",
                "retry_budget_remaining": 2,
            },
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-dm002",
                "source_signature": "truth-source-dm002",
                "canonical_next_action": "resume_same_study_line",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_root": str(profile.runtime_root / study_id),
            "current_stage": "managed_opl_runtime_owner_handoff_gap",
            "paper_stage": "publishability_gate_blocked",
            "refs": {"publication_eval_path": str(publication_eval_path)},
            "supervision": {"active_run_id": None, "health_status": "parked"},
            "quality_review_loop": {"closure_state": "review_required"},
            "ai_repair_lifecycle": {
                "state": "blocked",
                "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
                "next_owner": "ai_reviewer",
                "external_supervisor_required": False,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=True,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"]["present"] is True
    assert study["ai_reviewer_assessment"]["owner"] == "ai_reviewer"
    assert study["action_queue"] == []
    assert study["ai_repair_lifecycle"] is None
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["next_owner"] is None
    assert study["owner_route"]["owner_reason"] is None
    assert study["owner_route"]["allowed_actions"] == []
    assert not lifecycle_path.exists()


def test_scan_domain_routes_uses_current_record_archive_over_stale_progress_request_lifecycle(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    manuscript_path = study_root / "paper" / "draft.md"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    medical_review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260528T094456Z_publication_eval_record.json"
    )
    manuscript_text = "# Draft\n\nCurrent DPCC manuscript.\n"
    evidence_payload = {"schema_version": 1, "claim": "current evidence"}
    claim_payload = {"schema_version": 1, "claim": "current claim map"}
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    _write_json(evidence_path, evidence_payload)
    _write_json(claim_map_path, claim_payload)
    _write_json(medical_review_path, {"schema_version": 1})
    old_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::003-dpcc::old::20260527T235300Z",
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-27T23:53:00+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {"medical_journal_prose_quality": {"status": "partial"}},
        "recommended_actions": [],
    }
    _write_json(latest_eval_path, old_eval)
    stale_lifecycle = {
        "state": "requested",
        "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
        "stale_record_ref": str(record_path.resolve()),
        "required_currentness_refs": [str(manuscript_path.resolve())],
    }
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": dict(stale_lifecycle),
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                    "evidence_ledger": {"path": str(evidence_path.resolve()), "present": True, "valid": True},
                    "review_ledger": {
                        "path": str(study_root / "paper" / "review" / "review_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
                    "study_charter": {
                        "path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                        "present": True,
                        "valid": True,
                    },
                    "medical_manuscript_blueprint": {
                        "path": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                        "present": True,
                        "valid": True,
                    },
                    "claim_evidence_map": {"path": str(claim_map_path.resolve()), "present": True, "valid": True},
                    "medical_prose_review": {"path": str(medical_review_path.resolve()), "present": True, "valid": True},
                    "publication_gate_projection": {"path": str(latest_eval_path.resolve()), "present": True, "valid": True},
                }
            },
        },
    )
    current_eval_id = "publication-eval::003-dpcc::current-inputs::20260528T094456Z"
    current_record = {
        "schema_version": 1,
        "eval_id": current_eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": "2026-05-28T09:44:56+00:00",
        "evaluation_scope": "publication",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [
                str(request_path.resolve()),
                str(manuscript_path.resolve()),
                str(evidence_path.resolve()),
                str(claim_map_path.resolve()),
            ],
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            dimension: {
                "status": "partial" if dimension == "medical_journal_prose_quality" else "ready",
                "summary": f"{dimension} reviewed against current DPCC inputs.",
                "evidence_refs": [str(manuscript_path.resolve()), str(evidence_path.resolve())],
            }
            for dimension in (
                "clinical_significance",
                "evidence_strength",
                "novelty_positioning",
                "medical_journal_prose_quality",
                "human_review_readiness",
            )
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::dm003::gate-replay",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "finalize",
                "route_key_question": "Can the gate consume the current AI reviewer record?",
                "route_rationale": "Gate replay is now the current owner work unit.",
                "work_unit_fingerprint": "ai-reviewer-current-inputs::dm003",
                "next_work_unit": {
                    "unit_id": "owner_authorized_publication_gate_replay",
                    "lane": "finalize",
                    "summary": "Replay the MAS publication gate against current manuscript and evidence surfaces.",
                },
            }
        ],
        "future_facing_limitations_plan": [
            {
                "limitation": "AI reviewer authorization is scoped to this current-inputs record.",
                "impact_on_claim": "Claims remain tied to reviewed evidence refs.",
                "required_future_analysis_data_or_design": "Repeat review after substantive input changes.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "reviewer_operating_system": {
            "contract_id": "medical_publication_ai_reviewer_os_v1",
            "input_bundle": {
                "manuscript": str(manuscript_path.resolve()),
                "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "evidence_ledger": str(evidence_path.resolve()),
                "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
                "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                "claim_evidence_map": str(claim_map_path.resolve()),
                "medical_prose_review": str(medical_review_path.resolve()),
                "publication_gate_projection": str(latest_eval_path.resolve()),
            },
            "rubric_scores": {
                dimension: {
                    "status": "partial" if dimension == "medical_journal_prose_quality" else "ready",
                    "rationale": f"{dimension} was reviewed against current DPCC inputs.",
                    "evidence_refs": [str(manuscript_path.resolve())],
                }
                for dimension in (
                    "clinical_significance",
                    "evidence_strength",
                    "novelty_positioning",
                    "medical_journal_prose_quality",
                    "human_review_readiness",
                )
            },
            "decision_matrix": [
                {
                    "dimension": dimension,
                    "status": "partial" if dimension == "medical_journal_prose_quality" else "ready",
                    "rationale": f"{dimension} was reviewed against current DPCC inputs.",
                }
                for dimension in (
                    "clinical_significance",
                    "evidence_strength",
                    "novelty_positioning",
                    "medical_journal_prose_quality",
                    "human_review_readiness",
                )
            ],
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:" + "a" * 64,
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                    "route_back_required": True,
                    "route_target": "finalize",
                },
                "current_manuscript": {
                    "status": "current",
                    "manuscript_ref": str(manuscript_path.resolve()),
                    "manuscript_digest": _sha256_text(manuscript_text),
                    "reviewed_at": "2026-05-28T09:44:56+00:00",
                },
                "evidence_ledger": {
                    "status": "current",
                    "ref": str(evidence_path.resolve()),
                    "digest": _sha256_text(json.dumps(evidence_payload, ensure_ascii=False, indent=2) + "\n"),
                },
                "claim_evidence_map": {
                    "status": "current",
                    "ref": str(claim_map_path.resolve()),
                    "digest": _sha256_text(json.dumps(claim_payload, ensure_ascii=False, indent=2) + "\n"),
                },
                "source_eval": {"status": "current", "eval_id": current_eval_id},
                "current_package_freshness": {"status": "downstream_pending", "source_eval_id": current_eval_id},
            },
            "claim_evidence_alignment": {
                "surface_kind": "claim_evidence_alignment_gate_v1",
                "source_project": "academic-research-skills",
                "absorbed_as": "mas_native_claim_evidence_alignment_gate",
                "status": "ready",
                "input_refs": {
                    "claim_evidence_map": str(claim_map_path.resolve()),
                    "evidence_ledger": str(evidence_path.resolve()),
                },
                "claim_count": 1,
                "aligned_claim_count": 1,
                "claims": [
                    {
                        "claim_id": "C1",
                        "status": "aligned",
                        "evidence_item_refs": ["E1"],
                        "support_levels": ["primary"],
                    }
                ],
                "fail_closed_when_missing": True,
                "missing_required_fields": [],
                "blockers": [],
                "body_included": False,
                "may_authorize_publication_readiness": False,
                "may_authorize_quality_verdict": False,
                "can_write_domain_truth": False,
            },
            "publication_quality_readiness": {
                "surface_kind": "publication_quality_authority_kernel_v1",
                "status": "blocked",
                "current_manuscript_digest": _sha256_text(manuscript_text),
                "review_request_digest": "sha256:" + "b" * 64,
                "evidence_ledger_digest": _sha256_text(
                    json.dumps(evidence_payload, ensure_ascii=False, indent=2) + "\n"
                ),
                "claim_evidence_alignment_digest": "sha256:" + "c" * 64,
                "rubric_version": "medical_publication_critique_v1",
                "owner_attempt_id": f"ai-reviewer-publication-eval::{current_eval_id}",
                "fail_closed_when_missing": True,
                "missing_required_fields": ["owner_authorized_publication_gate_replay"],
            },
            "future_facing_limitations_plan": [
                {
                    "limitation": "AI reviewer authorization is scoped to this current-inputs record.",
                    "impact_on_claim": "Claims remain tied to reviewed evidence refs.",
                    "required_future_analysis_data_or_design": "Repeat review after substantive input changes.",
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
                "route_target": "finalize",
                "rationale": "Gate replay is now the current owner work unit.",
            },
        },
    }
    _write_json(record_path, current_record)
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "active_run_id": None,
        "publication_eval": old_eval,
        "domain_transition": {
            "study_id": study_id,
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "lane": "review",
                "summary": "Produce a current AI reviewer publication-eval record before dispatching the publication-eval workflow.",
            },
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-current-inputs",
            "canonical_runtime_action": "external_supervisor_required",
            "attempt_state": "escalated",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-current-inputs",
            "source_signature": "truth-source-dm003-current-inputs",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(latest_eval_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
        "ai_reviewer_request_lifecycle": {
            "surface": "ai_reviewer_request_lifecycle",
            "state": "requested",
            "request_owner": "ai_reviewer",
            "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
            "stale_record_ref": str(record_path.resolve()),
            "required_currentness_refs": [str(manuscript_path.resolve())],
            "refs": {"request_path": str(request_path.resolve())},
        },
        "ai_repair_lifecycle": {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "state": "blocked",
            "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: status_payload,
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: progress_payload,
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"]["present"] is True
    assert study["ai_reviewer_assessment"]["missing"] is False
    assert study["ai_reviewer_assessment"].get("blocked_reason") is None
    assert [action["action_type"] for action in study["action_queue"]] == ["run_gate_clearing_batch"]
    action = study["action_queue"][0]
    assert action["reason"] == "owner_authorized_publication_gate_replay"
    assert action["controller_work_unit_id"] == "owner_authorized_publication_gate_replay"
    assert action["original_route_target"] == "finalize"
    assert study["owner_route"]["next_owner"] == "gate_clearing_batch"
    assert study["owner_route"]["allowed_actions"] == ["run_gate_clearing_batch"]
    assert study["owner_route"]["owner_reason"] == "owner_authorized_publication_gate_replay"
    assert study["owner_route"]["source_refs"]["source_eval_id"] == current_eval_id
    assert study["owner_route"]["source_refs"]["publication_eval_path"] == str(record_path.resolve())
    assert study["blocked_reason"] == "owner_authorized_publication_gate_replay"


def test_scan_domain_routes_routes_requested_ai_reviewer_recheck_even_when_old_eval_is_ai_owned(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "obesity_multicenter_phenotype_atlas"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    ai_reviewer_eval = {
        "schema_version": 1,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_gate_report",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        },
        "recommended_actions": [],
    }
    _write_json(publication_eval_path, ai_reviewer_eval)

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_root": str(profile.runtime_root / study_id),
            "quest_status": "waiting_for_user",
            "active_run_id": None,
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "publication_eval": ai_reviewer_eval,
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-obesity",
                "source_signature": "truth-source-obesity",
                "canonical_next_action": "observe",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "auto_runtime_parked",
            "paper_stage": "publishability_gate_blocked",
            "refs": {"publication_eval_path": str(publication_eval_path)},
            "supervision": {"active_run_id": None, "health_status": "parked"},
            "quality_review_loop": {"closure_state": "quality_repair_required"},
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {
                    "status": "fresh",
                    "latest_progress_at": "2026-05-10T10:56:23+00:00",
                }
            },
            "ai_reviewer_request_lifecycle": {
                "surface": "ai_reviewer_request_lifecycle",
                "request_id": "return_to_ai_reviewer_workflow::obesity",
                "request_kind": "return_to_ai_reviewer_workflow",
                "state": "requested",
                "request_owner": "ai_reviewer",
                "refs": {
                    "request_path": str(
                        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
                    )
                },
            },
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "projection_only": True,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"]["missing"] is True
    assert study["ai_reviewer_assessment"]["request_state"] == "requested"
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["why_not_applied"] == "ai_reviewer_assessment_required"
    assert study["blocked_reason"] == "ai_reviewer_assessment_required"
    assert study["next_owner"] == "ai_reviewer"
    assert study["external_supervisor_required"] is False
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]


def test_scan_domain_routes_reads_stable_ai_reviewer_request_before_old_write_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    request_builder = importlib.import_module("med_autoscience.controllers.domain_action_requests")
    request_lifecycle = importlib.import_module("med_autoscience.controllers.domain_action_request_lifecycle")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::002::002::2026-05-22T05:00:04+00:00",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "source_refs": [],
        },
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "route_target": "write",
                "next_work_unit": {
                    "unit_id": "dm002_same_line_publication_paper_repair",
                    "lane": "write",
                    "summary": "Absorb fresh repair evidence into the manuscript.",
                },
            }
        ],
    }
    _write_json(publication_eval_path, publication_eval)
    _write_json(study_root / "paper" / "draft.md", {"body": "Current manuscript."})
    packet = request_builder.build_ai_reviewer_publication_eval_request(
        study_id=study_id,
        quest_id=study_id,
        source_surface="quality_repair_batch",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "review_required"},
            "route_back": {"required": True, "target": "ai_reviewer"},
            "blockers": [],
        },
        input_refs={
            "manuscript": {"relative_path": "paper/draft.md"},
            "evidence_ledger": {"relative_path": "paper/evidence_ledger.json"},
            "review_ledger": {"relative_path": "paper/review/review_ledger.json"},
            "study_charter": {"relative_path": "artifacts/controller/study_charter.json"},
            "medical_manuscript_blueprint": {"relative_path": "paper/medical_manuscript_blueprint.json"},
            "claim_evidence_map": {"relative_path": "paper/claim_evidence_map.json"},
            "medical_prose_review": {"relative_path": "artifacts/publication_eval/medical_prose_review.json"},
            "publication_gate_projection": {"relative_path": "artifacts/publication_eval/latest.json"},
        },
        lifecycle_state="requested",
    )
    request_lifecycle.materialize_ai_reviewer_request(study_root=study_root, packet=packet)

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_root": str(profile.runtime_root / study_id),
            "quest_status": "waiting_for_user",
            "active_run_id": None,
            "publication_eval": publication_eval,
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "write",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "dm002_same_line_publication_paper_repair",
                    "lane": "write",
                    "summary": "Absorb fresh repair evidence into the manuscript.",
                },
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "continue_supervising_runtime",
                "attempt_state": "idle",
                "retry_budget_remaining": 2,
            },
            "study_truth_snapshot": {
                "truth_epoch": "truth-epoch-dm002",
                "source_signature": "truth-source-dm002",
                "canonical_next_action": "resume_same_study_line",
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "managed_opl_runtime_owner_handoff_gap",
            "paper_stage": "publishability_gate_blocked",
            "refs": {"publication_eval_path": str(publication_eval_path)},
            "supervision": {"active_run_id": None, "health_status": "parked"},
            "quality_review_loop": {"closure_state": "review_required"},
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"]["missing"] is True
    assert study["ai_reviewer_assessment"]["request_state"] == "requested"
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["owner_route"]["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert study["blocked_reason"] == "ai_reviewer_assessment_required"


def test_ai_reviewer_request_lifecycle_keeps_new_fingerprint_pending_when_old_eval_refs_latest_path(
    tmp_path: Path,
) -> None:
    request_builder = importlib.import_module("med_autoscience.controllers.domain_action_requests")
    request_lifecycle = importlib.import_module("med_autoscience.controllers.domain_action_request_lifecycle")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    request_path = (
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    )
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::002::002::2026-05-21T21:37:22+00:00::ai-reviewer",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "source_refs": [str(request_path)],
        },
        "recommended_actions": [],
    }
    packet = request_builder.build_ai_reviewer_publication_eval_request(
        study_id=study_id,
        quest_id=study_id,
        source_surface="quality_repair_batch",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "review_required"},
            "route_back": {"required": True, "target": "ai_reviewer"},
            "blockers": [],
        },
        input_refs={
            "manuscript": {"relative_path": "paper/draft.md"},
            "evidence_ledger": {"relative_path": "paper/evidence_ledger.json"},
            "review_ledger": {"relative_path": "paper/review/review_ledger.json"},
            "study_charter": {"relative_path": "artifacts/controller/study_charter.json"},
            "medical_manuscript_blueprint": {"relative_path": "paper/medical_manuscript_blueprint.json"},
            "claim_evidence_map": {"relative_path": "paper/claim_evidence_map.json"},
            "medical_prose_review": {"relative_path": "artifacts/publication_eval/medical_prose_review.json"},
            "publication_gate_projection": {"relative_path": "artifacts/publication_eval/latest.json"},
        },
        lifecycle_state="requested",
    )
    packet["source_fingerprint"] = "sha256:new-ai-reviewer-request"
    request_lifecycle.materialize_ai_reviewer_request(study_root=study_root, packet=packet)

    projected = request_lifecycle.project_ai_reviewer_request_lifecycle(
        study_root=study_root,
        publication_eval_payload=publication_eval,
    )

    assert projected["state"] == "requested"
    assert projected["assessment_written"] is False
