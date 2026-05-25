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


def test_domain_handler_dispatch_records_provider_hosted_guarded_apply_receipt_without_forbidden_writes(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(study_root / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": study_root.name})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )
    _write_json(
        study_root / "artifacts" / "stage_knowledge" / "paper_soak_memory_apply_proof" / "latest.json",
        {
            "surface": "paper_soak_memory_apply_proof",
            "status": "ready",
            "stage_entry": {
                "publication_route_memory_refs": [
                    {"memory_id": "publication_route_memory_seed__negative_result_stoploss"}
                ]
            },
            "mas_router_receipt_refs": [{"ref": "receipt:memory-router"}],
            "workspace_writeback_receipt_refs": [{"ref": "receipt:writeback"}],
            "opl_aion_readonly_receipt_refs": [{"ref": "receipt:aion", "body_included": False}],
        },
    )
    before = {path: path.stat().st_mtime_ns for path in study_root.rglob("*.json")}
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "guarded-apply-dm002",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/guarded-apply",
            "payload": {
                "profile": str(profile_path),
                "study_id": "DM002",
                "provider_attempt_id": "opl-attempt-dm002-001",
                "idempotency_key": "opl-attempt-dm002-001:guarded-apply",
            },
        },
    )

    exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["dispatch"]["action_type"] == "paper_autonomy_guarded_apply"
    assert payload["dispatch"]["execution_policy"] == "mas_owner_provider_hosted_guarded_apply"
    result = payload["dispatch"]["result"]
    assert result["surface"] == "real_paper_autonomy_provider_hosted_guarded_apply_receipt"
    assert result["provider_attempt"]["attempt_id"] == "opl-attempt-dm002-001"
    assert result["status"] == "typed_blocker"
    assert result["typed_blockers"][0]["blocker_id"].startswith("mas_owner_apply_receipt_missing:")
    canary = result["paper_line_provider_canary_closeout"]
    assert canary["surface_kind"] == "mas_real_paper_line_provider_canary_closeout"
    assert canary["gate_id"] == "real_paper_line_provider_canary"
    assert canary["success_criterion"] == "mas_owner_chain_returns_owner_receipt_or_stable_typed_blocker"
    assert canary["provider_completion_is_success"] is False
    assert canary["required_return_shape_satisfied"] is True
    assert canary["owner_chain_result"]["result_kind"] == "stable_typed_blocker"
    assert canary["owner_chain_result"]["owner_receipt_refs"] == []
    assert canary["owner_chain_result"]["stable_typed_blocker_refs"][0].startswith(
        "mas_owner_apply_receipt_missing:"
    )
    assert [item["paper_line_id"] for item in canary["paper_line_owner_chain_results"]] == [
        "002-dm-china-us-mortality-attribution"
    ]
    assert canary["paper_line_owner_chain_results"][0]["result_kind"] == "stable_typed_blocker"
    assert canary["paper_line_owner_chain_results"][0]["required_return_shape_satisfied"] is True
    assert canary["paper_line_owner_chain_results"][0]["stable_typed_blocker_refs"][0].startswith(
        "mas_owner_apply_receipt_missing:"
    )
    assert canary["paper_line_owner_chain_results"][0]["body_included"] is False
    assert canary["selected_opl_ingestable_ref_surface"]["ref"] == (
        "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence"
    )
    canary_packets = canary["body_free_evidence_packets"]
    assert {packet["role"] for packet in canary_packets} == {
        "stable_typed_blocker_ref",
        "no_forbidden_write_proof_ref",
    }
    for packet in canary_packets:
        assert set(packet) == {
            "ref",
            "role",
            "freshness",
            "owner",
            "receipt_id",
            "no_forbidden_write_proof",
        }
        assert packet["owner"] == "MedAutoScience"
        assert packet["no_forbidden_write_proof"]["write_permitted"] is False
        assert packet["no_forbidden_write_proof"]["forbidden_writes_performed"] is False
        assert "artifact_body" not in packet
        assert "memory_body" not in packet
        assert "current_package" not in packet
    assert canary["no_forbidden_write_proof"]["provider_or_opl_wrote_domain_truth"] is False
    assert canary["no_forbidden_write_proof"]["provider_or_opl_wrote_current_package"] is False
    assert result["publication_route_memory_final_proof"]["status"] == "final_ref_chain_proven"
    assert result["publication_route_memory_final_proof"]["consumed_refs"] == [
        "publication_route_memory_seed__negative_result_stoploss"
    ]
    assert result["publication_route_memory_final_proof"]["writeback_receipt_refs"] == [
        "receipt:memory-router",
        "receipt:writeback",
        "receipt:aion",
    ]
    assert result["forbidden_write_guard"]["aggregate_result"] == "fail_closed_no_forbidden_writes"
    assert result["authority_boundary"]["opl_can_write_mas_truth"] is False
    assert result["authority_boundary"]["opl_can_write_memory_body"] is False
    assert payload["forbidden_write_guard_proof"]["result"] == "accepted_no_forbidden_writes"
    receipt_ref = workspace_root / payload["receipt_ref"]
    assert receipt_ref.is_file()
    persisted = json.loads(receipt_ref.read_text(encoding="utf-8"))
    assert persisted["dispatch"]["result"]["surface"] == "real_paper_autonomy_provider_hosted_guarded_apply_receipt"
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "paper" / "current_package").exists()
    assert not (study_root / "manuscript" / "current_package").exists()
    assert {path: path.stat().st_mtime_ns for path in before} == before


