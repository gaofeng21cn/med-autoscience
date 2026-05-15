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


def test_sidecar_export_guarded_apply_fingerprint_tracks_mas_owner_decision(
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
    first_payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    first_task = [
        task for task in first_payload["pending_family_tasks"]
        if task["task_kind"] == "paper_autonomy/guarded-apply"
    ][0]
    first_fingerprint = first_task["source_fingerprint"]
    first_owner_ref = [
        ref for ref in first_task["source_refs"]
        if ref["role"] == "mas_owner_controller_decision"
    ][0]
    contract_ref = [
        ref for ref in first_task["source_refs"]
        if ref["role"] == "mas_guarded_apply_owner_receipt_contract"
    ][0]
    assert contract_ref == {
        "role": "mas_guarded_apply_owner_receipt_contract",
        "ref": "mas-guarded-apply-owner-receipt.v2",
        "exists": True,
    }
    assert first_owner_ref == {
        "role": "mas_owner_controller_decision",
        "ref": "studies/DM002/artifacts/controller_decisions/latest.json",
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
    repeat_task = [
        task for task in repeat_payload["pending_family_tasks"]
        if task["task_kind"] == "paper_autonomy/guarded-apply"
    ][0]
    repeat_owner_ref = [
        ref for ref in repeat_task["source_refs"]
        if ref["role"] == "mas_owner_controller_decision"
    ][0]
    assert repeat_owner_ref["ref"] == "studies/002-early-residual-risk/artifacts/controller_decisions/latest.json"
    assert repeat_owner_ref["exists"] is True
    assert repeat_owner_ref["content_sha256"]
    assert repeat_task["source_fingerprint"] != first_fingerprint
