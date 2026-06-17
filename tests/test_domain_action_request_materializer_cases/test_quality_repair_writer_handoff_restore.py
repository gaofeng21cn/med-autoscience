from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


@pytest.fixture(autouse=True)
def _isolated_opl_state_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))


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
    }


def test_materialize_domain_action_requests_restores_writer_handoff_from_owner_request(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit_id = "dm002_same_line_display_table_package_repair"
    work_unit_fingerprint = "dm002_ai_reviewer_current_manuscript_display_table_package_repair_20260525"
    current_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="quest_waiting_opl_runtime_owner_route",
        allowed_actions=["run_quality_repair_batch"],
    )
    current_route.update(
        {
            "runtime_health_epoch": "runtime-health-event-006213-a9957042c5edec67",
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_refs": {
                "source_eval_id": "publication-eval::dm002::current",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
            },
        }
    )
    writer_route = dict(current_route)
    writer_route.update(
        {
            "current_owner": "quality_repair_batch",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "failure_signature": "manuscript_story_surface_delta_missing",
            "idempotency_key": f"quality-repair-writer-handoff::{study_id}::{work_unit_fingerprint}",
            "source_refs": {
                **current_route["source_refs"],
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "bridged_from_owner_reason": "quest_waiting_opl_runtime_owner_route",
                "bridged_from_idempotency_key": current_route["idempotency_key"],
                "bridge_authority": "quality_repair_batch_writer_handoff_currentness_bridge",
            },
        }
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "quality_repair_batch"
        / "latest.json"
    )
    repair_evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    source_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    source_summary_path = study_root / "artifacts" / "quality" / "summary.json"
    _write_json(repair_evidence_path, {"status": "blocked", "blockers": ["manuscript_story_surface_delta_missing"]})
    _write_json(source_eval_path, {"eval_id": "publication-eval::dm002::current"})
    _write_json(source_summary_path, {"summary_id": "quality-summary::dm002"})
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "next_executable_owner": "write",
            "dispatch_authority": None,
            "owner_route": current_route,
            "prompt_contract": {
                "owner_route": current_route,
                "do_not_repeat": True,
                "repeat_suppression_key": work_unit_fingerprint,
            },
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )
    _write_json(
        request_path,
        {
            "request_kind": "run_quality_repair_batch",
            "status": "requested",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "write",
            "next_executable_owner": "write",
            "action_type": "run_quality_repair_batch",
            "dispatch_authority": "quality_repair_batch_writer_handoff",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "owner_route": writer_route,
            "source_action": {
                "surface": "quality_repair_batch",
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "source_eval_id": "publication-eval::dm002::current",
                "repair_execution_evidence_ref": str(repair_evidence_path),
            },
            "refs": {
                "dispatch_path": str(dispatch_path),
                "request_path": str(request_path),
                "source_eval_path": str(source_eval_path),
                "source_summary_path": str(source_summary_path),
                "repair_execution_evidence_path": str(repair_evidence_path),
            },
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
                    "quest_id": quest_id,
                    "owner_route": current_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "run_quality_repair_batch",
                            "owner": "write",
                            "reason": "quest_waiting_opl_runtime_owner_route",
                            "required_output_surface": "artifacts/controller/quality_repair_batch/latest.json",
                            "next_work_unit": {
                                "unit_id": work_unit_id,
                                "lane": "write",
                                "summary": "Repair displays, tables, package-facing prose, and manuscript story surface.",
                            },
                            "owner_route": current_route,
                            "handoff_packet": {
                                "request_kind": "run_quality_repair_batch",
                                "request_owner": "write",
                                "owner_route": current_route,
                            },
                        }
                    ],
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

    dispatch = result["owner_callable_adapters"][0]
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert dispatch["owner_route"]["owner_reason"] == "manuscript_story_surface_delta_missing"
    assert dispatch["owner_route"]["source_refs"]["work_unit_id"] == work_unit_id
    assert dispatch["medical_claim_authoring_allowed"] is True
    assert "paper/draft.md" in dispatch["prompt_contract"]["allowed_write_surfaces"]
    assert dispatch["prompt_contract"]["search_boundaries"]["surface"] == "default_executor_search_discipline.v1"
    assert "grep -R" in dispatch["prompt_contract"]["search_boundaries"]["forbidden_command_patterns"]
    assert "runtime/**/codex_homes/**" in dispatch["prompt_contract"]["search_boundaries"]["forbidden_path_globs"]
    assert dispatch["refs"]["dispatch_path"] == str(dispatch_path)
    assert dispatch["owner_route"]["source_refs"]["bridged_from_idempotency_key"] == current_route["idempotency_key"]
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["mas_dispatch_authority"] is False
    assert dispatch["opl_domain_progress_transition_request"]["target_runtime_owner"] == "one-person-lab"
    assert result["written_files"] == []