def test_domain_handler_dispatch_guarded_apply_rejects_review_ledger_or_memory_body_write(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "guarded-apply-forbidden",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/guarded-apply",
            "payload": {
                "profile": "/tmp/profile.toml",
                "study_id": "DM002",
                "requested_writes": [
                    "review_ledger_write",
                    "memory_body_write",
                    "current_package_write",
                    "publication_eval_write",
                    "controller_decisions_write",
                ],
            },
        },
    )

    exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["accepted"] is False
    assert payload["reason"] == "domain_truth_or_artifact_gate_write_forbidden"
    assert payload["forbidden_requested_writes"] == [
        "review_ledger_write",
        "memory_body_write",
        "current_package_write",
        "publication_eval_write",
        "controller_decisions_write",
    ]



def test_domain_handler_dispatch_guarded_apply_records_mas_owner_receipt_present(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(study_root / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": study_root.name})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json",
        {
            "surface": "paper_repair_owner_receipt",
            "accepted": True,
            "execution_status": "executed",
            "canonical_artifact_delta_refs": [{"path": str(study_root / "paper" / "manuscript.md")}],
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
            "progress_delta_candidate": True,
        },
    )
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "guarded-apply-dm002-present",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/guarded-apply",
            "payload": {
                "profile": str(profile_path),
                "study_id": "DM002",
                "provider_attempt_id": "opl-attempt-dm002-present",
                "idempotency_key": "opl-attempt-dm002-present:guarded-apply",
            },
        },
    )

    exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    result = payload["dispatch"]["result"]
    assert result["status"] == "applied"
    assert result["provider_attempt"]["attempt_state"] == "mas_owner_receipt_present"
    assert result["paper_line_provider_canary_closeout"]["required_return_shape_satisfied"] is True
    assert result["paper_line_provider_canary_closeout"]["owner_chain_result"]["result_kind"] == "owner_receipt"
    assert result["paper_line_provider_canary_closeout"]["paper_line_owner_chain_results"][0][
        "result_kind"
    ] == "owner_receipt"
    assert result["paper_line_provider_canary_closeout"]["paper_line_owner_chain_results"][0][
        "paper_line_id"
    ] == "002-dm-china-us-mortality-attribution"
    assert result["paper_line_provider_canary_closeout"]["provider_attempt"]["provider_attempt_wrote_mas_truth"] is False
    assert result["summary"]["provider_attempt_wrote_workspace"] is False
    assert result["summary"]["writes_performed_by_this_receipt"] is False
    assert result["guarded_apply_receipts"][0]["workspace_mutation"]["mutation_owner"] == "med-autoscience"
    assert result["guarded_apply_receipts"][0]["workspace_mutation"]["provider_attempt_wrote_workspace"] is False


def test_domain_handler_dispatch_guarded_apply_records_provider_unavailable_typed_blocker(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "guarded-apply-provider-unavailable",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/guarded-apply",
            "payload": {
                "profile": str(profile_path),
                "study_id": "DM002",
                "provider_attempt_id": "opl-attempt-unavailable",
                "idempotency_key": "opl-attempt-unavailable:guarded-apply",
                "provider_ready": False,
                "provider_unavailable_reason": "opl_provider_ready_contract_missing",
            },
        },
    )

    exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    result = payload["dispatch"]["result"]
    assert result["status"] == "typed_blocker"
    assert result["provider_attempt"]["attempt_state"] == "provider_unavailable"
    assert result["provider_attempt"]["attempt_ready"] is False
    assert result["paper_line_provider_canary_closeout"]["required_return_shape_satisfied"] is False
    assert result["paper_line_provider_canary_closeout"]["owner_chain_result"]["result_kind"] == (
        "provider_typed_blocker"
    )
    assert result["paper_line_provider_canary_closeout"]["provider_attempt"]["provider_completion_is_success"] is False
    assert result["typed_blockers"][0]["blocker_id"].startswith("provider_guarded_apply_unavailable:")
    assert result["summary"]["writes_performed"] is False


