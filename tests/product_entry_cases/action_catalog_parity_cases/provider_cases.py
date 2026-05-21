from __future__ import annotations

from .shared import *  # noqa: F403,F401

def test_product_entry_manifest_exposes_provider_guarded_soak_read_model_with_typed_blockers(
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    provider_contract = manifest["opl_provider_ready_contract"]
    read_model = manifest["provider_guarded_soak_read_model"]

    assert read_model == provider_contract["provider_guarded_soak_read_model"]
    assert read_model["surface_kind"] == "provider_guarded_soak_read_model"
    assert read_model["version"] == "provider-guarded-soak-read-model.v1"
    assert read_model["mode"] == "descriptor_read_model"
    assert read_model["target_studies"] == ["DM002", "DM003", "Obesity"]
    assert read_model["expected_surface_shape"] == {
        "provider_proof_surface": "real_paper_autonomy_provider_hosted_paper_proof",
        "guarded_apply_surface": "real_paper_autonomy_guarded_apply_proof",
        "closeout_packet_surface": "domain_stage_closeout_packet",
        "typed_blocker_surface": "mas_provider_guarded_soak_typed_blocker",
    }
    assert read_model["provider_availability"]["status"] == "typed_blocker"
    assert read_model["provider_availability"]["provider_attempt_available"] is False
    assert read_model["provider_availability"]["blocker"]["blocker_id"] == (
        "provider_guarded_soak_provider_unavailable"
    )
    assert read_model["provider_completion_semantics"] == {
        "provider_completion_is_paper_closure": False,
        "queue_completion_is_paper_closure": False,
        "paper_closure_requires_mas_owner_receipt": True,
        "mutation_proof_surface": "MAS owner receipt",
    }

    coverage = {item["target_study"]: item for item in read_model["target_coverage"]}
    assert set(coverage) == {"DM002", "DM003", "Obesity"}
    assert all(item["status"] == "typed_blocker" for item in coverage.values())
    assert all(item["write_permitted"] is False for item in coverage.values())
    assert all(item["provider_completion_is_paper_closure"] is False for item in coverage.values())
    assert all(item["paper_closure_requires_mas_owner_receipt"] is True for item in coverage.values())

    proof = read_model["no_forbidden_write_proof"]
    assert proof["surface_kind"] == "mas_opl_forbidden_write_guard_proof"
    assert proof["result"] == "blocked_provider_completion_is_not_paper_closure"
    assert proof["provider_completion_is_paper_closure"] is False
    assert proof["queue_completion_is_paper_closure"] is False
    assert proof["paper_closure_requires_mas_owner_receipt"] is True
    assert proof["only_mas_owner_receipt_can_prove_mutation"] is True
    assert proof["can_write_domain_truth"] is False
    assert proof["can_write_current_package"] is False
    assert proof["can_authorize_publication_quality"] is False

    owner_contract = manifest["owner_receipt_contract"]
    assert owner_contract == provider_contract["owner_receipt_contract"]
    assert manifest["domain_owner_receipt_contract"] == owner_contract
    assert owner_contract["surface_kind"] == "domain_owner_receipt_contract"
    assert owner_contract["accepted_return_shapes"] == [
        "domain_receipt",
        "typed_blocker",
        "no_regression_evidence",
    ]
    assert owner_contract["receipt_ref_policy"]["opl_persists"] == "receipt_refs_only"
    assert owner_contract["receipt_ref_policy"]["memory_body_externalized"] is True
    assert owner_contract["typed_blocker"]["blocker_id"] == "mas_live_owner_receipt_soak_pending"
    assert owner_contract["forbidden_write_guard"]["forbidden_requested_writes"] == []
    assert owner_contract["authority_boundary"]["can_write_domain_truth"] is False
    assert owner_contract["authority_boundary"]["can_write_artifact_gate"] is False
    assert owner_contract["authority_boundary"]["can_write_memory_body"] is False

    evidence = read_model["paper_line_guarded_apply_evidence"]
    assert evidence["surface_kind"] == "mas_paper_line_guarded_apply_evidence_scaleout"
    assert evidence["lane_id"] == "lane_4a_mas_evidence_scaleout"
    assert evidence["mode"] == "domain_owned_refs_only"
    assert evidence["selected_evidence_surface"] == (
        "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence"
    )
    assert evidence["body_included"] is False
    assert evidence["artifact_body_included"] is False
    assert evidence["memory_body_included"] is False
    assert evidence["publication_eval_body_included"] is False
    assert evidence["controller_decision_body_included"] is False
    assert evidence["domain_verdict_claimed"] is False
    assert evidence["provider_completion_is_paper_closure"] is False
    assert evidence["opl_can_write_publication_eval"] is False
    assert evidence["opl_can_write_controller_decisions"] is False
    assert evidence["opl_can_write_artifact_gate"] is False
    assert evidence["opl_can_write_memory_body"] is False
    assert evidence["opl_can_write_final_verdict"] is False
    assert evidence["required_owner_outcome_refs"] == [
        "owner_receipt_ref",
        "progress_delta_ref",
        "ai_reviewer_gate_ref",
        "artifact_movement_ref",
        "human_gate_ref",
        "stop_loss_ref",
        "stable_typed_blocker_ref",
        "no_forbidden_write_proof_ref",
    ]
    opl_contract = evidence["opl_ingestable_ref_contract"]
    assert opl_contract["ref_packet_role"] == "opl_agent_lab_evidence_scaleout_input"
    assert opl_contract["selected_surface"] == "existing_mas_paper_line_guarded_apply_evidence"
    assert opl_contract["allowed_ref_roles"] == [
        "owner_receipt_ref",
        "progress_delta_ref",
        "ai_reviewer_gate_receipt_ref",
        "artifact_movement_ref",
        "human_gate_or_resume_ref",
        "stable_typed_blocker_ref",
        "no_forbidden_write_proof_ref",
    ]
    assert opl_contract["closeout_requires_mas_owner_receipt_or_typed_blocker"] is True
    assert opl_contract["opl_may_persist_refs_only"] is True
    assert opl_contract["opl_may_write_domain_truth"] is False
    assert opl_contract["opl_may_write_memory_body"] is False
    assert opl_contract["opl_may_write_artifact_body"] is False
    assert opl_contract["opl_may_authorize_publication_or_quality"] is False
    packets = {item["required_role"]: item for item in evidence["scaleout_ref_packets"]}
    assert set(packets) == {
        "owner_receipt_ref",
        "progress_delta_ref",
        "ai_reviewer_gate_receipt_ref",
        "artifact_movement_ref",
        "human_gate_or_resume_ref",
        "stable_typed_blocker_ref",
        "no_forbidden_write_proof_ref",
    }
    assert packets["owner_receipt_ref"]["owner_surface"] == "artifacts/runtime/owner_route/latest.json"
    assert packets["progress_delta_ref"]["fallback_owner_surface"] == (
        "artifacts/runtime/turn_closeouts/<active_run_id>.json"
    )
    assert packets["ai_reviewer_gate_receipt_ref"]["owner_surface"] == (
        "artifacts/publication_eval/latest.json"
    )
    assert packets["artifact_movement_ref"]["owner_surface"] == "artifact_authority_receipt"
    assert packets["human_gate_or_resume_ref"]["owner_surface"] == (
        "artifacts/controller_decisions/latest.json"
    )
    assert packets["stable_typed_blocker_ref"]["owner_surface"] == "typed_blocker_receipt"
    assert packets["no_forbidden_write_proof_ref"]["owner_surface"] == (
        "product_entry_manifest.provider_guarded_soak_read_model.no_forbidden_write_proof"
    )
    assert all(packet["body_included"] is False for packet in packets.values())
    assert all(packet["opl_ingestable"] is True for packet in packets.values())
    assert all(packet["write_permitted"] is False for packet in packets.values())

    handoff = evidence["opl_stage_evidence_receipt_handoff"]
    assert handoff["surface_kind"] == "mas_opl_stage_evidence_receipt_handoff"
    assert handoff["mode"] == "refs_only_payload_hints"
    assert handoff["record_action"] == "stage_production_evidence_receipt_record"
    assert handoff["verify_action"] == "stage_production_evidence_receipt_verify"
    assert handoff["payload_body_included"] is False
    assert handoff["opl_may_persist_refs_only"] is True
    assert handoff["opl_may_write_domain_truth"] is False
    assert handoff["opl_may_authorize_publication_or_quality"] is False
    assert handoff["publication_ready_claimed"] is False
    assert handoff["current_package_update_claimed"] is False
    expected_hints = {item["hint_id"]: item for item in handoff["expected_receipt_ref_hints"]}
    assert set(expected_hints) == {
        "owner_receipt",
        "progress_delta",
        "ai_reviewer_gate_receipt",
        "artifact_movement",
        "human_gate_or_resume",
        "stable_typed_blocker",
        "no_forbidden_write_proof",
    }
    assert expected_hints["owner_receipt"]["source_packet_id"] == "owner_receipt_ref_packet"
    assert expected_hints["no_forbidden_write_proof"]["source_ref_role"] == "no_forbidden_write_proof_ref"
    assert all(item["record_role"] == "expected_receipt_ref" for item in expected_hints.values())
    assert all(item["body_included"] is False for item in expected_hints.values())
    freshness = {item["hint_id"]: item for item in handoff["monitor_freshness_ref_hints"]}
    assert set(freshness) == {
        "paper_progress_delta_freshness",
        "quality_gate_freshness",
        "artifact_movement_freshness",
        "human_gate_or_stable_blocker_freshness",
        "forbidden_write_guard_freshness",
    }
    assert freshness["forbidden_write_guard_freshness"]["source_ref_roles"] == [
        "no_forbidden_write_proof_ref"
    ]
    assert all(item["record_role"] == "monitor_freshness_ref" for item in freshness.values())
    assert all(item["body_included"] is False for item in freshness.values())
    assert handoff["closeout_requires"] == [
        "mas_owner_receipt_ref",
        "progress_delta_ref_or_stable_typed_blocker_ref",
        "no_forbidden_write_proof_ref",
    ]
    no_forbidden = evidence["no_forbidden_write_proof_handoff"]
    assert no_forbidden["proof_ref_role"] == "no_forbidden_write_proof_ref"
    assert no_forbidden["must_be_recorded_with_each_opl_stage_evidence_receipt"] is True
    assert no_forbidden["body_included"] is False
    assert no_forbidden["write_permitted"] is False
    assert no_forbidden["opl_projection_only"] is True

    outcomes = {item["outcome_id"]: item for item in evidence["domain_owned_outcome_refs"]}
    assert set(outcomes) == {
        "progress_delta",
        "ai_reviewer_gate_movement",
        "artifact_movement",
        "human_gate",
        "stop_loss",
        "stable_typed_blocker",
    }
    assert outcomes["progress_delta"]["owner_surface_role"] == "progress_delta_ref"
    assert outcomes["progress_delta"]["source_surfaces"] == [
        "artifacts/controller/repair_execution_receipts/latest.json",
        "artifacts/controller/repair_execution_evidence/latest.json",
    ]
    assert outcomes["ai_reviewer_gate_movement"]["owner_surface_role"] == "ai_reviewer_gate_ref"
    assert outcomes["ai_reviewer_gate_movement"]["source_surfaces"] == [
        "artifacts/publication_eval/latest.json",
        "review_ledger",
    ]
    assert outcomes["artifact_movement"]["owner_surface_role"] == "artifact_movement_ref"
    assert outcomes["artifact_movement"]["source_surfaces"] == [
        "artifacts/controller/gate_replay_requests/latest.json",
        "artifact_authority_receipt",
    ]
    assert outcomes["human_gate"]["owner_surface_role"] == "human_gate_ref"
    assert outcomes["stop_loss"]["owner_surface_role"] == "stop_loss_ref"
    assert outcomes["stable_typed_blocker"]["owner_surface_role"] == "stable_typed_blocker_ref"
    assert all(item["body_included"] is False for item in outcomes.values())
    assert all(item["write_permitted"] is False for item in outcomes.values())
    assert all(item["domain_owned"] is True for item in outcomes.values())
    assert all(item["opl_projection_only"] is True for item in outcomes.values())
    assert set(evidence["forbidden_body_surfaces"]) == {
        "publication_eval_body",
        "controller_decision_body",
        "artifact_gate_body",
        "memory_body",
        "final_verdict_body",
    }
    assert evidence["accepted_apply_results"] == [
        "artifact_delta",
        "gate_replay",
        "ai_reviewer_re_eval",
        "route_decision",
        "human_gate",
        "stop_loss",
        "stable_blocker",
    ]
    assert evidence["scaleout_status"] == "pending_real_paper_line_owner_receipts"
    canary = evidence["real_paper_line_provider_canary_contract"]
    assert canary == {
        "gate_id": "real_paper_line_provider_canary",
        "task_id": "agent-lab-task:mas/real-paper-line-provider-canary",
        "success_criterion": "mas_owner_chain_returns_owner_receipt_or_stable_typed_blocker",
        "provider_completion_is_success": False,
        "selected_opl_ingestable_ref_surface": (
            "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence"
        ),
        "required_closeout_surface": "mas_real_paper_line_provider_canary_closeout",
        "allowed_terminal_owner_results": [
            "owner_receipt",
            "stable_typed_blocker",
        ],
        "forbidden_authority": [
            "provider_completion_authorizes_domain_ready",
            "provider_or_opl_writes_publication_eval",
            "provider_or_opl_writes_controller_decisions",
            "provider_or_opl_writes_current_package",
            "provider_or_opl_writes_memory_or_artifact_body",
        ],
        "body_included": False,
    }

    lifecycle_requests = manifest["lifecycle_apply_requests"]
    lifecycle_proof = manifest["lifecycle_guarded_apply_proof"]
    assert lifecycle_requests == provider_contract["lifecycle_apply_requests"]
    assert lifecycle_proof == provider_contract["lifecycle_guarded_apply_proof"]
    assert {request["action_kind"] for request in lifecycle_requests} == {
        "cleanup",
        "restore",
        "retention",
    }
    assert any(
        request["owner_scope"] == "opl_owned_ledger"
        and request["domain_receipt_required"] is False
        for request in lifecycle_requests
    )
    assert all(
        request["domain_receipt_required"] is True
        for request in lifecycle_requests
        if request["owner_scope"] == "domain_owned_artifact"
    )
    assert lifecycle_proof["apply_status"] == "blocked_domain_receipt_required"
    assert lifecycle_proof["domain_receipt_required_count"] == 2
    assert lifecycle_proof["domain_receipt_refs"] == []
    assert lifecycle_proof["authority_boundary"]["opl_can_apply_owned_ledger_or_locator"] is True
    assert lifecycle_proof["authority_boundary"]["opl_writes_domain_artifact"] is False
    assert lifecycle_proof["authority_boundary"]["domain_artifact_mutation_requires_mas_receipt"] is True

    assert manifest["skill_catalog"]["skills"][0]["domain_projection"][
        "stage_skill_surface_projection"
    ] == manifest["stage_skill_surface_projection"]


def test_product_entry_manifest_consumes_opl_production_proof_for_provider_availability(
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    proof_ref = tmp_path / "opl-production-proof.json"
    _write_opl_production_proof(proof_ref)

    manifest = product_entry.build_product_entry_manifest(
        profile=profile,
        profile_ref=profile_ref,
        opl_production_proof_ref=proof_ref,
    )
    read_model = manifest["provider_guarded_soak_read_model"]
    availability = read_model["provider_availability"]

    assert manifest["opl_provider_ready_contract"]["provider_topology"]["provider_state"] == (
        "production_residency_proven"
    )
    assert availability["status"] == "available"
    assert availability["provider_attempt_available"] is True
    assert availability["proof_ref"] == str(proof_ref)
    assert availability["proof_receipt"]["receipt_status"] == "proven"
    assert availability["runtime_snapshot"]["worker_ready"] is True
    managed_state = manifest["managed_temporal_state_consistency"]
    assert managed_state == manifest["opl_provider_ready_contract"]["managed_temporal_state_consistency"]
    assert managed_state["status"] == "consistent"
    assert managed_state["managed_state"]["address_source"] == "managed_local_service_state"
    assert managed_state["managed_state"]["lifecycle_status"] == "ready"
    assert managed_state["managed_state"]["server_reachable"] is True
    assert managed_state["managed_state"]["worker_ready"] is True
    assert managed_state["opl_status_projection"] == {
        "provider": "temporal",
        "read_model_owner": "one-person-lab",
        "managed_service_state": "ready",
        "worker_state": "ready",
        "attempt_query_ready": True,
        "retry_dead_letter_state_visible": True,
    }
    assert managed_state["authority_boundary"]["can_write_domain_truth"] is False
    assert availability["semantics"]["provider_completion_is_paper_closure"] is False
    assert availability["semantics"]["paper_closure_requires_mas_owner_receipt"] is True
    assert read_model["provider_completion_semantics"]["paper_closure_requires_mas_owner_receipt"] is True
    assert read_model["no_forbidden_write_proof"]["result"] == "configured"
    assert all(
        item["status"] == "provider_available_guarded_apply_pending"
        for item in read_model["target_coverage"]
    )
    assert all(item["write_permitted"] is False for item in read_model["target_coverage"])
    assert all(
        item["paper_closure_requires_mas_owner_receipt"] is True
        for item in read_model["target_coverage"]
    )
    residency_read_model = manifest["provider_residency_read_model"]
    assert residency_read_model == manifest["opl_provider_ready_contract"]["provider_residency_read_model"]
    assert residency_read_model["status"] == "ready"
    assert all(item["status"] == "receipt_observed" for item in residency_read_model["checks"])
    assert residency_read_model["authority_boundary"]["can_write_domain_truth"] is False
    tombstone = manifest["legacy_retirement_tombstone_proof"]
    assert tombstone == manifest["opl_provider_ready_contract"]["legacy_retirement_tombstone_proof"]
    assert tombstone["surface_kind"] == "mas_legacy_retirement_tombstone_proof"
    assert tombstone["status"] == "no_active_default_caller_proven"
    assert tombstone["active_default_callers"] == []
    assert {item["classification"] for item in tombstone["retired_or_tombstoned_surfaces"]} == {
        "explicit_optional_executor_adapter",
        "retired_no_default_caller",
        "fixture_or_provenance_only",
        "standalone_diagnostics_only",
    }
    assert tombstone["physical_tombstone_refs"] == [
        "contracts/runtime/legacy-active-path-tombstones.json",
        "docs/history/runtime/legacy_active_path_tombstones.md",
    ]
    assert tombstone["replacement_parity_refs"] == [
        "/opl_provider_ready_contract/provider_topology",
        "/opl_provider_ready_contract/managed_temporal_state_consistency",
        "/opl_provider_ready_contract/runtime_transport_handoff_projection",
        "/product_entry_manifest/functional_consumer_boundary",
        "contracts/runtime/legacy-active-path-tombstones.json",
    ]
    assert tombstone["no_regression_evidence_refs"] == [
        "tests/product_entry_cases/action_catalog_parity_cases/provider_cases.py::test_product_entry_manifest_exposes_provider_guarded_soak_read_model_with_typed_blockers",
        "tests/test_cli_cases/sidecar_family_adapter_command_cases/export_cases.py::test_sidecar_family_export_exposes_managed_temporal_state_consistency",
    ]
    assert tombstone["tombstone_refs"] == tombstone["physical_tombstone_refs"]
    assert tombstone["history_refs"] == [
        "docs/active/opl_temporal_mas_runtime_retirement_program.md",
        "docs/decisions.md#2026-05-16默认-domain-slo-scheduler-projection-owner-迁到-opl-replacement",
    ]
    assert "legacy_active_path_tombstones_landed" in tombstone["removal_policy"]["history_actions"]
    assert tombstone["authority_boundary"]["can_authorize_submission_readiness"] is False

    generated_default = manifest["functional_consumer_boundary"]["generated_default_caller_boundary"]
    assert tombstone["generated_default_caller_boundary"] == generated_default
    assert tombstone["physical_retirement_gate_matrix"] == manifest["functional_consumer_boundary"][
        "physical_retirement_gate_matrix"
    ]
    assert tombstone["removal_policy"]["delete_or_tombstone_when"] == [
        "generated_default_caller_boundary_proven",
        "active_caller_count=0",
        "opl_replacement_parity",
        "mas_owner_receipt_parity",
        "focused_tests_green",
        "tombstone_refs_landed",
    ]
    assert tombstone["removal_policy"]["current_action"] == (
        "retain_domain_receipt_adapter_refs_only_adapter_diagnostic_or_tombstone_until_gate_closes"
    )


def test_product_entry_manifest_exposes_provider_residency_typed_blocker(
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    provider_contract = manifest["opl_provider_ready_contract"]
    read_model = manifest["provider_residency_read_model"]

    assert read_model == provider_contract["provider_residency_read_model"]
    assert read_model["surface_kind"] == "provider_runtime_residency_read_model"
    assert read_model["version"] == "provider-runtime-residency-read-model.v1"
    assert read_model["status"] == "typed_blocker"
    assert read_model["provider_owner"] == "one-person-lab"
    assert read_model["domain_owner"] == "med-autoscience"
    assert read_model["provider_available"] is False
    assert read_model["required_evidence"] == [
        "temporal_production_residency",
        "worker_restart_requery",
        "retry_dead_letter",
        "long_soak_receipt",
    ]
    assert {item["check_id"] for item in read_model["checks"]} == set(read_model["required_evidence"])
    assert all(item["status"] == "typed_blocker" for item in read_model["checks"])
    assert all(item["body_included"] is False for item in read_model["checks"])
    assert all(item["write_permitted"] is False for item in read_model["checks"])
    assert read_model["typed_blocker"]["blocker_id"] == "production_provider_residency_evidence_missing"
    assert read_model["typed_blocker"]["missing_evidence"] == read_model["required_evidence"]
    assert read_model["consumer_contract"]["mas_owned_provider_kernel"] is False
    assert read_model["consumer_contract"]["provider_completion_is_paper_closure"] is False
    assert read_model["consumer_contract"]["queue_completion_is_paper_closure"] is False
    assert read_model["consumer_contract"]["paper_progress_requires_mas_owner_receipt"] is True
    assert read_model["authority_boundary"]["can_write_domain_truth"] is False
    assert read_model["authority_boundary"]["can_write_current_package"] is False
    assert read_model["authority_boundary"]["can_authorize_publication_quality"] is False
    assert read_model["authority_boundary"]["can_write_memory_body"] is False


def test_provider_residency_read_model_requires_all_opl_receipts() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.opl_provider_ready_adapter")

    payload = adapter.build_provider_residency_read_model(
        provider_available=True,
        receipt_refs={
            "temporal_production_residency": "opl://provider/temporal-residency.json",
            "worker_restart_requery": "opl://provider/worker-restart.json",
            "retry_dead_letter": "opl://provider/retry-dead-letter.json",
            "long_soak_receipt": "opl://provider/long-soak.json",
        },
    )

    assert payload["status"] == "ready"
    assert payload["typed_blocker"] is None
    assert all(item["status"] == "receipt_observed" for item in payload["checks"])
    assert all(item["body_included"] is False for item in payload["checks"])
    assert payload["consumer_contract"]["mas_consumes"] == [
        "sidecar_task",
        "typed_receipt",
        "receipt_refs",
    ]
    assert payload["authority_boundary"]["can_write_domain_truth"] is False
    assert payload["authority_boundary"]["can_authorize_publication_quality"] is False

    missing = adapter.build_provider_residency_read_model(
        provider_available=True,
        receipt_refs={
            "temporal_production_residency": "opl://provider/temporal-residency.json",
        },
    )
    assert missing["status"] == "typed_blocker"
    assert missing["typed_blocker"]["missing_evidence"] == [
        "worker_restart_requery",
        "retry_dead_letter",
        "long_soak_receipt",
    ]


def test_product_entry_manifest_omits_retired_legacy_residue_audit_surface(
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    assert "legacy_residue_audit" not in manifest

    tombstone = manifest["legacy_retirement_tombstone_proof"]
    assert tombstone["status"] == "no_active_default_caller_proven"
    assert tombstone["active_default_callers"] == []
    assert tombstone["tombstone_refs"] == [
        "contracts/runtime/legacy-active-path-tombstones.json",
        "docs/history/runtime/legacy_active_path_tombstones.md",
    ]

    boundary = manifest["functional_consumer_boundary"]
    tombstones = boundary["retired_legacy_residue_tombstones"]
    assert {item["residue_id"] for item in tombstones} == {
        "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases",
        "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_without_active_caller",
    }
    assert all(item["active_caller_count"] == 0 for item in tombstones)
    assert all(item["current_role"] == "history_tombstone_provenance_only" for item in tombstones)
