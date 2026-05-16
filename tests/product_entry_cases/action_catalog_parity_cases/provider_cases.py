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
    assert tombstone["removal_policy"]["current_action"] == "legacy_active_path_tombstones_landed"
    assert tombstone["authority_boundary"]["can_authorize_submission_readiness"] is False
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


def test_product_entry_manifest_exposes_legacy_residue_audit_without_default_callers(
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    audit = manifest["legacy_residue_audit"]

    assert audit["surface_kind"] == "mas_legacy_residue_audit"
    assert audit["status"] == "default_callers_retired_with_references_retained"
    assert audit["scan_policy"] == {
        "docs_are_not_machine_truth": True,
        "stale_term_scan_is_review_input_only": True,
        "delete_only_when_replacement_proof_and_no_default_caller": True,
    }
    assert audit["summary"]["default_caller_count"] == 0
    assert audit["summary"]["cleanup_pending_count"] == 0
    assert audit["summary"]["tombstoned_count"] == 1
    assert audit["summary"]["retired_no_default_caller_count"] == 1
    assert "provider_runtime_residency_read_model" in audit["replacement_surfaces"]
    by_id = {item["residue_id"]: item for item in audit["findings"]}
    assert by_id["hermes_agent_executor_adapter"]["default_caller"] is False
    assert by_id["hermes_agent_executor_adapter"]["disposition"] == "retain_reference"
    assert by_id["hermes_gateway_cron_scheduler"]["disposition"] == "retired_no_default_caller"
    assert by_id["med_deepscientist_backend_reference"]["current_role"] == (
        "historical_fixture_provenance_parity_oracle"
    )
    assert by_id["hosted_runtime_binding_wording"]["disposition"] == "tombstoned"
    assert by_id["hosted_runtime_binding_wording"]["delete_allowed"] is False
    assert "contracts/runtime/legacy-active-path-tombstones.json" in by_id[
        "hosted_runtime_binding_wording"
    ]["replacement_proof_refs"]
    assert all(item["body_included"] is False for item in audit["findings"])
    assert audit["authority_boundary"]["audit_can_delete_code"] is False
    assert audit["authority_boundary"]["audit_can_change_runtime_defaults"] is False


