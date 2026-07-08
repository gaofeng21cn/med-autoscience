from __future__ import annotations

import sqlite3

from tests.test_cli_cases import shared as _shared
from med_autoscience.workspace_paths import DATA_ASSET_LAYER_IDS, DATA_ASSET_REGISTRY_DIRECTORY_RELPATHS

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


DATASET_LAYER_NAMES = DATA_ASSET_LAYER_IDS
DATA_ASSET_REGISTRY_DIRS = tuple(path.as_posix() for path in DATA_ASSET_REGISTRY_DIRECTORY_RELPATHS)


def test_init_data_assets_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_init(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"private": {"release_count": 1}, "public": {"dataset_count": 0}}

    monkeypatch.setattr(cli.data_assets, "init_data_assets", fake_init)

    workspace_root = tmp_path / "workspace"
    exit_code = cli.main(["data", "init-assets", "--workspace-root", str(workspace_root)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert called["workspace_root"] == workspace_root
    assert '"release_count": 1' in captured.out
    for layer_name in DATASET_LAYER_NAMES:
        assert (workspace_root / "data" / "datasets" / layer_name).is_dir()
    for registry_dir in DATA_ASSET_REGISTRY_DIRS:
        assert (workspace_root / "memory" / "portfolio" / "data_assets" / registry_dir).is_dir()
    assert payload["layout"]["schema_version"] == 2
    assert payload["layout"]["layout_ready"] is True
    assert payload["layout"]["missing_directories"] == []
    assert payload["layout"]["body_plane"]["layer_names"] == list(DATASET_LAYER_NAMES)
    assert payload["layout"]["registry_lineage_plane"]["directory_names"] == list(DATA_ASSET_REGISTRY_DIRS)
    assert payload["layout"]["study_binding_plane"]["study_yaml_pattern"] == "studies/<study-id>/study.yaml"
    assert payload["layout"]["study_binding_plane"]["data_body_allowed"] is False


def test_init_workspace_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_init_workspace(
        *,
        workspace_root: Path,
        workspace_name: str,
        dry_run: bool,
        force: bool,
        default_publication_profile: str,
        default_citation_style: str,
        hermes_agent_repo_root: Path | None,
        hermes_home_root: Path | None,
        initialize_git: bool,
    ) -> dict:
        called["workspace_root"] = workspace_root
        called["workspace_name"] = workspace_name
        called["dry_run"] = dry_run
        called["force"] = force
        called["default_publication_profile"] = default_publication_profile
        called["default_citation_style"] = default_citation_style
        called["hermes_agent_repo_root"] = hermes_agent_repo_root
        called["hermes_home_root"] = hermes_home_root
        called["initialize_git"] = initialize_git
        return {
            "workspace_root": str(workspace_root),
            "workspace_name": workspace_name,
            "dry_run": dry_run,
            "force": force,
            "initialize_git": initialize_git,
        }

    monkeypatch.setattr(cli.workspace_init_controller, "init_workspace", fake_init_workspace)

    exit_code = cli.main(
        [
            "workspace",
            "init",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--workspace-name",
            "diabetes",
            "--dry-run",
            "--force",
            "--hermes-agent-repo-root",
            str(tmp_path / "_external" / "hermes-agent"),
            "--hermes-home-root",
            str(tmp_path / ".hermes"),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert called["workspace_name"] == "diabetes"
    assert called["dry_run"] is True
    assert called["force"] is True
    assert called["default_publication_profile"] == "general_medical_journal"
    assert called["default_citation_style"] == "AMA"
    assert called["hermes_agent_repo_root"] == tmp_path / "_external" / "hermes-agent"
    assert called["hermes_home_root"] == tmp_path / ".hermes"
    assert called["initialize_git"] is False
    assert '"workspace_name": "diabetes"' in captured.out
    assert '"initialize_git": false' in captured.out

    exit_code = cli.main(
        [
            "workspace",
            "init",
            "--workspace-root",
            str(tmp_path / "workspace-with-git"),
            "--workspace-name",
            "diabetes",
            "--with-git",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace-with-git"
    assert called["initialize_git"] is True
    assert '"initialize_git": true' in captured.out
def test_data_assets_status_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_status(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"layout_ready": True, "private": {"release_count": 2}}

    monkeypatch.setattr(cli.data_assets, "data_assets_status", fake_status)

    workspace_root = tmp_path / "workspace"
    exit_code = cli.main(["data", "assets-status", "--workspace-root", str(workspace_root)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert called["workspace_root"] == workspace_root
    assert '"layout_ready": true' in captured.out
    assert payload["layout"]["layout_ready"] is False
    assert payload["layout"]["missing_directories"]
    assert payload["layout"]["body_plane"]["layer_names"] == list(DATASET_LAYER_NAMES)
    assert payload["layout"]["registry_lineage_plane"]["directory_names"] == list(DATA_ASSET_REGISTRY_DIRS)


def test_manifest_refs_rebuild_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_rebuild(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"surface_kind": "mas_data_asset_manifest_refs_rebuild", "status": "rebuilt"}

    monkeypatch.setattr(cli.data_assets, "rebuild_manifest_refs", fake_rebuild)

    workspace_root = tmp_path / "workspace"
    exit_code = cli.main(["data", "manifest-refs-rebuild", "--workspace-root", str(workspace_root)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == workspace_root
    assert '"status": "rebuilt"' in captured.out


def test_asset_retention_plan_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_plan(
        *,
        workspace_root: Path,
        family_id: str,
        version_id: str,
        owner_authorization_ref: str | None,
        cold_ref: str | None,
        restore_proof_ref: str | None,
        apply: bool,
    ) -> dict:
        called.update(
            {
                "workspace_root": workspace_root,
                "family_id": family_id,
                "version_id": version_id,
                "owner_authorization_ref": owner_authorization_ref,
                "cold_ref": cold_ref,
                "restore_proof_ref": restore_proof_ref,
                "apply": apply,
            }
        )
        return {"surface_kind": "mas_data_asset_retention_plan", "status": "retention_receipt_recorded_no_body_delete"}

    monkeypatch.setattr(cli.data_assets, "data_asset_retention_plan", fake_plan)

    workspace_root = tmp_path / "workspace"
    exit_code = cli.main(
        [
            "data",
            "asset-retention-plan",
            "--workspace-root",
            str(workspace_root),
            "--family-id",
            "standardized_longitudinal",
            "--version-id",
            "v2026-06-01",
            "--owner-authorization-ref",
            "owner_receipts/data_asset/v2026-06-01.json",
            "--cold-ref",
            "memory/portfolio/data_assets/retention/cold_ref.json",
            "--restore-proof-ref",
            "memory/portfolio/data_assets/retention/restore_proof.json",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "workspace_root": workspace_root,
        "family_id": "standardized_longitudinal",
        "version_id": "v2026-06-01",
        "owner_authorization_ref": "owner_receipts/data_asset/v2026-06-01.json",
        "cold_ref": "memory/portfolio/data_assets/retention/cold_ref.json",
        "restore_proof_ref": "memory/portfolio/data_assets/retention/restore_proof.json",
        "apply": True,
    }
    assert '"retention_receipt_recorded_no_body_delete"' in captured.out


def test_asset_sqlite_compact_plan_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_plan(*, workspace_root: Path, db_path: Path) -> dict:
        called["workspace_root"] = workspace_root
        called["db_path"] = db_path
        return {"surface_kind": "mas_data_asset_sqlite_compact_plan", "status": "blocked"}

    monkeypatch.setattr(cli.data_assets, "data_asset_sqlite_compact_plan", fake_plan)

    workspace_root = tmp_path / "workspace"
    db_path = workspace_root / "data" / "datasets" / "master" / "v1" / "release.sqlite"
    exit_code = cli.main(
        [
            "data",
            "sqlite-compact-plan",
            "--workspace-root",
            str(workspace_root),
            "--db",
            str(db_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == workspace_root
    assert called["db_path"] == db_path
    assert '"status": "blocked"' in captured.out


def test_assess_data_asset_impact_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_assess(*, workspace_root: Path, persist_report: bool = False) -> dict:
        called["workspace_root"] = workspace_root
        called["persist_report"] = persist_report
        return {"study_count": 1, "studies": [{"study_id": "002-early-risk", "status": "review_needed"}]}

    monkeypatch.setattr(cli.data_assets, "assess_data_asset_impact", fake_assess)

    exit_code = cli.main(["data", "assess-asset-impact", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert called["persist_report"] is True
    assert '"review_needed"' in captured.out
def test_diff_private_release_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_diff(*, workspace_root: Path, family_id: str, from_version: str, to_version: str) -> dict:
        called["workspace_root"] = workspace_root
        called["family_id"] = family_id
        called["from_version"] = from_version
        called["to_version"] = to_version
        return {"report_path": "/tmp/report.json", "family_id": family_id}

    monkeypatch.setattr(cli.data_assets, "build_private_release_diff", fake_diff)

    exit_code = cli.main(
        [
            "data",
            "diff-private-release",
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--family-id",
            "master",
            "--from-version",
            "v2026-03-28",
            "--to-version",
            "v2026-04-10",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert called["family_id"] == "master"
    assert called["from_version"] == "v2026-03-28"
    assert called["to_version"] == "v2026-04-10"
    assert "/tmp/report.json" in captured.out
def test_validate_public_registry_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_validate(*, workspace_root: Path) -> dict:
        called["workspace_root"] = workspace_root
        return {"invalid_dataset_count": 0, "dataset_count": 2}

    monkeypatch.setattr(cli.data_assets, "validate_public_registry", fake_validate)

    exit_code = cli.main(["data", "validate-public-registry", "--workspace-root", str(tmp_path / "workspace")])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["workspace_root"] == tmp_path / "workspace"
    assert '"dataset_count": 2' in captured.out


def test_data_lifecycle_inspect_reports_read_only_categories_and_skips_dataset_body(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    dataset_file = workspace_root / "data" / "datasets" / "master" / "v1" / "clinical.csv"
    dataset_file.parent.mkdir(parents=True)
    dataset_file.write_text("id,value\n1,2\n", encoding="utf-8")
    (workspace_root / "runtime" / "quests" / "q1").mkdir(parents=True)
    (workspace_root / "runtime" / "quests" / "q1" / "stdout.jsonl").write_text("{}\n", encoding="utf-8")
    (workspace_root / "runtime" / "archives" / "q0").mkdir(parents=True)
    (workspace_root / "runtime" / "archives" / "q0" / "payload.tar.gz").write_text("archive", encoding="utf-8")
    (workspace_root / "studies" / "s1" / "artifacts").mkdir(parents=True)
    (workspace_root / "studies" / "s1" / "artifacts" / "table.csv").write_text("x\n", encoding="utf-8")
    (workspace_root / "memory" / "portfolio" / "data_assets" / "lineage").mkdir(parents=True)
    (workspace_root / ".pytest_cache" / "v" / "cache").mkdir(parents=True)
    (workspace_root / ".pytest_cache" / "v" / "cache" / "nodeids").write_text("[]\n", encoding="utf-8")

    exit_code = cli.main(
        [
            "data-lifecycle",
            "inspect",
            "--workspace-root",
            str(workspace_root),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "mas_data_lifecycle_inspection"
    assert payload["mutation_policy"]["read_only"] is True
    assert payload["mutation_policy"]["physical_cleanup_performed"] is False
    assert payload["management_mode"]["data_datasets"]["generic_cleanup_allowed"] is False
    assert payload["management_mode"]["data_datasets"]["reason"] == "current_clinical_data_asset_authority"
    assert "data/datasets" in payload["skipped_generic_cleanup_roots"]
    assert payload["plane_summary"]["body"]["workspace_relative_path"] == "data/datasets"
    assert payload["plane_summary"]["body"]["generic_cleanup_allowed"] is False
    assert payload["plane_summary"]["body"]["file_count"] == 1
    assert payload["plane_summary"]["body"]["bytes"] == dataset_file.stat().st_size
    assert payload["plane_summary"]["runtime"]["small_file_count"] >= 1
    assert payload["plane_summary"]["study"]["small_file_count"] >= 1
    assert set(payload["plane_summary"]) == {"body", "index", "study", "runtime", "export", "retention"}
    candidate_refs = {item["workspace_relative_path"] for item in payload["cleanup_candidates"]}
    assert "data/datasets/master/v1/clinical.csv" not in candidate_refs
    assert "runtime/quests/q1" in candidate_refs
    assert "runtime/archives/q0" in candidate_refs
    assert "studies/s1/artifacts" in candidate_refs
    assert ".pytest_cache" in candidate_refs
    categories = {item["category"] for item in payload["cleanup_candidates"]}
    assert {"runtime", "archive", "artifact", "cache"} <= categories
    for item in payload["cleanup_candidates"]:
        assert item["candidate_unit"] in {"directory", "file"}
        assert item["file_count"] >= 1
        assert item["bytes"] > 0


def test_data_lifecycle_inspect_skips_broken_archive_symlinks(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    archive_root = workspace_root / "archive" / "legacy_ops_surfaces" / "snapshot"
    archive_root.mkdir(parents=True)
    (archive_root / "deepscientist").symlink_to("med-deepscientist")
    kept_file = archive_root / "receipt.json"
    kept_file.write_text("{}\n", encoding="utf-8")
    (workspace_root / "data" / "datasets" / "master" / "v1").mkdir(parents=True)
    (workspace_root / "memory" / "portfolio" / "data_assets").mkdir(parents=True)

    exit_code = cli.main(
        [
            "data-lifecycle",
            "inspect",
            "--workspace-root",
            str(workspace_root),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "mas_data_lifecycle_inspection"
    candidate = next(
        item for item in payload["cleanup_candidates"] if item["workspace_relative_path"] == "archive/legacy_ops_surfaces"
    )
    assert candidate["category"] == "archive"
    assert candidate["file_count"] == 1
    assert candidate["bytes"] == kept_file.stat().st_size


def test_data_lifecycle_closeout_dry_run_projects_plan_without_workspace_mutation(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    cache_file = workspace_root / ".pytest_cache" / "v" / "cache" / "nodeids"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_text("[]\n", encoding="utf-8")

    exit_code = cli.main(
        [
            "data-lifecycle",
            "closeout",
            "--workspace-root",
            str(workspace_root),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert cache_file.exists()
    assert payload["surface_kind"] == "mas_data_lifecycle_closeout_plan"
    assert payload["dry_run"] is True
    assert payload["mutation_policy"]["writes_workspace"] is False
    assert payload["mutation_policy"]["physical_cleanup_performed"] is False
    assert payload["closeout_plan"]["cleanup_candidate_count"] == 1
    assert payload["closeout_plan"]["operations"][0]["category"] == "cache"
    assert payload["closeout_plan"]["operations"][0]["candidate_unit"] == "directory"
    assert payload["closeout_plan"]["operations"][0]["workspace_relative_path"] == ".pytest_cache"
    assert payload["closeout_plan"]["operations"][0]["physical_delete_performed"] is False


def test_data_lifecycle_compact_runtime_dry_run_indexes_small_runtime_files_only(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    small_runtime = workspace_root / "runtime" / "quests" / "q1" / "receipt.json"
    small_runtime.parent.mkdir(parents=True)
    small_runtime.write_text("{}\n", encoding="utf-8")
    current_package = workspace_root / "runtime" / "quests" / "q1" / "current_package.zip"
    current_package.write_bytes(b"zip")
    dataset_file = workspace_root / "data" / "datasets" / "master" / "v1" / "clinical.json"
    dataset_file.parent.mkdir(parents=True)
    dataset_file.write_text("{}\n", encoding="utf-8")

    exit_code = cli.main(
        [
            "data-lifecycle",
            "compact-runtime",
            "--workspace-root",
            str(workspace_root),
            "--dry-run",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "mas_data_lifecycle_runtime_compact_plan"
    assert payload["dry_run"] is True
    assert payload["mutation_policy"]["writes_workspace"] is False
    assert payload["target_index"] == "runtime/index.sqlite"
    candidate_refs = {candidate["workspace_relative_path"] for candidate in payload["candidates"]}
    assert "runtime/quests/q1/receipt.json" in candidate_refs
    assert "runtime/quests/q1/current_package.zip" not in candidate_refs
    assert "data/datasets/master/v1/clinical.json" not in candidate_refs
    assert "current_package.zip" in payload["forbidden_boundaries"]
    assert payload["sqlite_target_path"] == "runtime/index.sqlite"
    assert payload["estimated_benefit"]["candidate_small_file_count"] == 1
    assert "compact-runtime --workspace-root <workspace> --apply --format json" in payload["compact_plan"]["apply_command"]
    assert not (workspace_root / "runtime" / "index.sqlite").exists()


def test_data_lifecycle_compact_runtime_apply_writes_sqlite_index_without_deleting_sources(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    small_runtime = workspace_root / "runtime" / "quests" / "q1" / "receipt.json"
    small_runtime.parent.mkdir(parents=True)
    small_runtime.write_text('{"ok": true}\n', encoding="utf-8")
    current_package = workspace_root / "runtime" / "quests" / "q1" / "current_package.zip"
    current_package.write_bytes(b"zip")
    dataset_file = workspace_root / "data" / "datasets" / "master" / "v1" / "clinical.json"
    dataset_file.parent.mkdir(parents=True)
    dataset_file.write_text("{}\n", encoding="utf-8")

    exit_code = cli.main(
        [
            "data-lifecycle",
            "compact-runtime",
            "--workspace-root",
            str(workspace_root),
            "--apply",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    index_path = workspace_root / "runtime" / "index.sqlite"

    assert exit_code == 0
    assert payload["surface_kind"] == "mas_data_lifecycle_runtime_compact_plan"
    assert payload["status"] == "applied"
    assert payload["dry_run"] is False
    assert payload["mutation_policy"]["writes_runtime_index_only"] is True
    assert payload["apply_receipt"]["indexed_file_count"] == 1
    assert payload["apply_receipt"]["physical_delete_performed"] is False
    assert small_runtime.exists()
    assert current_package.exists()
    assert dataset_file.exists()
    assert index_path.exists()
    with sqlite3.connect(index_path) as connection:
        records = connection.execute(
            "SELECT workspace_relative_path, bytes, source_file_preserved FROM runtime_file_records"
        ).fetchall()
        manifest = connection.execute(
            "SELECT indexed_file_count, physical_delete_performed, source_files_preserved FROM runtime_compact_manifest"
        ).fetchone()
        payload_rows = connection.execute("SELECT bytes, payload FROM runtime_file_payloads").fetchall()

    assert records == [("runtime/quests/q1/receipt.json", small_runtime.stat().st_size, 1)]
    assert manifest == (1, 0, 1)
    assert payload_rows == [(small_runtime.stat().st_size, small_runtime.read_bytes())]


def test_data_lifecycle_compact_runtime_apply_migrates_existing_manifest_without_plane(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    small_runtime = workspace_root / "runtime" / "quests" / "q1" / "receipt.json"
    small_runtime.parent.mkdir(parents=True)
    small_runtime.write_text('{"ok": true}\n', encoding="utf-8")
    index_path = workspace_root / "runtime" / "index.sqlite"
    with sqlite3.connect(index_path) as connection:
        connection.execute(
            """
            CREATE TABLE runtime_compact_manifest (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                schema_version INTEGER NOT NULL,
                generated_at TEXT NOT NULL,
                workspace_root TEXT NOT NULL,
                small_file_threshold_bytes INTEGER NOT NULL,
                indexed_file_count INTEGER NOT NULL,
                indexed_bytes INTEGER NOT NULL,
                physical_delete_performed INTEGER NOT NULL,
                source_files_preserved INTEGER NOT NULL,
                forbidden_boundaries_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO runtime_compact_manifest (
                id,
                schema_version,
                generated_at,
                workspace_root,
                small_file_threshold_bytes,
                indexed_file_count,
                indexed_bytes,
                physical_delete_performed,
                source_files_preserved,
                forbidden_boundaries_json
            )
            VALUES (1, 1, 'old', ?, 16384, 0, 0, 0, 1, '[]')
            """,
            (str(workspace_root),),
        )

    exit_code = cli.main(
        [
            "data-lifecycle",
            "compact-runtime",
            "--workspace-root",
            str(workspace_root),
            "--apply",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "applied"
    with sqlite3.connect(index_path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(runtime_compact_manifest)")}
        manifest = connection.execute(
            "SELECT plane, indexed_file_count, physical_delete_performed FROM runtime_compact_manifest"
        ).fetchone()

    assert "plane" in columns
    assert manifest == ("runtime", 1, 0)


def test_data_lifecycle_index_assets_apply_writes_refs_only_asset_index(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    dataset_file = workspace_root / "data" / "datasets" / "master" / "v1" / "clinical.csv"
    dataset_file.parent.mkdir(parents=True)
    dataset_file.write_text("id,value\n1,2\n", encoding="utf-8")
    manifest = dataset_file.parent / "dataset_manifest.yaml"
    manifest.write_text("family_id: test\nversion_id: v1\n", encoding="utf-8")

    exit_code = cli.main(
        [
            "data-lifecycle",
            "index-assets",
            "--workspace-root",
            str(workspace_root),
            "--apply",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    index_path = workspace_root / "memory" / "portfolio" / "data_assets" / "index.sqlite"

    assert exit_code == 0
    assert payload["status"] == "applied"
    assert payload["mutation_policy"]["stores_dataset_body"] is False
    assert payload["apply_receipt"]["release_count"] == 1
    assert payload["apply_receipt"]["file_record_count"] == 2
    with sqlite3.connect(index_path) as connection:
        releases = connection.execute(
            "SELECT workspace_relative_path, manifest_exists FROM asset_releases"
        ).fetchall()
        files = connection.execute("SELECT count(*), sum(bytes) FROM asset_file_inventory").fetchone()
        manifest_row = connection.execute("SELECT stores_dataset_body FROM asset_index_manifest").fetchone()

    assert releases == [("data/datasets/master/v1", 1)]
    assert files == (2, dataset_file.stat().st_size + manifest.stat().st_size)
    assert manifest_row == (0,)


def test_data_lifecycle_compact_study_apply_writes_study_index_without_deleting_sources(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    study_note = workspace_root / "studies" / "s1" / "analysis" / "note.json"
    study_note.parent.mkdir(parents=True)
    study_note.write_text("{}\n", encoding="utf-8")

    exit_code = cli.main(
        [
            "data-lifecycle",
            "compact-study",
            "--workspace-root",
            str(workspace_root),
            "--apply",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    index_path = workspace_root / "studies" / "index.sqlite"

    assert exit_code == 0
    assert payload["status"] == "applied"
    assert payload["apply_receipt"]["indexed_file_count"] == 1
    assert study_note.exists()
    with sqlite3.connect(index_path) as connection:
        records = connection.execute(
            "SELECT workspace_relative_path, bytes, source_file_preserved FROM study_file_records"
        ).fetchall()
    assert records == [("studies/s1/analysis/note.json", study_note.stat().st_size, 1)]


def test_data_lifecycle_closeout_completed_project_apply_writes_semantic_capsule_only(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    dataset_file = workspace_root / "data" / "datasets" / "master" / "v1" / "clinical.csv"
    dataset_file.parent.mkdir(parents=True)
    dataset_file.write_text("id,value\n1,2\n", encoding="utf-8")

    exit_code = cli.main(
        [
            "data-lifecycle",
            "closeout-completed-project",
            "--workspace-root",
            str(workspace_root),
            "--project-id",
            "study_a",
            "--apply",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    capsule_path = workspace_root / payload["capsule_ref"]
    capsule_json_path = workspace_root / payload["capsule_json_ref"]

    assert exit_code == 0
    assert payload["status"] == "applied"
    assert payload["mutation_policy"]["writes_semantic_capsule_only"] is True
    assert payload["apply_receipt"]["physical_delete_performed"] is False
    assert dataset_file.exists()
    assert capsule_path.exists()
    assert capsule_json_path.exists()
    assert "Semantic Reproducible Capsule: study_a" in capsule_path.read_text(encoding="utf-8")
    capsule_json = json.loads(capsule_json_path.read_text(encoding="utf-8"))
    assert capsule_json["project_id"] == "study_a"
    assert capsule_json["mutation_policy"]["physical_delete_performed"] is False


def test_data_lifecycle_finalize_governance_apply_writes_refs_only_without_delete_or_transform(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    dataset_file = workspace_root / "data" / "datasets" / "master" / "v1" / "clinical.csv"
    dataset_file.parent.mkdir(parents=True)
    dataset_file.write_text("id,value\n1,2\n", encoding="utf-8")
    study_note = workspace_root / "studies" / "s1" / "analysis" / "note.json"
    study_note.parent.mkdir(parents=True)
    study_note.write_text("{}\n", encoding="utf-8")

    exit_code = cli.main(
        [
            "data-lifecycle",
            "finalize-governance",
            "--workspace-root",
            str(workspace_root),
            "--project-id",
            "study_a",
            "--apply",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "applied"
    assert payload["mutation_policy"]["physical_delete_performed"] is False
    assert payload["mutation_policy"]["clinical_data_transformation_performed"] is False
    assert dataset_file.exists()
    assert study_note.exists()
    assert set(payload["refs"]) == {
        "study_ttl_pin_audit",
        "owner_gated_deletion_receipt",
        "omop_like_semantic_mapping",
        "sidecar_registry",
        "ro_crate_metadata",
    }
    for ref in payload["refs"].values():
        assert (workspace_root / ref).exists()

    deletion_receipt = json.loads((workspace_root / payload["refs"]["owner_gated_deletion_receipt"]).read_text())
    semantic_mapping = json.loads((workspace_root / payload["refs"]["omop_like_semantic_mapping"]).read_text())
    sidecar_registry = json.loads((workspace_root / payload["refs"]["sidecar_registry"]).read_text())
    ro_crate = json.loads((workspace_root / payload["refs"]["ro_crate_metadata"]).read_text())

    assert deletion_receipt["status"] == "not_authorized"
    assert deletion_receipt["physical_delete_performed"] is False
    assert semantic_mapping["status"] == "mapping_manifest_only"
    assert semantic_mapping["clinical_data_transformation_performed"] is False
    assert sidecar_registry["status"] == "registry_only"
    assert sidecar_registry["clinical_data_transformation_performed"] is False
    assert ro_crate["status"] == "metadata_only"


def test_data_lifecycle_inspect_classifies_current_package_zip_as_exchange(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    package_zip = workspace_root / "manuscript" / "current_package.zip"
    package_zip.parent.mkdir(parents=True)
    package_zip.write_bytes(b"zip")

    exit_code = cli.main(
        [
            "data-lifecycle",
            "inspect",
            "--workspace-root",
            str(workspace_root),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    package_candidate = next(
        candidate
        for candidate in payload["cleanup_candidates"]
        if candidate["workspace_relative_path"] == "manuscript/current_package.zip"
    )
    assert package_candidate["category"] == "exchange"
    assert package_candidate["candidate_action"] == "retain_as_human_facing_exchange_surface"