def test_materialize_domain_action_requests_restores_writer_handoff_when_current_route_is_story_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit_id = "dm002_same_line_display_table_package_repair"
    work_unit_fingerprint = "dm002_ai_reviewer_current_manuscript_display_table_package_repair_20260525"
    current_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        allowed_actions=["run_quality_repair_batch"],
    )
    current_route.update(
        {
            "truth_epoch": f"truth-epoch::{study_id}::current",
            "route_epoch": f"truth-epoch::{study_id}::current",
            "source_fingerprint": f"truth-source::{study_id}::current",
            "runtime_health_epoch": "runtime-health-event-006214-direct-story-surface",
            "work_unit_fingerprint": work_unit_fingerprint,
            "idempotency_key": f"owner-route::{study_id}::direct-story-surface-current",
            "source_refs": {
                "source_eval_id": "publication-eval::dm002::current",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "runtime_health_epoch": "runtime-health-event-006214-direct-story-surface",
                "study_truth_epoch": f"truth-epoch::{study_id}::current",
                "blocked_reason": "manuscript_story_surface_delta_missing",
            },
        }
    )
    writer_route = dict(current_route)
    writer_route.update(
        {
            "current_owner": "quality_repair_batch",
            "failure_signature": "manuscript_story_surface_delta_missing",
            "idempotency_key": f"quality-repair-writer-handoff::{study_id}::{work_unit_fingerprint}",
            "source_refs": {
                **current_route["source_refs"],
                "bridge_authority": "quality_repair_batch_writer_handoff_currentness_bridge",
            },
        }
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "quality_repair_batch"
        / "latest.json"
    )
    repair_evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    source_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    source_summary_path = study_root / "artifacts" / "quality" / "summary.json"
    _write_json(repair_evidence_path, {"status": "blocked", "blockers": ["manuscript_story_surface_delta_missing"]})
    _write_json(source_eval_path, {"eval_id": "publication-eval::dm002::current"})
    _write_json(source_summary_path, {"summary_id": "quality-summary::dm002"})
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "next_executable_owner": "write",
            "dispatch_authority": None,
            "owner_route": current_route,
            "prompt_contract": {
                "owner_route": current_route,
                "do_not_repeat": True,
                "repeat_suppression_key": work_unit_fingerprint,
            },
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )
    _write_json(
        request_path,
        {
            "request_kind": "run_quality_repair_batch",
            "status": "requested",
            "study_id": study_id,
            "quest_id": quest_id,
            "request_owner": "write",
            "next_executable_owner": "write",
            "action_type": "run_quality_repair_batch",
            "dispatch_authority": "quality_repair_batch_writer_handoff",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "owner_route": writer_route,
            "source_action": {
                "surface": "quality_repair_batch",
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "source_eval_id": "publication-eval::dm002::current",
                "repair_execution_evidence_ref": str(repair_evidence_path),
                "next_work_unit": {"unit_id": work_unit_id, "lane": "write"},
            },
            "refs": {
                "dispatch_path": str(dispatch_path),
                "request_path": str(request_path),
                "source_eval_path": str(source_eval_path),
                "source_summary_path": str(source_summary_path),
                "repair_execution_evidence_path": str(repair_evidence_path),
            },
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
                    "quest_id": quest_id,
                    "owner_route": current_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "run_quality_repair_batch",
                            "owner": "write",
                            "reason": "manuscript_story_surface_delta_missing",
                            "required_output_surface": (
                                "canonical manuscript story-surface delta or "
                                "typed blocker:manuscript_story_surface_delta_missing"
                            ),
                            "next_work_unit": {
                                "unit_id": work_unit_id,
                                "lane": "write",
                                "summary": "Repair displays, tables, package-facing prose, and manuscript story surface.",
                            },
                            "owner_route": current_route,
                            "handoff_packet": {
                                "request_kind": "run_quality_repair_batch",
                                "request_owner": "write",
                                "owner_route": current_route,
                            },
                        }
                    ],
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

    dispatch = result["owner_callable_adapters"][0]
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert dispatch["owner_route"]["owner_reason"] == "manuscript_story_surface_delta_missing"
    assert dispatch["owner_route"]["idempotency_key"] == writer_route["idempotency_key"]
    assert dispatch["owner_route"]["source_refs"]["work_unit_id"] == work_unit_id
    assert dispatch["medical_claim_authoring_allowed"] is True
    assert "paper/draft.md" in dispatch["prompt_contract"]["allowed_write_surfaces"]
    assert dispatch["prompt_contract"]["medical_claim_authoring_allowed"] is True
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["mas_dispatch_authority"] is False
    assert dispatch["opl_domain_progress_transition_request"]["target_runtime_owner"] == "one-person-lab"
    assert result["written_files"] == []


