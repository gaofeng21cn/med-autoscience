from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tests.domain_action_request_materializer_cases.shared import owner_route as _owner_route
from tests.domain_action_request_materializer_cases.shared import write_json as _write_json
from tests.study_runtime_test_helpers import make_profile, write_study


@pytest.fixture(autouse=True)
def _isolated_opl_state_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPL_STATE_DIR", str(tmp_path / "opl-state"))


def _unsupported_domain_action(study_id: str, quest_id: str) -> dict[str, object]:
    action_type = "unsupported_supervisor_action"
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="external_observer",
        owner_reason=action_type,
        allowed_actions=[action_type],
    )
    return {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "authority": "observability_only",
        "reason": action_type,
        "action_id": f"supervisor-action::{study_id}::{action_type}",
        "owner_route": route,
        "handoff_packet": {
            "packet_type": "external_supervisor_handoff",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": action_type,
            "reason": action_type,
            "authority": "observability_only",
            "recommended_owner": "external_observer",
            "owner_route": route,
        },
    }


def _disable_progress_projection(monkeypatch) -> None:
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    monkeypatch.setattr(progress_module, "read_study_progress", lambda **_: {})


def test_materialize_domain_action_requests_dry_run_ignores_unsupported_action_without_writes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    latest_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "schema_version": 1,
            "action_queue": [_unsupported_domain_action(study_id, "quest-nf")],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
    )

    assert result["surface"] == "domain_action_request_materializer"
    assert result["dry_run"] is True
    assert result["effective_mode"] == "developer_apply_safe"
    assert result["github_gate"]["allowed"] is True
    assert result["runtime_control_owner"] == "one-person-lab"
    assert result["request_task_count"] == 0
    assert result["domain_progress_transition_request_count"] == 0
    assert result["ignored_actions"] == [
        {
            "study_id": study_id,
            "action_type": "unsupported_supervisor_action",
            "action_id": f"supervisor-action::{study_id}::unsupported_supervisor_action",
            "reason": "unsupported_action_type",
        }
    ]
    assert "repair_tasks" not in result
    assert not (profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json").exists()
    assert not (study_root / "artifacts" / "supervision" / "consumer" / "unsupported_supervisor_action.json").exists()


def test_materialize_domain_action_requests_apply_does_not_write_unsupported_action_surfaces(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    latest_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "schema_version": 1,
            "action_queue": [_unsupported_domain_action(study_id, "quest-nf")],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    consumer_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json"
    unsupported_packet_path = study_root / "artifacts" / "supervision" / "consumer" / "unsupported_supervisor_action.json"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "unsupported_supervisor_action.json"
    )
    assert result["dry_run"] is False
    assert result["runtime_control_owner"] == "one-person-lab"
    assert result["request_task_count"] == 0
    assert result["domain_progress_transition_request_count"] == 0
    assert result["ignored_actions"][0]["action_type"] == "unsupported_supervisor_action"
    assert result["ignored_actions"][0]["reason"] == "unsupported_action_type"
    assert not consumer_path.exists()
    assert not unsupported_packet_path.exists()
    assert not dispatch_path.exists()
    assert result["written_files"] == []
    assert not (study_root / "paper").exists()
    assert not (study_root / "manuscript").exists()


def test_materialize_domain_action_requests_does_not_resurrect_existing_unsupported_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    _disable_progress_projection(monkeypatch)
    profile = make_profile(tmp_path)
    study_id = "003-endocrine-burden-followup"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-nf")
    action = _unsupported_domain_action(study_id, "quest-nf")
    route = dict(action["owner_route"])
    route.update(
        {
            "schema_version": 2,
            "truth_epoch": route["route_epoch"],
            "runtime_health_epoch": "runtime-health-repeat",
            "work_unit_fingerprint": "unsupported-supervisor::repeat",
            "failure_signature": "unsupported_supervisor_action",
            "trace_id": "owner-route-trace::repeat",
        }
    )
    action["owner_route"] = route
    action["handoff_packet"]["owner_route"] = route
    latest_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "portable_paper_mission_owner_surface",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": route,
                    "meaningful_artifact_delta": False,
                }
            ],
            "action_queue": [action],
        },
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "unsupported_supervisor_action.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
            "study_id": study_id,
            "quest_id": "quest-nf",
            "action_type": "unsupported_supervisor_action",
            "dispatch_status": "ready",
            "owner_route": route,
            "idempotency_key": route["idempotency_key"],
            "prompt_contract": {
                "do_not_repeat": True,
                "repeat_suppression_key": "unsupported-supervisor::repeat",
            },
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["runtime_control_owner"] == "one-person-lab"
    assert result["request_task_count"] == 0
    assert result["domain_progress_transition_request_count"] == 0
    assert result["ignored_actions"][0]["action_type"] == "unsupported_supervisor_action"
    assert result["ignored_actions"][0]["reason"] == "unsupported_action_type"
    assert result["repeat_suppressed_count"] == 0
    assert result["written_files"] == []
    assert not (
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json"
    ).exists()
    assert dispatch_path.read_text(encoding="utf-8").find('"dispatch_status": "ready"') != -1
