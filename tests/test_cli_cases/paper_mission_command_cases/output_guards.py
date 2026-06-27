from __future__ import annotations

import importlib
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "workspace",
    ("DM-CVD-Mortality-Risk", "NF-PitNET", "Obesity"),
)
def test_paper_mission_output_guards_allow_matching_yang_ops_roots(workspace: str) -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")

    commands._assert_safe_one_shot_output_root(
        Path(
            f"/Users/gaofeng/workspace/Yang/{workspace}/"
            "ops/medautoscience/paper_mission_one_shot_migration/20260623"
        )
    )
    commands._assert_safe_candidate_package_output_root(
        Path(
            f"/Users/gaofeng/workspace/Yang/{workspace}/"
            "ops/medautoscience/paper_mission_candidate_package/20260623"
        )
    )
    commands._assert_safe_consumption_ledger_output_root(
        Path(
            f"/Users/gaofeng/workspace/Yang/{workspace}/"
            "ops/medautoscience/paper_mission_consumption_ledger/20260623"
        )
    )


def test_paper_mission_output_guards_reject_wrong_non_authority_bucket() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        commands._assert_safe_one_shot_output_root(
            Path(
                "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
                "ops/medautoscience/paper_mission_consumption_ledger/20260623"
            )
        )

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        commands._assert_safe_candidate_package_output_root(
            Path(
                "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
                "ops/medautoscience/paper_mission_one_shot_migration/20260623"
            )
        )

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        commands._assert_safe_consumption_ledger_output_root(
            Path(
                "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
                "ops/medautoscience/paper_mission_candidate_package/20260623"
            )
        )


def test_paper_mission_drive_yang_output_root_uses_allowed_sibling_buckets(
    tmp_path: Path,
) -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")

    class Profile:
        workspace_root = tmp_path / "workspace"

    roots = commands._paper_mission_drive_output_roots(
        profile=Profile(),
        output_root=Path(
            "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
            "ops/medautoscience/paper_mission_drive/20260627Tdrive"
        ),
        run_id="20260627Tdrive",
    )

    commands._assert_safe_candidate_package_output_root(roots["candidate_package"])
    commands._assert_safe_consumption_ledger_output_root(roots["consumption_ledger"])
    assert roots["candidate_package"] == Path(
        "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
        "ops/medautoscience/paper_mission_candidate_package/20260627Tdrive"
    )
    assert roots["consumption_ledger"] == Path(
        "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/"
        "ops/medautoscience/paper_mission_consumption_ledger/20260627Tdrive"
    )


def test_one_shot_migration_rejects_yang_authority_and_runtime_output_roots() -> None:
    commands = importlib.import_module("med_autoscience.cli_parts.paper_mission_commands")

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        commands._assert_safe_candidate_output_root(
            Path(
                "/Users/gaofeng/workspace/Yang/NF-PitNET/"
                "studies/001-lineage-pfs/artifacts/publication_eval"
            )
        )

    with pytest.raises(ValueError, match="forbidden paper mission output root"):
        commands._assert_safe_candidate_output_root(
            Path(
                "/Users/gaofeng/workspace/Yang/Obesity/"
                "runtime/quests/obesity_multicenter_phenotype_atlas/provider_attempt"
            )
        )
