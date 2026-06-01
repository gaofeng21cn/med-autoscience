from __future__ import annotations

import importlib
import json
import hashlib
from pathlib import Path

from tests.reviewer_os_fixture_helpers import (
    current_manuscript_routeback_record,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _current_input_routeback_record(
    *,
    study_root: Path,
    manuscript_path: Path,
    manuscript_text: str,
    evidence_path: Path,
    evidence_digest: str,
    claim_map_path: Path,
    claim_map_digest: str,
    study_id: str,
    quest_id: str,
    eval_id: str,
) -> dict:
    record = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
        emitted_at="2026-05-31T19:23:20+00:00",
    )
    currentness = record["reviewer_operating_system"]["currentness_checks"]
    currentness["evidence_ledger"] = {
        "status": "current",
        "ref": str(evidence_path.resolve()),
        "digest": evidence_digest,
        "authority_source_signature": "ai_reviewer_workflow_live_input",
    }
    currentness["claim_evidence_map"] = {
        "status": "current",
        "ref": str(claim_map_path.resolve()),
        "digest": claim_map_digest,
        "authority_source_signature": "ai_reviewer_workflow_live_input",
    }
    currentness["source_eval"] = {"status": "current", "eval_id": eval_id}
    record["recommended_actions"][0].update(
        {
            "action_id": "A1_consume_current_ai_reviewer_record_then_gate_replay",
            "reason": (
                "Consume this current AI reviewer record through MAS owner surfaces, refresh "
                "medical-prose currentness and publication-gate replay, then decide downstream package freshness."
            ),
            "work_unit_fingerprint": (
                "domain-transition::ai_reviewer_re_eval::"
                "produce_ai_reviewer_publication_eval_record_against_current_inputs"
            ),
            "next_work_unit": {
                "unit_id": "consume_current_ai_reviewer_record_then_prose_gate_package_replay",
                "lane": "write",
                "summary": (
                    "Consume the current AI reviewer record, refresh medical-prose currentness, "
                    "replay the publication gate, and only then refresh downstream package/display surfaces."
                ),
            },
        }
    )
    return record


def _required_coverage() -> dict[str, object]:
    return {
        "uncertainty": {
            "method": "nonparametric_bootstrap_fixed_model_external_validation",
            "replicates": 200,
            "metrics_95ci": {
                "c_index": {"estimate": 0.72, "lower": 0.61, "upper": 0.82},
                "observed_expected_ratio": {"estimate": 0.98, "lower": 0.74, "upper": 1.28},
                "brier_5y": {"estimate": 0.06, "lower": 0.04, "upper": 0.09},
            },
        },
        "calibration": {
            "calibration_intercept": {"estimate": -0.12, "ci_95": {"lower": -0.35, "upper": 0.04}},
            "calibration_slope": {"estimate": 0.88, "ci_95": {"lower": 0.66, "upper": 1.08}},
        },
        "grouped_calibration": {
            "groups": [
                {
                    "group": 1,
                    "n": 100,
                    "mean_predicted_5y_risk": 0.02,
                    "observed_5y_rate": 0.01,
                    "observed_5y_rate_ci_95": {"lower": 0.0, "upper": 0.03},
                }
            ]
        },
    }


