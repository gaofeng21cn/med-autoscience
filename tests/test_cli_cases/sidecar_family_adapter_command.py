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


def test_sidecar_export_projects_mas_owned_runtime_surfaces(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {"state": "running", "owner_route": {"owner": "mas_controller"}},
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {"state": "breach", "breach_reason": "worker_recovery"},
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "recovery_intent" / "latest.json",
        {"current_action": "safe_reconcile_ready", "retry_budget": {"remaining": 2}},
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {"decision_id": "decision-001", "owner_route": {"owner": "publication_controller"}},
    )

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "mas_family_sidecar_export"
    assert payload["target_domain_id"] == "medautoscience"
    assert payload["online_runtime_substrate"]["owner"] == "opl_managed_hermes"
    assert payload["authority_boundary"]["domain_truth_owner"] == "med-autoscience"
    assert payload["authority_boundary"]["forbidden_authorities"] == [
        "study_truth_write",
        "publication_quality_verdict",
        "artifact_gate_override",
        "current_package_write",
    ]
    assert payload["profile"]["profile_ref"] == str(profile_path)
    assert payload["workspace"]["workspace_root"] == str(workspace_root)
    assert payload["studies"][0]["study_id"] == "001-risk"
    assert payload["studies"][0]["runtime_supervision"]["state"] == "running"
    assert payload["studies"][0]["slo_status"]["state"] == "breach"
    assert payload["studies"][0]["recovery_intent"]["current_action"] == "safe_reconcile_ready"


def test_sidecar_dispatch_accepts_runtime_recovery_without_writing_truth(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "frt_001",
            "domain_id": "medautoscience",
            "task_kind": "runtime_supervision/recover",
            "payload": {"profile": str(profile_path), "study_id": "001-risk"},
            "attempts": 1,
            "source": "opl_family_runtime",
            "authority_boundary": {
                "hermes": "online_runtime_substrate_only",
                "opl": "typed_queue_and_dispatch_only",
                "domain": "truth_quality_artifact_gate_owner",
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "mas_family_sidecar_dispatch_receipt"
    assert payload["accepted"] is True
    assert payload["will_start_llm_worker"] is False
    assert payload["dispatch"]["action_type"] == "runtime_supervisor_recover"
    assert payload["dispatch"]["recommended_domain_command"].startswith("uv run python -m med_autoscience.cli runtime-supervisor-scan")
    assert payload["authority_boundary"]["writes_domain_truth"] is False
    assert payload["authority_boundary"]["writes_artifact_gate"] is False


def test_sidecar_dispatch_rejects_domain_truth_writes(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "frt_forbidden",
            "domain_id": "medautoscience",
            "task_kind": "artifact/override",
            "payload": {"domain_truth_write": True, "profile": "/tmp/profile.toml"},
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 1
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "mas_family_sidecar_dispatch_receipt"
    assert payload["accepted"] is False
    assert payload["forbidden_domain_truth_write"] is True
    assert payload["reason"] == "domain_truth_or_artifact_gate_write_forbidden"
