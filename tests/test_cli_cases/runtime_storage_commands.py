from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_runtime_maintain_storage_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_maintain_runtime_storage(
        *,
        profile,
        study_id: str | None,
        study_root: Path | None,
        include_worktrees: bool,
        older_than_seconds: int,
        jsonl_max_mb: int,
        text_max_mb: int,
        event_segment_max_mb: int,
        slim_jsonl_threshold_mb: int | None,
        dedupe_worktree_min_mb: int | None,
        head_lines: int,
        tail_lines: int,
        allow_live_runtime: bool,
        restore_proof_compaction: bool,
        restore_proof_buckets: tuple[str, ...],
        include_parked_controller_stop: bool,
        include_operator_confirmed_parked_active: bool,
        refs_only_state_index_pilot: bool,
        refs_only_state_index_only: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["include_worktrees"] = include_worktrees
        called["older_than_seconds"] = older_than_seconds
        called["jsonl_max_mb"] = jsonl_max_mb
        called["text_max_mb"] = text_max_mb
        called["event_segment_max_mb"] = event_segment_max_mb
        called["slim_jsonl_threshold_mb"] = slim_jsonl_threshold_mb
        called["dedupe_worktree_min_mb"] = dedupe_worktree_min_mb
        called["head_lines"] = head_lines
        called["tail_lines"] = tail_lines
        called["allow_live_runtime"] = allow_live_runtime
        called["restore_proof_compaction"] = restore_proof_compaction
        called["restore_proof_buckets"] = restore_proof_buckets
        called["include_parked_controller_stop"] = include_parked_controller_stop
        called["include_operator_confirmed_parked_active"] = include_operator_confirmed_parked_active
        called["refs_only_state_index_pilot"] = refs_only_state_index_pilot
        called["refs_only_state_index_only"] = refs_only_state_index_only
        return {"status": "maintained", "quest_id": "quest-001"}

    monkeypatch.setattr(cli.runtime_storage_maintenance, "maintain_runtime_storage", fake_maintain_runtime_storage)

    exit_code = cli.main(
        [
            "runtime",
            "maintain-storage",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--no-worktrees",
            "--older-than-hours",
            "12",
            "--jsonl-max-mb",
            "32",
            "--text-max-mb",
            "8",
            "--event-segment-max-mb",
            "48",
            "--slim-jsonl-threshold-mb",
            "6",
            "--dedupe-worktree-min-mb",
            "24",
            "--head-lines",
            "100",
            "--tail-lines",
            "120",
            "--allow-live-runtime",
            "--refs-only-state-index-pilot",
            "--refs-only-state-index-only",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["include_worktrees"] is False
    assert called["older_than_seconds"] == 12 * 3600
    assert called["jsonl_max_mb"] == 32
    assert called["text_max_mb"] == 8
    assert called["event_segment_max_mb"] == 48
    assert called["slim_jsonl_threshold_mb"] == 6
    assert called["dedupe_worktree_min_mb"] == 24
    assert called["head_lines"] == 100
    assert called["tail_lines"] == 120
    assert called["allow_live_runtime"] is True
    assert called["restore_proof_compaction"] is False
    assert called["restore_proof_buckets"] == ()
    assert called["include_parked_controller_stop"] is False
    assert called["include_operator_confirmed_parked_active"] is False
    assert called["refs_only_state_index_pilot"] is True
    assert called["refs_only_state_index_only"] is True
    assert json.loads(captured.out)["status"] == "maintained"


def test_runtime_maintain_storage_command_dispatches_quest_root_entry(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    quest_root = tmp_path / "runtime" / "quests" / "legacy-quest"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_maintain_quest_runtime_storage(
        *,
        profile,
        quest_root: Path,
        include_worktrees: bool,
        older_than_seconds: int,
        jsonl_max_mb: int,
        text_max_mb: int,
        event_segment_max_mb: int,
        slim_jsonl_threshold_mb: int | None,
        dedupe_worktree_min_mb: int | None,
        head_lines: int,
        tail_lines: int,
        allow_live_runtime: bool,
        restore_proof_compaction: bool,
        restore_proof_buckets: tuple[str, ...],
        include_parked_controller_stop: bool,
        include_operator_confirmed_parked_active: bool,
        refs_only_state_index_pilot: bool,
        refs_only_state_index_only: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["quest_root"] = quest_root
        called["restore_proof_compaction"] = restore_proof_compaction
        called["restore_proof_buckets"] = restore_proof_buckets
        called["include_parked_controller_stop"] = include_parked_controller_stop
        called["include_operator_confirmed_parked_active"] = include_operator_confirmed_parked_active
        called["refs_only_state_index_pilot"] = refs_only_state_index_pilot
        called["refs_only_state_index_only"] = refs_only_state_index_only
        return {"status": "maintained", "quest_id": "legacy-quest"}

    monkeypatch.setattr(
        cli.runtime_storage_maintenance,
        "maintain_quest_runtime_storage",
        fake_maintain_quest_runtime_storage,
    )

    exit_code = cli.main(
        [
            "runtime",
            "maintain-storage",
            "--profile",
            str(profile_path),
            "--quest-root",
            str(quest_root),
            "--restore-proof-compaction",
            "--restore-proof-bucket",
            "runs",
            "--include-parked-controller-stop",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["quest_root"] == quest_root
    assert called["restore_proof_compaction"] is True
    assert called["restore_proof_buckets"] == ("runs",)
    assert called["include_parked_controller_stop"] is True
    assert called["include_operator_confirmed_parked_active"] is False
    assert called["refs_only_state_index_pilot"] is False
    assert called["refs_only_state_index_only"] is False
    assert json.loads(captured.out)["status"] == "maintained"


def test_runtime_storage_audit_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_audit_workspace_storage(
        *,
        profile,
        study_id: str | None,
        all_studies: bool,
        stopped_only: bool,
        apply: bool,
        git_only: bool,
        reinitialize_empty_workspace_git: bool,
        retire_workspace_root_git: bool,
        include_worktrees: bool,
        older_than_seconds: int,
        jsonl_max_mb: int,
        text_max_mb: int,
        event_segment_max_mb: int,
        slim_jsonl_threshold_mb: int | None,
        dedupe_worktree_min_mb: int | None,
        head_lines: int,
        tail_lines: int,
        allow_live_runtime: bool,
        restore_proof_compaction: bool,
        restore_proof_buckets: tuple[str, ...],
        include_parked_controller_stop: bool,
        include_operator_confirmed_parked_active: bool,
        refs_only_state_index_pilot: bool,
        refs_only_state_index_only: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_id"] = study_id
        called["all_studies"] = all_studies
        called["stopped_only"] = stopped_only
        called["apply"] = apply
        called["git_only"] = git_only
        called["reinitialize_empty_workspace_git"] = reinitialize_empty_workspace_git
        called["retire_workspace_root_git"] = retire_workspace_root_git
        called["include_worktrees"] = include_worktrees
        called["older_than_seconds"] = older_than_seconds
        called["jsonl_max_mb"] = jsonl_max_mb
        called["text_max_mb"] = text_max_mb
        called["event_segment_max_mb"] = event_segment_max_mb
        called["slim_jsonl_threshold_mb"] = slim_jsonl_threshold_mb
        called["dedupe_worktree_min_mb"] = dedupe_worktree_min_mb
        called["head_lines"] = head_lines
        called["tail_lines"] = tail_lines
        called["allow_live_runtime"] = allow_live_runtime
        called["restore_proof_compaction"] = restore_proof_compaction
        called["restore_proof_buckets"] = restore_proof_buckets
        called["include_parked_controller_stop"] = include_parked_controller_stop
        called["include_operator_confirmed_parked_active"] = include_operator_confirmed_parked_active
        called["refs_only_state_index_pilot"] = refs_only_state_index_pilot
        called["refs_only_state_index_only"] = refs_only_state_index_only
        return {"mode": "apply", "latest_report_path": "storage_audit/latest.json"}

    monkeypatch.setattr(cli.runtime_storage_maintenance, "audit_workspace_storage", fake_audit_workspace_storage)

    exit_code = cli.main(
        [
            "runtime",
            "storage-audit",
            "--profile",
            str(profile_path),
            "--git-only",
            "--apply",
            "--reinitialize-empty-workspace-git",
            "--no-worktrees",
            "--older-than-hours",
            "12",
            "--jsonl-max-mb",
            "32",
            "--text-max-mb",
            "8",
            "--event-segment-max-mb",
            "48",
            "--no-slim-oversized-jsonl",
            "--no-dedupe-worktrees",
            "--head-lines",
            "100",
            "--tail-lines",
            "120",
            "--allow-live-runtime",
            "--refs-only-state-index-pilot",
            "--refs-only-state-index-only",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_id"] is None
    assert called["all_studies"] is False
    assert called["stopped_only"] is False
    assert called["apply"] is True
    assert called["git_only"] is True
    assert called["reinitialize_empty_workspace_git"] is True
    assert called["retire_workspace_root_git"] is False
    assert called["include_worktrees"] is False
    assert called["older_than_seconds"] == 12 * 3600
    assert called["jsonl_max_mb"] == 32
    assert called["text_max_mb"] == 8
    assert called["event_segment_max_mb"] == 48
    assert called["slim_jsonl_threshold_mb"] is None
    assert called["dedupe_worktree_min_mb"] is None
    assert called["head_lines"] == 100
    assert called["tail_lines"] == 120
    assert called["allow_live_runtime"] is True
    assert called["restore_proof_compaction"] is False
    assert called["restore_proof_buckets"] == ()
    assert called["include_parked_controller_stop"] is False
    assert called["include_operator_confirmed_parked_active"] is False
    assert called["refs_only_state_index_pilot"] is True
    assert called["refs_only_state_index_only"] is True
    assert json.loads(captured.out)["latest_report_path"] == "storage_audit/latest.json"


def test_runtime_storage_audit_restore_proof_compaction_requires_explicit_apply(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_audit_workspace_storage(
        *,
        profile,
        study_id: str | None,
        all_studies: bool,
        stopped_only: bool,
        apply: bool,
        git_only: bool,
        reinitialize_empty_workspace_git: bool,
        retire_workspace_root_git: bool,
        include_worktrees: bool,
        older_than_seconds: int,
        jsonl_max_mb: int,
        text_max_mb: int,
        event_segment_max_mb: int,
        slim_jsonl_threshold_mb: int | None,
        dedupe_worktree_min_mb: int | None,
        head_lines: int,
        tail_lines: int,
        allow_live_runtime: bool,
        restore_proof_compaction: bool,
        restore_proof_buckets: tuple[str, ...],
        include_parked_controller_stop: bool,
        include_operator_confirmed_parked_active: bool,
        refs_only_state_index_pilot: bool,
        refs_only_state_index_only: bool,
    ) -> dict[str, object]:
        called["study_id"] = study_id
        called["apply"] = apply
        called["git_only"] = git_only
        called["restore_proof_compaction"] = restore_proof_compaction
        called["restore_proof_buckets"] = restore_proof_buckets
        called["include_parked_controller_stop"] = include_parked_controller_stop
        called["include_operator_confirmed_parked_active"] = include_operator_confirmed_parked_active
        called["refs_only_state_index_pilot"] = refs_only_state_index_pilot
        called["refs_only_state_index_only"] = refs_only_state_index_only
        return {"mode": "apply" if apply else "dry-run", "restore_proof_compaction": restore_proof_compaction}

    monkeypatch.setattr(cli.runtime_storage_maintenance, "audit_workspace_storage", fake_audit_workspace_storage)

    exit_code = cli.main(
        [
            "runtime",
            "storage-audit",
            "--profile",
            str(profile_path),
            "--study-id",
            "004-completed",
            "--restore-proof-compaction",
            "--restore-proof-bucket",
            "cold_archive",
            "--include-parked-controller-stop",
            "--include-operator-confirmed-parked-active",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "study_id": "004-completed",
        "apply": False,
        "git_only": False,
        "restore_proof_compaction": True,
        "restore_proof_buckets": ("cold_archive",),
        "include_parked_controller_stop": True,
        "include_operator_confirmed_parked_active": True,
        "refs_only_state_index_pilot": False,
        "refs_only_state_index_only": False,
    }
    assert json.loads(captured.out)["restore_proof_compaction"] is True


def test_runtime_storage_audit_validation_error_uses_grouped_command_usage(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["runtime", "storage-audit", "--profile", "workspace.toml", "--git-only", "--restore-proof-compaction"])
    captured = capsys.readouterr()

    assert excinfo.value.code == 2
    assert "usage: medautosci runtime storage-audit" in captured.err
    assert "workspace-storage-audit" not in captured.err
