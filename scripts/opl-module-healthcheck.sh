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
plugin_mcp_launcher=("${repo_root}/plugins/med-autoscience/bin/medautosci-mcp")

"${clean_python[@]}" -m med_autoscience.cli --help >/dev/null
"${clean_python[@]}" -m med_autoscience.cli doctor stage-route-contract >/dev/null
mcp_tools_json="$(printf '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n' | "${plugin_mcp_launcher[@]}")"
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
plugin_root = repo_root / "plugins" / "med-autoscience"
legacy_plugin_root = repo_root / "plugins" / "mas"
skill_root = plugin_root / "skills" / "med-autoscience"
legacy_skill_root = legacy_plugin_root / "skills" / "mas"
required_paths = [
    plugin_root / ".codex-plugin" / "plugin.json",
    plugin_root / "bin" / "medautosci-mcp",
    skill_root / "SKILL.md",
    skill_root / "agents" / "openai.yaml",
]
missing = [str(path) for path in required_paths if not path.is_file()]
if missing:
    raise SystemExit(f"Missing MedAutoScience OPL plugin files: {missing}")
if not os.access(required_paths[1], os.X_OK):
    raise SystemExit("MedAutoScience plugin-local MCP launcher must be executable.")
if not legacy_plugin_root.is_symlink():
    raise SystemExit("Legacy plugins/mas compatibility path must remain a symlink to the canonical plugin root.")
if legacy_plugin_root.resolve() != plugin_root.resolve():
    raise SystemExit("Legacy plugins/mas compatibility path must resolve to plugins/med-autoscience.")
if not legacy_skill_root.is_dir():
    raise SystemExit("Legacy skills/mas compatibility path must remain available for lookup compatibility.")
if legacy_skill_root.resolve() != skill_root.resolve():
    raise SystemExit("Legacy skills/mas compatibility path must resolve to skills/med-autoscience.")

manifest = json.loads(required_paths[0].read_text(encoding="utf-8"))
if manifest.get("name") != "med-autoscience":
    raise SystemExit("MedAutoScience plugin manifest name must be `med-autoscience`.")
if manifest.get("skills") != "./skills/":
    raise SystemExit("MedAutoScience plugin manifest must point to ./skills/.")
if "mcpServers" in manifest:
    raise SystemExit("Standard MAS domain-agent plugin manifest must not expose standalone mcpServers.")

mcp_tools = {
    item["name"]: item
    for item in json.loads(os.environ["MCP_TOOLS_JSON"])["result"]["tools"]
}
if "product_entry" in mcp_tools:
    raise SystemExit("medautosci-mcp resurrected retired product_entry tool surface.")
authority_operations = mcp_tools.get("authority_operations")
if authority_operations is None:
    raise SystemExit("medautosci-mcp authority_operations tool is missing.")
authority_operation_modes = set(authority_operations["inputSchema"]["properties"]["mode"]["enum"])
required_modes = set(json.loads(os.environ["AUTHORITY_OPERATION_MCP_MODES_JSON"]))
missing_modes = sorted(required_modes - authority_operation_modes)
if missing_modes:
    raise SystemExit(f"medautosci-mcp authority_operations mode enum missing: {missing_modes}")
retired_modes = {"migration_audit", "cleanup_apply", "lifecycle_report", "safe_cache_cleanup_apply"}
resurrected_modes = sorted(retired_modes & authority_operation_modes)
if resurrected_modes:
    raise SystemExit(f"medautosci-mcp authority_operations mode enum resurrected: {resurrected_modes}")

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
        "plugin_mcp_launcher": "ready",
        "standalone_mcp_servers": "retired",
        "skill": "ready",
    },
}, ensure_ascii=False))
PY
