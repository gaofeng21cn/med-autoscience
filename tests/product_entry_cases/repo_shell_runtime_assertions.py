from __future__ import annotations

def _assert_manifest_runtime_identity(*, module, payload, profile, profile_ref) -> None:
    assert payload["surface_kind"] == "product_entry_manifest"
    assert payload["manifest_version"] == 2
    assert payload["manifest_kind"] == "med_autoscience_product_entry_manifest"
    assert payload["target_domain_id"] == "med-autoscience"
    assert payload["formal_entry"]["default"] == "CLI"
    assert payload["formal_entry"]["supported_protocols"] == ["MCP"]
    assert payload["runtime"]["runtime_owner"] == "one-person-lab"

def _assert_managed_runtime_contract(*, module, payload, profile, profile_ref) -> None:
    assert payload["runtime"]["domain_owner"] == "med-autoscience"
    assert payload["runtime"]["executor_owner"] == "controlled_research_backend"
    assert payload["runtime"]["runtime_substrate"] == "opl_hosted_stage_runtime"
    assert payload["managed_runtime_contract"] == {
        "shared_contract_ref": "contracts/opl-framework/managed-runtime-three-layer-contract.json",
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "executor_owner": "controlled_research_backend",
        "supervision_status_surface": {
            "surface_kind": "study_progress",
            "owner": "med-autoscience",
        },
        "attention_queue_surface": {
            "surface_kind": "workspace_cockpit",
            "owner": "med-autoscience",
        },
        "recovery_contract_surface": {
            "surface_kind": "progress_projection",
            "owner": "med-autoscience",
        },
        "fail_closed_rules": [
            "domain_supervision_cannot_bypass_runtime",
            "executor_cannot_declare_global_gate_clear",
            "runtime_cannot_invent_domain_publishability_truth",
        ],
    }
    assert payload["runtime_inventory"]["surface_kind"] == "runtime_inventory"
    assert payload["runtime_inventory"]["runtime_owner"] == "one-person-lab"
    assert payload["runtime_inventory"]["domain_owner"] == "med-autoscience"

def _assert_runtime_inventory(*, module, payload, profile, profile_ref) -> None:
    assert payload["runtime_inventory"]["executor_owner"] == "controlled_research_backend"
    assert payload["runtime_inventory"]["substrate"] == "opl_hosted_stage_runtime"
    assert payload["runtime_inventory"]["availability"] == "ready"
    assert payload["runtime_inventory"]["health_status"] == "healthy"
    assert payload["runtime_inventory"]["status_surface"]["ref_kind"] == "workspace_locator"
    assert payload["runtime_inventory"]["status_surface"]["ref"] == (
        "studies/<study_id>/artifacts/domain_health_diagnostic/latest.json"
    )
    assert payload["runtime_inventory"]["attention_surface"]["ref_kind"] == "json_pointer"

def _assert_session_and_progress_projection(*, module, payload, profile, profile_ref) -> None:
    assert payload["runtime_inventory"]["attention_surface"]["ref"] == "/operator_loop_surface"
    assert payload["runtime_inventory"]["recovery_surface"]["ref_kind"] == "json_pointer"
    assert payload["runtime_inventory"]["recovery_surface"]["ref"] == "/managed_runtime_contract/recovery_contract_surface"
    assert payload["runtime_inventory"]["workspace_binding"]["workspace_root"] == str(profile.workspace_root)
    assert payload["runtime_inventory"]["workspace_binding"]["profile_name"] == profile.name
    assert payload["runtime_inventory"]["domain_projection"]["opl_runtime_ref"] == profile.opl_runtime_ref
    assert payload["runtime_inventory"]["domain_projection"]["recommended_loop_surface"] == "workspace_cockpit"
    assert payload["session_continuity"]["surface_kind"] == "session_continuity"

