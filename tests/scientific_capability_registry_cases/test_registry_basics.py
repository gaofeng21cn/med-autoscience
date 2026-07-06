from __future__ import annotations

from .common import (
    SCHOLARSKILLS_MODULE_IDS,
    SCHOLARSKILLS_RECEIPT_REF_KEYS_BY_MODULE,
    _structured_payload,
    _write_tables_materialized_package,
    importlib,
    json,
    Path,
)


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
    assert registry["authority_boundary"]["can_authorize_provider_admission"] is False
    assert registry["authority_boundary"]["capability_or_sidecar_can_be_admission_gate"] is False
    assert registry["authority_boundary"]["missing_capability_blocks_owner_action"] is False
    assert registry["authority_boundary"]["failed_capability_blocks_owner_action"] is False
    assert registry["authority_boundary"]["low_confidence_capability_blocks_owner_action"] is False
    assert registry["authority_boundary"]["sidecar_completion_required_for_stage_closeout"] is False
    capability_ids = {item["capability_id"] for item in registry["capabilities"]}
    assert {
        "external_learning_authoring_advisory",
        "evo_scientist_progress_sidecar",
        "light_external_skill_content_advisory",
        "co_scientist_current_owner_affordance",
        "reviewer_revision_feedbackops_oma_work_order",
        "nature_figure_display_contract_refs",
        "display_pack_visual_capability",
    } <= capability_ids

    selected = {item["capability_id"]: item for item in resolution["selected_capabilities"]}
    assert resolution["surface_kind"] == "mas_scientific_capability_resolution"
    assert resolution["status"] == "resolved"
    assert resolution["mainline_waits_for_capability"] is False
    assert resolution["missing_capability_blocks_owner_action"] is False
    assert resolution["authority_boundary"]["can_authorize_provider_admission"] is False
    assert resolution["authority_boundary"]["capability_or_sidecar_can_be_admission_gate"] is False
    assert resolution["authority_boundary"]["sidecar_completion_required_for_stage_closeout"] is False
    assert selected["external_learning_authoring_advisory"]["invocation_kind"] == (
        "external_learning_sidecar"
    )
    assert selected["co_scientist_current_owner_affordance"]["invocation_kind"] == (
        "descriptor_only_current_owner_input_refs"
    )
    assert all(item["refs_only"] is True for item in selected.values())
    assert all(item["can_block_current_owner_action"] is False for item in selected.values())
    assert all(
        item["authority_boundary"]["can_authorize_provider_admission"] is False
        for item in selected.values()
    )
    assert all(
        item["authority_boundary"]["capability_or_sidecar_can_be_admission_gate"] is False
        for item in selected.values()
    )
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


def test_registry_resolves_reviewer_revision_feedbackops_oma_descriptor() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")

    resolution = module.resolve_scientific_capabilities(
        current_owner_delta={
            "action_type": "reviewer_revision",
            "task_intent": "Major revision with OMA FeedbackOps coverage audit requirement.",
        }
    )

    selected = {item["capability_id"]: item for item in resolution["selected_capabilities"]}
    capability = selected["reviewer_revision_feedbackops_oma_work_order"]
    assert capability["capability_family"] == "feedbackops_oma_work_order"
    assert capability["invocation_kind"] == "descriptor_only_current_owner_input_refs"
    assert capability["descriptor_only"] is True
    assert capability["external_runner_invocation_allowed"] is False
    assert "candidate:reviewer_revision_coverage_audit_ref" in capability["output_refs"]
    assert "candidate:stage_attempt_readback_ref" in capability["output_refs"]
    assert capability["authority_boundary"]["can_write_domain_truth"] is False
    assert capability["authority_boundary"]["can_write_owner_receipt"] is False


