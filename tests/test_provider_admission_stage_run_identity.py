from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_stage_run_identity import (
    candidate_with_stage_run_admission_identity,
)


def test_default_executor_execution_dispatch_ref_opt_in_recovers_stage_packet_identity_only() -> None:
    study_root = Path("/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap")
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )

    candidate = candidate_with_stage_run_admission_identity(
        {
            "source": "default_executor_execution",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "work_unit_fingerprint": "sha256:current",
            "source_refs": {
                "stage_packet_ref": "preserved-stage-packet",
                "stage_packet_refs": ["preserved-stage-packet"],
            },
        },
        execution={
            "source": "default_executor_execution",
            "surface": "default_executor_dispatch_execution",
            "dispatch_path": str(dispatch_path),
            "owner_route_current": True,
        },
        study_root=study_root,
        allow_dispatch_ref_stage_packet_authority=True,
    )

    expected_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_dispatches/run_gate_clearing_batch.json"
    )
    assert candidate["dispatch_ref"] == expected_ref
    assert candidate["stage_packet_ref"] == expected_ref
    assert candidate["stage_packet_refs"] == [expected_ref]
    assert candidate["source_refs"]["stage_packet_ref"] == "preserved-stage-packet"
    assert candidate["source_refs"]["stage_packet_refs"] == ["preserved-stage-packet"]
    assert candidate.get("provider_admission_authority") is not True
    assert candidate.get("execution_authority") is not True
    assert candidate.get("attempt_lifecycle_authority") is not True


def test_dispatch_ref_stage_packet_authority_requires_explicit_opt_in() -> None:
    candidate = candidate_with_stage_run_admission_identity(
        {
            "source": "default_executor_execution",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "work_unit_fingerprint": "sha256:current",
        },
        execution={
            "source": "default_executor_execution",
            "surface": "default_executor_dispatch_execution",
            "dispatch_path": "/workspace/studies/003/default_executor_dispatches/run.json",
            "owner_route_current": True,
        },
    )

    assert "stage_packet_ref" not in candidate
    assert "stage_packet_refs" not in candidate


def test_dispatch_ref_stage_packet_authority_rejects_stale_owner_route() -> None:
    candidate = candidate_with_stage_run_admission_identity(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "work_unit_fingerprint": "sha256:current",
        },
        execution={
            "source": "default_executor_execution",
            "surface": "default_executor_dispatch_execution",
            "dispatch_path": "/workspace/studies/003/default_executor_dispatches/run.json",
            "owner_route_current": False,
        },
    )

    assert "stage_packet_ref" not in candidate
    assert "stage_packet_refs" not in candidate


def test_generic_dispatch_ref_does_not_replace_stage_packet_ref() -> None:
    candidate = candidate_with_stage_run_admission_identity(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "work_unit_fingerprint": "sha256:current",
        },
        execution={
            "surface": "queue_projection",
            "dispatch_path": "/workspace/studies/003/default_executor_dispatches/run.json",
            "owner_route_current": True,
        },
    )

    assert "stage_packet_ref" not in candidate
    assert "stage_packet_refs" not in candidate
