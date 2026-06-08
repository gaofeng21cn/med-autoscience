from __future__ import annotations

from typing import Any


SERIES_ID = "opl_foundry_agent_series.v1"
SERIES_LABEL = "OPL Foundry Agent"
AGENT_ID = "mas"
AGENT_LABEL = "Med Auto Science"
DOMAIN_ID = "medautoscience"
DOMAIN_LABEL = "Medical research"
DOMAIN_ALIASES = ("med-autoscience", "mas", "med_auto_science")
FOUNDRY_OPERATIONS = ("status", "inspect", "interfaces", "validate", "doctor", "peers")
FOUNDRY_TOP_LEVEL_ALIASES = ("status", "inspect", "interfaces", "validate")
FOUNDRY_GROUP = "foundry"
COMMAND_SURFACE_SPINE = ("workspace", "work", "stage", "run", "vault", "handoff", "connect")
SERIES_PEERS = ("MAS", "MAG", "RCA", "OMA")

AUTHORITY_BOUNDARY_SUMMARY = (
    "OPL projects refs and interfaces; MAS owns study truth, publication quality, "
    "artifact authority, memory decisions and owner receipts."
)

PUBLIC_HELP_LINES = (
    f"Series: {SERIES_LABEL}",
    f"Agent id: {AGENT_ID}",
    "Ordinary path: study -> stage -> domain owner receipt or typed blocker -> handoff",
    "Executable command surface: medautosci foundry status --json",
    f"Authority boundary: {AUTHORITY_BOUNDARY_SUMMARY}",
)


def grouped_command_aliases() -> dict[tuple[str, str], str]:
    return {
        (FOUNDRY_GROUP, operation): f"foundry-{operation}"
        for operation in FOUNDRY_OPERATIONS
    }


def grouped_command_summaries() -> dict[str, str]:
    return {
        FOUNDRY_GROUP: (
            "OPL Foundry Agent series identity, ordinary spine, interfaces, conformance and peers."
        ),
    }


def normalize_foundry_argv(argv: list[str]) -> list[str]:
    if len(argv) >= 2 and argv[0] == FOUNDRY_GROUP and argv[1] in FOUNDRY_OPERATIONS:
        return [f"foundry-{argv[1]}", *argv[2:]]
    if argv and argv[0] in FOUNDRY_TOP_LEVEL_ALIASES:
        return [f"foundry-{argv[0]}", *argv[1:]]
    return argv


def is_foundry_command(command: str) -> bool:
    return command.startswith("foundry-")


def operation_from_command(command: str) -> str:
    if not is_foundry_command(command):
        raise ValueError(f"Unsupported foundry command: {command}")
    operation = command.removeprefix("foundry-")
    if operation not in FOUNDRY_OPERATIONS:
        raise ValueError(f"Unsupported foundry operation: {operation}")
    return operation


def build_foundry_command_surface_projection(*, operation: str) -> dict[str, Any]:
    if operation not in FOUNDRY_OPERATIONS:
        raise ValueError(f"Unsupported foundry operation: {operation}")

    payload = _base_projection(operation=operation)
    if operation == "interfaces":
        payload["focus"] = {"interfaces": payload["interfaces"]}
    elif operation == "validate":
        payload["focus"] = {"conformance": payload["conformance"]}
    elif operation == "peers":
        payload["focus"] = {"peers": payload["peers"]}
    elif operation == "inspect":
        payload["focus"] = {
            "command_surface_spine": payload["command_surface_spine"],
            "ordinary_golden_path": payload["ordinary_golden_path"],
            "authority_boundary": payload["authority_boundary"],
        }
    elif operation == "doctor":
        payload["focus"] = {
            "status": payload["status"],
            "conformance": payload["conformance"],
            "legacy_implementation_bucket_policy": payload["legacy_implementation_bucket_policy"],
            "forbidden_claims": payload["ordinary_golden_path"]["forbidden_claims"],
        }
    else:
        payload["focus"] = {"status": payload["status"]}
    return payload


