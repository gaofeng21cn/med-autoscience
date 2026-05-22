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
        "current_mas_role": "handwritten_migration_bridge",
        "status": "handoff_declared_mas_shells_are_migration_bridges",
        "long_term_mas_owner": False,
        "mas_handwritten_shell_expansion_allowed": False,
        "handoff_surfaces": [
            {
                "surface_id": "cli",
                "current_paths": ["src/med_autoscience/cli.py", "src/med_autoscience/cli_parts/"],
                "current_role": "migration_bridge_thin_wrapper",
                "target_role": "opl_generated_command_surface",
            },
            {
                "surface_id": "mcp",
                "current_paths": ["src/med_autoscience/mcp_server.py"],
                "current_role": "migration_bridge_tool_handler_target",
                "target_role": "opl_generated_mcp_descriptor_surface",
            },
            {
                "surface_id": "skill",
                "current_paths": [
                    "plugins/mas/skills/mas/SKILL.md",
                    "src/med_autoscience/controllers/product_entry_parts/program_surfaces.py",
                ],
                "current_role": "migration_bridge_domain_skill_target_and_pack_guidance",
                "target_role": "opl_generated_skill_descriptor_surface",
            },
            {
                "surface_id": "product_entry",
                "current_paths": ["src/med_autoscience/controllers/product_entry.py"],
                "current_role": "migration_bridge_manifest_builder",
                "target_role": "opl_generated_product_entry_surface",
            },
            {
                "surface_id": "sidecar",
                "current_paths": [
                    "src/med_autoscience/controllers/owner_route_handoff.py",
                    (
                        "src/med_autoscience/controllers/owner_route_handoff_parts/"
                        "export_projection.py"
                    ),
                    (
                        "src/med_autoscience/controllers/owner_route_handoff_parts/"
                        "export_study_projection.py"
                    ),
                    (
                        "src/med_autoscience/controllers/owner_route_handoff_parts/"
                        "dispatch_orchestration.py"
                    ),
                ],
                "current_role": "migration_bridge_export_dispatch_adapter",
                "target_role": "opl_generated_sidecar_handoff_surface",
            },
            {
                "surface_id": "status",
                "current_paths": [
                    "src/med_autoscience/controllers/product_entry_parts/",
                    "src/med_autoscience/controllers/progress_projection.py",
                ],
                "current_role": "domain_truth_plus_migration_bridge_status_wrapper",
                "target_role": "opl_generated_status_wrapper_over_mas_truth_refs",
            },
            {
                "surface_id": "workbench",
                "current_paths": [
                    "src/med_autoscience/controllers/progress_portal.py",
                    "src/med_autoscience/controllers/product_entry_parts/workspace_cockpit/",
                ],
                "current_role": "migration_bridge_workbench_projection_shell",
                "target_role": "opl_hosted_workbench_shell_consuming_mas_refs",
            },
            {
                "surface_id": "projection_shell",
                "current_paths": [
                    "src/med_autoscience/controllers/product_entry_parts/",
                    "src/med_autoscience/controllers/progress_portal_parts/",
                ],
                "current_role": "migration_bridge_projection_builder",
                "target_role": "opl_generated_projection_shell",
            },
            {
                "surface_id": "test_lane_harness",
                "current_paths": ["contracts/test-lane-manifest.json", "tests/"],
                "current_role": "migration_bridge_repo_guard",
                "target_role": "opl_generated_harness_consumer_over_mas_pack",
            },
        ],
        "migration_bridge_exit_criteria": [
            "opl_pack_compiler_generated_surface_available",
            "active_callers_migrated",
            "focused_lane_green",
            "no_forbidden_write",
            "history_tombstone_or_delete_unowned_shell",
        ],
    }


__all__ = ["build_generated_surface_handoff"]
