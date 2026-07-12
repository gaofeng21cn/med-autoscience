from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_contract(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / "contracts" / f"{name}.json").read_text(encoding="utf-8"))


def test_pack_compiler_input_declares_canonical_agent_identity() -> None:
    materialized = _read_contract("pack_compiler_input")

    assert materialized["canonical_agent_id"] == "mas"
    assert materialized["domain_id"] == "mas"


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
        "entry_command_template": interface["workspace_binding"]["entry_command_template"],
        "manifest_command_template": interface["workspace_binding"]["manifest_command_template"],
    }
    for command_field in ("entry_command_template", "manifest_command_template"):
        command = interface["workspace_binding"][command_field]
        assert command[:7] == [
            "uv",
            "run",
            "--isolated",
            "--frozen",
            "--project",
            "{workspace_root}",
            "python",
        ]
        assert command[-1] == "{profile_ref}"
    assert interface["runtime"] == {
        "runtime_domain_id": "mas",
        "dispatch_command": None,
        "registration_ref": "contracts/domain_route_profile.json",
    }
    assert interface["progress"] == {
        "deliverable_delta_aliases": ["paper_progress_delta", "paper_work_progress"],
        "platform_delta_aliases": ["runtime_transport_delta", "provider_attempt_delta"],
    }
    assert interface["routing"]["ambiguity_policy"] == (
        "require_explicit_domain_selection_when_multiple_standard_agents_match"
    )


def test_package_manifest_routes_interface_and_lifecycle_to_opl_connect() -> None:
    manifest = _read_contract("opl_agent_package_manifest")

    assert manifest["domain_descriptor_ref"] == "contracts/domain_descriptor.json"
    dependency = manifest["capability_dependencies"][0]
    assert all(
        command.startswith("opl connect agent-packages status --package-id mas")
        for command in dependency["status_command_templates"].values()
    )
    assert all(
        command.startswith("opl connect agent-packages repair --package-id mas")
        for command in dependency["repair_command_templates"].values()
    )


def test_pack_compiler_input_declares_python_helper_boundary_without_generic_runtime() -> None:
    materialized = _read_contract("pack_compiler_input")
    profile = materialized["implementation_profile"]

    assert materialized["canonical_agent_id"] == "mas"
    assert materialized["domain_id"] == "mas"
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
    assert {entry["role"] for entry in helper_implementations} == {"domain_helper"}
    for entry in helper_implementations:
        assert entry["source_roots"]
        for source_root in entry["source_roots"]:
            assert source_root.endswith("/"), source_root
            assert (REPO_ROOT / source_root).is_dir(), source_root


def test_domain_owner_answer_projection_profile_is_domain_owned_and_refs_only() -> None:
    descriptor = _read_contract("domain_descriptor")
    profile = _read_contract("domain_owner_answer_projection_profile")

    assert descriptor["standard_contract_refs"]["domain_owner_answer_projection_profile"] == (
        "contracts/domain_owner_answer_projection_profile.json"
    )
    assert profile["surface_kind"] == "opl_domain_owner_answer_projection_profile"
    assert profile["version"] == "domain-owner-answer-projection-profile.v1"
    assert profile["profile_role"] == "registry"
    assert profile["domain_id"] == "medautoscience"
    assert profile["binding_project_id"] == "medautoscience"
    assert profile["checkout_currentness_required"] is True
    assert profile["projection_relative_path"] == [
        "artifacts",
        "publication_handoff",
        "owner_receipt.json",
    ]
    assert profile["authority_boundary"] == {
        "refs_only": True,
        "can_write_domain_truth": False,
        "can_create_owner_receipt": False,
        "can_create_typed_blocker": False,
        "can_claim_domain_ready": False,
        "can_claim_production_ready": False,
    }


def test_opl_standard_pack_declares_single_ordinary_default_stage() -> None:
    stage_manifest = json.loads(
        (REPO_ROOT / "agent/stages/manifest.json").read_text(encoding="utf-8")
    )
    profile = _read_contract("golden_path_profile")

    stages = stage_manifest["stages"]
    assert isinstance(stages, list)
    default_stage_ids = [stages[0]["stage_id"]]

    assert default_stage_ids == profile["ordinary_path"]["stage_refs"] == [
        "direction_and_route_selection"
    ]
    assert profile["ordinary_path"]["path_role"] == "ordinary_default"
    assert profile["default_surface_policy"]["ordinary_route_count"] == 1
