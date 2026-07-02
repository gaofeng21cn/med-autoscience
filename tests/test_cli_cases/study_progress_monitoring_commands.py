from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_progress_projection_command_is_retired() -> None:
    cli = importlib.import_module("med_autoscience.cli")
    parser = cli.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "progress-projection",
                "--profile",
                "profile.local.toml",
                "--study-id",
                "003-dpcc",
                "--format",
                "json",
            ]
        )


def test_study_progress_json_surfaces_progress_first_user_visible_view(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    monkeypatch.setattr(
        cli.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "schema_version": 1,
            "study_id": kwargs["study_id"],
            "quest_id": kwargs["study_id"],
            "current_stage": "publication_supervision",
            "current_stage_summary": "old runtime-facing stage",
            "paper_stage": "analysis-campaign",
            "paper_stage_summary": "old paper stage summary",
            "next_system_action": "old runtime-facing action",
            "needs_physician_decision": False,
            "user_visible_projection": {
                "schema_version": 2,
                "writer_state": "queued",
                "user_next": "repair",
                "reason": "quality",
                "state": "queued/repair/quality",
                "state_label": "质量修复/复审中",
                "state_summary": "质量修复/复审中；质量、artifact 或 runtime 有明确修复 owner。",
                "current_stage": "queued",
                "current_stage_summary": "质量修复/复审中；质量、artifact 或 runtime 有明确修复 owner。",
                "paper_stage": "analysis-campaign",
                "paper_stage_summary": "质量修复/复审中；质量、artifact 或 runtime 有明确修复 owner。",
                "next_system_action": "回到 AI reviewer 复评。",
                "next_step": "回到 AI reviewer 复评。",
                "current_blockers": ["medical journal prose style not met"],
                "needs_user_decision": False,
                "needs_physician_decision": False,
            },
        },
    )

    exit_code = cli.main(
        [
            "study-progress",
            "--profile",
            str(profile_path),
            "--study-id",
            "003-dpcc",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["current_stage"] == "queued"
    assert payload["current_stage_summary"] == "质量修复/复审中；质量、artifact 或 runtime 有明确修复 owner。"
    assert payload["next_system_action"] == "回到 AI reviewer 复评。"
    assert payload["reason"] == "quality"
    assert payload["paper_stage"] == "analysis-campaign"
    assert payload["current_blockers"] == ["medical journal prose style not met"]
    assert payload["user_visible_projection"]["state"] == "queued/repair/quality"
    assert payload["progress_first_projection"]["source"] == "user_visible_projection"


def test_study_progress_json_preserves_typed_blocker_resolution_owner_action(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    action = {
        "surface_kind": "current_executable_owner_action",
        "source": "paper_mission_typed_blocker_resolution",
        "authority": "study_progress.current_executable_owner_action",
        "required_delta_kind": "typed_blocker_resolution_owner_action",
        "next_owner": "mas_authority_kernel",
        "action_type": "classify_quality_blockers_or_materialize_degraded_handoff_gate",
        "work_unit_id": "submission_blocker_degraded_handoff_or_quality_repair",
        "work_unit_fingerprint": "133c677b0fd92c0a91ae075b",
    }

    monkeypatch.setattr(
        cli.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "schema_version": 1,
            "study_id": kwargs["study_id"],
            "current_stage": "paper_mission",
            "current_executable_owner_action": action,
        },
    )

    exit_code = cli.main(
        [
            "study-progress",
            "--profile",
            str(profile_path),
            "--study-id",
            "obesity_multicenter_phenotype_atlas",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["current_executable_owner_action"] == action


def test_study_progress_json_still_removes_legacy_owner_action(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    monkeypatch.setattr(
        cli.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "schema_version": 1,
            "study_id": kwargs["study_id"],
            "current_stage": "paper_mission",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "legacy_current_executable_owner_action",
            },
        },
    )

    exit_code = cli.main(
        [
            "study-progress",
            "--profile",
            str(profile_path),
            "--study-id",
            "obesity_multicenter_phenotype_atlas",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    payload = json.loads(captured.out)
    assert exit_code == 0
    assert "current_executable_owner_action" not in payload
