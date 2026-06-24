from __future__ import annotations

import importlib
import json
from pathlib import Path


SCHOLARSKILLS_MODULE_IDS = [
    "opl.scholarskills.display",
    "opl.scholarskills.tables",
    "opl.scholarskills.stats",
    "opl.scholarskills.omics",
    "opl.scholarskills.lit",
    "opl.scholarskills.write",
    "opl.scholarskills.review",
    "opl.scholarskills.submit",
    "opl.scholarskills.data",
    "opl.scholarskills.intake",
]

SCHOLARSKILLS_RECEIPT_REF_KEYS_BY_MODULE = {
    "opl.scholarskills.display": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "render_cache_ref",
        "artifact_manifest_ref",
        "visual_audit_or_gallery_preview_ref",
    ],
    "opl.scholarskills.tables": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "table_manifest_ref",
        "table_qc_ref",
    ],
    "opl.scholarskills.stats": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "analysis_manifest_ref",
        "reproducibility_check_ref",
    ],
    "opl.scholarskills.omics": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "omics_pipeline_manifest_ref",
        "feature_matrix_qc_ref",
    ],
    "opl.scholarskills.lit": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "evidence_map_ref",
        "citation_manifest_ref",
    ],
    "opl.scholarskills.write": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "draft_section_manifest_ref",
        "source_trace_ref",
    ],
    "opl.scholarskills.review": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "reviewer_report_ref",
        "route_back_ref",
    ],
    "opl.scholarskills.submit": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "package_manifest_ref",
        "submission_checklist_ref",
    ],
    "opl.scholarskills.data": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "data_manifest_ref",
        "lineage_readiness_ref",
    ],
    "opl.scholarskills.intake": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "source_snapshot_ref",
        "adoption_contract_ref",
    ],
}


def _write_tables_materialized_package(
    package_root: Path,
    *,
    manifest_overrides: dict[str, object] | None = None,
    receipt_overrides: dict[str, object] | None = None,
) -> dict[str, Path]:
    package_root.mkdir(parents=True)
    receipt_path = package_root / "execution_receipt_candidate.json"
    manifest_path = package_root / "manifest.json"
    artifact_manifest_path = package_root / "artifacts" / "table_manifest.json"
    artifact_manifest_path.parent.mkdir()
    artifact_manifest_path.write_text('{"items":[]}', encoding="utf-8")
    authority_flags = {
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_current_package": False,
        "can_write_paper_or_package": False,
        "can_write_study_truth": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
    }
    receipt = {
        "surface_kind": "opl_scholarskills_execution_receipt_candidate",
        "module_id": "opl.scholarskills.tables",
        "execution_receipt_ref": "opl-vault:receipts/tables/receipt.json",
        "artifact_manifest_path": str(artifact_manifest_path),
        "candidate_artifacts": [
            {
                "kind": "table_manifest",
                "ref": "opl-vault:tables/table_manifest.json",
                "sha256": "sha256:table-manifest",
                "readiness_notes": ["candidate table package ready for MAS owner review"],
                "missing_inputs": [],
            }
        ],
        "candidate_artifact_bodies": {
            "table_summary": {
                "body": {"rows": 2, "columns": ["metric", "value"]},
                "readiness_notes": ["body carried only as candidate artifact evidence"],
                "missing_inputs": ["owner_acceptance_ref"],
            }
        },
        "execution_receipt_refs": {
            "input_fingerprint_ref": "opl-vault:inputs/tables.sha256",
            "dependency_profile_ref": "opl-vault:prepare/tables-env.json",
            "prepared_run_context_ref": "opl-vault:run-context/tables-run.json",
            "table_qc_ref": "opl-vault:tables/qc.json",
        },
        "written_files": [
            "opl-vault:tables/table_manifest.json",
            "opl-vault:tables/qc.json",
        ],
        "sha256": "sha256:receipt",
        "authority_flags": dict(authority_flags),
    }
    if receipt_overrides:
        receipt.update(receipt_overrides)
    manifest = {
        "surface_kind": "opl_scholarskills_materialized_package_manifest",
        "module_id": "opl.scholarskills.tables",
        "execution_receipt_candidate_path": receipt_path.name,
        "artifact_manifest_path": str(artifact_manifest_path),
        "written_files": [str(artifact_manifest_path)],
        "sha256": "sha256:manifest",
        "authority_flags": dict(authority_flags),
    }
    if manifest_overrides:
        manifest.update(manifest_overrides)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return {
        "artifact_manifest_path": artifact_manifest_path,
        "manifest_path": manifest_path,
        "receipt_path": receipt_path,
    }


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


def test_scholarskills_registry_declares_workspace_local_install_boundary() -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")

    registry = module.build_scientific_capability_registry()
    capabilities = {item["capability_id"]: item for item in registry["capabilities"]}
    candidate = capabilities["opl.scholarskills.write"]

    assert registry["scholarskills_local_install"]["install_owner"] == "one-person-lab"
    assert registry["scholarskills_local_install"]["workspace"]["sync_command_template"]["argv"] == [
        "opl",
        "connect",
        "sync-skills",
        "--domain",
        "scholarskills",
        "--scope",
        "workspace",
        "--target-workspace",
        "<workspace_root>",
        "--json",
    ]
    assert registry["scholarskills_local_install"]["workspace"]["target_skill_path_template"] == (
        "<workspace_root>/.codex/skills/opl-scholarskills"
    )
    assert registry["scholarskills_local_install"]["quest"]["sync_command_template"]["argv"] == [
        "opl",
        "connect",
        "sync-skills",
        "--domain",
        "scholarskills",
        "--scope",
        "quest",
        "--target-quest",
        "<quest_root>",
        "--json",
    ]
    assert registry["scholarskills_local_install"]["quest"]["target_skill_path_template"] == (
        "<quest_root>/.codex/skills/opl-scholarskills"
    )
    assert registry["scholarskills_local_install"]["mas_program_repo_plugin_is_execution_source"] is False
    assert registry["scholarskills_local_install"]["source_repo_ref"] == "external:opl-scholarskills"

    assert candidate["source_repo_ref"] == "external:opl-scholarskills"
    assert candidate["local_install"]["install_scopes"] == ["workspace", "quest"]
    assert candidate["local_install"]["mas_program_repo_plugin_is_execution_source"] is False
    assert candidate["local_install"]["workspace"]["target_skill_path_template"] == (
        "<workspace_root>/.codex/skills/opl-scholarskills"
    )
    assert "readback:mas_scholarskills_local_install" in candidate["descriptor_refs"]
    assert "external:opl-scholarskills" in candidate["source_frameworks"]
    assert candidate["owner_consumption_boundary"]["owner_gated_refs_consumption"] is True
    assert candidate["owner_consumption_boundary"]["counts_as_paper_truth"] is False


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


