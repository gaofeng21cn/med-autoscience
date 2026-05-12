from __future__ import annotations

from copy import deepcopy
from typing import Any

from med_autoscience.agent_entry.modes import load_entry_modes_payload
from med_autoscience.stage_knowledge_contract import STAGE_OBLIGATIONS
from med_autoscience.stage_quality_contract import build_stage_quality_pack_ref_projection

MAIN_STAGE_ROUTE_IDS = (
    "scout",
    "idea",
    "baseline",
    "experiment",
    "analysis-campaign",
    "write",
    "review",
    "finalize",
    "decision",
    "journal-resolution",
)

CANONICAL_ROUTE_CONTRACT_REF = "src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml"

STAGE_KNOWLEDGE_SOURCE_REFS = (
    "stage_knowledge_packet",
    "stage_recall_index",
    "publication_route_memory_pack",
    "src/med_autoscience/stage_knowledge_contract.py",
)
STAGE_CLOSEOUT_SOURCE_REFS = (
    "stage_memory_closeout_packet",
    "memory_write_router_receipt",
    "src/med_autoscience/stage_knowledge_contract.py",
)
QUALITY_SOURCE_REFS = (
    "publication_eval/latest.json",
    "review_ledger",
    "evidence_ledger",
    "controller_decisions/latest.json",
    "src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml#/evidence_review_contract",
)
DELIVERABLE_INDEX_SOURCE_REFS = (
    "stage_knowledge_packet",
    "stage_memory_closeout_packet",
    "memory_write_router_receipt",
    "evidence_ledger",
    "review_ledger",
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "package_freshness_proof",
    "artifact_delta_proof",
)
HUMAN_REVIEW_ALLOWED_STATES = (
    {
        "state": "accept_for_next_stage",
        "label": "can enter next stage",
        "blocks_auto_advance": False,
    },
    {
        "state": "needs_revision",
        "label": "needs revision",
        "blocks_auto_advance": False,
    },
    {
        "state": "route_back",
        "label": "route back",
        "blocks_auto_advance": False,
    },
    {
        "state": "stop_or_pivot",
        "label": "stop or pivot",
        "blocks_auto_advance": False,
    },
    {
        "state": "human_gate_required",
        "label": "human gate required",
        "blocks_auto_advance": True,
    },
)
HUMAN_GATE_BOUNDARY_EXAMPLES = (
    "direction_reset",
    "claim_boundary_expansion",
    "stop_or_reopen_decision",
    "submission_or_external_release",
    "ethics_authorship_or_data_permission",
)
PAPER_ASSET_DELTA_TYPES = (
    "manuscript",
    "table",
    "figure",
    "supplement",
    "reference",
    "response_letter",
    "analysis_record",
    "review_record",
    "package_or_delivery",
    "no_paper_asset_body_delta",
)
CLAIM_IMPACT_STATES = (
    "strengthened",
    "weakened",
    "rewritten",
    "removed",
    "unsupported",
    "newly_blocked",
    "no_claim_change",
)
FRESHNESS_SIGNAL_STATES = (
    {
        "state": "green_current",
        "label": "新鲜一致",
        "review_color": "green",
        "blocks_auto_advance": False,
    },
    {
        "state": "yellow_refresh_recommended",
        "label": "建议刷新",
        "review_color": "yellow",
        "blocks_auto_advance": False,
    },
    {
        "state": "red_stale_or_inconsistent",
        "label": "过期或不一致",
        "review_color": "red",
        "blocks_auto_advance": False,
    },
)
FRESHNESS_EVALUATED_REFS = (
    "evidence_ledger",
    "review_ledger",
    "manuscript_or_package_ref",
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
)
ALLOWED_OWNER_TOOLS = (
    "MAS controller-authorized CLI/MCP/product-entry/runtime surfaces",
    "stage-knowledge-packet",
    "stage-memory-closeout-route",
    "runtime-supervisor-reconcile",
    "ai-reviewer-publication-eval",
    "publication-gate",
)


