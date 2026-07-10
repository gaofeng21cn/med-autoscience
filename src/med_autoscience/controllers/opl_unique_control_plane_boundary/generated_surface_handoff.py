from __future__ import annotations

from typing import Any


def build_generated_surface_handoff(
    *,
    schema_version: int,
    replacement_owner: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_generated_surface_handoff",
        "schema_version": schema_version,
        "generated_surface_owner": replacement_owner,
        "current_mas_role": "domain_handler_and_refs_projection_source",
        "status": "handoff_declared_opl_default_surfaces_mas_domain_refs_only_standard_agent_purity_guarded",
        "long_term_mas_owner": False,
        "mas_handwritten_shell_expansion_allowed": False,
        "handoff_surfaces": [
            {
                "surface_id": "cli",
                "current_paths": ["src/med_autoscience/cli/__init__.py", "src/med_autoscience/cli/"],
                "current_role": "domain_handler_command_target_refs_only",
                "target_role": "opl_generated_command_surface",
            },
            {
                "surface_id": "mcp",
                "current_paths": ["src/med_autoscience/domain_entry.py"],
                "current_role": "domain_handler_tool_target_refs_only",
                "target_role": "opl_generated_mcp_descriptor_surface",
            },
            {
                "surface_id": "skill",
                "current_paths": [
                    "plugins/med-autoscience/skills/med-autoscience/SKILL.md",
                ],
                "current_role": "domain_skill_handler_target_and_pack_refs_only",
                "target_role": "opl_generated_skill_descriptor_surface",
            },
            {
                "surface_id": "product_entry",
                "current_paths": [
                    "contracts/domain_projection_profile.json",
                    "src/med_autoscience/controllers/current_work_unit/workspace_projection.py",
                ],
                "current_role": "domain_projection_profile_and_refs_source",
                "target_role": "opl_generated_product_entry_surface",
            },
            {
                "surface_id": "domain_handler",
                "current_paths": [
                    (
                        "src/med_autoscience/controllers/owner_route_handoff/"
                        "domain_handler_export.py"
                    ),
                    (
                        "src/med_autoscience/controllers/owner_route_handoff/"
                        "domain_handler_functional_closure.py"
                    ),
                    (
                        "src/med_autoscience/controllers/owner_route_handoff/"
                        "dispatch_orchestration.py"
                    ),
                ],
                "current_role": "domain_owner_route_refs_export_dispatch_source",
                "target_role": "opl_generated_domain_handler_handoff_surface",
            },
            {
                "surface_id": "status",
                "current_paths": [
                    "src/med_autoscience/controllers/study_progress/",
                    "src/med_autoscience/controllers/current_work_unit/workspace_projection.py",
                ],
                "current_role": "domain_truth_refs_status_projection_source",
                "target_role": "opl_generated_status_wrapper_over_mas_truth_refs",
            },
            {
                "surface_id": "workbench",
                "current_paths": [
                    "src/med_autoscience/controllers/current_work_unit/workspace_projection.py",
                ],
                "current_role": "domain_refs_workbench_projection_source",
                "target_role": "opl_hosted_workbench_shell_consuming_mas_refs",
            },
            {
                "surface_id": "projection_shell",
                "current_paths": [
                    "src/med_autoscience/controllers/current_work_unit/workspace_projection.py",
                    "src/med_autoscience/controllers/study_launch_projection.py",
                    "src/med_autoscience/controllers/study_task_submission.py",
                ],
                "current_role": "domain_refs_projection_builder_source",
                "target_role": "opl_generated_projection_shell",
            },
            {
                "surface_id": "test_lane_harness",
                "current_paths": ["contracts/test-lane-manifest.json", "tests/"],
                "current_role": "focused_contract_guard_for_standard_agent_purity",
                "target_role": "opl_generated_harness_consumer_over_mas_pack",
            },
        ],
        "domain_refs_projection_exit_criteria": [
            "opl_pack_compiler_generated_surface_available",
            "opl_generated_default_owner_consumes_domain_refs",
            "focused_lane_green",
            "no_forbidden_write",
            "history_tombstone_or_delete_unowned_shell",
        ],
    }


__all__ = ["build_generated_surface_handoff"]
