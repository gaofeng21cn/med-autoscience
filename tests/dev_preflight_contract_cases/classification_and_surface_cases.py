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
            "src/med_autoscience/controllers/study_outer_loop.py",
            "src/med_autoscience/controllers/study_runtime_decision.py",
            "src/med_autoscience/controllers/study_runtime_resolution.py",
            "src/med_autoscience/controllers/domain_status_projection.py",
            "src/med_autoscience/controllers/domain_health_diagnostic.py",
            "tests/test_profiles.py",
            "tests/test_opl_runtime_contract.py",
            "tests/test_runtime_root_cause_depth_gate.py",
            "tests/test_runtime_protocol_layout.py",
            "tests/test_runtime_protocol_study_runtime.py",
            "tests/test_domain_health_diagnostic.py",
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


def test_classify_changed_files_routes_branding_assets_to_review_only() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "assets/branding/medautoscience-overview.png",
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
            "src/med_autoscience/controllers/stage_knowledge_plane_parts/publication_route_memory_cards.py",
            "tests/test_stage_knowledge_plane.py",
        ]
    )

    assert result.matched_categories == (
        "documentation_review_only",
        "publication_route_memory_surface",
    )
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "scripts/run-pytest-clean.sh tests/test_stage_knowledge_plane.py -q",
        "scripts/run-pytest-clean.sh tests/test_opl_family_contract_adoption.py -q",
    ]


def test_classify_changed_files_routes_mcp_plugin_config_to_codex_plugin_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "plugins/mas/skills/mas/SKILL.md",
            "scripts/install-codex-plugin.sh",
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
            "contracts/stage_control_plane.json",
            "scripts/real-paper-autonomy-soak-inventory.py",
            "src/med_autoscience/controllers/domain_authority_snapshot.py",
            "src/med_autoscience/controllers/artifact_lifecycle_inventory.py",
            "src/med_autoscience/controllers/artifact_lifecycle_operations_report.py",
            "src/med_autoscience/controllers/opl_provider_ready_adapter.py",
            "src/med_autoscience/controllers/owner_route_handoff_parts/domain_handler_export.py",
            "src/med_autoscience/controllers/owner_route_handoff_parts/dispatch_orchestration.py",
            "src/med_autoscience/controllers/control_intent.py",
            "src/med_autoscience/controllers/control_identity.py",
            "src/med_autoscience/mcp_server.py",
            "src/med_autoscience/controllers/runtime_storage_maintenance_parts/dataset_retention.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/authority_dispatch_gate.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/managed_wakeup.py",
            "src/med_autoscience/controllers/study_progress_parts/projection.py",
            "src/med_autoscience/controllers/study_progress_parts/projection_quality_surfaces.py",
            "src/med_autoscience/controllers/study_progress_parts/projection_runtime_surfaces.py",
            "src/med_autoscience/controllers/study_delivery_sync_parts/sync_orchestration.py",
            "src/med_autoscience/controllers/study_delivery_sync_parts/sync_cli.py",
            "tests/test_autonomy_state_surface.py",
            "tests/test_artifact_lifecycle_inventory.py",
            "tests/test_artifact_lifecycle_operations_report.py",
            "tests/test_workspace_authority_migration_audit.py",
            "tests/test_cli_cases/owner_route_handoff_command/test_export.py",
            "tests/test_cli_cases/owner_route_handoff_command/test_dispatch.py",
            "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_managed_recovery_redrive.py",
        ]
    )

    assert result.matched_categories == (
        "control_plane_surface",
    )
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_cli_parser_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(["src/med_autoscience/cli_parts/parser.py"])

    assert result.matched_categories == ("cli_parser_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "scripts/run-pytest-clean.sh tests/test_runtime_lifecycle_payload_retention.py -q",
    ]


