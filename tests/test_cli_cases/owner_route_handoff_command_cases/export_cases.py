from __future__ import annotations

from .shared import *  # noqa: F403,F401

def test_sidecar_export_projects_mas_owned_runtime_surfaces(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {"state": "running", "owner_route": {"owner": "mas_controller"}},
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {"state": "breach", "breach_reason": "worker_recovery"},
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "owner_receipt_handoff" / "latest.json",
        {"current_action": "safe_reconcile_ready", "retry_budget": {"remaining": 2}},
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {"decision_id": "decision-001", "owner_route": {"owner": "publication_controller"}},
    )

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "mas_family_sidecar_export"
    assert payload["target_domain_id"] == "medautoscience"
    framework = payload["online_runtime_framework"]
    assert framework["owner"] == "one-person-lab"
    assert framework["framework_role"] == "codex_first_stage_led_provider_backed_runtime_framework"
    assert framework["stage_semantics"] == "human_expert_large_task_stage"
    assert framework["minimal_executor"] == "Codex CLI"
    assert framework["provider_abstraction"] == "opl_family_runtime_provider"
    assert framework["target_production_provider"] == "Temporal"
    assert framework["executor_adapter_requirement"] == {
        "owner": "one-person-lab",
        "generic_executor_adapter_owner": "one-person-lab",
        "default_executor_kind": "codex_cli_default",
        "required_capability": "opl_executor_adapter_receipt",
        "mas_accepts": "typed_closeout_or_domain_task_receipt",
        "mas_local_codex_cli_scope": "standalone_diagnostics_only",
        "external_executor_opt_in_policy": "explicit_opl_opt_in_then_typed_receipt_only",
        "mas_owned_hermes_or_claude_executor": False,
        "mas_does_not_provide": ["hosted_executor", "hermes_executor_adapter", "claude_executor_adapter"],
    }
    assert "diagnostic_providers" not in framework
    assert framework["optional_executor_adapters"] == [
        {
            "adapter_id": "hermes_agent",
            "display_name": "Hermes-Agent",
            "classification": "explicit_optional_executor_adapter",
            "runtime_policy": "explicit_opl_opt_in_then_typed_receipt_only",
            "executor_policy": "not_a_mas_executor_adapter",
            "default_provider": False,
        }
    ]
    assert payload["authority_boundary"]["domain_truth_owner"] == "med-autoscience"
    assert payload["authority_boundary"]["online_runtime_provider_owner"] == "opl_family_runtime_provider"
    assert payload["authority_boundary"]["mas_domain_authority"] == [
        "study_truth",
        "memory_body",
        "evidence_ledger",
        "review_ledger",
        "runtime_health_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "publication_authority",
        "owner_route_decision",
    ]
    assert payload["authority_boundary"]["opl_receipt_policy"] == "transport_receipt_only_no_domain_truth_authority"
    assert payload["authority_boundary"]["forbidden_authorities"] == [
        "study_truth_write",
        "memory_body_write",
        "evidence_ledger_write",
        "review_ledger_write",
        "publication_quality_verdict",
        "artifact_gate_override",
        "publication_authority_write",
        "current_package_write",
    ]
    assert payload["authority_boundary"]["opl_substrate_authority"] == (
        "locator_index_lifecycle_projection_only"
    )
    assert payload["authority_boundary"]["owns_generic_scheduler"] is False
    assert payload["authority_boundary"]["owns_generic_daemon"] is False
    assert payload["authority_boundary"]["owns_generic_queue"] is False
    assert payload["authority_boundary"]["owns_generic_attempt_ledger"] is False
    assert payload["authority_boundary"]["owns_generic_locator"] is False
    assert payload["authority_boundary"]["owns_generic_lifecycle"] is False
    assert payload["authority_boundary"]["owns_generic_projection"] is False
    assert payload["authority_boundary"]["owns_generic_runner"] is False
    assert payload["authority_boundary"]["owns_generic_workbench"] is False
    boundary = payload["functional_consumer_boundary"]
    assert boundary["surface_kind"] == "mas_functional_consumer_boundary"
    assert boundary["generic_surface_owner"] == "one-person-lab"
    assert set(boundary["mas_does_not_own"]) >= {
        "generic_scheduler",
        "generic_daemon",
        "generic_queue",
        "generic_attempt_ledger",
        "generic_runner",
        "generic_workbench",
    }
    assert set(boundary["mas_domain_authority_surfaces"]) >= {
        "study_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "publication_route_memory_body",
        "owner_receipt",
        "typed_blocker",
        "safe_action_refs",
    }
    assert boundary["declarative_pack_compiler_input"]["compiler_owner"] == "one-person-lab"
    assert boundary["declarative_pack_compiler_input"]["compiler_outputs_expected"] == [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "product_status",
        "product_session",
        "domain_action_adapter",
        "sidecar",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ]
    assert boundary["generated_surface_handoff"]["current_mas_role"] == (
        "domain_handler_and_refs_projection_source"
    )
    assert boundary["generated_surface_handoff"]["mas_handwritten_shell_expansion_allowed"] is False
    assert boundary["generated_surface_handoff"]["long_term_mas_owner"] is False
    assert boundary["minimal_authority_function_manifest"]["function_ids"] == [
        "publication_quality_verdict",
        "ai_reviewer_quality_decision",
        "artifact_mutation_authorization",
        "publication_route_memory_accept_reject",
        "source_readiness_verdict",
        "owner_receipt_signer",
        "medical_helper_implementation",
    ]
    inventory_by_id = {
        item["module_id"]: item for item in boundary["functional_module_inventory"]
    }
    assert len(inventory_by_id) == 18
    assert inventory_by_id["domain_authority_refs_index"]["migration_action"] == (
        "declare_domain_authority_refs_index_and_consume_opl_current_control_state"
    )
    assert inventory_by_id["domain_authority_refs_index"]["current_ref_status"] == (
        "domain_authority_refs_index_no_runtime_lifecycle_owner"
    )
    assert inventory_by_id["publication_quality_verdict"]["migration_action"] == "authority_stays_in_mas"
    assert inventory_by_id["publication_quality_verdict"]["classification"] == "minimal_authority_function"
    assert payload["profile"]["profile_ref"] == str(profile_path)
    assert payload["workspace"]["workspace_root"] == str(workspace_root)
    substrate = payload["opl_substrate_adapter"]
    assert substrate["surface_kind"] == "mas_opl_generic_substrate_adapter"
    assert substrate["mode"] == "opaque_index_only_refs"
    assert substrate["projection_policy"] == {
        "body_included": False,
        "opl_may_index": True,
        "opl_may_resolve_locator": True,
        "opl_may_manage_lifecycle": True,
        "opl_may_project_status": True,
        "opl_may_write_mas_truth": False,
        "opl_may_write_memory_body": False,
        "opl_may_write_evidence_ledger": False,
        "opl_may_write_review_ledger": False,
        "opl_may_write_publication_or_artifact_authority": False,
    }
    assert substrate["authority_boundary"]["mas_owns"] == [
        "study_truth",
        "memory_body",
        "evidence_ledger",
        "review_ledger",
        "publication_authority",
        "artifact_authority",
    ]
    assert substrate["authority_boundary"]["opl_owns"] == [
        "locator",
        "index",
        "lifecycle",
        "projection",
    ]
    assert substrate["authority_boundary"]["can_write_publication_eval"] is False
    assert substrate["authority_boundary"]["can_write_controller_decisions"] is False
    assert substrate["authority_boundary"]["can_write_current_package"] is False
    for ref_family in ("workspace_refs", "source_refs", "artifact_refs", "memory_refs"):
        assert substrate[ref_family]
        assert all(ref["body_included"] is False for ref in substrate[ref_family])
        assert all(ref["write_permitted"] is False for ref in substrate[ref_family])
        assert all(ref["opaque_to_opl"] is True for ref in substrate[ref_family])
        assert all(ref["index_only"] is True for ref in substrate[ref_family])
    artifact_roles = {ref["role"] for ref in substrate["artifact_refs"]}
    assert {
        "publication_eval",
        "controller_decisions",
        "evidence_ledger",
        "review_ledger",
        "current_package_root",
        "current_package_zip",
    } <= artifact_roles
    memory_roles = {ref["role"] for ref in substrate["memory_refs"]}
    assert "publication_route_memory_pack" in memory_roles
    assert "domain_memory_descriptor" in memory_roles
    provider = payload["provider_ready_adapter"]
    assert provider["surface_kind"] == "mas_opl_provider_ready_contract"
    assert provider["provider_topology"]["target_provider"] == "temporal"
    assert provider["provider_topology"]["provider_attempt_is_truth"] is False
    runtime_handoff = payload["opl_unique_control_plane_handoff"]
    assert "runtime_transport_handoff_projection" not in payload
    assert "runtime_transport_handoff_projection" not in provider
    assert runtime_handoff == provider["opl_unique_control_plane_handoff"]
    assert runtime_handoff["status"] == "opl_generic_runtime_owner_mas_domain_bridge_only"
    assert runtime_handoff["generic_runtime_owner"] == "one-person-lab"
    assert runtime_handoff["domain_intent_adapter_role"] == (
        "refs_only_owner_route_typed_blocker_and_owner_receipt_handoff"
    )
    assert runtime_handoff["retired_runtime_transport_surfaces"][0]["retirement_status"] == (
        "package_absent_physically_retired_no_alias"
    )
    assert runtime_handoff["default_caller_policy"]["mas_runtime_transport_active_as_generic_provider"] is False
    assert runtime_handoff["default_caller_policy"]["mas_runtime_transport_active_contract_surface"] is False
    assert runtime_handoff["generated_default_caller_boundary"] == payload[
        "functional_consumer_boundary"
    ]["generated_default_caller_boundary"]
    assert runtime_handoff["physical_retirement_gate_matrix"] == payload[
        "functional_consumer_boundary"
    ]["physical_retirement_gate_matrix"]
    no_resurrection_summary = runtime_handoff["physical_retirement_gate_matrix"]["no_resurrection_summary"]
    assert no_resurrection_summary["default_runtime_owner"] == "one-person-lab"
    assert no_resurrection_summary["mas_default_runtime_owner_allowed"] is False
    assert no_resurrection_summary["all_runtime_control_surfaces_retired_or_opl_owned"] is True
    assert no_resurrection_summary["physical_delete_candidate_count"] == 6
    assert no_resurrection_summary["physical_delete_ready_count"] == 2
    assert no_resurrection_summary["physically_retired_surface_ids"] == [
        "runtime_transport",
        "lifecycle_refs_sqlite_index",
    ]
    assert no_resurrection_summary["remaining_surfaces_are_domain_refs_not_runtime_control"] is True
    assert "generic_worker_residency_owner" in runtime_handoff["forbidden_mas_roles"]
    assert "legacy_provider" not in provider["provider_topology"]
    assert "legacy_provider_classification" not in provider["provider_topology"]
    assert provider["legacy_retirement_tombstone_proof"]["status"] == "no_active_default_caller_proven"
    assert provider["executor_requirements"] == {
        "adapter_owner": "one-person-lab",
        "generic_executor_adapter_owner": "one-person-lab",
        "default_executor_kind": "codex_cli_default",
        "required_adapter": "opl_executor_adapter",
        "accepted_receipts": ["opl_provider_attempt_receipt", "typed_closeout_receipt"],
        "domain_action_authority": "med-autoscience",
        "mas_builtin_executor_adapter": False,
        "mas_local_codex_cli_scope": "standalone_diagnostics_only",
        "non_default_executor_opt_in_owner": "one-person-lab",
        "non_default_executor_opt_in_policy": "explicit_opt_in_only_receipt_to_mas",
        "mas_owned_hermes_or_claude_executor": False,
    }
    assert provider["direct_mas_path"]["status"] == "authoritative"
    assert provider["truth_source_precedence"]["direct_mas_skill_path"] == "authoritative"
    assert provider["truth_source_precedence"]["provider_completion_can_advance_paper_progress"] is False
    assert provider["workspace_runtime_artifact_root_locator"]["repo_root_tracks_real_artifacts"] is False
    assert provider["sidecar_contract"]["queue_hydration_source"] == "/pending_family_tasks"
    assert payload["dispatch"]["receipt_refs"]["dispatch_receipt_root"] == (
        "artifacts/runtime/opl_family_sidecar/dispatch_receipts"
    )
    assert "family_runtime_supervision" not in payload
    family_handoff = payload["family_opl_current_control_state_handoff"]
    assert family_handoff["surface_kind"] == "family_opl_current_control_state_handoff"
    assert family_handoff["repair_command"] == (
        f"medautosci owner-route-reconcile --profile {profile_path} "
        "--developer-supervisor-mode developer_apply_safe"
    )
    assert family_handoff["local_scheduler_tombstone_ref"] == (
        "contracts/runtime/legacy-active-path-tombstones.json#mas-local-scheduler"
    )
    assert family_handoff["consumer_migration"]["active_path_role"] == (
        "opl_replacement_default"
    )
    assert family_handoff["consumer_migration"]["replacement_owner"] == "one-person-lab"
    assert family_handoff["consumer_migration"]["replacement_owner_surface"] == (
        "opl_provider_runtime_manager"
    )
    assert family_handoff["read_only_authority_boundary"]["runtime_owner"] == "one-person-lab"
    assert family_handoff["read_only_authority_boundary"]["scheduler_owner"] == "one-person-lab"
    assert family_handoff["read_only_authority_boundary"]["domain_owner"] == "med-autoscience"
    assert family_handoff["read_only_authority_boundary"]["mas_local_scheduler_role"] == (
        "physical_retired_tombstone_provenance_only"
    )
    study_projection = payload["studies"][0]
    assert study_projection["study_id"] == "001-risk"
    assert "runtime_supervision" not in study_projection
    assert "slo_status" not in study_projection
    assert "owner_receipt_handoff" not in study_projection
    assert study_projection["controller_decisions"]["decision_id"] == "decision-001"
    assert any(
        ref["role"] == "controller_decisions" and ref["exists"] is True
        for ref in study_projection["domain_owned_source_refs"]
    )
    assert study_projection["autonomy_continuation"]["status"] == "retired_runtime_liveness_scheduler_signal"
    assert study_projection["autonomy_continuation"]["replacement_owner"] == "one-person-lab"
    assert payload["pending_family_tasks"] == []


