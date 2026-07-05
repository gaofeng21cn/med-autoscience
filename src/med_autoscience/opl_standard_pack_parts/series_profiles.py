from __future__ import annotations

SHARED_POLICY_RELEASE = {
    "policy_release_contract_ref": (
        "contracts/opl-framework/foundry-agent-series-policy-release.json"
    ),
    "policy_bundle_fingerprint": (
        "sha256:503f515e8fa08b3f81ce28cac461368c609d4565de239c9f95c3f910cb758ed5"
    ),
    "fingerprint_algorithm": "sha256:stable-json",
    "domain_contract_policy_release_pin_required": True,
    "domain_adapter_must_not_copy_policy_body_as_authority": True,
    "consumer_alignment_check": "foundry:policy-release",
}

AGENT_MEMBERSHIP_PROJECTION_POLICY = {
    "surface_kind": "opl_foundry_agent_membership_projection_policy",
    "version": "foundry-agent-membership-projection.v1",
    "policy_id": "standard_agent_membership_not_surface_origin",
    "default_membership": "standard_domain_agent",
    "public_agent_list_must_not_split_by_generated_surface": True,
    "public_agent_list_must_not_split_by_plugin_transport": True,
    "generated_surface_is_membership_axis": False,
    "generated_surface_is_status_axis": False,
    "plugin_transport_is_membership_axis": False,
    "plugin_transport_is_status_axis": False,
    "generated_surface_only_field_public_default": False,
}

STANDARD_PUBLIC_PROJECTION_POLICY = {
    "surface_kind": "opl_foundry_agent_standard_public_projection_policy",
    "version": "foundry-agent-standard-public-projection.v1",
    "policy_id": "standard_agent_public_foundry_surface_is_opl_generated_hosted_series",
    "standard_public_foundry_surface": "opl_generated_hosted_series",
    "canonical_inspect_command_pattern": "opl foundry agents inspect <agent_id>",
    "allowed_active_public_foundry_surfaces": [
        "opl_foundry_agent_series_spine",
        "opl_family_hosted_surfaces",
    ],
    "active_public_projection_allows_non_opl_foundry_cli": False,
    "active_public_projection_allows_domain_owned_cli_as_standard_surface": False,
    "active_public_projection_allows_forbidden_surface_roles": False,
    "active_public_projection_allows_retired_surface_aliases": False,
    "active_public_projection_allows_compatibility_aliases": False,
    "active_public_projection_allows_legacy_json_aliases": False,
    "minimal_authority_functions_are_membership_axis": False,
    "domain_owned_helpers_are_membership_axis": False,
    "allowed_domain_owned_helper_context": "minimal_authority_functions_only",
    "non_standard_surface_retention_contexts": [
        "history",
        "tombstone",
    ],
}

STANDARD_FEEDBACK_SELF_EVOLUTION_TRIGGER_POLICY = {
    "surface_kind": "opl_foundry_agent_standard_feedback_self_evolution_trigger_policy",
    "version": "foundry-agent-feedback-self-evolution-trigger.v1",
    "policy_id": "standard_agent_feedback_self_evolution_trigger.v1",
    "applies_to_series_memberships": [
        "standard_domain_agent",
        "framework_capability_package",
    ],
    "feedbackops_event_kind": "target_agent_feedback_external_suite",
    "accepted_feedback_profile": "target_agent_feedback_external_suite",
    "must_follow_target_domain_mainline": True,
    "must_not_compete_with_target_domain_mainline": True,
    "target_domain_terminal_route": "owner_gate_or_typed_blocker",
    "trigger_chain": [
        "domain_or_package_thin_feedback_adapter",
        "opl_feedbackops_agent_lab_status_projection",
        "opl_meta_agent_oma_agent_evolution_work_order",
        "developer_mode_direct_fix_or_fork_pr_route",
        "target_owner_closeout_readback",
    ],
    "required_trigger_fields": [
        "feedbackops_event_kind",
        "accepted_feedback_profile",
        "target_agent_id",
        "idempotency_key",
        "external_suite_ref",
        "developer_mode_execution_gate_refs",
        "oma_evolution_skill_ref",
        "owner_closeout_readback_refs",
    ],
    "standard_status_projection_ref": (
        "contracts/opl-framework/agent-lab-contract.json#/"
        "domain_feedback_self_evolution_surface"
    ),
    "feedback_capture_requires_developer_mode": False,
    "repo_fix_execution_requires_opl_developer_mode": True,
    "contract_can_trigger_execution": False,
    "developer_mode_execution_gate_refs": [
        "opl-developer-mode:repo-fix-execution",
        "opl-developer-mode:direct-fix-or-fork-pr-route",
    ],
    "developer_route_policy": {
        "feedback_capture_route": "allowed_for_all_users_refs_only",
        "direct_fix_route": (
            "requires_target_repo_direct_write_authority_or_"
            "agent_owner_developer_authority"
        ),
        "manual_enable_without_direct_write_route": "fork_pull_request",
        "official_or_third_party_agent_without_authority_route": (
            "fork_pull_request_or_owner_handoff"
        ),
        "manual_developer_mode_cannot_grant_direct_repo_write": True,
        "auto_developer_mode_can_select_local_checkout_source_when_identity_matches": True,
    },
    "authority_boundary": {
        "refs_only": True,
        "can_write_domain_truth": False,
        "can_mutate_artifact_body": False,
        "can_authorize_quality_or_export": False,
        "can_create_owner_receipt": False,
        "can_create_typed_blocker": False,
        "can_execute_repo_patch_without_developer_mode": False,
    },
}

