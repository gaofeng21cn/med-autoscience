from __future__ import annotations


def assert_manifest_runtime_and_continuity(*, module, payload, profile, profile_ref) -> None:
        assert payload["surface_kind"] == "product_entry_manifest"

        assert payload["manifest_version"] == 2

        assert payload["manifest_kind"] == "med_autoscience_product_entry_manifest"

        assert payload["target_domain_id"] == "med-autoscience"

        assert payload["formal_entry"]["default"] == "CLI"

        assert payload["formal_entry"]["supported_protocols"] == ["MCP"]

        assert payload["runtime"]["runtime_owner"] == "upstream_hermes_agent"

        assert payload["runtime"]["domain_owner"] == "med-autoscience"

        assert payload["runtime"]["executor_owner"] == "med_deepscientist"

        assert payload["runtime"]["runtime_substrate"] == "external_hermes_agent_target"

        assert payload["managed_runtime_contract"] == {
            "shared_contract_ref": "contracts/opl-gateway/managed-runtime-three-layer-contract.json",
            "runtime_owner": "upstream_hermes_agent",
            "domain_owner": "med-autoscience",
            "executor_owner": "med_deepscientist",
            "supervision_status_surface": {
                "surface_kind": "study_progress",
                "owner": "med-autoscience",
            },
            "attention_queue_surface": {
                "surface_kind": "workspace_cockpit",
                "owner": "med-autoscience",
            },
            "recovery_contract_surface": {
                "surface_kind": "study_runtime_status",
                "owner": "med-autoscience",
            },
            "fail_closed_rules": [
                "domain_supervision_cannot_bypass_runtime",
                "executor_cannot_declare_global_gate_clear",
                "runtime_cannot_invent_domain_publishability_truth",
            ],
        }

        assert payload["runtime_inventory"]["surface_kind"] == "runtime_inventory"

        assert payload["runtime_inventory"]["runtime_owner"] == "upstream_hermes_agent"

        assert payload["runtime_inventory"]["domain_owner"] == "med-autoscience"

        assert payload["runtime_inventory"]["executor_owner"] == "med_deepscientist"

        assert payload["runtime_inventory"]["substrate"] == "external_hermes_agent_target"

        assert payload["runtime_inventory"]["availability"] == "ready"

        assert payload["runtime_inventory"]["health_status"] == "healthy"

        assert payload["runtime_inventory"]["status_surface"]["ref_kind"] == "workspace_locator"

        assert payload["runtime_inventory"]["status_surface"]["ref"] == "studies/<study_id>/artifacts/runtime_watch/latest.json"

        assert payload["runtime_inventory"]["attention_surface"]["ref_kind"] == "json_pointer"

        assert payload["runtime_inventory"]["attention_surface"]["ref"] == "/operator_loop_surface"

        assert payload["runtime_inventory"]["recovery_surface"]["ref_kind"] == "json_pointer"

        assert payload["runtime_inventory"]["recovery_surface"]["ref"] == "/managed_runtime_contract/recovery_contract_surface"

        assert payload["runtime_inventory"]["workspace_binding"]["workspace_root"] == str(profile.workspace_root)

        assert payload["runtime_inventory"]["workspace_binding"]["profile_name"] == profile.name

        assert payload["runtime_inventory"]["domain_projection"]["managed_runtime_backend_id"] == profile.managed_runtime_backend_id

        assert payload["session_continuity"]["surface_kind"] == "session_continuity"

        assert payload["session_continuity"]["domain_agent_id"] == "mas"

        assert payload["session_continuity"]["restore_surface"]["surface_kind"] == "launch_study"

        assert payload["session_continuity"]["progress_surface"]["surface_kind"] == "study_progress"

        assert payload["session_continuity"]["artifact_surface"]["surface_kind"] == "study_runtime_status"

        assert payload["progress_projection"]["surface_kind"] == "progress_projection"

        assert payload["progress_projection"]["progress_surface"]["surface_kind"] == "workspace_cockpit"

        assert "studies/<study_id>/artifacts" in payload["progress_projection"]["inspect_paths"]

        assert payload["progress_projection"]["domain_projection"]["research_runtime_control_projection"] == {
            "surface_kind": "research_runtime_control_projection",
            "study_session_owner": {
                "runtime_owner": "upstream_hermes_agent",
                "study_owner": "med-autoscience",
                "executor_owner": "med_deepscientist",
            },
            "session_lineage_surface": {
                "surface_kind": "study_progress",
                "field_path": "family_checkpoint_lineage",
                "resume_contract_field": "family_checkpoint_lineage.resume_contract",
                "continuation_state_field": "continuation_state",
                "active_run_id_field": "supervision.active_run_id",
            },
            "restore_point_surface": {
                "surface_kind": "study_progress",
                "field_path": "autonomy_contract.restore_point",
                "lineage_anchor_field": "family_checkpoint_lineage.resume_contract",
                "summary_field": "autonomy_contract.restore_point.summary",
            },
            "progress_cursor_surface": {
                "surface_kind": "study_progress",
                "field_path": "operator_status_card.current_focus",
            },
            "progress_surface": {
                "surface_kind": "study_progress",
                "field_path": "operator_status_card.current_focus",
                "fallback_field_path": "next_system_action",
            },
            "artifact_inventory_surface": {
                "surface_kind": "study_progress",
                "field_path": "refs",
            },
            "artifact_pickup_surface": {
                "surface_kind": "study_progress",
                "field_path": "refs.evaluation_summary_path",
                "fallback_fields": [
                    "refs.publication_eval_path",
                    "refs.controller_decision_path",
                    "refs.runtime_supervision_path",
                    "refs.runtime_watch_report_path",
                ],
                "pickup_refs_field": "research_runtime_control_projection.artifact_pickup_surface.pickup_refs",
            },
            "command_templates": {
                "resume": (
                    "uv run python -m med_autoscience.cli launch-study --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id>"
                ),
                "check_progress": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --format json"
                ),
                "check_runtime_status": (
                    "uv run python -m med_autoscience.cli study-runtime-status --profile "
                    + str(profile_ref.resolve())
                    + " --study-id <study_id> --format json"
                ),
            },
            "research_gate_surface": {
                "surface_kind": "study_progress",
                "approval_gate_field": "needs_user_decision",
                "approval_gate_required_field": "needs_user_decision",
                "legacy_approval_gate_field": "needs_physician_decision",
                "approval_gate_owner": "mas_controller",
                "interrupt_policy_field": "intervention_lane.recommended_action_id",
                "interrupt_policy_value_field": "intervention_lane.recommended_action_id",
                "gate_lane_field": "intervention_lane.lane_id",
                "gate_summary_field": "intervention_lane.summary",
                "human_gate_required_field": "autonomy_contract.restore_point.human_gate_required",
            },
        }

        assert payload["artifact_inventory"]["surface_kind"] == "artifact_inventory"

        assert payload["artifact_inventory"]["summary"]["deliverable_files_count"] == 0
