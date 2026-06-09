from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.stage_route_contract import STAGE_ROUTE_CONTRACT_REF, load_stage_route_contract_payload

PROJECTED_ROUTE_FIELD_OVERRIDES: dict[tuple[str, str], tuple[str, ...]] = {
    (
        "write",
        "enter_conditions",
    ): (
        "active claim and supporting evidence package are readable",
        "required route artifacts are linked or referenced",
        "reviewer-first pressure can be applied against the current draft",
        "user manuscript-change requests from Codex have been converted into a study revision intake with OPL runtime control boundary checked",
    ),
    (
        "write",
        "durable_outputs_minimum",
    ): (
        "manuscript draft or section update tied to current claim scope",
        "claim-evidence map or equivalent traceability surface",
        "reviewer-first pass note with explicit concerns",
        "first-draft quality note covering field-verified multicenter/geography, subgroup/association, guideline, and real-world constraint axes",
        "revision handoff stating data source, scripts, changed tables/figures, claim guardrails, OPL provider attempt hydration/resume refs, and whether `current_package` was regenerated from controller-authorized `paper/`",
    ),
    (
        "write",
        "route_back_triggers",
    ): (
        "any active claim lacks supporting evidence",
        "reviewer-first scan finds unresolved logic, novelty, or rigor gaps",
        "first-draft quality scan finds verified asset dimensions that can support a stronger bounded analysis or manuscript framing",
        "manuscript narrative changes the claim boundary",
        "foreground edits only touched `manuscript/current_package/` before OPL provider attempt hydration/resume and MAS owner authorization, or have not been reconciled into the canonical paper source",
    ),
}


def render_stage_route_contract_payload() -> dict[str, object]:
    return _project_stage_route_payload(load_stage_route_contract_payload())


