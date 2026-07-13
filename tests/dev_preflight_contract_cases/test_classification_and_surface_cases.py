from __future__ import annotations

import importlib

from med_autoscience.dev_preflight_contract import PreflightCoveragePathFamily


def _all_category_exact_paths(module) -> tuple[str, ...]:
    return tuple(dict.fromkeys(path for spec in module._CATEGORY_SPECS for path in spec.exact_paths))


def _category_path_families(module) -> tuple:
    return tuple(
        PreflightCoveragePathFamily(
            family_id=spec.category_id,
            exact_paths=spec.exact_paths,
            prefix_paths=spec.prefix_paths,
        )
        for spec in module._CATEGORY_SPECS
    )


def test_preflight_category_audit_keeps_spec_paths_explicit() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    audit = module.audit_preflight_contract_coverage(
        _all_category_exact_paths(module),
        path_families=_category_path_families(module),
    )

    assert audit.generic_python_regression_paths == ()
    assert audit.fail_closed_paths == ()
    assert all(
        family_audit.family_id in family_audit.explicit_categories
        for family_audit in audit.family_audits
        if family_audit.explicit_classified_paths
    )


def test_classify_changed_files_matches_runtime_contract_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/references/example-runtime-note.md",
            "docs/runtime/example-runtime-contract.md",
            "contracts/runtime/mas-live-runtime-evidence-rollup.json",
            "contracts/runtime/mas-live-runtime-gap-work-orders.json",
            "contracts/runtime/mas-runtime-live-tail-work-orders.json",
            "contracts/runtime/mas-root-cause-depth-gate.json",
            "src/med_autoscience/profiles.py",
            "profiles/workspace.profile.template.toml",
            "src/med_autoscience/controllers/study_outer_loop/__init__.py",
            "src/med_autoscience/controllers/study_runtime_decision/__init__.py",
            "src/med_autoscience/controllers/study_runtime_resolution.py",
            "src/med_autoscience/controllers/domain_status_projection.py",
            "tests/test_profiles.py",
            "tests/test_opl_runtime_contract.py",
            "tests/test_workspace_runtime_layout.py",
            "tests/test_study_runtime_domain_status.py",
        ]
    )

    assert result.matched_categories == ("documentation_review_only", "runtime_contract_surface")
    assert result.unclassified_changes == ()


def test_classify_changed_files_routes_display_docs_to_review_only() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/delivery/example-capability-guide.md",
        ]
    )

    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_routes_display_pack_config_to_publication_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(["config/display_packs.toml"])

    assert result.matched_categories == ("display_publication_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "make test-paths -- tests/display_schema_contract_cases -q",
        "make test-paths -- tests/test_display_surface_materialization.py -q",
        "make test-paths -- tests/test_display_layout_qc.py -q",
        "make test-paths -- tests/test_publication_gate_cases -q",
        "make test-paths -- tests/medical_publication_surface_cases -q",
    ]


def test_classify_changed_files_routes_branding_assets_to_review_only() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "assets/branding/medautoscience-overview-v2.png",
        ]
    )

    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_routes_publication_route_memory_fixture_to_owner_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/policies/study-workflow/publication_route_memory_policy.md",
            "docs/policies/study-workflow/publication_route_memory_seed_fixture.json",
            "src/med_autoscience/controllers/research_memory/publication_route_memory_cards.py",
            "tests/test_research_memory.py",
        ]
    )

    assert result.matched_categories == (
        "documentation_review_only",
        "publication_route_memory_surface",
    )
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "make test-paths -- tests/test_research_memory.py -q",
        "make test-paths -- tests/test_opl_family_contract_adoption.py -q",
    ]