def test_consumed_ai_reviewer_receipt_routes_owner_route_to_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    evidence_ref = (
        study_root
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )
    _write_json(
        evidence_ref,
        {
            "surface": "unit_harmonized_external_validation_rerun_evidence",
            "schema_version": 1,
            "status": "completed",
            **_required_coverage(),
            "old_raw_scale_transport_claim_must_not_be_used_as_medical_conclusion": True,
        },
    )
    analysis_path = study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    _write_json(
        analysis_path,
        {
            "surface": "analysis_harmonization_owner_result",
            "schema_version": 1,
            "study_id": study_id,
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "completed",
            "unit_harmonized_rerun_completed": True,
            "rerun_evidence_ref": str(evidence_ref),
            "next_owner": "ai_reviewer",
            "next_work_unit": "ai_reviewer_medical_prose_quality_review",
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "medical_claim_authoring_allowed": False,
            "publication_eval_written": False,
            "controller_decision_written": False,
        },
    )
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::post-harmonization-write-route",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": {"trace_id": "ai-reviewer-os::post-harmonization"},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "partial"}},
        "recommended_actions": [
            {
                "action_id": "dm002-current-ai-reviewer-write-pass",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "work_unit_fingerprint": "dm002_current_manuscript_write_pass",
                "next_work_unit": {
                    "unit_id": "dm002_current_manuscript_write_pass",
                    "lane": "write",
                    "summary": "Repair current AI reviewer manuscript findings.",
                },
            }
        ],
    }
    completion_receipt_consumption = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "receipt_ref": "artifacts/publication_eval/latest.json",
        "eval_id": publication_eval["eval_id"],
        "reviewer_trace_ref": "artifacts/publication_eval/latest.json#reviewer_operating_system",
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }
    domain_transition = {
        "study_id": study_id,
        "decision_type": "route_back_same_line",
        "route_target": "write",
        "next_work_unit": {
            "unit_id": "dm002_current_manuscript_write_pass",
            "lane": "write",
            "summary": "Repair current AI reviewer manuscript findings.",
        },
        "controller_action": "request_opl_stage_attempt",
        "owner": "write",
        "typed_blocker": None,
        "guard_boundary": {
            "runner_boundary": "mas_domain_read_model_only",
            "required_owner_surface": "artifacts/publication_eval/latest.json",
        },
        "source_refs": ["artifacts/publication_eval/latest.json", str(analysis_path), str(evidence_ref)],
        "completion_receipt_consumption": completion_receipt_consumption,
    }
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "domain_transition": domain_transition,
        "runtime_health_snapshot": {
            "attempt_state": "recovering",
            "canonical_runtime_action": "recover_runtime",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-consumed-ai-reviewer-write",
            "source_signature": "truth-source-dm002-consumed-ai-reviewer-write",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "analysis-campaign",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_reviewer_request_lifecycle": {
            "surface": "ai_reviewer_request_lifecycle",
            "schema_version": 1,
            "state": "requested",
            "request_owner": "ai_reviewer",
            "request_id": "stale-ai-reviewer-request-before-consumed-routeback",
            "blocked_reason": "ai_reviewer_assessment_required",
        },
        "ai_repair_lifecycle": {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "state": "blocked",
            "authority": "external_supervisor",
            "auto_apply_allowed": True,
            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
            "top_action": {
                "action_type": "controller_repair",
                "owner": "mas_controller",
                "repair_kind": "analysis_claim_evidence_redrive",
                "auto_apply_allowed": True,
            },
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["domain_transition"]["completion_receipt_consumption"] == completion_receipt_consumption
    assert study["ai_reviewer_status"]["status"] == "trace_missing"
    assert study["ai_reviewer_assessment"]["request_state"] == "requested"
    assert study["ai_repair_lifecycle"] is None
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    assert study["action_queue"][0]["owner"] == "write"
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert study["owner_route"]["owner_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert study["blocked_reason"] == "quest_waiting_opl_runtime_owner_route"
    assert study["why_not_applied"] == "quest_waiting_opl_runtime_owner_route"


def test_consumed_ai_reviewer_receipt_routes_finalize_gate_replay_to_gate_clearing(
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
    eval_id = "publication-eval::dm003::current-manuscript-finalize-gate-replay"
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "route_back_required": True,
                    "route_target": "finalize",
                },
                "current_manuscript": {"status": "current"},
            },
            "publication_quality_readiness": {
                "status": "blocked",
                "missing_required_fields": ["owner_authorized_publication_gate_recheck"],
            },
        },
    }
    completion_receipt_consumption = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "receipt_ref": "artifacts/publication_eval/latest.json",
        "eval_id": eval_id,
        "reviewer_trace_ref": "artifacts/publication_eval/latest.json#reviewer_operating_system",
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }
    domain_transition = {
        "study_id": study_id,
        "decision_type": "route_back_same_line",
        "route_target": "finalize",
        "next_work_unit": {
            "unit_id": "owner_authorized_publication_gate_replay",
            "lane": "finalize",
            "summary": "Replay the MAS publication gate against current manuscript and evidence surfaces.",
        },
        "controller_action": "request_opl_stage_attempt",
        "owner": "finalize",
        "typed_blocker": None,
        "guard_boundary": {"required_owner_surface": "artifacts/publication_eval/latest.json"},
        "source_refs": ["artifacts/publication_eval/latest.json", "artifacts/controller_decisions/latest.json"],
        "completion_receipt_consumption": completion_receipt_consumption,
    }
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "domain_transition": domain_transition,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-finalize-gate-replay",
            "attempt_state": "escalated",
            "canonical_runtime_action": "external_supervisor_required",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-finalize-gate-replay",
            "source_signature": "truth-source-dm003-finalize-gate-replay",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "analysis-campaign",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": {
            "surface": "ai_repair_lifecycle",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "state": "blocked",
            "authority": "external_supervisor",
            "auto_apply_allowed": True,
            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
        },
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["domain_transition"]["completion_receipt_consumption"] == completion_receipt_consumption
    assert [action["action_type"] for action in study["action_queue"]] == ["run_gate_clearing_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "gate_clearing_batch"
    assert action["reason"] == "owner_authorized_publication_gate_replay"
    assert action["next_work_unit"] == "owner_authorized_publication_gate_replay"
    assert action["controller_work_unit_id"] == "owner_authorized_publication_gate_replay"
    assert action["original_route_target"] == "finalize"
    assert action["work_unit_fingerprint"] == (
        "domain-transition::route_back_same_line::owner_authorized_publication_gate_replay"
    )
    assert study["owner_route"]["next_owner"] == "gate_clearing_batch"
    assert study["owner_route"]["allowed_actions"] == ["run_gate_clearing_batch"]
    assert study["owner_route"]["owner_reason"] == "owner_authorized_publication_gate_replay"
    assert study["owner_route"]["owner_reason_contract"]["registered"] is True
    assert study["blocked_reason"] == "owner_authorized_publication_gate_replay"
    assert study["why_not_applied"] == "owner_authorized_publication_gate_replay"


def test_consumed_ai_reviewer_receipt_routes_dpcc_publication_gate_lane_to_gate_clearing(
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
    eval_id = "publication-eval::dm003::current-ai-reviewer-record"
    completion_receipt_consumption = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
        "eval_id": eval_id,
        "reviewer_trace_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json#reviewer_operating_system",
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "recommended_actions": [
            {
                "action_id": "dm003-consume-current-ai-reviewer-record",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "next_work_unit": {
                    "unit_id": work_unit_id,
                    "lane": "publication_gate",
                    "summary": "MAS publication-gate/currentness replay after current AI reviewer archive.",
                },
                "work_unit_fingerprint": "truth-snapshot::dm003-current-ai-reviewer-record",
            }
        ],
    }
    domain_transition = {
        "study_id": study_id,
        "decision_type": "route_back_same_line",
        "route_target": "write",
        "next_work_unit": {
            "unit_id": work_unit_id,
            "lane": "publication_gate",
            "summary": "MAS publication-gate/currentness replay after current AI reviewer archive.",
        },
        "controller_action": "request_opl_stage_attempt",
        "owner": "write",
        "typed_blocker": None,
        "guard_boundary": {"required_owner_surface": "artifacts/publication_eval/latest.json"},
        "source_refs": ["artifacts/publication_eval/ai_reviewer_responses/current.json"],
        "completion_receipt_consumption": completion_receipt_consumption,
    }
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "domain_transition": domain_transition,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-current-ai-reviewer-record",
            "attempt_state": "parked",
            "canonical_runtime_action": "request_opl_stage_attempt",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-current-ai-reviewer-record",
            "source_signature": "truth-source-dm003-current-ai-reviewer-record",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publication_gate",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["run_gate_clearing_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "gate_clearing_batch"
    assert action["reason"] == work_unit_id
    assert action["next_work_unit"] == work_unit_id
    assert action["controller_work_unit_id"] == work_unit_id
    assert action["original_route_target"] == "write"
    assert study["owner_route"]["next_owner"] == "gate_clearing_batch"
    assert study["owner_route"]["allowed_actions"] == ["run_gate_clearing_batch"]
    assert study["owner_route"]["owner_reason"] == work_unit_id
    assert study["owner_route"]["owner_reason_contract"]["registered"] is True


def test_consumed_ai_reviewer_receipt_clears_stale_analysis_reviewer_lifecycle_in_observe_mode(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::post-harmonization-observe-route",
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": {"trace_id": "ai-reviewer-os::post-harmonization-observe"},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "partial"}},
    }
    completion_receipt_consumption = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "receipt_ref": "artifacts/publication_eval/latest.json",
        "eval_id": publication_eval["eval_id"],
        "reviewer_trace_ref": "artifacts/publication_eval/latest.json#reviewer_operating_system",
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }
    domain_transition = {
        "study_id": study_id,
        "decision_type": "route_back_same_line",
        "route_target": "write",
        "next_work_unit": {
            "unit_id": "dm002_current_manuscript_write_pass",
            "lane": "write",
            "summary": "Repair current AI reviewer manuscript findings.",
        },
        "controller_action": "request_opl_stage_attempt",
        "owner": "write",
        "typed_blocker": None,
        "guard_boundary": {"required_owner_surface": "artifacts/publication_eval/latest.json"},
        "source_refs": ["artifacts/publication_eval/latest.json"],
        "completion_receipt_consumption": completion_receipt_consumption,
    }
    stale_lifecycle = {
        "surface": "ai_repair_lifecycle",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "state": "blocked",
        "blocked_reason": "analysis_harmonization_completed_ai_reviewer_review_required",
        "next_owner": "ai_reviewer",
        "external_supervisor_required": False,
    }
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "active",
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "domain_transition": domain_transition,
        "runtime_health_snapshot": {
            "attempt_state": "recovering",
            "canonical_runtime_action": "recover_runtime",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-consumed-ai-reviewer-observe",
            "source_signature": "truth-source-dm002-consumed-ai-reviewer-observe",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "auto_runtime_parked",
        "paper_stage": "analysis-campaign",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": stale_lifecycle,
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        apply_safe_actions=False,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["action_queue"] == []
    assert study["ai_repair_lifecycle"] is None
    assert study["owner_route"]["next_owner"] == "one-person-lab"
    assert study["owner_route"]["owner_reason"] == "opl_stage_attempt_admission_required"
    assert study["blocked_reason"] == "opl_stage_attempt_admission_required"
    assert study["why_not_applied"] == "opl_stage_attempt_admission_required"


def test_consumed_current_record_production_receipt_returns_to_write_without_reviewer_loop(
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
    manuscript_text = "# Draft\n\nCurrent DM003 manuscript after AI-reviewer record production.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    eval_id = "publication-eval::dm003::current-record::2026-05-29T01:22:50Z"
    publication_eval = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
        emitted_at="2026-05-29T01:22:50Z",
    )
    publication_eval["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "consume_current_manuscript_ai_reviewer_record_and_return_to_write",
        "lane": "write",
        "summary": "Consume the current AI reviewer record and repair prose, citations, and displays.",
    }
    publication_eval["recommended_actions"][0]["work_unit_fingerprint"] = (
        "sha256:dm003-current-ai-reviewer-record-write"
    )
    completion_receipt_consumption = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "receipt_ref": "artifacts/publication_eval/latest.json",
        "eval_id": eval_id,
        "reviewer_trace_ref": "artifacts/publication_eval/latest.json#reviewer_operating_system",
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }
    domain_transition = {
        "study_id": study_id,
        "decision_type": "ai_reviewer_re_eval",
        "route_target": "review",
        "next_work_unit": {
            "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "lane": "review",
            "summary": "Produce a current AI reviewer publication-eval record before dispatching the publication-eval workflow.",
        },
        "controller_action": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "typed_blocker": None,
        "guard_boundary": {"required_owner_surface": "artifacts/publication_eval/latest.json"},
        "source_refs": ["artifacts/publication_eval/latest.json"],
        "completion_receipt_consumption": completion_receipt_consumption,
    }
    stale_lifecycle = {
        "surface": "ai_repair_lifecycle",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "state": "blocked",
        "blocked_reason": "ai_reviewer_record_stale_after_current_manuscript",
        "next_owner": "ai_reviewer",
        "external_supervisor_required": False,
    }
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "resume",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "domain_transition": domain_transition,
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-dm003-current-record",
            "attempt_state": "idle",
            "canonical_runtime_action": "continue_supervising_runtime",
            "retry_budget_remaining": 2,
            "blocking_reasons": [],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm003-current-record",
            "source_signature": "truth-source-dm003-current-record",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "analysis-campaign",
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
        "ai_repair_lifecycle": stale_lifecycle,
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["domain_transition"]["completion_receipt_consumption"] == completion_receipt_consumption
    assert study["ai_reviewer_assessment"]["present"] is True
    assert study["ai_reviewer_assessment"]["missing"] is False
    assert study["ai_repair_lifecycle"] is None
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["next_work_unit"] == "consume_current_manuscript_ai_reviewer_record_and_return_to_write"
    assert action["source_eval_id"] == eval_id
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]