def render_stage_route_contract_guide() -> str:
    payload = render_stage_route_contract_payload()
    compatible_agents = _string_list(payload.get("compatible_agents"), field="compatible_agents")
    modes = _mode_payload_list(payload)
    route_contracts = _route_contract_payload_map(payload)
    ordinary_progress_handoff = _mapping(
        payload.get("ordinary_progress_handoff_policy"),
        "ordinary_progress_handoff_policy",
    )
    evidence_review_contract = _evidence_review_contract_payload(payload)
    sprint_contract = _mapping(payload.get("late_stage_progress_sprint_contract"), "late_stage_progress_sprint_contract")
    runtime_modes = sorted({mode["default_runtime_mode"] for mode in modes})

    lines: list[str] = [
        "# MAS Stage Route Contract",
        "",
        "Owner: `MedAutoScience`",
        "Purpose: `Explain MAS runtime contract and stage-surface boundaries for human maintainers.`",
        "State: `active_runtime_support`",
        "Machine boundary: Human-readable runtime contract support only; enforceable runtime truth remains in "
        "machine-readable contracts, source, tests, CLI/read-model output, runtime ledgers, and owner receipts.",
        "",
        f"Canonical source: `{STAGE_ROUTE_CONTRACT_REF}`.",
        "",
        "## Compatible Agents",
        f"- {', '.join(compatible_agents)}",
        "",
        "## Runtime Modes",
        f"- {', '.join(runtime_modes)}",
        "",
        "## Mode Contract",
    ]
    for mode in modes:
        lines.extend(
            (
                "",
                f"### {mode['mode_id']} ({mode['display_name']})",
                f"- default_runtime_mode: {mode['default_runtime_mode']}",
                f"- lightweight_scope: {mode['lightweight_scope']}",
                _render_list_line("preconditions", mode["preconditions"]),
                _render_list_line("managed_entry_actions", mode["managed_entry_actions"]),
                _render_list_line("lightweight_routes", mode["lightweight_routes"]),
                _render_list_line("managed_routes", mode["managed_routes"]),
                _render_list_line("startup_boundary_gated_routes", mode["startup_boundary_gated_routes"]),
                _render_list_line("governance_routes", mode["governance_routes"]),
                _render_list_line("auxiliary_routes", mode["auxiliary_routes"]),
                _render_list_line("upgrade_triggers", mode["upgrade_triggers"]),
            )
        )

    lines.extend(
        (
            "",
            "## Route Contracts",
        )
    )
    for route_contract in route_contracts:
        lines.extend(
            (
                "",
                f"### {route_contract['route_id']} ({route_contract['display_name']})",
                f"- key_question: {route_contract['key_question']}",
                f"- goal: {route_contract['goal']}",
                _render_list_line("enter_conditions", route_contract["enter_conditions"]),
                _render_list_line("hard_success_gate", route_contract["hard_success_gate"]),
                _render_list_line("durable_outputs_minimum", route_contract["durable_outputs_minimum"]),
                _render_list_line("human_gate_boundary", route_contract["human_gate_boundary"]),
                _render_list_line("next_routes", route_contract["next_routes"]),
                _render_list_line("route_back_triggers", route_contract["route_back_triggers"]),
                _render_optional_list_line("knowledge_input_obligations", route_contract),
                _render_optional_list_line("memory_closeout_obligations", route_contract),
            )
        )

    lines.extend(_render_ordinary_progress_handoff_policy(ordinary_progress_handoff))
    lines.extend(_render_late_stage_progress_sprint_contract(sprint_contract))

    lines.extend(
        (
            "",
            "## Evidence And Review Contract",
            _render_list_line("minimum_proof_package", evidence_review_contract["minimum_proof_package"]),
            _render_list_line("reviewer_first_checks", evidence_review_contract["reviewer_first_checks"]),
            _render_list_line(
                "claim_evidence_consistency_requirements",
                evidence_review_contract["claim_evidence_consistency_requirements"],
            ),
            _render_list_line("route_back_policy", evidence_review_contract["route_back_policy"]),
        )
    )
    lines.extend(_render_medical_handoff_evidence_gate(evidence_review_contract))
    lines.extend(_render_medical_route_quality_loop(evidence_review_contract))

    lines.extend(
        (
            "",
            "## Upgrade Rules",
            "If `upgrade_triggers` is non-empty and any trigger is satisfied, "
            "upgrade from lightweight to managed before continuing.",
            "",
            "## Startup Boundary Rule",
            "Read MAS domain refs and request OPL provider hydration before any managed compute decision. Do not enter "
            "`startup_boundary_gated_routes` unless the MAS controller projection reports "
            "`startup_boundary_gate.allow_compute_stage = true`; otherwise stay within "
            "`managed_routes`, `governance_routes`, and any writing-only delivery route.",
            "",
            "## OPL Runtime Control Rule",
            "If `execution_owner_guard.supervisor_only = true`, stay in governance / monitoring mode, "
            "notify the user, report `browser_url`, `quest_session_api_url`, and `active_run_id` when present, "
            "and do not write OPL runtime-owned study surfaces.",
            "Treat `bundle_tasks_downstream_only = true` as a hard block on bundle/build/proofing actions.",
            "",
            "## No Ad-hoc Execution Rule",
            "When operating MAS-covered work, agents must use controller-authorized `CLI`, `MCP`, "
            "`product-entry`, or OPL-dispatched MAS domain handler surfaces before writing research outputs or advancing a study route.",
            "If a required capability is not exposed through those MAS contracts, stop and close the contract gap "
            "in the repo-tracked controller/callable surface before continuing; do not bypass MAS with ad-hoc "
            "scripts, direct artifact edits, prompt-only research chains, or generic document/PDF/Office tooling.",
            "",
            "## Revision Intake Rule",
            "Treat reviewer feedback, manuscript revision, mentor feedback, 审稿意见, 导师反馈, 论文修改, "
            "and Introduction/Methods/Results/Figure/Table feedback as `reviewer_revision` study task intake.",
            "Explicit user/reviewer manuscript feedback after a stopped, submission-ready, or finalize milestone "
            "reactivates the same study line; it is not permission to foreground-edit `manuscript/current_package`.",
            "After writing the durable task intake, OPL must hydrate or resume the provider attempt from MAS "
            "owner refs before MAS domain handlers edit canonical paper sources and regenerate `current_package` from that authority.",
        )
    )
    return "\n".join(lines).rstrip() + "\n"