def test_classify_changed_files_routes_mcp_plugin_config_to_codex_plugin_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "plugins/med-autoscience/skills/med-autoscience/SKILL.md",
        ]
    )

    assert result.matched_categories == ("codex_plugin_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_flags_unclassified_paths() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/active/untracked_runtime_contract.md",
        ]
    )

    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_routes_unknown_python_to_generic_smoke() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/new_controller.py",
            "tests/test_new_controller.py",
        ]
    )

    assert result.matched_categories == ("generic_python_smoke_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == ["make test-smoke"]


def test_classify_changed_files_keeps_unknown_docs_fail_closed() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(["docs/active/new_runtime_contract.md"])

    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()


def test_audit_preflight_contract_coverage_identifies_explicit_classification() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    audit = module.audit_preflight_contract_coverage(
        ["src/med_autoscience/controllers/domain_status_projection.py"],
        path_families=(
            module.PreflightCoveragePathFamily(
                family_id="controller_sources",
                exact_paths=(),
                prefix_paths=("src/med_autoscience/controllers/",),
            ),
        ),
    )

    assert audit.explicit_classified_paths == (
        "src/med_autoscience/controllers/domain_status_projection.py",
    )
    assert audit.generic_python_regression_paths == ()
    assert audit.fail_closed_paths == ()
    assert audit.family_audits[0].explicit_categories == ("runtime_contract_surface",)
    assert audit.family_audits[0].explicit_classified_paths == (
        "src/med_autoscience/controllers/domain_status_projection.py",
    )


def test_audit_preflight_contract_coverage_marks_generic_python_fallback() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    audit = module.audit_preflight_contract_coverage(
        [
            "src/med_autoscience/controllers/new_controller.py",
            "tests/test_new_controller.py",
        ],
        path_families=(
            module.PreflightCoveragePathFamily(
                family_id="controller_sources",
                exact_paths=(),
                prefix_paths=("src/med_autoscience/controllers/",),
            ),
            module.PreflightCoveragePathFamily(
                family_id="test_sources",
                exact_paths=(),
                prefix_paths=("tests/",),
            ),
        ),
    )

    assert audit.explicit_classified_paths == ()
    assert audit.generic_python_regression_paths == (
        "src/med_autoscience/controllers/new_controller.py",
        "tests/test_new_controller.py",
    )
    assert audit.fail_closed_paths == ()
    assert audit.generic_python_regression_families == (
        "controller_sources",
        "test_sources",
    )


def test_audit_preflight_contract_coverage_keeps_docs_review_only_and_workflow_fail_closed() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    audit = module.audit_preflight_contract_coverage(
        [
            "docs/active/new_runtime_contract.md",
            ".github/workflows/new-release.yml",
            "tox.ini",
        ],
        path_families=(
            module.PreflightCoveragePathFamily(
                family_id="program_docs",
                exact_paths=(),
                prefix_paths=("docs/active/",),
            ),
            module.PreflightCoveragePathFamily(
                family_id="workflow_config",
                exact_paths=("tox.ini",),
                prefix_paths=(".github/workflows/",),
            ),
        ),
    )

    assert audit.explicit_classified_paths == ("docs/active/new_runtime_contract.md",)
    assert audit.generic_python_regression_paths == ()
    assert audit.fail_closed_paths == (
        ".github/workflows/new-release.yml",
        "tox.ini",
    )
    assert audit.fail_closed_families == ("workflow_config",)


def test_classify_changed_files_matches_control_plane_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "agent/stages/manifest.json",
            "scripts/real-paper-autonomy-soak-inventory.py",
            "src/med_autoscience/controllers/domain_authority_snapshot.py",
            "src/med_autoscience/controllers/delivery_artifact_authority.py",
            "src/med_autoscience/controllers/delivery_authority_backfill_apply.py",
            "src/med_autoscience/controllers/opl_provider_ready_adapter/__init__.py",
            "src/med_autoscience/controllers/owner_route_handoff/domain_handler_export.py",
            "src/med_autoscience/controllers/owner_route_handoff/dispatch_orchestration.py",
            "src/med_autoscience/controllers/control_identity.py",
            "src/med_autoscience/controllers/study_progress/projection.py",
            "src/med_autoscience/controllers/study_progress/projection_quality_surfaces.py",
            "src/med_autoscience/controllers/study_progress/projection_runtime_surfaces.py",
            "src/med_autoscience/controllers/study_delivery_sync/sync_orchestration.py",
            "src/med_autoscience/controllers/study_delivery_sync/sync_cli.py",
            "tests/test_autonomy_state_surface.py",
            "tests/test_delivery_artifact_authority.py",
            "tests/test_delivery_authority_backfill_apply.py",
        ]
    )

    assert result.matched_categories == (
        "standard_agent_pack_surface",
        "control_plane_surface",
    )
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_owner_answer_candidate_intake_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/owner_answer_candidate_intake.py",
            "tests/test_owner_answer_candidate_intake.py",
        ]
    )

    assert result.matched_categories == ("owner_answer_candidate_intake_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "make test-paths -- tests/test_owner_answer_candidate_intake.py -q",
    ]


def test_classify_changed_files_matches_study_owner_gate_decision_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/study_interventions.py",
            "tests/test_study_interventions.py",
        ]
    )

    assert result.matched_categories == ("study_owner_gate_decision_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "make test-paths -- tests/test_study_interventions.py -q",
    ]