SERIES_DESIGN_PROFILE = {
    "surface_kind": "opl_foundry_agent_series_design_profile",
    "version": "foundry-agent-series-design-profile.v1",
    "profile_id": "opl_foundry_agent_series_design_profile.v1",
    "profile_summary": (
        "All Foundry Agents share the same OPL domain-pack to stage-led execution "
        "to gate/receipt to handoff lifecycle; domain inputs, outputs, aliases, "
        "and authority functions vary by agent."
    ),
    "shared_lifecycle_pipeline": [
        "domain_material_intake",
        "domain_pack_interpretation",
        "stage_led_agent_execution",
        "independent_quality_gate_or_owner_review",
        "owner_receipt_or_typed_blocker_closeout",
        "artifact_or_deliverable_handoff",
        "opl_refs_only_projection_and_recovery",
    ],
    "domain_io_profile": {
        "input_slot": "domain_materials_or_task_request",
        "output_slot": "domain_deliverable_or_owner_handoff",
        "input_is_domain_specific": True,
        "output_is_domain_specific": True,
        "shared_runtime_interpretation": (
            "OPL treats input/output as opaque domain refs and projects identity, "
            "stage, progress, closeout, evidence, and recovery metadata only."
        ),
    },
    "stage_pack_sections": [
        "prompts",
        "stages",
        "stage_completion_policy",
        "skills",
        "tools",
        "knowledge",
        "quality_gates",
    ],
    "shared_closeout_contract": {
        "success_shape": "domain_owner_receipt_ref",
        "blocked_shape": "domain_owned_typed_blocker_ref",
        "route_back_shape": "route_back_or_human_gate_ref",
        "provider_completion_is_closeout": False,
    },
    "authority_invariants": {
        "opl_can_infer_domain_output": False,
        "opl_can_read_domain_body": False,
        "opl_can_write_domain_truth": False,
        "opl_can_authorize_quality_or_export": False,
        "domain_owns_input_truth_and_output_authority": True,
    },
}

