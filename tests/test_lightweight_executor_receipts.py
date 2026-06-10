from __future__ import annotations

import importlib


def test_lightweight_executor_receipt_defaults_to_nonblocking_l0_l1_contract() -> None:
    module = importlib.import_module("med_autoscience.lightweight_executor_receipts")

    receipt = module.build_lightweight_executor_receipt(
        executor_backend="codex_cli",
        command_ref="artifacts/supervision/requests/current.json#command",
        work_unit={
            "owner": "MedAutoScience",
            "action_type": "complete_medical_paper_readiness_surface",
            "work_unit_id": "readiness-surface",
            "work_unit_fingerprint": "fingerprint-001",
        },
        execution={
            "exit_code": 0,
            "stdout_ref": "artifacts/executor/stdout.txt",
            "stderr_ref": "artifacts/executor/stderr.txt",
            "artifact_refs": ["artifacts/medical_paper/readiness.json"],
            "changed_file_refs": ["artifacts/medical_paper/readiness.json"],
            "duration_ms": 1234,
        },
    )

    assert receipt["surface_kind"] == "mas_lightweight_executor_receipt"
    assert receipt["schema_version"] == 1
    assert receipt["status"] == "executor_receipt_recorded"
    assert receipt["execution_model"] == "receipt_only_no_command_execution"
    assert receipt["executor_backend"] == "codex_cli"
    assert receipt["isolation"]["level"] == "L1_process_workspace"
    assert receipt["isolation"]["default_levels"] == [
        "L0_host_clean_runner",
        "L1_process_workspace",
    ]
    assert receipt["isolation"]["docker_sandbox_available"] is False
    assert receipt["isolation"]["docker_in_docker_allowed"] is False
    assert receipt["isolation"]["openhands_runtime_default"] is False
    assert receipt["can_block_current_owner_action"] is False
    assert receipt["mainline_waits_for_executor_receipt"] is False
    assert receipt["allowed_writes"] == ["artifacts/executor_receipts/**/*.json"]
    assert "artifacts/publication_eval/latest.json" in receipt["forbidden_writes"]
    assert receipt["authority_boundary"]["can_write_domain_truth"] is False
    assert receipt["authority_boundary"]["can_write_owner_receipt"] is False
    assert receipt["authority_boundary"]["can_write_typed_blocker"] is False
    assert receipt["authority_boundary"]["can_authorize_publication_quality"] is False
    assert receipt["authority_boundary"]["can_close_stage"] is False
    assert receipt["work_unit"]["work_unit_fingerprint"] == "fingerprint-001"
    assert receipt["execution"]["exit_code"] == 0
    assert receipt["execution"]["artifact_refs"] == ["artifacts/medical_paper/readiness.json"]


def test_lightweight_executor_receipt_rejects_default_docker_and_flags_container_context() -> None:
    module = importlib.import_module("med_autoscience.lightweight_executor_receipts")

    receipt = module.build_lightweight_executor_receipt(
        executor_backend="openhands",
        command_ref="executor:proof-lane",
        requested_isolation_level="L3_containerized_sandbox",
        host_context={"inside_container": True, "docker_socket_mounted": True},
        explicit_sandbox_request=False,
    )

    assert receipt["status"] == "sandbox_not_authorized"
    assert receipt["isolation"]["level"] == "L1_process_workspace"
    assert receipt["isolation"]["requested_level"] == "L3_containerized_sandbox"
    assert receipt["isolation"]["inside_container"] is True
    assert receipt["isolation"]["docker_sandbox_available"] is False
    assert receipt["isolation"]["docker_in_docker_allowed"] is False
    assert receipt["isolation"]["docker_socket_mount_allowed"] is False
    assert receipt["diagnostics"] == [
        "containerized sandbox requires explicit proof-lane authorization",
        "inside-container context disables default Docker sandbox",
        "Docker socket mount is not accepted as implicit sandbox authorization",
    ]
    assert receipt["execution_model"] == "receipt_only_no_command_execution"
    assert receipt["can_block_current_owner_action"] is False


