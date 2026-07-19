from __future__ import annotations

import json
from pathlib import Path

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


def test_quality_cycle_declares_role_bound_review_transport_production_path() -> None:
    profile = _load("contracts/stage_quality_cycle_policy.json")
    pack_input = _load("contracts/pack_compiler_input.json")
    transport = profile["review_transport_contracts"]
    snapshot = transport["review_input_snapshot_materialization_request"]
    page_candidate = transport["page_hash_evidence_candidate"]

    assert snapshot["envelope_path"] == (
        "route_impact.stage_quality_cycle."
        "review_input_snapshot_materialization_request"
    )
    assert snapshot["allowed_attempt_roles"] == ["producer", "repairer"]
    assert snapshot["forbidden_attempt_roles"] == ["reviewer", "re_reviewer"]
    assert snapshot["requires_generation_manifest_schema_version"] == 2
    assert snapshot[
        "source_refs_by_member_id_must_exactly_match_review_scope"
    ] is True
    assert snapshot["owner_ref_source"] == (
        "mas_owned_generation_manifest_review_scope_member_ref"
    )
    assert snapshot["source_ref_source"] == "explicit_host_transport_locator_mapping"
    assert snapshot["source_ref_is_review_scope_identity"] is False
    assert snapshot["mas_authority_record_required"] is True
    assert snapshot["mas_authority_record_ref_binds_canonical_exact_bytes"] is True
    assert snapshot["snapshot_authority_record_includes_owner_ref"] is True
    assert snapshot[
        "all_review_scope_topology_locators_are_path_independent"
    ] is True
    assert snapshot["host_may_infer_from_generic_artifact_refs"] is False
    assert snapshot["missing_request_blocks_hosted_action_liveness"] is False
    assert snapshot["missing_request_policy"] == (
        "lane_quality_debt_without_quality_or_readiness_claim"
    )
    assert snapshot[
        "present_invalid_or_unmaterializable_request_fails_closed"
    ] is True
    assert snapshot["transport_failure_may_forge_domain_typed_blocker"] is False
    assert snapshot["schema_ref"].endswith(
        "/reviewer-input-snapshot-materialization-request.schema.json"
    )

    assert page_candidate["envelope_path"] == (
        "route_impact.stage_quality_cycle.page_hash_evidence_candidate"
    )
    assert page_candidate["allowed_attempt_roles"] == ["reviewer", "re_reviewer"]
    assert page_candidate["forbidden_attempt_roles"] == ["producer", "repairer"]
    assert page_candidate["pass_through_unchanged"] is True
    assert page_candidate["candidate_or_cache_can_emit_verdict_or_authority"] is False
    assert page_candidate["fresh_reviewer_invocation_still_required"] is True
    assert page_candidate["fresh_reviewer_receipt_still_required"] is True
    assert page_candidate["fresh_mas_judgment_still_required"] is True

    assert pack_input["stage_quality_transport_contract_refs"] == {
        "review_input_snapshot_materialization_request": (
            "contracts/stage_quality_cycle_policy.json#/review_transport_contracts/"
            "review_input_snapshot_materialization_request"
        ),
        "page_hash_evidence_candidate": (
            "contracts/stage_quality_cycle_policy.json#/review_transport_contracts/"
            "page_hash_evidence_candidate"
        ),
    }
    assert pack_input["source_refs"][
        "review_input_snapshot_request_builder_ref"
    ].endswith("#build_review_input_snapshot_materialization_request")
    assert pack_input["source_refs"][
        "review_input_snapshot_materialization_request_schema_ref"
    ] == snapshot["schema_ref"]
    assert pack_input["source_refs"][
        "scholarskills_page_hash_evidence_candidate_schema_ref"
    ] == page_candidate["schema_ref"]

    roles = (ROOT / "agent/quality_gates/stage_quality_cycle_roles.md").read_text(
        encoding="utf-8"
    )
    normalized_roles = " ".join(roles.split())
    producer = roles.split("## Producer", 1)[1].split("## Reviewer", 1)[0]
    reviewer = roles.split("## Reviewer", 1)[1].split("## Repairer", 1)[0]
    repairer = roles.split("## Repairer", 1)[1].split("## Re Reviewer", 1)[0]
    re_reviewer = roles.split("## Re Reviewer", 1)[1]
    assert "review_input_snapshot_materialization_request" in roles
    assert "never infer the map from generic artifact refs" in normalized_roles
    assert "record lane quality debt and continue" in normalized_roles
    assert "present request fails closed as a transport contract error" in (
        normalized_roles
    )
    assert "never relabel it as ordinary quality debt" in normalized_roles
    assert "forge a MAS typed blocker" in normalized_roles
    assert "page_hash_evidence_candidate" in roles
    assert "returns it unchanged" in roles
    assert "page-hash evidence candidate" not in producer
    assert "page-hash evidence candidate" not in repairer
    assert "page-hash evidence candidate" in reviewer
    assert "page-hash evidence candidate" in re_reviewer