def test_consumed_current_input_record_archive_preempts_stale_reviewer_redrive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    canonical_inputs = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.canonical_inputs"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    manuscript_path = study_root / "paper" / "draft.md"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    manuscript_text = "# Draft\n\nCurrent DM002 manuscript after current-input AI reviewer record production.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    evidence_payload = {"schema_version": 1, "status": "current-input-evidence"}
    claim_map_payload = {"schema_version": 1, "status": "current-input-claims"}
    _write_json(evidence_path, evidence_payload)
    _write_json(claim_map_path, claim_map_payload)
    evidence_digest = "sha256:" + hashlib.sha256(
        (json.dumps(evidence_payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    ).hexdigest()
    claim_map_digest = "sha256:" + hashlib.sha256(
        (json.dumps(claim_map_payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    ).hexdigest()
    old_eval = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text="# Draft\n\nOlder DM002 manuscript before current inputs.\n",
        study_id=study_id,
        quest_id=quest_id,
        eval_id="publication-eval::dm002::old::2026-05-28T23:10:58+00:00::ai-reviewer-record",
        emitted_at="2026-05-28T23:10:58+00:00",
    )
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(latest_path, old_eval)
    eval_id = "publication-eval::002-dm-china-us-mortality-attribution::ai-reviewer-current-inputs::20260531T192047Z"
    record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260531T192320Z_publication_eval_record.json"
    )
    current_record = _current_input_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        evidence_path=evidence_path,
        evidence_digest=evidence_digest,
        claim_map_path=claim_map_path,
        claim_map_digest=claim_map_digest,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
    )
    _write_json(record_path, current_record)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                "stale_record_ref": str(record_path.resolve()),
                "required_currentness_refs": [
                    str(evidence_path.resolve()),
                    str(claim_map_path.resolve()),
                ],
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(manuscript_path.resolve()), "present": True, "valid": True},
                    "evidence_ledger": {"path": str(evidence_path.resolve()), "present": True, "valid": True},
                    "claim_evidence_map": {"path": str(claim_map_path.resolve()), "present": True, "valid": True},
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    completion_receipt_consumption = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "receipt_ref": str(record_path.resolve()),
        "eval_id": eval_id,
        "reviewer_trace_ref": f"{record_path.resolve()}#reviewer_operating_system",
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }
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
            "completion_receipt_consumption": completion_receipt_consumption,
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-current-input-record",
            "source_signature": "truth-source-dm002-current-input-record",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "publication_supervision",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(latest_path)},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    selected_publication_eval = canonical_inputs.publication_eval_payload(status_payload, progress_payload)
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, selected_publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["domain_transition"]["completion_receipt_consumption"] == completion_receipt_consumption
    assert study["ai_reviewer_assessment"]["present"] is True
    assert study["ai_reviewer_assessment"].get("blocked_reason") is None
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["next_work_unit"] == "consume_current_ai_reviewer_record_then_prose_gate_package_replay"
    assert action["source_eval_id"] == eval_id
    assert action["controller_route"]["publication_eval_ref"]["artifact_path"] == str(record_path.resolve())
    assert "owner_output_consumption" in action
    assert study["owner_route"]["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
