from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from med_autoscience.domain_entry import MedAutoScienceDomainEntry
from med_autoscience.domain_entry_contract import SERVICE_SAFE_ENTRY_TARGET


PROBE_COMMAND = "mainline-status"


def build_domain_handler_probe() -> dict[str, Any]:
    response = MedAutoScienceDomainEntry().dispatch({"command": PROBE_COMMAND})
    if response.get("command") != PROBE_COMMAND:
        raise RuntimeError("MAS domain handler probe returned an unexpected command identity.")
    return {
        "ok": True,
        "surface_kind": "opl_module_domain_handler_probe",
        "module_id": "medautoscience",
        "domain_handler_target": SERVICE_SAFE_ENTRY_TARGET,
        "probe_command": PROBE_COMMAND,
        "probe_effect": "read_only",
        "domain_mutation": False,
    }


def build_module_healthcheck(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
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

    probe = build_domain_handler_probe()
    return {
        "ok": True,
        "surface_kind": "opl_module_runtime_source_healthcheck",
        "module": "medautoscience",
        "checks": {
            "generated_surface_owner": "one-person-lab",
            "domain_handler_target": SERVICE_SAFE_ENTRY_TARGET,
            "domain_handler_probe": probe,
            "repo_cli": "retired",
            "repo_mcp_server": "retired",
            "plugin_mcp_launcher": "retired",
            "skill_carrier": "ready",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the OPL-managed MAS source carrier without domain mutation."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--probe", action="store_true", help="Probe the canonical domain handler target.")
    mode.add_argument("--healthcheck", action="store_true", help="Run the full source-carrier healthcheck.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    payload = build_domain_handler_probe() if args.probe else build_module_healthcheck(args.repo_root)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