def test_domain_handler_dispatch_keys_guarded_apply_receipts_by_task_source_fingerprint(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)

    def fake_guarded_apply(**_: object) -> dict[str, object]:
        return {
            "surface": "real_paper_autonomy_provider_hosted_guarded_apply_receipt",
            "schema_version": 1,
            "status": "typed_blocker",
            "source_fingerprint": "stable-domain-result",
            "summary": {"status": "typed_blocker"},
            "authority_boundary": {"provider_attempt_is_truth": False},
        }

    monkeypatch.setattr(
        adapter.real_paper_autonomy_soak_inventory,
        "build_real_paper_autonomy_provider_hosted_guarded_apply_receipt",
        fake_guarded_apply,
    )

    task_path = tmp_path / "task.json"
    base_task = {
        "task_id": "frt_provider_guarded",
        "domain_id": "medautoscience",
        "task_kind": "paper_autonomy/guarded-apply",
        "payload": {
            "profile": str(profile_path),
            "study_id": "DM002",
            "target_studies": ["DM002"],
            "provider_attempt_id": "opl-temporal:nfpitnet:DM002:provider-hosted-guarded-apply",
            "idempotency_key": "mas:nfpitnet:DM002:provider-hosted-guarded-apply:opl-temporal",
        },
    }
    _write_json(task_path, {**base_task, "source_fingerprint": "proof-fingerprint-v1"})
    first_exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    first_payload = json.loads(capsys.readouterr().out)

    assert first_exit_code == 0
    assert first_payload["accepted"] is True
    assert first_payload["source_fingerprint"] == "proof-fingerprint-v1"
    assert first_payload["dispatch"]["result"]["source_fingerprint"] == "stable-domain-result"
    assert first_payload["receipt_ref"].startswith("artifacts/runtime/opl_family_domain_handler/dispatch_receipts/")

    repeat_exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    repeat_payload = json.loads(capsys.readouterr().out)

    assert repeat_exit_code == 0
    assert repeat_payload["receipt_ref"] == first_payload["receipt_ref"]
    assert repeat_payload["idempotent_noop"] is True

    _write_json(task_path, {**base_task, "source_fingerprint": "proof-fingerprint-v2"})
    updated_exit_code = cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"])
    updated_payload = json.loads(capsys.readouterr().out)

    assert updated_exit_code == 0
    assert updated_payload["accepted"] is True
    assert updated_payload["source_fingerprint"] == "proof-fingerprint-v2"
    assert updated_payload["dispatch"]["result"]["source_fingerprint"] == "stable-domain-result"
    assert updated_payload["receipt_ref"] != first_payload["receipt_ref"]
    assert updated_payload.get("idempotent_noop") is None


def test_domain_handler_dispatch_guarded_apply_replays_duplicate_attempt_idempotently(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(study_root / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": study_root.name})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )
    task = {
        "task_id": "guarded-apply-duplicate",
        "domain_id": "medautoscience",
        "task_kind": "paper_autonomy/guarded-apply",
        "payload": {
            "profile": str(profile_path),
            "study_id": "DM002",
            "provider_attempt_id": "opl-attempt-duplicate",
            "idempotency_key": "opl-attempt-duplicate:guarded-apply",
        },
    }
    task_path = tmp_path / "task.json"
    _write_json(task_path, task)

    assert cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"]) == 0
    first = json.loads(capsys.readouterr().out)
    assert cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"]) == 0
    second = json.loads(capsys.readouterr().out)

    assert second["idempotent_noop"] is True
    assert second["dispatch"]["result"]["source_fingerprint"] == first["dispatch"]["result"]["source_fingerprint"]


def test_domain_handler_dispatch_guarded_apply_fails_closed_on_conflicting_receipt(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(study_root / "artifacts" / "runtime" / "runtime_status_summary.json", {"study_id": study_root.name})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "guarded-apply-conflict",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/guarded-apply",
            "payload": {
                "profile": str(profile_path),
                "study_id": "DM002",
                "provider_attempt_id": "opl-attempt-conflict-a",
                "idempotency_key": "opl-attempt-conflict:guarded-apply",
            },
        },
    )
    assert cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"]) == 0
    first = json.loads(capsys.readouterr().out)
    _write_json(
        task_path,
        {
            "task_id": "guarded-apply-conflict",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/guarded-apply",
            "payload": {
                "profile": str(profile_path),
                "study_id": "DM002",
                "provider_attempt_id": "opl-attempt-conflict-b",
                "idempotency_key": "opl-attempt-conflict:guarded-apply",
            },
        },
    )

    assert cli.main(["domain-handler", "dispatch", "--task", str(task_path), "--format", "json"]) == 1
    conflict = json.loads(capsys.readouterr().out)

    assert conflict["accepted"] is False
    assert conflict["reason"] == "idempotency_key_intent_conflict"
    assert conflict["existing_source_fingerprint"] == first["dispatch"]["result"]["source_fingerprint"]
    assert conflict["requested_source_fingerprint"] != conflict["existing_source_fingerprint"]
