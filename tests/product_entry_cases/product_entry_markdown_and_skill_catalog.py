from __future__ import annotations

from .product_entry_preflight_and_task_submission import *  # noqa: F403,F401


def test_build_skill_catalog_projects_recommended_shell_and_direct_activation_hints(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_text(
        profile.workspace_root / "contracts" / "runtime-program" / "current-program.json",
        json.dumps(
            {
                "schema_version": 1,
                "program_id": "research-foundry-medical-mainline",
                "title": "Medical Research Mainline",
                "current_phase_id": "phase_2_user_product_loop",
                "phases": [
                    {
                        "phase_id": "phase_2_user_product_loop",
                        "label": "Phase 2",
                        "status": "active",
                        "summary": "继续收口 blocker 并把用户入口壳压实。",
                        "exit_criteria": ["todo"],
                    }
                ],
                "active_tranche_id": "f4_blocker_closeout",
            },
            ensure_ascii=False,
        ),
    )
    write_study(profile.workspace_root, "001-risk")

    payload = module.build_skill_catalog(profile=profile, profile_ref=profile_ref)

    assert payload["surface_kind"] == "skill_catalog"
    assert payload["recommended_shell"] == "workspace_cockpit"
    assert payload["recommended_command"].endswith(
        "opl app workbench --agent med-autoscience --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["manifest_command"].endswith(
        "product-entry-manifest --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert payload["skills"][0]["domain_projection"]["skill_entry"] == "mas"
    assert payload["skills"][0]["domain_projection"]["recommended_shell"] == "workspace_cockpit"
    assert payload["skills"][0]["descriptor_owner"] == "one-person-lab"
    assert payload["skills"][0]["domain_repo_can_own_generated_surface"] is False
    assert payload["skills"][0]["domain_handler_target"] == "MedAutoScienceDomainEntry"
    assert payload["skills"][0]["domain_handler_target_owner"] == "MedAutoScience"
    assert payload["skills"][0]["descriptor_role"] == (
        "opl_generated_skill_descriptor_targeting_mas_domain_entry"
    )
    runtime_manager_registration = payload["skills"][0]["domain_projection"]["opl_runtime_manager_registration"]
    assert payload["skills"][0]["domain_projection"]["opl_stage_runtime_registration"] == runtime_manager_registration
    assert runtime_manager_registration["surface_kind"] == "opl_runtime_manager_domain_registration"
    assert runtime_manager_registration["registration_id"] == "mas.opl_runtime_manager.registration.v1"
    assert runtime_manager_registration["domain_id"] == "medautoscience"
    assert runtime_manager_registration["registration_surface"]["command"].endswith(
        "skill-catalog --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert (
        "/progress_projection/domain_projection/research_runtime_control_projection"
        in runtime_manager_registration["consumable_projection_refs"]
    )
    assert runtime_manager_registration["state_index_inputs"]["artifact_projection_index"] == "/artifact_inventory"
    native_helper_consumption = runtime_manager_registration["native_helper_consumption"]
    assert native_helper_consumption["protocol_ref"] == "contracts/opl-framework/native-helper-contract.json"
    assert native_helper_consumption["language"] == "rust"
    assert native_helper_consumption["indexes"]["artifact_projection_index"]["backing_helper_id"] == "opl-artifact-indexer"
    assert native_helper_consumption["indexes"]["runtime_health_snapshot_index"]["backing_helper_id"] == "opl-runtime-watch"
    assert native_helper_consumption["source_of_truth_rule"].startswith("Rust helpers may index MAS")
    proof_surface = native_helper_consumption["proof_surface"]
    assert proof_surface["surface_kind"] == "mas_opl_native_helper_indexing_proof"
    assert proof_surface["proof_id"] == "mas.opl_native_helper.indexing_proof.v1"
    assert proof_surface["allowed_operation"] == "index_only"
    assert proof_surface["runtime_surface_refs"] == [
        "/skill_catalog/skills/0/domain_projection/runtime_continuity",
        "/progress_projection/domain_projection/research_runtime_control_projection",
        "/runtime_inventory",
    ]
    assert proof_surface["product_entry_surface_refs"] == [
        "/skill_catalog/skills/0/domain_projection/opl_stage_runtime_registration/domain_entry_surface",
        "/skill_catalog/skills/0/domain_projection/opl_stage_runtime_registration/registration_surface",
        "/skill_catalog/skills/0/domain_projection/opl_runtime_manager_registration/domain_entry_surface",
        "/skill_catalog/skills/0/domain_projection/opl_runtime_manager_registration/registration_surface",
        "/artifact_inventory/artifact_surface",
        "/automation/automations/0",
    ]
    assert proof_surface["authority_boundary"] == {
        "domain_truth_owner": "MedAutoScience",
        "helper_owner": "one-person-lab",
        "helper_write_policy": "no_domain_truth_writes",
        "authoritative_truth_refs": [
            "/progress_projection",
            "/domain_health_diagnostic",
            "/publication_eval/latest.json",
            "/controller_decisions/latest.json",
        ],
    }
    native_helper_contract = json.loads(Path(native_helper_consumption["protocol_ref"]).read_text(encoding="utf-8"))
    assert native_helper_contract["surface_kind"] == "opl_native_helper_consumption_contract"
    assert native_helper_contract["consumer_domain"] == "medautoscience"
    assert native_helper_contract["authority_boundary"]["domain_truth_owner"] == "MedAutoScience"
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
