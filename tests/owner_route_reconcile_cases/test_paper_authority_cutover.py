from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_routes_clean_paper_authority_cutover_to_ai_reviewer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    migration = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json",
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_id,
        },
    )
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_id": f"return_to_ai_reviewer_workflow::{study_id}",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": {},
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "canonical_runtime_action": "observe",
            "attempt_state": "parked",
            "blocking_reasons": [],
        },
        "publication_eval": {
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "legacy_recheck",
                "ai_reviewer_required": False,
            },
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-cutover",
            "source_signature": "truth-source-cutover",
        },
        "study_macro_state": {
            "writer_state": "parked",
            "reason": "external_info",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "current_stage": "auto_runtime_parked",
        "paper_stage": "bundle_stage_ready",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
        "ai_reviewer_request_lifecycle": {
            "surface": "ai_reviewer_request_lifecycle",
            "state": "requested",
            "request_id": f"return_to_ai_reviewer_workflow::{study_id}",
            "request_owner": "ai_reviewer",
            "refs": {"request_path": str(request_path)},
        },
    }

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            status_payload,
            progress_payload,
            study_id,
            migration.cutover_publication_eval_payload(study_root=study_root),
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"]["missing"] is True
    assert study["ai_reviewer_assessment"]["owner"] == "ai_reviewer"
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["blocked_reason"] == "paper_authority_clean_migration_required"
    assert study["next_owner"] == "ai_reviewer"


