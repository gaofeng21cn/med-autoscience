from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.real_paper_autonomy_soak_inventory import (
    build_real_paper_autonomy_soak_projection,
    discover_yang_profile_paths,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_profile(workspace: Path, profile_path: Path) -> None:
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        "\n".join(
            (
                'name = "fixture"',
                f'workspace_root = "{workspace}"',
                f'runtime_root = "{workspace / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'studies_root = "{workspace / "studies"}"',
                f'portfolio_root = "{workspace / "memory" / "portfolio"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_soak_projection_discovers_profile_from_workspace_root(tmp_path: Path) -> None:
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

    assert discover_yang_profile_paths(workspace) == [profile_path.resolve()]
    payload = build_real_paper_autonomy_soak_projection(
        yang_root=workspace,
        target_studies=("DM002",),
    )

    assert payload["profiles"][0]["profile_path"] == str(profile_path.resolve())
    coverage = {item["target_study"]: item for item in payload["summary"]["target_coverage"]}
    assert coverage["DM002"]["status"] == "has_projection_evidence"
    assert coverage["DM002"]["matched_study_ids"] == [study_root.name]
    assert payload["summary"]["typed_blocker_count"] == 0
    assert payload["summary"]["writes_performed"] is False