def build_stage_surface_contract(payload: dict[str, object] | None = None) -> dict[str, object]:
    entry_payload = deepcopy(payload) if payload is not None else load_entry_modes_payload()
    route_contracts = _route_contracts(entry_payload)
    _validate_main_routes(route_contracts)

    cards = [_build_stage_card(route_contracts[route_id]) for route_id in MAIN_STAGE_ROUTE_IDS]
    return {
        "surface_kind": "mas_stage_surface_contract",
        "version": "mas-stage-surface-contract.v1",
        "machine_boundary": {
            "canonical_route_contract": CANONICAL_ROUTE_CONTRACT_REF,
            "markdown_is_truth": False,
            "markdown_role": "generated_human_reading_surface",
            "machine_truth_owners": [
                "canonical route contract",
                "stage knowledge plane contracts",
                "MAS controller/runtime surfaces",
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "evidence/review ledgers",
                "workspace artifact locator refs",
            ],
        },
        "authority_boundary": {
            "opl_allowed": ["projection", "dispatch", "read_refs"],
            "opl_forbidden": [
                "domain_truth",
                "quality_verdict",
                "artifact_authority",
                "memory_writeback_acceptance",
            ],
            "mas_authority": [
                "domain_truth",
                "quality_verdict",
                "artifact_authority",
                "runtime_owner",
            ],
        },
        "human_review_policy": _human_review_policy(),
        "stage_deliverable_index": _stage_deliverable_index_summary(cards),
        "stage_cards": cards,
        "validation": {
            "main_stage_route_ids": list(MAIN_STAGE_ROUTE_IDS),
            "route_contract_count": len(route_contracts),
            "stage_card_count": len(cards),
            "source_ref_integrity": "route ids validated against canonical payload",
        },
    }


def render_stage_surfaces_markdown(surface: dict[str, object] | None = None) -> str:
    contract = surface if surface is not None else build_stage_surface_contract()
    machine_boundary = _mapping(contract["machine_boundary"], "machine_boundary")
    authority_boundary = _mapping(contract["authority_boundary"], "authority_boundary")
    cards = _list_of_mappings(contract["stage_cards"], "stage_cards")

    lines: list[str] = [
        "# MAS Stage Surfaces",
        "",
        f"Canonical route source: `{machine_boundary['canonical_route_contract']}`.",
        "Markdown is a generated human-reading surface; it is not machine truth.",
        "OPL may only project, dispatch, and read refs.",
        "MAS keeps domain truth, quality verdict, runtime owner, and artifact authority.",
        "",
        "## Machine Boundary",
        _render_list_line("Machine truth owners", machine_boundary["machine_truth_owners"]),
        _render_list_line("OPL allowed", authority_boundary["opl_allowed"]),
        _render_list_line("OPL forbidden", authority_boundary["opl_forbidden"]),
        _render_list_line("MAS authority", authority_boundary["mas_authority"]),
        "",
        "## Stage Cards",
    ]

    for card in cards:
        lines.extend(_render_stage_card(card))

    return "\n".join(lines).rstrip() + "\n"