def test_classify_changed_files_matches_owner_answer_candidate_intake_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/owner_answer_candidate_intake.py",
            "src/med_autoscience/cli_parts/current_owner_delta_owner_answer_commands.py",
            "tests/test_owner_answer_candidate_intake.py",
        ]
    )

    assert result.matched_categories == ("owner_answer_candidate_intake_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "scripts/run-pytest-clean.sh tests/test_owner_answer_candidate_intake.py -q",
    ]


def test_classify_changed_files_matches_study_owner_gate_decision_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/study_interventions.py",
            "src/med_autoscience/cli_parts/study_owner_gate_commands.py",
            "tests/test_study_interventions.py",
            "tests/test_cli_cases/domain_action_request_materializer_command.py",
        ]
    )

    assert result.matched_categories == ("study_owner_gate_decision_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "scripts/run-pytest-clean.sh tests/test_study_interventions.py "
        "tests/test_cli_cases/domain_action_request_materializer_command.py -q",
    ]


def test_classify_changed_files_matches_runtime_lifecycle_payload_retention_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "src/med_autoscience/cli_parts/retention_commands.py",
            "src/med_autoscience/controllers/runtime_lifecycle_payload_retention.py",
            "tests/test_runtime_lifecycle_payload_retention.py",
        ]
    )

    assert result.matched_categories == (
        "runtime_lifecycle_payload_retention_surface",
    )
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "scripts/run-pytest-clean.sh tests/test_runtime_lifecycle_payload_retention.py -q",
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
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/obligation_actuator.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_current_control.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_current_control_actions.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_current_control_arbiter.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_current_control_identity.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/runtime_scan.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/runtime_scan_support.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_transition_request.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_report.py",
            "src/med_autoscience/controllers/paper_recovery_state_parts/provider_admission_state.py",
            "src/med_autoscience/controllers/paper_progress_policy_adapter.py",
            "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/provider_admission_current_control_cases.py",
            (
                "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/"
                "provider_admission_current_control_same_tick_cases.py"
            ),
            (
                "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/"
                "test_obligation_actuator_outcomes.py"
            ),
            "tests/test_opl_domain_progress_transition_runtime_contract.py",
            "tests/test_paper_progress_policy_adapter.py",
            "tests/test_paper_recovery_provider_admission_state.py",
            "tests/test_provider_admission_current_control_arbiter.py",
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
        "scripts/run-pytest-clean.sh "
        "tests/test_paper_progress_policy_adapter.py "
        "tests/test_provider_admission_current_control_arbiter.py "
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/"
        "provider_admission_current_control_cases.py "
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/"
        "provider_admission_current_control_same_tick_cases.py "
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/"
        "test_obligation_actuator_outcomes.py -q"
    ) in planned_commands
    assert (
        "scripts/run-pytest-clean.sh "
        "tests/test_opl_domain_progress_transition_runtime_contract.py "
        "tests/test_paper_recovery_provider_admission_state.py -q"
    ) in planned_commands


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
            "scripts/run-parallel-test-lanes.sh",
            "src/med_autoscience/controllers/workspace_init.py",
            "tests/test_workspace_init.py",
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
            "src/med_autoscience/editable_shared_bootstrap.py",
            "src/med_autoscience/dev_preflight.py",
            "src/med_autoscience/dev_preflight_contract.py",
            "src/med_autoscience/family_shared_release.py",
            "tests/test_editable_shared_bootstrap.py",
            "tests/test_dev_preflight.py",
            "tests/test_dev_preflight_contract.py",
            "tests/fixtures/opl_agent_lab_longline.json",
            "tests/test_family_shared_release.py",
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
            "tests/test_test_command_surfaces.py",
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
            "contracts/agent_tool_arsenal.json",
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
            "src/med_autoscience/overlay/templates/medical-research-baseline.SKILL.md",
            "src/med_autoscience/overlay/templates/medical-research-experiment.SKILL.md",
            "templates/codex/medautoscience-entry.SKILL.md",
            "templates/openclaw/medautoscience-entry.prompt.md",
            "templates/stage_route_contract.yaml",
        ]
    )

    assert result.matched_categories == ("standard_agent_pack_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        (
            "scripts/run-pytest-clean.sh "
            "tests/test_opl_family_contract_adoption.py "
            "tests/test_progress_first_safety_envelope_contract.py "
            "tests/test_standard_agent_completion_acceptance_contract.py "
            "tests/test_test_lane_governance.py "
            "tests/test_stage_quality_contract.py "
            "tests/test_stage_route_contract.py "
            "tests/test_stage_route_reconcile_contract.py "
            "tests/test_overlay_installer.py -q"
        ),
        "scripts/run-pytest-clean.sh tests/test_product_entry.py -q",
    ]