def test_scholarskills_registry_declares_workspace_local_install_boundary() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    install_readback = importlib.import_module("med_autoscience.scholarskills_local_install")

    registry = module.build_scientific_capability_registry()
    capabilities = {item["capability_id"]: item for item in registry["capabilities"]}
    candidate = capabilities["mas-scholar-skills.write"]

    assert registry["scholarskills_local_install"]["install_owner"] == "one-person-lab"
    assert registry["scholarskills_local_install"]["synced_skill_ids"] == list(
        install_readback.SCHOLARSKILLS_DEFAULT_SKILL_IDS
    )
    assert registry["scholarskills_local_install"]["optional_skill_ids"] == list(
        install_readback.SCHOLARSKILLS_OPTIONAL_SKILL_IDS
    )
    assert "medical-rebuttal-strategy" in registry["scholarskills_local_install"]["optional_skill_ids"]
    assert "medical-rebuttal-strategy" not in registry["scholarskills_local_install"]["synced_skill_ids"]
    assert registry["scholarskills_local_install"]["optional_skill_policy"] == {
        "surface": "optional_medical_method_specialist_skills",
        "source_repo_ref": "external:mas-scholar-skills",
        "source_contract_ref": (
            "external:mas-scholar-skills/contracts/"
            "scholar-skills-capability-modules.json#/medical_method_specialist_pack_policy"
        ),
        "materialization_owner": "one-person-lab",
        "sync_path": "opl_connect_source_materialization",
        "refs_only": True,
        "body_included": False,
        "default_core": False,
        "missing_optional_skills_block_mas_ordinary_progress": False,
        "writes_authority": False,
    }
    assert registry["scholarskills_local_install"]["workspace"]["sync_command_template"]["argv"] == [
        "opl",
        "connect",
        "sync-skills",
        "--domain",
        "mas-scholar-skills",
        "--scope",
        "workspace",
        "--target-workspace",
        "<workspace_root>",
        "--json",
    ]
    assert registry["scholarskills_local_install"]["workspace"]["target_skill_path_template"] == (
        "<workspace_root>/.codex/skills/mas-scholar-skills"
    )
    assert registry["scholarskills_local_install"]["workspace"]["target_skill_path_templates"][
        "medical-data-governance"
    ] == "<workspace_root>/.codex/skills/medical-data-governance"
    assert registry["scholarskills_local_install"]["workspace"]["target_skill_path_templates"][
        "medical-figure-style"
    ] == "<workspace_root>/.codex/skills/medical-figure-style"
    assert registry["scholarskills_local_install"]["workspace"]["target_skill_path_templates"][
        "medical-figure-composer"
    ] == "<workspace_root>/.codex/skills/medical-figure-composer"
    assert registry["scholarskills_local_install"]["workspace"]["optional_target_skill_path_templates"][
        "medical-rebuttal-strategy"
    ] == "<workspace_root>/.codex/skills/medical-rebuttal-strategy"
    assert (
        "medical-rebuttal-strategy"
        not in registry["scholarskills_local_install"]["workspace"]["target_skill_path_templates"]
    )
    assert registry["scholarskills_local_install"]["quest"]["sync_command_template"]["argv"] == [
        "opl",
        "connect",
        "sync-skills",
        "--domain",
        "mas-scholar-skills",
        "--scope",
        "quest",
        "--target-quest",
        "<quest_root>",
        "--json",
    ]
    assert registry["scholarskills_local_install"]["quest"]["target_skill_path_template"] == (
        "<quest_root>/.codex/skills/mas-scholar-skills"
    )
    assert registry["scholarskills_local_install"]["quest"]["target_skill_path_templates"][
        "medical-statistical-review"
    ] == "<quest_root>/.codex/skills/medical-statistical-review"
    assert registry["scholarskills_local_install"]["quest"]["optional_target_skill_path_templates"][
        "medical-survival-analysis-plan"
    ] == "<quest_root>/.codex/skills/medical-survival-analysis-plan"
    assert registry["scholarskills_local_install"]["mas_program_repo_plugin_is_execution_source"] is False
    assert registry["scholarskills_local_install"]["source_repo_ref"] == "external:mas-scholar-skills"

    assert candidate["source_repo_ref"] == "external:mas-scholar-skills"
    assert candidate["local_install"]["install_scopes"] == ["workspace", "quest"]
    assert candidate["local_install"]["mas_program_repo_plugin_is_execution_source"] is False
    assert candidate["local_install"]["workspace"]["target_skill_path_template"] == (
        "<workspace_root>/.codex/skills/mas-scholar-skills"
    )
    assert "readback:mas_scholarskills_local_install" in candidate["descriptor_refs"]
    assert "external:mas-scholar-skills" in candidate["source_frameworks"]
    assert candidate["owner_consumption_boundary"]["owner_gated_refs_consumption"] is True
    assert candidate["owner_consumption_boundary"]["counts_as_paper_truth"] is False


def test_scholarskills_registry_summary_uses_active_mas_scholar_skill_ids() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")

    summary = module.build_scientific_capability_registry_summary()

    assert set(SCHOLARSKILLS_MODULE_IDS) <= set(summary["capability_ids"])
    assert "mas-scholar-skills.data" in summary["capability_ids"]
    assert "opl.scholarskills.data" not in summary["capability_ids"]


