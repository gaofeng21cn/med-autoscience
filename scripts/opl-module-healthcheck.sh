#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

healthcheck_tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/mas-opl-healthcheck.XXXXXX")"
cleanup_healthcheck_tmp_root() {
  rm -rf "${healthcheck_tmp_root}"
}
trap cleanup_healthcheck_tmp_root EXIT

command -v python3 >/dev/null 2>&1
command -v uv >/dev/null 2>&1

export MAS_CLEAN_RUNNER_ANALYSIS_EXTRA=1
export MAS_CLEAN_RUNNER_TMP_ROOT="${healthcheck_tmp_root}/python"
clean_python=("${repo_root}/scripts/run-python-clean.sh")

"${clean_python[@]}" -m med_autoscience.cli --help >/dev/null
"${clean_python[@]}" -m med_autoscience.cli doctor stage-route-contract >/dev/null
mcp_tools_json="$(printf '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n' | "${clean_python[@]}" -m med_autoscience.mcp_server)"
authority_operation_mcp_modes_json="$("${clean_python[@]}" - <<'PY'
import json
from med_autoscience.authority_operation_command_catalog import AUTHORITY_OPERATION_MCP_MODES

print(json.dumps(AUTHORITY_OPERATION_MCP_MODES))
PY
)"
export MCP_TOOLS_JSON="${mcp_tools_json}"
export AUTHORITY_OPERATION_MCP_MODES_JSON="${authority_operation_mcp_modes_json}"

python3 - <<'PY'
import json
import os
from pathlib import Path

repo_root = Path.cwd()
required_paths = [
    repo_root / "plugins" / "mas" / ".codex-plugin" / "plugin.json",
    repo_root / "plugins" / "mas" / ".mcp.json",
    repo_root / "plugins" / "mas" / "skills" / "mas" / "SKILL.md",
    repo_root / "plugins" / "mas" / "skills" / "mas" / "agents" / "openai.yaml",
]
missing = [str(path) for path in required_paths if not path.is_file()]
if missing:
    raise SystemExit(f"Missing MedAutoScience OPL plugin files: {missing}")

manifest = json.loads(required_paths[0].read_text(encoding="utf-8"))
if manifest.get("name") != "mas":
    raise SystemExit("MedAutoScience plugin manifest name must be `mas`.")
if manifest.get("skills") != "./skills/":
    raise SystemExit("MedAutoScience plugin manifest must point to ./skills/.")

mcp_tools = {
    item["name"]: item
    for item in json.loads(os.environ["MCP_TOOLS_JSON"])["result"]["tools"]
}
product_entry_modes = set(mcp_tools["product_entry"]["inputSchema"]["properties"]["mode"]["enum"])
required_modes = set(json.loads(os.environ["AUTHORITY_OPERATION_MCP_MODES_JSON"]))
missing_modes = sorted(required_modes - product_entry_modes)
if missing_modes:
    raise SystemExit(f"medautosci-mcp product_entry mode enum missing: {missing_modes}")
retired_modes = {"migration_audit", "cleanup_apply", "lifecycle_report", "safe_cache_cleanup_apply"}
resurrected_modes = sorted(retired_modes & product_entry_modes)
if resurrected_modes:
    raise SystemExit(f"medautosci-mcp product_entry mode enum resurrected: {resurrected_modes}")

print(json.dumps({
    "ok": True,
    "module": "medautoscience",
    "checks": {
        "cli": "repo-local clean runner medautosci",
        "mcp_cli": "repo-local clean runner medautosci-mcp",
        "public_help": "ready",
        "entry_modes": "ready",
        "mcp_control_plane_modes": "ready",
        "plugin": "ready",
        "skill": "ready",
    },
}, ensure_ascii=False))
PY