def test_quality_cycle_adopts_framework_epistemic_currentness_and_scope_budget() -> None:
    profile = _load("contracts/stage_quality_cycle_policy.json")
    adoption = profile["epistemic_review_currentness_adoption"]

    assert adoption["canonical_framework_sha"] == (
        "367738244273664452e6b7ebfb86d5de5bb36c30"
    )
    assert adoption["evidence_profile"] == "epistemic_provenance"
    assert adoption["trust_model"] == "trusted_local_workspace"
    assert adoption["framework_owns"] == [
        "generic_contract_validation",
        "dependency_currentness_evaluation",
        "stage_quality_scope_budget_enforcement",
    ]
    assert (
        "domain_artifact_claim_and_provenance_dependency_declaration"
        in adoption["mas_owns"]
    )
    assert adoption["hash_change_alone_invalidates_review"] is False
    assert adoption[
        "semantic_change_invalidates_only_declared_dependency_closure"
    ] is True
    assert adoption["scope_budget"] == {
        "surface_kind": "opl_stage_quality_scope_budget",
        "version": "opl-stage-quality-scope-budget.v1",
        "max_attempts": 3,
        "max_elapsed_ms": 21600000,
        "max_tokens": 1000000,
        "token_budget_requires_observed_usage": True,
        "missing_token_telemetry_is_not_zero_usage": True,
        "foreground_execution_must_use_managed_attempt": True,
        "enforcement_owner": "OPL Framework",
        "mas_attempt_projection": "repair_state.attempts_used/max_attempts",
        "reviewer_revision_uses_same_scope_budget": True,
        "available_disposition": "route_back",
        "exhausted_with_consumable_artifact_disposition": (
            "completed_with_quality_debt"
        ),
    }
    assert adoption["professional_skills"] == {
        "owner": "mas-scholar-skills",
        "supplies_quality_rules_only": True,
        "owns_generation_signature": False,
        "owns_currentness_or_loop_scheduling": False,
    }
    separation = adoption["integrity_separation"]
    assert separation["release_integrity_allowed_only_for"] == (
        "mas_software_package_release_set"
    )
    assert separation["release_set_ref"] == (
        "contracts/mas_validator_release_set_receipt.json"
    )
    assert separation[
        "manuscript_analysis_reference_and_submission_package_use_release_integrity"
    ] is False


def test_reviewer_revision_reuses_framework_scope_budget_and_scholar_quality_rules() -> None:
    stage_pack = _load("contracts/mas-paper-study-stage-pack.json")
    mechanism = stage_pack["reviewer_revision_default_mechanism"]
    route = mechanism["epistemic_review_route_back"]

    assert route == {
        "trigger": (
            "consumed_reviewer_revision_with_missing_or_stale_review_currentness"
        ),
        "framework_contract_sha": (
            "367738244273664452e6b7ebfb86d5de5bb36c30"
        ),
        "scope_budget_ref": (
            "contracts/stage_quality_cycle_policy.json#/"
            "epistemic_review_currentness_adoption/scope_budget"
        ),
        "attempt_projection": "paper_mission.repair_state",
        "max_attempts": 3,
        "attempts_remaining_disposition": "route_back_to_independent_reviewer",
        "budget_exhausted_with_consumable_artifact_disposition": (
            "completed_with_quality_debt"
        ),
        "budget_exhausted_reason_code": "review_scope_budget_exhausted",
        "applies_in_finalize_and_publication_handoff": True,
        "creates_parallel_retry_scheduler": False,
    }
    skills = mechanism["specialist_skill_writeback_contract"]
    assert skills["professional_skills_supply_quality_rules_only"] is True
    assert skills[
        "professional_skills_own_generation_signatures_or_loop_scheduling"
    ] is False


def test_artifact_iteration_separates_preview_freeze_and_projection() -> None:
    policy = _load("contracts/artifact_iteration_efficiency_policy.json")
    plan = policy["impact_plan"]
    fallback = plan["legacy_descriptor_fallback"]
    preview = policy["iterative_preview"]
    freeze = policy["candidate_freeze"]
    change_classes = policy["change_classes"]

    assert plan["required_before_heavyweight_side_effects"] is True
    assert plan["changed_inputs_select_only_reachable_components"] is True
    assert plan["host_may_infer_undeclared_dependencies"] is False
    assert fallback["owner"] == "mas_executor"
    assert fallback[
        "materialize_bounded_plan_from_exact_inputs_and_canonical_role_policy"
    ] is True
    assert fallback[
        "cache_hit_allowed_without_complete_code_tool_and_configuration_closure"
    ] is False
    assert fallback["missing_graph_blocks_hosted_action_liveness"] is False
    assert change_classes["no_change"] == {
        "allowed_work": "currentness_and_cache_receipt_only",
        "heavyweight_external_invocations": 0,
        "projection_rewrites": 0,
    }
    assert change_classes["layout_only"]["analysis_or_source_generation_allowed"] is False
    assert change_classes["manuscript_only"][
        "analysis_display_workbook_or_supplement_rebuild_by_default"
    ] is False
    assert "generation_descriptor_sha256" not in preview["required_cache_key_fields"]
    assert preview[
        "whole_descriptor_sha256_is_provenance_not_component_cache_identity"
    ] is True
    assert preview["build_scope"] == "affected_components_only"
    assert preview["full_package_export_allowed"] is False
    assert preview["full_page_raster_allowed"] is False
    assert preview["formal_review_allowed"] is False
    assert freeze["required_actions"] == [
        "one_full_delivery_export",
        "one_complete_page_and_sheet_render_check",
        "one_complete_exact_byte_member_manifest",
        "one_archive_build_per_unique_tree",
        "one_parallel_review_wave_for_all_affected_lanes",
    ]
    assert freeze["projection_switch_is_outside_candidate_freeze"] is True


