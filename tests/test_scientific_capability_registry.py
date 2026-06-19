from __future__ import annotations

import importlib
import json
from pathlib import Path


def _structured_payload(result: dict[str, object]) -> dict[str, object]:
    structured = result["structuredContent"]
    assert isinstance(structured, dict)
    assert structured["surface_kind"] == "mas_tool_result_envelope"
    payload = structured["structured_payload"]
    assert isinstance(payload, dict)
    return payload


def test_scientific_capability_registry_resolves_current_delta_bound_candidates() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")

    registry = module.build_scientific_capability_registry()
    resolution = module.resolve_scientific_capabilities(
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "repair-story",
            "work_unit_fingerprint": "sha256:repair",
        }
    )

    assert registry["surface_kind"] == "mas_scientific_capability_registry"
    assert registry["default_policy"]["fail_open"] is True
    assert registry["default_policy"]["always_on_scan"] is False
    assert registry["default_policy"]["wildcard_action_triggers_auto_select"] is False
    assert (
        registry["default_policy"]["wildcard_action_triggers_require_explicit_capability_request"]
        is True
    )
    assert registry["owner_consumption_evidence_schema"][
        "standard_agent_feedback_loop_tail"
    ] == {
        "required_keys": [
            "production_generated_surface_caller_negative_samples_ref",
            "real_target_owner_accepted_answer_or_typed_blocker_scaleout_ref",
            "long_soak_negative_conformance_ref",
        ],
        "false_completion_blockers": [
            "MAS_contract_landed_without_OPL_family_consumption",
            "suite_pass_without_target_owner_receipt_or_typed_blocker",
            "hosted_consumption_packet_without_live_owner_answer",
            "domain_local_selector_or_always_on_sidecar",
        ],
        "mas_repo_can_close_opl_family_tail": False,
        "opl_hosted_runtime_consumption_required": True,
    }
    assert registry["authority_boundary"]["can_write_domain_truth"] is False
    assert registry["authority_boundary"]["can_write_owner_receipt"] is False
    capability_ids = {item["capability_id"] for item in registry["capabilities"]}
    assert {
        "external_learning_authoring_advisory",
        "evo_scientist_progress_sidecar",
        "light_external_skill_content_advisory",
        "co_scientist_current_owner_affordance",
        "nature_figure_display_contract_refs",
        "display_pack_visual_capability",
    } <= capability_ids

    selected = {item["capability_id"]: item for item in resolution["selected_capabilities"]}
    assert resolution["surface_kind"] == "mas_scientific_capability_resolution"
    assert resolution["status"] == "resolved"
    assert resolution["mainline_waits_for_capability"] is False
    assert resolution["missing_capability_blocks_owner_action"] is False
    assert selected["external_learning_authoring_advisory"]["invocation_kind"] == (
        "external_learning_sidecar"
    )
    assert selected["co_scientist_current_owner_affordance"]["invocation_kind"] == (
        "descriptor_only_current_owner_input_refs"
    )
    assert all(item["refs_only"] is True for item in selected.values())
    assert all(item["can_block_current_owner_action"] is False for item in selected.values())
    wildcard_capabilities = {
        item["capability_id"]: item
        for item in registry["capabilities"]
        if "*" in item["action_triggers"]
    }
    assert wildcard_capabilities["evo_scientist_progress_sidecar"][
        "wildcard_action_trigger_policy"
    ] == {
        "auto_select": False,
        "requires_explicit_capability_request": True,
        "reason": "support_or_diagnostic_wildcards_must_not_become_mas_private_selectors",
    }


