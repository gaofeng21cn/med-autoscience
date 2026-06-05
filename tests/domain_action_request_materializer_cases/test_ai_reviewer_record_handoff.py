from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _owner_route(
    *,
    study_id: str,
    quest_id: str,
    next_owner: str,
    owner_reason: str,
    allowed_actions: list[str],
) -> dict[str, object]:
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "route_epoch": f"truth-epoch::{study_id}",
        "source_fingerprint": f"truth-source::{study_id}::{owner_reason}",
        "current_owner": "mas_controller",
        "next_owner": next_owner,
        "owner_reason": owner_reason,
        "active_run_id": None,
        "allowed_actions": allowed_actions,
        "blocked_actions": [],
        "idempotency_key": f"owner-route::{study_id}::{owner_reason}",
        "runtime_health_epoch": f"runtime-health::{study_id}::{owner_reason}",
        "source_refs": {
            "runtime_health_epoch": f"runtime-health::{study_id}::{owner_reason}",
            "work_unit_id": owner_reason,
            "work_unit_fingerprint": f"truth-source::{study_id}::{owner_reason}",
        },
    }


def test_materialize_ai_reviewer_dispatch_uses_record_handoff_when_latest_is_forbidden_by_owner_reason(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    dispatch_contract = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.dispatch_contract"
    )
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    owner_forbidden_surfaces = [
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="paper_authority_clean_migration_required",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    route["source_refs"]["work_unit_id"] = None
    route["source_refs"]["owner_route_currentness_basis"] = {
        "truth_epoch": "truth-event-000038-6a578a0ba3e8f28a",
        "work_unit_id": "truth-snapshot::4600359bf94e777a03837b8b",
        "work_unit_fingerprint": "truth-snapshot::4600359bf94e777a03837b8b",
        "runtime_health_epoch": "runtime-health-event-006595-02a0d578ea81eec6",
    }
    route["owner_reason_contract"] = {
        "registered": True,
        "reason": "paper_authority_clean_migration_required",
        "owner": "ai_reviewer",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "required_output": "new MAS paper authority surface or typed blocker",
        "forbidden_surfaces": [
            "manuscript/**",
            "current_package/**",
            "paper/current_package/**",
            "manuscript/current_package/**",
            *owner_forbidden_surfaces,
        ],
        "priority_class": "ai_reviewer_currentness",
    }
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "reason": "paper_authority_clean_migration_required",
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "owner_route": route,
                    "handoff_packet": {
                        "request_kind": "return_to_ai_reviewer_workflow",
                        "authority": "observability_only",
                        "request_owner": "ai_reviewer",
                        "owner_route": route,
                    },
                }
            ],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["dispatch_authority"] == "ai_reviewer_record_production_handoff"
    assert dispatch["required_output_surface"] == (
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    )
    assert dispatch["prompt_contract"]["owner_callable_command"].endswith("--build-production-trace")
    assert dispatch["prompt_contract"]["owner_callable_payload_ref"].endswith(
        "record_production_payloads/return_to_ai_reviewer_workflow_payload.json"
    )
    prompt_forbidden_surfaces = set(dispatch["prompt_contract"]["forbidden_surfaces"])
    for surface in owner_forbidden_surfaces:
        assert surface in prompt_forbidden_surfaces
    assert dispatch_contract.prompt_contract_error(
        dispatch["prompt_contract"],
        forbidden_surfaces=module.FORBIDDEN_SURFACES,
    ) is None
    assert dispatch["source_action"]["record_only_surface"] is True
    assert dispatch["source_action"]["publication_eval_latest_write_allowed"] is False
    persisted = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_dispatches"
            / "return_to_ai_reviewer_workflow.json"
        ).read_text(encoding="utf-8")
    )
    assert set(persisted["prompt_contract"]["forbidden_surfaces"]) == prompt_forbidden_surfaces
    assert persisted["dispatch_authority"] == "ai_reviewer_record_production_handoff"


def test_materialize_ai_reviewer_record_handoff_suppresses_ready_dispatch_after_current_record(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript already reviewed.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    basis = {
        "truth_epoch": "truth-event-000040-current",
        "runtime_health_epoch": "runtime-health-event-006616-current",
        "work_unit_id": "truth-snapshot::current-ai-reviewer-record",
        "work_unit_fingerprint": "truth-snapshot::current-ai-reviewer-record",
    }
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="paper_authority_clean_migration_required",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    route["runtime_health_epoch"] = basis["runtime_health_epoch"]
    route["work_unit_fingerprint"] = basis["work_unit_fingerprint"]
    route["source_refs"]["owner_route_currentness_basis"] = basis
    route["source_refs"]["work_unit_fingerprint"] = basis["work_unit_fingerprint"]
    route["source_refs"]["work_unit_id"] = None
    route["owner_reason_contract"] = {
        "registered": True,
        "reason": "paper_authority_clean_migration_required",
        "owner": "ai_reviewer",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "required_output": "artifacts/publication_eval/latest.json",
        "forbidden_surfaces": [
            "artifacts/publication_eval/latest.json",
            "artifacts/controller_decisions/latest.json",
        ],
        "priority_class": "ai_reviewer_currentness",
    }
    eval_id = "publication-eval::dm002::current-record::2026-06-05T04:55:53+00:00::ai-reviewer"
    record = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id=study_id,
        quest_id=quest_id,
        eval_id=eval_id,
        emitted_at="2026-06-05T04:55:53+00:00",
    )
    record["assessment_provenance"]["owner_route_currentness_basis"] = basis
    record["assessment_provenance"]["work_unit_id"] = basis["work_unit_id"]
    record["assessment_provenance"]["work_unit_fingerprint"] = basis["work_unit_fingerprint"]
    _write_json(
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260605T045553Z_publication_eval_record.json",
        record,
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json",
        {
            "surface": "domain_action_request",
            "schema_version": 1,
            "request_kind": "return_to_ai_reviewer_workflow",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "requested", "blocked_reason": None},
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "authority": "observability_only",
                    "owner": "ai_reviewer",
                    "reason": "paper_authority_clean_migration_required",
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "owner_route": route,
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
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "executor_kind": "codex_cli_default",
            "next_executable_owner": "ai_reviewer",
            "owner_route": route,
            "prompt_contract": {
                "action_type": "return_to_ai_reviewer_workflow",
                "next_executable_owner": "ai_reviewer",
                "owner_route": route,
                "do_not_repeat": True,
            },
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    dispatch = result["default_executor_dispatches"][0]
    assert dispatch["dispatch_status"] == "repeat_suppressed"
    assert dispatch["repeat_suppressed"] is True
    assert dispatch["blocked_reason"] == "repeat_suppressed"
    assert dispatch["repeat_suppression"]["suppression_source"] == (
        "ai_reviewer_record_production_output_satisfied"
    )
    assert dispatch["record_production_satisfaction"]["record_ref"].endswith(
        "20260605T045553Z_publication_eval_record.json"
    )
    assert result["ready_default_executor_dispatch_count"] == 0
    assert result["repeat_suppressed_count"] == 1
    persisted = json.loads(dispatch_path.read_text(encoding="utf-8"))
    assert persisted["dispatch_status"] == "repeat_suppressed"
    assert persisted["record_production_satisfaction"]["eval_id"] == eval_id
