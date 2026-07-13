from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from med_autoscience.domain_entry import MedAutoScienceDomainEntry
from med_autoscience.domain_entry_contract import SERVICE_SAFE_DOMAIN_COMMANDS, SERVICE_SAFE_ENTRY_TARGET


PROBE_COMMAND = "mainline-status"


def build_domain_entry_request(
    *,
    command: str,
    string_fields: list[tuple[str, str]] | None = None,
    list_fields: list[tuple[str, str]] | None = None,
    flag_fields: list[str] | None = None,
) -> dict[str, Any]:
    normalized_command = command.strip().replace("_", "-")
    spec = SERVICE_SAFE_DOMAIN_COMMANDS.get(normalized_command)
    if spec is None:
        raise ValueError(f"Unsupported MAS domain entry command: {normalized_command}")

    allowed_fields = {"command", *spec.required_fields, *spec.optional_fields}
    request: dict[str, Any] = {"command": normalized_command}
    for field_name, value in string_fields or []:
        _assert_allowed_request_field(normalized_command, field_name, allowed_fields)
        if field_name in request:
            raise ValueError(f"Duplicate MAS domain entry field: {field_name}")
        request[field_name] = value
    for field_name, value in list_fields or []:
        _assert_allowed_request_field(normalized_command, field_name, allowed_fields)
        current = request.setdefault(field_name, [])
        if not isinstance(current, list):
            raise ValueError(f"MAS domain entry field cannot be both scalar and list: {field_name}")
        current.append(value)
    for field_name in flag_fields or []:
        _assert_allowed_request_field(normalized_command, field_name, allowed_fields)
        if field_name in request:
            raise ValueError(f"Duplicate MAS domain entry field: {field_name}")
        request[field_name] = True
    return request


def _assert_allowed_request_field(command: str, field_name: str, allowed_fields: set[str]) -> None:
    if field_name not in allowed_fields:
        raise ValueError(f"Unsupported field for MAS domain entry `{command}`: {field_name}")


def dispatch_domain_entry_request(request: dict[str, Any]) -> dict[str, Any]:
    return MedAutoScienceDomainEntry().dispatch(request)


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
        description="Operate the OPL-managed MAS source carrier through its canonical domain handler."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--probe", action="store_true", help="Probe the canonical domain handler target.")
    mode.add_argument("--healthcheck", action="store_true", help="Run the full source-carrier healthcheck.")
    mode.add_argument(
        "--dispatch-command",
        metavar="COMMAND",
        help="Dispatch one structured request to the canonical MAS domain handler.",
    )
    parser.add_argument(
        "--string-field",
        action="append",
        default=[],
        nargs=2,
        metavar=("NAME", "VALUE"),
        help="Add one string field to a structured dispatch request.",
    )
    parser.add_argument(
        "--list-field",
        action="append",
        default=[],
        nargs=2,
        metavar=("NAME", "VALUE"),
        help="Append one string item to a list field in a structured dispatch request.",
    )
    parser.add_argument(
        "--flag-field",
        action="append",
        default=[],
        metavar="NAME",
        help="Set one boolean request field to true.",
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    request_fields_supplied = bool(args.string_field or args.list_field or args.flag_field)
    if not args.dispatch_command and request_fields_supplied:
        parser.error("request fields require --dispatch-command")

    if args.dispatch_command:
        request = build_domain_entry_request(
            command=args.dispatch_command,
            string_fields=args.string_field,
            list_fields=args.list_field,
            flag_fields=args.flag_field,
        )
        payload = dispatch_domain_entry_request(request)
    elif args.probe:
        payload = build_domain_handler_probe()
    else:
        payload = build_module_healthcheck(args.repo_root)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
