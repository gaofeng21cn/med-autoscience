from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    write_current_dispatch as _write_current_dispatch,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_runtime_platform_repair_dispatch_uses_non_persistent_scan(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    scan_module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    latest_path = profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"
    dispatch = _dispatch(
        study_id=study_id,
        action_type="runtime_platform_repair",
        owner="external_engineering_agent",
        required_output_surface="artifacts/supervision/consumer/runtime_platform_repair.json",
    )
    _write_json(
        latest_path,
        {
            "surface": "portable_domain_route_scan",
            "generated_at": "2026-05-05T00:00:00+00:00",
            "studies": [
                {"study_id": "001-dm-cvd-mortality-risk"},
                {"study_id": study_id, "owner_route": dispatch["owner_route"]},
            ],
        },
    )
    _write_current_dispatch(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "runtime_platform_repair.json",
        profile,
        dispatch,
    )
    before = latest_path.read_text(encoding="utf-8")
    called: dict[str, object] = {}

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        assert kwargs["persist_surfaces"] is False
        return {
            "surface": "portable_domain_route_scan",
            "studies": [
                {
                    "study_id": study_id,
                    "runtime_platform_repair_apply": {
                        "dispatch_status": "applied",
                        "reason": "stale_specificity_terminal_gate_cleared",
                    },
                }
            ],
        }

    monkeypatch.setattr(scan_module, "scan_domain_routes", fake_scan_domain_routes)

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        action_types=("runtime_platform_repair",),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executed_count"] == 1
    assert result["codex_dispatch_count"] == 0
    assert result["executions"][0]["action_class"] == "controller_apply"
    assert result["executions"][0]["will_start_llm"] is False
    assert called["study_ids"] == (study_id,)
    assert called["apply_runtime_platform_repair"] is True
    assert latest_path.read_text(encoding="utf-8") == before
