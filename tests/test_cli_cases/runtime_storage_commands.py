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
    assert called["restore_proof_buckets"] == ()
    assert called["include_parked_controller_stop"] is False
    assert called["include_operator_confirmed_parked_active"] is False
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
    ) -> dict[str, object]:
        called["profile"] = profile
        called["quest_root"] = quest_root
        called["restore_proof_compaction"] = restore_proof_compaction
        called["restore_proof_buckets"] = restore_proof_buckets
        called["include_parked_controller_stop"] = include_parked_controller_stop
        called["include_operator_confirmed_parked_active"] = include_operator_confirmed_parked_active
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
    ) -> dict[str, object]:
        called["study_id"] = study_id
        called["apply"] = apply
        called["git_only"] = git_only
        called["restore_proof_compaction"] = restore_proof_compaction
        called["restore_proof_buckets"] = restore_proof_buckets
        called["include_parked_controller_stop"] = include_parked_controller_stop
        called["include_operator_confirmed_parked_active"] = include_operator_confirmed_parked_active
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


def test_runtime_lifecycle_export_command_dispatches_read_model(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    output_path = tmp_path / "exports" / "watch.md"
    called: dict[str, object] = {}

    def fake_export_lifecycle_projection(
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
            "surface_kind": "runtime_lifecycle_export",
            "legacy_restore_import_used": False,
            "output_path": str(output_path),
        }

    monkeypatch.setattr(
        cli.runtime_lifecycle_read_model,
        "export_lifecycle_projection",
        fake_export_lifecycle_projection,
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
            "domain_health_diagnostic",
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
        "report_group": "domain_health_diagnostic",
        "output_path": output_path,
        "db_path": None,
    }
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "runtime_lifecycle_export"
    assert payload["legacy_restore_import_used"] is False


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
            "surface_kind": "runtime_lifecycle_read_model",
            "mode": "inventory",
            "status": "missing",
            "read_only": True,
            "legacy_restore_import_used": False,
        }

    monkeypatch.setattr(cli.runtime_lifecycle_read_model, "build_lifecycle_inventory", fake_build_lifecycle_inventory)

    exit_code = cli.main(["runtime", "lifecycle-inventory", "--workspace-root", str(workspace_root)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {"quest_root": None, "workspace_root": workspace_root, "db_path": None}
    payload = json.loads(captured.out)
    assert payload["read_only"] is True
    assert payload["legacy_restore_import_used"] is False


def test_runtime_lifecycle_inventory_command_can_output_quest_git_inventory(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    called: dict[str, object] = {}

    def fake_build_quest_git_inventory(*, workspace_root: Path) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        return {
            "surface_kind": "quest_git_inventory",
            "workspace_root": str(workspace_root),
            "items": [
                {
                    "quest_id": "quest-001",
                    "active_path": str(workspace_root / "runtime" / "quests" / "quest-001"),
                    "git_path": str(workspace_root / "runtime" / "quests" / "quest-001" / ".git"),
                    "quest_git_present_in_active_path": True,
                    "quest_git_active_path_retired": False,
                    "status": "pending",
                    "skipped_reason": "active_quest_git_present",
                }
            ],
        }

    monkeypatch.setattr(cli.runtime_lifecycle_migration, "build_quest_git_inventory", fake_build_quest_git_inventory)

    exit_code = cli.main(["runtime", "lifecycle-inventory", "--workspace-root", str(workspace_root), "--quest-git"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {"workspace_root": workspace_root}
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "quest_git_inventory"
    assert payload["items"][0]["status"] == "pending"


def test_runtime_lifecycle_ledger_command_outputs_auto_quest_git_inventory(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    (workspace_root / ".gitignore").write_text("*.sqlite\n*.sqlite-wal\n*.sqlite-shm\n", encoding="utf-8")
    quest_git = workspace_root / "runtime" / "quests" / "quest-active" / ".git"
    quest_git.mkdir(parents=True)

    exit_code = cli.main(
        [
            "runtime",
            "lifecycle-ledger",
            "--workspace-root",
            str(workspace_root),
            "--mode",
            "verify",
            "--workspace-classification",
            "parked_controller_stop",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    cutover = payload["git_lifecycle_cutover"]
    assert cutover["status"] == "pending"
    assert cutover["quest_git_inventory"][0]["quest_id"] == "quest-active"
    assert cutover["quest_git_inventory"][0]["active_path"] == str(quest_git.parent)
    assert cutover["quest_git_inventory"][0]["git_path"] == str(quest_git)


def test_runtime_lifecycle_quest_git_cutover_command_dispatches_safe_cutover(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    output_root = tmp_path / "out"
    called: dict[str, object] = {}

    def fake_cutover_quest_git_active_paths(
        *,
        workspace_root: Path,
        mode: str,
        migration_run_id: str | None,
        output_root: Path | None,
    ) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        called["mode"] = mode
        called["migration_run_id"] = migration_run_id
        called["output_root"] = output_root
        return {
            "surface_kind": "quest_git_active_path_cutover",
            "status": "pending",
            "summary": {"planned_count": 1, "skipped_count": 0},
        }

    monkeypatch.setattr(
        cli.runtime_lifecycle_migration,
        "cutover_quest_git_active_paths",
        fake_cutover_quest_git_active_paths,
    )

    exit_code = cli.main(
        [
            "runtime",
            "lifecycle-quest-git-cutover",
            "--workspace-root",
            str(workspace_root),
            "--mode",
            "dry_run",
            "--migration-run-id",
            "run-001",
            "--output-root",
            str(output_root),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "workspace_root": workspace_root,
        "mode": "dry_run",
        "migration_run_id": "run-001",
        "output_root": output_root,
    }
    assert json.loads(captured.out)["surface_kind"] == "quest_git_active_path_cutover"


def test_runtime_lifecycle_ledger_command_reads_latest_quest_git_cutover_record(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    quest_git = workspace_root / "runtime" / "quests" / "quest-stopped" / ".git"
    quest_git.mkdir(parents=True)
    (quest_git / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (quest_git.parent / ".ds").mkdir()
    (quest_git.parent / ".ds" / "runtime_state.json").write_text(
        json.dumps({"status": "stopped", "active_run_id": None, "worker_running": False}),
        encoding="utf-8",
    )

    cutover_exit = cli.main(
        [
            "runtime",
            "lifecycle-quest-git-cutover",
            "--workspace-root",
            str(workspace_root),
            "--mode",
            "apply",
            "--migration-run-id",
            "quest-git-cutover-cli-test",
        ]
    )
    capsys.readouterr()

    ledger_exit = cli.main(
        [
            "runtime",
            "lifecycle-ledger",
            "--workspace-root",
            str(workspace_root),
            "--mode",
            "verify",
            "--workspace-classification",
            "stopped_cold",
        ]
    )
    captured = capsys.readouterr()

    assert cutover_exit == 0
    assert ledger_exit == 0
    payload = json.loads(captured.out)
    assert payload["git_lifecycle_cutover"]["status"] == "verified"
    assert payload["git_lifecycle_cutover"]["quest_git_inventory"][0]["quest_id"] == "quest-stopped"
    assert payload["quest_git_cutover_record"]["migration_run_id"] == "quest-git-cutover-cli-test"


def test_runtime_lifecycle_read_accepts_sqlite_only_surface(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    called: dict[str, object] = {}

    def fake_read_lifecycle_projection(
        *,
        surface: str,
        report_group: str,
        quest_root: Path | None,
        workspace_root: Path | None,
        db_path: Path | None,
    ) -> dict[str, object]:
        called["surface"] = surface
        called["report_group"] = report_group
        called["quest_root"] = quest_root
        called["workspace_root"] = workspace_root
        called["db_path"] = db_path
        return {
            "surface_kind": "runtime_lifecycle_read_model",
            "surface": surface,
            "legacy_restore_import_used": False,
        }

    monkeypatch.setattr(
        cli.runtime_lifecycle_read_model,
        "read_lifecycle_projection",
        fake_read_lifecycle_projection,
    )

    exit_code = cli.main(
        [
            "runtime",
            "lifecycle-read",
            "--workspace-root",
            str(workspace_root),
            "--surface",
            "lineage_route",
            "--report-group",
            "domain_health_diagnostic",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "surface": "lineage_route",
        "report_group": "domain_health_diagnostic",
        "quest_root": None,
        "workspace_root": workspace_root,
        "db_path": None,
    }
    payload = json.loads(captured.out)
    assert payload["surface"] == "lineage_route"
    assert payload["legacy_restore_import_used"] is False


def test_runtime_lifecycle_read_rejects_legacy_restore_import_diagnostic_flag(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    def fake_read_lifecycle_projection(
        *,
        surface: str,
        report_group: str,
        quest_root: Path | None,
        workspace_root: Path | None,
        db_path: Path | None,
    ) -> dict[str, object]:
        return {
            "surface_kind": "runtime_lifecycle_read_model",
            "surface": surface,
            "legacy_restore_import_used": False,
        }

    monkeypatch.setattr(
        cli.runtime_lifecycle_read_model,
        "read_lifecycle_projection",
        fake_read_lifecycle_projection,
    )

    retired_flag = "--legacy" + "-restore-import-diagnostic"
    with pytest.raises(SystemExit):
        cli.main(
            [
                "runtime",
                "lifecycle-read",
                "--quest-root",
                str(quest_root),
                "--surface",
                "runtime_report",
                retired_flag,
            ]
        )
    captured = capsys.readouterr()

    assert retired_flag in captured.err


def test_runtime_quest_materialize_command_dispatches_plain_directory_materializer(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    called: dict[str, object] = {}

    def fake_materialize_quest_workspace(
        *,
        workspace_root: Path,
        quest_id: str,
        node_id: str,
        mode: str,
    ) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        called["quest_id"] = quest_id
        called["node_id"] = node_id
        called["mode"] = mode
        return {
            "schema_version": 1,
            "status": "materialized",
            "action": "create_plain_directory",
            "manifest_path": str(workspace_root / "runtime" / "quests" / quest_id / "artifacts" / "runtime" / "materialization_manifest.json"),
        }

    monkeypatch.setattr(cli.quest_materializer, "materialize_quest_workspace", fake_materialize_quest_workspace)

    exit_code = cli.main(
        [
            "runtime",
            "quest-materialize",
            "--workspace-root",
            str(workspace_root),
            "--quest-id",
            "quest-001",
            "--node-id",
            "node-001",
            "--mode",
            "apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "workspace_root": workspace_root,
        "quest_id": "quest-001",
        "node_id": "node-001",
        "mode": "apply",
    }
    payload = json.loads(captured.out)
    assert payload["status"] == "materialized"
    assert payload["action"] == "create_plain_directory"