def test_academicforge_claude_science_skills_are_descriptor_only_and_fail_open() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")

    registry = module.build_scientific_capability_registry()
    capabilities = {item["capability_id"]: item for item in registry["capabilities"]}
    expected_ids = {
        "academicforge_claude_science_skill_first_pack",
        "academicforge_life_science_specialist_skills",
        "academicforge_scientific_compute_runner_skill",
    }

    assert expected_ids <= set(capabilities)
    for capability_id in expected_ids:
        capability = capabilities[capability_id]
        assert capability["invocation_kind"] == "descriptor_only_current_owner_input_refs"
        assert capability["descriptor_only"] is True
        assert capability["refs_only"] is True
        assert capability["fail_open"] is True
        assert capability["mainline_waits_for_capability"] is False
        assert capability["external_runtime_dependency"] is False
        assert capability["external_runner_invocation_allowed"] is False
        assert capability["authority_boundary"]["can_write_domain_truth"] is False
        assert capability["authority_boundary"]["can_write_owner_receipt"] is False
        assert (
            capability["authority_boundary"]["capability_or_sidecar_can_be_admission_gate"]
            is False
        )
    assert "figure-style/SKILL.md" in " ".join(
        capabilities["academicforge_claude_science_skill_first_pack"]["descriptor_refs"]
    )
    assert "scientific-compute-runner/SKILL.md" in " ".join(
        capabilities["academicforge_scientific_compute_runner_skill"]["descriptor_refs"]
    )

    resolution = module.resolve_scientific_capabilities(
        current_owner_delta={
            "action_type": "analysis_specialist_evidence_required",
            "capability_families": [
                "life_science_specialist_skill_pack",
                "scientific_compute_runner",
            ],
            "requested_refs": ["single-cell", "remote compute", "model endpoint"],
        }
    )
    selected = {item["capability_id"]: item for item in resolution["selected_capabilities"]}
    assert {
        "academicforge_life_science_specialist_skills",
        "academicforge_scientific_compute_runner_skill",
    } <= set(selected)
    for item in selected.values():
        assert item["can_block_current_owner_action"] is False
        assert item["readback"]["can_execute_external_runner"] is False


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


def test_scientific_capability_registry_exposes_openscience_provenance_advisory(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    current_owner_delta = {
        "action_type": "artifact_provenance_review",
        "action_id": "openscience-001",
        "owner": "artifact_authority",
        "work_unit_id": "figure-provenance",
        "work_unit_fingerprint": "sha256:openscience",
        "declared_needs": [
            "artifact graph",
            "claim warning",
            "annotation regeneration",
            "project ledger",
            "connector provenance",
            "data flow refs",
        ],
    }

    registry = module.build_scientific_capability_registry()
    summary = module.build_scientific_capability_registry_summary()
    inventory = module.build_scientific_capability_registry_inventory()
    capabilities = {item["capability_id"]: item for item in registry["capabilities"]}
    capability = capabilities["openscience_artifact_provenance_advisory"]

    assert "openscience_artifact_provenance_advisory" in summary["capability_ids"]
    inventory_item = {
        item["capability_id"]: item for item in inventory["inventory"]
    }["openscience_artifact_provenance_advisory"]
    assert inventory_item["capability_family"] == "workspace_provenance_advisory"
    assert inventory_item["source_frameworks"] == [
        "ai4s-research/open-science@2200ad2ec4e2ac7c7ff59c5dcdfaeb0b9a5fda66",
        "OpenScience@2200ad2",
    ]
    assert capability["callable_surface"] == (
        "external_learning_sidecar.run_external_learning_sidecar"
    )
    assert capability["output_refs"] == [
        "artifacts/advisory/external_learning_sidecar/latest.json"
    ]
    assert "artifact_graph" in capability["current_delta_trigger_terms"]
    assert "unit_harmonized_external_validation_rerun" in capability["action_triggers"]
    assert "wildcard_action_trigger_policy" not in capability
    assert capability["role"] == (
        "artifact_graph_claim_warning_annotation_regeneration_ledger_"
        "connector_and_data_flow_refs_only_advisory"
    )
    assert capability["fail_open"] is True
    assert capability["mainline_waits_for_capability"] is False
    assert capability["authority_boundary"]["can_authorize_artifact_authority"] is False

    resolution = module.resolve_scientific_capabilities(
        current_owner_delta=current_owner_delta,
    )
    selected = {
        item["capability_id"]: item
        for item in resolution["selected_capabilities"]
    }
    candidate = selected["openscience_artifact_provenance_advisory"]
    assert resolution["fail_open"] is True
    assert resolution["mainline_waits_for_capability"] is False
    assert candidate["trigger_reason"] == (
        "current_delta_declared_openscience_artifact_provenance_need"
    )
    assert candidate["readback"]["can_execute_external_runner"] is False
    assert candidate["readback"]["can_authorize_quality_verdict"] is False
    assert candidate["authority_boundary"]["can_authorize_artifact_authority"] is False

    invocation = module.invoke_scientific_capability(
        capability_id="openscience_artifact_provenance_advisory",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )

    assert invocation["status"] == "opl_capability_request_pending"
    assert invocation["refs_only"] is True
    assert invocation["request_only"] is True
    assert invocation["mainline_waits_for_capability"] is False
    assert invocation["can_block_current_owner_action"] is False
    assert invocation["mas_can_invoke_capability_sidecar"] is False
    assert invocation["authority_boundary"]["can_authorize_artifact_authority"] is False
    assert invocation["opl_capability_invocation_request"]["callable_surface"] == (
        "external_learning_sidecar.run_external_learning_sidecar"
    )
    assert invocation["result"]["output_refs"] == [
        "artifacts/advisory/external_learning_sidecar/latest.json"
    ]
    assert not (
        study_root / "artifacts/advisory/external_learning_sidecar/latest.json"
    ).exists()
    assert not (study_root / "artifacts/artifact_authority").exists()
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()


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
