from __future__ import annotations

import argparse
import json

from med_autoscience.authority_operation_command_catalog import AUTHORITY_OPERATION_COMMANDS
from tests.test_test_command_surfaces import (
    _assert_command_surface_matches_catalog,
    _assert_mcp_modes_cover_catalog,
    _read,
)


def test_authority_operation_command_catalog_guards_cli_mcp_manifest_and_schema_surfaces() -> None:
    from med_autoscience import cli, domain_entry_contract, mcp_server

    parser = cli.build_parser()
    cli_commands: set[str] = set()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            cli_commands.update(action.choices)

    mcp_tools = {tool["name"]: tool for tool in mcp_server.build_tool_manifest()}
    mcp_modes = set(mcp_tools["authority_operations"]["inputSchema"]["properties"]["mode"]["enum"])
    domain_catalog = domain_entry_contract.build_domain_entry_command_catalog()
    product_entry_manifest_contract = domain_entry_contract.build_domain_entry_contract()
    schema = json.loads(_read("contracts/schemas/v1/product-entry-manifest.schema.json"))
    supported_command_enum = set(
        schema["$defs"]["domainEntryContract"]["properties"]["supported_commands"]["items"]["enum"]
    )
    catalog_commands = {spec.command for spec in AUTHORITY_OPERATION_COMMANDS}
    assert not any(command.startswith("control-plane-") for command in cli_commands)
    assert not any(command.startswith("control-plane-") for command in supported_command_enum)
    assert "cleanup_apply" not in mcp_modes
    assert "safe_cache_cleanup_apply" not in mcp_modes

    _assert_command_surface_matches_catalog(
        surface="cli",
        expected_commands=catalog_commands,
        actual_commands={command for command in cli_commands if command in catalog_commands},
    )
    _assert_mcp_modes_cover_catalog(
        expected=AUTHORITY_OPERATION_COMMANDS,
        actual_modes=mcp_modes,
    )
    _assert_command_surface_matches_catalog(
        surface="product_entry_manifest",
        expected_commands=catalog_commands,
        actual_commands={
            command
            for command in product_entry_manifest_contract["supported_commands"]
            if command in catalog_commands
        },
    )
    _assert_command_surface_matches_catalog(
        surface="domain_entry_command_catalog",
        expected_commands=catalog_commands,
        actual_commands={
            item["command"]
            for item in domain_catalog["command_contracts"]
            if item["command"] in catalog_commands
        },
    )
    _assert_command_surface_matches_catalog(
        surface="schema",
        expected_commands=catalog_commands,
        actual_commands={command for command in supported_command_enum if command in catalog_commands},
    )

    manifest_contracts = {
        item["command"]: item
        for item in product_entry_manifest_contract["command_contracts"]
        if item["command"] in catalog_commands
    }
    for spec in AUTHORITY_OPERATION_COMMANDS:
        assert manifest_contracts.get(spec.command) == spec.command_contract(), (
            "authority command contract drift: "
            f"command={spec.command!r} "
            f"manifest_contract={manifest_contracts.get(spec.command)!r} "
            f"catalog_contract={spec.command_contract()!r}"
        )
