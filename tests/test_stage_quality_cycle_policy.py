from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta
ROOT = Path(__file__).resolve().parents[1]


def _load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def test_quality_cycle_uses_canonical_attempt_outcome_and_controller_receipt() -> None:
    profile = _load("contracts/stage_quality_cycle_policy.json")
    defaults = profile["quality_cycle_defaults"]
    attempt = defaults["attempt_output_contract"]

    assert attempt == {
        "envelope_path": "route_impact.stage_quality_cycle",
        "outcome_field": "outcome",
        "outcome_required_for_roles": ["reviewer", "re_reviewer"],
        "outcome_values": [
            "pass",
            "repair_required",
            "quality_debt",
            "blocked",
            "human_gate",
        ],
        "attempts_must_not_emit_receipt_verdict": True,
        "receipt_materializer_owner": "opl_stage_run_controller",
        "review_receipt_verdict_mapping": {
            "pass": "pass",
            "repair_required": "repair_required",
            "quality_debt": "quality_debt",
            "blocked": "hard_stop",
            "human_gate": "hard_stop",
        },
    }
    formal = defaults["formal_review"]
    assert formal["new_stage_attempt_required"] is True
    assert formal["new_execution_session_required"] is True
    assert formal["no_context_inheritance"] is True
    assert formal["reviewer_session_must_differ_from_producer_session"] is True
    assert defaults["repair_map"]["repairer_can_make_terminal_route_decision"] is False
    assert defaults["re_review_closure"]["fresh_re_reviewer_attempt_required"] is True


def test_all_six_stages_bind_quality_policy_and_budget_exhaustion() -> None:
    profile = _load("contracts/stage_quality_cycle_policy.json")
    manifest = _load("agent/stages/manifest.json")
    stage_ids = [stage["stage_id"] for stage in manifest["stages"]]

    assert set(profile["stage_policies"]) == set(stage_ids)
    for stage in manifest["stages"]:
        stage_id = stage["stage_id"]
        assert stage["stage_quality_cycle_policy_ref"] == (
            f"contracts/stage_quality_cycle_policy.json#/stage_policies/{stage_id}"
        )
        stage_policy = profile["stage_policies"][stage_id]
        assert stage_policy["budget_exhaustion"] == (
            "complete_with_quality_debt_if_consumable"
        )
        assert stage_policy["attempt_boundary"] == {
            "inherits_stage_goal_scope_authority": True,
            "role_overlay_may_only_narrow": True,
            "controller_creates_next_attempt": True,
            "attempt_is_not_sub_stage": True,
        }


def test_route_authority_is_split_and_legacy_owner_is_absent() -> None:
    principles = _load("contracts/stage_operating_principles.json")
    manifest = _load("agent/stages/manifest.json")
    profile = _load("contracts/stage_quality_cycle_policy.json")

    for policy in (principles["speed_policy"], manifest["progress_first_policy"]):
        assert policy["semantic_route_decision_owner"] == "decisive_codex_attempt"
        assert policy["stage_transition_materialization_owner"] == (
            "opl_stage_run_controller"
        )
        assert "route_selection_owner" not in policy

    progress_policy = manifest["progress_first_policy"]
    assert progress_policy["primary_only_decisive_attempt_role"] == "producer"
    assert progress_policy["formal_review_decisive_attempt_roles"] == [
        "reviewer",
        "re_reviewer",
    ]
    assert progress_policy["repairer_can_be_decisive_attempt"] is False

    route = profile["cross_stage_route_selection"]
    assert route["semantic_route_decision_owner"] == "decisive_codex_attempt"
    assert route["stage_transition_materialization_owner"] == (
        "opl_stage_run_controller"
    )
    assert route["primary_only_decisive_attempt_role"] == "producer"
    assert route["formal_review_decisive_attempt_roles"] == [
        "reviewer",
        "re_reviewer",
    ]
    assert route["producer_can_be_decisive_attempt_in_formal_review"] is False
    assert route["repairer_can_be_decisive_attempt"] is False
    assert "producer_or_repairer_may_return_terminal_route_decision" not in route
    assert route[
        "same_stage_repair_required_with_budget_remaining_continues_quality_loop"
    ] is True
    assert route[
        "repair_required_review_or_re_review_may_select_cross_stage_route_back_before_budget_exhaustion"
    ] is True
    assert route[
        "repair_required_cross_stage_route_back_requires_target_different_from_current_stage"
    ] is True
    assert route[
        "cross_stage_route_back_requires_narrowest_canonical_owner_stage"
    ] is True
    assert route[
        "repair_required_review_or_re_review_may_select_other_terminal_route_before_budget_exhaustion"
    ] is False
    assert route[
        "repair_required_review_or_re_review_may_select_terminal_route_after_budget_exhaustion"
    ] is True
    assert route["hard_stop_or_zero_consumable_artifact_route_output"] == "none"


