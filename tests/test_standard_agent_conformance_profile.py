from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "contracts" / "standard_agent_conformance_profile.json"
STAGE_MANIFEST = ROOT / "agent" / "stages" / "manifest.json"
AGENT_LAB_HANDOFF = ROOT / "contracts" / "agent_lab_handoff.json"


def test_standard_agent_conformance_profile_matches_canonical_stage_pack() -> None:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    stage_manifest = json.loads(STAGE_MANIFEST.read_text(encoding="utf-8"))
    stage_ids = [stage["stage_id"] for stage in stage_manifest["stages"]]

    assert profile["surface_kind"] == "opl_standard_agent_conformance_profile"
    assert profile["version"] == "opl.standard-agent-conformance-profile.v1"
    assert profile["target_domain_id"] == "medautoscience"
    assert profile["golden_path"]["required_stage_ids"] == stage_ids
    assert profile["golden_path"]["allowed_stage_ids"] == stage_ids
    assert profile["golden_path"]["default_stage_id"] == "direction_and_route_selection"
    assert profile["quality_governance"] == {
        "profile_ref": "contracts/stage_quality_cycle_policy.json",
        "required_for_all_canonical_stages": True,
        "formal_review_requires_independent_attempt": True,
        "formal_review_requires_new_execution_session": True,
        "no_context_inheritance_required": True,
        "same_thread_checking_is_in_thread_refinement_only": True,
        "default_max_quality_revision_rounds": 3,
        "meta_review_stage_id": "review_and_quality_gate",
    }
    assert profile["canonical_stage_mapping"]["canonical_stage_count"] == 6
    assert profile["canonical_stage_mapping"]["physical_stage_count"] == 8


def test_standard_agent_conformance_profile_classifies_every_required_surface() -> None:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    morphology = profile["physical_morphology"]
    classifications = {
        entry["surface_id"]: entry for entry in morphology["surface_classifications"]
    }

    assert set(morphology["required_surface_ids"]) == set(classifications)
    assert all(entry["source_refs"] for entry in classifications.values())
    for entry in classifications.values():
        for source_ref in entry["source_refs"]:
            assert (ROOT / source_ref).exists(), source_ref

    assert "medical_truth_quality_artifact_and_owner_receipt_remain_mas_owned" in morphology[
        "required_parity_gates"
    ]


def test_agent_lab_handoff_uses_the_generic_evolution_skill_ref() -> None:
    handoff = json.loads(AGENT_LAB_HANDOFF.read_text(encoding="utf-8"))
    adapter = handoff["suite_templates"]["medical_manuscript_quality"]

    assert adapter["agent_evolution_skill_ref"] == (
        "opl-meta-agent:oma-agent-evolution"
    )
    assert "oma_evolution_skill_ref" not in adapter