DOMAIN_SPECIFIC_PROFILE = {
    "profile_id": "mas_domain_specific_series_profile.v1",
    "series_members": ["MAS", "MAG", "RCA", "OMA"],
    "shared_agent_logic": (
        "same_opl_foundry_agent_lifecycle_with_domain_specific_medical_research_inputs_"
        "and_manuscript_outputs"
    ),
    "domain_input_taxonomy": [
        "disease_specific_study_question",
        "workspace_profile_and_study_truth_refs",
        "data_asset_and_source_readiness_refs",
        "evidence_review_and_claim_boundary_refs",
        "publication_route_memory_refs",
        "human_gate_or_PI_decision_refs",
    ],
    "domain_output_taxonomy": [
        "research_evidence_pack_refs",
        "manuscript_or_display_delta_refs",
        "AI_reviewer_or_auditor_record_refs",
        "publication_gate_or_route_back_refs",
        "artifact_lineage_rebuild_or_package_refs",
        "owner_receipt_or_stable_typed_blocker_refs",
    ],
    "shared_lifecycle_pipeline": [
        "intake_or_resume",
        "stage_packet_hydration",
        "executor_attempt",
        "independent_reviewer_or_auditor_gate",
        "progress_currentness_projection",
        "owner_receipt_or_typed_blocker_closeout",
        "handoff_or_next_forced_delta",
    ],
    "authority_invariants": {
        "opl_role": "refs_projection_runtime_lifecycle_and_generated_surface_owner",
        "mas_role": (
            "study_truth_publication_quality_artifact_authority_memory_authority_"
            "and_owner_receipt_owner"
        ),
        "opl_can_write_study_truth": False,
        "opl_can_claim_publication_quality": False,
        "opl_can_authorize_artifact_mutation": False,
        "opl_can_accept_or_reject_memory_body": False,
        "mas_owner_receipt_required_for_domain_closeout": True,
    },
    "stage_pack_sections": [
        "prompts",
        "stage_policies",
        "skills",
        "knowledge",
        "quality_gates",
        "action_catalog",
        "memory_artifact_receipt_contracts",
    ],
    "progress_currentness_closeout_packets": [
        "stage_completion_policy",
        "user_stage_log_contract",
        "progress_delta_policy",
        "typed_blocker_lineage_policy",
        "effective_current_context",
        "owner_receipt_or_typed_blocker_closeout",
    ],
}
WORKSPACE_TOPOLOGY_PROFILE = {
    "surface_kind": "opl_workspace_topology_profile",
    "version": "workspace-topology-profile.v1",
    "profile_id": "opl.workspace_topology_profile.v1",
    "topology_model": [
        "workspace_group",
        "project_unit",
        "stage_artifact_unit",
        "owner_receipt_or_typed_blocker",
    ],
    "workspace_modes": ["one_off", "series", "portfolio"],
    "default_project_stage_outputs_root": "artifacts/stage_outputs",
    "default_profiles": {
        "one_off": {
            "workspace_mode": "one_off",
            "project_collection_path": "projects",
            "series_capable_skeleton": True,
            "shared_resource_roots": [
                "shared/sources",
                "shared/memory",
                "shared/style_system",
            ],
            "project_stage_outputs_root": "artifacts/stage_outputs",
        },
        "rca_series": {
            "workspace_mode": "series",
            "project_collection_path": "projects",
            "shared_resource_roots": [
                "shared/sources",
                "shared/brand",
                "shared/visual_memory",
                "shared/style_system",
                "shared/material_inventory",
            ],
            "project_stage_outputs_root": "artifacts/stage_outputs",
        },
        "mas_portfolio": {
            "workspace_mode": "portfolio",
            "project_collection_path": "projects",
            "shared_resource_roots": [
                "data",
                "literature",
                "memory",
                "shared/sources",
            ],
            "project_stage_outputs_root": "artifacts/stage_outputs",
        },
    },
    "domain_profile_defaults": {
        "mas": "mas_portfolio",
        "mag": "one_off",
        "rca": "rca_series",
        "oma": "one_off",
    },
    "default_user_inspection_surface": {
        "ordinary_user_default_surface": "workspace_local_project_stage_outputs",
        "project_stage_outputs_pattern": "<project-root>/artifacts/stage_outputs/<stage-id>/",
        "runtime_state_is_default_user_surface": False,
        "product_views_are_stage_outputs": False,
    },
    "runtime_state_boundary": {
        "role": "provider_backing_provenance_restore_audit",
        "runtime_state_can_be_canonical_project_root": False,
        "runtime_state_can_close_stage": False,
        "runtime_state_can_replace_owner_receipt_or_typed_blocker": False,
    },
    "authority_boundary": {
        "opl_can_define_topology_contract": True,
        "opl_can_project_workspace_refs": True,
        "opl_can_write_domain_truth": False,
        "opl_can_mutate_artifact_body": False,
        "opl_can_create_owner_receipt": False,
        "opl_can_create_typed_blocker": False,
        "runtime_state_counts_as_user_default_surface": False,
    },
    "workspace_initialization_policy": {
        "default_workspace_mode": "one_off",
        "infer_series_when_user_requests_multiple_related_deliverables": True,
        "infer_portfolio_when_user_requests_shared_research_workspace_with_multiple_studies": True,
        "upgrading_one_off_to_series_must_not_move_existing_project_roots": True,
        "explicit_workspace_mode_declaration_preferred": True,
        "default_project_collection_path": "projects",
        "legacy_project_collection_aliases": [
            "deliverables",
            "studies",
        ],
    },
    "example_project_layouts": {
        "one_off": {
            "project_collection_path": "projects",
            "project_root_pattern": "projects/<project-id>",
            "project_stage_outputs_pattern": (
                "projects/<project-id>/artifacts/stage_outputs/<stage-id>/"
            ),
            "legacy_project_collection_aliases": ["deliverables"],
        },
        "rca_series": {
            "shared_roots": [
                "shared/sources",
                "shared/brand",
                "shared/visual_memory",
                "shared/style_system",
                "shared/material_inventory",
            ],
            "project_collection_path": "projects",
            "project_root_pattern": "projects/<deck-id>",
            "project_stage_outputs_pattern": (
                "projects/<deck-id>/artifacts/stage_outputs/<stage-id>/"
            ),
            "legacy_project_collection_aliases": ["deliverables"],
        },
        "mas_portfolio": {
            "shared_roots": [
                "data",
                "literature",
                "memory",
            ],
            "project_collection_path": "projects",
            "project_root_pattern": "projects/<study-id>",
            "project_stage_outputs_pattern": (
                "projects/<study-id>/artifacts/stage_outputs/<stage-id>/"
            ),
            "legacy_project_collection_aliases": ["studies"],
        },
    },
}