def test_classify_changed_files_matches_external_learning_sidecar_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "contracts/opl-framework/family-contract-adoption.json",
            "contracts/progress_first_safety_envelope.json",
            "src/med_autoscience/external_learning_adoption_closure.py",
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
            "scripts/run-pytest-clean.sh "
            "tests/controller_charter/test_controller_charter_module_contract.py "
            "tests/runtime/test_runtime_module_contract.py "
            "tests/eval_hygiene/test_eval_hygiene_module_contract.py "
            "tests/integration/test_monorepo_scaffold_boundaries.py -q"
        ),
        "scripts/run-pytest-clean.sh tests/test_opl_family_contract_adoption.py -q",
        "scripts/run-pytest-clean.sh tests/test_opl_family_persistence_adapter.py -q",
        "scripts/run-pytest-clean.sh tests/test_test_command_surfaces.py -q",
        (
            "scripts/run-pytest-clean.sh "
            "tests/test_opl_family_contract_adoption.py "
            "tests/test_progress_first_safety_envelope_contract.py "
            "tests/test_standard_agent_completion_acceptance_contract.py "
            "tests/test_test_lane_governance.py "
            "tests/test_stage_quality_contract.py "
            "tests/test_stage_route_contract.py "
            "tests/test_stage_route_reconcile_contract.py "
            "tests/test_overlay_installer.py -q"
        ),
        "scripts/run-pytest-clean.sh tests/test_product_entry.py -q",
        (
            "scripts/run-pytest-clean.sh "
            "tests/test_external_learning_adoption_closure.py "
            "tests/test_opl_family_contract_adoption.py "
            "tests/test_progress_first_safety_envelope_contract.py -q"
        ),
        "make test-meta",
    ]


def test_classify_changed_files_matches_evo_scientist_progress_accelerator_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "contracts/evo_scientist_progress_accelerator.json",
            "src/med_autoscience/evo_scientist_learning_projection.py",
            "tests/test_evo_scientist_learning_projection.py",
        ]
    )

    assert result.matched_categories == ("evo_scientist_progress_accelerator_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "scripts/run-pytest-clean.sh tests/test_evo_scientist_learning_projection.py -q",
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
            "src/med_autoscience/overlay/templates/medical-research-citation-locator-audit.template.md",
            "src/med_autoscience/overlay/templates/medical-research-figure-integrity.template.md",
            "src/med_autoscience/overlay/templates/medical-research-prisma-flow.template.md",
            "src/med_autoscience/overlay/templates/medical-research-skill-content-patterns.block.md",
            "src/med_autoscience/resources/stage_route_contract.yaml",
        ]
    )

    assert result.matched_categories == (
        "data_asset_operating_surface",
        "display_pack_v2_contract_surface",
        "standard_agent_pack_surface",
    )
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_stage_kernel_pack_contract_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "contracts/README.md",
            "contracts/mas-paper-study-stage-pack.json",
            "contracts/stage_artifact_kernel_adoption.json",
            "docs/active/stage_surface_standardization_program.md",
            "src/med_autoscience/controllers/stage_artifact_index.py",
            "tests/test_stage_artifact_index.py",
            "tests/test_stage_artifact_kernel_adoption_contract.py",
        ]
    )

    assert result.matched_categories == (
        "root_governance_contract_surface",
        "standard_agent_pack_surface",
        "documentation_review_only",
        "generic_python_smoke_surface",
    )
    assert result.unclassified_changes == ()


