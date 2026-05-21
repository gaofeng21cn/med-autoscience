from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_current_dispatch as _write_current_dispatch,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_treats_quality_repair_writer_handoff_as_dispatchable_not_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    route["work_unit_fingerprint"] = "domain-transition::route_back_same_line::medical_prose_write_repair"
    route["source_fingerprint"] = "truth-source::dm003::medical-prose"
    route["idempotency_key"] = "owner-route::dm003::medical-prose"
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
    dispatch_payload["source_action"] = {
        "action_type": "run_quality_repair_batch",
        "route_target": "write",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "next_work_unit": {
            "unit_id": "medical_prose_write_repair",
            "lane": "write",
        },
    }
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_current_dispatch(dispatch_path, profile, dispatch_payload)
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

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "handoff_ready",
            "blocked_reason": None,
            "next_owner": "write",
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
        study_ids=(study_id,),
        action_types=("run_quality_repair_batch",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["blocked_count"] == 0
    assert result["codex_dispatch_count"] == 1
    execution = result["executions"][0]
    assert execution["owner_route_current"] is True
    assert execution["execution_status"] == "handoff_ready"
    assert execution["blocked_reason"] is None
    assert execution["action_class"] == "codex_worker_dispatch"
    assert execution["will_start_llm"] is True
    assert execution["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert execution["writer_worker_handoff"]["next_executable_owner"] == "write"
    assert called["study_id"] == study_id
    assert called["quest_id"] == f"quest-{study_id}"
    route_context = called["control_plane_route_context"]
    assert route_context["controller_action_type"] == "run_quality_repair_batch"
    assert route_context["work_unit_id"] == "medical_prose_write_repair"