def render_foundry_command_surface_text(payload: dict[str, Any]) -> str:
    lines = [
        f"Series: {payload['series_label']}",
        f"Agent id: {payload['agent_id']}",
        f"Agent label: {payload['agent_label']}",
        "Ordinary path: study -> stage -> domain owner receipt or typed blocker -> handoff",
        "Executable command surface: medautosci foundry status --json",
        f"Authority boundary: {AUTHORITY_BOUNDARY_SUMMARY}",
        "",
        "Command surface spine:",
    ]
    for spine_name in payload["command_surface_spine"]:
        interface = payload["interfaces"][spine_name]
        alias = interface.get("domain_alias")
        alias_suffix = f" (domain alias: {alias})" if alias else ""
        lines.append(f"  {spine_name:<10}{interface['command']}{alias_suffix}")
    lines.extend(
        [
            "",
            f"Conformance: {payload['conformance']['status']}",
            "Readiness claims: study=false, paper_quality=false, artifact=false, production=false",
        ]
    )
    if payload["operation"] == "peers":
        lines.extend(["", "Peers: " + ", ".join(payload["peers"])])
    return "\n".join(lines) + "\n"


def _base_projection(*, operation: str) -> dict[str, Any]:
    return {
        "surface_kind": "mas_foundry_agent_series_command_surface_projection",
        "schema_version": "mas-foundry-command-surface.v1",
        "version": "g2",
        "operation": operation,
        "series": SERIES_ID,
        "series_label": SERIES_LABEL,
        "agent_id": AGENT_ID,
        "agent_label": AGENT_LABEL,
        "domain_id": DOMAIN_ID,
        "domain_label": DOMAIN_LABEL,
        "domain_aliases": list(DOMAIN_ALIASES),
        "brand_cli": "mas",
        "direct_domain_cli": "medautosci",
        "direct_cli": "medautosci",
        "compatibility_command_surface": "medautosci foundry",
        "domain_alias": {"work": "study"},
        "ordinary_golden_path": {
            "path_id": "med-autoscience_ordinary_default",
            "path_role": "ordinary_default",
            "path": "study -> stage -> domain owner receipt or typed blocker -> handoff",
            "command_chain": [
                "medautosci foundry status",
                "medautosci foundry inspect",
                "medautosci foundry interfaces",
                "medautosci foundry validate",
                "medautosci foundry doctor",
            ],
            "stage_refs": ["direction_and_route_selection"],
            "readiness_claims": {
                "study_ready": False,
                "paper_quality_ready": False,
                "artifact_ready": False,
                "production_ready": False,
            },
            "forbidden_claims": [
                "descriptor_ready_means_domain_ready",
                "provider_completion_means_publication_ready",
                "generated_surface_ready_means_paper_closed",
                "same_attempt_self_review_closes_quality_gate",
            ],
        },
        "command_surface_spine": list(COMMAND_SURFACE_SPINE),
        "operations": list(FOUNDRY_OPERATIONS),
        "authority_boundary": {
            "summary": AUTHORITY_BOUNDARY_SUMMARY,
            "opl_can_project_workspace_refs": True,
            "opl_can_write_domain_truth": False,
            "opl_can_claim_publication_quality": False,
            "opl_can_authorize_artifact_mutation": False,
            "opl_can_accept_or_reject_memory_body": False,
            "generated_surface_can_claim_study_ready": False,
            "generated_surface_can_claim_quality_ready": False,
            "generated_surface_can_claim_artifact_ready": False,
            "generated_surface_can_claim_production_ready": False,
            "generated_surface_can_create_owner_receipt": False,
            "generated_surface_can_create_typed_blocker": False,
            "mas_owner_receipt_required_for_domain_closeout": True,
        },
        "interfaces": _interfaces(),
        "work_object": {
            "canonical_object": "work",
            "natural_alias": "study",
            "alias_command_pattern": "medautosci study ...",
            "compatibility_alias_command_pattern": "medautosci study ...",
        },
        "peers": list(SERIES_PEERS),
        "status": {
            "state": "available",
            "read_only": True,
            "ordinary_path_default": True,
            "domain_authority_owner": "MedAutoScience",
            "series_contract_owner": "one-person-lab",
        },
        "opl_series_command_surfaces": {
            "aggregate": "opl agents foundry",
            "agent": "opl foundry agents inspect mas",
            "connect_skills": "opl connect skills --domain medautoscience",
            "connect_sync": "opl connect sync-skills --domain medautoscience",
        },
        "mcp_projection": {
            "descriptor_owner": "one-person-lab",
            "domain_repo_mcp_role": "domain_handler_target_or_direct_protocol_adapter_only",
            "mcp_descriptor_must_delegate_to_series_spine": True,
        },
        "legacy_implementation_bucket_policy": {
            "ordinary_public_command_surface_allowed": False,
            "retained_scope": "diagnostic_or_migration_only",
            "replacement_command_surface": "medautosci foundry",
            "retired_bucket_prefixes": [
                "runtime",
                "index",
                "stage-artifact",
                "private runner",
                "legacy adapter",
            ],
        },
        "conformance": {
            "status": "read_only_series_projection",
            "series_spine_discoverable": True,
            "ordinary_operations": list(FOUNDRY_OPERATIONS),
            "command_surface_spine_complete": True,
            "domain_ready": False,
            "study_ready": False,
            "paper_quality_ready": False,
            "artifact_ready": False,
            "production_ready": False,
            "notes": [
                "This direct CLI command surface only projects OPL Foundry Agent series identity and refs.",
                "MAS owner surfaces continue to decide study truth, quality, artifact and receipt authority.",
            ],
        },
    }


