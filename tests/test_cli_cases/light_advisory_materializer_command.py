from __future__ import annotations

import json
from pathlib import Path

from .shared import *  # noqa: F403,F401


def test_light_advisory_materializer_cli_applies_refs_from_profile(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    (study_root / "paper").mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    (study_root / "paper" / "evidence_ledger.json").write_text('{"claims": []}\n', encoding="utf-8")

    exit_code = cli.main(
        [
            "light-advisory-materialize",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--work-unit-id",
            "wu-cli-001",
            "--owner-action",
            "run_ai_reviewer_workflow",
            "--stage",
            "review",
            "--source-ref",
            "study.yaml",
            "--source-ref",
            "paper/evidence_ledger.json",
            "--payload-json",
            json.dumps(
                {
                    "collision_check": {
                        "core_claim_ref": "paper/evidence_ledger.json#/claims/0",
                        "nearest_neighbor_work_refs": ["pmid:neighbor-1"],
                    },
                    "fresh_evidence_gate": {
                        "verification_command_or_ref": "scripts/verify.sh",
                        "verification_exit_state": "passed",
                    },
                }
            ),
            "--apply",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "light_external_advisory_materialize_command"
    assert payload["result"]["status"] == "materialized"
    assert payload["result"]["study_id"] == "001-risk"
    bundle_path = study_root / payload["result"]["bundle_ref"]
    assert bundle_path.is_file()
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle["owner_action"] == "run_ai_reviewer_workflow"
    assert bundle["authority_boundary"]["can_sign_owner_receipt"] is False


def test_light_advisory_materializer_cli_grouped_study_alias(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    exit_code = cli.main(
        [
            "study",
            "light-advisory-materialize",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--work-unit-id",
            "wu-cli-alias",
            "--owner-action",
            "scout_next_delta",
            "--source-ref",
            "study.yaml",
            "--dry-run",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["result"]["status"] == "dry_run"
    assert payload["result"]["bundle_ref"] == (
        "artifacts/stage_outputs/current_owner_action/advisory/light_external_pattern_refs.json"
    )
