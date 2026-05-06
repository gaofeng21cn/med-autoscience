from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.runtime_supervisor_dispatch_executor_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
    write_scan_latest as _write_scan_latest,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_blocks_ai_reviewer_when_request_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
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

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "ai_reviewer_request_missing"
    assert execution["owner_callable_surface"] == "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
    assert execution["next_owner"] == "ai_reviewer"
    latest = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_execution"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    assert latest["blocked_count"] == 1
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()


def test_execute_dispatch_blocks_dispatch_without_owner_route(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
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
    route = dict(dispatch["owner_route"])
    del dispatch["owner_route"]
    del dispatch["prompt_contract"]["owner_route"]
    del dispatch["prompt_contract"]["idempotency_key"]
    _write_json(dispatch_path, dispatch)
    _write_scan_latest(profile, study_id, route)
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "runtime_supervisor_consumer",
            "schema_version": 1,
            "default_executor_dispatches": [{**dispatch, "refs": {"dispatch_path": str(dispatch_path)}}],
        },
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "blocked"
    assert execution["blocked_reason"] == "owner_route_missing"


def test_execute_dispatch_blocks_ai_reviewer_when_record_payload_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
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

    result = module.execute_default_executor_dispatches(
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


def test_execute_dispatch_runs_ai_reviewer_owner_workflow(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    input_refs = {
        "manuscript": {"path": str(study_root / "paper" / "draft.md"), "present": True, "valid": True},
        "evidence_ledger": {"path": str(study_root / "paper" / "evidence_ledger.json"), "present": True, "valid": True},
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
        "claim_evidence_map": {
            "path": str(study_root / "paper" / "claim_evidence_map.json"),
            "present": True,
            "valid": True,
        },
        "medical_prose_review": {
            "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
            "present": True,
            "valid": True,
        },
        "publication_gate_projection": {
            "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "present": True,
            "valid": True,
        },
    }
    _write_json(
        request_path,
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": input_refs,
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
            "ai_reviewer_record": {
                "eval_id": "publication-eval::001::quest::2026-05-05T00:00:00+00:00",
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
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
        module.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        fake_run_ai_reviewer_publication_eval_workflow,
    )

    result = module.execute_default_executor_dispatches(
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
    assert called["record"]["study_id"] == study_id
    assert (study_root / "artifacts" / "publication_eval" / "latest.json").is_file()


def test_execute_dispatch_runs_current_package_freshness_owner_workflow(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "current_package_freshness_required.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="current_package_freshness_required",
        owner="artifact_os",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        dispatch,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_run_gate_clearing_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        }

    monkeypatch.setattr(module.gate_clearing_batch, "run_gate_clearing_batch", fake_run_gate_clearing_batch)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("current_package_freshness_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_callable_surface"] == "gate_clearing_batch.run_gate_clearing_batch"
    assert called["profile"] == profile
    assert called["study_id"] == study_id
    assert called["study_root"] == study_root
    assert called["quest_id"] == f"quest-{study_id}"
    assert called["source"] == "runtime_supervisor_dispatch_executor"
    route_context = called["control_plane_route_context"]["controller_route_context"]
    assert route_context["control_surface"] == "gate_clearing_batch"
    assert route_context["controller_action_type"] == "run_gate_clearing_batch"
    assert route_context["work_unit_id"] == "submission_minimal_refresh"


def test_execute_dispatch_uses_existing_publication_eval_for_ai_reviewer_record(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    input_refs = {
        "manuscript": {"path": str(study_root / "paper" / "draft.md"), "present": True, "valid": True},
        "evidence_ledger": {"path": str(study_root / "paper" / "evidence_ledger.json"), "present": True, "valid": True},
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
        "claim_evidence_map": {
            "path": str(study_root / "paper" / "claim_evidence_map.json"),
            "present": True,
            "valid": True,
        },
        "medical_prose_review": {
            "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
            "present": True,
            "valid": True,
        },
        "publication_gate_projection": {
            "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "present": True,
            "valid": True,
        },
    }
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
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::001::quest::2026-05-05T00:00:00+00:00",
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
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
        module.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        fake_run_ai_reviewer_publication_eval_workflow,
    )

    result = module.execute_default_executor_dispatches(
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
    assert called["record"]["eval_id"] == "publication-eval::001::quest::2026-05-05T00:00:00+00:00"
    assert called["record"]["quality_assessment"]["medical_journal_prose_quality"]["status"] == "underdefined"
    assert called["additional_refs"]["publication_gate_projection"] == input_refs["publication_gate_projection"]["path"]


def test_execute_dispatch_prefers_current_publication_eval_over_stale_request_record(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    input_refs = {
        "manuscript": {"path": str(study_root / "paper" / "draft.md"), "present": True, "valid": True},
        "evidence_ledger": {"path": str(study_root / "paper" / "evidence_ledger.json"), "present": True, "valid": True},
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
        "claim_evidence_map": {
            "path": str(study_root / "paper" / "claim_evidence_map.json"),
            "present": True,
            "valid": True,
        },
        "medical_prose_review": {
            "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
            "present": True,
            "valid": True,
        },
        "publication_gate_projection": {
            "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "present": True,
            "valid": True,
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "input_contract": {"required_refs": input_refs},
            "ai_reviewer_record": {
                "eval_id": "publication-eval::stale-request-record",
                "study_id": study_id,
                "quest_id": f"quest-{study_id}",
                "recommended_actions": [{"specificity_targets": [{"target_kind": "claim"}]}],
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::current-projection",
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "quality_assessment": {"medical_journal_prose_quality": {"status": "underdefined"}},
            "recommended_actions": [
                {
                    "specificity_targets": [
                        {"target_kind": "claim"},
                        {"target_kind": "metric"},
                    ]
                }
            ],
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
        return {
            "surface": "ai_reviewer_publication_eval_workflow",
            "status": "materialized",
            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            "eval_id": "publication-eval::current-projection",
        }

    monkeypatch.setattr(
        module.ai_reviewer_publication_eval_workflow,
        "run_ai_reviewer_publication_eval_workflow",
        fake_run_ai_reviewer_publication_eval_workflow,
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("return_to_ai_reviewer_workflow",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert called["record"]["eval_id"] == "publication-eval::current-projection"
    assert called["record"]["recommended_actions"][0]["specificity_targets"] == [
        {"target_kind": "claim"},
        {"target_kind": "metric"},
    ]


def test_execute_dispatch_runs_publication_gate_owner_surface(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "publication_gate_specificity_required.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        dispatch,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": f"quest-{study_id}",
            "quest_root": str(quest_root),
        },
    )
    called: dict[str, object] = {}

    def fake_build_gate_state(quest_root_arg) -> dict[str, object]:
        called["quest_root"] = quest_root_arg
        return {"quest_root": quest_root_arg}

    def fake_build_gate_report(state) -> dict[str, object]:
        called["state"] = state
        return {
            "generated_at": "2026-05-05T00:00:00+00:00",
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
        }

    def fake_write_gate_files(quest_root_arg, report) -> tuple[Path, Path]:
        called["write_quest_root"] = quest_root_arg
        called["report"] = report
        json_path = quest_root_arg / "artifacts" / "reports" / "publishability_gate" / "latest.json"
        md_path = quest_root_arg / "artifacts" / "reports" / "publishability_gate" / "latest.md"
        _write_json(json_path, report)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text("# gate\n", encoding="utf-8")
        return json_path, md_path

    def fake_materialize_publication_eval_latest(**kwargs) -> dict[str, str]:
        called["materialize_kwargs"] = kwargs
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {
                "surface": "publication_eval",
                "recommended_actions": [
                    {
                        "action_type": "return_to_controller",
                        "specificity_targets": [
                            {
                                "target_kind": "claim",
                                "target_id": "primary_claim",
                                "source_path": "paper/claim_evidence_map.json",
                                "blocking_reason": "claim_evidence_consistency_failed",
                            },
                            {
                                "target_kind": "figure",
                                "target_id": "figure_catalog",
                                "source_path": "paper/figures/figure_catalog.json",
                                "blocking_reason": "figure_semantics_manifest_missing_or_incomplete",
                            },
                            {
                                "target_kind": "table",
                                "target_id": "submission_manifest",
                                "source_path": "paper/submission_minimal/submission_manifest.json",
                                "blocking_reason": "submission_hardening_incomplete",
                            },
                            {
                                "target_kind": "metric",
                                "target_id": "main_result_metrics",
                                "source_path": "artifacts/results/main_result.json",
                                "blocking_reason": "derived_analysis_manifest_missing_or_incomplete",
                            },
                            {
                                "target_kind": "source_path",
                                "target_id": "gate_report",
                                "source_path": "artifacts/reports/publishability_gate/latest.json",
                                "blocking_reason": "publication_gate_blocked",
                            },
                        ],
                    }
                ],
            },
        )
        return {"artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")}

    monkeypatch.setattr(module.publication_gate, "build_gate_state", fake_build_gate_state)
    monkeypatch.setattr(module.publication_gate, "build_gate_report", fake_build_gate_report)
    monkeypatch.setattr(module.publication_gate, "write_gate_files", fake_write_gate_files)
    monkeypatch.setattr(module.publication_gate, "_materialize_publication_eval_latest", fake_materialize_publication_eval_latest)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_gate_specificity_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["owner_callable_surface"] == "publication_gate.write_gate_files+_materialize_publication_eval_latest"
    assert called["quest_root"] == quest_root
    assert called["write_quest_root"] == quest_root
    assert called["materialize_kwargs"]["report"]["latest_gate_path"].endswith("latest.json")
    assert (study_root / "artifacts" / "publication_eval" / "latest.json").is_file()


def test_execute_dispatch_defaults_to_current_consumer_dispatches(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch_dir = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_dispatches"
    current_dispatch_path = dispatch_dir / "publication_gate_specificity_required.json"
    stale_ai_dispatch_path = dispatch_dir / "return_to_ai_reviewer_workflow.json"
    stale_runtime_dispatch_path = dispatch_dir / "runtime_platform_repair.json"
    current_dispatch = _dispatch(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    current_dispatch["refs"] = {"dispatch_path": str(current_dispatch_path)}
    _write_json(current_dispatch_path, current_dispatch)
    _write_scan_latest(profile, study_id, dict(current_dispatch["owner_route"]))
    _write_json(
        stale_ai_dispatch_path,
        _dispatch(
            study_id=study_id,
            action_type="return_to_ai_reviewer_workflow",
            owner="ai_reviewer",
            required_output_surface="artifacts/publication_eval/latest.json",
        ),
    )
    _write_json(
        stale_runtime_dispatch_path,
        _dispatch(
            study_id=study_id,
            action_type="runtime_platform_repair",
            owner="external_engineering_agent",
            required_output_surface="artifacts/supervision/consumer/runtime_platform_repair.json",
        ),
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "runtime_supervisor_consumer",
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [current_dispatch],
        },
    )
    executed_action_types: list[str] = []

    def fake_publication_gate_specificity(**kwargs) -> dict[str, object]:
        executed_action_types.append("publication_gate_specificity_required")
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "publication_gate.write_gate_files+_materialize_publication_eval_latest",
        }

    def fail_stale_dispatch(**kwargs) -> dict[str, object]:
        raise AssertionError("stale dispatch should not execute")

    monkeypatch.setattr(module, "_execute_publication_gate_specificity", fake_publication_gate_specificity)
    monkeypatch.setattr(module, "_execute_ai_reviewer_workflow", fail_stale_dispatch)
    monkeypatch.setattr(module, "_execute_runtime_platform_repair", fail_stale_dispatch)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert executed_action_types == ["publication_gate_specificity_required"]
    latest = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_execution"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    assert [item["action_type"] for item in latest["executions"]] == ["publication_gate_specificity_required"]


def test_execute_dispatch_rejects_incomplete_forbidden_surface_contract(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch = _dispatch(
        study_id=study_id,
        action_type="runtime_platform_repair",
        owner="external_engineering_agent",
        required_output_surface="artifacts/supervision/consumer/runtime_platform_repair.json",
    )
    dispatch["prompt_contract"]["forbidden_surfaces"] = ["paper/**"]
    _write_current_dispatch(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "runtime_platform_repair.json",
        profile,
        dispatch,
    )

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("runtime_platform_repair",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["blocked_count"] == 1
    assert result["executions"][0]["blocked_reason"] == "forbidden_surfaces_incomplete"


def test_runtime_platform_repair_dispatch_uses_non_persistent_scan(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    scan_module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    latest_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    dispatch = _dispatch(
        study_id=study_id,
        action_type="runtime_platform_repair",
        owner="external_engineering_agent",
        required_output_surface="artifacts/supervision/consumer/runtime_platform_repair.json",
    )
    _write_json(
        latest_path,
        {
            "surface": "portable_runtime_supervisor_scan",
            "generated_at": "2026-05-05T00:00:00+00:00",
            "studies": [
                {"study_id": "001-dm-cvd-mortality-risk"},
                {"study_id": study_id, "owner_route": dispatch["owner_route"]},
            ],
        },
    )
    _write_current_dispatch(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "runtime_platform_repair.json",
        profile,
        dispatch,
    )
    before = latest_path.read_text(encoding="utf-8")
    called: dict[str, object] = {}

    def fake_supervisor_scan(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        assert kwargs["persist_surfaces"] is False
        return {
            "surface": "portable_runtime_supervisor_scan",
            "studies": [
                {
                    "study_id": study_id,
                    "runtime_platform_repair_apply": {
                        "dispatch_status": "applied",
                        "reason": "stale_specificity_terminal_gate_cleared",
                    },
                }
            ],
        }

    monkeypatch.setattr(scan_module, "supervisor_scan", fake_supervisor_scan)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("runtime_platform_repair",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert called["study_ids"] == (study_id,)
    assert called["apply_runtime_platform_repair"] is True
    assert latest_path.read_text(encoding="utf-8") == before