def render_public_yaml() -> str:
    payload = render_stage_route_contract_payload()
    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    return rendered if rendered.endswith("\n") else f"{rendered}\n"


def render_codex_entry_skill() -> str:
    return _render_agent_entry_prompt(
        title="# MedAutoScience Agent Entry (Codex)",
        intro="Use this stage route contract to select entry mode and route actions without changing canonical definitions.",
    )


def render_openclaw_entry_prompt() -> str:
    return _render_agent_entry_prompt(
        title="# MedAutoScience Agent Entry (OpenClaw)",
        intro="Use this prompt contract to choose runtime mode and route transitions from the canonical stage route contract.",
    )


def sync_agent_entry_assets(repo_root: Path) -> dict[str, object]:
    root = repo_root.expanduser().resolve()
    assets: tuple[tuple[Path, str], ...] = (
        (Path("docs/runtime/contracts/stage_route_contract.md"), render_stage_route_contract_guide()),
        (Path("templates/stage_route_contract.yaml"), render_public_yaml()),
        (Path("templates/codex/medautoscience-entry.SKILL.md"), render_codex_entry_skill()),
        (Path("templates/openclaw/medautoscience-entry.prompt.md"), render_openclaw_entry_prompt()),
        (Path("src/med_autoscience/resources/stage_route_contract.yaml"), render_public_yaml()),
    )
    written_files: list[str] = []

    for relative_path, content in assets:
        output_path = root / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        written_files.append(str(output_path))

    return {
        "repo_root": str(root),
        "written_count": len(written_files),
        "written_files": written_files,
    }