def test_materialize_domain_action_requests_builds_writer_handoff_from_current_story_surface_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    work_unit_id = "dm002_same_line_display_table_package_repair"
    work_unit_fingerprint = "dm002_ai_reviewer_current_manuscript_display_table_package_repair_20260525"
    current_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="manuscript_story_surface_delta_missing",
        allowed_actions=["run_quality_repair_batch"],
    )
    current_route.update(
        {
            "truth_epoch": f"truth-epoch::{study_id}::current",
            "route_epoch": f"truth-epoch::{study_id}::current",
            "source_fingerprint": f"truth-source::{study_id}::current",
            "runtime_health_epoch": "runtime-health-event-006222-direct-story-surface",
            "work_unit_fingerprint": work_unit_fingerprint,
            "idempotency_key": f"owner-route::{study_id}::direct-story-surface-current",
            "source_refs": {
                "source_eval_id": "publication-eval::dm002::current",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "runtime_health_epoch": "runtime-health-event-006222-direct-story-surface",
                "study_truth_epoch": f"truth-epoch::{study_id}::current",
                "blocked_reason": "manuscript_story_surface_delta_missing",
            },
        }
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    repair_evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    source_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    source_summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    _write_json(repair_evidence_path, {"status": "blocked", "blockers": ["manuscript_story_surface_delta_missing"]})
    _write_json(source_eval_path, {"eval_id": "publication-eval::dm002::current"})
    _write_json(source_summary_path, {"summary_id": "quality-summary::dm002"})
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": current_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "action_type": "run_quality_repair_batch",
                            "owner": "write",
                            "reason": "manuscript_story_surface_delta_missing",
                            "required_output_surface": (
                                "canonical manuscript story-surface delta or "
                                "typed blocker:manuscript_story_surface_delta_missing"
                            ),
                            "next_work_unit": {
                                "unit_id": work_unit_id,
                                "lane": "write",
                                "summary": "Repair display, table, package-facing prose, and story surface.",
                            },
                            "work_unit_fingerprint": work_unit_fingerprint,
                            "owner_route": current_route,
                            "handoff_packet": {
                                "request_kind": "run_quality_repair_batch",
                                "request_owner": "write",
                                "owner_route": current_route,
                            },
                        }
                    ],
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

    dispatch = result["owner_callable_adapters"][0]
    assert dispatch["dispatch_status"] == "transition_request_pending"
    assert dispatch["dispatch_authority"] == "quality_repair_batch_writer_handoff"
    assert dispatch["owner_route"]["owner_reason"] == "manuscript_story_surface_delta_missing"
    assert dispatch["owner_route"]["source_refs"]["work_unit_id"] == work_unit_id
    assert dispatch["medical_claim_authoring_allowed"] is True
    assert dispatch["prompt_contract"]["medical_claim_authoring_allowed"] is True
    assert dispatch["prompt_contract"]["allowed_write_surfaces"] == [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    assert dispatch["source_action"]["surface"] == "quality_repair_batch"
    assert dispatch["source_action"]["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert dispatch["refs"]["repair_execution_evidence_path"] == str(repair_evidence_path)
    assert dispatch["provider_admission_pending"] is False
    assert dispatch["provider_admission_requires_opl_runtime_result"] is True
    assert dispatch["mas_dispatch_authority"] is False
    assert dispatch["opl_domain_progress_transition_request"]["target_runtime_owner"] == "one-person-lab"
    assert result["written_files"] == []
