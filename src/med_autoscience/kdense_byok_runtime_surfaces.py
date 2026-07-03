from __future__ import annotations

from typing import Any, Mapping


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_kdense_byok_runtime_projection_surfaces"
FRAMEWORK_ID = "kdense_byok"
SOURCE_CONTRACT_REF = "contracts/kdense_byok_external_intake.json"

KDENSE_SOURCE_PIN = {
    "repo": "https://github.com/K-Dense-AI/k-dense-byok",
    "inspected_head_commit": "dccc7ec4d034a00d7662eaabb3f5916bc3d00602",
    "latest_release_tag": "v0.6.0",
    "release_tag_commit": "b5b6b832ad6eaa266ca27924331041435b834bd4",
    "license": "MIT",
}
SCIENTIFIC_AGENT_SKILLS_SOURCE_PIN = {
    "repo": "https://github.com/K-Dense-AI/scientific-agent-skills",
    "inspected_head_commit": "1e024ea8547ada12039edbe8197aaa959d97763f",
    "license": "MIT",
}

SURFACE_DEFINITIONS = (
    {
        "surface_id": "attempt_replay_lab_notebook_export",
        "pattern_id": "session_replay_lab_notebook",
        "contract_kind": "attempt_replay_lab_notebook_export_contract",
        "consumer_owner_surface": "OPL Vault attempt ledger",
        "description": "Attempt replay and lab notebook export projection contract.",
    },
    {
        "surface_id": "cost_ledger_budget_cap",
        "pattern_id": "cost_ledger_budget_cap",
        "contract_kind": "cost_ledger_budget_cap_contract",
        "consumer_owner_surface": "OPL Vault / Console budget receipt",
        "description": "Cost ledger and budget cap projection contract.",
    },
    {
        "surface_id": "mcp_connector_doctor_test",
        "pattern_id": "mcp_connector_test_surface",
        "contract_kind": "mcp_connector_doctor_test_contract",
        "consumer_owner_surface": "OPL Connect connector trust and health",
        "description": "MCP connector doctor/test projection contract.",
    },
    {
        "surface_id": "remote_compute_execution_receipt",
        "pattern_id": "remote_compute_adapter",
        "contract_kind": "remote_compute_execution_receipt_contract",
        "consumer_owner_surface": "OPL Runway remote execution receipt",
        "description": "Remote compute execution receipt projection contract.",
    },
    {
        "surface_id": "human_gate_form_schema",
        "pattern_id": "human_gate_form_schema",
        "contract_kind": "human_gate_form_schema_contract",
        "consumer_owner_surface": "MAS human gate / OPL Console schema candidate",
        "description": "Human-gate form schema projection contract.",
    },
    {
        "surface_id": "console_workbench_activity_selector_timeline",
        "pattern_id": "workbench_ux_selector_tool_activity",
        "contract_kind": "console_workbench_activity_selector_timeline_contract",
        "consumer_owner_surface": "OPL Console operator workbench display",
        "description": "Console/workbench activity selector and timeline projection contract.",
    },
    {
        "surface_id": "openrouter_fusion_watch_only_briefing",
        "pattern_id": "openrouter_fusion_watch_only",
        "contract_kind": "openrouter_fusion_watch_only_briefing_contract",
        "consumer_owner_surface": "Reviewer briefing only",
        "description": "OpenRouter Fusion watch-only briefing projection contract.",
        "classification": "watch_only",
        "watch_only": True,
    },
)


def build_kdense_byok_runtime_surfaces(
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    context = _dispatch_context(dispatch)
    surfaces = [
        _surface(definition, context["candidate_dispatch_id"])
        for definition in SURFACE_DEFINITIONS
    ]
    surfaces_by_id = {surface["surface_id"]: surface for surface in surfaces}

    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "projection_emitted",
        "framework_id": FRAMEWORK_ID,
        "source_contract_ref": SOURCE_CONTRACT_REF,
        "source_pins": {
            "kdense_byok": dict(KDENSE_SOURCE_PIN),
            "scientific_agent_skills": dict(SCIENTIFIC_AGENT_SKILLS_SOURCE_PIN),
        },
        "source_evidence_refs": [
            f"{SOURCE_CONTRACT_REF}#/source_evidence/kdense_byok",
            f"{SOURCE_CONTRACT_REF}#/source_evidence/scientific_agent_skills",
        ],
        "refs_only": True,
        "advisory_only": True,
        "nonblocking": True,
        "fail_open": True,
        "failure_policy": "fail_open_projection_only",
        "mainline_waits_for_projection": False,
        "current_owner_action": context["current_owner_action"],
        "diagnostic": context["diagnostic"],
        "allowed_writes": [],
        "written_refs": [],
        "writes_mas_truth": False,
        "writes_runtime": False,
        "can_claim_publication_ready": False,
        "can_claim_paper_progress": False,
        "runtime_boundary": {
            "kdense_runtime_dependency": False,
            "openrouter_fusion_dependency": False,
            "modal_dependency": False,
            "mcp_server_dependency": False,
            "external_runtime_invocation_allowed": False,
        },
        "authority_boundary": _authority_boundary(),
        "surface_ids": [surface["surface_id"] for surface in surfaces],
        "watch_only_surface_ids": [
            surface["surface_id"] for surface in surfaces if surface["watch_only"]
        ],
        "surfaces": surfaces,
        **surfaces_by_id,
    }


