from __future__ import annotations

from tests.test_cli_cases.owner_route_handoff_command.shared import *  # noqa: F403,F401


def _guarded_apply_current_owner_delta_contract() -> dict[str, object]:
    return importlib.import_module(
        "med_autoscience.controllers.guarded_apply_owner_delta_contract"
    ).guarded_apply_current_owner_delta_contract()


def _guarded_apply_accepted_answer_shapes() -> list[str]:
    return list(
        importlib.import_module(
            "med_autoscience.controllers.guarded_apply_owner_delta_contract"
        ).GUARDED_APPLY_ACCEPTED_ANSWER_SHAPES
    )


def test_domain_handler_export_consumes_opl_production_proof_without_domain_authority(
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
            "domain-handler",
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
    assert availability["semantics"]["mas_domain_diagnostic_report_role"] == "domain_truth_and_local_diagnostics"
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
    assert "retired_surface_history_projection" not in payload
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
    assert by_line["standard_agent_purity_projection"]["status"] == "standard_agent_source_shape_landed"
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
        assert task["task_id"] == dedupe_key
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
        assert "current_owner_delta" not in task["payload"]
        assert task == {
            "domain_id": "medautoscience",
            "task_id": dedupe_key,
            "task_kind": "paper_autonomy/guarded-apply",
            "priority": 30,
            "source": "mas-domain-handler-export",
            "requires_approval": False,
            "dedupe_key": dedupe_key,
            "default_paper_mission_entry": False,
            "paper_mission_default_role": "diagnostic_or_explicit_owner_handoff",
            "can_select_next_paper_stage": False,
            "can_authorize_provider_admission": False,
            "counts_as_paper_progress": False,
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
                "current_owner_delta_contract": _guarded_apply_current_owner_delta_contract(),
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
                    "role": "opl_current_owner_delta_contract",
                    "ref": "paper_autonomy/guarded-apply",
                    "exists": True,
                    "accepted_answer_shapes": _guarded_apply_accepted_answer_shapes(),
                    "desired_delta": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
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
            "domain-handler",
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
