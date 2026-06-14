from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    patch_dispatchable_study_progress as _patch_dispatchable_study_progress,
    write_json as _write_json,
    write_scan_latest as _write_scan_latest,
)
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
from tests.study_runtime_test_helpers import make_profile, write_study
from tests.test_domain_owner_action_dispatch_cases.consumer_dispatch_progress_and_writer_handoff import (
    test_execute_dispatch_prefers_owner_request_persisted_writer_handoff_over_stale_consumer_inline,
    test_execute_dispatch_preserves_prior_execution_in_study_ledger,
    test_execute_dispatch_reports_per_study_progress_first_dispatch_accounting,
)


def test_execute_dispatch_defaults_to_current_consumer_dispatches(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    _patch_dispatchable_study_progress(monkeypatch, default_study_id=study_id)
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


def test_execute_dispatch_defaults_to_same_tick_consumer_payload_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    action_type = "run_quality_repair_batch"
    _patch_dispatchable_study_progress(
        monkeypatch,
        default_study_id=study_id,
        actions_by_study={
            study_id: {
                "action_type": action_type,
                "next_owner": "write",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::current",
            }
        },
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    route = _owner_route(study_id=study_id, action_type=action_type, owner="write")
    route["source_refs"] = {
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "publication-blockers::current",
        "owner_route_currentness_basis": {
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::current",
            "truth_epoch": route["truth_epoch"],
            "runtime_health_epoch": route["runtime_health_epoch"],
        },
    }
    route["work_unit_fingerprint"] = "publication-blockers::current"
    route["source_fingerprint"] = "publication-blockers::current"
    route["idempotency_key"] = "paper-recovery-owner-gate::002::run_quality_repair_batch::current"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type=action_type,
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=route,
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_scan_latest(profile, study_id, route)
    consumer_payload = {
        "surface": "domain_action_request_materializer",
        "default_executor_dispatch_count": 1,
        "default_executor_dispatches": [dispatch_payload],
    }

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(),
        mode="developer_apply_safe",
        apply=False,
        consumer_payload=consumer_payload,
    )

    assert result["execution_count"] == 1
    assert result["dry_run_count"] == 1
    assert result["blocked_count"] == 0
    assert result["per_study_execution_summary"][0]["selected_dispatch_count"] == 1
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] is None
    assert result["executions"][0]["action_type"] == action_type
    assert result["executions"][0]["dispatch_path"] == str(dispatch_path)


def test_execute_dispatch_selects_fresh_progress_current_owner_action_when_current_control_is_stale(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    work_unit_fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    route = _owner_route(study_id=study_id, action_type=action_type, owner="write")
    route.update(
        {
            "truth_epoch": work_unit_fingerprint,
            "route_epoch": work_unit_fingerprint,
            "runtime_health_epoch": work_unit_fingerprint,
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_fingerprint": work_unit_fingerprint,
            "idempotency_key": f"paper-recovery::{study_id}::{action_type}::{work_unit_fingerprint}",
        }
    )
    route["source_refs"] = {
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "owner_route_currentness_basis": {
            "truth_epoch": work_unit_fingerprint,
            "runtime_health_epoch": work_unit_fingerprint,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
        },
    }
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type=action_type,
        owner="write",
        required_output_surface="artifacts/controller/quality_repair_batch/latest.json",
        owner_route=route,
    )
    dispatch_payload.update(
        {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "next_work_unit": work_unit_id,
            "refs": {"dispatch_path": str(dispatch_path)},
        }
    )
    dispatch_payload["prompt_contract"]["next_work_unit"] = work_unit_id
    dispatch_payload["prompt_contract"]["work_unit_fingerprint"] = work_unit_fingerprint
    dispatch_payload["prompt_contract"]["owner_route_currentness_basis"] = route["source_refs"][
        "owner_route_currentness_basis"
    ]
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "typed_blocker",
                        "owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": "sha256:stale-gate-replay",
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
            "default_executor_dispatches": [dispatch_payload],
        },
    )

    def fake_read_study_progress(**kwargs) -> dict[str, object]:
        return {
            "study_id": study_id,
            "current_execution_envelope": {"state_kind": "executable_owner_action"},
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "owner": "write",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "next_owner": "write",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    def fake_execute_owner_dispatch_action(**kwargs) -> dict[str, object]:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "quality_repair_batch.run_quality_repair_batch",
        }

    monkeypatch.setattr(module, "_execute_owner_dispatch_action", fake_execute_owner_dispatch_action)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(action_type,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 1
    assert result["dry_run_count"] == 1
    assert result["blocked_count"] == 0
    assert result["per_study_execution_summary"][0]["selected_dispatch_count"] == 1
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] is None
    assert result["executions"][0]["action_type"] == action_type
    assert result["executions"][0]["dispatch_path"] == str(dispatch_path)


