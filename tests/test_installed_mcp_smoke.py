from __future__ import annotations

import json
import os
import shutil
import subprocess

from med_autoscience.control_plane_command_catalog import (
    CONTROL_PLANE_OPERATION_CLI_COMMANDS,
    CONTROL_PLANE_OPERATION_MCP_MODES,
    CONTROL_PLANE_OPERATIONS_COMMANDS,
)


def test_installed_medautosci_mcp_lists_control_plane_operation_modes() -> None:
    executable = shutil.which("medautosci-mcp")
    assert executable is not None

    environment = dict(os.environ)
    environment["PYTHONPATH"] = "src" + os.pathsep + environment.get("PYTHONPATH", "")
    result = subprocess.run(
        [executable],
        input='{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n',
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
        env=environment,
    )
    payload = json.loads(result.stdout)
    tools = {tool["name"]: tool for tool in payload["result"]["tools"]}
    mode_schema = tools["product_entry"]["inputSchema"]["properties"]["mode"]

    assert set(CONTROL_PLANE_OPERATION_MCP_MODES).issubset(set(mode_schema["enum"]))


def test_installed_medautosci_mcp_lists_storage_governance_surface_modes() -> None:
    executable = shutil.which("medautosci-mcp")
    assert executable is not None

    environment = dict(os.environ)
    environment["PYTHONPATH"] = "src" + os.pathsep + environment.get("PYTHONPATH", "")
    result = subprocess.run(
        [executable],
        input='{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n',
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
        env=environment,
    )
    payload = json.loads(result.stdout)
    tools = {tool["name"]: tool for tool in payload["result"]["tools"]}
    mode_schema = tools["product_entry"]["inputSchema"]["properties"]["mode"]
    expected_modes = {
        item.mcp_mode
        for item in CONTROL_PLANE_OPERATIONS_COMMANDS
        if item.surface in {
            "storage_governance_report",
            "control_plane_backfill_apply",
            "control_plane_safe_cache_cleanup_apply",
        }
    }

    assert expected_modes == {
        "governance_report",
        "backfill_apply",
        "safe_cache_cleanup_apply",
    }
    assert expected_modes.issubset(set(mode_schema["enum"]))


def test_installed_medautosci_cli_lists_control_plane_operation_commands() -> None:
    executable = shutil.which("medautosci")
    assert executable is not None

    environment = dict(os.environ)
    environment["PYTHONPATH"] = "src" + os.pathsep + environment.get("PYTHONPATH", "")
    result = subprocess.run(
        [executable, "--help"],
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
        env=environment,
    )

    for command in CONTROL_PLANE_OPERATION_CLI_COMMANDS:
        assert command in result.stdout


def test_installed_medautosci_cli_lists_storage_governance_commands() -> None:
    executable = shutil.which("medautosci")
    assert executable is not None

    environment = dict(os.environ)
    environment["PYTHONPATH"] = "src" + os.pathsep + environment.get("PYTHONPATH", "")
    result = subprocess.run(
        [executable, "--help"],
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
        env=environment,
    )
    expected_commands = {
        item.cli_command
        for item in CONTROL_PLANE_OPERATIONS_COMMANDS
        if item.surface in {
            "storage_governance_report",
            "control_plane_backfill_apply",
            "control_plane_safe_cache_cleanup_apply",
        }
    }

    for command in expected_commands:
        assert command in result.stdout
