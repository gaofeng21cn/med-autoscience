from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "contracts" / "stage_quality_cycle_policy.json"
MANIFEST_PATH = ROOT / "agent" / "stages" / "manifest.json"
PHYSICAL_PACK_PATH = ROOT / "contracts" / "mas-paper-study-stage-pack.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_profile_binds_shared_quality_cycle_abi_and_context_isolation() -> None:
    profile = _load(PROFILE_PATH)

    assert profile["surface_kind"] == "opl_domain_stage_quality_cycle_profile"
    assert profile["version"] == "domain-stage-quality-cycle-profile.v1"
    assert profile["shared_surface_contracts"] == {
        "policy": {
            "surface_kind": "opl_stage_quality_cycle_policy",
            "version": "stage-quality-cycle-policy.v1",
        },
        "review_receipt": {
            "surface_kind": "opl_stage_review_receipt",
            "version": "stage-review-receipt.v1",
        },
        "review_context_manifest": {
            "surface_kind": "opl_stage_review_context_manifest",
            "version": "stage-review-context-manifest.v1",
        },
    }
    defaults = profile["quality_cycle_defaults"]
    assert defaults["in_thread_refinement"] == {
        "allowed": True,
        "authoritative": False,
        "can_emit_review_receipt": False,
        "can_close_formal_review": False,
    }
    formal = defaults["formal_review"]
    assert formal["new_stage_attempt_required"] is True
    assert formal["new_execution_session_required"] is True
    assert formal["no_context_inheritance"] is True
    assert formal["reviewer_session_must_differ_from_producer_session"] is True
    assert defaults["quality_revision_budget"]["max_repair_rounds"] == 3
    assert defaults["quality_revision_budget"]["provider_retry_consumes_budget"] is False
    assert defaults["role_prompt_refs"] == {
        "producer": "agent/quality_gates/stage_quality_cycle_roles.md#producer",
        "reviewer": "agent/quality_gates/stage_quality_cycle_roles.md#reviewer",
        "repairer": "agent/quality_gates/stage_quality_cycle_roles.md#repairer",
        "re_reviewer": "agent/quality_gates/stage_quality_cycle_roles.md#re-reviewer",
    }
    assert defaults["finding_repair_map"]["reviewer_can_repair_inline"] is False
    assert defaults["finding_repair_map"]["repairer_can_close_finding"] is False
    assert defaults["re_review_closure"]["fresh_re_reviewer_attempt_required"] is True
    assert defaults["re_review_closure"][
        "reviewed_hash_must_equal_repaired_artifact_hash"
    ] is True
    legacy_labels = profile["terminology"]["legacy_machine_label_classifications"]
    assert legacy_labels["triggered_meta_review"]["canonical_term"] == (
        "strategy_retrospective"
    )
    assert legacy_labels["triggered_meta_review"]["can_satisfy_cross_stage_meta_review"] is False
    assert legacy_labels["manuscript_consistency_meta_review"]["canonical_term"] == (
        "manuscript_consistency_gate_input"
    )
    assert legacy_labels["manuscript_consistency_meta_review"][
        "can_satisfy_cross_stage_meta_review"
    ] is False


def test_all_canonical_stages_bind_quality_policy_and_meta_review_is_explicit() -> None:
    profile = _load(PROFILE_PATH)
    manifest = _load(MANIFEST_PATH)
    stage_ids = [stage["stage_id"] for stage in manifest["stages"]]

    assert manifest["quality_governance_profile_ref"] == (
        "contracts/opl-framework/official-knowledge-deliverable-quality-profile.json"
    )
    assert manifest["meta_review_policy_ref"] == (
        "contracts/stage_quality_cycle_policy.json#/meta_review_policy"
    )
    assert set(profile["stage_policies"]) == set(stage_ids)
    for stage in manifest["stages"]:
        assert stage["stage_quality_cycle_policy_ref"] == (
            "contracts/stage_quality_cycle_policy.json#/stage_policies/"
            f"{stage['stage_id']}"
        )

    meta_stage = next(
        stage for stage in manifest["stages"]
        if stage["stage_id"] == "review_and_quality_gate"
    )
    assert meta_stage["stage_role"] == "cross_stage_meta_review"
    meta_policy = profile["stage_policies"]["review_and_quality_gate"]
    assert meta_policy["formal_review"]["required"] is False
    assert meta_policy["formal_review"]["max_repair_rounds"] == 0
    assert profile["meta_review_policy"]["inline_repair_allowed"] is False
    assert profile["meta_review_policy"]["attempt_role"] == "producer"
    assert profile["meta_review_policy"]["role_prompt_ref"].endswith("#producer")
    assert profile["meta_review_policy"]["rubric_refs"]

    required_policy_keys = {
        "surface_kind",
        "version",
        "enabled",
        "stage_prompt_ref",
        "role_prompt_refs",
        "quality_rubric_refs",
        "in_thread_refinement",
        "formal_review",
        "budget_exhaustion",
        "attempt_boundary",
    }
    assert profile["quality_cycle_defaults"]["attempt_roles"] == [
        "producer",
        "reviewer",
        "repairer",
        "re_reviewer",
    ]
    for stage_id, stage_policy in profile["stage_policies"].items():
        assert set(stage_policy) == required_policy_keys
        assert stage_policy["surface_kind"] == "opl_stage_quality_cycle_policy"
        assert stage_policy["version"] == "stage-quality-cycle-policy.v1"
        assert stage_policy["enabled"] is True
        assert stage_policy["stage_prompt_ref"] == f"agent/prompts/{stage_id}.md"
        assert set(stage_policy["role_prompt_refs"]) == {
            "producer",
            "reviewer",
            "repairer",
            "re_reviewer",
        }
        assert stage_policy["quality_rubric_refs"]
        assert stage_policy["in_thread_refinement"] == {
            "allowed": True,
            "authoritative": False,
        }
        formal_review = stage_policy["formal_review"]
        assert set(formal_review) == {
            "required",
            "risk_tier",
            "review_depth",
            "context_isolation_required",
            "max_repair_rounds",
        }
        assert formal_review["context_isolation_required"] is True
        assert 0 <= formal_review["max_repair_rounds"] <= 3
        assert stage_policy["budget_exhaustion"] == (
            "complete_with_quality_debt_if_consumable"
        )
        assert stage_policy["attempt_boundary"] == {
            "inherits_stage_goal_scope_authority": True,
            "role_overlay_may_only_narrow": True,
            "controller_creates_next_attempt": True,
            "attempt_is_not_sub_stage": True,
        }


def test_six_canonical_stages_cover_each_of_eight_physical_stages_once() -> None:
    profile = _load(PROFILE_PATH)
    manifest = _load(MANIFEST_PATH)
    physical_pack = _load(PHYSICAL_PACK_PATH)
    mapping = profile["canonical_to_physical_stage_mapping"]
    canonical_stage_ids = [stage["stage_id"] for stage in manifest["stages"]]
    physical_stage_ids = [stage["stage_id"] for stage in physical_pack["stages"]]

    assert list(mapping) == canonical_stage_ids
    mapped_physical_ids = [
        stage_id
        for canonical_stage_id in canonical_stage_ids
        for stage_id in mapping[canonical_stage_id]
    ]
    assert len(canonical_stage_ids) == 6
    assert len(physical_stage_ids) == 8
    assert mapped_physical_ids == physical_stage_ids
    assert len(mapped_physical_ids) == len(set(mapped_physical_ids))
