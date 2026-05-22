from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_reconcile_study_truth_command_materializes_from_runtime_status(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    study_root = tmp_path / "studies" / "001-risk"
    called: dict[str, object] = {}

    def fake_status(*, profile, study_id: str | None, study_root: Path | None, entry_mode: str | None) -> dict:
        called["status_profile"] = profile
        called["status_study_id"] = study_id
        called["status_study_root"] = study_root
        called["status_entry_mode"] = entry_mode
        return {
            "study_id": "001-risk",
            "study_root": str(study_root if study_root is not None else tmp_path / "studies" / "001-risk"),
            "generated_at": "2026-05-01T00:00:00+00:00",
            "quest_status": "running",
            "execution_owner_guard": {
                "supervisor_only": True,
                "active_run_id": "run-live",
            },
        }

    def fake_reconcile(*, study_root: Path, study_id: str, status_payload: dict, recorded_at: str) -> dict:
        called["reconcile_study_root"] = study_root
        called["reconcile_study_id"] = study_id
        called["reconcile_status_payload"] = status_payload
        called["reconcile_recorded_at"] = recorded_at
        return {
            "surface": "study_truth_reconcile_result",
            "study_id": study_id,
            "truth_epoch": "truth-event-000002-live",
            "snapshot_path": str(study_root / "artifacts" / "truth" / "latest.json"),
        }

    monkeypatch.setattr(cli.study_runtime_router, "progress_projection", fake_status)
    monkeypatch.setattr(cli.study_truth_kernel, "reconcile_truth_snapshot_from_status_payload", fake_reconcile)

    exit_code = cli.main(
        [
            "study",
            "reconcile-truth",
            "--profile",
            str(profile_path),
            "--study-root",
            str(study_root),
            "--entry-mode",
            "full_research",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert called["status_profile"].name == "nfpitnet"
    assert called["status_study_id"] is None
    assert called["status_study_root"] == study_root
    assert called["status_entry_mode"] == "full_research"
    assert called["reconcile_study_root"] == study_root
    assert called["reconcile_study_id"] == "001-risk"
    assert called["reconcile_status_payload"]["execution_owner_guard"]["active_run_id"] == "run-live"
    assert called["reconcile_recorded_at"] == "2026-05-01T00:00:00+00:00"
    assert payload["surface"] == "study_truth_reconcile_result"
    assert payload["truth_epoch"] == "truth-event-000002-live"