def test_scientific_capability_registry_indexes_resolves_and_invokes_all_scholarskills_modules(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"

    registry = module.build_scientific_capability_registry()
    capabilities = {
        item["capability_id"]: item
        for item in registry["capabilities"]
    }

    assert set(SCHOLARSKILLS_MODULE_IDS) <= set(capabilities)
    for module_id in SCHOLARSKILLS_MODULE_IDS:
        capability = capabilities[module_id]
        module_name = module_id.removeprefix("opl.scholarskills.")

        assert capability["module_id"] == module_id
        assert capability["capability_family"] == f"scholarskills_{module_name}"
        assert capability["invocation_kind"] == "descriptor_only_current_owner_input_refs"
        assert capability["descriptor_only"] is True
        assert capability["refs_only"] is True
        assert capability["external_runner_invocation_allowed"] is False
        assert "contracts/opl-framework/scholar-skills-capability-modules.json" in capability[
            "descriptor_refs"
        ]
        assert "opl:runtime-env:prepare" in capability["dependency_profile_refs"]
        assert "opl:run-context:prepared-runtime-env" in capability["run_context_refs"]
        assert capability["artifact_refs"]
        assert capability["execution_receipt_expectation"]["module_id"] == module_id
        assert capability["execution_receipt_expectation"][
            "execution_receipt_can_authorize_publication_readiness"
        ] is False
        assert capability["owner_consumption_boundary"]["candidate_output_only"] is True
        assert capability["owner_consumption_boundary"]["counts_as_paper_truth"] is False
        assert capability["authority_boundary"]["can_write_publication_eval"] is False
        assert capability["authority_boundary"]["can_write_owner_receipt"] is False

        current_owner_delta = {
            "action_type": f"prepare_{module_name}_candidate",
            "action_id": f"{module_name}-001",
            "work_unit_id": f"{module_name}-candidate",
            "work_unit_fingerprint": f"sha256:{module_name}",
            "capability_families": [capability["capability_family"]],
        }
        resolution = module.resolve_scientific_capabilities(
            current_owner_delta=current_owner_delta,
        )
        selected = {
            item["capability_id"]: item
            for item in resolution["selected_capabilities"]
        }
        assert module_id in selected
        assert selected[module_id]["trigger_reason"] == (
            "current_delta_requested_capability_family"
        )

        invocation = module.invoke_scientific_capability(
            capability_id=module_id,
            study_root=study_root,
            current_owner_delta=current_owner_delta,
            apply=True,
        )
        assert invocation["status"] == "descriptor_only"
        assert invocation["request_only"] is False
        assert invocation["descriptor_only"] is True
        assert invocation["external_runner_invocation_allowed"] is False
        assert invocation["opl_capability_runtime_required"] is False
        assert invocation["result"]["readback"]["module_id"] == module_id
        assert invocation["result"]["readback"]["execution_receipt_expectation"][
            "module_id"
        ] == module_id
        assert invocation["result"]["readback"]["owner_consumption_boundary"][
            "counts_as_owner_receipt"
        ] is False


def test_scientific_capability_registry_indexes_and_resolves_scholar_display_descriptor(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    current_owner_delta = {
        "action_type": "prepare_manuscript_visual_package",
        "action_id": "scholar-display-001",
        "owner": "display",
        "work_unit_id": "scholar-display-candidate",
        "work_unit_fingerprint": "sha256:scholar-display",
        "capability_families": ["scholarskills_display"],
        "declared_needs": [
            "Scholar Display refs",
            "Display Pack gallery preview",
            "publication display candidate artifact refs",
        ],
    }

    registry = module.build_scientific_capability_registry()
    capabilities = {
        item["capability_id"]: item
        for item in registry["capabilities"]
    }
    capability = capabilities["opl.scholarskills.display"]

    assert capability["module_id"] == "opl.scholarskills.display"
    assert capability["capability_family"] == "scholarskills_display"
    assert capability["invocation_kind"] == "descriptor_only_current_owner_input_refs"
    assert capability["descriptor_only"] is True
    assert capability["refs_only"] is True
    assert capability["external_runner_invocation_allowed"] is False
    assert capability["bridged_capability_refs"] == [
        "scientific-capability:display_pack_visual_capability",
        "display-pack-contract.v2",
    ]
    assert "contracts/display-pack-contract.v2.json" in capability["descriptor_refs"]
    assert {
        "opl:runtime-env:prepare",
        "opl:scholarskills.display:dependency-profile",
        "opl:scholarskills.display:doctor",
    } <= set(capability["dependency_profile_refs"])
    assert {
        "opl:run-context:prepared-runtime-env",
        "opl:scholarskills.display:run-context",
        "opl:scholarskills.display:render-cache",
    } <= set(capability["run_context_refs"])
    assert {
        "display_pack_agent_orchestration",
        "paper/build/display_pack_lock.json",
        "paper/figure_render_receipt.json",
        "paper/figure_visual_audit_receipt.json",
        "display_pack_gallery_manifest",
    } <= set(capability["artifact_refs"])
    assert capability["execution_receipt_expectation"] == {
        "surface_kind": "mas_scholar_display_execution_receipt_expectation",
        "schema_version": 1,
        "module_id": "opl.scholarskills.display",
        "receipt_owner": "one-person-lab",
        "receipt_role": "candidate_display_execution_receipt",
        "required_ref_families": [
            "input_fingerprint_ref",
            "dependency_profile_ref",
            "prepared_run_context_ref",
            "render_cache_ref",
            "artifact_manifest_ref",
            "visual_audit_or_gallery_preview_ref",
        ],
        "mas_owner_receipt_required_for_paper_truth": True,
        "execution_receipt_can_authorize_publication_readiness": False,
    }
    assert capability["owner_consumption_boundary"] == {
        "surface_kind": "mas_scholar_display_owner_consumption_boundary",
        "schema_version": 1,
        "candidate_output_only": True,
        "owner_consumption_evidence": "refs_only",
        "counts_as_paper_truth": False,
        "counts_as_current_package_authority": False,
        "counts_as_owner_receipt": False,
        "mas_owner_gate_required_for_paper_truth": True,
    }
    assert capability["authority_boundary"]["can_write_publication_eval"] is False
    assert capability["authority_boundary"]["can_write_paper_or_package"] is False
    assert capability["authority_boundary"]["can_write_owner_receipt"] is False

    resolution = module.resolve_scientific_capabilities(
        current_owner_delta=current_owner_delta,
    )
    selected = {
        item["capability_id"]: item
        for item in resolution["selected_capabilities"]
    }
    candidate = selected["opl.scholarskills.display"]

    assert candidate["module_id"] == "opl.scholarskills.display"
    assert candidate["trigger_reason"] == "current_delta_requested_capability_family"
    assert candidate["descriptor_only"] is True
    assert candidate["refs_only"] is True
    assert candidate["external_runner_invocation_allowed"] is False
    assert candidate["can_block_current_owner_action"] is False
    assert candidate["descriptor_refs"] == capability["descriptor_refs"]
    assert candidate["dependency_profile_refs"] == capability["dependency_profile_refs"]
    assert candidate["run_context_refs"] == capability["run_context_refs"]
    assert candidate["artifact_refs"] == capability["artifact_refs"]
    assert candidate["execution_receipt_expectation"] == capability[
        "execution_receipt_expectation"
    ]
    assert candidate["owner_consumption_boundary"] == capability[
        "owner_consumption_boundary"
    ]
    assert candidate["readback"]["module_id"] == "opl.scholarskills.display"
    assert candidate["readback"]["authority_false_flags"] == {
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_paper_or_package": False,
        "can_write_memory_body": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_authorize_owner_action": False,
        "can_authorize_provider_admission": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_artifact_authority": False,
        "can_close_stage": False,
    }

    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.display",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )
    assert invocation["status"] == "descriptor_only"
    assert invocation["request_only"] is False
    assert invocation["descriptor_only"] is True
    assert invocation["external_runner_invocation_allowed"] is False
    assert invocation["opl_capability_runtime_required"] is False
    assert invocation["output_refs"] == capability["output_refs"]
    assert invocation["result"]["contract_refs"] == capability["contract_refs"]
    assert invocation["result"]["readback"]["dependency_profile_refs"] == capability[
        "dependency_profile_refs"
    ]
    assert invocation["result"]["readback"]["run_context_refs"] == capability[
        "run_context_refs"
    ]
    assert invocation["result"]["readback"]["owner_consumption_boundary"][
        "owner_consumption_evidence"
    ] == "refs_only"
    assert invocation["authority_boundary"]["can_write_publication_eval"] is False
    assert invocation["authority_boundary"]["can_write_controller_decisions"] is False
    assert invocation["authority_boundary"]["can_write_paper_or_package"] is False
    assert invocation["authority_boundary"]["can_write_owner_receipt"] is False
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()

    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta=current_owner_delta,
    )
    assert evidence["capability_id"] == "opl.scholarskills.display"
    assert evidence["refs_only"] is True
    assert evidence["owner_consumption_status"] == "no_owner_response_refs"
    assert evidence["consumption_evidence_only"] is True
    assert evidence["counts_as_progress"] is False
    assert evidence["owner_receipt_ref"] is None
    assert evidence["typed_blocker_ref"] is None
    assert evidence["can_authorize_owner_action"] is False
    assert evidence["can_authorize_publication_readiness"] is False
    assert evidence["counts_as_paper_truth"] is False
    assert evidence["counts_as_owner_receipt"] is False
    assert evidence["execution_receipt_status"] == "missing_required_refs"
    assert evidence["observed_execution_receipt_ref_families"] == []
    assert evidence["missing_execution_receipt_ref_families"] == [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "render_cache_ref",
        "artifact_manifest_ref",
        "visual_audit_or_gallery_preview_ref",
    ]
    assert evidence["no_forbidden_write_proof"]["forbidden_refs_absent"] is True


def test_scientific_capability_registry_consumes_opl_scholar_display_receipt_candidate_as_refs_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    current_owner_delta = {
        "action_type": "prepare_manuscript_visual_package",
        "action_id": "scholar-display-001",
        "owner": "display",
        "work_unit_id": "scholar-display-candidate",
        "work_unit_fingerprint": "sha256:scholar-display",
        "capability_families": ["scholarskills_display"],
    }
    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.display",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )

    opl_receipt_candidate = {
        "surface_kind": "opl_scholarskills_execution_receipt_candidate",
        "status": "receipt_candidate_unsigned",
        "module_id": "opl.scholarskills.display",
        "execution_receipt_ref": "opl-vault:receipts/scholar-display/receipt.json",
        "execution_receipt_refs": {
            "input_fingerprint_ref": "opl-vault:inputs/fingerprint.sha256",
            "dependency_profile_ref": "opl-vault:prepare/display-env.json",
            "prepared_run_context_ref": "opl-vault:run-context/display-run.json",
            "render_cache_ref": "opl-vault:cache/display-render-cache.json",
            "artifact_manifest_ref": "opl-vault:artifacts/display-manifest.json",
            "visual_audit_or_gallery_preview_ref": "opl-vault:gallery/preview.json",
        },
        "execution_receipt_counts_as_candidate_artifact": True,
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "can_authorize_publication_readiness": False,
        "can_sign_owner_receipt": False,
    }

    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta=current_owner_delta,
        execution_receipt=opl_receipt_candidate,
    )

    assert evidence["execution_receipt_ref"] == (
        "opl-vault:receipts/scholar-display/receipt.json"
    )
    assert evidence["execution_receipt_status"] == "complete"
    assert evidence["observed_execution_receipt_ref_families"] == [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "render_cache_ref",
        "artifact_manifest_ref",
        "visual_audit_or_gallery_preview_ref",
    ]
    assert evidence["missing_execution_receipt_ref_families"] == []
    assert evidence["execution_receipt_refs"] == {
        "input_fingerprint_ref": "opl-vault:inputs/fingerprint.sha256",
        "dependency_profile_ref": "opl-vault:prepare/display-env.json",
        "prepared_run_context_ref": "opl-vault:run-context/display-run.json",
        "render_cache_ref": "opl-vault:cache/display-render-cache.json",
        "artifact_manifest_ref": "opl-vault:artifacts/display-manifest.json",
        "visual_audit_or_gallery_preview_ref": "opl-vault:gallery/preview.json",
    }
    assert evidence["execution_receipt_counts_as_candidate_artifact"] is True
    assert evidence["counts_as_progress"] is False
    assert evidence["counts_as_paper_truth"] is False
    assert evidence["counts_as_owner_receipt"] is False
    assert evidence["can_authorize_owner_action"] is False
    assert evidence["can_authorize_publication_readiness"] is False
    assert evidence["authority_boundary"]["can_write_publication_eval"] is False
    assert evidence["authority_boundary"]["can_write_controller_decisions"] is False
    assert evidence["authority_boundary"]["can_write_owner_receipt"] is False
    assert evidence["authority_boundary"]["can_write_typed_blocker"] is False
    assert evidence["no_forbidden_write_proof"]["forbidden_refs_absent"] is True
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_scholar_display_missing_receipt_refs_and_owner_refs_stay_non_authorizing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    current_owner_delta = {
        "action_type": "prepare_manuscript_visual_package",
        "action_id": "scholar-display-002",
        "owner": "display",
        "work_unit_id": "scholar-display-candidate",
        "work_unit_fingerprint": "sha256:scholar-display-missing",
        "capability_families": ["scholarskills_display"],
    }
    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.display",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )

    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta=current_owner_delta,
        dependency_prepared_receipt_ref="opl-vault:prepare/display-env.json",
        artifact_manifest_ref="opl-vault:artifacts/display-manifest.json",
        owner_response_refs={
            "owner_receipt_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
            "typed_blocker_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
        },
    )

    assert evidence["owner_consumption_status"] == "owner_response_refs_observed"
    assert evidence["owner_receipt_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json"
    )
    assert evidence["typed_blocker_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    assert evidence["execution_receipt_status"] == "missing_required_refs"
    assert evidence["observed_execution_receipt_ref_families"] == [
        "dependency_profile_ref",
        "artifact_manifest_ref",
    ]
    assert evidence["missing_execution_receipt_ref_families"] == [
        "input_fingerprint_ref",
        "prepared_run_context_ref",
        "render_cache_ref",
        "visual_audit_or_gallery_preview_ref",
    ]
    assert evidence["execution_receipt_counts_as_candidate_artifact"] is False
    assert evidence["counts_as_progress"] is False
    assert evidence["counts_as_paper_truth"] is False
    assert evidence["counts_as_owner_receipt"] is False
    assert evidence["can_authorize_owner_action"] is False
    assert evidence["can_authorize_publication_readiness"] is False
    tail = evidence["standard_agent_feedback_loop_tail"]
    assert tail["owner_answer_or_typed_blocker_observed"] is True
    assert tail["counts_as_opl_family_completion"] is False
    assert evidence["authority_boundary"]["can_write_owner_receipt"] is False
    assert evidence["authority_boundary"]["can_write_typed_blocker"] is False
    assert evidence["authority_boundary"]["can_authorize_publication_readiness"] is False
    assert evidence["no_forbidden_write_proof"]["forbidden_refs_absent"] is True
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_consumes_non_display_scholarskills_receipts_as_refs_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    current_owner_delta = {
        "action_type": "prepare_table_package",
        "action_id": "scholar-tables-001",
        "work_unit_id": "scholar-tables-candidate",
        "work_unit_fingerprint": "sha256:scholar-tables",
        "capability_families": ["scholarskills_tables"],
    }
    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.tables",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )

    complete_receipt = {
        "surface_kind": "opl_scholarskills_execution_receipt_candidate",
        "status": "receipt_candidate_unsigned",
        "module_id": "opl.scholarskills.tables",
        "execution_receipt_ref": "opl-vault:receipts/scholar-tables/receipt.json",
        "execution_receipt_refs": {
            "input_fingerprint_ref": "opl-vault:inputs/tables.sha256",
            "dependency_profile_ref": "opl-vault:prepare/tables-env.json",
            "prepared_run_context_ref": "opl-vault:run-context/tables-run.json",
            "table_manifest_ref": "opl-vault:tables/table-manifest.json",
            "table_qc_ref": "opl-vault:tables/qc.json",
        },
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "can_authorize_publication_readiness": False,
    }
    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta=current_owner_delta,
        execution_receipt=complete_receipt,
    )

    assert evidence["capability_id"] == "opl.scholarskills.tables"
    assert evidence["execution_receipt_status"] == "complete"
    assert evidence["missing_execution_receipt_ref_families"] == []
    assert evidence["observed_execution_receipt_ref_families"] == [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "table_manifest_ref",
        "table_qc_ref",
    ]
    assert evidence["execution_receipt_counts_as_candidate_artifact"] is True
    assert evidence["counts_as_progress"] is False
    assert evidence["counts_as_paper_truth"] is False
    assert evidence["counts_as_owner_receipt"] is False
    assert evidence["can_authorize_publication_readiness"] is False
    assert "owner_gate_request" not in evidence
    assert "owner_gate_handoff" not in evidence
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()

    missing_evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta=current_owner_delta,
        execution_receipt_refs={
            "dependency_prepared_receipt_ref": "opl-vault:prepare/tables-env.json",
            "table_manifest_ref": "opl-vault:tables/table-manifest.json",
        },
    )

    assert missing_evidence["execution_receipt_status"] == "missing_required_refs"
    assert missing_evidence["observed_execution_receipt_ref_families"] == [
        "dependency_profile_ref",
        "table_manifest_ref",
    ]
    assert missing_evidence["missing_execution_receipt_ref_families"] == [
        "input_fingerprint_ref",
        "prepared_run_context_ref",
        "table_qc_ref",
    ]
    assert missing_evidence["execution_receipt_counts_as_candidate_artifact"] is False
    assert missing_evidence["counts_as_owner_receipt"] is False


