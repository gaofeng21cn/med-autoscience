from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from med_autoscience.controllers.domain_handler_export import paper_mission_task_shaping


def test_start_or_resume_does_not_invent_handoff_without_canonical_route(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        paper_mission_task_shaping,
        "build_paper_mission_readback",
        lambda **_: {
            "opl_runtime_carrier": {},
            "opl_route_command": {},
            "stage_terminal_decision": {},
            "forbidden_authority_writes": [],
        },
    )
    profile = SimpleNamespace(workspace_root=tmp_path)

    task = paper_mission_task_shaping.paper_mission_start_or_resume_task(
        profile=profile,
        profile_ref=tmp_path / "profile.json",
        study_id="study-001",
    )

    assert "opl_route_handoff" not in task
    assert "opl_route_handoff" not in task["payload"]
    assert "next_action" not in task
    assert "next_action" not in task["payload"]
