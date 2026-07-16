from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_PAPER_STAGE_DISPLAY_NAMES = {
    "01-study_intake": {"en-US": "Study Intake", "zh-CN": "研究立项"},
    "02-protocol_and_analysis_plan": {
        "en-US": "Protocol And Analysis Plan",
        "zh-CN": "研究方案与分析计划",
    },
    "03-data_asset_and_cohort_build": {
        "en-US": "Data Asset And Cohort Build",
        "zh-CN": "数据资产与队列构建",
    },
    "04-analysis_execution": {"en-US": "Analysis Execution", "zh-CN": "分析执行"},
    "05-evidence_synthesis": {"en-US": "Evidence Synthesis", "zh-CN": "证据综合"},
    "06-manuscript_authoring": {"en-US": "Manuscript Authoring", "zh-CN": "论文撰写"},
    "07-independent_review_and_revision": {
        "en-US": "Independent Review And Revision",
        "zh-CN": "独立评审与修订",
    },
    "08-publication_package_handoff": {
        "en-US": "Publication Package Handoff",
        "zh-CN": "投稿包交接",
    },
}


def _read_contract(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / "contracts" / f"{name}.json").read_text(encoding="utf-8"))


def test_pack_compiler_input_declares_canonical_agent_identity() -> None:
    materialized = _read_contract("pack_compiler_input")

    assert materialized["canonical_agent_id"] == "mas"
    assert materialized["domain_id"] == "medautoscience"


def test_domain_descriptor_exposes_generic_standard_agent_interface() -> None:
    descriptor = _read_contract("domain_descriptor")
    interface = descriptor["standard_agent_interface"]

    assert interface["version"] == "opl_standard_agent_interface.v1"
    assert interface["workspace_binding"] == {
        "default_profile_id": "portfolio",
        "workspace_kind": "medical_research_workspace",
        "project_kind": "study",
        "project_collection_label": "studies",
        "default_workspace_id": "research-workspace",
        "default_project_id": "study-001",
        "locator_surface_kind": "med_autoscience_workspace_profile",
        "required_locator_fields": ["profile_ref"],
        "optional_locator_fields": ["workspace_root"],
    }
    assert "entry_command_template" not in interface["workspace_binding"]
    assert "manifest_command_template" not in interface["workspace_binding"]
    assert interface["inventory_projection"] == {
        "source_kind": "workspace_relative_json",
        "relative_path": "workspace_index.json",
        "items_pointer": "/studies",
        "field_map": {
            "work_item_id": "study_id",
            "display_name": "display_name",
            "work_item_root": "canonical_study_root",
            "business_status": "status",
            "current_stage_id": "current_stage_id",
            "current_stage_status": "current_stage_status",
            "package_status": "package_status",
            "lifecycle_ref": "lifecycle_ref",
            "next_action": "next_action",
            "stage_index_ref": "stage_index_ref",
        },
    }
    assert interface["stage_catalog"] == {
        "source_kind": "agent_repo_relative_json",
        "relative_path": "contracts/mas-paper-study-stage-pack.json",
        "items_pointer": "/stages",
        "field_map": {
            "stage_id": "stage_id",
            "display_name": "display_name",
            "display_names": "display_names",
        },
    }
    assert interface["runtime"] == {
        "runtime_domain_id": "medautoscience",
        "registration_ref": "contracts/domain_route_profile.json",
    }
    assert "dispatch_command" not in interface["runtime"]
    assert interface["progress"] == {
        "deliverable_delta_aliases": ["paper_progress_delta", "paper_work_progress"],
        "platform_delta_aliases": ["runtime_transport_delta", "provider_attempt_delta"],
    }
    assert interface["routing"]["ambiguity_policy"] == (
        "require_explicit_domain_selection_when_multiple_standard_agents_match"
    )


def test_paper_study_stage_catalog_declares_stable_localized_display_names() -> None:
    stage_pack = _read_contract("mas-paper-study-stage-pack")
    stages = stage_pack["stages"]

    assert isinstance(stages, list)
    assert [stage["stage_id"] for stage in stages] == list(
        EXPECTED_PAPER_STAGE_DISPLAY_NAMES
    )
    for stage in stages:
        expected_names = EXPECTED_PAPER_STAGE_DISPLAY_NAMES[stage["stage_id"]]
        display_names = stage["display_names"]

        assert isinstance(display_names, dict)
        assert {
            locale: display_names.get(locale) for locale in expected_names
        } == expected_names
        assert stage["display_name"] == display_names["en-US"]


