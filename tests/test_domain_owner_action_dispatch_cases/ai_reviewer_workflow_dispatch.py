from __future__ import annotations

import importlib
from pathlib import Path

from tests.ai_reviewer_record_fixture_helpers import minimal_ai_reviewer_record as _minimal_ai_reviewer_record
from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_domain_owner_action_dispatch_cases.ai_reviewer_workflow_helpers import (
    _complete_ai_reviewer_input_refs,
)


def test_execute_dispatch_blocks_ai_reviewer_when_record_payload_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(study_root / "paper" / "draft.md"), "present": True, "valid": True},
                    "evidence_ledger": {
                        "path": str(study_root / "paper" / "evidence_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
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
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        dispatch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "ai_reviewer_record_missing"
    assert execution["owner_callable_surface"] == "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
    assert execution["next_owner"] == "ai_reviewer"


def test_execute_dispatch_hands_off_ai_reviewer_record_production_when_request_record_stale_after_unit_harmonized_rerun(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    stale_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260517T074205Z_publication_eval_record.json"
    )
    required_currentness_refs = [
        str(study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"),
        str(
            study_root
            / "artifacts"
            / "controller"
            / "analysis_harmonization"
            / "unit_harmonized_external_validation_rerun.json"
        ),
    ]
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_stale_after_unit_harmonized_rerun",
                "stale_record_ref": str(stale_record_path),
                "required_currentness_refs": required_currentness_refs,
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(study_root / "paper" / "draft.md"), "present": True, "valid": True},
                    "evidence_ledger": {
                        "path": str(study_root / "paper" / "evidence_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
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
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    route.update(
        {
            "failure_signature": "ai_reviewer_record_stale_after_unit_harmonized_rerun",
            "owner_reason": "ai_reviewer_record_stale_after_unit_harmonized_rerun",
            "source_refs": {
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization",
                "blocked_reason": "ai_reviewer_record_stale_after_unit_harmonized_rerun",
            },
        }
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
            owner_route=route,
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["codex_dispatch_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
    assert execution["action_class"] == "codex_worker_dispatch"
    assert execution["will_start_llm"] is True
    assert execution["stale_record_ref"] == str(stale_record_path)
    assert execution["required_currentness_refs"] == required_currentness_refs
    production_request = execution["ai_reviewer_record_production_request"]
    assert production_request["surface"] == "ai_reviewer_record_production_request"
    assert production_request["request_kind"] == "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization"
    assert production_request["request_owner"] == "ai_reviewer"
    assert production_request["required_output_surface"] == (
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    )
    assert production_request["owner_callable_surface"] == "publication materialize-ai-reviewer-record"
    assert production_request["stale_record_ref"] == str(stale_record_path)
    assert production_request["required_currentness_refs"] == required_currentness_refs
    assert production_request["record_must_consume_refs"] == required_currentness_refs
    assert production_request["required_input_refs"]["manuscript"] == str(study_root / "paper" / "draft.md")
    assert production_request["required_input_refs"]["evidence_ledger"] == str(
        study_root / "paper" / "evidence_ledger.json"
    )
    assert production_request["authority_contract"] == {
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "publication_eval_latest_write_allowed": False,
        "controller_decision_write_allowed": False,
        "record_only_surface": True,
    }
    assert "artifacts/publication_eval/latest.json" in production_request["forbidden_surfaces"]
    assert "artifacts/controller_decisions/latest.json" in production_request["forbidden_surfaces"]
    assert execution["next_required_actions"] == [
        "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization",
        "rematerialize_ai_reviewer_request",
        "return_to_ai_reviewer_workflow",
    ]
    handoff = execution["ai_reviewer_record_worker_handoff"]
    assert handoff["surface"] == "default_executor_dispatch_request"
    assert handoff["dispatch_status"] == "ready"
    assert handoff["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert handoff["next_executable_owner"] == "ai_reviewer"
    assert handoff["required_output_surface"] == (
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    )
    assert handoff["owner_route"]["owner_reason"] == "ai_reviewer_record_stale_after_unit_harmonized_rerun"
    assert handoff["owner_route"]["source_refs"]["work_unit_id"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization"
    )
    assert handoff["prompt_contract"]["allowed_write_surfaces"] == [
        "artifacts/supervision/requests/ai_reviewer/record_production_payloads/*_payload.json",
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
    ]
    assert "artifacts/publication_eval/latest.json" in handoff["forbidden_surfaces"]
    assert "artifacts/controller_decisions/latest.json" in handoff["forbidden_surfaces"]


def test_execute_dispatch_blocks_ai_reviewer_when_request_record_leaks_repair_story(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    stale_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260517T074205Z_publication_eval_record.json"
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {
                "state": "requested",
                "blocked_reason": "ai_reviewer_record_manuscript_story_provenance_leakage",
                "stale_record_ref": str(stale_record_path),
                "leakage_reason": "manuscript_story_provenance_leakage",
                "leakage_field_path": "quality_assessment.novelty_positioning.summary",
            },
            "input_contract": {
                "required_refs": {
                    "manuscript": {"path": str(study_root / "paper" / "draft.md"), "present": True, "valid": True},
                    "evidence_ledger": {
                        "path": str(study_root / "paper" / "evidence_ledger.json"),
                        "present": True,
                        "valid": True,
                    },
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
                },
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "ai_reviewer_record_manuscript_story_provenance_leakage"
    assert execution["stale_record_ref"] == str(stale_record_path)
    assert execution["leakage_reason"] == "manuscript_story_provenance_leakage"
    assert execution["leakage_field_path"] == "quality_assessment.novelty_positioning.summary"
    assert execution["next_required_actions"] == [
        "produce_ai_reviewer_publication_eval_record_against_current_medical_prose_style_v3",
        "rematerialize_ai_reviewer_request",
        "return_to_ai_reviewer_workflow",
    ]


def test_execute_dispatch_runs_ai_reviewer_owner_workflow(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    input_refs = _complete_ai_reviewer_input_refs(study_root)
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": input_refs,
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
            "ai_reviewer_record": _minimal_ai_reviewer_record(
                study_id,
                f"quest-{study_id}",
                "publication-eval::001::quest::2026-05-05T00:00:00+00:00",
            ),
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        dispatch,
    )
    called: dict[str, object] = {}

    def fake_run_ai_reviewer_publication_eval_workflow(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {"assessment_provenance": {"owner": "ai_reviewer"}},
        )
        return {
            "surface": "ai_reviewer_publication_eval_workflow",
            "status": "materialized",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "eval_id": "publication-eval::001::quest::2026-05-05T00:00:00+00:00",
        }

    monkeypatch.setattr(
        module.action_execution.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        fake_run_ai_reviewer_publication_eval_workflow,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_callable_surface"] == "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
    assert called["study_root"] == study_root
    assert called["manuscript_ref"] == input_refs["manuscript"]["path"]
    assert called["evidence_ref"] == input_refs["evidence_ledger"]["path"]
    assert called["review_ref"] == input_refs["review_ledger"]["path"]
    assert called["charter_ref"] == input_refs["study_charter"]["path"]
    assert called["additional_refs"] == {
        "medical_manuscript_blueprint": input_refs["medical_manuscript_blueprint"]["path"],
        "claim_evidence_map": input_refs["claim_evidence_map"]["path"],
        "medical_prose_review": input_refs["medical_prose_review"]["path"],
        "publication_gate_projection": input_refs["publication_gate_projection"]["path"],
    }
    assert called["workflow_currentness_mode"] == "request_bound_ai_reviewer_record"
    assert called["record"]["study_id"] == study_id
    assert (study_root / "artifacts" / "publication_eval" / "latest.json").is_file()


def test_execute_dispatch_blocks_ai_reviewer_workflow_without_materialized_latest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    input_refs = _complete_ai_reviewer_input_refs(study_root)
    _write_json(
        request_path,
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "ai_reviewer_record": _minimal_ai_reviewer_record(
                study_id,
                study_id,
                {
                    "assessment_provenance": {
                        "owner": "ai_reviewer",
                        "source_kind": "publication_eval_ai_reviewer",
                    },
                    "recommended_actions": [{"action_type": "return_to_controller"}],
                },
            ),
            "input_contract": {
                "required_refs": input_refs,
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
            "ai_reviewer_record": _minimal_ai_reviewer_record(
                study_id,
                f"quest-{study_id}",
                "publication-eval::001::quest::2026-05-05T00:00:00+00:00",
            ),
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )

    def fake_run_ai_reviewer_publication_eval_workflow(**_: object) -> dict[str, object]:
        return {
            "surface": "ai_reviewer_publication_eval_workflow",
            "status": "materialized",
            "publication_eval_surface": "artifacts/publication_eval/latest.json",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "eval_id": "publication-eval::001::quest::2026-05-05T00:00:00+00:00",
        }

    monkeypatch.setattr(
        module.action_execution.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        fake_run_ai_reviewer_publication_eval_workflow,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 0
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "ai_reviewer_workflow_output_missing"
    assert execution["error"] == "artifact_path_not_written"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_dispatch_routes_stale_live_manuscript_prose_review_to_rehydrate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    input_refs = _complete_ai_reviewer_input_refs(study_root)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": input_refs,
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
            "ai_reviewer_record": _minimal_ai_reviewer_record(
                study_id,
                f"quest-{study_id}",
                "publication-eval::003::quest::2026-05-22T00:00:00+00:00",
            ),
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )

    def stale_live_manuscript_review(**_kwargs) -> dict[str, object]:
        raise ValueError("medical_prose_review_live_manuscript_digest_mismatch")

    monkeypatch.setattr(
        module.action_execution.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        stale_live_manuscript_review,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "medical_prose_review_request_rehydrate_required"
    assert execution["next_owner"] == "ai_reviewer"
    assert execution["error"] == "medical_prose_review_live_manuscript_digest_mismatch"
    assert execution["owner_result"]["stale_medical_prose_review_reuse_allowed"] is False
    assert execution["owner_result"]["quality_verdict_written"] is False
    assert "produce_ai_reviewer_medical_prose_review_against_current_manuscript" in execution["owner_result"][
        "next_required_actions"
    ]
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_execute_dispatch_after_paper_authority_cutover_ignores_archived_latest_and_builds_new_record(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    receipt_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "latest.json"
    )
    _write_json(
        receipt_path,
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_id,
        },
    )
    input_refs = _complete_ai_reviewer_input_refs(study_root, publication_gate_projection=receipt_path)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": input_refs,
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )
    called: dict[str, object] = {}

    def fake_run_ai_reviewer_publication_eval_workflow(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {"assessment_provenance": {"owner": "ai_reviewer", "source_kind": "publication_eval_ai_reviewer"}},
        )
        return {
            "surface": "ai_reviewer_publication_eval_workflow",
            "status": "materialized",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "eval_id": "publication-eval::002::quest::clean-migration",
        }

    monkeypatch.setattr(
        module.action_execution.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        fake_run_ai_reviewer_publication_eval_workflow,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert called["additional_refs"]["publication_gate_projection"] == str(receipt_path)
    assert called["record"]["assessment_provenance"]["source_kind"] == "publication_eval_ai_reviewer"
    assert called["record"]["quality_assessment"]["medical_journal_prose_quality"]["status"] == "underdefined"
    assert "route_target" not in called["record"]["recommended_actions"][0]
    assert "route_key_question" not in called["record"]["recommended_actions"][0]
    assert "route_rationale" not in called["record"]["recommended_actions"][0]
    assert called["record"]["recommended_actions"][0]["action_type"] == "return_to_controller"
    from med_autoscience.publication_eval_record import PublicationEvalRecord

    PublicationEvalRecord.from_payload(called["record"])


def test_execute_dispatch_passes_reporting_guideline_and_calibration_refs_to_ai_reviewer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    reporting_guideline = study_root / "paper" / "reporting_guideline.json"
    calibration_refs = study_root / "artifacts" / "ai_reviewer" / "calibration_refs.json"
    _write_json(reporting_guideline, {"guideline": "STROBE"})
    _write_json(calibration_refs, {"case_family": "claim_overreach"})
    input_refs = _complete_ai_reviewer_input_refs(
        study_root,
        extra_refs={
            "reporting_guideline": reporting_guideline,
            "calibration_refs": calibration_refs,
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {"required_refs": input_refs},
            "ai_reviewer_record": _minimal_ai_reviewer_record(
                study_id,
                f"quest-{study_id}",
                "publication-eval::001::quest::2026-05-05T00:00:00+00:00",
            ),
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    _write_current_dispatch(dispatch_path, profile, dispatch)
    called: dict[str, object] = {}

    def fake_run_ai_reviewer_publication_eval_workflow(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {"assessment_provenance": {"owner": "ai_reviewer"}},
        )
        return {
            "surface": "ai_reviewer_publication_eval_workflow",
            "status": "materialized",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        }

    monkeypatch.setattr(
        module.action_execution.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        fake_run_ai_reviewer_publication_eval_workflow,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert called["additional_refs"]["reporting_guideline"] == str(reporting_guideline)
    assert called["additional_refs"]["calibration_refs"] == str(calibration_refs)


def test_execute_dispatch_runs_ai_reviewer_when_current_owner_route_carries_terminal_stall(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    input_refs = _complete_ai_reviewer_input_refs(study_root)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "write/ai_reviewer",
            "input_contract": {"required_refs": input_refs},
            "ai_reviewer_record": _minimal_ai_reviewer_record(
                study_id,
                f"quest-{study_id}",
                "publication-eval::003::quest::2026-05-09T00:00:00+00:00",
            ),
        },
    )
    route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": f"quest-{study_id}",
        "truth_epoch": "truth-event-current-handoff",
        "runtime_health_epoch": "runtime-health-terminal-stall",
        "work_unit_fingerprint": "truth-snapshot::terminal-owner-handoff",
        "failure_signature": "controller_work_unit_owner_handoff_required",
        "trace_id": "owner-route-trace::terminal-owner-handoff",
        "route_epoch": "truth-event-current-handoff",
        "source_fingerprint": "truth-snapshot::terminal-owner-handoff",
        "current_owner": "mas_controller",
        "next_owner": "write/ai_reviewer",
        "owner_reason": "controller_work_unit_owner_handoff_required",
        "active_run_id": None,
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "blocked_actions": [
            "publication_gate_specificity_required",
            "current_package_freshness_required",
            "artifact_display_surface_materialization_required",
        ],
        "idempotency_key": "owner-route::003::write-ai-reviewer::terminal-owner-handoff",
    }
    stall = {
        "surface_kind": "paper_progress_stall",
        "stalled": True,
        "terminal": True,
        "action_fingerprint": "paper_progress_stall:terminal-owner-handoff",
        "stall_reasons": [
            "same_fingerprint_loop",
            "runtime_recovery_retry_budget_exhausted",
        ],
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="write/ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["paper_progress_stall"] = stall
    dispatch["prompt_contract"]["repeat_suppression_key"] = "truth-snapshot::terminal-owner-handoff"
    _write_current_dispatch(dispatch_path, profile, dispatch)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "paper_progress_stall": stall,
                    "meaningful_artifact_delta": True,
                    "ai_reviewer_assessment": {
                        "present": True,
                        "missing": False,
                        "owner": "ai_reviewer",
                    },
                }
            ],
        },
    )
    called: dict[str, object] = {}

    def fake_run_ai_reviewer_publication_eval_workflow(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {"assessment_provenance": {"owner": "ai_reviewer"}},
        )
        return {
            "surface": "ai_reviewer_publication_eval_workflow",
            "status": "materialized",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        }

    monkeypatch.setattr(
        module.action_execution.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        fake_run_ai_reviewer_publication_eval_workflow,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_callable_surface"] == "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
    assert execution["current_paper_progress_stall"]["terminal"] is True
    assert called["study_root"] == study_root
