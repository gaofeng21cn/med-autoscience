from __future__ import annotations

import json
import subprocess
from pathlib import Path

from med_autoscience.controllers.real_paper_autonomy_soak_inventory import (
    build_real_paper_autonomy_soak_projection,
    discover_yang_profile_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


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
                f'portfolio_root = "{workspace / "memory" / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_discover_yang_profile_paths_accepts_workspace_root(tmp_path: Path) -> None:
    workspace = tmp_path / "Yang" / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)

    assert discover_yang_profile_paths(workspace) == [profile_path.resolve()]


def test_real_paper_autonomy_soak_projection_discovers_profile_from_workspace_root(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "Yang" / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    study_root = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_status_summary.json",
        {"study_id": study_root.name, "health_status": "running"},
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )

    payload = build_real_paper_autonomy_soak_projection(
        yang_root=workspace,
        target_studies=("DM002",),
    )

    assert payload["profiles"][0]["profile_path"] == str(profile_path.resolve())
    assert payload["profiles"][0]["studies"][0]["study_id"] == study_root.name
    coverage = {item["target_study"]: item for item in payload["summary"]["target_coverage"]}
    assert coverage["DM002"]["status"] == "has_projection_evidence"
    assert coverage["DM002"]["matched_study_ids"] == [study_root.name]
    assert payload["summary"]["typed_blocker_count"] == 0


def test_real_paper_autonomy_guarded_apply_proof_cli_discovers_workspace_root_profile(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "Yang" / "DM"
    profile_path = workspace / "ops" / "medautoscience" / "profiles" / "dm.workspace.toml"
    _write_profile(workspace, profile_path)
    study_root = workspace / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_status_summary.json",
        {"study_id": study_root.name, "health_status": "running"},
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"assessment_provenance": {"owner": "ai_reviewer"}, "eval_id": "eval-dm002"},
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-m",
            "med_autoscience.cli",
            "real-paper-autonomy-guarded-apply-proof",
            "--yang-root",
            str(workspace),
            "--target-study",
            "DM002",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    receipt = payload["guarded_apply_receipts"][0]
    assert receipt["study_id"] == study_root.name
    assert str(study_root / "artifacts" / "publication_eval" / "latest.json") in receipt["source_refs"]
    assert payload["summary"]["writes_performed"] is False