def test_classify_changed_files_matches_paper_progress_transition_boundary_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "contracts/opl_domain_progress_transition_runtime_contract.json",
            "contracts/paper_progress_replay_live_evidence_status.json",
            "contracts/paper_progress_transition_runtime_completion_audit.json",
            "contracts/runtime/mas-runtime-surface-retirement-inventory.json",
            "docs/active/mas-ideal-state-gap-plan.md",
            "docs/runtime/control/controllers.md",
            "docs/runtime/designs/" + "paper_progress_" + "transition_kernel_target.md",
            "docs/status.md",
            "src/med_autoscience/controllers/opl_domain_progress_transition_contract.py",
            "src/med_autoscience/controllers/opl_transition_readback.py",
            "src/med_autoscience/controllers/paper_progress_policy_adapter.py",
            "tests/test_opl_domain_progress_transition_runtime_contract.py",
            "tests/test_opl_transition_readback_contract.py",
            "tests/test_mas_workspace_domain_projection.py",
        ]
    )

    assert result.matched_categories == (
        "paper_progress_transition_boundary_surface",
        "documentation_review_only",
    )
    assert result.unclassified_changes == ()
    planned_commands = module.plan_commands_for_categories(result.matched_categories)
    assert "make test-control-plane" not in planned_commands
    assert (
        "make test-paths -- "
        "tests/test_opl_transition_readback_contract.py "
        "tests/test_mas_workspace_domain_projection.py "
        "tests/test_live_stage_run_progress_evidence.py -q"
    ) in planned_commands
    assert (
        "make test-paths -- "
        "tests/test_opl_domain_progress_transition_runtime_contract.py -q"
    ) in planned_commands


def test_classify_changed_files_covers_current_contract_and_carrier_surfaces() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "agent/primary_skill/SKILL.md",
            "contracts/agent_tool_arsenal.json",
            "contracts/capability_map.json",
            "contracts/domain_projection_profile.json",
            "contracts/domain_route_profile.json",
            "contracts/hosted_ordinary_path_consumption.json",
            "contracts/live_stage_run_progress_evidence.json",
            "contracts/paper_autonomy_live_supervisor_canary_contract.json",
            "contracts/paper_autonomy_supervisor_contract.json",
            "contracts/research-integrity-layer.json",
            "contracts/runtime_environment_requirements.json",
            "contracts/standard-agent-principles-adoption.json",
            "plugins/med-autoscience/bin/medautosci-mcp",
            "scripts/opl-module-healthcheck.sh",
        ]
    )

    assert result.matched_categories == (
        "standard_agent_pack_surface",
        "production_acceptance_surface",
        "paper_progress_transition_boundary_surface",
        "research_integrity_surface",
        "runtime_contract_surface",
        "codex_plugin_surface",
        "family_shared_surface",
    )
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_optional_provider_archive_audit_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/active/example-runtime-gate.md",
            "docs/references/example-workspace-note.md",
            "src/med_autoscience/workspace_contracts.py",
        ]
    )

    assert result.matched_categories == ("documentation_review_only", "optional_provider_archive_audit_surface")
    assert result.unclassified_changes == ()


