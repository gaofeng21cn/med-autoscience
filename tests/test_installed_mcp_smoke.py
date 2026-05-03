from __future__ import annotations

import json
import os
import shutil
import subprocess

from med_autoscience.control_plane_command_catalog import CONTROL_PLANE_OPERATION_MCP_MODES


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