def _assert_research_runtime_control_projection(*, module, payload, profile, profile_ref) -> None:
    assert payload["session_continuity"]["domain_agent_id"] == "mas"
    assert payload["session_continuity"]["restore_surface"]["surface_kind"] == "launch_study"
    assert payload["session_continuity"]["progress_surface"]["surface_kind"] == "study_progress"
    assert payload["session_continuity"]["artifact_surface"]["surface_kind"] == "progress_projection"
    assert payload["progress_projection"]["surface_kind"] == "progress_projection"
    assert payload["progress_projection"]["progress_surface"] == {
        "surface_kind": "study_progress",
        "summary": (
            "默认读取 study_progress.current_owner_delta、current_executable_owner_action 和 owner receipt / typed blocker refs。"
        ),
        "command": (
            "uv run python -m med_autoscience.cli study progress --profile "
            + str(profile_ref.resolve())
            + " --study-id <study_id> --format json"
        ),
        "step_id": "inspect_current_owner_delta",
        "locator_fields": ["profile_ref", "study_id"],
    }
    assert payload["progress_projection"]["domain_projection"]["default_read_surface"] == {
        "surface_kind": "study_progress",
        "field_path": "current_owner_delta",
        "fallback_field_path": "current_executable_owner_action",
        "receipt_or_blocker_fields": ["owner_receipt_ref", "typed_blocker_ref"],
        "ordinary_read_priority": 0,
    }
    diagnostic_audit_plane = payload["progress_projection"]["domain_projection"]["diagnostic_audit_plane"]
    assert diagnostic_audit_plane["audit_only_fields"] == [
        "raw_worklist",
        "provider_trace",
        "queue_counts",
        "legacy_dispatch",
    ]
    assert diagnostic_audit_plane["must_not_override_current_owner_delta"] is True
    assert "workbench" in diagnostic_audit_plane["workspace_cockpit_command"]
    assert "study progress" in diagnostic_audit_plane["runtime_status_command"]
    assert "studies/<study_id>/artifacts" in payload["progress_projection"]["inspect_paths"]

