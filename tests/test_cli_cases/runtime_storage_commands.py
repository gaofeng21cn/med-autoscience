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
        include_parked_controller_stop: bool,
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
        called["include_parked_controller_stop"] = include_parked_controller_stop
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
    assert called["include_parked_controller_stop"] is False
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
        include_parked_controller_stop: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_id"] = study_id
        called["all_studies"] = all_studies
        called["stopped_only"] = stopped_only
        called["apply"] = apply
        called["git_only"] = git_only
        called["reinitialize_empty_workspace_git"] = reinitialize_empty_workspace_git
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
        called["include_parked_controller_stop"] = include_parked_controller_stop
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
    assert called["include_parked_controller_stop"] is False
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
        include_parked_controller_stop: bool,
    ) -> dict[str, object]:
        called["study_id"] = study_id
        called["apply"] = apply
        called["git_only"] = git_only
        called["restore_proof_compaction"] = restore_proof_compaction
        called["include_parked_controller_stop"] = include_parked_controller_stop
        return {"mode": "apply", "restore_proof_compaction": restore_proof_compaction}

    monkeypatch.setattr(cli.runtime_storage_maintenance, "audit_workspace_storage", fake_audit_workspace_storage)

    exit_code = cli.main(
        [
            "runtime",
            "storage-audit",
            "--profile",
            str(profile_path),
            "--study-id",
            "004-completed",
            "--apply",
            "--restore-proof-compaction",
            "--include-parked-controller-stop",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "study_id": "004-completed",
        "apply": True,
        "git_only": False,
        "restore_proof_compaction": True,
        "include_parked_controller_stop": True,
    }
    assert json.loads(captured.out)["restore_proof_compaction"] is True


def test_runtime_lifecycle_export_command_dispatches_read_model(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    output_path = tmp_path / "exports" / "watch.md"
    called: dict[str, object] = {}

    def fake_export_compatibility_projection(
        *,
        surface: str,
        export_format: str,
        quest_root: Path | None,
        workspace_root: Path | None,
        report_group: str,
        output_path: Path | None,
        db_path: Path | None,
    ) -> dict[str, object]:
        called["surface"] = surface
        called["export_format"] = export_format
        called["quest_root"] = quest_root
        called["workspace_root"] = workspace_root
        called["report_group"] = report_group
        called["output_path"] = output_path
        called["db_path"] = db_path
        return {
            "surface_kind": "runtime_lifecycle_compatibility_export",
            "compatibility_fallback_used": False,
            "output_path": str(output_path),
        }

    monkeypatch.setattr(
        cli.runtime_lifecycle_read_model,
        "export_compatibility_projection",
        fake_export_compatibility_projection,
    )

    exit_code = cli.main(
        [
            "runtime",
            "lifecycle-export",
            "--quest-root",
            str(quest_root),
            "--surface",
            "runtime_report",
            "--format",
            "markdown",
            "--report-group",
            "runtime_watch",
            "--output-path",
            str(output_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "surface": "runtime_report",
        "export_format": "markdown",
        "quest_root": quest_root,
        "workspace_root": None,
        "report_group": "runtime_watch",
        "output_path": output_path,
        "db_path": None,
    }
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "runtime_lifecycle_compatibility_export"
    assert payload["compatibility_fallback_used"] is False


def test_runtime_lifecycle_inventory_command_is_read_only(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    called: dict[str, object] = {}

    def fake_build_lifecycle_inventory(
        *,
        quest_root: Path | None,
        workspace_root: Path | None,
        db_path: Path | None,
    ) -> dict[str, object]:
        called["quest_root"] = quest_root
        called["workspace_root"] = workspace_root
        called["db_path"] = db_path
        return {
            "surface_kind": "runtime_lifecycle_compatibility_read_model",
            "mode": "inventory",
            "status": "missing",
            "read_only": True,
            "compatibility_fallback_used": True,
        }

    monkeypatch.setattr(cli.runtime_lifecycle_read_model, "build_lifecycle_inventory", fake_build_lifecycle_inventory)

    exit_code = cli.main(["runtime", "lifecycle-inventory", "--workspace-root", str(workspace_root)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {"quest_root": None, "workspace_root": workspace_root, "db_path": None}
    payload = json.loads(captured.out)
    assert payload["read_only"] is True
    assert payload["compatibility_fallback_used"] is True
