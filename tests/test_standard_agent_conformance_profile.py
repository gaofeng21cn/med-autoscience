from __future__ import annotations

import json
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "contracts" / "standard_agent_conformance_profile.json"
STAGE_MANIFEST = ROOT / "agent" / "stages" / "manifest.json"
EXPECTED_STAGE_DISPLAY_NAMES = {
    "direction_and_route_selection": {
        "en-US": "Direction and route selection",
        "zh-CN": "研究方向与路线选择",
    },
    "baseline_and_evidence_setup": {
        "en-US": "Baseline and evidence setup",
        "zh-CN": "基线与证据准备",
    },
    "bounded_analysis_campaign": {
        "en-US": "Bounded analysis campaign",
        "zh-CN": "有界分析推进",
    },
    "manuscript_authoring": {
        "en-US": "Manuscript authoring",
        "zh-CN": "论文撰写",
    },
    "review_and_quality_gate": {
        "en-US": "Review and quality gate",
        "zh-CN": "评审与质量门禁",
    },
    "finalize_and_publication_handoff": {
        "en-US": "Finalize and publication handoff",
        "zh-CN": "定稿与投稿交接",
    },
}


def test_standard_agent_conformance_profile_matches_canonical_stage_pack() -> None:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    stage_manifest = json.loads(STAGE_MANIFEST.read_text(encoding="utf-8"))
    stages = stage_manifest["stages"]
    stage_ids = [stage["stage_id"] for stage in stages]

    assert profile["surface_kind"] == "opl_standard_agent_conformance_profile"
    assert profile["version"] == "opl.standard-agent-conformance-profile.v1"
    assert profile["target_domain_id"] == "medautoscience"
    assert stage_ids == list(EXPECTED_STAGE_DISPLAY_NAMES)
    for stage in stages:
        expected_names = EXPECTED_STAGE_DISPLAY_NAMES[stage["stage_id"]]
        display_names = stage["display_names"]

        assert isinstance(display_names, dict)
        assert {
            locale: display_names.get(locale) for locale in expected_names
        } == expected_names
        assert stage["title"] == display_names["en-US"]
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


def test_medical_authority_source_refs_match_repo_hygiene_allowlist() -> None:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    classifications = {
        entry["surface_id"]: entry
        for entry in profile["physical_morphology"]["surface_classifications"]
    }
    medical_authority_refs = {
        ref
        for ref in classifications["medical_authority_functions"]["source_refs"]
        if ref.startswith("src/med_autoscience/authority_handlers/")
    }
    hygiene_globals = runpy.run_path(str(ROOT / "scripts" / "repo_hygiene_audit.py"))
    expected_source_files = hygiene_globals["EXPECTED_STANDARD_AGENT_SOURCE_FILES"]
    expected_authority_refs = {
        ref
        for ref in expected_source_files
        if ref.startswith("src/med_autoscience/authority_handlers/")
    }

    assert medical_authority_refs == expected_authority_refs


def test_repo_hygiene_delegates_shared_byproducts_to_opl() -> None:
    verify_script = (ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8")
    hygiene_globals = runpy.run_path(str(ROOT / "scripts" / "repo_hygiene_audit.py"))

    assert 'workspace source-hygiene --source-root "${repo_root}" --json' in verify_script
    assert set(hygiene_globals["MAS_POLICY_DIRECTORY_NAMES"]) == {
        "ops",
        "build",
        "tmp",
        ".ruff_cache",
        ".mypy_cache",
    }
    assert set(hygiene_globals["MAS_POLICY_FILE_NAMES"]) == {".DS_Store"}