def _assert_artifact_inventory_summary(*, module, payload, profile, profile_ref) -> None:
    assert payload["progress_projection"]["domain_projection"]["research_runtime_control_projection"] == {
        "surface_kind": "research_runtime_control_projection",
        "study_session_owner": {
            "runtime_owner": "one-person-lab",
            "study_owner": "med-autoscience",
            "executor_owner": "controlled_research_backend",
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
        "artifact_runtime_proof_surface": {
            "surface_kind": "study_progress",
            "field_path": "artifact_runtime_proof",
            "delivery_manifest_field": "refs.artifact_runtime_proof_delivery_manifest_path",
        },
        "submission_hygiene_truth_surface": {
            "surface_kind": "study_progress",
            "field_path": "submission_hygiene_truth",
            "recommended_flow_field": "product_recommended_flow",
            "blocking_gate_keys_field": "submission_hygiene_truth.blocking_gate_keys",
        },
        "artifact_pickup_surface": {
            "surface_kind": "study_progress",
            "field_path": "refs.evaluation_summary_path",
            "fallback_fields": [
                "refs.publication_eval_path",
                "refs.medical_manuscript_blueprint_path",
                "refs.medical_journal_style_corpus_path",
                "refs.medical_prose_review_request_path",
                "refs.medical_prose_review_path",
                "refs.retrospective_medical_prose_audit_path",
                "refs.controller_decision_path",
                "refs.opl_runtime_owner_handoff_path",
                "refs.domain_health_diagnostic_report_path",
            ],
            "pickup_refs_field": "research_runtime_control_projection.artifact_pickup_surface.pickup_refs",
        },
        "medical_writing_quality_surface": {
            "surface_kind": "study_progress",
            "field_path": "medical_writing_quality_surfaces",
            "blueprint_field": "medical_writing_quality_surfaces.blueprint",
            "style_corpus_field": "medical_writing_quality_surfaces.style_corpus",
            "prose_review_request_field": "medical_writing_quality_surfaces.prose_review_request",
            "prose_review_field": "medical_writing_quality_surfaces.prose_review",
            "retrospective_audit_field": "medical_writing_quality_surfaces.retrospective_audit",
            "subjective_quality_owner": "ai_reviewer",
            "mechanical_flags_role": "evidence_snippets_only",
        },
        "recommended_flow_surface": {
            "surface_kind": "study_progress",
            "field_path": "product_recommended_flow",
            "default_step_field": "product_recommended_flow.recommended_step_id",
        },
        "command_templates": {
            "resume": (
                "uv run python -m med_autoscience.cli study launch --profile "
                + str(profile_ref.resolve())
                + " --study-id <study_id>"
            ),
            "check_progress": (
                "uv run python -m med_autoscience.cli study progress --profile "
                + str(profile_ref.resolve())
                + " --study-id <study_id> --format json"
            ),
            "check_runtime_status": (
                "uv run python -m med_autoscience.cli study progress --profile "
                + str(profile_ref.resolve())
                + " --study-id <study_id> --format json"
            ),
        },
        "research_gate_surface": {
            "surface_kind": "study_progress",
            "approval_gate_field": "needs_user_decision",
            "approval_gate_required_field": "needs_user_decision",
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

def _assert_family_persistence_lifecycle_owner_route(*, module, payload, profile, profile_ref) -> None:
    policy = payload["persistence_policy"]
    assert policy["surface_kind"] == "family_persistence_policy"
    assert policy["target_domain_id"] == "med-autoscience"
    assert {entry["storage_role"] for entry in policy["authority_surfaces"]} == {"file_authority"}
    assert "publication_eval_latest" in {entry["surface_id"] for entry in policy["authority_surfaces"]}
    assert policy["lifecycle_ref_indexes"][0]["storage_role"] == "opl_state_index_source_adapter_ref"
    assert policy["lifecycle_ref_indexes"][0]["owner"] == "one-person-lab"
    assert policy["lifecycle_ref_indexes"][0]["surface_role"] == "opl_state_index_source_adapter"
    assert policy["lifecycle_ref_indexes"][0]["ref"]["ref"] == "runtime/artifacts/domain_authority_refs.sqlite"
    assert policy["projection_caches"][0]["storage_role"] == "projection_cache"
    assert policy["explicit_archive_import_refs"][0]["storage_role"] == "explicit_archive_import_ref_only"

    ledger = payload["lifecycle_ledger"]
    assert ledger["surface_kind"] == "family_lifecycle_ledger"
    assert ledger["target_domain_id"] == "med-autoscience"
    assert ledger["phase"] == "verify"
    assert ledger["actions"][0]["manifest_ref"]["ref"] == (
        "/opl_family_persistence_lifecycle_owner_route_adoption/refs/sqlite_refs_index"
    )
    assert ledger["actions"][0]["authority_owner"] == "one-person-lab"
    assert ledger["actions"][0]["safety_gate"] == "refs_only_no_domain_truth_write"
    assert ledger["actions"][0]["sha256"] == "0" * 64
    assert ledger["actions"][0]["restore_ref"]["ref"] == "/session_continuity/restore_surface"

    owner_route = payload["owner_route"]
    assert owner_route["surface_kind"] == "family_owner_route"
    assert owner_route["target_domain_id"] == "med-autoscience"
    assert owner_route["next_owner"] == "med-autoscience"
    assert owner_route["allowed_actions"] == [
        "workspace-cockpit",
        "submit-study-task",
        "launch-study",
        "study-progress",
    ]
    assert owner_route["idempotency_key"] == "med-autoscience:product-entry-manifest:manifest-projection"
    assert "/opl_family_persistence_lifecycle_owner_route_adoption" in {
        entry["ref"] for entry in owner_route["projection_refs"]
    }

def assert_manifest_runtime_and_continuity(*, module, payload, profile, profile_ref) -> None:
    _assert_manifest_runtime_identity(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_managed_runtime_contract(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_runtime_inventory(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_session_and_progress_projection(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_research_runtime_control_projection(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_artifact_inventory_summary(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
    _assert_family_persistence_lifecycle_owner_route(module=module, payload=payload, profile=profile, profile_ref=profile_ref)