def test_package_manifest_routes_interface_and_lifecycle_to_opl_packages() -> None:
    manifest = _read_contract("opl_agent_package_manifest")

    assert manifest["agent_id"] == "mas"
    assert manifest["package_id"] == "mas"
    assert manifest["codex_surface"]["plugin_id"] == "med-autoscience"
    assert manifest["domain_descriptor_ref"] == "contracts/domain_descriptor.json"
    dependency = manifest["capability_dependencies"][0]
    assert all(
        command.startswith("opl packages status --package-id mas")
        for command in dependency["status_command_templates"].values()
    )
    assert all(
        command.startswith("opl packages repair mas")
        for command in dependency["repair_command_templates"].values()
    )


def test_pack_compiler_input_declares_python_helper_boundary_without_generic_runtime() -> None:
    materialized = _read_contract("pack_compiler_input")
    profile = materialized["implementation_profile"]

    assert materialized["canonical_agent_id"] == "mas"
    assert materialized["domain_id"] == "medautoscience"
    assert profile["profile_id"] == "opl.standard_domain_agent.v1"
    assert profile["agent_identity"] == "declarative_standard_agent_pack"
    assert profile["pack_formats"] == ["markdown", "json"]
    assert profile["generated_surfaces_owner"] == "one-person-lab"
    helpers = profile["helpers"]
    assert helpers["optional"] is True
    assert helpers["language_is_identity"] is False
    assert helpers["rust_policy"] == "framework_hot_path_only"

    helper_implementations = helpers["entries"]
    assert {entry["language"] for entry in helper_implementations} == {"python"}
    assert {entry["role"] for entry in helper_implementations} == {"authority_function"}
    for entry in helper_implementations:
        assert entry["source_roots"]
        for source_root in entry["source_roots"]:
            assert source_root.endswith("/"), source_root
            assert (REPO_ROOT / source_root).is_dir(), source_root


def test_owner_answer_uses_the_hosted_stage_run_contract_without_private_dispatch_abi() -> None:
    descriptor = _read_contract("domain_descriptor")
    pack_input = _read_contract("pack_compiler_input")
    projection = _read_contract("domain_projection_profile")
    state_index = _read_contract("state_index_kernel_adoption")

    assert not (REPO_ROOT / "contracts/domain_owner_answer_projection_profile.json").exists()
    contract_refs = descriptor["standard_contract_refs"]
    assert "domain_owner_answer_projection_profile" not in contract_refs
    assert contract_refs["hosted_action_runtime"] == (
        "contracts/opl-framework/standard-agent-hosted-action-runtime-contract.json"
    )
    assert contract_refs["owner_answer_schema"] == (
        "contracts/opl-framework/owner-answer.schema.json"
    )
    assert contract_refs["stage_run_kernel_profile"] == (
        "contracts/stage_run_kernel_profile.json"
    )
    assert pack_input["source_refs"]["hosted_action_runtime_contract_ref"] == (
        "contracts/opl-framework/standard-agent-hosted-action-runtime-contract.json"
    )
    assert pack_input["source_refs"]["owner_answer_schema_source_ref"] == (
        "contracts/opl-framework/owner-answer.schema.json"
    )
    assert pack_input["source_refs"]["stage_run_kernel_profile_ref"] == (
        "contracts/stage_run_kernel_profile.json"
    )
    assert "contracts/domain_owner_answer_projection_profile.json" not in pack_input[
        "required_domain_pack_paths"
    ]
    assert projection["source_contract_refs"] == [
        "contracts/domain_descriptor.json",
        "contracts/opl-framework/standard-agent-hosted-action-runtime-contract.json",
        "contracts/opl-framework/owner-answer.schema.json",
        "contracts/stage_run_kernel_profile.json",
        "contracts/action_catalog.json",
    ]
    assert state_index["projection_source_refs"] == [
        "contracts/domain_descriptor.json",
        "contracts/stage_run_kernel_profile.json",
        "agent/stages/manifest.json",
    ]

    active_payload = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (REPO_ROOT / "agent", REPO_ROOT / "contracts", REPO_ROOT / "runtime")
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".json", ".yaml", ".yml", ".md"}
    )
    for retired_token in (
        "domain_owner/default-executor-dispatch",
        "complete_medical_paper",
        "artifacts/medical_paper/readiness_owner_receipt.json",
        "artifacts/medical_paper/readiness_typed_blocker.json",
    ):
        assert retired_token not in active_payload


