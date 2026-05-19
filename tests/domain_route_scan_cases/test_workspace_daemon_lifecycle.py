from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def test_scan_domain_routes_apply_safe_actions_releases_idle_workspace_daemon(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-endocrine-burden-followup", quest_id="quest-nf")
    calls: list[Path] = []

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "quest_id": "quest-nf",
            "quest_status": "stopped",
            "runtime_health_snapshot": {"attempt_state": "idle"},
            "publication_eval": {"assessment_provenance": {"owner": "ai_reviewer"}},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "current_stage": "publication_supervision",
            "paper_stage": "bundle_stage_ready",
            "supervision": {"active_run_id": None},
        },
    )

    def fake_release_idle_workspace_daemon(*, runtime_root: Path):
        calls.append(runtime_root)
        return {
            "released": True,
            "reason": "idle_workspace_daemon_released",
            "runtime_root": str(runtime_root),
            "daemon_lifecycle": {"status": "idle", "active_lease_count": 0},
        }

    daemon_part = importlib.import_module("med_autoscience.controllers.domain_route_scan_parts.workspace_daemon")
    monkeypatch.setattr(daemon_part.mas_runtime_transport, "release_idle_workspace_daemon", fake_release_idle_workspace_daemon)

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=True,
    )

    assert calls == [profile.managed_runtime_home]
    assert result["workspace_daemon_lifecycle"]["released"] is True
    assert result["workspace_daemon_lifecycle"]["reason"] == "idle_workspace_daemon_released"
    assert result["workspace_daemon_lifecycle"]["daemon_lifecycle"]["active_lease_count"] == 0


def test_scan_domain_routes_observe_mode_does_not_release_workspace_daemon(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-endocrine-burden-followup", quest_id="quest-nf")

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "quest_id": "quest-nf",
            "quest_status": "stopped",
            "publication_eval": {"assessment_provenance": {"owner": "ai_reviewer"}},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "paper_stage": "bundle_stage_ready",
            "supervision": {"active_run_id": None},
        },
    )
    daemon_part = importlib.import_module("med_autoscience.controllers.domain_route_scan_parts.workspace_daemon")
    monkeypatch.setattr(
        daemon_part.mas_runtime_transport,
        "release_idle_workspace_daemon",
        lambda **_: (_ for _ in ()).throw(AssertionError("observe mode must not stop workspace daemon")),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=False,
    )

    assert result["workspace_daemon_lifecycle"]["released"] is False
    assert result["workspace_daemon_lifecycle"]["reason"] == "safe_actions_not_enabled"