def test_quality_role_prompt_allows_only_cross_stage_route_back_before_exhaustion() -> None:
    roles = (ROOT / "agent/quality_gates/stage_quality_cycle_roles.md").read_text(
        encoding="utf-8"
    )
    analysis_prompt = (ROOT / "agent/prompts/bounded_analysis_campaign.md").read_text(
        encoding="utf-8"
    )
    normalized_roles = " ".join(roles.split())
    reviewer = roles.split("## Reviewer", 1)[1].split("## Repairer", 1)[0]
    re_reviewer = roles.split("## Re Reviewer", 1)[1]

    assert roles.count("`same_stage_repair_required`") >= 3
    assert "controller creates the next fresh repairer Attempt" in roles
    assert roles.count("`cross_stage_route_back_before_budget_exhaustion`") >= 3
    assert "outcome `repair_required` plus exactly one" in normalized_roles
    assert "`decision_kind=route_back`" in roles
    assert "`target_stage_id` different from the current" in normalized_roles
    assert "only terminal route allowed before repair-budget exhaustion" in normalized_roles
    assert "narrowest canonical owner is a different declared Stage" in normalized_roles
    assert "A repairer never makes a terminal route decision" in roles
    assert "hard-boundary reviewer returns no route output" in normalized_roles
    assert "same-Stage repair continues the quality loop" in analysis_prompt
    for decisive_review_section in (reviewer, re_reviewer):
        assert "`same_stage_repair_required`" in decisive_review_section
        assert (
            "`cross_stage_route_back_before_budget_exhaustion`"
            in decisive_review_section
        )


def test_main_prompts_label_the_forward_stage_as_a_default_not_a_route_constraint() -> None:
    manifest = _load("agent/stages/manifest.json")
    stage_ids = {
        "direction_and_route_selection",
        "baseline_and_evidence_setup",
        "bounded_analysis_campaign",
        "manuscript_authoring",
    }

    prompts = {
        stage["stage_id"]: (ROOT / stage["prompt_ref"]).read_text(encoding="utf-8")
        for stage in manifest["stages"]
        if stage["stage_id"] in stage_ids
    }
    assert set(prompts) == stage_ids
    for prompt in prompts.values():
        assert "\nDefault forward stage: " in prompt
        assert "\nNext stage: " not in prompt


def test_active_stage_manifest_uses_canonical_review_gate_input_ids() -> None:
    manifest = _load("agent/stages/manifest.json")
    required_gate_inputs = {
        gate_input
        for stage in manifest["stages"]
        for check in stage.get("stage_contract_extension", {}).get(
            "mandatory_pre_gate_checks", []
        )
        for gate_input in check.get("required_gate_input_surfaces", [])
    }

    assert "manuscript_consistency_gate_input" in required_gate_inputs
    assert "manuscript_consistency_meta_review" not in required_gate_inputs


def test_hypothesis_promotion_is_a_review_contract_not_python_validator() -> None:
    manifest = _load("agent/stages/manifest.json")
    pack_input = _load("contracts/pack_compiler_input.json")
    pack_contract = pack_input["hypothesis_portfolio_evidence_pack_contract"]

    assert pack_contract["candidate_promotion_requires_review_receipt"] is True
    assert pack_contract["validation_contract_ref"] == (
        "contracts/stage_quality_cycle_policy.json#/quality_cycle_defaults/formal_review"
    )
    assert "validator_ref" not in pack_contract
    required_refs = pack_contract["candidate_required_ref_families"]
    assert "hypothesis_candidate_ref" in required_refs
    assert "supporting_evidence_ref" in required_refs
    assert "contradicting_evidence_ref" in required_refs
    assert "testability_ref" in required_refs
    assert "safety_risk_ref" in required_refs
    assert "independent_reviewer_or_auditor_receipt_ref" in required_refs

    for stage in manifest["stages"]:
        contract = stage["stage_contract_extension"][
            "hypothesis_portfolio_evidence_pack"
        ]
        assert contract["candidate_promotion_requires_review_receipt"] is True
        assert "validator_ref" not in contract


def test_connect_receipts_are_consumed_by_hosted_review_not_private_transport() -> None:
    manifest = _load("agent/stages/manifest.json")
    contracts = [
        check["provider_resolution_contract"]
        for stage in manifest["stages"]
        for check in stage.get("stage_contract_extension", {}).get(
            "mandatory_pre_gate_checks", []
        )
    ]

    assert len(contracts) == 2
    for contract in contracts:
        assert contract["execution_owner"] == "OPL Connect"
        assert contract["provider_lookup_mode"] == "opl_connect_receipt_input_only"
        assert contract["provider_receipt_consumed_by"] == (
            "opl_hosted:mas_independent_reviewer_attempt"
        )
        assert contract["mas_can_invoke_opl_connect"] is False
        assert "provider_evidence_consumed_by" not in contract