def test_stage_run_kernel_profile_has_the_exact_generic_base_abi() -> None:
    profile = _read_contract("stage_run_kernel_profile")

    assert {
        "surface_kind": profile["surface_kind"],
        "version": profile["version"],
        "domain_id": profile["domain_id"],
        "kernel_contract_ref": profile["kernel_contract_ref"],
        "kernel_role": profile["kernel_role"],
        "stage_native_unit": profile["stage_native_unit"],
        "required_object_models": profile["required_object_models"],
        "authority_boundary": profile["authority_boundary"],
    } == {
        "surface_kind": "opl_stage_run_kernel_profile",
        "version": "stage-run-kernel-profile.v1",
        "domain_id": "medautoscience",
        "kernel_contract_ref": "contracts/opl-framework/stage-run-kernel-contract.json",
        "kernel_role": "minimal_state_shell_not_domain_controller_system",
        "stage_native_unit": [
            "stage_folder",
            "stage_manifest",
            "role_artifacts",
            "progress_receipt_or_owner_answer_or_hard_stop",
        ],
        "required_object_models": [
            "StageRun",
            "RoleArtifactRef",
            "ProgressDeltaReceipt",
            "OwnerReceipt",
            "TypedBlocker",
            "ReadModel",
        ],
        "authority_boundary": {
            "opl_can_write_domain_truth": False,
            "opl_can_mutate_artifact_body": False,
            "opl_can_sign_domain_owner_receipt": False,
            "opl_can_create_typed_blocker": False,
            "opl_can_authorize_quality_or_export": False,
            "provider_completion_counts_as_domain_accepted": False,
            "read_model_can_be_truth_source": False,
        },
    }
    assert profile["stage_run_state_machine"]["file_presence_counts_as_stage_complete"] is False
    assert "ArtifactRef" not in profile["object_models"]
    assert "RoleArtifactRef" in profile["object_models"]
    assert "source_design_ref" not in profile
    assert "opl_mas_boundary" not in profile
    assert "can_write_mas_truth" not in json.dumps(profile)


