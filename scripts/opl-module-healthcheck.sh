#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

command -v python3 >/dev/null 2>&1
command -v uv >/dev/null 2>&1
medautosci_bin="$(command -v medautosci)"
medautosci_mcp_bin="$(command -v medautosci-mcp)"

"${medautosci_bin}" --help >/dev/null
"${medautosci_bin}" doctor entry-modes >/dev/null

python3 - <<'PY'
import json
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

print(json.dumps({
    "ok": True,
    "module": "medautoscience",
    "checks": {
        "cli": "medautosci",
        "mcp_cli": "medautosci-mcp",
        "public_help": "ready",
        "entry_modes": "ready",
        "plugin": "ready",
        "skill": "ready",
    },
}, ensure_ascii=False))
PY