def render_stage_skill_surface_block(stage_id: str) -> str:
    normalized_stage_id = str(stage_id).strip()
    route_contracts = _route_contracts(load_entry_modes_payload())
    _validate_main_routes(route_contracts)
    if normalized_stage_id not in MAIN_STAGE_ROUTE_IDS:
        raise ValueError(f"unsupported main stage id: {normalized_stage_id}")
    if normalized_stage_id not in STAGE_OBLIGATIONS:
        raise ValueError(f"stage obligations missing for main stage id: {normalized_stage_id}")

    card = _build_stage_card(route_contracts[normalized_stage_id])
    machine_source_refs = _mapping(card["machine_source_refs"], "machine_source_refs")
    knowledge = _mapping(card["knowledge"], "knowledge")
    tools = _mapping(card["tools"], "tools")
    quality = _mapping(card["quality"], "quality")
    closeout = _mapping(card["closeout"], "closeout")
    opl_boundary = _mapping(card["opl_boundary"], "opl_boundary")
    quality_pack_projection = build_stage_quality_pack_ref_projection([normalized_stage_id])
    stage_obligations = STAGE_OBLIGATIONS[normalized_stage_id]
    knowledge_obligations = list(stage_obligations.get("knowledge_input_obligations", ()))
    closeout_obligations = list(stage_obligations.get("memory_closeout_obligations", ()))

    lines = [
        "## MAS stage surface",
        "",
        f"- Stage: `{card['route_id']}` / {card['display_name']}",
        f"- Key question: {card['key_question']}",
        f"- Stage card ref: `docs/runtime/contracts/stage_surfaces.md#{card['route_id']}`",
        f"- Route contract ref: `{machine_source_refs['route_contract']}`",
        "- Machine truth: canonical route contract, stage knowledge contract, stage quality contract, MAS controller/runtime surfaces, publication gate, evidence/review ledgers, and controller decisions.",
        "- Markdown/Skill role: generated human-readable operating surface only; it is not machine truth.",
        "",
        "### Route contract",
        _render_list_line("Purpose", [card["purpose"]]),
        _render_list_line("Entry", card["entry"]),
        _render_list_line("Durable outputs", card["outputs"]),
        _render_list_line("Route success gate", quality["route_success_gate"]),
        _render_list_line("Route back", card["route_back"]),
        _render_list_line("Human gate", card["human_gate"]),
        _render_list_line("Next routes", card["next_routes"]),
        "",
        "### Knowledge obligations",
        _render_list_line("Machine source refs", knowledge["machine_source_refs"]),
        _render_list_line("Canonical obligations", knowledge_obligations),
        _render_list_line("Stage card status", [knowledge["status"]]),
        "",
        "### Quality pack refs",
        _render_list_line("Pack refs", quality_pack_projection["pack_refs"]),
        f"- Contract ref: `{quality_pack_projection['contract_ref']}`",
        f"- Freshness ref: `{quality_pack_projection['freshness_ref']}`",
        f"- Locator ref: `{quality_pack_projection['locator_ref']}`",
        f"- Authority boundary ref: `{quality_pack_projection['authority_boundary_ref']}`",
        f"- OPL projection boundary: `{quality_pack_projection['opl_projection_boundary']}`",
        "- Publication readiness authority: `false`",
        "- Quality verdict authority: `false`",
        "",
        "### Closeout obligations",
        _render_list_line("Machine source refs", closeout["machine_source_refs"]),
        _render_list_line("Canonical obligations", closeout_obligations),
        _render_list_line("Stage card status", [closeout["status"]]),
        "",
        "### Allowed MAS owner tools",
        _render_list_line("Allowed", tools["allowed"]),
        f"- Boundary: `{tools['boundary']}`",
        "",
        "### Forbidden actions",
        "- Do not write MAS domain truth outside controller-authorized surfaces.",
        "- Do not authorize quality verdicts, publication readiness, or submission readiness from this Skill text.",
        "- Do not accept memory writeback without `memory_write_router_receipt`.",
        "- Do not treat OPL/provider completion as paper closure.",
        "",
        "### OPL/provider boundary",
        _render_list_line("May", opl_boundary["may"]),
        _render_list_line("Must not", opl_boundary["must_not"]),
        "- Provider/OPL projections may expose locators, freshness, and refs only; MAS keeps domain truth, quality verdict, runtime owner, and artifact authority.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _build_stage_card(route_payload: dict[str, Any]) -> dict[str, object]:
    route_id = _string(route_payload["route_id"], "route_id")
    knowledge_obligations = _optional_string_list(route_payload, "knowledge_input_obligations")
    closeout_obligations = _optional_string_list(route_payload, "memory_closeout_obligations")
    deliverable_index = _build_deliverable_index(
        route_id=route_id,
        entry=_required_string_list(route_payload, "enter_conditions"),
        outputs=_required_string_list(route_payload, "durable_outputs_minimum"),
        next_routes=_required_string_list(route_payload, "next_routes"),
    )
    return {
        "surface_kind": "mas_stage_card",
        "route_id": route_id,
        "display_name": _string(route_payload["display_name"], "display_name"),
        "machine_source_refs": {
            "route_contract": f"{CANONICAL_ROUTE_CONTRACT_REF}#/route_contracts/{route_id}",
            "knowledge_contract": "src/med_autoscience/stage_knowledge_contract.py",
            "quality_contract": f"{CANONICAL_ROUTE_CONTRACT_REF}#/evidence_review_contract",
        },
        "purpose": _string(route_payload["goal"], "goal"),
        "key_question": _string(route_payload["key_question"], "key_question"),
        "entry": _required_string_list(route_payload, "enter_conditions"),
        "tools": {
            "allowed": list(ALLOWED_OWNER_TOOLS),
            "boundary": "controller_authorized_surfaces_only",
        },
        "knowledge": {
            "obligations": knowledge_obligations,
            "status": _obligation_status(knowledge_obligations),
            "machine_source_refs": list(STAGE_KNOWLEDGE_SOURCE_REFS),
        },
        "outputs": _required_string_list(route_payload, "durable_outputs_minimum"),
        "deliverable_index": deliverable_index,
        "human_review_page": _build_human_review_page(route_payload, deliverable_index=deliverable_index),
        "quality": {
            "route_success_gate": _required_string_list(route_payload, "hard_success_gate"),
            "verdict_owner": "MedAutoScience",
            "machine_source_refs": list(QUALITY_SOURCE_REFS),
        },
        "closeout": {
            "obligations": closeout_obligations,
            "status": _obligation_status(closeout_obligations),
            "machine_source_refs": list(STAGE_CLOSEOUT_SOURCE_REFS),
        },
        "route_back": _required_string_list(route_payload, "route_back_triggers"),
        "human_gate": _required_string_list(route_payload, "human_gate_boundary"),
        "next_routes": _required_string_list(route_payload, "next_routes"),
        "opl_boundary": {
            "may": ["project", "dispatch", "read source refs"],
            "must_not": [
                "write MAS domain truth",
                "authorize quality verdicts",
                "own canonical artifacts",
                "accept memory writeback",
            ],
        },
    }


def _render_stage_card(card: dict[str, Any]) -> list[str]:
    machine_source_refs = _mapping(card["machine_source_refs"], "machine_source_refs")
    knowledge = _mapping(card["knowledge"], "knowledge")
    tools = _mapping(card["tools"], "tools")
    quality = _mapping(card["quality"], "quality")
    closeout = _mapping(card["closeout"], "closeout")
    deliverable_index = _mapping(card["deliverable_index"], "deliverable_index")
    human_review_page = _mapping(card["human_review_page"], "human_review_page")
    opl_boundary = _mapping(card["opl_boundary"], "opl_boundary")

    lines = [
        "",
        f"## {card['route_id']}",
        "",
        f"- Display name: {card['display_name']}",
        f"- Machine source: `{machine_source_refs['route_contract']}`",
        f"- Key question: {card['key_question']}",
        "",
        "### Purpose",
        _render_list_block([card["purpose"]]),
        "",
        "### Entry",
        _render_list_block(card["entry"]),
        "",
        "### Allowed Tools",
        _render_list_block(tools["allowed"]),
        f"- Boundary: `{tools['boundary']}`",
        "",
        "### Knowledge",
        _render_list_line("Status", [knowledge["status"]]),
        _render_list_line("Machine source refs", knowledge["machine_source_refs"]),
        _render_list_line("Obligations", knowledge["obligations"]),
        "",
        "### Outputs",
        _render_list_block(card["outputs"]),
        "",
        "### Quality",
        _render_list_line("Verdict owner", [quality["verdict_owner"]]),
        _render_list_line("Machine source refs", quality["machine_source_refs"]),
        _render_list_line("Route success gate", quality["route_success_gate"]),
        "",
        "### Closeout",
        _render_list_line("Status", [closeout["status"]]),
        _render_list_line("Machine source refs", closeout["machine_source_refs"]),
        _render_list_line("Obligations", closeout["obligations"]),
        "",
        "### Deliverable Index",
        _render_ref_list_line("Input refs", deliverable_index["input_refs"]),
        _render_ref_list_line("Output refs", deliverable_index["output_refs"]),
        _render_ref_list_line("Ledger refs", deliverable_index["ledger_refs"]),
        _render_mapping_line("Quality gate ref", deliverable_index["quality_gate_ref"]),
        _render_mapping_line("Package/artifact delta ref", deliverable_index["package_artifact_delta_ref"]),
        _render_mapping_line("Next owner", deliverable_index["next_owner"]),
        "",
        "### One-Page Paper Review",
        _render_review_sections(human_review_page["sections"]),
        "",
        "### Route Back / Human Gate",
        _render_list_line("Route back", card["route_back"]),
        _render_list_line("Human gate", card["human_gate"]),
        _render_list_line("Next routes", card["next_routes"]),
        "",
        "### OPL Boundary",
        _render_list_line("May", opl_boundary["may"]),
        _render_list_line("Must not", opl_boundary["must_not"]),
    ]
    return lines


def _stage_deliverable_index_summary(cards: list[dict[str, object]]) -> dict[str, object]:
    return {
        "surface_kind": "mas_stage_deliverable_index",
        "version": "mas-stage-deliverable-index.v1",
        "role": "human_audit_and_opl_locator",
        "stage_count": len(cards),
        "stage_refs": [f"/stage_cards/{_string(card['route_id'], 'route_id')}/deliverable_index" for card in cards],
        "human_review_page_refs": [
            f"/stage_cards/{_string(card['route_id'], 'route_id')}/human_review_page" for card in cards
        ],
        "source_refs": list(DELIVERABLE_INDEX_SOURCE_REFS),
        "human_review_policy": _human_review_policy(),
        "review_page_policy": _review_page_policy(),
        "authority_boundary": _deliverable_authority_boundary(),
    }


def _build_deliverable_index(
    *,
    route_id: str,
    entry: list[str],
    outputs: list[str],
    next_routes: list[str],
) -> dict[str, object]:
    return {
        "surface_kind": "mas_stage_deliverable_index_entry",
        "stage": route_id,
        "role": "human_audit_and_opl_locator",
        "input_refs": [
            _ref("workspace_artifact", f"artifacts/stage_knowledge/{route_id}/latest.json", "stage_knowledge_packet"),
            _ref("workspace_artifact", "artifacts/controller/study_charter.json", "active_study_charter"),
            _ref("route_contract_field", "enter_conditions", "stage_entry_conditions", values=entry),
        ],
        "output_refs": [
            _ref("route_contract_field", "durable_outputs_minimum", "durable_outputs_minimum", values=outputs),
            _ref(
                "workspace_artifact",
                f"artifacts/stage_knowledge/{route_id}/closeouts",
                "stage_memory_closeout_packet",
            ),
            _ref(
                "workspace_artifact",
                "artifacts/stage_knowledge/memory_write_router_receipts",
                "memory_write_router_receipt",
            ),
        ],
        "ledger_refs": [
            _ref("durable_surface", "evidence_ledger", "evidence_ledger"),
            _ref("durable_surface", "review_ledger", "review_ledger"),
            _ref("durable_surface", "controller_decisions/latest.json", "controller_decision"),
        ],
        "quality_gate_ref": {
            "ref_kind": "durable_surface",
            "ref": "publication_eval/latest.json",
            "role": "ai_reviewer_or_publication_gate_projection",
            "owner": "MedAutoScience",
            "publication_readiness_authority": False,
        },
        "package_artifact_delta_ref": {
            "ref_kind": "durable_surface",
            "ref": "package_freshness_proof_or_artifact_delta_proof",
            "role": "paper_asset_delta_evidence",
            "owner": "MedAutoScience",
            "body_included": False,
        },
        "next_owner": {
            "owner": "MedAutoScience",
            "next_routes": list(next_routes),
            "source_ref": "route_contract.next_routes",
        },
        "human_review_page_ref": f"/stage_cards/{route_id}/human_review_page",
        "human_review_policy_ref": "/human_review_policy",
        "review_page_policy_ref": "/stage_deliverable_index/review_page_policy",
        "authority_boundary": _deliverable_authority_boundary(),
    }


def _build_human_review_page(
    route_payload: dict[str, Any],
    *,
    deliverable_index: dict[str, object],
) -> dict[str, object]:
    route_id = _string(route_payload["route_id"], "route_id")
    return {
        "surface_kind": "mas_stage_human_review_page",
        "stage": route_id,
        "role": "one_page_paper_audit_surface",
        "display_name": _string(route_payload["display_name"], "display_name"),
        "paper_question": _string(route_payload["key_question"], "key_question"),
        "deliverable_index_ref": f"/stage_cards/{route_id}/deliverable_index",
        "review_annotation_policy": _human_review_policy(
            human_gate_boundary=_required_string_list(route_payload, "human_gate_boundary")
        ),
        "paper_asset_delta_policy": _paper_asset_delta_policy(),
        "claim_trace_policy": _claim_trace_policy(),
        "freshness_signal_policy": _freshness_signal_policy(),
        "sections": [
            _review_section("paper_question", "本阶段要回答的论文问题", [_string(route_payload["key_question"], "key_question")]),
            _review_section("stage_inputs", "本阶段输入", _required_string_list(route_payload, "enter_conditions")),
            _review_section("work_completed", "本阶段完成的工作", [_string(route_payload["goal"], "goal")]),
            _review_section(
                "manuscript_or_artifact_delta",
                "论文资产变化",
                _required_string_list(route_payload, "durable_outputs_minimum"),
            ),
            _review_section(
                "claim_trace",
                "跨阶段 claim 影响",
                list(CLAIM_IMPACT_STATES),
            ),
            _review_section(
                "evidence_and_citation_basis",
                "证据与引用依据",
                _optional_string_list(route_payload, "knowledge_input_obligations"),
            ),
            _review_section("quality_judgment", "质量判断", _required_string_list(route_payload, "hard_success_gate")),
            _review_section(
                "freshness_signal",
                "stale / freshness 红黄绿",
                [str(item["state"]) for item in FRESHNESS_SIGNAL_STATES],
            ),
            _review_section("advance_decision", "是否进入下一阶段", _required_string_list(route_payload, "next_routes")),
            _review_section(
                "route_back_or_human_gate",
                "退回原因或人工决策点",
                [
                    *_required_string_list(route_payload, "route_back_triggers"),
                    *_required_string_list(route_payload, "human_gate_boundary"),
                ],
            ),
        ],
        "authority_boundary": {
            "can_authorize_quality_verdict": False,
            "can_authorize_submission_readiness": False,
            "can_mark_publication_ready": False,
            "can_override_auto_advance": False,
            "can_write_domain_truth": False,
            "truth_owner": "MedAutoScience",
        },
    }


def _review_section(section_id: str, title: str, source_items: list[str]) -> dict[str, object]:
    return {
        "section_id": section_id,
        "title": title,
        "source_items": source_items,
        "human_judgment": "optional_annotation",
        "blocks_auto_advance": False,
    }


def _human_review_policy(*, human_gate_boundary: list[str] | None = None) -> dict[str, object]:
    return {
        "mode": "optional_human_review_annotation",
        "default_blocks_auto_advance": False,
        "allowed_states": list(HUMAN_REVIEW_ALLOWED_STATES),
        "blocking_state": "human_gate_required",
        "blocking_only_when": "route_contract.human_gate_boundary_triggered",
        "human_gate_boundary": list(human_gate_boundary or []),
        "human_gate_boundary_examples": list(HUMAN_GATE_BOUNDARY_EXAMPLES),
        "annotation_can_authorize_quality_verdict": False,
        "annotation_can_authorize_submission_readiness": False,
        "annotation_can_mark_publication_ready": False,
        "auto_advance_owner": "MedAutoScience controller/runtime owner surfaces",
    }


def _review_page_policy() -> dict[str, object]:
    return {
        "paper_asset_delta_policy": _paper_asset_delta_policy(),
        "claim_trace_policy": _claim_trace_policy(),
        "freshness_signal_policy": _freshness_signal_policy(),
    }


def _paper_asset_delta_policy() -> dict[str, object]:
    return {
        "allowed_delta_types": list(PAPER_ASSET_DELTA_TYPES),
        "body_included": False,
        "required_ref_roles": [
            "artifact_delta_proof",
            "package_freshness_proof",
            "owner_receipt",
        ],
        "delta_types_are_human_review_projection": True,
        "can_authorize_artifact_authority": False,
    }


def _claim_trace_policy() -> dict[str, object]:
    return {
        "allowed_impact_states": list(CLAIM_IMPACT_STATES),
        "requires_claim_refs": True,
        "cross_stage_trace": True,
        "supports_quality_review_only": True,
        "can_authorize_quality_verdict": False,
    }


def _freshness_signal_policy() -> dict[str, object]:
    return {
        "status_kind": "traffic_light",
        "allowed_states": list(FRESHNESS_SIGNAL_STATES),
        "evaluated_refs": list(FRESHNESS_EVALUATED_REFS),
        "stale_or_inconsistent_means_refresh_required_for_human_review": True,
        "freshness_signal_can_authorize_submission_readiness": False,
        "freshness_signal_blocks_auto_advance_by_default": False,
    }


def _deliverable_authority_boundary() -> dict[str, object]:
    return {
        "truth_owner": "MedAutoScience",
        "role": "locator_and_human_audit_projection",
        "can_write_mas_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "human_review_blocks_auto_advance_by_default": False,
        "body_included": False,
    }


def _ref(ref_kind: str, ref: str, role: str, *, values: list[str] | None = None) -> dict[str, object]:
    payload: dict[str, object] = {"ref_kind": ref_kind, "ref": ref, "role": role}
    if values is not None:
        payload["values"] = list(values)
    return payload


def _route_contracts(payload: dict[str, object]) -> dict[str, dict[str, Any]]:
    value = payload.get("route_contracts")
    if not isinstance(value, dict):
        raise ValueError("route_contracts must be a mapping")
    return {
        str(route_id): _mapping(route_payload, f"route_contracts[{route_id}]")
        for route_id, route_payload in value.items()
    }


def _validate_main_routes(route_contracts: dict[str, dict[str, Any]]) -> None:
    missing = [route_id for route_id in MAIN_STAGE_ROUTE_IDS if route_id not in route_contracts]
    if missing:
        raise ValueError(f"missing main stage route contracts: {', '.join(missing)}")


def _obligation_status(obligations: list[str]) -> str:
    if obligations:
        return "declared_in_canonical_route_contract"
    return "not_declared_in_canonical_route_contract"


def _mapping(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a mapping")
    return value


def _string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _required_string_list(payload: dict[str, Any], field: str) -> list[str]:
    if field not in payload:
        raise ValueError(f"{field} missing")
    return _string_list(payload[field], field)


def _optional_string_list(payload: dict[str, Any], field: str) -> list[str]:
    if field not in payload:
        return []
    return _string_list(payload[field], field)


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must contain only strings")
    return list(value)


def _list_of_mappings(value: object, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return [_mapping(item, f"{field}[]") for item in value]


def _render_list_block(values: object) -> str:
    items = _string_list(values, "values") if isinstance(values, list) else [_string(values, "value")]
    if not items:
        return "- (none)"
    return "\n".join(f"- {item}" for item in items)


def _render_list_line(label: str, values: object) -> str:
    items = _string_list(values, label) if isinstance(values, list) else [_string(values, label)]
    rendered = " | ".join(items) if items else "(none)"
    return f"- {label}: {rendered}"


def _render_ref_list_line(label: str, refs: object) -> str:
    items = _list_of_mappings(refs, label)
    rendered_refs = [f"{item.get('role')} -> {item.get('ref')}" for item in items]
    return _render_list_line(label, rendered_refs)


def _render_mapping_line(label: str, value: object) -> str:
    mapping = _mapping(value, label)
    rendered = ", ".join(f"{key}={mapping[key]}" for key in sorted(mapping))
    return f"- {label}: {rendered}"


def _render_review_sections(sections: object) -> str:
    items = _list_of_mappings(sections, "sections")
    rendered = [f"{item.get('section_id')}: {item.get('title')}" for item in items]
    return _render_list_block(rendered)
