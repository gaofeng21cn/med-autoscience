from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def test_product_entry_manifest_domain_commands_include_authority_operations(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    catalog = importlib.import_module("med_autoscience.authority_operation_command_catalog")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    payload = module.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    commands = payload["domain_entry_contract"]["supported_commands"]
    command_contracts = {
        item["command"]: item
        for item in payload["domain_entry_contract"]["command_contracts"]
    }

    for spec in catalog.AUTHORITY_OPERATION_COMMANDS:
        assert spec.command in commands
        assert command_contracts[spec.command] == spec.command_contract()
    assert command_contracts["storage-governance-report"]["optional_fields"] == [
        "markdown",
        "deep",
        "max_files",
        "max_seconds",
    ]
    assert command_contracts["delivery-authority-backfill-apply"]["optional_fields"] == [
        "apply",
        "authority_snapshot",
    ]
    assert command_contracts["artifact-lifecycle-report"]["optional_fields"] == [
        "markdown",
        "deep",
        "max_files",
        "max_seconds",
    ]
    assert not any(command.startswith("control-plane-") for command in commands)
    assert "control-plane-cleanup-apply" not in command_contracts
    assert "control-plane-safe-cache-cleanup-apply" not in command_contracts


def test_product_entry_manifest_schema_enum_matches_authority_command_catalog() -> None:
    catalog = importlib.import_module("med_autoscience.authority_operation_command_catalog")
    schema_path = Path(__file__).resolve().parents[2] / "contracts" / "schemas" / "v1" / "product-entry-manifest.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    supported_command_enum = set(
        schema["$defs"]["domainEntryContract"]["properties"]["supported_commands"]["items"]["enum"]
    )
    catalog_commands = {spec.command for spec in catalog.AUTHORITY_OPERATION_COMMANDS}
    schema_authority_commands = {
        command
        for command in supported_command_enum
        if command in catalog_commands
    }

    assert not any(command.startswith("control-plane-") for command in supported_command_enum)
    assert catalog_commands == schema_authority_commands, (
        "authority command catalog/schema drift: "
        f"missing_from_schema={sorted(catalog_commands - schema_authority_commands)} "
        f"missing_from_catalog={sorted(schema_authority_commands - catalog_commands)}"
    )


def test_domain_entry_command_contracts_match_authority_command_catalog() -> None:
    catalog = importlib.import_module("med_autoscience.authority_operation_command_catalog")
    domain_entry_contract = importlib.import_module("med_autoscience.domain_entry_contract")

    expected = {
        spec.command: spec.command_contract()
        for spec in catalog.AUTHORITY_OPERATION_COMMANDS
    }
    actual = {
        item["command"]: item
        for item in domain_entry_contract.build_domain_entry_command_contracts()
        if item["command"] in expected
    }

    assert actual == expected
    assert not any(
        item["command"].startswith("control-plane-")
        for item in domain_entry_contract.build_domain_entry_command_contracts()
    )