def test_artifact_iteration_preserves_currentness_and_owner_boundaries() -> None:
    policy = _load("contracts/artifact_iteration_efficiency_policy.json")
    review = policy["review_dispatch"]
    archive = policy["archive_and_projection"]
    observability = policy["observability"]

    assert review["dispatch_only_affected_lanes"] is True
    assert review["dispatch_affected_lanes_in_one_wave"] is True
    assert review["parallelize_independent_lanes"] is True
    assert review["reuse_requires_mas_owned_currentness_receipt"] is True
    assert review[
        "reuse_requires_identical_scope_policy_and_professional_rubric"
    ] is True
    assert review["reuse_requires_complete_origin_provenance"] is True
    assert review["reuse_requires_framework_epistemic_currentness_evaluation"] is True
    assert review[
        "reuse_requires_current_scope_id_kind_and_dependency_closure"
    ] is True
    assert review["review_scope_sha256_is_dependency_topology_locator_only"] is True
    assert review["hash_change_alone_invalidates_professional_review"] is False
    assert review[
        "semantic_change_invalidates_only_declared_dependency_lanes"
    ] is True
    assert review["fresh_receipt_requires_opl_immutable_snapshot_binding"] is True
    assert review[
        "legacy_origin_receipt_without_snapshot_binding_may_reuse_unchanged_scope"
    ] is False
    assert review[
        "fresh_missing_snapshot_binding_is_lane_quality_debt_not_host_liveness_failure"
    ] is True
    assert review["missing_or_stale_review_currentness_blocks_hosted_action"] is False
    assert review[
        "exact_byte_package_reviews_package_content_and_wrapper_inventory"
    ] is True
    assert review[
        "exact_byte_package_excludes_governance_checklist_status_and_receipt_members"
    ] is True
    page_cache = policy["page_hash_evidence_cache"]
    assert page_cache["persistent_store_owner"] == "one-person-lab"
    assert page_cache["cache_key_fields"] == [
        "ordered_page_pixel_hashes",
        "raster_contract",
        "review_scope_sha256",
        "rubric_sha256",
    ]
    assert page_cache["cache_hit_can_skip_fresh_reviewer_invocation"] is False
    assert page_cache["cache_hit_can_emit_mas_receipt_or_verdict"] is False
    assert page_cache["cache_hit_requires_fresh_mas_judgment"] is True
    assert archive["one_compression_per_unique_tree"] is True
    assert archive["projection_requires_current_mas_owner_result"] is True
    assert archive["unchanged_projection_tree_is_no_op"] is True
    assert observability["same_identity_retry_budget_per_failed_action"] == 1
    assert observability[
        "budget_exhaustion_routes_to_owner_instead_of_silent_retry"
    ] is True


def test_artifact_iteration_policy_is_packaged_and_used_by_stage_prompts() -> None:
    pack_input = _load("contracts/pack_compiler_input.json")
    policy_ref = "contracts/artifact_iteration_efficiency_policy.json"
    manuscript = (ROOT / "agent/prompts/manuscript_authoring.md").read_text(
        encoding="utf-8"
    )
    review = (ROOT / "agent/prompts/review_and_quality_gate.md").read_text(
        encoding="utf-8"
    )
    finalize = (ROOT / "agent/prompts/finalize_and_publication_handoff.md").read_text(
        encoding="utf-8"
    )
    execution = (ROOT / "agent/skills/medical_research_execution.md").read_text(
        encoding="utf-8"
    )
    normalized_manuscript = " ".join(manuscript.split())
    normalized_execution = " ".join(execution.split())

    assert policy_ref in pack_input["required_domain_pack_paths"]
    assert policy_ref in pack_input["source_refs"]["required_domain_pack_paths"]
    assert pack_input["source_refs"]["artifact_iteration_efficiency_policy_ref"] == (
        policy_ref
    )
    assert policy_ref in manuscript
    assert "missing graph metadata never blocks the hosted action" in normalized_manuscript
    assert "`reused_unchanged_scope`" in review
    assert "Dispatch all affected" in review
    assert "Treat any source, ledger" not in review
    assert "Any new bytes" not in finalize
    assert "every affected v2 review lane" in finalize
    assert policy_ref in execution
    assert "mtime alone is never currentness proof" in normalized_execution
    assert "Projection happens only after a current MAS owner" in normalized_execution


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