def _interfaces() -> dict[str, dict[str, Any]]:
    return {
        "workspace": {
            "spine_object": "workspace",
            "command": "medautosci workspace",
            "compatibility_command": "medautosci workspace",
            "points_to": [
                "medautosci workspace init",
                "medautosci workspace bootstrap",
                "medautosci workspace study-status",
            ],
            "projection_role": "workspace group and profile readiness projection",
        },
        "work": {
            "spine_object": "work",
            "domain_alias": "study",
            "command": "medautosci study",
            "compatibility_command": "medautosci study",
            "points_to": [
                "medautosci study progress",
                "medautosci study launch",
                "medautosci study submit-task",
            ],
            "projection_role": "domain work unit read model; MAS study truth remains owner-held",
        },
        "stage": {
            "spine_object": "stage",
            "command": "medautosci doctor stage-route-contract",
            "compatibility_command": "medautosci doctor stage-route-contract",
            "points_to": [
                "medautosci doctor stage-route-contract",
                "medautosci stage-artifact-materialize",
                "medautosci stage-knowledge-packet",
            ],
            "projection_role": "stage control-plane and stage artifact refs",
        },
        "run": {
            "spine_object": "run",
            "command": "medautosci runtime",
            "compatibility_command": "medautosci runtime",
            "points_to": [
                "medautosci runtime domain-health-diagnostic",
                "medautosci runtime overlay-status",
                "medautosci runtime maintain-storage",
            ],
            "projection_role": "provider/runtime diagnostics and refs-only supervision",
        },
        "vault": {
            "spine_object": "vault",
            "command": "medautosci data",
            "compatibility_command": "medautosci data",
            "points_to": [
                "medautosci data assets-status",
                "medautosci data memory-status",
                "medautosci publication route-memory-inventory",
            ],
            "projection_role": "source, memory and evidence ref inventory",
        },
        "handoff": {
            "spine_object": "handoff",
            "command": "medautosci domain-handler",
            "compatibility_command": "medautosci domain-handler",
            "points_to": [
                "medautosci domain-handler export",
                "medautosci domain-handler dispatch",
            ],
            "projection_role": "MAS owner receipt, typed blocker and route-back transport boundary",
        },
        "connect": {
            "spine_object": "connect",
            "command": "medautosci domain-handler",
            "compatibility_command": "medautosci domain-handler",
            "points_to": [
                "medautosci domain-handler export",
                "medautosci domain-handler dispatch",
                "plugins/mas/bin/medautosci-mcp",
            ],
            "projection_role": "CLI, MCP and skill connector discovery",
        },
    }
