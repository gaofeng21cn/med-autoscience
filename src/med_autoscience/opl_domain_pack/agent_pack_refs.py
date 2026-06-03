from __future__ import annotations

from collections.abc import Mapping

AGENT_PROMPT_REFS: dict[str, str] = {
    "direction_and_route_selection": "agent/prompts/direction_and_route_selection.md",
    "baseline_and_evidence_setup": "agent/prompts/baseline_and_evidence_setup.md",
    "bounded_analysis_campaign": "agent/prompts/bounded_analysis_campaign.md",
    "manuscript_authoring": "agent/prompts/manuscript_authoring.md",
    "review_and_quality_gate": "agent/prompts/review_and_quality_gate.md",
    "finalize_and_publication_handoff": "agent/prompts/finalize_and_publication_handoff.md",
}
AGENT_STAGE_POLICY_REFS: dict[str, str] = {
    stage_id: f"agent/stages/{stage_id}.policy.md" for stage_id in AGENT_PROMPT_REFS
}
AGENT_SKILL_REFS: tuple[str, ...] = (
    "agent/skills/medical_research_execution.md",
    "agent/skills/owner_receipt_and_route_control.md",
)
AGENT_QUALITY_GATE_REFS: tuple[str, ...] = (
    "agent/quality_gates/ai_reviewer_auditor_gate.md",
    "agent/quality_gates/artifact_source_authority_gate.md",
)
AGENT_KNOWLEDGE_REFS: tuple[str, ...] = (
    "agent/knowledge/medical_research_truth.md",
    "agent/knowledge/hypothesis_portfolio_evidence_pack.md",
    "agent/knowledge/publication_route_memory.md",
    "agent/knowledge/source_readiness_and_artifact_authority.md",
)
REQUIRED_DOMAIN_PACK_PATHS: tuple[str, ...] = (
    "agent/stages/stage_route_contract.yaml",
    *AGENT_PROMPT_REFS.values(),
    *AGENT_STAGE_POLICY_REFS.values(),
    *AGENT_SKILL_REFS,
    *AGENT_QUALITY_GATE_REFS,
    *AGENT_KNOWLEDGE_REFS,
)


def stage_prompt_ref(stage: Mapping[str, object]) -> str:
    stage_id = str(stage.get("stage_id") or "")
    try:
        return AGENT_PROMPT_REFS[stage_id]
    except KeyError as exc:
        raise ValueError(f"stage missing agent prompt ref: {stage_id}") from exc


def stage_policy_ref(stage: Mapping[str, object]) -> str:
    stage_id = str(stage.get("stage_id") or "")
    try:
        return AGENT_STAGE_POLICY_REFS[stage_id]
    except KeyError as exc:
        raise ValueError(f"stage missing agent policy ref: {stage_id}") from exc


def stage_knowledge_refs(stage: Mapping[str, object]) -> list[dict[str, object]]:
    domain_stage_refs = {str(item) for item in stage.get("domain_stage_refs", [])}
    refs: list[dict[str, object]] = [
        {"ref_kind": "repo_path", "ref": ref, "role": "domain_pack_knowledge"}
        for ref in AGENT_KNOWLEDGE_REFS
    ]
    if domain_stage_refs & {"scout", "idea", "analysis-campaign", "review", "decision"}:
        refs.append(
            {
                "ref_kind": "domain_memory_ref",
                "ref": "mas_publication_route_memory",
                "role": "publication_route_memory_locator",
            }
        )
    return refs

__all__ = [
    "AGENT_KNOWLEDGE_REFS",
    "AGENT_PROMPT_REFS",
    "AGENT_QUALITY_GATE_REFS",
    "AGENT_SKILL_REFS",
    "AGENT_STAGE_POLICY_REFS",
    "REQUIRED_DOMAIN_PACK_PATHS",
    "stage_knowledge_refs",
    "stage_policy_ref",
    "stage_prompt_ref",
]
