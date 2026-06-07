from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
    write_scan_latest as _write_scan_latest,
)
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_defaults_to_current_consumer_dispatches(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch_dir = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_dispatches"
    current_dispatch_path = dispatch_dir / "publication_gate_specificity_required.json"
    stale_ai_dispatch_path = dispatch_dir / "return_to_ai_reviewer_workflow.json"
    stale_unsupported_dispatch_path = dispatch_dir / "unsupported_supervisor_action.json"
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
        stale_unsupported_dispatch_path,
        _dispatch(
            study_id=study_id,
            action_type="unsupported_supervisor_action",
            owner="external_observer",
            required_output_surface="artifacts/supervision/consumer/unsupported_supervisor_action.json",
        ),
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
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

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["codex_dispatch_count"] == 0
    assert result["suppressed_dispatch_count"] == 0
    assert result["executions"][0]["action_class"] == "controller_apply"
    assert result["executions"][0]["will_start_llm"] is False
    assert result["dispatch_budget_window"]["duplicate_policy"] == "suppress_same_action_fingerprint"
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


def test_execute_dispatch_accepts_single_dispatch_payload_shape(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
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
        / "immutable"
        / "publication_gate_specificity_required"
        / "current.json"
    )
    current_dispatch = _dispatch(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    current_dispatch["refs"] = {
        "dispatch_path": str(dispatch_path),
        "immutable_dispatch_path": str(dispatch_path),
    }
    _write_scan_latest(profile, study_id, dict(current_dispatch["owner_route"]))
    executed_action_types: list[str] = []

    def fake_publication_gate_specificity(**kwargs) -> dict[str, object]:
        executed_action_types.append("publication_gate_specificity_required")
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "publication_gate.write_gate_files+_materialize_publication_eval_latest",
        }

    monkeypatch.setattr(module, "_execute_publication_gate_specificity", fake_publication_gate_specificity)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_gate_specificity_required",),
        mode="developer_apply_safe",
        apply=True,
        consumer_payload=current_dispatch,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["executions"][0]["dispatch_path"] == str(dispatch_path)
    assert executed_action_types == ["publication_gate_specificity_required"]


def test_execute_dispatch_uses_current_consumer_payload_when_dispatch_file_is_stale(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript snapshot for consumer dispatch.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
    )
    _write_json(dispatch_path, stale_dispatch)
    current_route = dict(
        stale_dispatch["owner_route"],
        runtime_health_epoch="runtime-health-current",
        work_unit_fingerprint="truth-snapshot::current-ai-reviewer",
        source_fingerprint="truth-snapshot::current-ai-reviewer",
        idempotency_key="owner-route::003::current-ai-reviewer",
    )
    current_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=current_route,
    )
    current_dispatch["refs"] = {"dispatch_path": str(dispatch_path)}
    current_dispatch["prompt_contract"]["owner_route"] = current_route
    current_dispatch["prompt_contract"]["idempotency_key"] = current_route["idempotency_key"]
    current_dispatch["prompt_contract"]["repeat_suppression_key"] = current_route["work_unit_fingerprint"]
    _write_scan_latest(profile, study_id, current_route)
    input_refs = {
        "manuscript": {"path": str(study_root / "paper" / "draft.md")},
        "evidence_ledger": {"path": str(study_root / "paper" / "evidence_ledger.json")},
        "review_ledger": {"path": str(study_root / "paper" / "review" / "review_ledger.json")},
        "study_charter": {"path": str(study_root / "artifacts" / "controller" / "study_charter.json")},
        "medical_manuscript_blueprint": {"path": str(study_root / "paper" / "medical_manuscript_blueprint.json")},
        "claim_evidence_map": {"path": str(study_root / "paper" / "claim_evidence_map.json")},
        "medical_prose_review": {"path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json")},
        "publication_gate_projection": {"path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
    }
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
            "ai_reviewer_record": current_manuscript_routeback_record(
                study_root=study_root,
                manuscript_path=manuscript_path,
                manuscript_text=manuscript_text,
                study_id=study_id,
                quest_id=study_id,
                eval_id="publication-eval::003::current-consumer-payload",
            ),
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}},
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [current_dispatch],
        },
    )
    called: list[str] = []

    def fake_run_ai_reviewer_publication_eval_workflow(**kwargs) -> dict[str, object]:
        called.append(str(kwargs["study_root"]))
        _write_json(
            study_root / "artifacts" / "publication_eval" / "latest.json",
            {
                "eval_id": "publication-eval::003::current-consumer-payload",
                "study_id": study_id,
                "quest_id": study_id,
                "assessment_provenance": {"owner": "ai_reviewer"},
            },
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
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_route"]["work_unit_fingerprint"] == "truth-snapshot::current-ai-reviewer"
    assert called == [str(study_root)]


def test_execute_dispatch_defaults_to_current_persisted_dispatch_when_consumer_latest_is_empty(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "publication_gate_specificity_required.json"
    )
    route = _owner_route(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_scan_latest(profile, study_id, route)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "publication_gate_specificity" / "latest.json",
        {
            "surface": "domain_action_request",
            "request_kind": "publication_gate_specificity_required",
            "status": "requested",
            "study_id": study_id,
            "request_owner": "publication_gate",
            "owner_route": route,
        },
    )

    called: list[str] = []

    def fake_publication_gate_specificity(**kwargs) -> dict[str, object]:
        called.append(str(kwargs["study_id"]))
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "publication_gate.write_gate_files+_materialize_publication_eval_latest",
        }

    monkeypatch.setattr(module, "_execute_publication_gate_specificity", fake_publication_gate_specificity)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 1
    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert called == [study_id]
    summary = result["per_study_execution_summary"][0]
    assert summary["selected_dispatch_count"] == 1
    assert summary["zero_dispatch_reason"] is None
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


