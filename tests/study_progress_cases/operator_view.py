from __future__ import annotations

from pathlib import Path

from tests.study_progress_cases.shared import make_profile


def test_study_command_surfaces_include_paper_mission_refresh(tmp_path: Path) -> None:
    from med_autoscience.controllers.study_progress.operator_view import (
        _study_command_surfaces,
    )

    profile = make_profile(tmp_path)
    commands = _study_command_surfaces(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        profile_ref=profile.profile_ref,
    )

    assert "paper-mission inspect" in commands["refresh_supervision"]
    assert "--format json" in commands["refresh_supervision"]
