#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

python3 - <<'PY'
import json
from pathlib import Path

root = Path.cwd()
plugin = json.loads(
    (root / "plugins/med-autoscience/.codex-plugin/plugin.json").read_text(encoding="utf-8")
)
descriptor = json.loads((root / "contracts/domain_descriptor.json").read_text(encoding="utf-8"))
handoff = json.loads((root / "contracts/generated_surface_handoff.json").read_text(encoding="utf-8"))

assert plugin["name"] == "med-autoscience"
assert plugin["skills"] == "./skills/"
assert "mcpServers" not in plugin
assert descriptor["generated_surface_owner"] == "one-person-lab"
assert descriptor["domain_repo_can_own_generated_surface"] is False
assert handoff["generated_surface_owner"] == "one-person-lab"
assert not (root / "plugins/med-autoscience/bin/medautosci-mcp").exists()
assert not (root / "src/med_autoscience/cli/__init__.py").exists()
assert not (root / "src/med_autoscience/mcp_server/__init__.py").exists()

print(json.dumps({
    "ok": True,
    "module": "medautoscience",
    "checks": {
        "generated_surface_owner": "one-person-lab",
        "domain_handler_target": "med_autoscience.domain_entry.MedAutoScienceDomainEntry.dispatch",
        "repo_cli": "retired",
        "repo_mcp_server": "retired",
        "plugin_mcp_launcher": "retired",
        "skill_carrier": "ready",
    },
}, ensure_ascii=False))
PY
