from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_opl_production_proof(path: Path) -> None:
    checks = {
        "external_temporal_server_reachable": True,
        "managed_worker_ready": True,
        "worker_completed_attempt": True,
        "worker_restart_requery": True,
        "signal_history_preserved": True,
        "typed_closeout_required_for_completed": True,
        "missing_closeout_blocks_completion": True,
        "retry_or_dead_letter_boundary_observed": True,
        "domain_truth_boundary_preserved": True,
    }
    _write_json(
        path,
        {
            "family_runtime_residency_proof": {
                "surface_kind": "opl_temporal_production_residency_proof",
                "provider_kind": "temporal",
                "closeout_status": "production_residency_proven",
                "production_residency_proof": {
                    "surface_kind": "opl_temporal_external_production_residency_proof",
                    "provider_kind": "temporal",
                    "closeout_status": "production_residency_proven",
                    "runtime_snapshot": {
                        "address_source": "managed_local_service_state",
                        "lifecycle_status": "ready",
                        "server_reachable": True,
                        "worker_ready": True,
                        "task_queue": "opl-stage-attempts",
                    },
                    "proof_receipt": {
                        "receipt_kind": "temporal_production_residency_proof",
                        "receipt_status": "proven",
                        "completed_workflow_id": "wf-complete",
                        "blocked_workflow_id": "wf-blocked",
                    },
                    "checks": checks,
                },
            }
        },
    )


def test_domain_handler_export_guarded_apply_fingerprint_tracks_mas_owner_decision(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    proof_ref = tmp_path / "opl-production-proof.json"
    decision_path = (
        workspace_root / "studies" / "002-early-residual-risk" / "artifacts" / "controller_decisions" / "latest.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
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
    first_payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    first_tasks = [
        task for task in first_payload["pending_family_tasks"]
        if task["task_kind"] == "paper_autonomy/guarded-apply"
    ]
    assert [task["payload"]["study_id"] for task in first_tasks] == ["DM002", "DM003", "Obesity"]
    first_fingerprints = {task["payload"]["study_id"]: task["source_fingerprint"] for task in first_tasks}
    for task in first_tasks:
        study_id = task["payload"]["study_id"]
        owner_delta_contract = task["payload"]["current_owner_delta_contract"]
        assert owner_delta_contract["default_planning_root"] == "current_owner_delta"
        assert owner_delta_contract["stage_id"] == "paper_autonomy/guarded-apply"
        assert owner_delta_contract["current_owner"] == "med-autoscience"
        assert owner_delta_contract["desired_delta"] == (
            "domain_owner_receipt_quality_gate_or_typed_blocker_required"
        )
        assert owner_delta_contract["accepted_answer_shape"] == [
            "domain_owner_receipt_ref",
            "quality_gate_receipt_ref",
            "typed_blocker_ref",
            "human_gate_ref",
            "route_back_evidence_ref",
        ]
        assert owner_delta_contract["owner_answer_missing"] is True
        assert owner_delta_contract["owner_answer_still_required"] is True
        assert owner_delta_contract["domain_ready_authorized"] is False
        owner_ref = [
            ref for ref in task["source_refs"]
            if ref["role"] == "mas_owner_controller_decision"
        ][0]
        owner_delta_ref = [
            ref for ref in task["source_refs"]
            if ref["role"] == "opl_current_owner_delta_contract"
        ][0]
        contract_ref = [
            ref for ref in task["source_refs"]
            if ref["role"] == "mas_guarded_apply_owner_receipt_contract"
        ][0]
        assert contract_ref == {
            "role": "mas_guarded_apply_owner_receipt_contract",
            "ref": "mas-guarded-apply-owner-receipt.v2",
            "exists": True,
        }
        assert owner_delta_ref == {
            "role": "opl_current_owner_delta_contract",
            "ref": "paper_autonomy/guarded-apply",
            "exists": True,
            "accepted_answer_shapes": [
                "domain_owner_receipt_ref",
                "quality_gate_receipt_ref",
                "typed_blocker_ref",
                "human_gate_ref",
                "route_back_evidence_ref",
            ],
            "desired_delta": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
            "body_included": False,
        }
        assert owner_ref == {
            "role": "mas_owner_controller_decision",
            "ref": f"studies/{study_id}/artifacts/controller_decisions/latest.json",
            "exists": False,
        }

    _write_json(
        decision_path,
        {
            "surface": "controller_decision",
            "decision_type": "medical_paper_readiness_owner_blocker",
            "route_decision": "stable_blocker",
            "runtime_decision": "blocked",
            "blocked_reason": "medical_paper_readiness_missing",
            "quality_claim_authorized": False,
            "submission_authorized": False,
        },
    )
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
    repeat_by_study = {task["payload"]["study_id"]: task for task in repeat_tasks}
    repeat_owner_ref = [
        ref for ref in repeat_by_study["DM002"]["source_refs"]
        if ref["role"] == "mas_owner_controller_decision"
    ][0]
    assert repeat_owner_ref["ref"] == "studies/002-early-residual-risk/artifacts/controller_decisions/latest.json"
    assert repeat_owner_ref["exists"] is True
    assert repeat_owner_ref["content_sha256"]
    assert repeat_by_study["DM002"]["source_fingerprint"] != first_fingerprints["DM002"]
    assert repeat_by_study["DM003"]["source_fingerprint"] == first_fingerprints["DM003"]
    assert repeat_by_study["Obesity"]["source_fingerprint"] == first_fingerprints["Obesity"]


def test_domain_handler_export_guarded_apply_targets_live_canonical_studies_when_present(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    proof_ref = tmp_path / "opl-production-proof.json"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_opl_production_proof(proof_ref)
    _write_json(
        workspace_root / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap" / "study.yaml",
        {"study_id": "003-dpcc-primary-care-phenotype-treatment-gap"},
    )

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

    assert exit_code == 0
    guarded_apply_tasks = [
        task for task in payload["pending_family_tasks"]
        if task["task_kind"] == "paper_autonomy/guarded-apply"
    ]
    assert [task["payload"]["study_id"] for task in guarded_apply_tasks] == [
        "003-dpcc-primary-care-phenotype-treatment-gap"
    ]
    assert guarded_apply_tasks[0]["source_refs"][-1]["ref"] == (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller_decisions/latest.json"
    )
    evidence_payload = guarded_apply_tasks[0]["domain_dispatch_evidence_record_payload"]
    assert evidence_payload["study_id"] == "003-dpcc-primary-care-phenotype-treatment-gap"
    assert evidence_payload["identity_binding"]["payload_identity"]["study_id"] == (
        "003-dpcc-primary-care-phenotype-treatment-gap"
    )