def test_scientific_capability_registry_wildcard_sidecars_require_explicit_capability_request() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")

    implicit_resolution = module.resolve_scientific_capabilities(
        current_owner_delta={
            "action_type": "unknown_owner_action",
            "work_unit_id": "unknown-work",
        }
    )
    implicit_ids = {
        item["capability_id"]
        for item in implicit_resolution["selected_capabilities"]
    }

    assert implicit_resolution["status"] == "no_matching_capability"
    assert "evo_scientist_progress_sidecar" not in implicit_ids
    assert "light_external_skill_content_advisory" not in implicit_ids
    assert implicit_resolution["authority_boundary"]["can_authorize_owner_action"] is False

    explicit_family_resolution = module.resolve_scientific_capabilities(
        current_owner_delta={
            "action_type": "unknown_owner_action",
            "capability_families": ["progress_accelerator"],
            "work_unit_id": "unknown-work",
        }
    )
    explicit_family_ids = {
        item["capability_id"]: item
        for item in explicit_family_resolution["selected_capabilities"]
    }
    assert "evo_scientist_progress_sidecar" in explicit_family_ids
    assert explicit_family_ids["evo_scientist_progress_sidecar"][
        "wildcard_action_trigger_policy"
    ] == {
        "auto_select": False,
        "requires_explicit_capability_request": True,
        "reason": "support_or_diagnostic_wildcards_must_not_become_mas_private_selectors",
    }

    explicit_id_resolution = module.resolve_scientific_capabilities(
        current_owner_delta={
            "action_type": "unknown_owner_action",
            "capability_families": ["light_external_skill_content_advisory"],
            "work_unit_id": "unknown-work",
        }
    )
    explicit_id_ids = {
        item["capability_id"]: item
        for item in explicit_id_resolution["selected_capabilities"]
    }
    assert "light_external_skill_content_advisory" in explicit_id_ids
    assert explicit_id_ids["light_external_skill_content_advisory"][
        "wildcard_action_trigger_policy"
    ] == {
        "auto_select": False,
        "requires_explicit_capability_request": True,
        "reason": "support_or_diagnostic_wildcards_must_not_become_mas_private_selectors",
    }