def test_execute_dispatch_ignores_stale_consumer_dispatch_after_consumed_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    stale_ai_route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    stale_ai_route.update(
        {
            "runtime_health_epoch": "runtime-health-stale-ai-reviewer",
            "work_unit_fingerprint": "truth-snapshot::stale-ai-reviewer",
            "source_fingerprint": "truth-source::stale-ai-reviewer",
            "idempotency_key": "owner-route::003::stale-ai-reviewer",
        }
    )
    stale_ai_dispatch = _dispatch(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=stale_ai_route,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_ai_dispatch["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, stale_ai_dispatch)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": stale_ai_route,
                    "domain_transition": {
                        "decision_type": "route_back_same_line",
                        "route_target": "write",
                        "owner": "write",
                        "controller_action": "request_opl_stage_attempt",
                        "next_work_unit": {
                            "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                            "lane": "write",
                        },
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                        },
                    },
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [stale_ai_dispatch],
        },
    )

    def fail_ai_reviewer(**kwargs) -> dict[str, object]:
        raise AssertionError("stale consumed AI reviewer dispatch should not execute")

    monkeypatch.setattr(module, "_execute_ai_reviewer_workflow", fail_ai_reviewer)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 0
    assert result["executed_count"] == 0
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] == (
        "no_selected_dispatch_for_requested_action_types"
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    ).exists()


