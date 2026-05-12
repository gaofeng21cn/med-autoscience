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


def test_sidecar_dispatch_guarded_apply_records_mas_owner_receipt_present(
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

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    result = payload["dispatch"]["result"]
    assert result["status"] == "applied"
    assert result["provider_attempt"]["attempt_state"] == "mas_owner_receipt_present"
    assert result["summary"]["provider_attempt_wrote_workspace"] is False
    assert result["summary"]["writes_performed_by_this_receipt"] is False
    assert result["guarded_apply_receipts"][0]["workspace_mutation"]["mutation_owner"] == "med-autoscience"
    assert result["guarded_apply_receipts"][0]["workspace_mutation"]["provider_attempt_wrote_workspace"] is False


def test_sidecar_dispatch_guarded_apply_records_provider_unavailable_typed_blocker(
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

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    result = payload["dispatch"]["result"]
    assert result["status"] == "typed_blocker"
    assert result["provider_attempt"]["attempt_state"] == "provider_unavailable"
    assert result["provider_attempt"]["attempt_ready"] is False
    assert result["typed_blockers"][0]["blocker_id"].startswith("provider_guarded_apply_unavailable:")
    assert result["summary"]["writes_performed"] is False


def test_sidecar_dispatch_guarded_apply_replays_duplicate_attempt_idempotently(
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

    assert cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"]) == 0
    first = json.loads(capsys.readouterr().out)
    assert cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"]) == 0
    second = json.loads(capsys.readouterr().out)

    assert second["idempotent_noop"] is True
    assert second["dispatch"]["result"]["source_fingerprint"] == first["dispatch"]["result"]["source_fingerprint"]


def test_sidecar_dispatch_guarded_apply_fails_closed_on_conflicting_receipt(
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
    assert cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"]) == 0
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

    assert cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"]) == 1
    conflict = json.loads(capsys.readouterr().out)

    assert conflict["accepted"] is False
    assert conflict["reason"] == "idempotency_key_intent_conflict"
    assert conflict["existing_source_fingerprint"] == first["dispatch"]["result"]["source_fingerprint"]
    assert conflict["requested_source_fingerprint"] != conflict["existing_source_fingerprint"]