def test_scientific_capability_registry_resolves_nature_figure_display_refs_only_descriptor(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    current_owner_delta = {
        "action_type": "prepare_manuscript_visual_package",
        "action_id": "display-delta-001",
        "owner": "display",
        "work_unit_id": "figure-display-router",
        "work_unit_fingerprint": "sha256:display-router",
        "declared_needs": [
            "figure router refs",
            "display manifest refs",
            "stable plotting need",
        ],
    }

    resolution = module.resolve_scientific_capabilities(
        current_owner_delta=current_owner_delta,
    )
    selected = {
        item["capability_id"]: item
        for item in resolution["selected_capabilities"]
    }
    candidate = selected["nature_figure_display_contract_refs"]

    assert candidate["capability_family"] == "figure_display_contract_refs"
    assert candidate["invocation_kind"] == "descriptor_only_current_owner_input_refs"
    assert candidate["trigger_reason"] == "current_delta_declared_figure_display_need"
    assert candidate["refs_only"] is True
    assert candidate["descriptor_only"] is True
    assert candidate["external_runner_invocation_allowed"] is False
    assert candidate["can_block_current_owner_action"] is False
    assert candidate["authority_boundary"]["can_write_publication_eval"] is False
    assert candidate["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert {
        "external:nature-skills@1cb9070fdd94929d5f267ce6585ac87e2cba60b3:skills/nature-figure/SKILL.md",
        "external:nature-skills@1cb9070fdd94929d5f267ce6585ac87e2cba60b3:skills/nature-figure/manifest.yaml",
        "external:nature-skills@1cb9070fdd94929d5f267ce6585ac87e2cba60b3:skills/nature-figure/references/figure-contract.md",
        "external:nature-skills@1cb9070fdd94929d5f267ce6585ac87e2cba60b3:skills/nature-figure/references/qa-contract.md",
        "external:nature-skills@1cb9070fdd94929d5f267ce6585ac87e2cba60b3:skills/nature-figure/references/backend-selection.md",
    } == set(candidate["contract_refs"])
    assert candidate["readback"] == {
        "surface_kind": "mas_scientific_capability_readback",
        "capability_id": "nature_figure_display_contract_refs",
        "invocation_kind": "descriptor_only_current_owner_input_refs",
        "descriptor_only": True,
        "refs_only": True,
        "request_only": False,
        "can_execute_external_runner": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_quality_verdict": False,
        "contract_refs": candidate["contract_refs"],
    }

    invocation = module.invoke_scientific_capability(
        capability_id="nature_figure_display_contract_refs",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )

    assert invocation["surface_kind"] == "mas_scientific_capability_invocation"
    assert invocation["status"] == "descriptor_only"
    assert invocation["refs_only"] is True
    assert invocation["request_only"] is False
    assert invocation["descriptor_only"] is True
    assert invocation["mas_local_capability_actuator"] is False
    assert invocation["external_runner_invocation_allowed"] is False
    assert invocation["opl_capability_runtime_required"] is False
    assert invocation["authority_boundary"]["can_write_publication_eval"] is False
    assert invocation["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert invocation["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert invocation["result"]["surface_kind"] == (
        "mas_scientific_capability_descriptor_only_projection"
    )
    assert invocation["result"]["contract_refs"] == candidate["contract_refs"]
    assert invocation["result"]["readback"]["can_execute_external_runner"] is False
    request = invocation["opl_capability_invocation_request"]
    assert request["mas_can_run_capability_actuator"] is False
    assert request["expected_output_refs"] == candidate["contract_refs"]
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_does_not_treat_generic_manifest_as_nature_figure_need() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")

    resolution = module.resolve_scientific_capabilities(
        current_owner_delta={
            "action_type": "prepare_manifest_router",
            "declared_needs": ["router refs", "manifest refs"],
            "work_unit_id": "generic-router-manifest",
        },
    )

    selected_ids = {
        item["capability_id"]
        for item in resolution["selected_capabilities"]
    }
    assert "nature_figure_display_contract_refs" not in selected_ids


def test_scientific_capability_registry_resolves_nature_paper_mainline_refs_only_descriptors(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    current_owner_delta = {
        "action_type": "paper_mainline_owner_action",
        "action_id": "paper-mainline-001",
        "work_unit_id": "paper-mainline",
        "work_unit_fingerprint": "sha256:paper-mainline",
        "paper_need": [
            "section source map",
            "claim citation support",
            "reviewer repair action candidates",
        ],
        "requested_refs": [
            "draft_block_refs",
            "claim_refs",
            "evidence_refs",
            "source_map_refs",
            "citation_refs",
            "support_grade",
            "reviewer_repair_refs",
        ],
    }

    resolution = module.resolve_scientific_capabilities(
        current_owner_delta=current_owner_delta,
    )
    selected = {
        item["capability_id"]: item
        for item in resolution["selected_capabilities"]
    }
    expected_ids = {
        "nature_paper_section_source_map_readback": (
            "paper_mainline_section_source_map",
            "current_delta_declared_paper_mainline_section_need",
            "med_autoscience.paper_mainline_section_source_map.build_paper_section_source_map_readback",
            "readback:mas_paper_section_source_map_readback",
        ),
        "nature_claim_citation_support_matrix": (
            "claim_citation_support_matrix",
            "current_delta_declared_claim_support_need",
            "med_autoscience.paper_mainline_claim_support.build_claim_citation_support_matrix",
            "readback:mas_claim_citation_support_matrix",
        ),
        "nature_reviewer_repair_action_projection": (
            "reviewer_repair_action_projection",
            "current_delta_declared_reviewer_repair_need",
            "med_autoscience.paper_mainline_reviewer_repair.build_reviewer_repair_action_projection",
            "readback:mas_reviewer_repair_action_projection",
        ),
    }

    assert set(expected_ids) <= set(selected)
    for capability_id, (
        capability_family,
        trigger_reason,
        callable_surface,
        output_ref,
    ) in expected_ids.items():
        candidate = selected[capability_id]
        assert candidate["capability_family"] == capability_family
        assert candidate["trigger_reason"] == trigger_reason
        assert candidate["callable_surface"] == callable_surface
        assert candidate["output_refs"] == [output_ref]
        assert candidate["invocation_kind"] == "descriptor_only_current_owner_input_refs"
        assert candidate["refs_only"] is True
        assert candidate["descriptor_only"] is True
        assert candidate["external_runner_invocation_allowed"] is False
        assert candidate["can_block_current_owner_action"] is False
        assert candidate["readback"]["can_execute_external_runner"] is False
        assert candidate["readback"]["can_authorize_quality_verdict"] is False
        assert candidate["authority_boundary"]["can_write_publication_eval"] is False
        assert candidate["authority_boundary"]["can_authorize_publication_readiness"] is False

        invocation = module.invoke_scientific_capability(
            capability_id=capability_id,
            study_root=study_root,
            current_owner_delta=current_owner_delta,
            apply=True,
        )
        assert invocation["status"] == "descriptor_only"
        assert invocation["refs_only"] is True
        assert invocation["request_only"] is False
        assert invocation["descriptor_only"] is True
        assert invocation["external_runner_invocation_allowed"] is False
        assert invocation["opl_capability_runtime_required"] is False
        assert invocation["result"]["surface_kind"] == (
            "mas_scientific_capability_descriptor_only_projection"
        )
        assert invocation["result"]["readback"]["can_execute_external_runner"] is False
        assert invocation["authority_boundary"]["can_write_publication_eval"] is False

    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_invokes_external_learning_as_opl_request_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"

    result = module.invoke_scientific_capability(
        capability_id="external_learning_authoring_advisory",
        study_root=study_root,
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "action_id": "dispatch-001",
            "owner_route": {
                "owner": "quality_repair_batch",
                "work_unit_id": "repair-story",
                "work_unit_fingerprint": "sha256:repair",
            },
        },
        apply=True,
    )

    result_path = study_root / "artifacts/advisory/external_learning_sidecar/latest.json"
    assert result["surface_kind"] == "mas_scientific_capability_invocation"
    assert result["status"] == "opl_capability_request_pending"
    assert result["refs_only"] is True
    assert result["request_only"] is True
    assert result["mas_local_capability_actuator"] is False
    assert result["mas_can_invoke_capability_sidecar"] is False
    assert result["opl_capability_runtime_required"] is True
    assert result["mainline_waits_for_capability"] is False
    assert result["authority_boundary"]["can_write_publication_eval"] is False
    request = result["opl_capability_invocation_request"]
    assert request["surface_kind"] == "mas_opl_capability_invocation_request"
    assert request["target_runtime_owner"] == "one-person-lab"
    assert request["target_runtime_kind"] == "CapabilityRegistry"
    assert request["mas_can_run_capability_actuator"] is False
    assert result["result"]["surface_kind"] == "mas_scientific_capability_invocation_request_projection"
    assert not result_path.exists()
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()


def test_scientific_capability_registry_builds_nonblocking_consumption_evidence_without_owner_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    invocation = module.invoke_scientific_capability(
        capability_id="external_learning_authoring_advisory",
        study_root=study_root,
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "action_id": "dispatch-001",
            "work_unit_id": "repair-story",
            "work_unit_fingerprint": "sha256:repair",
            "source_ref": "artifacts/controller_decisions/latest.json",
        },
        apply=True,
    )

    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "action_id": "dispatch-001",
            "work_unit_id": "repair-story",
            "work_unit_fingerprint": "sha256:repair",
            "source_ref": "artifacts/controller_decisions/latest.json",
        },
    )

    assert evidence["surface_kind"] == "mas_scientific_capability_owner_consumption_evidence"
    assert evidence["schema_version"] == 1
    assert evidence["refs_only"] is True
    assert evidence["capability_id"] == "external_learning_authoring_advisory"
    assert evidence["output_refs"] == ["artifacts/advisory/external_learning_sidecar/latest.json"]
    assert evidence["current_owner_delta_identity"] == {
        "action_type": "run_quality_repair_batch",
        "action_id": "dispatch-001",
        "owner": "",
        "work_unit_id": "repair-story",
        "work_unit_fingerprint": "sha256:repair",
        "source_ref": "artifacts/controller_decisions/latest.json",
    }
    assert evidence["owner_consumption_status"] == "no_owner_response_refs"
    assert evidence["owner_receipt_ref"] is None
    assert evidence["typed_blocker_ref"] is None
    assert evidence["reviewer_receipt_ref"] is None
    assert evidence["route_back_evidence_ref"] is None
    assert evidence["counts_as_progress"] is False
    assert evidence["can_authorize_owner_action"] is False
    assert evidence["mainline_waits_for_owner_consumption"] is False
    assert evidence["fail_open"] is True
    assert evidence["missing_owner_response_refs_blocks"] is False
    tail = evidence["standard_agent_feedback_loop_tail"]
    assert tail["surface_kind"] == "mas_standard_agent_feedback_loop_tail_evidence"
    assert tail["repo_side_shape_landed"] is True
    assert tail["owner_answer_or_typed_blocker_observed"] is False
    assert tail["real_target_owner_accepted_answer_or_typed_blocker_scaleout_ref"] is None
    assert tail["production_generated_surface_caller_negative_samples_ref"] is None
    assert tail["long_soak_negative_conformance_ref"] is None
    assert tail["missing_external_tail_keys"] == [
        "production_generated_surface_caller_negative_samples_ref",
        "real_target_owner_accepted_answer_or_typed_blocker_scaleout_ref",
        "long_soak_negative_conformance_ref",
    ]
    assert "MAS_contract_landed_without_OPL_family_consumption" in tail[
        "false_completion_blockers"
    ]
    assert tail["mas_repo_can_close_opl_family_tail"] is False
    assert tail["opl_hosted_runtime_consumption_required"] is True
    assert tail["counts_as_opl_family_completion"] is False
    assert evidence["no_forbidden_write_proof"]["forbidden_refs_absent"] is True
    assert evidence["no_forbidden_write_proof"]["checked_relative_refs"] == [
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
        "paper",
        "package",
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
    ]
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()