def test_sidecar_export_projects_memory_paper_soak_proof_refs_readonly(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "stage_knowledge" / "paper_soak_memory_apply_proof" / "latest.json",
        {
            "surface": "paper_soak_memory_apply_proof",
            "schema_version": 1,
            "study_id": "001-risk",
            "stage": "decision",
            "status": "ready",
            "stage_entry": {
                "publication_route_memory_refs": [
                    {
                        "memory_id": "publication_route_memory_seed__negative_result_stoploss",
                        "memory_pack_ref": "portfolio/research_memory/publication_route_memory/memory_pack.json",
                    }
                ]
            },
            "typed_closeout_writeback_proposals": [{"ref": "closeouts/decision.json", "body_included": False}],
            "mas_router_receipt_refs": [{"ref": "router/r1.json", "status": "applied", "body_included": False}],
            "opl_aion_readonly_receipt_refs": [
                {
                    "ref_kind": "memory_write_router_receipt",
                    "ref": "router/r1.json",
                    "status": "applied",
                    "display_role": "receipt_ref_only",
                    "consumer": "OPL/Aion",
                    "body_included": False,
                }
            ],
            "source_fingerprint": "proof-fp",
            "authority_boundary": {"can_authorize_publication_quality": False},
            "read_only_display_policy": {
                "consumer_role": "OPL/Aion read-only display",
                "repo_tracks_memory_body": False,
                "repo_tracks_receipt_instances": False,
                "can_write_study_truth": False,
            },
        },
    )

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    projection = payload["studies"][0]["memory_paper_soak_proof"]
    assert projection["surface_kind"] == "mas_memory_paper_soak_proof_projection"
    assert projection["status"] == "ready"
    assert projection["proof_ref"] == (
        "studies/001-risk/artifacts/stage_knowledge/paper_soak_memory_apply_proof/latest.json"
    )
    assert projection["route_memory_ref_count"] == 1
    assert projection["router_receipt_ref_count"] == 1
    assert projection["writeback_proposal_ref_count"] == 1
    assert projection["receipt_refs"] == [
        {
            "ref_kind": "memory_write_router_receipt",
            "ref": "router/r1.json",
            "status": "applied",
            "display_role": "receipt_ref_only",
            "consumer": "OPL/Aion",
            "body_included": False,
        }
    ]
    assert projection["read_only_display_policy"]["repo_tracks_memory_body"] is False
    assert projection["read_only_display_policy"]["can_write_study_truth"] is False
    assert "prose_summary" not in json.dumps(projection, ensure_ascii=False)