def test_execute_dispatch_accepts_single_dispatch_payload_shape(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    _patch_dispatchable_study_progress(monkeypatch, default_study_id=study_id)
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
    _patch_dispatchable_study_progress(
        monkeypatch,
        default_study_id=study_id,
        actions_by_study={
            study_id: {
                "action_type": "return_to_ai_reviewer_workflow",
                "next_owner": "ai_reviewer",
                "work_unit_fingerprint": "truth-snapshot::current-ai-reviewer",
            }
        },
    )
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
    _patch_dispatchable_study_progress(monkeypatch, default_study_id=study_id)
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


def test_execute_dispatch_allows_terminal_closeout_owner_answer_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    action_type = "run_gate_clearing_batch"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    route = _owner_route(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
    )
    route["source_refs"] = {
        "work_unit_id": work_unit_id,
        "source_eval_id": "publication-eval::dm002::gate",
    }
    route["work_unit_fingerprint"] = "truth-snapshot::dm002::gate"
    route["source_fingerprint"] = "truth-source::dm002::gate"
    route["idempotency_key"] = "owner-route::dm002::gate"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=route,
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    dispatch_payload["source_action"] = {
        "action_type": action_type,
        "next_work_unit": {"unit_id": work_unit_id},
        "source_eval_id": "publication-eval::dm002::gate",
    }
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "current_work_unit": {
                        "status": "typed_blocker",
                        "action_type": action_type,
                        "owner": "one-person-lab",
                        "currentness_basis": {"work_unit_id": work_unit_id},
                    },
                    "current_execution_envelope": {
                        "state_kind": "typed_blocker",
                        "typed_blocker": {
                            "blocker_id": "terminal_closeout_owner_answer_required",
                            "action_type": action_type,
                            "work_unit_id": work_unit_id,
                        },
                    },
                }
            ],
        },
    )

    def fake_read_study_progress(**kwargs) -> dict[str, object]:
        return {
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_id": "terminal_closeout_owner_answer_required",
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "closeout_refs": [
                        str(dispatch_path),
                    ],
                },
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(action_type,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 1
    assert result["dry_run_count"] == 1
    assert result["blocked_count"] == 0
    assert result["per_study_execution_summary"][0]["selected_dispatch_count"] == 1
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] is None
    assert result["executions"][0]["action_type"] == action_type
    assert result["executions"][0]["execution_status"] == "dry_run"
    assert result["executions"][0]["owner_route_basis"] == "terminal_closeout_owner_answer_dispatch"


def test_execute_dispatch_rejects_terminal_closeout_owner_answer_dispatch_with_stale_identity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    action_type = "run_gate_clearing_batch"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    route = _owner_route(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
    )
    route["source_refs"] = {
        "work_unit_id": work_unit_id,
        "source_eval_id": "publication-eval::dm002::old-gate",
        "owner_route_currentness_basis": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": "truth-snapshot::dm002::old-gate",
            "source_eval_id": "publication-eval::dm002::old-gate",
        },
    }
    route["work_unit_fingerprint"] = "truth-snapshot::dm002::old-gate"
    route["source_fingerprint"] = "truth-source::dm002::old-gate"
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=route,
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    dispatch_payload["source_action"] = {
        "action_type": action_type,
        "next_work_unit": {"unit_id": work_unit_id},
        "source_eval_id": "publication-eval::dm002::old-gate",
    }
    _write_json(dispatch_path, dispatch_payload)
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "current_work_unit": {
                        "status": "typed_blocker",
                        "action_type": action_type,
                        "owner": "one-person-lab",
                        "currentness_basis": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": "truth-snapshot::dm002::fresh-gate",
                            "source_eval_id": "publication-eval::dm002::fresh-gate",
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "typed_blocker",
                        "typed_blocker": {
                            "blocker_id": "terminal_closeout_owner_answer_required",
                            "action_type": action_type,
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": "truth-snapshot::dm002::fresh-gate",
                            "source_eval_id": "publication-eval::dm002::fresh-gate",
                        },
                    },
                }
            ],
        },
    )

    def fake_read_study_progress(**kwargs) -> dict[str, object]:
        return {
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_id": "terminal_closeout_owner_answer_required",
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": "truth-snapshot::dm002::fresh-gate",
                    "source_eval_id": "publication-eval::dm002::fresh-gate",
                    "closeout_refs": [
                        "artifacts/supervision/consumer/default_executor_execution/latest.json",
                    ],
                },
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(action_type,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 0
    assert result["per_study_execution_summary"][0]["selected_dispatch_count"] == 0
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] == (
        "no_selected_dispatch_for_requested_action_types"
    )


def test_execute_dispatch_keeps_unrelated_typed_blocker_closed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    action_type = "run_gate_clearing_batch"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    route = _owner_route(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
    )
    dispatch_payload = _dispatch(
        study_id=study_id,
        action_type=action_type,
        owner="gate_clearing_batch",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
        owner_route=route,
    )
    dispatch_payload["refs"] = {"dispatch_path": str(dispatch_path)}
    _write_json(dispatch_path, dispatch_payload)
    _write_scan_latest(profile, study_id, route)

    def fake_read_study_progress(**kwargs) -> dict[str, object]:
        return {
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_id": "anti_loop_budget_exhausted",
                    "action_type": action_type,
                    "work_unit_id": "same-work-unit",
                },
            },
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=(action_type,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["execution_count"] == 0
    assert result["per_study_execution_summary"][0]["selected_dispatch_count"] == 0
    assert result["per_study_execution_summary"][0]["zero_dispatch_reason"] == (
        "no_selected_dispatch_for_requested_action_types"
    )


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