def test_scientific_capability_registry_consumption_evidence_with_owner_refs_stays_non_authorizing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    invocation = module.invoke_scientific_capability(
        capability_id="external_learning_review_and_progress_advisory",
        study_root=study_root,
        current_owner_delta={
            "action_type": "unit_harmonized_external_validation_rerun",
            "action_id": "dispatch-002",
            "owner": "MedAutoScience",
            "work_unit_id": "external-validation",
            "work_unit_fingerprint": "sha256:external-validation",
            "source_ref": "projection/current_owner_delta.json",
        },
        apply=True,
    )

    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta={
            "action_type": "unit_harmonized_external_validation_rerun",
            "action_id": "dispatch-002",
            "owner": "MedAutoScience",
            "work_unit_id": "external-validation",
            "work_unit_fingerprint": "sha256:external-validation",
            "source_ref": "projection/current_owner_delta.json",
        },
        owner_response_refs={
            "owner_receipt_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
            "reviewer_receipt_ref": "artifacts/reviewer/receipt.json",
            "route_back_evidence_ref": "artifacts/routes/route-back.json",
        },
    )

    assert evidence["owner_consumption_status"] == "owner_response_refs_observed"
    assert evidence["owner_receipt_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json"
    )
    assert evidence["typed_blocker_ref"] is None
    assert evidence["reviewer_receipt_ref"] == "artifacts/reviewer/receipt.json"
    assert evidence["route_back_evidence_ref"] == "artifacts/routes/route-back.json"
    assert evidence["counts_as_progress"] is False
    assert evidence["consumption_evidence_only"] is True
    tail = evidence["standard_agent_feedback_loop_tail"]
    assert tail["owner_answer_or_typed_blocker_observed"] is True
    assert tail["real_target_owner_accepted_answer_or_typed_blocker_scaleout_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json"
    )
    assert tail["observed_owner_response_refs"] == [
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
        "artifacts/reviewer/receipt.json",
        "artifacts/routes/route-back.json",
    ]
    assert tail["missing_external_tail_keys"] == [
        "production_generated_surface_caller_negative_samples_ref",
        "long_soak_negative_conformance_ref",
    ]
    assert tail["counts_as_opl_family_completion"] is False
    assert evidence["authority_boundary"]["can_write_owner_receipt"] is False
    assert evidence["authority_boundary"]["can_write_typed_blocker"] is False
    assert evidence["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert evidence["no_forbidden_write_proof"]["forbidden_refs_absent"] is True
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()


def test_scientific_capability_registry_requests_light_and_evo_without_mas_actuator(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    light = module.invoke_scientific_capability(
        capability_id="light_external_skill_content_advisory",
        study_root=study_root,
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "study_id": "001-risk",
            "work_unit_id": "repair-story",
            "source_refs": ["study.yaml"],
        },
        payload={
            "fresh_evidence_gate": {"claim_supported": True},
            "argument_review_hint": {"claim_boundary_state": "bounded"},
        },
        apply=True,
    )
    evo = module.invoke_scientific_capability(
        capability_id="evo_scientist_progress_sidecar",
        study_root=study_root,
        current_owner_delta={
            "action_type": "run_quality_repair_batch",
            "study_id": "001-risk",
            "source_ref": "artifacts/controller_decisions/latest.json",
            "work_unit_id": "repair-story",
        },
        payload={"executor_turn_summary_ref": "artifacts/executor/turn.json"},
        apply=True,
    )

    assert light["status"] == "opl_capability_request_pending"
    assert light["mas_local_capability_actuator"] is False
    assert light["result"]["surface_kind"] == "mas_scientific_capability_invocation_request_projection"
    assert light["opl_capability_invocation_request"]["expected_output_refs"] == [
        "artifacts/stage_outputs/<stage>/advisory/light_external_pattern_refs.json"
    ]
    assert not (
        study_root
        / "artifacts/stage_outputs/current_owner_action/advisory/light_external_pattern_refs.json"
    ).exists()
    assert evo["status"] == "opl_capability_request_pending"
    assert evo["mas_local_capability_actuator"] is False
    assert evo["result"]["surface_kind"] == "mas_scientific_capability_invocation_request_projection"
    assert evo["opl_capability_invocation_request"]["expected_output_refs"] == [
        "artifacts/runtime/evo_scientist_sidecar/latest.json"
    ]
    assert not (study_root / "artifacts/runtime/evo_scientist_sidecar/latest.json").exists()
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()


def test_scientific_capability_registry_mcp_modes_and_tool_arsenal_card(
    tmp_path: Path,
) -> None:
    mcp = importlib.import_module("med_autoscience.mcp_server")
    arsenal_module = importlib.import_module("med_autoscience.agent_tool_arsenal")
    tools = {tool["name"]: tool for tool in mcp.build_tool_manifest()}

    assert "scientific_capability_registry" in tools
    assert tools["scientific_capability_registry"]["inputSchema"]["properties"]["mode"]["enum"] == [
        "index",
        "resolve",
        "invoke",
    ]

    resolve_result = mcp.call_tool(
        "scientific_capability_registry",
        {
            "mode": "resolve",
            "current_owner_delta": {
                "action_type": "unit_harmonized_external_validation_rerun",
                "work_unit_id": "external-validation",
            },
        },
    )
    assert resolve_result["isError"] is False
    resolve_envelope = resolve_result["structuredContent"]
    assert resolve_envelope["surface_kind"] == "mas_tool_result_envelope"
    assert resolve_envelope["tool_id"] == "scientific_capability_registry"
    assert resolve_envelope["tool_mode"] == "resolve"
    assert resolve_envelope["status"] == "succeeded"
    assert resolve_envelope["authority_boundary"]["tool_result_envelope_is_authority_outcome"] is False
    assert resolve_envelope["authority_boundary"]["can_write_domain_truth"] is False
    assert resolve_envelope["authority_boundary"]["can_authorize_publication_quality"] is False
    assert "publication_quality" in resolve_envelope["audit_trail"]["forbidden_authority"]
    resolve_payload = resolve_envelope["structured_payload"]
    assert resolve_payload["surface_kind"] == "mas_scientific_capability_resolution"
    selected = {
        item["capability_id"]
        for item in resolve_payload["selected_capabilities"]
    }
    assert "external_learning_review_and_progress_advisory" in selected

    invoke_result = mcp.call_tool(
        "scientific_capability_registry",
        {
            "mode": "invoke",
            "capability_id": "external_learning_review_and_progress_advisory",
            "study_root": str(tmp_path / "studies" / "001-risk"),
            "current_owner_delta": {
                "action_type": "unit_harmonized_external_validation_rerun",
                "action_id": "dispatch-001",
                "owner_route": {
                    "owner": "source_truth",
                    "work_unit_id": "external-validation",
                    "work_unit_fingerprint": "sha256:external-validation",
                },
            },
        },
    )
    assert invoke_result["isError"] is False
    invoke_envelope = invoke_result["structuredContent"]
    assert invoke_envelope["surface_kind"] == "mas_tool_result_envelope"
    assert invoke_envelope["tool_id"] == "scientific_capability_registry"
    assert invoke_envelope["tool_mode"] == "invoke"
    assert invoke_envelope["audit_trail"]["authority_flags"]["readOnlyHint"] is False
    assert invoke_envelope["audit_trail"]["authority_flags"]["destructiveHint"] is False
    assert (
        "artifacts/advisory/external_learning_sidecar/latest.json"
        in invoke_envelope["audit_trail"]["allowed_write_refs"]
    )
    assert invoke_envelope["authority_boundary"]["can_write_domain_truth"] is False
    assert invoke_envelope["authority_boundary"]["can_authorize_submission_readiness"] is False
    assert invoke_envelope["structured_payload"]["surface_kind"] == (
        "mas_scientific_capability_invocation"
    )
    assert invoke_envelope["structured_payload"]["status"] == "opl_capability_request_pending"
    assert invoke_envelope["structured_payload"]["mas_local_capability_actuator"] is False

    arsenal = arsenal_module.build_agent_tool_arsenal_index()
    assert arsenal["scientific_capability_registry"]["surface_kind"] == (
        "mas_scientific_capability_registry"
    )
    plan = arsenal_module.build_capability_invocation_plan(
        current_owner_delta={
            "action_type": "scientific_capability_registry",
            "source_ref": "artifacts/controller_decisions/latest.json",
        },
        arsenal=arsenal,
    )
    assert plan["selected_card_kind"] == "action_catalog"
    assert plan["selected_tool_id"] == "scientific_capability_registry"
    assert plan["authority_boundary"]["can_write_domain_truth"] is False


def test_scientific_capability_registry_cli_modes_emit_json(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "studies" / "001-risk"

    exit_code = cli.main(["scientific-capability-registry", "--mode", "index"])
    assert exit_code == 0
    index_payload = json.loads(capsys.readouterr().out)
    assert index_payload["surface_kind"] == "mas_scientific_capability_registry"
    assert index_payload["default_policy"]["fail_open"] is True

    exit_code = cli.main(
        [
            "scientific-capability-registry",
            "--mode",
            "resolve",
            "--current-owner-delta-json",
            json.dumps({"action_type": "run_quality_repair_batch"}),
        ]
    )
    assert exit_code == 0
    resolve_payload = json.loads(capsys.readouterr().out)
    assert resolve_payload["surface_kind"] == "mas_scientific_capability_resolution"
    assert resolve_payload["status"] == "resolved"

    exit_code = cli.main(
        [
            "scientific-capability-registry",
            "--mode",
            "invoke",
            "--capability-id",
            "external_learning_authoring_advisory",
            "--study-root",
            str(study_root),
            "--current-owner-delta-json",
            json.dumps(
                {
                    "action_type": "run_quality_repair_batch",
                    "owner_route": {
                        "owner": "quality_repair_batch",
                        "work_unit_id": "repair-story",
                        "work_unit_fingerprint": "sha256:repair",
                    },
                }
            ),
            "--apply",
        ]
    )
    assert exit_code == 0
    invoke_payload = json.loads(capsys.readouterr().out)
    assert invoke_payload["surface_kind"] == "mas_scientific_capability_invocation"
    assert invoke_payload["refs_only"] is True
    assert invoke_payload["status"] == "opl_capability_request_pending"
    assert invoke_payload["mas_local_capability_actuator"] is False
    assert not (study_root / "artifacts/advisory/external_learning_sidecar/latest.json").exists()

    exit_code = cli.main(
        [
            "scientific-capability-registry",
            "--mode",
            "resolve",
            "--current-owner-delta-json",
            json.dumps(
                {
                    "action_type": "prepare_manuscript_visual_package",
                    "declared_needs": ["figure router", "display manifest"],
                }
            ),
        ]
    )
    assert exit_code == 0
    nature_resolve_payload = json.loads(capsys.readouterr().out)
    nature_selected = {
        item["capability_id"]: item
        for item in nature_resolve_payload["selected_capabilities"]
    }
    assert nature_selected["nature_figure_display_contract_refs"]["readback"][
        "descriptor_only"
    ] is True
    assert nature_selected["nature_figure_display_contract_refs"]["readback"][
        "can_execute_external_runner"
    ] is False

    exit_code = cli.main(
        [
            "scientific-capability-registry",
            "--mode",
            "invoke",
            "--capability-id",
            "nature_figure_display_contract_refs",
            "--study-root",
            str(study_root),
            "--current-owner-delta-json",
            json.dumps(
                {
                    "action_type": "prepare_manuscript_visual_package",
                    "declared_needs": ["stable plotting need"],
                }
            ),
            "--apply",
        ]
    )
    assert exit_code == 0
    nature_invoke_payload = json.loads(capsys.readouterr().out)
    assert nature_invoke_payload["status"] == "descriptor_only"
    assert nature_invoke_payload["request_only"] is False
    assert nature_invoke_payload["result"]["readback"]["descriptor_only"] is True
    assert nature_invoke_payload["result"]["readback"][
        "can_authorize_publication_readiness"
    ] is False
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
