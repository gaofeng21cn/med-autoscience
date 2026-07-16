from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_stage_routes_consume_registry_signal_validity_pack_by_owner_role() -> None:
    contract = _read("agent/stages/stage_route_contract.yaml")
    start = contract.index("registry_signal_validity_pack_consumption:\n")
    end = contract.index("\nevidence_review_contract:\n", start)
    policy = contract[start:end]

    required_fragments = (
        "pack_id: registry_signal_validity_pack",
        "specialist_package: mas-scholar-skills",
        "owner_route: medical-statistical-review",
        "pack_producer_skill: medical-statistical-review",
        "optional_framing_input_skill: medical-registry-atlas-story-architect",
        "aggregate_ref_family: ehr_registry_signal_validity_ref",
        "- clinical-gap",
        "- data-audit",
        "scout:",
        "idea:",
        "baseline:",
        "validity_plan_ref",
        "analysis-campaign:",
        "produce validation and sensitivity evidence refs",
        "write:",
        "review:",
        "pack_presence_is_validation: false",
        "optional_framing_input_can_produce_or_own_pack_alone: false",
    )
    assert all(fragment in policy for fragment in required_fragments)
    assert policy.index("scout:") < policy.index("idea:") < policy.index("baseline:")
    assert policy.index("baseline:") < policy.index("analysis-campaign:")
    assert policy.index("analysis-campaign:") < policy.index("write:")
    assert policy.index("write:") < policy.index("review:")


def test_execution_and_reviewer_policies_preserve_boundaries() -> None:
    execution = _read("agent/skills/medical_research_execution.md")
    gate = _read("agent/quality_gates/ai_reviewer_auditor_gate.md")
    normalized_execution = " ".join(execution.split())
    normalized_gate = " ".join(gate.split())

    assert "`medical-statistical-review`" in execution
    assert (
        "`medical-registry-atlas-story-architect` may contribute optional"
        in normalized_execution
    )
    assert "cannot produce or own the pack alone" in normalized_execution
    assert "`registry_signal_validity_pack`" in execution
    assert "`ehr_registry_signal_validity_ref`" in execution
    assert "Keep the professional checklist in ScholarSkills" in normalized_execution
    assert "## Registry Signal Validity Floor" in gate
    assert "not executed validation evidence" in gate
    assert "explicit current MAS owner or human waiver ref" in gate
    assert "`unvalidated data-audit` or `exploratory`" in normalized_gate


def test_revision_uses_existing_stage_action_and_workspace_authority() -> None:
    policy = _read(
        "docs/policies/study-workflow/submission_revision_operating_contract.md"
    )
    catalog = json.loads(_read("contracts/action_catalog.json"))
    action_ids = [action["action_id"] for action in catalog["actions"]]
    manuscript_action = next(
        action
        for action in catalog["actions"]
        if action["action_id"] == "manuscript_authoring"
    )

    assert "Workspace `manuscript/` is the controller-authorized canonical" in policy
    assert "Workspace `submission/`" in policy
    assert "legacy compatibility alias or provenance surface" in policy
    assert "`revision_intake_wake_host_binding_missing`" in policy
    assert "must all start from controller-authorized `paper/` sources" not in policy
    assert "revision_intake_wake" not in action_ids
    assert len(action_ids) == 8
    assert {"user_intent", "input_refs", "route_context_refs"}.issubset(
        manuscript_action["optional_fields"]
    )
