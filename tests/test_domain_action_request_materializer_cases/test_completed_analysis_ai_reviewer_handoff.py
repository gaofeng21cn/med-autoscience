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


def test_materialize_domain_action_requests_consumes_completed_analysis_ai_reviewer_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="analysis_harmonization_completed_ai_reviewer_review_required",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "analysis_harmonization_completed_ai_reviewer_review_required",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": route,
        "required_currentness_refs": [
            str(study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"),
            str(
                study_root
                / "artifacts"
                / "controller"
                / "analysis_harmonization"
                / "unit_harmonized_external_validation_rerun.json"
            ),
        ],
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": route,
                    "action_queue": [action],
                    "ai_reviewer_assessment": {
                        "present": True,
                        "missing": True,
                        "blocked_reason": "ai_reviewer_record_stale_after_unit_harmonized_rerun",
                    },
                }
            ],
            "action_queue": [action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["request_task_count"] == 1
    assert result["default_executor_dispatch_count"] == 1
    task = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    assert task["dispatch_status"] == "applied"
    assert task["request_owner"] == "ai_reviewer"
    assert task["owner_route_current"] is True
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["blocked_reason"] is None
    assert dispatch["repeat_suppressed"] is False
    packet_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "ai_reviewer"
        / "latest.json"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    assert packet_path.is_file()
    assert dispatch_path.is_file()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    written_dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    assert packet["request_owner"] == "ai_reviewer"
    assert packet["required_output_surface"] == "artifacts/publication_eval/latest.json"
    assert written_dispatch["dispatch_status"] == "ready"
    assert written_dispatch["prompt_contract"]["request_packet_ref"] == (
        "artifacts/supervision/requests/ai_reviewer/latest.json"
    )


def test_materialize_domain_transition_ai_reviewer_re_eval_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="domain_transition_ai_reviewer_re_eval",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "domain_transition_ai_reviewer_re_eval",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "next_work_unit": "ai_reviewer_medical_prose_quality_review",
        "owner_route": route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": route,
        },
    }
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "owner_route": route,
                    "action_queue": [action],
                    "ai_reviewer_assessment": {
                        "present": True,
                        "missing": False,
                    },
                }
            ],
            "action_queue": [action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["request_task_count"] == 1
    assert result["default_executor_dispatch_count"] == 1
    task = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    assert task["dispatch_status"] == "applied"
    assert task["request_owner"] == "ai_reviewer"
    assert task["owner_route_current"] is True
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["next_executable_owner"] == "ai_reviewer"
    assert dispatch["blocked_reason"] is None
    written_dispatch = json.loads(
        (
            study_root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_dispatches"
            / "return_to_ai_reviewer_workflow.json"
        ).read_text(encoding="utf-8")
    )
    assert written_dispatch["owner_route"]["owner_reason_contract"]["registered"] is True
    assert written_dispatch["owner_route"]["owner_reason_contract"]["reason"] == (
        "domain_transition_ai_reviewer_re_eval"
    )
    assert "return_to_ai_reviewer_workflow" in written_dispatch["owner_route"]["allowed_actions"]


def test_current_write_domain_transition_supersedes_stale_ai_reviewer_queue(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    current_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="write",
        owner_reason="quest_waiting_opl_runtime_owner_route",
        allowed_actions=["run_quality_repair_batch"],
    )
    stale_route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="ai_reviewer_record_stale_after_current_manuscript",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    stale_action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": "ai_reviewer_record_stale_after_current_manuscript",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route": stale_route,
        "handoff_packet": {
            "request_kind": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "request_owner": "ai_reviewer",
            "owner_route": stale_route,
        },
    }
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
                    "domain_transition": {
                        "study_id": study_id,
                        "decision_type": "route_back_same_line",
                        "route_target": "write",
                        "owner": "write",
                        "controller_action": "request_opl_stage_attempt",
                        "next_work_unit": {
                            "unit_id": "dm002_same_line_display_table_package_repair",
                            "lane": "write",
                            "summary": (
                                "Reconcile Table 2, figures, display registry, claim-map boundaries, "
                                "and package freshness."
                            ),
                        },
                        "guard_boundary": {"opl_generic_runner_may_resume": False},
                    },
                    "action_queue": [stale_action],
                }
            ],
            "action_queue": [stale_action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["request_task_count"] == 1
    assert result["default_executor_dispatch_count"] == 1
    task = result["request_tasks"][0]
    dispatch = result["default_executor_dispatches"][0]
    assert task["action_type"] == "run_quality_repair_batch"
    assert task["request_owner"] == "write"
    assert dispatch["action_type"] == "run_quality_repair_batch"
    assert dispatch["next_executable_owner"] == "write"
    assert dispatch["dispatch_status"] == "ready"
    assert dispatch["owner_route"]["next_owner"] == "write"
    assert dispatch["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
    assert any(
        ignored["action_type"] == "return_to_ai_reviewer_workflow"
        and ignored["reason"] == "superseded_by_current_domain_transition"
        for ignored in result["ignored_actions"]
    )
    assert not (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    ).exists()
    assert (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    ).is_file()