def test_classify_changed_files_matches_domain_action_materializer_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/domain_action_request_materializer.py",
            "src/med_autoscience/controllers/domain_action_request_materializer_parts/publication_owner_materialization.py",
            "tests/domain_action_request_materializer_cases/test_dm002_effective_eval_gate_sprint.py",
            (
                "tests/fixtures/dm002_20260529T095414Z_effective_eval_sprint_canary/"
                "artifacts/controller/gate_replay_requests/latest.json"
            ),
            (
                "tests/fixtures/dm002_20260529T095414Z_effective_eval_sprint_canary/"
                "artifacts/controller/repair_execution_evidence/latest.json"
            ),
            (
                "tests/fixtures/dm002_20260529T095414Z_effective_eval_sprint_canary/"
                "artifacts/controller/repair_execution_receipts/latest.json"
            ),
            (
                "tests/fixtures/dm002_20260529T095414Z_effective_eval_sprint_canary/"
                "artifacts/controller_decisions/latest.json"
            ),
            (
                "tests/fixtures/dm002_20260529T095414Z_effective_eval_sprint_canary/"
                "artifacts/runtime/runtime_status_summary.json"
            ),
            "tests/fixtures/dm002_20260529T095414Z_effective_eval_sprint_canary/study.yaml",
        ]
    )

    assert result.matched_categories == ("domain_action_materializer_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        (
            "scripts/run-pytest-clean.sh "
            "tests/domain_action_request_materializer_cases/test_dm002_effective_eval_gate_sprint.py -q"
        ),
        "scripts/run-pytest-clean.sh tests/test_domain_action_request_materializer.py -q",
    ]


def test_classify_changed_files_matches_paper_autonomy_supervisor_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "contracts/paper_autonomy_supervisor_contract.json",
            "src/med_autoscience/controllers/paper_autonomy_supervisor.py",
            "tests/test_paper_autonomy_supervisor.py",
            "tests/test_paper_autonomy_supervisor_contract.py",
        ]
    )

    assert result.matched_categories == ("paper_autonomy_supervisor_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        (
            "scripts/run-pytest-clean.sh "
            "tests/test_paper_autonomy_supervisor.py "
            "tests/test_paper_autonomy_supervisor_contract.py -q"
        ),
    ]


def test_classify_changed_files_matches_production_acceptance_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "contracts/agent_lab_handoff.json",
            "contracts/production_acceptance/mas-multiprofile-guarded-apply-receipt-scaleout-evidence-20260527.json",
            "contracts/production_acceptance/mas-production-acceptance.json",
            "tests/test_mas_production_acceptance.py",
            "tests/test_opl_standard_pack.py",
        ]
    )

    assert result.matched_categories == ("production_acceptance_surface",)
    assert result.unclassified_changes == ()
    assert module.plan_commands_for_categories(result.matched_categories) == [
        "scripts/run-pytest-clean.sh tests/test_mas_production_acceptance.py -q",
        "scripts/run-pytest-clean.sh tests/test_opl_standard_pack.py -q",
    ]


def test_classify_changed_files_matches_codex_plugin_skill_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            ".agents/plugins/marketplace.json",
            "plugins/mas/.codex-plugin/plugin.json",
            "plugins/mas/skills/mas/SKILL.md",
            "tests/test_codex_plugin_scaffold.py",
        ]
    )

    assert result.matched_categories == ("codex_plugin_surface",)
    assert result.unclassified_changes == ()


def test_classify_changed_clean_runner_scripts_as_family_shared_surface() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    result = module.classify_changed_files(
        [
            "scripts/run-build-clean.sh",
            "scripts/run-python-clean.sh",
            "scripts/run-pytest-clean.sh",
            "scripts/verify.sh",
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