def test_lightweight_executor_receipt_allows_explicit_l3_proof_lane_without_authority() -> None:
    module = importlib.import_module("med_autoscience.lightweight_executor_receipts")

    receipt = module.build_lightweight_executor_receipt(
        executor_backend="openhands",
        command_ref="executor:proof-lane",
        requested_isolation_level="L3_containerized_sandbox",
        host_context={"inside_container": False},
        explicit_sandbox_request=True,
        execution={
            "exit_code": 1,
            "failure_class": "dependency_resolution_failed",
            "stdout_ref": "artifacts/executor/stdout.txt",
            "stderr_ref": "artifacts/executor/stderr.txt",
        },
    )

    assert receipt["status"] == "executor_receipt_recorded"
    assert receipt["isolation"]["level"] == "L3_containerized_sandbox"
    assert receipt["isolation"]["explicit_sandbox_request"] is True
    assert receipt["isolation"]["docker_sandbox_available"] is True
    assert receipt["isolation"]["docker_in_docker_allowed"] is False
    assert receipt["authority_boundary"]["can_write_publication_eval"] is False
    assert receipt["authority_boundary"]["can_authorize_owner_action"] is False
    assert receipt["authority_boundary"]["can_authorize_artifact_authority"] is False
    assert receipt["readiness_authorization"]["may_authorize_publication_readiness"] is False
    assert receipt["execution"]["failure_class"] == "dependency_resolution_failed"


def test_external_learning_closure_exposes_lightweight_executor_receipt_contract() -> None:
    closure_module = importlib.import_module("med_autoscience.external_learning_adoption_closure")

    closure = closure_module.build_external_learning_adoption_closure()
    receipt_contract = closure["lightweight_executor_receipt_contract"]

    assert receipt_contract["surface_kind"] == "mas_lightweight_executor_receipt_contract"
    assert receipt_contract["default_isolation_levels"] == [
        "L0_host_clean_runner",
        "L1_process_workspace",
    ]
    assert receipt_contract["containerized_sandbox_default"] is False
    assert receipt_contract["docker_in_docker_default"] is False
    assert receipt_contract["openhands_runtime_default"] is False
    assert receipt_contract["explicit_l3_proof_lane_only"] is True
    assert receipt_contract["mainline_waits_for_executor_receipt"] is False
    assert receipt_contract["receipt_counts_as_owner_receipt"] is False
    assert {
        "exit_code",
        "stdout_ref",
        "stderr_ref",
        "artifact_refs",
        "changed_file_refs",
        "duration_ms",
        "env_fingerprint",
    } <= set(receipt_contract["execution_ref_fields"])
    assert {
        "publication_eval",
        "controller_decisions",
        "owner_receipt",
        "typed_blocker",
        "quality_verdict",
        "stage_closeout",
    } <= set(receipt_contract["forbidden_authority"])


def test_action_catalog_exposes_lightweight_executor_receipt_as_read_only_contract() -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")

    catalog = action_catalog.build_mas_action_catalog()
    actions = {item["action_id"]: item for item in catalog["actions"]}
    action = actions["lightweight_executor_receipt"]

    assert action["effect"] == "read_only"
    assert action["source_command"]["surface_kind"] == "mas_lightweight_executor_receipt_contract"
    assert action["authority_boundary"]["surface_authority"] == (
        "executor_receipt_contract_read_model"
    )
    assert action["authority_boundary"]["can_execute_command"] is False
    assert action["authority_boundary"]["can_start_docker"] is False
    assert action["authority_boundary"]["can_mount_docker_socket"] is False
    assert action["authority_boundary"]["can_write_owner_receipt"] is False
    assert action["authority_boundary"]["can_write_typed_blocker"] is False
    assert action["authority_boundary"]["can_block_current_owner_action"] is False
