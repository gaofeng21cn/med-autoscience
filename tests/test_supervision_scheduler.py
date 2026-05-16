from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def _write_legacy_local_scheduler_artifacts(local, profile) -> tuple[Path, Path]:
    script_path = local._tick_script_path(profile)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("#!/bin/sh\necho legacy MAS scheduler\n", encoding="utf-8")
    script_path.chmod(0o755)
    plist_path = local._launch_agent_path(profile)
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_bytes(
        local.plistlib.dumps(
            {
                "Label": local._launchd_label(profile),
                "ProgramArguments": [str(script_path)],
                "StartInterval": 300,
            }
        )
    )
    return script_path, plist_path


def test_default_scheduler_status_uses_opl_replacement_without_launchagent(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
    launch_agents = tmp_path / "LaunchAgents"
    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(launch_agents))

    result = module.read_supervision_status(profile=profile)

    assert result["scheduler_owner"] == "opl_provider_runtime_manager"
    assert result["adapter_id"] == "opl_family_runtime_provider"
    assert result["manager"] == "opl"
    assert result["status"] == "replacement_owner_active"
    assert result["loaded"] is True
    assert result["adapter_status"]["migration_state"] == "replacement_owner_active"
    assert result["opl_replacement"]["provider_slo_tick_command"] == (
        "opl family-runtime provider-slo tick --provider temporal"
    )
    assert result["legacy_adapter"]["manager"] == "local"
    assert result["legacy_adapter"]["scheduler_owner"] == "mas_supervision_scheduler"
    assert result["authority_boundary"]["can_install_domain_daemon"] is False
    assert result["authority_boundary"]["can_own_generic_scheduler"] is False
    assert result["authority_boundary"]["can_own_generic_daemon"] is False
    assert result["authority_boundary"]["can_own_generic_queue"] is False
    assert result["authority_boundary"]["can_own_generic_attempt_ledger"] is False
    assert result["authority_boundary"]["can_own_generic_runner"] is False
    assert result["authority_boundary"]["can_own_generic_workbench"] is False
    assert result["outer_supervision_slo"]["supervision_owner"] == "opl_provider_runtime_manager"
    boundary = result["consumer_migration"]["functional_consumer_boundary"]
    assert boundary["surface_kind"] == "mas_functional_consumer_boundary"
    assert boundary["generic_surface_owner"] == "one-person-lab"
    assert set(boundary["mas_does_not_own"]) >= {
        "generic_scheduler",
        "generic_daemon",
        "generic_queue",
        "generic_attempt_ledger",
        "generic_runner",
        "generic_workbench",
    }
    assert set(boundary["mas_retains"]) >= {
        "study_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "publication_route_memory_body",
        "owner_receipt",
        "typed_blocker",
    }
    assert not launch_agents.exists()


def test_default_scheduler_ensure_delegates_to_opl_replacement_without_launchagent(
    monkeypatch, tmp_path: Path
) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
    launch_agents = tmp_path / "LaunchAgents"
    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(launch_agents))

    result = module.ensure_supervision(profile=profile, trigger_now=True, write_install_proof=True)

    assert result["action"] == "delegated_to_opl_provider_scheduler"
    assert result["scheduler_owner"] == "opl_provider_runtime_manager"
    assert result["manager"] == "opl"
    assert result["dry_run"] is False
    assert result["write_install_proof"] is False
    assert result["after"]["status"] == "replacement_owner_active"
    assert result["legacy_local_adapter"]["manager"] == "local"
    assert result["authority_boundary"]["can_install_domain_daemon"] is False
    assert not launch_agents.exists()


def test_default_scheduler_remove_delegates_to_opl_and_keeps_local_cleanup_explicit(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    profile = make_profile(tmp_path)

    result = module.remove_supervision(profile=profile)

    assert result["action"] == "delegated_to_opl_provider_scheduler"
    assert result["scheduler_owner"] == "opl_provider_runtime_manager"
    assert result["manager"] == "opl"
    assert result["removed_job_ids"] == []
    assert result["legacy_local_cleanup_command"].endswith(" --manager local")


def test_local_scheduler_dry_run_projects_launchd_without_hermes(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)

    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(tmp_path / "LaunchAgents"))

    result = module.ensure_supervision(
        profile=profile,
        manager="local",
        trigger_now=False,
        dry_run=True,
    )

    assert result["scheduler_owner"] == "mas_supervision_scheduler"
    assert result["adapter_id"] == "local_launchd"
    assert result["active_path_role"] == "standalone_local_diagnostic_migration_bridge"
    assert result["consumer_migration"]["replacement_owner"] == "one-person-lab"
    assert result["consumer_migration"]["replacement_owner_surface"] == "opl_provider_runtime_manager"
    assert result["consumer_migration"]["replacement_required_before_retirement"] is True
    assert result["dry_run"] is True
    assert result["write_install_proof"] is False
    assert result["reason"] == "mas_local_scheduler_install_retired_use_opl_replacement"
    assert "install_proof" not in result
    assert result["after"]["adapter_id"] == "local_launchd"
    assert not Path(result["script_path"]).exists()


