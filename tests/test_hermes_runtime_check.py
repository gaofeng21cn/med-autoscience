from __future__ import annotations

import importlib
from pathlib import Path


def test_run_hermes_runtime_check_blocks_when_provider_not_configured(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_runtime_check")

    monkeypatch.setattr(
        module,
        "inspect_hermes_runtime_contract",
        lambda **_: {
            "configured": True,
            "repo_exists": True,
            "is_git_repo": True,
            "launcher_exists": True,
            "gateway_launcher_exists": True,
            "managed_python_exists": True,
            "hermes_home_exists": True,
            "state_db_exists": True,
            "logs_dir_exists": True,
            "sessions_dir_exists": True,
            "provider_ready": False,
            "gateway_service_loaded": False,
            "ready": False,
            "issues": ["external_runtime.provider_not_configured"],
        },
    )

    result = module.run_hermes_runtime_check(
        hermes_agent_repo_root=tmp_path / "hermes-agent",
        hermes_home_root=tmp_path / ".hermes",
    )

    assert result["decision"] == "blocked_hermes_provider_not_configured"
    assert "configure_hermes_model_or_provider" in result["recommended_actions"]
    assert "install_or_start_hermes_gateway_service" in result["recommended_actions"]


def test_run_hermes_runtime_check_reports_ready_for_adapter_cutover(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.hermes_runtime_check")

    monkeypatch.setattr(
        module,
        "inspect_hermes_runtime_contract",
        lambda **_: {
            "configured": True,
            "repo_exists": True,
            "is_git_repo": True,
            "launcher_exists": True,
            "gateway_launcher_exists": True,
            "managed_python_exists": True,
            "hermes_home_exists": True,
            "state_db_exists": True,
            "logs_dir_exists": True,
            "sessions_dir_exists": True,
            "provider_ready": True,
            "gateway_service_loaded": True,
            "ready": True,
            "issues": [],
        },
    )

    result = module.run_hermes_runtime_check(
        hermes_agent_repo_root=tmp_path / "hermes-agent",
        hermes_home_root=tmp_path / ".hermes",
    )

    assert result["decision"] == "ready_for_adapter_cutover"
    assert result["recommended_actions"] == ["promote_repo_side_seam_to_real_adapter"]