def test_execute_dispatch_preserves_prior_execution_in_study_ledger(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    quest_root.mkdir(parents=True, exist_ok=True)
    execution_root = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution"
    previous_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    previous_route.update(
        {
            "idempotency_key": "owner-route::dm002::previous-quality-repair",
            "work_unit_fingerprint": "truth-snapshot::previous-quality-repair",
            "source_refs": {
                "work_unit_id": "dm002_current_manuscript_reporting_consistency_write_repair",
                "work_unit_fingerprint": "truth-snapshot::previous-quality-repair",
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
            },
        }
    )
    _write_json(
        execution_root / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": study_id,
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": "execution::dm002::run_quality_repair_batch::previous",
                    "idempotency_key": previous_route["idempotency_key"],
                    "current_owner_route": previous_route,
                    "prompt_contract": {"owner_route": previous_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "build" / "review_manuscript.md")},
                            ],
                        },
                    },
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
        / "publication_gate_specificity_required.json"
    )
    route = _owner_route(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type="publication_gate_specificity_required",
        owner="publication_gate",
        required_output_surface="artifacts/publication_eval/latest.json",
        owner_route=route,
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_scan_latest(profile, study_id, route)
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [dispatch_payload],
        },
    )
    def fake_publication_gate_specificity(**kwargs) -> dict[str, object]:
        return {
            "execution_status": "executed",
            "blocked_reason": None,
            "owner_callable_surface": "publication_gate.write_gate_files+_materialize_publication_eval_latest",
        }

    monkeypatch.setattr(module, "_execute_publication_gate_specificity", fake_publication_gate_specificity)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("publication_gate_specificity_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    latest = json.loads((execution_root / "latest.json").read_text(encoding="utf-8"))
    assert [item["action_type"] for item in latest["executions"]] == ["publication_gate_specificity_required"]
    assert [item["execution_id"] for item in latest["execution_ledger"]] == [
        "execution::dm002::run_quality_repair_batch::previous",
        result["executions"][0]["execution_id"],
    ]
    assert latest["ledger_execution_count"] == 2


def test_execute_dispatch_reports_per_study_progress_first_dispatch_accounting(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_ids = (
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    )
    dispatches: list[dict[str, object]] = []
    scan_studies: list[dict[str, object]] = []
    for index, study_id in enumerate(study_ids, start=2):
        study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
        quest_root = profile.runtime_root / f"quest-{study_id}"
        quest_root.mkdir(parents=True, exist_ok=True)
        route = _owner_route(
            study_id=study_id,
            action_type="run_quality_repair_batch",
            owner="write",
        )
        route.update(
            {
                "work_unit_fingerprint": f"domain-transition::{study_id}::medical-prose-write-repair",
                "source_fingerprint": f"truth-source::{study_id}::medical-prose",
                "idempotency_key": f"owner-route::{study_id}::medical-prose",
            }
        )
        dispatch_payload = _dispatch(
            study_id=study_id,
            action_type="run_quality_repair_batch",
            owner="write",
            required_output_surface=(
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            owner_route=route,
        )
        dispatch_path = (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_dispatches"
            / "run_quality_repair_batch.json"
        )
        dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
        dispatch_payload["source_action"] = {
            "action_type": "run_quality_repair_batch",
            "route_target": "write",
            "work_unit_fingerprint": route["work_unit_fingerprint"],
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
            },
            "source_eval_id": f"publication-eval::dm00{index}",
        }
        _write_json(dispatch_path, dispatch_payload)
        _write_json(
            study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
            {
                "surface": "domain_action_request",
                "request_kind": "run_quality_repair_batch",
                "status": "requested",
                "study_id": study_id,
                "request_owner": "write",
                "expected_owner": "write",
                "next_executable_owner": "write",
                "owner_route": route,
            },
        )
        dispatches.append(dispatch_payload)
        scan_studies.append({"study_id": study_id, "owner_route": route})

    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": scan_studies,
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatch_count": len(dispatches),
            "default_executor_dispatches": dispatches,
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda *, study_id, **_: {
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "quest_root": str(profile.runtime_root / f"quest-{study_id}"),
        },
    )
    called: list[str] = []

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.append(str(kwargs["study_id"]))
        return {
            "ok": True,
            "status": "handoff_ready",
            "blocked_reason": None,
            "writer_worker_handoff": {
                "surface": "default_executor_dispatch_request",
                "dispatch_status": "ready",
                "next_executable_owner": "write",
                "required_output_surface": (
                    "canonical manuscript story-surface delta or "
                    "typed blocker:manuscript_story_surface_delta_missing"
                ),
            },
        }

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=study_ids,
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["execution_count"] == 2
    assert result["executed_count"] == 2
    assert result["codex_dispatch_count"] == 2
    assert result["dispatch_budget_window"] == {
        "scope": "per_study_owner_route_action_fingerprint",
        "max_codex_dispatches_per_scope": 1,
        "workspace_global_max_codex_dispatches": None,
        "duplicate_policy": "suppress_same_action_fingerprint",
        "dry_run_starts_llm": False,
        "observe_only_starts_llm": False,
    }
    assert called == list(study_ids)
    summaries = {item["study_id"]: item for item in result["per_study_execution_summary"]}
    assert set(summaries) == set(study_ids)
    for study_id in study_ids:
        assert summaries[study_id]["selected_dispatch_count"] == 1
        assert summaries[study_id]["executed_count"] == 1
        assert summaries[study_id]["codex_dispatch_count"] == 1
        assert summaries[study_id]["zero_dispatch_reason"] is None


def test_execute_dispatch_prefers_owner_request_persisted_writer_handoff_over_stale_consumer_inline(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    quest_root.mkdir(parents=True, exist_ok=True)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    route = _owner_route(study_id=study_id, action_type="run_quality_repair_batch", owner="write")
    route.update(
        {
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "work_unit_fingerprint": "dm002-current-write-handoff",
            "idempotency_key": "owner-route::dm002::current-write-handoff",
        }
    )
    stale_stall = {
        "surface_kind": "paper_progress_stall",
        "terminal": True,
        "action_fingerprint": "paper_progress_stall::legacy-inline",
    }
    stale_consumer_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    stale_consumer_dispatch["refs"] = {"dispatch_path": str(dispatch_path)}
    stale_consumer_dispatch["paper_progress_stall"] = stale_stall
    stale_consumer_dispatch["prompt_contract"]["paper_progress_stall"] = stale_stall
    stale_consumer_dispatch["action_id"] = "legacy-inline-dispatch"

    persisted_handoff = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    persisted_handoff["refs"] = {"dispatch_path": str(dispatch_path)}
    persisted_handoff["dispatch_authority"] = "quality_repair_batch_writer_handoff"
    persisted_handoff["source_action"] = {
        "surface": "quality_repair_batch",
        "blocked_reason": "manuscript_story_surface_delta_missing",
        "next_work_unit": {"unit_id": "medical_prose_write_repair", "lane": "write"},
    }
    persisted_handoff["medical_claim_authoring_allowed"] = True
    persisted_handoff["prompt_contract"]["medical_claim_authoring_allowed"] = True
    persisted_handoff["prompt_contract"]["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    persisted_handoff["prompt_contract"]["forbidden_surfaces"] = [
        "manuscript/**",
        "current_package/**",
        "paper/current_package/**",
        "manuscript/current_package/**",
        "src/med_autoscience/platform/**",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    _write_json(dispatch_path, persisted_handoff)
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "quality_repair_batch" / "latest.json",
        {
            "request_kind": "run_quality_repair_batch",
            "status": "requested",
            "study_id": study_id,
            "request_owner": "write",
            "expected_owner": "write",
            "next_executable_owner": "write",
            "dispatch_authority": "quality_repair_batch_writer_handoff",
            "owner_route": route,
        },
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "paper_progress_stall": stale_stall,
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [stale_consumer_dispatch],
        },
    )
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        raise AssertionError("writer handoff dispatch must not re-enter quality_repair_batch owner callable")

    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        fake_run_quality_repair_batch,
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    execution = result["executions"][0]
    assert execution["execution_status"] == "handoff_ready"
    assert execution["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert execution["prompt_contract"]["medical_claim_authoring_allowed"] is True
    assert execution["owner_callable_surface"] == "opl_default_executor.stage_attempt"
    assert execution["writer_worker_handoff"]["source_action"]["next_work_unit"]["unit_id"] == "medical_prose_write_repair"