def test_scan_domain_routes_routes_clean_cutover_rehydrate_blocker_to_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    migration = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json",
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_id,
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "blocked",
                    "blocked_reason": "canonical_paper_inputs_rehydrate_required",
                    "next_owner": "write",
                    "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
                    "required_input_surface": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                    "owner_result": {
                        "surface_kind": "canonical_paper_inputs_rehydrate_blocker",
                        "authority_source_signature": "paper_authority_clean_migration",
                        "canonical_surface": "paper/medical_manuscript_blueprint.json",
                        "legacy_artifact_reader_allowed": False,
                        "mechanical_blueprint_as_canonical_allowed": False,
                        "next_owner": "write",
                    },
                }
            ],
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "canonical_runtime_action": "observe",
            "attempt_state": "parked",
            "blocking_reasons": [],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-cutover",
            "source_signature": "truth-source-cutover",
        },
        "study_macro_state": {
            "writer_state": "parked",
            "reason": "external_info",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "current_stage": "auto_runtime_parked",
        "paper_stage": "bundle_stage_ready",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
    }

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            status_payload,
            progress_payload,
            study_id,
            migration.cutover_publication_eval_payload(study_root=study_root),
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["canonical_paper_inputs_rehydrate_required"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["request_owner"] == "write"
    assert action["recommended_owner"] == "write"
    assert action["reason"] == "canonical_paper_inputs_rehydrate_required"
    assert action["required_input_surface"].endswith("paper/medical_manuscript_blueprint.json")
    assert action["required_output_surface"].endswith("paper/medical_manuscript_blueprint_source.json")
    assert study["blocked_reason"] == "canonical_paper_inputs_rehydrate_required"
    assert study["next_owner"] == "write"


def test_scan_domain_routes_routes_clean_cutover_quality_repair_no_paper_root_to_write(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    migration = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "004-dpcc-longitudinal-care-inertia-intensification-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json",
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_id,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": "publication-eval::clean-migration",
            "status": "blocked_no_paper_root",
            "ok": False,
            "quest_id": study_id,
            "study_id": study_id,
            "blocked_reason": "canonical_paper_inputs_rehydrate_required",
            "next_owner": "write",
            "paper_owner_surface_prepare": {
                "status": "blocked_missing_projection",
                "paper_root": str(study_root / "paper"),
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "canonical_runtime_action": "observe",
            "attempt_state": "parked",
            "blocking_reasons": [],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-cutover",
            "source_signature": "truth-source-cutover",
        },
        "study_macro_state": {
            "writer_state": "parked",
            "reason": "external_info",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "current_stage": "auto_runtime_parked",
        "paper_stage": "bundle_stage_ready",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
    }

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            status_payload,
            progress_payload,
            study_id,
            migration.cutover_publication_eval_payload(study_root=study_root),
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["canonical_paper_inputs_rehydrate_required"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "canonical_paper_inputs_rehydrate_required"
    assert action["legacy_artifact_reader_allowed"] is False
    assert action["mechanical_blueprint_as_canonical_allowed"] is False
    assert study["blocked_reason"] == "canonical_paper_inputs_rehydrate_required"
    assert study["next_owner"] == "write"


def test_scan_domain_routes_keeps_clean_cutover_rehydrate_failure_on_write_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    migration = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json",
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_id,
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "canonical_paper_inputs_rehydrate_required",
                    "execution_status": "blocked",
                    "blocked_reason": "canonical_paper_inputs_rehydrate_failed",
                    "next_owner": "write",
                    "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
                    "required_output_surface": str(study_root / "paper" / "medical_manuscript_blueprint_source.json"),
                    "error": "medical manuscript blueprint is invalid: main_findings_by_clinical_importance must be a non-empty list",
                }
            ],
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "canonical_runtime_action": "observe",
            "attempt_state": "parked",
            "blocking_reasons": [],
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-cutover",
            "source_signature": "truth-source-cutover",
        },
        "study_macro_state": {
            "writer_state": "parked",
            "reason": "external_info",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "current_stage": "auto_runtime_parked",
        "paper_stage": "bundle_stage_ready",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
    }

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            status_payload,
            progress_payload,
            study_id,
            migration.cutover_publication_eval_payload(study_root=study_root),
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["canonical_paper_inputs_rehydrate_required"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "canonical_paper_inputs_rehydrate_required"
    assert action["required_output_surface"].endswith("paper/medical_manuscript_blueprint_source.json")
    assert study["blocked_reason"] == "canonical_paper_inputs_rehydrate_required"
    assert study["next_owner"] == "write"


def test_scan_domain_routes_defers_clean_cutover_rehydrate_when_scientific_anchor_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    migration = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "004-dpcc-longitudinal-care-inertia-intensification-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    _write_json(
        study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json",
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_id,
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "canonical_paper_inputs_rehydrate_required",
                    "execution_status": "blocked",
                    "blocked_reason": "canonical_paper_inputs_rehydrate_failed",
                    "next_owner": "write",
                    "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
                    "required_output_surface": str(study_root / "paper" / "medical_manuscript_blueprint_source.json"),
                    "error": "medical manuscript blueprint is invalid: main_findings_by_clinical_importance must be a non-empty list",
                }
            ],
        },
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "gate_kind": "publishability_control",
            "status": "blocked",
            "blockers": ["missing_publication_anchor"],
            "anchor_kind": "missing",
            "main_result_path": None,
            "paper_root": None,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "supervisor_phase": "scientific_anchor_missing",
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "reason": "quest_waiting_platform_repair_redrive",
        "runtime_health_snapshot": {
            "canonical_runtime_action": "external_supervisor_required",
            "attempt_state": "escalated",
            "retry_budget_remaining": 0,
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
        },
        "publication_supervisor_state": {
            "supervisor_phase": "scientific_anchor_missing",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": False,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-cutover",
            "source_signature": "truth-source-cutover",
        },
        "study_macro_state": {
            "writer_state": "blocked",
            "reason": "scientific_anchor_missing",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_runtime_recovering",
        "paper_stage": "scientific_anchor_missing",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "recovering"},
        "quality_review_loop": {"closure_state": "review_required"},
    }

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            status_payload,
            progress_payload,
            study_id,
            migration.cutover_publication_eval_payload(study_root=study_root),
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["publication_gate_specificity_required"]
    action = study["action_queue"][0]
    assert action["owner"] == "publication_gate"
    assert action["reason"] == "publication_gate_specificity_required"
    assert action["scientific_anchor_required"] is True
    assert action["write_rehydrate_deferred"] is True
    assert study["blocked_reason"] == "publication_gate_specificity_required"
    assert study["next_owner"] == "publication_gate"
