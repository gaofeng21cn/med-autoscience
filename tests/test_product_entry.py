from __future__ import annotations

from tests.product_entry_cases.attention_queue_and_cockpit_base import (
    test_workspace_cockpit_marks_domain_diagnostic_commands_as_diagnostic_only,
    test_attention_queue_prefers_route_repair_focus_for_quality_blockers,
    test_attention_queue_uses_quality_execution_lane_for_generic_study_blocked,
    test_attention_queue_projects_manual_finishing_as_package_handoff_without_generic_blocker_wording,
    test_attention_queue_prefers_autonomy_contract_summary_for_runtime_recovery,
    test_attention_queue_prefers_gate_clearing_followthrough_for_quality_blockers,
    test_study_item_normalizes_gate_clearing_batch_followthrough_from_progress_payload,
    test_workspace_cockpit_summarizes_alerts_and_user_commands,
    test_workspace_cockpit_reads_study_progress_in_parallel_and_preserves_order,
    test_workspace_cockpit_markdown_prefers_shared_human_status_narration,
)
from tests.product_entry_cases.cockpit_status_and_entry_status_focus import *
from tests.product_entry_cases.authority_operation_manifest import (
    test_product_entry_manifest_domain_commands_include_authority_operations,
    test_product_entry_manifest_schema_enum_matches_authority_command_catalog,
    test_domain_entry_command_contracts_match_authority_command_catalog,
)
from tests.product_entry_cases.manifest_launch_and_task_intake import (
    test_build_product_entry_manifest_projects_contract_bundle_with_product_entry_fields,
    test_build_product_entry_manifest_exposes_source_provenance_refs_for_opl_projection,
    test_build_product_entry_status_projects_contract_bundle_from_manifest,
    test_render_product_entry_status_markdown_prefers_human_facing_labels,
    test_submit_study_task_writes_durable_intake_and_updates_startup_brief_block,
    test_submit_study_task_projects_reviewer_revision_intake,
    test_submit_study_task_honors_explicit_reviewer_revision_kind_without_text_marker,
    test_submit_study_task_writes_structured_manual_hold_intake,
    test_build_product_entry_reuses_latest_task_intake_and_shared_handoff_envelope,
)
from tests.product_entry_cases.repo_shell_and_handoff_templates import (
    test_build_product_entry_manifest_projects_repo_shell_and_shared_handoff_templates,
    test_product_entry_progress_projection_defaults_to_next_action_envelope,
)
from tests.product_entry_cases.product_entry_preflight_and_task_submission import *
from tests.product_entry_cases.product_entry_markdown_and_skill_catalog import (
    test_build_skill_catalog_projects_recommended_shell_and_direct_activation_hints,
)
from tests.product_entry_cases.paper_orchestra_operator_projection import (
    test_product_entry_surfaces_paper_orchestra_operator_projection_without_runtime_authority,
)
from tests.product_entry_cases.open_auto_research_projection import (
    test_product_entry_surfaces_workspace_open_auto_research_projection,
)
from tests.product_entry_cases.opl_current_control_state_handoff_projection import (
    test_workspace_cockpit_and_product_entry_surface_opl_current_control_state_handoff_dashboard,
)
from tests.product_entry_cases.delivery_inspection_visibility import (
    test_product_entry_surfaces_delivery_inspection_in_cockpit_and_entry_status,
    test_product_entry_labels_visible_delivery_projection_as_observability_only,
    test_product_entry_exposes_publication_inspection_package_operator_surface,
    test_product_entry_counts_layout_migration_even_when_stale_status_is_primary,
    test_product_entry_does_not_normalize_retired_delivery_projection_input,
)
from tests.product_entry_cases.action_catalog_parity import *
from tests.product_entry_cases.functional_consumer_boundary import (
    test_product_entry_manifest_exposes_functional_consumer_boundary,
)
from tests.product_entry_cases.transition_spec_descriptor import (
    test_product_entry_manifest_exposes_domain_transition_spec_descriptor,
)
from tests.product_entry_cases.functional_closure_projection import (
    test_product_entry_manifest_projects_current_development_lines_closure,
)


def test_product_entry_manifest_exposes_paper_mission_default_entry(tmp_path):
    from med_autoscience.controllers.product_entry.manifest_surfaces import build_product_entry_manifest
    from med_autoscience.profiles import load_profile
    from tests.test_cli_cases.shared import write_profile

    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    profile = load_profile(profile_path)

    manifest = build_product_entry_manifest(profile=profile, profile_ref=profile_path)

    paper_mission = manifest["medical_paper_product_entry"]
    assert paper_mission["default_action_intent"] == "paper_mission/start_or_resume"
    assert paper_mission["authority_boundary"]["writes_authority"] is False
    assert "paper-mission drive" in paper_mission["default_command"]
    assert paper_mission["drive_command"] == paper_mission["default_command"]
    assert "paper-mission inspect" in paper_mission["inspect_command"]
    assert "paper_mission" not in manifest["product_entry_shell"]