def _surface(definition: Mapping[str, Any], dispatch_id: str) -> dict[str, Any]:
    surface_id = _required_text(definition["surface_id"])
    pattern_id = _required_text(definition["pattern_id"])
    classification = _text(definition.get("classification")) or "adapt"
    watch_only = bool(definition.get("watch_only"))
    return {
        "surface_id": surface_id,
        "pattern_id": pattern_id,
        "contract_kind": _required_text(definition["contract_kind"]),
        "classification": classification,
        "status": "projection_available",
        "source_contract_ref": SOURCE_CONTRACT_REF,
        "source_plan_item_ref": f"{SOURCE_CONTRACT_REF}#/planned_learning_items",
        "source_plan_item_id": pattern_id,
        "source_ref": _projection_ref(dispatch_id, surface_id),
        "consumer_owner_surface": _required_text(definition["consumer_owner_surface"]),
        "description": _required_text(definition["description"]),
        "refs_only": True,
        "advisory_only": True,
        "nonblocking": True,
        "fail_open": True,
        "watch_only": watch_only,
        "mainline_waits_for_surface": False,
        "allowed_writes": [],
        "written_refs": [],
        "writes_mas_truth": False,
        "writes_runtime": False,
        "can_claim_publication_ready": False,
        "can_claim_paper_progress": False,
        "authority_boundary": _authority_boundary(),
        "required_consumer_receipt": {
            "owner_surface_consumption_required": True,
            "projection_itself_is_authority": False,
        },
    }


def _authority_boundary() -> dict[str, Any]:
    return {
        "refs_only": True,
        "advisory_only": True,
        "nonblocking": True,
        "fail_open": True,
        "allowed_writes": [],
        "writes_mas_truth": False,
        "writes_runtime": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_sign_owner_receipt": False,
        "can_create_typed_blocker": False,
        "can_create_human_gate": False,
        "can_claim_publication_ready": False,
        "can_claim_paper_progress": False,
    }


def _dispatch_context(dispatch: Mapping[str, Any] | None) -> dict[str, Any]:
    dispatch_mapping = _mapping(dispatch)
    action_id = _dispatch_text(dispatch_mapping, "action_id")
    return {
        "candidate_dispatch_id": action_id or "unknown_dispatch",
        "current_owner_action": _current_owner_action(dispatch_mapping),
        "diagnostic": (
            {"reason": "missing_or_invalid_dispatch"} if not dispatch_mapping else None
        ),
    }


def _current_owner_action(dispatch: Mapping[str, Any]) -> dict[str, str | None]:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    refs = _mapping(dispatch.get("refs"))
    return {
        "action_type": _dispatch_text(dispatch, "action_type"),
        "action_id": _dispatch_text(dispatch, "action_id"),
        "owner": _text(owner_route.get("owner")) or _dispatch_text(dispatch, "owner"),
        "work_unit_id": _text(owner_route.get("work_unit_id"))
        or _text(owner_route.get("unit_id")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
        "dispatch_path": _text(refs.get("dispatch_path")),
    }


def _projection_ref(dispatch_id: str, surface_id: str) -> str:
    return f"external-learning:{FRAMEWORK_ID}:{dispatch_id}:{surface_id}"


def _dispatch_text(dispatch: Mapping[str, Any], key: str) -> str | None:
    return _text(dispatch.get(key)) or _text(_mapping(dispatch.get("source_action")).get(key))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _required_text(value: object) -> str:
    text = _text(value)
    if text is None:
        raise ValueError("required text value is missing")
    return text


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "FRAMEWORK_ID",
    "SCHEMA_VERSION",
    "SOURCE_CONTRACT_REF",
    "SURFACE_KIND",
    "build_kdense_byok_runtime_surfaces",
]
