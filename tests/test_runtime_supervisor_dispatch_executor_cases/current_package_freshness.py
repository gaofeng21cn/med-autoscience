from __future__ import annotations

import importlib
from pathlib import Path

from tests.runtime_supervisor_dispatch_executor_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_runs_current_package_freshness_owner_workflow(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_dispatch_executor")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "001-dm-cvd-mortality-risk"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    quest_root = profile.runtime_root / f"quest-{study_id}"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "current_package_freshness_required.json"
    )
    dispatch = _dispatch(
        study_id=study_id,
        action_type="current_package_freshness_required",
        owner="artifact_os",
        required_output_surface="artifacts/controller/gate_clearing_batch/latest.json",
    )
    _write_current_dispatch(
        dispatch_path,
        profile,
        dispatch,
    )
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

    def fake_run_gate_clearing_batch(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
        }

    monkeypatch.setattr(module.gate_clearing_batch, "run_gate_clearing_batch", fake_run_gate_clearing_batch)

    result = module.execute_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        action_types=("current_package_freshness_required",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    execution = result["executions"][0]
    assert execution["execution_status"] == "executed"
    assert execution["blocked_reason"] is None
    assert execution["owner_callable_surface"] == "gate_clearing_batch.run_gate_clearing_batch"
    assert called["profile"] == profile
    assert called["study_id"] == study_id
    assert called["study_root"] == study_root
    assert called["quest_id"] == f"quest-{study_id}"
    assert called["source"] == "runtime_supervisor_dispatch_executor"
    route_context = called["control_plane_route_context"]["controller_route_context"]
    assert route_context["control_surface"] == "gate_clearing_batch"
    assert route_context["controller_action_type"] == "run_gate_clearing_batch"
    assert route_context["work_unit_id"] == "submission_minimal_refresh"
