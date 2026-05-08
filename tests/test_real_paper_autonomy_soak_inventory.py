from __future__ import annotations

import json
import subprocess
from pathlib import Path

from med_autoscience.controllers.real_paper_autonomy_soak_inventory import (
    build_real_paper_autonomy_soak_inventory,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_profile(workspace: Path, profile_path: Path) -> None:
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        "\n".join(
            [
                'name = "fixture"',
                f'workspace_root = "{workspace}"',
                f'runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'studies_root = "{workspace / "studies"}"',
                f'portfolio_root = "{workspace / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_real_paper_autonomy_soak_inventory_is_dry_run_and_reports_legacy_evidence(
    tmp_path: Path,
) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "Fixture"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "fixture.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    (workspace / "ops" / "med-deepscientist" / "runtime" / "quests").mkdir(parents=True)
    (workspace / "ops" / "medautoscience" / "bin").mkdir(parents=True)
    launcher = workspace / "ops" / "medautoscience" / "bin" / "watch-runtime"
    launcher.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    status_path = _write_json(
        workspace / "studies" / "001-paper" / "artifacts" / "runtime" / "runtime_status_summary.json",
        {
            "study_id": "001-paper",
            "health_status": "inactive",
            "runtime_reason": "quest_parked_on_unchanged_finalize_state",
            "active_run_id": "",
        },
    )
    before_mtimes = {path: path.stat().st_mtime_ns for path in (profile_path, launcher, status_path)}

    payload = build_real_paper_autonomy_soak_inventory(yang_root=yang_root)

    assert payload["surface"] == "real_paper_autonomy_soak_inventory"
    assert payload["mode"] == "dry_run_inventory"
    assert payload["read_only_contract"]["writes_real_workspace"] is False
    assert payload["summary"]["writes_performed"] is False
    assert payload["profile_count"] == 1
    report = payload["profiles"][0]
    assert report["profile_readable"] is True
    assert report["migration_readiness"] == "dry_run_ready_legacy_evidence_present"
    assert report["status_progress_readability"] == {
        "study_count": 1,
        "readable_study_count": 1,
        "all_discovered_studies_readable": True,
    }
    assert report["studies"][0]["status"] == "parked"
    assert report["studies"][0]["reason"] == "quest_parked_on_unchanged_finalize_state"
    assert any(item["kind"] == "profile_path" for item in report["legacy_mds_evidence"])
    assert any(item["key"] == "ops/medautoscience/bin/watch-runtime" for item in report["legacy_mds_evidence"])
    assert not (workspace / "artifacts" / "runtime" / "real_paper_autonomy_soak_inventory.json").exists()
    assert {path: path.stat().st_mtime_ns for path in before_mtimes} == before_mtimes


def test_real_paper_autonomy_soak_inventory_reports_active_as_audit_only(tmp_path: Path) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "Active"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "active.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    _write_json(
        workspace / "studies" / "002-active" / "artifacts" / "runtime" / "runtime_status_summary.json",
        {
            "study_id": "002-active",
            "health_status": "running",
            "active_run_id": "run-123",
            "runtime_reason": "worker_running",
        },
    )

    payload = build_real_paper_autonomy_soak_inventory(yang_root=yang_root)

    report = payload["profiles"][0]
    assert report["migration_readiness"] == "audit_only_active_study_present"
    assert report["studies"][0]["status"] == "active"
    assert report["studies"][0]["active_run_id"] == "run-123"


def test_real_paper_autonomy_soak_inventory_script_outputs_json_without_writes(
    tmp_path: Path,
) -> None:
    yang_root = tmp_path / "Yang"
    workspace = yang_root / "Script"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "script.workspace.toml"
    _write_profile(workspace, profile_path)
    (workspace / "portfolio").mkdir(parents=True)
    _write_json(
        workspace / "studies" / "003-complete" / "artifacts" / "runtime" / "runtime_status_summary.json",
        {"study_id": "003-complete", "quest_status": "completed", "runtime_reason": "done"},
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/real-paper-autonomy-soak-inventory.py",
            "--yang-root",
            str(yang_root),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["profile_count"] == 1
    assert payload["profiles"][0]["studies"][0]["status"] == "completed"
    assert not (workspace / "artifacts").exists()
