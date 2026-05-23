from __future__ import annotations

import json
import os
import shutil
import subprocess

from med_autoscience.authority_operation_command_catalog import (
    AUTHORITY_OPERATION_CLI_COMMANDS,
    AUTHORITY_OPERATION_MCP_MODES,
    AUTHORITY_OPERATION_COMMANDS,
)


def test_installed_medautosci_mcp_lists_authority_operation_modes() -> None:
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

    assert set(AUTHORITY_OPERATION_MCP_MODES).issubset(set(mode_schema["enum"]))


def test_installed_medautosci_mcp_lists_authority_surface_modes() -> None:
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
        for item in AUTHORITY_OPERATION_COMMANDS
        if item.surface in {
            "storage_governance_report",
            "delivery_authority_backfill_apply",
            "artifact_lifecycle_continuous_soak_summary",
        }
    }

    assert expected_modes == {
        "storage_governance_report",
        "delivery_authority_backfill_apply",
        "artifact_lifecycle_continuous_soak_summary",
    }
    assert expected_modes.issubset(set(mode_schema["enum"]))
    assert "cleanup_apply" not in mode_schema["enum"]
    assert "safe_cache_cleanup_apply" not in mode_schema["enum"]


def test_installed_medautosci_cli_lists_authority_operation_commands() -> None:
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

    for command in AUTHORITY_OPERATION_CLI_COMMANDS:
        assert command in result.stdout
    assert "control-plane-cleanup-apply" not in result.stdout
    assert "control-plane-safe-cache-cleanup-apply" not in result.stdout


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
        for item in AUTHORITY_OPERATION_COMMANDS
        if item.surface in {
            "storage_governance_report",
            "delivery_authority_backfill_apply",
            "artifact_lifecycle_continuous_soak_summary",
        }
    }

    for command in expected_commands:
        assert command in result.stdout


def test_installed_medautosci_mcp_calls_artifact_lifecycle_continuous_soak_summary(tmp_path) -> None:
    executable = shutil.which("medautosci-mcp")
    assert executable is not None

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    environment = dict(os.environ)
    environment["PYTHONPATH"] = "src" + os.pathsep + environment.get("PYTHONPATH", "")
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "product_entry",
            "arguments": {
                "mode": "artifact_lifecycle_continuous_soak_summary",
                "workspace_roots": [str(workspace_root)],
            },
        },
    }
    result = subprocess.run(
        [executable],
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
        env=environment,
    )
    payload = json.loads(result.stdout)
    structured = payload["result"]["structuredContent"]

    assert structured["surface"] == "continuous_soak_summary"
    assert structured["mutating_actions"] == 0
    assert structured["unclassified_authority_surface"] == 0
    assert structured["writes_workspace"] is False
    assert structured["read_only_contract"] == {
        "dry_run": True,
        "physical_cleanup_owned_by": "one-person-lab",
        "writes_workspace": False,
    }


def test_installed_medautosci_cli_calls_artifact_lifecycle_continuous_soak_summary(tmp_path) -> None:
    executable = shutil.which("medautosci")
    assert executable is not None

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    environment = dict(os.environ)
    environment["PYTHONPATH"] = "src" + os.pathsep + environment.get("PYTHONPATH", "")
    result = subprocess.run(
        [
            executable,
            "artifact-lifecycle-continuous-soak-summary",
            "--workspace-root",
            str(workspace_root),
        ],
        text=True,
        capture_output=True,
        check=True,
        timeout=10,
        env=environment,
    )
    payload = json.loads(result.stdout)

    assert payload["surface"] == "continuous_soak_summary"
    assert payload["mutating_actions"] == 0
    assert payload["unclassified_authority_surface"] == 0
    assert payload["writes_workspace"] is False