def test_classify_changed_files_routes_public_docs_to_review_only() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "README.md",
            "README.zh-CN.md",
            "bootstrap/README.md",
            "docs/example.md",
            "docs/references/example-reference.md",
        ]
    )

    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_ci_workflow_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            ".github/workflows/advisory.yml",
            ".github/workflows/ci.yml",
            "tests/test_release_workflow.py",
        ]
    )

    assert result.matched_categories == ("workflow_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_packaging_workflow_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "MANIFEST.in",
            "setup.py",
            "tests/test_release_workflow.py",
        ]
    )

    assert result.matched_categories == ("workflow_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_integration_harness_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "docs/history/program/example-history-board.md",
            "docs/active/example-backend-map.md",
            "docs/references/example-phase-ladder.md",
            "scripts/prepare-sentrux-gitstats-clone.sh",
            "tests/test_sentrux_gitstats_helper.py",
        ]
    )

    assert result.matched_categories == ("documentation_review_only", "integration_harness_surface")
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_family_shared_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "pyproject.toml",
            "uv.lock",
            "Makefile",
            "scripts/verify.sh",
            "src/med_autoscience/dev_preflight.py",
            "src/med_autoscience/dev_preflight_contract/__init__.py",
            "tests/test_framework_python_carrier.py",
            "tests/test_dev_preflight.py",
            "tests/test_dev_preflight_contract.py",
            "tests/fixtures/opl_agent_lab_longline.json",
            "tests/test_foundry_agent_series_consumer_contract.py",
            "tests/test_opl_agent_lab_longline_migration.py",
        ]
    )

    assert result.matched_categories == ("workflow_surface", "family_shared_surface")
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_root_governance_contract_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "AGENTS.md",
            "TASTE.md",
            "agent/standard-domain-agent-anchor.json",
            "contracts/README.md",
            "contracts/test-lane-manifest.json",
            "contracts/runtime/legacy-active-path-tombstones.json",
            "contracts/runtime/standard-domain-agent-anchor.json",
            "contracts/modules/runtime/module_contract.yaml",
            "contracts/opl-framework/family-contract-adoption.json",
            "contracts/schemas/v1/product-entry-manifest.schema.json",
            "runtime/artifact_locator/workspace-runtime-artifact-root.locator.json",
            "tests/runtime/test_runtime_module_contract.py",
            "tests/test_opl_family_contract_adoption.py",
            "tests/test_opl_family_persistence_adapter.py",
            "tests/test_test_lane_governance.py",
        ]
    )

    assert result.matched_categories == (
        "root_governance_contract_surface",
        "external_learning_sidecar_surface",
    )
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_standard_agent_pack_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "agent/knowledge/medical_research_truth.md",
            "agent/knowledge/publication_route_memory.md",
            "agent/knowledge/source_readiness_and_artifact_authority.md",
            "agent/prompts/baseline_and_evidence_setup.md",
            "agent/prompts/bounded_analysis_campaign.md",
            "agent/prompts/direction_and_route_selection.md",
            "agent/prompts/finalize_and_publication_handoff.md",
            "agent/prompts/manuscript_authoring.md",
            "agent/prompts/review_and_quality_gate.md",
            "agent/quality_gates/ai_reviewer_auditor_gate.md",
            "agent/quality_gates/artifact_source_authority_gate.md",
            "agent/skills/medical_research_execution.md",
            "agent/skills/owner_receipt_and_route_control.md",
            "agent/stages/baseline_and_evidence_setup.policy.md",
            "agent/stages/bounded_analysis_campaign.policy.md",
            "agent/stages/direction_and_route_selection.policy.md",
            "agent/stages/finalize_and_publication_handoff.policy.md",
            "agent/stages/manuscript_authoring.policy.md",
            "agent/stages/review_and_quality_gate.policy.md",
            "contracts/action_catalog.json",
            "contracts/authority_kernel_inventory.json",
            "contracts/functional_privatization_audit.json",
            "contracts/generated_surface_handoff.json",
            "contracts/foundry_agent_series.json",
            "contracts/golden_path_profile.json",
            "contracts/mas-paper-study-stage-pack.json",
            "contracts/pack_compiler_input.json",
            "contracts/paper_mission_run_contract.json",
            "contracts/standard_agent_completion_acceptance.json",
            "contracts/standard_agent_completion_evidence_status.json",
            "contracts/stage_artifact_kernel_adoption.json",
            "contracts/stage_route_reconcile_contract.json",
            "contracts/stage_run_kernel_profile.json",
            "templates/codex/medautoscience-entry.SKILL.md",
            "templates/openclaw/medautoscience-entry.prompt.md",
        ]
    )

    assert result.matched_categories == ("standard_agent_pack_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        (
            "make test-paths -- "
            "tests/test_opl_family_contract_adoption.py "
            "tests/test_progress_first_safety_envelope_contract.py "
            "tests/test_standard_agent_completion_acceptance_contract.py "
            "tests/test_test_lane_governance.py "
            "tests/test_stage_quality_contract.py "
            "tests/test_stage_route_contract.py "
            "tests/test_stage_route_reconcile_contract.py -q"
        ),
        "make test-paths -- tests/test_domain_route_profile.py -q",
        "make test-paths -- tests/test_mas_workspace_domain_projection.py -q",
    ]


