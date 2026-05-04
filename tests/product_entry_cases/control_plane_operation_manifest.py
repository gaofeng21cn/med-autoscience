from __future__ import annotations

import importlib
import json
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


def test_product_entry_manifest_schema_enum_matches_control_plane_command_catalog() -> None:
    catalog = importlib.import_module("med_autoscience.control_plane_command_catalog")
    schema_path = Path(__file__).resolve().parents[2] / "contracts" / "schemas" / "v1" / "product-entry-manifest.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    supported_command_enum = set(
        schema["$defs"]["domainEntryContract"]["properties"]["supported_commands"]["items"]["enum"]
    )
    catalog_commands = {spec.command for spec in catalog.CONTROL_PLANE_OPERATIONS_COMMANDS}
    schema_control_plane_commands = {
        command for command in supported_command_enum if command.startswith("control-plane-")
    }

    assert catalog_commands == schema_control_plane_commands, (
        "control-plane command catalog/schema drift: "
        f"missing_from_schema={sorted(catalog_commands - schema_control_plane_commands)} "
        f"missing_from_catalog={sorted(schema_control_plane_commands - catalog_commands)}"
    )


def test_domain_entry_command_contracts_match_control_plane_command_catalog() -> None:
    catalog = importlib.import_module("med_autoscience.control_plane_command_catalog")
    domain_entry_contract = importlib.import_module("med_autoscience.domain_entry_contract")

    expected = {
        spec.command: spec.command_contract()
        for spec in catalog.CONTROL_PLANE_OPERATIONS_COMMANDS
    }
    actual = {
        item["command"]: item
        for item in domain_entry_contract.build_domain_entry_command_contracts()
        if item["command"].startswith("control-plane-")
    }

    assert actual == expected