def _render_agent_entry_prompt(*, title: str, intro: str) -> str:
    payload = render_stage_route_contract_payload()
    modes = _mode_payload_list(payload)
    route_contracts = _route_contract_payload_map(payload)
    ordinary_progress_handoff = _mapping(
        payload.get("ordinary_progress_handoff_policy"),
        "ordinary_progress_handoff_policy",
    )
    evidence_review_contract = _evidence_review_contract_payload(payload)
    sprint_contract = _mapping(payload.get("late_stage_progress_sprint_contract"), "late_stage_progress_sprint_contract")
    runtime_modes = sorted({mode["default_runtime_mode"] for mode in modes})
    lines: list[str] = [
        title,
        "",
        intro,
        "",
        "Compatible agents: " + ", ".join(_string_list(payload.get("compatible_agents"), field="compatible_agents")),
        "Runtime modes: " + ", ".join(runtime_modes),
        "",
        "## Mode Contract",
    ]
    for mode in modes:
        lines.extend(
            (
                f"- {mode['mode_id']}: runtime={mode['default_runtime_mode']}, scope={mode['lightweight_scope']}",
                "  "
                + _render_list_line("preconditions", mode["preconditions"], inline=True),
                "  "
                + _render_list_line("managed_entry_actions", mode["managed_entry_actions"], inline=True),
                "  "
                + _render_list_line("lightweight_routes", mode["lightweight_routes"], inline=True),
                "  "
                + _render_list_line("managed_routes", mode["managed_routes"], inline=True),
                "  "
                + _render_list_line(
                    "startup_boundary_gated_routes",
                    mode["startup_boundary_gated_routes"],
                    inline=True,
                ),
                "  "
                + _render_list_line("governance_routes", mode["governance_routes"], inline=True),
                "  "
                + _render_list_line("auxiliary_routes", mode["auxiliary_routes"], inline=True),
                "  "
                + _render_list_line("upgrade_triggers", mode["upgrade_triggers"], inline=True),
            )
        )

    lines.extend(
        (
            "",
            "## Route Contracts",
        )
    )
    for route_contract in route_contracts:
        lines.extend(
            (
                f"- {route_contract['route_id']}: {route_contract['display_name']}",
                "  key_question: " + route_contract["key_question"],
                "  goal: " + route_contract["goal"],
                "  " + _render_list_line("enter_conditions", route_contract["enter_conditions"], inline=True),
                "  " + _render_list_line("hard_success_gate", route_contract["hard_success_gate"], inline=True),
                "  "
                + _render_list_line(
                    "durable_outputs_minimum",
                    route_contract["durable_outputs_minimum"],
                    inline=True,
                ),
                "  "
                + _render_list_line(
                    "human_gate_boundary",
                    route_contract["human_gate_boundary"],
                    inline=True,
                ),
                "  " + _render_list_line("next_routes", route_contract["next_routes"], inline=True),
                "  "
                + _render_list_line("route_back_triggers", route_contract["route_back_triggers"], inline=True),
                "  " + _render_optional_list_line("knowledge_input_obligations", route_contract, inline=True),
                "  " + _render_optional_list_line("memory_closeout_obligations", route_contract, inline=True),
            )
        )

    lines.extend(_render_ordinary_progress_handoff_policy(ordinary_progress_handoff))
    lines.extend(_render_late_stage_progress_sprint_contract(sprint_contract))

    lines.extend(
        (
            "",
            "## Evidence And Review Contract",
            _render_list_line("minimum_proof_package", evidence_review_contract["minimum_proof_package"]),
            _render_list_line("reviewer_first_checks", evidence_review_contract["reviewer_first_checks"]),
            _render_list_line(
                "claim_evidence_consistency_requirements",
                evidence_review_contract["claim_evidence_consistency_requirements"],
            ),
            _render_list_line("route_back_policy", evidence_review_contract["route_back_policy"]),
        )
    )
    lines.extend(_render_medical_handoff_evidence_gate(evidence_review_contract))
    lines.extend(_render_medical_route_quality_loop(evidence_review_contract))

    lines.extend(
        (
            "",
            "## Upgrade Rule",
            "If `upgrade_triggers` is non-empty and any trigger is satisfied, "
            "upgrade from lightweight to managed before continuing.",
            "",
            "## Startup Boundary Rule",
            "Read MAS domain refs and request OPL provider hydration before any managed compute decision. Do not enter "
            "`startup_boundary_gated_routes` unless the MAS controller projection reports "
            "`startup_boundary_gate.allow_compute_stage = true`; otherwise stay within "
            "`managed_routes`, `governance_routes`, and any writing-only delivery route.",
            "",
            "## OPL Runtime Control Rule",
            "If `execution_owner_guard.supervisor_only = true`, stay in governance / monitoring mode, "
            "notify the user, report `browser_url`, `quest_session_api_url`, and `active_run_id` when present, "
            "and do not write OPL runtime-owned study surfaces.",
            "Treat `bundle_tasks_downstream_only = true` as a hard block on bundle/build/proofing actions.",
            "",
            "## No Ad-hoc Execution Rule",
            "When operating MAS-covered work, agents must use controller-authorized `CLI`, `MCP`, "
            "`product-entry`, or OPL-dispatched MAS domain handler surfaces before writing research outputs or advancing a study route.",
            "If a required capability is not exposed through those MAS contracts, stop and close the contract gap "
            "in the repo-tracked controller/callable surface before continuing; do not bypass MAS with ad-hoc "
            "scripts, direct artifact edits, prompt-only research chains, or generic document/PDF/Office tooling.",
            "",
            "## Revision Intake Rule",
            "Treat reviewer feedback, manuscript revision, mentor feedback, 审稿意见, 导师反馈, 论文修改, "
            "and Introduction/Methods/Results/Figure/Table feedback as `reviewer_revision` study task intake.",
            "Explicit user/reviewer manuscript feedback after a stopped, submission-ready, or finalize milestone "
            "reactivates the same study line; it is not permission to foreground-edit `manuscript/current_package`.",
            "After writing the durable task intake, OPL must hydrate or resume the provider attempt from MAS "
            "owner refs before MAS domain handlers edit canonical paper sources and regenerate `current_package` from that authority.",
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def _mode_payload_list(payload: dict[str, object]) -> list[dict[str, Any]]:
    raw_modes = payload.get("modes")
    if not isinstance(raw_modes, list):
        raise ValueError("modes must be a list")
    modes: list[dict[str, Any]] = []
    for mode in raw_modes:
        if not isinstance(mode, dict):
            raise ValueError("each mode must be a mapping")
        modes.append(mode)
    return modes


def _route_contract_payload_map(payload: dict[str, object]) -> list[dict[str, Any]]:
    raw_route_contracts = payload.get("route_contracts")
    if not isinstance(raw_route_contracts, dict):
        raise ValueError("route_contracts must be a mapping")
    route_contracts: list[dict[str, Any]] = []
    for route_id, route_contract in raw_route_contracts.items():
        if not isinstance(route_id, str) or not route_id:
            raise ValueError("route_contracts keys must be non-empty strings")
        if not isinstance(route_contract, dict):
            raise ValueError(f"route_contracts[{route_id}] must be a mapping")
        route_contracts.append(_project_route_contract(route_id, route_contract))
    return route_contracts


def _project_stage_route_payload(payload: dict[str, object]) -> dict[str, object]:
    projected = deepcopy(payload)
    raw_route_contracts = projected.get("route_contracts")
    if not isinstance(raw_route_contracts, dict):
        raise ValueError("route_contracts must be a mapping")
    for route_id, route_contract in list(raw_route_contracts.items()):
        if not isinstance(route_id, str) or not isinstance(route_contract, dict):
            continue
        raw_route_contracts[route_id] = _project_route_contract(route_id, route_contract)
    return projected


def _project_route_contract(route_id: str, route_contract: dict[str, Any]) -> dict[str, Any]:
    projected = deepcopy(route_contract)
    for (override_route_id, field), values in PROJECTED_ROUTE_FIELD_OVERRIDES.items():
        if override_route_id == route_id:
            projected[field] = list(values)
    return projected


def _evidence_review_contract_payload(payload: dict[str, object]) -> dict[str, Any]:
    raw_contract = payload.get("evidence_review_contract")
    if not isinstance(raw_contract, dict):
        raise ValueError("evidence_review_contract must be a mapping")
    return raw_contract


def _mapping(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a mapping")
    return value


def _render_late_stage_progress_sprint_contract(contract: dict[str, Any]) -> list[str]:
    return [
        "",
        "## Late-Stage Progress Sprint Contract",
        f"- sprint_id: {contract['sprint_id']}",
        f"- objective: {contract['objective']}",
        _render_list_line("covered_work_units", contract["covered_work_units"]),
        _render_list_line("covered_routes", contract["covered_routes"]),
        _render_list_line("attempt_scope", contract["attempt_scope"]),
        _render_list_line("control_plane_outputs", contract["control_plane_outputs"]),
        _render_list_line("forbidden_control_plane_outputs", contract["forbidden_control_plane_outputs"]),
        _render_list_line("quality_gate_policy", contract["quality_gate_policy"]),
        _render_optional_list_line("currentness_followthrough_policy", contract),
        _render_list_line("authority_boundary", contract["authority_boundary"]),
    ]


def _render_ordinary_progress_handoff_policy(policy: dict[str, Any]) -> list[str]:
    progress_delta_receipt = _mapping(policy.get("progress_delta_receipt"), "progress_delta_receipt")
    artifact_tier_policy = _mapping(policy.get("artifact_tier_policy"), "artifact_tier_policy")
    readiness_jit_policy = _mapping(policy.get("readiness_jit_policy"), "readiness_jit_policy")
    audit_sidecar_policy = _mapping(policy.get("audit_sidecar_policy"), "audit_sidecar_policy")

    return [
        "",
        "## Ordinary Progress Handoff Policy",
        f"- source_ref: {policy['source_ref']}",
        f"- default_progress_root: {policy['default_progress_root']}",
        f"- stage_goal_source: {policy['stage_goal_source']}",
        f"- executor_output_requirement: {policy['executor_output_requirement']}",
        _render_list_line("accepted_closeout_shapes", policy["accepted_closeout_shapes"]),
        f"- progress_delta_receipt_kind: {progress_delta_receipt['receipt_kind']}",
        f"- progress_delta_receipt_artifact_tier: {progress_delta_receipt['artifact_tier']}",
        f"- progress_delta_receipt_role: {progress_delta_receipt['role']}",
        _render_list_line("progress_delta_receipt_required_fields", progress_delta_receipt["required_fields"]),
        _render_list_line("progress_delta_receipt_cannot_authorize", progress_delta_receipt["cannot_authorize"]),
        _render_list_line("artifact_tiers", artifact_tier_policy["tiers"]),
        f"- artifact_default_tier: {artifact_tier_policy['default_tier']}",
        "- ordinary_delta_requires_full_stage_artifact_manifest: "
        f"{artifact_tier_policy['ordinary_delta_requires_full_stage_artifact_manifest']}",
        _render_list_line(
            "delivery_or_publication_claim_requires_tier",
            artifact_tier_policy["delivery_or_publication_claim_requires_tier"],
        ),
        f"- readiness_default_mode: {readiness_jit_policy['default_mode']}",
        f"- readiness_check_scope_source: {readiness_jit_policy['check_scope_source']}",
        f"- readiness_full_inventory_role: {readiness_jit_policy['full_readiness_inventory_role']}",
        f"- readiness_ordinary_blocking_policy: {readiness_jit_policy['ordinary_progress_blocking_policy']}",
        "- readiness_cannot_require_all_surfaces_before_writing_analysis_or_review_delta: "
        f"{readiness_jit_policy['cannot_require_all_surfaces_before_writing_analysis_or_review_delta']}",
        f"- audit_sidecar_role: {audit_sidecar_policy['role']}",
        f"- audit_sidecar_can_generate_default_next_action: {audit_sidecar_policy['can_generate_default_next_action']}",
        f"- audit_sidecar_can_close_stage: {audit_sidecar_policy['can_close_stage']}",
        f"- audit_sidecar_can_claim_domain_ready: {audit_sidecar_policy['can_claim_domain_ready']}",
    ]


def _render_medical_handoff_evidence_gate(evidence_review_contract: dict[str, Any]) -> list[str]:
    fields = {
        "structured_medical_handoff": "structured medical handoff",
        "durable_evidence_refs": "durable evidence refs",
        "medical_qa_feedback_loop": "medical QA feedback loop",
        "ai_reviewer_gate": "AI reviewer gate",
        "claim_only_ready_ban": "no claim-only ready",
    }
    if not any(field in evidence_review_contract for field in fields):
        return []
    lines = [
        "",
        "## Medical Handoff And Evidence Gate",
    ]
    for field, label in fields.items():
        if field in evidence_review_contract:
            lines.append(_render_list_line(label, evidence_review_contract[field]))
    return lines


def _render_medical_route_quality_loop(evidence_review_contract: dict[str, Any]) -> list[str]:
    fields = {
        "bounded_medical_repair_loop": "bounded medical repair loop",
        "default_needs_review_gate": "default needs review gate",
        "phase_gate_handoff": "phase gate handoff",
        "analysis_campaign_statistical_discipline": "analysis-campaign statistical discipline",
        "incident_postmortem_feedback_loop": "incident postmortem feedback loop",
    }
    if not any(field in evidence_review_contract for field in fields):
        return []
    lines = [
        "",
        "## Medical Route Quality Loop",
    ]
    for field, label in fields.items():
        if field in evidence_review_contract:
            lines.append(_render_list_line(label, evidence_review_contract[field]))
    return lines


def _string_list(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must contain strings")
    return list(value)


def _render_list_line(field: str, value: object, *, inline: bool = False) -> str:
    rendered_values = _string_list(value, field=field)
    rendered = " | ".join(rendered_values) if rendered_values else "(none)"
    prefix = "" if inline else "- "
    return f"{prefix}{field}: {rendered}"


def _render_optional_list_line(field: str, payload: dict[str, Any], *, inline: bool = False) -> str:
    value = payload.get(field)
    if not isinstance(value, list):
        prefix = "" if inline else "- "
        return f"{prefix}{field}: (none)"
    return _render_list_line(field, value, inline=inline)