def test_scientific_capability_registry_consumes_opl_shaped_receipts_for_every_scholarskills_module(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"

    for module_id, expected_ref_keys in SCHOLARSKILLS_RECEIPT_REF_KEYS_BY_MODULE.items():
        module_name = module_id.removeprefix("opl.scholarskills.")
        current_owner_delta = {
            "action_type": f"prepare_{module_name}_candidate",
            "action_id": f"{module_name}-receipt-001",
            "work_unit_id": f"{module_name}-receipt-candidate",
            "work_unit_fingerprint": f"sha256:{module_name}-receipt",
            "capability_families": [f"scholarskills_{module_name}"],
        }
        invocation = module.invoke_scientific_capability(
            capability_id=module_id,
            study_root=study_root / module_name,
            current_owner_delta=current_owner_delta,
            apply=True,
        )
        complete_receipt = {
            "surface_kind": "opl_scholarskills_execution_receipt_candidate",
            "status": "receipt_candidate_unsigned",
            "module_id": module_id,
            "execution_receipt_ref": f"opl-vault:receipts/{module_name}/receipt.json",
            "execution_receipt_refs": {
                ref_key: f"opl-vault:{module_name}/{ref_key}.json"
                for ref_key in expected_ref_keys
            },
            "counts_as_paper_truth": False,
            "counts_as_owner_receipt": False,
            "can_authorize_publication_readiness": False,
        }
        evidence = module.build_capability_owner_consumption_evidence(
            invocation_result=invocation,
            current_owner_delta=current_owner_delta,
            execution_receipt=complete_receipt,
        )

        assert invocation["result"]["readback"]["execution_receipt_expectation"][
            "required_ref_families"
        ] == expected_ref_keys
        assert evidence["capability_id"] == module_id
        assert evidence["execution_receipt_status"] == "complete"
        assert evidence["missing_execution_receipt_ref_families"] == []
        assert evidence["observed_execution_receipt_ref_families"] == expected_ref_keys
        assert list(evidence["execution_receipt_refs"]) == expected_ref_keys
        assert evidence["execution_receipt_counts_as_candidate_artifact"] is True
        assert evidence["counts_as_progress"] is False
        assert evidence["counts_as_paper_truth"] is False
        assert evidence["counts_as_owner_receipt"] is False
        assert evidence["can_authorize_publication_readiness"] is False


def test_scientific_capability_registry_consumes_file_materialized_scholarskills_package_as_refs_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    package_root = tmp_path / "opl-package"
    package_root.mkdir()
    receipt_path = package_root / "execution_receipt_candidate.json"
    manifest_path = package_root / "manifest.json"
    artifact_manifest_path = package_root / "artifacts" / "table_manifest.json"
    artifact_manifest_path.parent.mkdir()
    artifact_manifest_path.write_text('{"items":[]}', encoding="utf-8")
    receipt_path.write_text(
        json.dumps(
            {
                "surface_kind": "opl_scholarskills_execution_receipt_candidate",
                "module_id": "opl.scholarskills.tables",
                "execution_receipt_ref": "opl-vault:receipts/tables/receipt.json",
                "artifact_manifest_path": str(artifact_manifest_path),
                "candidate_artifacts": [
                    {
                        "kind": "table_manifest",
                        "ref": "opl-vault:tables/table_manifest.json",
                        "sha256": "sha256:table-manifest",
                        "readiness_notes": [
                            "candidate table package ready for MAS owner review"
                        ],
                        "missing_inputs": [],
                    }
                ],
                "candidate_artifact_bodies": {
                    "table_summary": {
                        "body": {"rows": 2, "columns": ["metric", "value"]},
                        "readiness_notes": [
                            "body carried only as candidate artifact evidence"
                        ],
                        "missing_inputs": ["owner_acceptance_ref"],
                    }
                },
                "execution_receipt_refs": {
                    "input_fingerprint_ref": "opl-vault:inputs/tables.sha256",
                    "dependency_profile_ref": "opl-vault:prepare/tables-env.json",
                    "prepared_run_context_ref": "opl-vault:run-context/tables-run.json",
                    "table_qc_ref": "opl-vault:tables/qc.json",
                },
                "written_files": [
                    "opl-vault:tables/table_manifest.json",
                    "opl-vault:tables/qc.json",
                ],
                "sha256": "sha256:receipt",
                "authority_flags": {
                    "can_write_publication_eval": False,
                    "can_write_controller_decisions": False,
                    "can_write_current_package": False,
                    "can_write_paper_or_package": False,
                    "can_write_study_truth": False,
                    "can_write_owner_receipt": False,
                    "can_write_typed_blocker": False,
                    "can_write_human_gate": False,
                },
            }
        ),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(
            {
                "surface_kind": "opl_scholarskills_materialized_package_manifest",
                "module_id": "opl.scholarskills.tables",
                "execution_receipt_candidate_path": receipt_path.name,
                "artifact_manifest_path": str(artifact_manifest_path),
                "written_files": [str(artifact_manifest_path)],
                "sha256": "sha256:manifest",
                "authority_flags": {
                    "can_write_publication_eval": False,
                    "can_write_controller_decisions": False,
                    "can_write_current_package": False,
                    "can_write_paper_or_package": False,
                    "can_write_study_truth": False,
                    "can_write_owner_receipt": False,
                    "can_write_typed_blocker": False,
                    "can_write_human_gate": False,
                },
            }
        ),
        encoding="utf-8",
    )
    current_owner_delta = {
        "action_type": "prepare_table_package",
        "action_id": "scholar-tables-file-001",
        "work_unit_id": "scholar-tables-file-candidate",
        "work_unit_fingerprint": "sha256:scholar-tables-file",
        "capability_families": ["scholarskills_tables"],
    }
    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.tables",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )

    evidence = module.build_capability_owner_consumption_evidence(
        invocation_result=invocation,
        current_owner_delta=current_owner_delta,
        materialized_package_manifest_path=manifest_path,
    )

    assert evidence["execution_receipt_status"] == "complete"
    assert evidence["execution_receipt_refs"]["table_manifest_ref"] == str(
        artifact_manifest_path
    )
    assert evidence["observed_execution_receipt_ref_families"] == [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "table_manifest_ref",
        "table_qc_ref",
    ]
    package_consumption = evidence["materialized_package_consumption"]
    assert package_consumption["refs_only"] is True
    assert package_consumption["manifest_path"] == str(manifest_path.resolve())
    assert package_consumption["execution_receipt_path"] == str(receipt_path.resolve())
    assert package_consumption["authority_flags_false"] is True
    assert package_consumption["candidate_artifact_count"] == 4
    candidate_artifacts = package_consumption["candidate_artifacts"]
    ref_artifact = next(
        artifact
        for artifact in candidate_artifacts
        if artifact["kind"] == "table_manifest"
        and artifact["ref"] == "opl-vault:tables/table_manifest.json"
    )
    assert ref_artifact == {
        "kind": "table_manifest",
        "ref": "opl-vault:tables/table_manifest.json",
        "sha256": "sha256:table-manifest",
        "authority": False,
        "authority_flags": {},
        "authority_flags_false": True,
        "readiness_notes": ["candidate table package ready for MAS owner review"],
        "missing_inputs": [],
        "body_included": False,
        "body_carried_to_owner_request": False,
        "written_files": [],
        "forbidden_written_file_collisions": [],
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "can_authorize_publication_readiness": False,
    }
    body_artifact = next(
        artifact for artifact in candidate_artifacts if artifact["kind"] == "table_summary"
    )
    assert body_artifact["kind"] == "table_summary"
    assert body_artifact["ref"] is None
    assert body_artifact["sha256"].startswith("sha256:")
    assert body_artifact["authority"] is False
    assert body_artifact["body_included"] is True
    assert body_artifact["body_carried_to_owner_request"] is False
    assert body_artifact["readiness_notes"] == [
        "body carried only as candidate artifact evidence"
    ]
    assert body_artifact["missing_inputs"] == ["owner_acceptance_ref"]
    assert package_consumption["candidate_artifact_missing_inputs"] == [
        "owner_acceptance_ref"
    ]
    assert package_consumption["forbidden_written_file_collisions"] == []
    assert package_consumption["mas_consumer_written_files"] == []
    assert package_consumption["counts_as_paper_truth"] is False
    assert package_consumption["counts_as_owner_receipt"] is False
    assert package_consumption["can_authorize_publication_readiness"] is False
    assert package_consumption["can_write_publication_eval"] is False
    assert package_consumption["can_write_controller_decisions"] is False
    assert package_consumption["can_write_current_package"] is False
    assert package_consumption["can_write_paper_or_package"] is False
    assert package_consumption["can_write_study_truth"] is False
    assert package_consumption["can_write_typed_blocker"] is False
    assert package_consumption["can_write_human_gate"] is False
    assert evidence["counts_as_progress"] is False
    assert evidence["counts_as_paper_truth"] is False
    assert evidence["counts_as_owner_receipt"] is False
    assert evidence["can_authorize_publication_readiness"] is False
    owner_gate_request = evidence["owner_gate_request"]
    assert owner_gate_request["surface_kind"] == "mas_scholarskills_owner_gate_request"
    assert owner_gate_request["request_status"] == "ready_for_owner_gate_review"
    assert owner_gate_request["non_authoritative_request"] is True
    assert owner_gate_request["capability_id"] == "opl.scholarskills.tables"
    assert owner_gate_request["module_id"] == "opl.scholarskills.tables"
    assert owner_gate_request["execution_receipt_status"] == "complete"
    assert owner_gate_request["materialized_package_manifest_path"] == str(
        manifest_path.resolve()
    )
    assert owner_gate_request["materialized_package_sha256"] == "sha256:receipt"
    assert owner_gate_request["candidate_artifact_count"] == 4
    assert owner_gate_request["candidate_artifact_missing_inputs"] == [
        "owner_acceptance_ref"
    ]
    owner_ref_artifact = next(
        artifact
        for artifact in owner_gate_request["candidate_artifacts"]
        if artifact["kind"] == "table_manifest"
        and artifact["ref"] == "opl-vault:tables/table_manifest.json"
    )
    assert owner_ref_artifact == {
        "kind": "table_manifest",
        "ref": "opl-vault:tables/table_manifest.json",
        "sha256": "sha256:table-manifest",
        "authority": False,
        "authority_flags_false": True,
        "readiness_notes": ["candidate table package ready for MAS owner review"],
        "missing_inputs": [],
        "body_included": False,
        "body_carried_to_owner_request": False,
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "can_authorize_publication_readiness": False,
    }
    owner_body_artifact = next(
        artifact
        for artifact in owner_gate_request["candidate_artifacts"]
        if artifact["kind"] == "table_summary"
    )
    assert owner_body_artifact["kind"] == "table_summary"
    assert owner_body_artifact["sha256"] == body_artifact["sha256"]
    assert owner_body_artifact["body_included"] is True
    assert owner_body_artifact["body_carried_to_owner_request"] is False
    assert owner_body_artifact["missing_inputs"] == ["owner_acceptance_ref"]
    assert owner_gate_request["required_owner_response_shapes"] == [
        "owner_receipt_ref",
        "typed_blocker_ref",
        "route_back_evidence_ref",
        "reviewer_receipt_ref",
    ]
    assert owner_gate_request["counts_as_progress"] is False
    assert owner_gate_request["counts_as_paper_truth"] is False
    assert owner_gate_request["counts_as_owner_receipt"] is False
    assert owner_gate_request["can_authorize_publication_readiness"] is False
    assert owner_gate_request["can_write_owner_receipt"] is False
    owner_gate_handoff = evidence["owner_gate_handoff"]
    assert owner_gate_handoff["surface_kind"] == "mas_scholarskills_owner_gate_handoff"
    assert owner_gate_handoff["handoff_status"] == "ready_for_owner_gate_review"
    assert owner_gate_handoff["next_owner"] == "MAS owner gate"
    assert owner_gate_handoff["source_request_ref"] == "inline:owner_gate_request"
    assert owner_gate_handoff["candidate_artifact_missing_inputs"] == [
        "owner_acceptance_ref"
    ]
    assert owner_gate_handoff["candidate_artifacts"] == owner_gate_request[
        "candidate_artifacts"
    ]
    assert owner_gate_handoff["mas_consumer_written_files"] == []
    assert evidence["required_owner_response_shapes"] == [
        {
            "shape": "owner_receipt_ref",
            "required_for": "accept_candidate_into_mas_paper_truth",
            "may_be_written_by_this_request": False,
        },
        {
            "shape": "typed_blocker_ref",
            "required_for": "block_candidate_with_stable_owner_reason",
            "may_be_written_by_this_request": False,
        },
        {
            "shape": "route_back_evidence_ref",
            "required_for": "return_candidate_to_capability_or_executor",
            "may_be_written_by_this_request": False,
        },
        {
            "shape": "reviewer_receipt_ref",
            "required_for": "attach_non_authoritative_reviewer_readback",
            "may_be_written_by_this_request": False,
        },
    ]
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_cli_consumes_materialized_scholarskills_package_as_refs_only(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "studies" / "001-risk"
    package = _write_tables_materialized_package(tmp_path / "opl-package")

    exit_code = cli.main(
        [
            "scientific-capability-registry",
            "--mode",
            "owner-consumption",
            "--capability-id",
            "opl.scholarskills.tables",
            "--study-root",
            str(study_root),
            "--current-owner-delta-json",
            json.dumps(
                {
                    "action_type": "prepare_table_package",
                    "work_unit_id": "scholar-tables-cli-candidate",
                    "work_unit_fingerprint": "sha256:scholar-tables-cli",
                    "capability_families": ["scholarskills_tables"],
                }
            ),
            "--materialized-package-manifest-path",
            str(package["manifest_path"]),
        ]
    )

    assert exit_code == 0
    evidence = json.loads(capsys.readouterr().out)
    assert evidence["surface_kind"] == (
        "mas_scientific_capability_owner_consumption_evidence"
    )
    assert evidence["refs_only"] is True
    assert evidence["capability_id"] == "opl.scholarskills.tables"
    assert evidence["execution_receipt_status"] == "complete"
    assert evidence["missing_execution_receipt_ref_families"] == []
    assert evidence["execution_receipt_refs"]["table_manifest_ref"] == str(
        package["artifact_manifest_path"]
    )
    package_consumption = evidence["materialized_package_consumption"]
    assert package_consumption["refs_only"] is True
    assert package_consumption["manifest_path"] == str(package["manifest_path"].resolve())
    assert package_consumption["execution_receipt_path"] == str(
        package["receipt_path"].resolve()
    )
    assert package_consumption["authority_flags_false"] is True
    assert package_consumption["candidate_artifact_count"] == 4
    assert package_consumption["candidate_artifact_missing_inputs"] == [
        "owner_acceptance_ref"
    ]
    assert package_consumption["forbidden_written_file_collisions"] == []
    assert package_consumption["mas_consumer_written_files"] == []
    assert package_consumption["counts_as_paper_truth"] is False
    assert package_consumption["counts_as_owner_receipt"] is False
    assert package_consumption["can_authorize_publication_readiness"] is False
    assert package_consumption["can_write_publication_eval"] is False
    assert package_consumption["can_write_controller_decisions"] is False
    assert package_consumption["can_write_current_package"] is False
    assert package_consumption["can_write_paper_or_package"] is False
    assert package_consumption["can_write_study_truth"] is False
    assert package_consumption["can_write_typed_blocker"] is False
    assert package_consumption["can_write_human_gate"] is False
    assert evidence["counts_as_progress"] is False
    assert evidence["counts_as_paper_truth"] is False
    assert evidence["counts_as_owner_receipt"] is False
    assert evidence["can_authorize_publication_readiness"] is False
    assert evidence["owner_gate_request"]["request_status"] == (
        "ready_for_owner_gate_review"
    )
    assert evidence["owner_gate_request"]["non_authoritative_request"] is True
    assert evidence["owner_gate_request"]["candidate_artifact_count"] == 4
    cli_ref_artifact = next(
        artifact
        for artifact in evidence["owner_gate_request"]["candidate_artifacts"]
        if artifact["kind"] == "table_manifest"
        and artifact["ref"] == "opl-vault:tables/table_manifest.json"
    )
    assert cli_ref_artifact["authority"] is False
    assert evidence["owner_gate_request"]["candidate_artifact_missing_inputs"] == [
        "owner_acceptance_ref"
    ]
    assert evidence["owner_gate_handoff"]["handoff_status"] == (
        "ready_for_owner_gate_review"
    )
    assert evidence["owner_gate_handoff"]["candidate_artifact_missing_inputs"] == [
        "owner_acceptance_ref"
    ]
    assert evidence["owner_gate_handoff"]["mas_consumer_written_files"] == []
    assert evidence["required_owner_response_shapes"][0]["shape"] == (
        "owner_receipt_ref"
    )
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_cli_rejects_materialized_package_module_mismatch(
    tmp_path: Path,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "studies" / "001-risk"
    package = _write_tables_materialized_package(
        tmp_path / "opl-package",
        manifest_overrides={"module_id": "opl.scholarskills.review"},
    )

    try:
        cli.main(
            [
                "scientific-capability-registry",
                "--mode",
                "owner-consumption",
                "--capability-id",
                "opl.scholarskills.tables",
                "--study-root",
                str(study_root),
                "--materialized-package-manifest-path",
                str(package["manifest_path"]),
            ]
        )
    except SystemExit as exc:
        assert "module_id mismatch" in str(exc)
        assert "opl.scholarskills.review" in str(exc)
    else:
        raise AssertionError("mismatched module_id should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_cli_rejects_materialized_package_authority_flag(
    tmp_path: Path,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "studies" / "001-risk"
    package = _write_tables_materialized_package(
        tmp_path / "opl-package",
        receipt_overrides={
            "authority_flags": {
                "can_write_owner_receipt": True,
                "can_write_publication_eval": False,
            }
        },
    )

    try:
        cli.main(
            [
                "scientific-capability-registry",
                "--mode",
                "owner-consumption",
                "--capability-id",
                "opl.scholarskills.tables",
                "--study-root",
                str(study_root),
                "--materialized-package-manifest-path",
                str(package["manifest_path"]),
            ]
        )
    except SystemExit as exc:
        assert "authority flags must be false" in str(exc)
        assert "can_write_owner_receipt" in str(exc)
    else:
        raise AssertionError("truthy authority flag should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_cli_rejects_materialized_package_forbidden_written_file(
    tmp_path: Path,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "studies" / "001-risk"
    package = _write_tables_materialized_package(
        tmp_path / "opl-package",
        manifest_overrides={
            "written_files": [
                "artifacts/publication_eval/latest.json",
                "artifacts/tables/table_manifest.json",
            ]
        },
    )

    try:
        cli.main(
            [
                "scientific-capability-registry",
                "--mode",
                "owner-consumption",
                "--capability-id",
                "opl.scholarskills.tables",
                "--study-root",
                str(study_root),
                "--materialized-package-manifest-path",
                str(package["manifest_path"]),
            ]
        )
    except SystemExit as exc:
        assert "forbidden authority writes" in str(exc)
        assert "artifacts/publication_eval/latest.json" in str(exc)
    else:
        raise AssertionError("forbidden written_file should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_cli_rejects_materialized_package_candidate_artifact_authority_claim(
    tmp_path: Path,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "studies" / "001-risk"
    package = _write_tables_materialized_package(
        tmp_path / "opl-package",
        receipt_overrides={
            "candidate_artifact_bodies": {
                "table_summary": {
                    "body": {"rows": 2},
                    "counts_as_paper_truth": True,
                }
            }
        },
    )

    try:
        cli.main(
            [
                "scientific-capability-registry",
                "--mode",
                "owner-consumption",
                "--capability-id",
                "opl.scholarskills.tables",
                "--study-root",
                str(study_root),
                "--materialized-package-manifest-path",
                str(package["manifest_path"]),
            ]
        )
    except SystemExit as exc:
        assert "candidate artifact authority flags" in str(exc)
        assert "counts_as_paper_truth" in str(exc)
    else:
        raise AssertionError("candidate artifact authority claim should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_rejects_file_materialized_scholarskills_authority_flags(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    receipt_path = tmp_path / "execution_receipt_candidate.json"
    receipt_path.write_text(
        json.dumps(
            {
                "module_id": "opl.scholarskills.tables",
                "execution_receipt_refs": {
                    "input_fingerprint_ref": "opl-vault:inputs/tables.sha256",
                    "dependency_profile_ref": "opl-vault:prepare/tables-env.json",
                    "prepared_run_context_ref": "opl-vault:run-context/tables-run.json",
                    "table_manifest_ref": "opl-vault:tables/table-manifest.json",
                    "table_qc_ref": "opl-vault:tables/qc.json",
                },
                "authority_flags": {
                    "can_write_owner_receipt": True,
                    "can_write_publication_eval": False,
                },
            }
        ),
        encoding="utf-8",
    )
    current_owner_delta = {
        "action_type": "prepare_table_package",
        "action_id": "scholar-tables-bad-001",
        "work_unit_id": "scholar-tables-bad-candidate",
        "work_unit_fingerprint": "sha256:scholar-tables-bad",
        "capability_families": ["scholarskills_tables"],
    }
    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.tables",
        study_root=study_root,
        current_owner_delta=current_owner_delta,
        apply=True,
    )

    try:
        module.build_capability_owner_consumption_evidence(
            invocation_result=invocation,
            current_owner_delta=current_owner_delta,
            execution_receipt_path=receipt_path,
        )
    except ValueError as exc:
        assert "can_write_owner_receipt" in str(exc)
    else:
        raise AssertionError("truthy authority flag should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_rejects_file_materialized_scholarskills_module_mismatch(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    receipt_path = tmp_path / "execution_receipt_candidate.json"
    receipt_path.write_text(
        json.dumps(
            {
                "module_id": "opl.scholarskills.review",
                "execution_receipt_refs": {
                    "input_fingerprint_ref": "opl-vault:inputs/tables.sha256",
                    "dependency_profile_ref": "opl-vault:prepare/tables-env.json",
                    "prepared_run_context_ref": "opl-vault:run-context/tables-run.json",
                    "table_manifest_ref": "opl-vault:tables/table-manifest.json",
                    "table_qc_ref": "opl-vault:tables/qc.json",
                },
                "authority_flags": {
                    "can_write_owner_receipt": False,
                    "can_write_publication_eval": False,
                },
            }
        ),
        encoding="utf-8",
    )
    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.tables",
        study_root=study_root,
        current_owner_delta={
            "action_type": "prepare_table_package",
            "work_unit_id": "scholar-tables-mismatch-candidate",
            "capability_families": ["scholarskills_tables"],
        },
        apply=True,
    )

    try:
        module.build_capability_owner_consumption_evidence(
            invocation_result=invocation,
            execution_receipt_path=receipt_path,
        )
    except ValueError as exc:
        assert "module_id mismatch" in str(exc)
        assert "opl.scholarskills.review" in str(exc)
    else:
        raise AssertionError("mismatched module_id should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


def test_scientific_capability_registry_rejects_file_materialized_scholarskills_top_level_authority_claims(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.scientific_capability_registry")
    study_root = tmp_path / "studies" / "001-risk"
    receipt_path = tmp_path / "execution_receipt_candidate.json"
    receipt_path.write_text(
        json.dumps(
            {
                "module_id": "opl.scholarskills.tables",
                "counts_as_paper_truth": True,
                "execution_receipt_refs": {
                    "input_fingerprint_ref": "opl-vault:inputs/tables.sha256",
                    "dependency_profile_ref": "opl-vault:prepare/tables-env.json",
                    "prepared_run_context_ref": "opl-vault:run-context/tables-run.json",
                    "table_manifest_ref": "opl-vault:tables/table-manifest.json",
                    "table_qc_ref": "opl-vault:tables/qc.json",
                },
                "authority_flags": {
                    "can_write_owner_receipt": False,
                    "can_write_publication_eval": False,
                },
            }
        ),
        encoding="utf-8",
    )
    invocation = module.invoke_scientific_capability(
        capability_id="opl.scholarskills.tables",
        study_root=study_root,
        current_owner_delta={
            "action_type": "prepare_table_package",
            "work_unit_id": "scholar-tables-top-level-authority-candidate",
            "capability_families": ["scholarskills_tables"],
        },
        apply=True,
    )

    try:
        module.build_capability_owner_consumption_evidence(
            invocation_result=invocation,
            execution_receipt_path=receipt_path,
        )
    except ValueError as exc:
        assert "counts_as_paper_truth" in str(exc)
    else:
        raise AssertionError("truthy top-level authority claim should fail closed")
    assert not (study_root / "artifacts/publication_eval/latest.json").exists()
    assert not (study_root / "artifacts/controller_decisions/latest.json").exists()
    assert not (study_root / "paper").exists()
    assert not (study_root / "package").exists()


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