def test_sidecar_export_consumes_opl_production_proof_without_domain_authority(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    proof_ref = tmp_path / "opl-production-proof.json"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        workspace_root / "studies" / "001-risk" / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {"state": "running"},
    )
    _write_opl_production_proof(proof_ref)

    exit_code = cli.main(
        [
            "sidecar",
            "export",
            "--profile",
            str(profile_path),
            "--opl-production-proof",
            str(proof_ref),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    read_model = payload["provider_ready_adapter"]["provider_guarded_soak_read_model"]
    availability = read_model["provider_availability"]

    assert exit_code == 0
    assert payload["provider_ready_adapter"]["provider_topology"]["provider_state"] == (
        "production_residency_proven"
    )
    assert payload["provider_ready_adapter"]["provider_topology"]["hosted_runtime_policy"] == (
        "default_enabled_opl_temporal_hosted_autonomy"
    )
    assert payload["provider_ready_adapter"]["provider_topology"]["codex_app_outer_driver_required"] is False
    assert payload["provider_ready_adapter"]["provider_topology"]["mas_daemon_scheduler_attempt_loop_allowed"] is False
    assert availability["status"] == "available"
    assert availability["provider_attempt_available"] is True
    assert availability["proof_ref"] == str(proof_ref)
    assert availability["semantics"]["provider_completion_is_paper_closure"] is False
    assert availability["semantics"]["mas_domain_health_diagnostic_role"] == "domain_truth_and_local_diagnostics"
    managed_state = payload["managed_temporal_state_consistency"]
    assert managed_state["surface_kind"] == "mas_opl_managed_temporal_state_consistency"
    assert managed_state["status"] == "consistent"
    assert managed_state["provider_state"] == "production_residency_proven"
    assert managed_state["default_autonomous_runtime"] == {
        "enabled_by_default": True,
        "hosted_runtime_owner": "one-person-lab",
        "hosted_runtime_provider": "temporal",
        "runtime_substrate": "opl_hosted_stage_runtime",
        "persistent_online_control_plane": "opl_temporal",
        "task_start_handoff": "mas_domain_intent_to_opl_stage_attempt",
        "wakeup_retry_resume_owner": "one-person-lab",
        "codex_app_outer_driver_required": False,
        "mas_daemon_scheduler_attempt_loop_allowed": False,
    }
    assert managed_state["managed_state"] == {
        "address_source": "managed_local_service_state",
        "lifecycle_status": "ready",
        "server_reachable": True,
        "worker_ready": True,
        "task_queue": "opl-stage-attempts",
    }
    assert managed_state["opl_status_projection"]["managed_service_state"] == "ready"
    assert managed_state["opl_status_projection"]["worker_state"] == "ready"
    assert managed_state["opl_status_projection"]["attempt_query_ready"] is True
    assert managed_state["authority_boundary"]["can_write_domain_truth"] is False
    tombstone = payload["legacy_retirement_tombstone_proof"]
    assert tombstone["surface_kind"] == "mas_legacy_retirement_tombstone_proof"
    assert tombstone["status"] == "no_active_default_caller_proven"
    assert tombstone["active_default_callers"] == []
    assert {item["surface_id"] for item in tombstone["retired_or_tombstoned_surfaces"]} == {
        "hermes_agent_executor_adapter",
        "hermes_scheduler_hosted_runtime",
        "mds_deepscientist_backend",
        "workspace_local_scheduler",
    }
    assert tombstone["authority_boundary"]["can_authorize_publication_quality"] is False
    assert read_model["provider_completion_semantics"] == {
        "provider_completion_is_paper_closure": False,
        "queue_completion_is_paper_closure": False,
        "paper_closure_requires_mas_owner_receipt": True,
        "mutation_proof_surface": "MAS owner receipt",
    }
    assert read_model["authority_boundary"]["can_write_domain_truth"] is False
    assert read_model["authority_boundary"]["can_authorize_publication_quality"] is False
    assert all(
        item["status"] == "provider_available_guarded_apply_pending"
        for item in read_model["target_coverage"]
    )
    closure = payload["mas_functional_closure_status_projection"]
    assert closure["surface_kind"] == "mas_functional_closure_status_projection"
    assert closure["summary"]["production_evidence_pending_count"] == 2
    assert closure["authority_boundary"]["provider_completion_is_paper_closure"] is False
    by_line = {line["line_id"]: line for line in closure["lines"]}
    assert by_line["p2_provider_residency_and_activity_soak"]["status"] == (
        "provider_residency_projected_domain_activity_soak_pending"
    )
    assert by_line["p0_live_paper_autonomy_acceptance"]["typed_blockers"][0]["blocker_id"] == (
        "provider_hosted_live_paper_apply_pending"
    )
    assert by_line["legacy_residue_retirement"]["status"] == (
        "no_active_default_caller_proven_cleanup_policy_satisfied"
    )
    guarded_apply_tasks = [
        task for task in payload["pending_family_tasks"]
        if task["task_kind"] == "paper_autonomy/guarded-apply"
    ]
    assert [task["payload"]["study_id"] for task in guarded_apply_tasks] == [
        "DM002",
        "DM003",
        "Obesity",
    ]
    fingerprints = {
        task["payload"]["study_id"]: task.pop("source_fingerprint")
        for task in guarded_apply_tasks
    }
    assert all(isinstance(value, str) and len(value) == 16 for value in fingerprints.values())
    expected_refs = {
        "DM002": "studies/DM002/artifacts/controller_decisions/latest.json",
        "DM003": "studies/DM003/artifacts/controller_decisions/latest.json",
        "Obesity": "studies/Obesity/artifacts/controller_decisions/latest.json",
    }
    for task in guarded_apply_tasks:
        study_id = task["payload"]["study_id"]
        dedupe_key = f"mas:nfpitnet:{study_id}:provider-hosted-guarded-apply:opl-temporal"
        evidence_payload = task.pop("domain_dispatch_evidence_record_payload")
        assert evidence_payload["surface_kind"] == "mas_domain_dispatch_evidence_record_payload"
        assert evidence_payload["domain_id"] == "medautoscience"
        assert evidence_payload["task_kind"] == "paper_autonomy/guarded-apply"
        assert evidence_payload["study_id"] == study_id
        assert evidence_payload["body_included"] is False
        assert evidence_payload["domain_ready_claimed"] is False
        assert evidence_payload["authority_boundary"]["opl_records_refs_only"] is True
        assert evidence_payload["authority_boundary"]["opl_writes_mas_truth"] is False
        assert evidence_payload["record_payload"]["typed_blocker_refs"]
        assert evidence_payload["record_payload"]["evidence_refs"]
        assert evidence_payload["record_payload"]["no_regression_refs"]
        assert evidence_payload["opl_runtime_action_execute_payload"] == evidence_payload[
            "record_payload"
        ]
        assert evidence_payload["opl_runtime_action_execute_usage"]["payload_field"] == (
            "opl_runtime_action_execute_payload"
        )
        assert evidence_payload["opl_runtime_action_execute_usage"][
            "operator_must_bind_to_matching_opl_target_identity"
        ] is True
        assert evidence_payload["identity_binding"]["payload_identity"]["task_kind"] == (
            "paper_autonomy/guarded-apply"
        )
        assert evidence_payload["identity_binding"]["payload_identity"]["study_id"] == study_id
        assert evidence_payload["identity_binding"]["payload_identity"]["profile_name"] == "nfpitnet"
        assert evidence_payload["identity_binding"]["conflict_error_kind"] == (
            "domain_dispatch_evidence_receipt_conflict"
        )
        assert "receipt_ref" not in evidence_payload["record_payload"]
        assert evidence_payload["ledger_receipt_ref_hint"].startswith(
            "mas://domain-dispatch-evidence/medautoscience/"
        )
        assert {
            packet["role"] for packet in evidence_payload["body_free_evidence_packets"]
        } == {"stable_typed_blocker_ref", "no_forbidden_write_proof_ref"}
        assert task == {
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/guarded-apply",
            "priority": 30,
            "source": "mas-sidecar-export",
            "requires_approval": False,
            "dedupe_key": dedupe_key,
            "payload": {
                "profile": str(profile_path),
                "study_id": study_id,
                "target_studies": [study_id],
                "provider_attempt_id": f"opl-temporal:nfpitnet:{study_id}:provider-hosted-guarded-apply",
                "idempotency_key": dedupe_key,
                "paper_autonomy_reason": "provider_hosted_guarded_apply_soak",
                "authority_boundary": "mas_owner_guarded_apply_only",
                "selected_evidence_surface": (
                    "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence"
                ),
                "canary_gate_id": "real_paper_line_provider_canary",
                "closeout_requires_mas_owner_receipt_or_typed_blocker": True,
            },
            "dispatch_owner": "med-autoscience",
            "profile_name": "nfpitnet",
            "source_refs": [
                {
                    "role": "opl_production_proof",
                    "ref": str(proof_ref),
                    "exists": True,
                },
                {
                    "role": "provider_guarded_soak_read_model",
                    "ref": "/provider_ready_adapter/provider_guarded_soak_read_model",
                    "exists": True,
                },
                {
                    "role": "paper_line_guarded_apply_evidence",
                    "ref": (
                        "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence"
                    ),
                    "exists": True,
                    "body_included": False,
                },
                {
                    "role": "mas_guarded_apply_owner_receipt_contract",
                    "ref": "mas-guarded-apply-owner-receipt.v2",
                    "exists": True,
                },
                {
                    "role": "mas_owner_controller_decision",
                    "ref": expected_refs[study_id],
                    "exists": False,
                },
            ],
        }
    repeat_exit_code = cli.main(
        [
            "sidecar",
            "export",
            "--profile",
            str(profile_path),
            "--opl-production-proof",
            str(proof_ref),
            "--format",
            "json",
        ]
    )
    repeat_payload = json.loads(capsys.readouterr().out)
    assert repeat_exit_code == 0
    repeat_tasks = [
        task for task in repeat_payload["pending_family_tasks"]
        if task["task_kind"] == "paper_autonomy/guarded-apply"
    ]
    assert {
        task["payload"]["study_id"]: task["source_fingerprint"]
        for task in repeat_tasks
    } == fingerprints


def test_sidecar_export_projects_ai_reviewer_repair_recheck_tasks(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _ai_reviewer_blocking_eval(study_root),
    )

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study = payload["studies"][0]
    assert study["paper_autonomy_loop"]["status"] == "repair_recheck_ready"
    assert study["paper_autonomy_loop"]["eligible_for_auto_dispatch"] is True
    repair_tasks = [
        task for task in payload["pending_family_tasks"]
        if task["task_kind"] == "paper_autonomy/repair-recheck"
    ]
    assert repair_tasks
    first_task = repair_tasks[0]
    assert first_task["payload"]["profile"] == str(profile_path)
    assert first_task["payload"]["study_id"] == "001-risk"
    assert first_task["payload"]["authority_boundary"] == "mas_owner_reconcile_only"
    assert first_task["dispatch_owner"] == "med-autoscience"
    unit = first_task["payload"]["repair_work_unit"]
    assert unit["owner"] in {"quality_repair_batch", "ai_reviewer"}
    assert unit["callable_surface"]
    assert unit["gate_replay_target"] in {
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
    }
    assert unit["direct_package_mutation_allowed"] is False
    assert unit["current_package_mutation_allowed"] is False
    assert unit["quality_authorization_allowed"] is False
    assert unit["submission_authorization_allowed"] is False
    assert unit["prohibited_outputs"] == [
        "paper/current_package",
        "manuscript/current_package",
        "quality_override",
        "submission_authorization",
    ]


def test_sidecar_export_projects_controller_route_back_as_pending_task(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "study-decision::dm002::route-back::2026-05-21T17:36:04+00:00",
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "emitted_at": "2026-05-21T17:36:04+00:00",
            "decision_type": "route_back_same_line",
            "requires_human_confirmation": False,
            "controller_actions": [
                {
                    "action_type": "request_opl_stage_attempt",
                    "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                }
            ],
            "route_target": "analysis-campaign",
            "route_key_question": "当前 AI reviewer-backed route-back 应由哪一个同线 owner work unit 继续？",
            "route_rationale": "The current AI reviewer-backed quality record names a same-line owner route.",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::"
                "unit_harmonized_validation_uncertainty_and_grouped_calibration"
            ),
            "next_work_unit": {
                "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                "lane": "analysis-campaign",
                "summary": (
                    "Add uncertainty intervals, grouped calibration evidence, and reproducibility details "
                    "to the unit-harmonized external validation."
                ),
            },
            "blocking_work_units": [
                {
                    "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                    "lane": "analysis-campaign",
                    "summary": (
                        "Missing validation uncertainty and grouped calibration outputs block "
                        "publication readiness."
                    ),
                }
            ],
        },
    )

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    route_tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"] == "domain_route/owner-handoff"
    ]
    assert len(route_tasks) == 1
    task = route_tasks[0]
    assert task["source"] == "mas-controller-decision"
    assert task["requires_approval"] is False
    assert task["dedupe_key"].startswith(
        "mas:nfpitnet:002-dm-china-us-mortality-attribution:controller-decision:"
    )
    assert task["source_fingerprint"]
    assert task["payload"]["profile"] == str(profile_path)
    assert task["payload"]["study_id"] == "002-dm-china-us-mortality-attribution"
    assert task["payload"]["continuation_reason"] == "controller_decision_route_back"
    assert task["payload"]["route_target"] == "analysis-campaign"
    assert task["payload"]["next_work_unit"]["unit_id"] == (
        "unit_harmonized_validation_uncertainty_and_grouped_calibration"
    )
    assert task["payload"]["work_unit_fingerprint"] == (
        "domain-transition::route_back_same_line::"
        "unit_harmonized_validation_uncertainty_and_grouped_calibration"
    )
    assert task["payload"]["authority_boundary"] == "mas_owner_reconcile_only"
    assert task["domain_truth_owner"] == "med-autoscience"
    assert task["queue_owner"] == "one-person-lab"
    assert task["reason"] == "controller_decision_route_back"
    assert task["dispatch_owner"] == "med-autoscience"
    assert task["profile_name"] == "nfpitnet"
    assert task["source_refs"] == [
        {
            "role": "mas_controller_decision_route_back",
            "ref": "studies/002-dm-china-us-mortality-attribution/artifacts/controller_decisions/latest.json",
            "exists": True,
        }
    ]
    evidence_payload = task["domain_dispatch_evidence_record_payload"]
    assert evidence_payload["surface_kind"] == "mas_domain_dispatch_evidence_record_payload"
    assert evidence_payload["task_kind"] == "domain_route/owner-handoff"
    assert evidence_payload["study_id"] == "002-dm-china-us-mortality-attribution"
    assert evidence_payload["source_fingerprint"] == task["source_fingerprint"]
    assert evidence_payload["domain_source_fingerprint"] == task["source_fingerprint"]
    assert evidence_payload["profile_name"] == "nfpitnet"
    assert {
        key: evidence_payload["record_payload"][key]
        for key in ("domain_id", "task_kind", "study_id", "source_fingerprint", "profile_name")
    } == {
        "domain_id": "medautoscience",
        "task_kind": "domain_route/owner-handoff",
        "study_id": "002-dm-china-us-mortality-attribution",
        "source_fingerprint": task["source_fingerprint"],
        "profile_name": "nfpitnet",
    }
    assert evidence_payload["record_payload"]["typed_blocker_refs"]
    assert evidence_payload["record_payload"]["no_regression_refs"]
    assert evidence_payload["opl_runtime_action_execute_payload"] == evidence_payload["record_payload"]
    assert evidence_payload["opl_runtime_action_execute_usage"]["required_preflight_status_before_record"] == (
        "ready_to_record"
    )
    assert evidence_payload["opl_runtime_action_execute_usage"][
        "required_identity_binding_status_before_record"
    ] == "matched"
    assert evidence_payload["identity_binding"]["payload_identity"] == {
        "domain_id": "medautoscience",
        "task_kind": "domain_route/owner-handoff",
        "study_id": "002-dm-china-us-mortality-attribution",
        "source_fingerprint": task["source_fingerprint"],
        "domain_source_fingerprint": task["source_fingerprint"],
        "profile_name": "nfpitnet",
    }
    assert evidence_payload["body_included"] is False
    assert evidence_payload["domain_ready_claimed"] is False


