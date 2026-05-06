from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def test_study_state_matrix_command_projects_macro_state_without_writing(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    studies_root = workspace_root / "studies"
    for study_id in ("001-dm", "002-dm"):
        study_root = studies_root / study_id
        study_root.mkdir(parents=True)
        (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    def fake_status(*, study_id, **_):
        if study_id == "002-dm":
            return {"study_id": study_id, "quest_status": "running", "active_run_id": "run-002"}
        return {
            "study_id": study_id,
            "quest_status": "paused",
            "active_run_id": None,
            "reason": "quest_waiting_for_submission_metadata",
            "auto_runtime_parked": {"parked": True, "parked_state": "external_metadata_pending"},
            "submission_metadata": {"missing_external_info": ["authors", "ethics", "funding"]},
            "study_truth_snapshot": {
                "truth_epoch": "truth-001",
                "source_signature": "source-001",
                "package_state": {"authority_state": "current"},
            },
        }

    monkeypatch.setattr(cli.study_runtime_router, "study_runtime_status", fake_status)

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["surface"] == "study_state_matrix"
    assert payload["counts"] == {"live": 1, "parked": 1}
    assert payload["studies"][0]["study_id"] == "001-dm"
    assert payload["studies"][0]["study_macro_state"]["user_next"] == "submit_info"
    assert payload["studies"][1]["study_macro_state"]["writer_state"] == "live"
    assert payload["studies"][1]["active_run_id"] == "run-002"


def test_study_state_matrix_markdown_uses_short_macro_status(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "004-invasive"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 004-invasive\n", encoding="utf-8")

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "004-invasive",
            "quest_status": "paused",
            "active_run_id": None,
            "reason": "publishability_stop_loss_recommended",
            "study_truth_snapshot": {
                "quality_state": {"state": "stop_loss_recommended"},
                "package_state": {"authority_state": "current"},
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "markdown"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "| 004-invasive | parked | none | stop_loss |" in captured.out
    assert "publishability_stop_loss_recommended" not in captured.out


def test_study_state_matrix_marks_stop_line_milestone_package_without_reopening_quality_gate(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "004-dpcc"
    package_root = study_root / "manuscript" / "current_package"
    (package_root / "figures").mkdir(parents=True)
    (package_root / "tables").mkdir()
    (study_root / "study.yaml").write_text("study_id: 004-dpcc\n", encoding="utf-8")
    for path in (
        package_root / "manuscript.docx",
        package_root / "paper.pdf",
        package_root / "figures" / "Figure1.png",
        package_root / "tables" / "Table1.csv",
        study_root / "manuscript" / "current_package.zip",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")
    (package_root / "SUBMISSION_TODO.md").write_text(
        "# Submission TODO\n\nPending items:\n- Authors: pending\n- Ethics: pending\n- Funding: pending\n",
        encoding="utf-8",
    )
    (package_root / "submission_manifest.json").write_text(
        json.dumps(
            {
                "figures": [{"figure_id": "F1"}],
                "tables": [{"table_id": "T1"}],
                "surface_qc": {"status": "pass", "failures": []},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "004-dpcc",
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
            "reason": "quest_waiting_for_explicit_wakeup_after_manual_hold",
            "study_truth_snapshot": {
                "quality_state": {"state": "user_stopped"},
                "package_state": {"authority_state": "not_observed"},
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    study = json.loads(captured.out)["studies"][0]

    assert exit_code == 0
    assert study["study_macro_state"]["writer_state"] == "parked"
    assert study["study_macro_state"]["reason"] == "user_stop"
    assert study["study_macro_state"]["details"]["package_delivered"] is True
    assert study["delivered_package"]["authority_role"] == "user_visible_milestone_package_not_quality_authority"


def test_study_state_matrix_top_active_run_uses_macro_truth_when_status_top_level_is_empty(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "002-dm"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 002-dm\n", encoding="utf-8")

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "002-dm",
            "study_root": str(study_root),
            "quest_status": "active",
            "active_run_id": None,
            "study_truth_snapshot": {
                "active_run_id": "run-from-truth",
                "execution_owner": {"active_run_id": "run-from-truth"},
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    study = json.loads(captured.out)["studies"][0]

    assert exit_code == 0
    assert study["active_run_id"] == "run-from-truth"
    assert study["study_macro_state"]["writer_state"] == "live"
