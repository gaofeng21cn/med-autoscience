from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tests.profile_test_helpers import write_profile


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_opl_module_carrier_builds_only_declared_structured_fields() -> None:
    carrier = importlib.import_module("med_autoscience.opl_module_carrier")

    request = carrier.build_domain_entry_request(
        command="study_state_matrix",
        string_fields=[("profile_ref", "/tmp/profile.toml")],
        list_fields=[("study_ids", "study-001"), ("study_ids", "study-002")],
    )

    assert request == {
        "command": "study-state-matrix",
        "profile_ref": "/tmp/profile.toml",
        "study_ids": ["study-001", "study-002"],
    }
    with pytest.raises(ValueError, match="Unsupported field"):
        carrier.build_domain_entry_request(
            command="study-state-matrix",
            string_fields=[("private_cli_command", "status")],
        )


def test_workspace_entry_materialization_upgrades_legacy_scripts_without_private_cli(tmp_path: Path) -> None:
    rendering = importlib.import_module("med_autoscience.controllers.workspace_entry_rendering")
    workspace_root = tmp_path / "workspace"
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "fixture.local.toml"
    profile_path.parent.mkdir(parents=True)
    write_profile(profile_path, workspace_root=workspace_root)
    shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    matrix = shared.parent / "study-state-matrix"
    config_example = workspace_root / "ops" / "medautoscience" / "config.env.example"
    shared.parent.mkdir(parents=True)
    shared.write_text(
        '#!/usr/bin/env bash\nMEDAUTOSCI_OPS_ROOT="legacy"\nrun_medautosci() { python -m med_autoscience.cli "$@"; }\n',
        encoding="utf-8",
    )
    matrix.write_text(
        '#!/usr/bin/env bash\nsource "$(cd "$(dirname "$0")" && pwd)/_shared.sh"\nrun_medautosci study-state-matrix\n',
        encoding="utf-8",
    )
    config_example.write_text(
        'MED_AUTOSCIENCE_REPO="/old/med-autoscience"\n'
        f'MED_AUTOSCIENCE_PROFILE="{profile_path}"\n',
        encoding="utf-8",
    )

    result = rendering.materialize_workspace_entries(
        workspace_root=workspace_root,
        profile_ref=profile_path,
        repo_root=REPO_ROOT,
    )

    assert str(shared) in result["upgraded_files"]
    assert str(matrix) in result["upgraded_files"]
    assert str(config_example) in result["upgraded_files"]
    assert result["blocked_files"] == []
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (shared, matrix, shared.parent / "study-progress", shared.parent / "paper-mission")
    )
    assert "opl-module-dispatch.sh" in combined
    assert "run_medautosci" not in combined
    assert "workspace/.venv" not in combined
    assert "med_autoscience.cli" not in combined
    assert "run-python-clean.sh" not in combined
    assert result["workspace_local_venv_used"] is False
    assert result["private_cli_used"] is False


def test_workspace_entry_materializer_script_supports_dry_run_and_apply(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "fixture.local.toml"
    profile_path.parent.mkdir(parents=True)
    write_profile(profile_path, workspace_root=workspace_root)
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "materialize-workspace-entry.py"),
        "--workspace-root",
        str(workspace_root),
        "--profile",
        str(profile_path),
    ]

    dry_run = subprocess.run(
        [*command, "--dry-run"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    dry_payload = json.loads(dry_run.stdout)
    matrix_path = workspace_root / "ops" / "medautoscience" / "bin" / "study-state-matrix"
    assert str(matrix_path) in dry_payload["created_files"]
    assert matrix_path.exists() is False

    applied = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    applied_payload = json.loads(applied.stdout)
    assert str(matrix_path) in applied_payload["created_files"]
    assert os.access(matrix_path, os.X_OK)


@pytest.mark.materialization_heavy
def test_materialized_study_state_matrix_returns_json_through_opl_managed_runtime(tmp_path: Path) -> None:
    rendering = importlib.import_module("med_autoscience.controllers.workspace_entry_rendering")
    workspace_root = tmp_path / "workspace"
    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "fixture.local.toml"
    profile_path.parent.mkdir(parents=True)
    write_profile(profile_path, workspace_root=workspace_root)

    result = rendering.materialize_workspace_entries(
        workspace_root=workspace_root,
        profile_ref=profile_path,
        repo_root=REPO_ROOT,
    )
    assert result["blocked_files"] == []

    runtime_root = tmp_path / "opl-runtime"
    cache_root = tmp_path / "opl-cache"
    env = {
        **os.environ,
        "MAS_OPL_MODULE_RUNTIME_ROOT": str(runtime_root),
        "MAS_OPL_MODULE_CACHE_ROOT": str(cache_root),
    }
    subprocess.run(
        [str(REPO_ROOT / "scripts" / "opl-module-bootstrap.sh")],
        cwd=REPO_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    completed = subprocess.run(
        [
            "/bin/bash",
            str(workspace_root / "ops" / "medautoscience" / "bin" / "study-state-matrix"),
            "--format",
            "json",
        ],
        cwd=workspace_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["command"] == "study-state-matrix"
    assert payload["surface"] == "study_state_matrix"
    assert payload["workspace_root"] == str(workspace_root)
    assert payload["study_count"] == 0
