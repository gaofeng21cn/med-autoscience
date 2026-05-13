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
                    },
                    "checks": checks,
                },
            }
        },
    )


def test_sidecar_export_exposes_functional_closeout_contracts(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    proof_ref = tmp_path / "opl-production-proof.json"
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
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    owner_contract = payload["owner_receipt_contract"]
    assert owner_contract == payload["domain_owner_receipt_contract"]
    assert owner_contract["surface_kind"] == "domain_owner_receipt_contract"
    assert owner_contract["provider_availability"]["status"] == "available"
    assert owner_contract["typed_blocker"] is None
    assert owner_contract["receipt_ref_policy"]["opl_persists"] == "receipt_refs_only"
    assert owner_contract["authority_boundary"]["can_write_domain_truth"] is False
    assert owner_contract["authority_boundary"]["can_write_artifact_gate"] is False
    assert owner_contract["authority_boundary"]["can_write_memory_body"] is False

    lifecycle_requests = payload["lifecycle_apply_requests"]
    lifecycle_proof = payload["lifecycle_guarded_apply_proof"]
    assert {request["action_kind"] for request in lifecycle_requests} == {
        "cleanup",
        "restore",
        "retention",
    }
    assert lifecycle_proof["apply_status"] == "blocked_domain_receipt_required"
    assert lifecycle_proof["domain_receipt_required_count"] == 2
    assert lifecycle_proof["authority_boundary"]["opl_writes_domain_artifact"] is False
    assert lifecycle_proof["authority_boundary"]["domain_artifact_mutation_requires_mas_receipt"] is True
