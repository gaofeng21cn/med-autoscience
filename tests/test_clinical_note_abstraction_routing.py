from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = "medical-clinical-note-abstraction"
REQUIRED_CANDIDATE_REFS = {
    "abstraction_schema_ref",
    "note_level_candidate_refs",
    "span_provenance_ref",
    "assertion_context_ref",
    "terminology_validation_ref",
    "completeness_ref",
    "chart_review_validation_candidate_ref",
    "candidate_refs",
    "route_back_candidate",
    "owner_gate_handoff_ref",
}


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _capability() -> dict[str, object]:
    capability_map = json.loads(_read("contracts/capability_map.json"))
    matches = [
        item
        for item in capability_map["capabilities"]
        if item["capability_id"] == SKILL_ID
    ]
    assert len(matches) == 1
    return matches[0]


def test_clinical_note_abstraction_is_optional_refs_only_without_new_module_or_runtime() -> None:
    capability = _capability()

    assert capability["canonical_owner"] == "mas-scholar-skills"
    assert capability["specialist_classification"] == "optional_named_specialty"
    assert capability["router_skill_id"] == "medical-methodology-planner"
    assert capability["applicable_stage_ids"] == ["baseline_and_evidence_setup"]
    assert set(capability["required_candidate_ref_families"]) == REQUIRED_CANDIDATE_REFS
    assert "module_id" not in capability
    assert capability["routing_boundaries"] == {
        "one_note_per_invocation": True,
        "explicit_schema_required": True,
        "unsupported_values_are_explicit_nulls": True,
        "verbatim_span_and_assertion_context_required_when_evidenced": True,
        "terminology_mapping_requires_separate_current_source_validation": True,
        "chart_review_validation_remains_candidate_until_owner_consumption": True,
        "adds_active_module_id": False,
        "adds_runtime_or_provider": False,
        "becomes_required_core_export": False,
    }
    assert all(value is False for key, value in capability["authority_boundary"].items() if key.startswith("can_"))
    assert capability["authority_boundary"]["closeout_requires_mas_owner_surface"] is True


def test_clinical_note_abstraction_routes_only_through_declared_local_surfaces() -> None:
    capability = _capability()

    local_paths = {
        path
        for path in capability["canonical_paths"]
        if not path.startswith("external_repo:")
    }
    assert local_paths == {
        "agent/prompts/baseline_and_evidence_setup.md",
        "agent/skills/medical_research_execution.md",
        "contracts/capability_map.json",
    }
    assert all((ROOT / path).is_file() for path in local_paths)
    assert (ROOT / "agent/stages/baseline_and_evidence_setup.policy.md").is_file()
    assert (ROOT / "agent/stages/stage_route_contract.yaml").is_file()


def test_clean_room_provenance_does_not_admit_anthropic_as_runtime_or_authority() -> None:
    capability = _capability()
    provenance = capability["clean_room_learning_provenance"]

    assert provenance["source_ref"].endswith(
        "744278a1fe63fd5eb99fe9961db0a73c0cb3280c"
    )
    assert provenance["source_status_at_review"] == (
        "experimental_no_standard_open_source_license_observed"
    )
    assert provenance["local_absorption"] == (
        "behavioral_patterns_only_no_source_code_templates_or_regulatory_wording_copied"
    )
    assert provenance["source_is_runtime_or_authority"] is False
