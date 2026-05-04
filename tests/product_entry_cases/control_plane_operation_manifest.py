from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def test_product_entry_manifest_domain_commands_include_control_plane_operations(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    catalog = importlib.import_module("med_autoscience.control_plane_command_catalog")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    payload = module.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    commands = payload["domain_entry_contract"]["supported_commands"]
    command_contracts = {
        item["command"]: item
        for item in payload["domain_entry_contract"]["command_contracts"]
    }

    for spec in catalog.CONTROL_PLANE_OPERATIONS_COMMANDS:
        assert spec.command in commands
        assert command_contracts[spec.command] == spec.command_contract()
    assert command_contracts["control-plane-governance-report"]["optional_fields"] == [
        "markdown",
        "deep",
        "max_files",
        "max_seconds",
    ]
    assert command_contracts["control-plane-backfill-apply"]["optional_fields"] == [
        "apply",
        "control_plane_snapshot",
    ]
    assert command_contracts["control-plane-safe-cache-cleanup-apply"]["optional_fields"] == [
        "apply",
        "control_plane_snapshot",
        "retention_report",
    ]
    assert command_contracts["control-plane-cleanup-apply"]["optional_fields"] == [
        "apply",
        "control_plane_snapshot",
        "retention_report",
    ]
    assert command_contracts["control-plane-lifecycle-report"]["optional_fields"] == [
        "markdown",
        "deep",
        "max_files",
        "max_seconds",
    ]