def test_local_scheduler_ensure_is_retired_cleanup_only(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
    launch_agents = tmp_path / "LaunchAgents"
    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(launch_agents))

    result = module.ensure_supervision(
        profile=profile,
        manager="local",
        trigger_now=True,
        write_install_proof=True,
    )

    assert result["action"] == "retired_cleanup_only"
    assert result["status"] == "blocked"
    assert result["write_install_proof"] is False
    assert result["reason"] == "mas_local_scheduler_install_retired_use_opl_replacement"
    assert "install_proof" not in result
    assert result["cleanup_command"].endswith(" --manager local")
    assert result["after"]["job_exists"] is False
    assert result["after"]["active_path_role"] == "standalone_local_diagnostic_migration_bridge"
    assert result["after"]["consumer_migration"]["retirement_state"] == (
        "local_legacy_retirement_pending_no_active_caller_proof"
    )
    assert not Path(result["script_path"]).exists()
    assert not Path(result["launch_agent_path"]).exists()
    assert result["command_outputs"] == []


def test_local_scheduler_apply_blocks_when_workspace_python_missing(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
    launch_agents = tmp_path / "LaunchAgents"
    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(launch_agents))

    result = module.ensure_supervision(
        profile=profile,
        manager="local",
        trigger_now=True,
        write_install_proof=True,
    )

    assert result["action"] == "retired_cleanup_only"
    assert result["status"] == "blocked"
    assert result["write_install_proof"] is False
    assert result["reason"] == "mas_local_scheduler_install_retired_use_opl_replacement"
    assert "install_proof" not in result
    assert not Path(result["script_path"]).exists()
    assert not Path(result["launch_agent_path"]).exists()


def test_local_scheduler_status_treats_existing_launchagent_as_retired_cleanup_evidence(
    monkeypatch, tmp_path: Path
) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
    launch_agents = tmp_path / "LaunchAgents"
    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(launch_agents))

    script_path, plist_path = _write_legacy_local_scheduler_artifacts(local, profile)
    monkeypatch.setattr(
        local,
        "_run_command",
        lambda command: {"command": command, "exit_code": 0, "output": "service is loaded"},
    )

    result = module.read_supervision_status(profile=profile, manager="local")

    assert result["status"] == "retired_legacy_cleanup_required"
    assert result["loaded"] is False
    assert result["adapter_loaded"] is False
    assert result["adapter_enabled"] is False
    assert result["job_enabled"] is False
    assert result["job_state"] == "retired_cleanup_required"
    assert result["legacy_service_role"] == "retired_cleanup_evidence"
    assert result["retired_legacy_cleanup_required"] is True
    assert result["retired_artifacts"] == {
        "launch_agent": str(plist_path),
        "tick_script": str(script_path),
    }
    assert "legacy_launch_agent_present" in result["drift_reasons"]
    assert "legacy_tick_script_present" in result["drift_reasons"]
    assert result["launch_agent_probe"]["loaded"] is True
    assert result["outer_supervision_slo"]["state"] == "blocked"
    assert "retired_legacy_cleanup_required" in result["outer_supervision_slo"]["blocked_reasons"]
    assert result["tick_script_checksum"] is None
    assert result["expected_tick_script_checksum"] is None
    assert result["watch_command"] == []
    assert result["tick_sequence"] == []


def test_local_scheduler_remove_deletes_legacy_launchagent_and_tick_script(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    local = importlib.import_module("med_autoscience.controllers.supervision_scheduler_parts.local_adapter")
    profile = make_profile(tmp_path)
    launch_agents = tmp_path / "LaunchAgents"
    monkeypatch.setattr(local.platform, "system", lambda: "Darwin")
    monkeypatch.setenv("MAS_LAUNCHD_AGENTS_DIR", str(launch_agents))

    script_path, plist_path = _write_legacy_local_scheduler_artifacts(local, profile)
    monkeypatch.setattr(
        local,
        "_run_command",
        lambda command: {"command": command, "exit_code": 0, "output": ""},
    )

    result = module.remove_supervision(profile=profile, manager="local")

    assert result["before"]["status"] == "retired_legacy_cleanup_required"
    assert result["after"]["status"] == "not_installed"
    assert result["launch_agent_removed"] is True
    assert result["script_removed"] is True
    assert result["removed_job_ids"] == [result["before"]["job_id"]]
    assert not plist_path.exists()
    assert not script_path.exists()


def test_explicit_hermes_adapter_is_projected_under_mas_scheduler_owner(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    profile = make_profile(tmp_path)

    monkeypatch.setattr(
        module.hermes_supervision,
        "read_supervision_status",
        lambda **_: {
            "schema_version": 1,
            "surface_kind": "workspace_runtime_supervision",
            "owner": "hermes_gateway_cron",
            "status": "loaded",
            "loaded": True,
            "job_name": "medautoscience-supervision-diabetes-abc12345",
            "watch_command": ["watch-runtime", "--interval-seconds", "300"],
        },
    )

    result = module.read_supervision_status(profile=profile, manager="hermes")

    assert result["scheduler_owner"] == "mas_supervision_scheduler"
    assert result["adapter_id"] == "hermes_gateway_cron"
    assert result["active_path_role"] == "standalone_local_diagnostic_migration_bridge"
    assert result["consumer_migration"]["replacement_owner"] == "one-person-lab"
    assert result["owner"] == "hermes_gateway_cron"
    assert result["workspace_key"] == "diabetes-abc12345"
    assert result["outer_supervision_slo"]["supervision_owner"] == "mas_supervision_scheduler"
    assert result["outer_supervision_slo"]["adapter_id"] == "hermes_gateway_cron"
    assert result["outer_supervision_slo"]["handoff"]["replacement_owner"] == "one-person-lab"
    assert result["outer_supervision_slo"]["consumer_migration"]["retirement_proof_required"] == [
        "opl_replacement_contract_available",
        "replacement_proof",
        "no_active_caller_proof",
        "no_forbidden_write",
        "focused_cli_status_tests",
        "git_diff_check",
    ]
