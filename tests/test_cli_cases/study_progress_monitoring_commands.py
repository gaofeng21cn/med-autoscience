from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_progress_projection_retires_json_alias_and_keeps_format_json() -> None:
    cli = importlib.import_module("med_autoscience.cli")
    parser = cli.build_parser()

    args = parser.parse_args(
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
    assert args.command == "progress-projection"
    assert args.format == "json"

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "progress-projection",
                "--profile",
                "profile.local.toml",
                "--study-id",
                "003-dpcc",
                "--json",
            ]
        )


def test_progress_projection_command_surfaces_progress_first_user_visible_view(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    def fail_old_progress_projection(**_: object) -> dict:
        raise AssertionError("progress-projection must not use legacy domain_status_projection")

    def fake_read_study_progress(
        *,
        profile,
        profile_ref: Path,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        sync_runtime_summary: bool,
        materialize_read_model_artifacts: bool,
    ) -> dict:
        assert profile.name == "nfpitnet"
        assert profile_ref == profile_path
        assert study_id == "003-dpcc"
        assert study_root is None
        assert entry_mode is None
        assert sync_runtime_summary is False
        assert materialize_read_model_artifacts is False
        return {
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "decision": "resume",
            "reason": "domain_transition_ai_reviewer_re_eval",
            "active_run_id": "stale-runtime-run",
            "progress_projection": {
                "study_id": study_id,
                "quest_id": study_id,
                "current_stage": "publication_supervision",
                "current_stage_summary": "old runtime-facing stage",
                "paper_stage": "analysis-campaign",
                "paper_stage_summary": "old paper stage summary",
                "next_system_action": "old runtime-facing action",
                "needs_physician_decision": False,
                "progress_first_monitoring_summary": {
                    "surface": "progress_first_monitoring_summary",
                    "authority": "refs_only_observability",
                    "study_id": study_id,
                    "active_run_id": "run-003",
                    "active_stage_attempt_id": "attempt-003",
                    "running_provider_attempt": True,
                    "worker_liveness": {"health_status": "live"},
                    "next_owner": "ai_reviewer",
                    "controller_action": "return_to_ai_reviewer_workflow",
                    "next_work_unit": {
                        "unit_id": "ai_reviewer_medical_prose_quality_review",
                    },
                    "foreground_write_policy": {
                        "supervisor_only": True,
                        "foreground_can_write_runtime_owned_surfaces": False,
                    },
                },
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
        }

    monkeypatch.setattr(cli.domain_status_projection, "progress_projection", fail_old_progress_projection)
    monkeypatch.setattr(cli.study_progress, "read_study_progress", fake_read_study_progress)

    exit_code = cli.main(
        [
            "progress-projection",
            "--profile",
            str(profile_path),
            "--study-id",
            "003-dpcc",
        ]
    )
    captured = capsys.readouterr()

    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["decision"] == "resume"
    assert payload["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert payload["current_stage"] == "queued"
    assert payload["current_stage_summary"] == "质量修复/复审中；质量、artifact 或 runtime 有明确修复 owner。"
    assert payload["next_system_action"] == "回到 AI reviewer 复评。"
    assert payload["paper_stage"] == "analysis-campaign"
    assert payload["current_blockers"] == ["medical journal prose style not met"]
    assert payload["user_visible_projection"]["state"] == "queued/repair/quality"
    monitoring = payload["progress_first_monitoring_summary"]
    assert monitoring["authority"] == "refs_only_observability"
    assert monitoring["active_run_id"] == "run-003"
    assert monitoring["active_stage_attempt_id"] == "attempt-003"
    assert monitoring["worker_liveness"]["health_status"] == "live"
    assert monitoring["next_owner"] == "ai_reviewer"
    assert monitoring["controller_action"] == "return_to_ai_reviewer_workflow"
    assert monitoring["next_work_unit"]["unit_id"] == "ai_reviewer_medical_prose_quality_review"
    assert monitoring["foreground_write_policy"]["foreground_can_write_runtime_owned_surfaces"] is False
    assert payload["progress_first_projection"]["source"] == "progress_projection.user_visible_projection"


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
