from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_action_request_materializer_cases.shared import owner_route as _owner_route
from tests.domain_action_request_materializer_cases.shared import write_json as _write_json
from tests.study_runtime_test_helpers import make_profile, write_study


def test_owner_callable_surface_does_not_fall_back_to_registry_for_legacy_current_action() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")

    surface = module._owner_callable_surface(
        {
            "action_type": "return_to_ai_reviewer_workflow",
            "authority": "study_progress.current_executable_owner_action",
            "target_surface": {
                "ref_kind": "paper_recovery_successor_owner_action",
                "surface_ref": "artifacts/publication_eval/latest.json",
            },
        }
    )

    assert surface is None
    assert module._mas_foreground_owner_callable_action(
        {
            "action_type": "return_to_ai_reviewer_workflow",
            "authority": "study_progress.current_executable_owner_action",
            "target_surface": {
                "ref_kind": "paper_recovery_successor_owner_action",
                "surface_ref": "artifacts/publication_eval/latest.json",
            },
        }
    ) is False


def test_materializer_does_not_keep_registry_known_legacy_successor_action_as_mas_foreground(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    write_study(profile.workspace_root, study_id, quest_id=quest_id)
    route = _owner_route(
        study_id=study_id,
        quest_id=quest_id,
        next_owner="ai_reviewer",
        owner_reason="return_to_ai_reviewer_workflow",
        allowed_actions=["return_to_ai_reviewer_workflow"],
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "study_progress.current_executable_owner_action",
        "owner": "ai_reviewer",
        "next_owner": "ai_reviewer",
        "request_owner": "ai_reviewer",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "work_unit_id": "return_to_ai_reviewer_workflow",
        "work_unit_fingerprint": "ai-reviewer-current-inputs-fingerprint",
        "action_fingerprint": "ai-reviewer-current-inputs-fingerprint",
        "target_surface": {
            "ref_kind": "paper_recovery_successor_owner_action",
            "surface_ref": "artifacts/publication_eval/latest.json",
        },
        "owner_route": route,
    }
    _write_json(
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json",
        {
            "surface": "portable_paper_mission_owner_surface",
            "schema_version": 1,
            "studies": [{"study_id": study_id, "quest_id": quest_id, "owner_route": route}],
            "action_queue": [action],
        },
    )

    result = module.materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
        dispatch_ready_for_execution=True,
    )

    assert result["domain_progress_transition_requests"] == []
    assert result["domain_progress_transition_request_count"] == 0
    assert any(
        item["action_type"] == "return_to_ai_reviewer_workflow"
        for item in result["ignored_actions"]
    )
