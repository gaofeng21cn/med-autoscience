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
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
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


def test_execute_dispatch_uses_current_consumer_payload_when_dispatch_file_is_stale(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
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
            "ai_reviewer_record": {
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {"status": "underdefined"},
                },
                "future_facing_limitations_plan": [
                    {
                        "limitation": "Pending reviewer confirmation.",
                        "impact_on_claim": "Claims remain provisional.",
                        "required_future_analysis_data_or_design": "Rerun reviewer workflow.",
                        "current_manuscript_wording_must_be_restrained": True,
                    }
                ],
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}},
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "default_executor_dispatch_count": 1,
            "default_executor_dispatches": [current_dispatch],
        },
    )
    called: list[str] = []

    def fake_run_ai_reviewer_publication_eval_workflow(**kwargs) -> dict[str, object]:
        called.append(str(kwargs["study_root"]))
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
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [stale_consumer_dispatch],
        },
    )
    monkeypatch.setattr(module.action_execution, "quest_root_from_status", lambda *_: quest_root)
    called: dict[str, object] = {}

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        }

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
    assert execution["execution_status"] == "executed"
    assert execution["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert execution["prompt_contract"]["medical_claim_authoring_allowed"] is True
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert called["authority_route_context"]["work_unit_id"] == "medical_prose_write_repair"