def test_classify_changed_files_covers_current_standard_agent_contract_paths() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "agent/principles/opl-standard-agent-principles.md",
            "agent/tools/domain_affordances.md",
            "contracts/opl_agent_package_manifest.json",
            "contracts/stage_operating_principles.json",
            "contracts/state_index_kernel_adoption.json",
        ]
    )

    assert result.matched_categories == (
        "standard_agent_pack_surface",
        "control_plane_surface",
    )
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_external_learning_sidecar_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "contracts/opl-framework/family-contract-adoption.json",
            "contracts/progress_first_safety_envelope.json",
            "src/med_autoscience/external_learning_adoption_closure/__init__.py",
            "src/med_autoscience/external_learning_authoring_advisory.py",
            "src/med_autoscience/external_learning_progress_workers.py",
            "src/med_autoscience/external_learning_review_advisory.py",
            "tests/test_external_learning_adoption_closure.py",
            "tests/test_opl_family_contract_adoption.py",
            "tests/test_progress_first_safety_envelope_contract.py",
        ]
    )

    assert result.matched_categories == (
        "root_governance_contract_surface",
        "external_learning_sidecar_surface",
        "standard_agent_pack_surface",
    )
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        (
            "make test-paths -- "
            "tests/controller_charter/test_controller_charter_module_contract.py "
            "tests/runtime/test_runtime_module_contract.py "
            "tests/eval_hygiene/test_eval_hygiene_module_contract.py "
            "tests/integration/test_monorepo_scaffold_boundaries.py -q"
        ),
        "make test-paths -- tests/test_opl_family_contract_adoption.py -q",
        "make test-paths -- tests/test_opl_family_persistence_adapter.py -q",
        "make test-paths -- tests/test_test_lane_governance.py -q",
        (
            "make test-paths -- "
            "tests/test_opl_family_contract_adoption.py "
            "tests/test_progress_first_safety_envelope_contract.py "
            "tests/test_standard_agent_completion_acceptance_contract.py "
            "tests/test_test_lane_governance.py "
            "tests/test_stage_quality_contract.py "
            "tests/test_stage_route_contract.py "
            "tests/test_stage_route_reconcile_contract.py -q"
        ),
        "make test-paths -- tests/test_domain_route_profile.py -q",
        "make test-paths -- tests/test_mas_workspace_domain_projection.py -q",
        (
            "make test-paths -- "
            "tests/test_external_learning_adoption_closure.py "
            "tests/test_opl_family_contract_adoption.py "
            "tests/test_progress_first_safety_envelope_contract.py -q"
        ),
        "make test-meta",
    ]


def test_classify_changed_files_matches_evo_scientist_pattern_boundary() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "contracts/evo_scientist_progress_accelerator.json",
            "src/med_autoscience/evo_scientist_learning_projection.py",
            "tests/test_evo_scientist_learning_projection.py",
        ]
    )

    assert result.matched_categories == ("evo_scientist_pattern_boundary",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "make test-paths -- tests/test_evo_scientist_learning_projection.py -q",
    ]


def test_classify_changed_files_matches_data_asset_display_and_overlay_contracts() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "contracts/data_asset_operating_contract.json",
            "contracts/display-pack-contract.v2.json",
            "contracts/figure_polish_lifecycle_contract.json",
            "contracts/medical_figure_spec_contract.json",
            "contracts/publication_figure_quality_contract.json",
            "src/med_autoscience/resources/stage_route_contract.yaml",
        ]
    )

    assert result.matched_categories == (
        "data_asset_operating_surface",
        "display_pack_v2_contract_surface",
        "standard_agent_pack_surface",
    )
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_production_acceptance_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "contracts/agent_lab_handoff.json",
            "contracts/production_acceptance/mas-multiprofile-guarded-apply-receipt-scaleout-evidence-20260527.json",
            "contracts/production_acceptance/mas-production-acceptance.json",
            "tests/test_mas_production_acceptance.py",
            "tests/test_opl_standard_pack_cases/test_generated_interface_cases.py",
            "tests/test_opl_standard_pack_cases/test_stage_contract_cases.py",
        ]
    )

    assert result.matched_categories == ("production_acceptance_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "make test-paths -- tests/test_mas_production_acceptance.py -q",
        "make test-paths -- tests/test_opl_standard_pack_cases -q",
    ]


def test_classify_changed_files_matches_codex_plugin_skill_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            ".agents/plugins/marketplace.json",
            "plugins/med-autoscience/.codex-plugin/plugin.json",
            "plugins/med-autoscience/skills/med-autoscience/SKILL.md",
            "tests/test_codex_plugin_scaffold.py",
        ]
    )

    assert result.matched_categories == ("codex_plugin_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_native_python_entrypoints_as_family_shared_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "scripts/run-build-clean.sh",
            "Makefile",
            "scripts/verify.sh",
            "scripts/opl-module-bootstrap.sh",
            "scripts/opl-module-healthcheck.sh",
            "src/med_autoscience/opl_module_carrier.py",
            "tests/test_opl_module_runtime_carrier.py",
        ]
    )

    assert result.matched_categories == ("family_shared_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_sentrux_baseline_as_structure_quality_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            ".sentrux/baseline.json",
        ]
    )

    assert result.matched_categories == ("structure_quality_surface",)
    assert result.unclassified_changes == ()