def test_machine_identity_fields_match_the_framework_registry_semantics() -> None:
    forbidden: dict[str, list[str]] = {}

    def visit(value: object, location: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                child = f"{location}.{key}"
                if key in {
                    "domain_id",
                    "target_domain_id",
                    "runtime_domain_id",
                    "stage_control_plane_target_domain_id",
                } and item in {"mas", "med-autoscience"}:
                    forbidden.setdefault(child, []).append(str(item))
                visit(item, child)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, f"{location}[{index}]")

    for root in (REPO_ROOT / "agent", REPO_ROOT / "contracts", REPO_ROOT / "runtime"):
        for path in sorted(root.rglob("*.json")):
            visit(json.loads(path.read_text(encoding="utf-8")), path.relative_to(REPO_ROOT).as_posix())

    assert forbidden == {}
    canonical_top_level_fields = {
        "agent/stages/manifest.json": "target_domain_id",
        "contracts/action_catalog.json": "target_domain_id",
        "contracts/agent_lab_handoff.json": "domain_id",
        "contracts/artifact_locator_contract.json": "domain_id",
        "contracts/capability_map.json": "domain_id",
        "contracts/domain_descriptor.json": "domain_id",
        "contracts/domain_projection_profile.json": "domain_id",
        "contracts/domain_route_profile.json": "domain_id",
        "contracts/foundry_agent_series.json": "domain_id",
        "contracts/generated_surface_handoff.json": "domain_id",
        "contracts/memory_descriptor.json": "target_domain_id",
        "contracts/owner_receipt_contract.json": "domain_id",
        "contracts/pack_compiler_input.json": "domain_id",
        "contracts/private_functional_surface_policy.json": "domain_id",
        "contracts/runtime_environment_requirements.json": "domain_id",
        "contracts/stage_artifact_kernel_adoption.json": "domain_id",
        "contracts/stage_operating_principles.json": "domain_id",
        "contracts/stage_quality_cycle_policy.json": "domain_id",
        "contracts/stage_run_canary_evidence.json": "domain_id",
        "contracts/stage_run_kernel_profile.json": "domain_id",
        "contracts/standard-agent-principles-adoption.json": "domain_id",
        "contracts/standard_agent_conformance_profile.json": "target_domain_id",
        "contracts/state_index_kernel_adoption.json": "domain_id",
        "contracts/workspace_lifecycle_policy.json": "domain_id",
    }
    for relative_path, field in canonical_top_level_fields.items():
        payload = json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))
        assert payload[field] == "medautoscience", (relative_path, field, payload[field])

    stage_manifest = json.loads(
        (REPO_ROOT / "agent/stages/manifest.json").read_text(encoding="utf-8")
    )
    assert stage_manifest["owner"] == "medautoscience"
    assert stage_manifest["authority_boundary"]["domain_truth_owner"] == "medautoscience"

    audit = _read_contract("functional_privatization_audit")
    assert audit["domain_id"] == audit["target_domain_id"] == "medautoscience"
    assert _read_contract("foundry_agent_series")["stage_control_plane_target_domain_id"] == (
        "medautoscience"
    )
    assert _read_contract("domain_descriptor")["standard_agent_interface"]["runtime"] == {
        "runtime_domain_id": "medautoscience",
        "registration_ref": "contracts/domain_route_profile.json",
    }
    stage_pack = _read_contract("mas-paper-study-stage-pack")
    assert stage_pack["physical_stage_folder_kernel"]["locator"]["domain_id"] == (
        "medautoscience"
    )
    assert _read_contract("pack_compiler_input")["canonical_agent_id"] == "mas"
    assert _read_contract("domain_route_profile")["agent_id"] == "mas"
    assert _read_contract("domain_projection_profile")["agent_id"] == "mas"
    assert _read_contract("state_index_kernel_adoption")["agent_id"] == "mas"
    assert _read_contract("opl_agent_package_manifest")["codex_surface"]["plugin_id"] == (
        "med-autoscience"
    )
    semantic_pack = (REPO_ROOT / "agent/stages/stage_native_semantic_pack.yaml").read_text(
        encoding="utf-8"
    )
    assert "target_domain_id: med-autoscience" not in semantic_pack
    assert "target_domain_id: medautoscience" in semantic_pack

def test_zero_readable_stage_output_is_a_progress_diagnostic() -> None:
    stage_manifest = json.loads(
        (REPO_ROOT / "agent/stages/manifest.json").read_text(encoding="utf-8")
    )
    progress_policy = stage_manifest["progress_first_policy"]
    assert progress_policy["semantic_route_decision_owner"] == "decisive_codex_attempt"
    assert progress_policy["stage_transition_materialization_owner"] == (
        "opl_stage_run_controller"
    )
    assert "route_selection_owner" not in progress_policy
    assert progress_policy["primary_only_decisive_attempt_role"] == "producer"
    assert progress_policy["formal_review_decisive_attempt_roles"] == [
        "reviewer",
        "re_reviewer",
    ]
    assert progress_policy["repairer_can_be_decisive_attempt"] is False
    assert progress_policy["codex_may_advance_skip_repeat_reverse_or_route_back"] is True
    assert progress_policy["any_declared_stage_may_start_from_any_prior_stage_result"] is True
    assert progress_policy["declared_requires_are_quality_context_not_launch_gates"] is True
    assert progress_policy["next_stage_refs_are_recommendations_not_constraints"] is True
    assert progress_policy["no_output_or_failure_diagnostic_advances_stage"] is True

    policies = [
        stage["stage_contract_extension"]["hypothesis_portfolio_evidence_pack"]["missing_ref_output_policy"]
        for stage in stage_manifest["stages"]
    ]
    assert policies
    for policy in policies:
        assert policy["zero_readable_artifact"] == "no_output_diagnostic"
        assert policy["quality_debt_blocks_stage_transition"] is False