def test_sidecar_export_projects_publication_aftercare_analysis_and_reviewer_tasks(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "DM002"
    aris_root = study_root / "artifacts" / "algorithm_research" / "aris"
    write_profile(profile_path, workspace_root=workspace_root)
    for name in (
        "input_contract.json",
        "algorithm_scout_report.md",
        "innovation_hypotheses.md",
        "final_method_proposal.md",
        "experiment_plan.md",
        "experiment_results_summary.md",
        "review_loop_summary.md",
        "prior_limitations.md",
        "why_our_method_can_work.md",
        "claim_to_evidence_map.md",
        "sidecar_manifest.json",
    ):
        if name.endswith(".json"):
            _write_json(aris_root / name, {"provider": "aris", "status": "result_ready"})
        else:
            (aris_root / name).parent.mkdir(parents=True, exist_ok=True)
            (aris_root / name).write_text("# ref-only\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "analysis_queue" / "latest.json",
        {
            "queue_ref": "analysis-queue:dm002/reviewer-repair",
            "items": [{"item_ref": "analysis-item:rerun", "source_refs": ["review-ref:ledger"]}],
            "experiment_refs": ["experiment-ref:rerun"],
            "reviewer_refs": ["review-ref:ledger"],
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "review_refs": ["review-ref:eval"]},
    )
    _write_json(study_root / "paper" / "review" / "review_ledger.json", {"review_refs": ["review-ref:ledger"]})
    _write_json(study_root / "paper" / "claim_evidence_map.json", {"claim_refs": ["claim-ref:main"]})

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    study = payload["studies"][0]
    assert study["publication_aftercare"]["analysis_queue_entry"]["status"] == "ready"
    task_kinds = [task["task_kind"] for task in payload["pending_family_tasks"]]
    assert "publication_aftercare/analysis-queue-progress" in task_kinds
    assert "publication_aftercare/reviewer-refresh" in task_kinds
    aftercare_tasks = [
        task
        for task in payload["pending_family_tasks"]
        if task["task_kind"].startswith("publication_aftercare/")
    ]
    assert all(task["source"] == "mas-publication-aftercare" for task in aftercare_tasks)
    assert all(task["payload"]["authority_boundary"] == "mas_owner_route_task_ref_only" for task in aftercare_tasks)
    assert all(ref["body_included"] is False for task in aftercare_tasks for ref in task["source_refs"])
