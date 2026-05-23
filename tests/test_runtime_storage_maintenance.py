from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import sqlite3
import time

import pytest

from tests.study_runtime_test_helpers import make_profile


def _write_fake_mds_repo(repo_root: Path) -> None:
    script_path = repo_root / "scripts" / "maintain_quest_runtime_storage.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "from __future__ import annotations",
                "import json",
                "import os",
                "import sys",
                "from pathlib import Path",
                "",
                "quest_root = Path(sys.argv[1]).expanduser().resolve()",
                "print(json.dumps({",
                '    "status": "ok",',
                '    "quest_root": str(quest_root),',
                '    "argv": sys.argv[1:],',
                '    "pythonpath": os.environ.get("PYTHONPATH", ""),',
                '    "roots": [],',
                "}, ensure_ascii=False))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    os.chmod(script_path, 0o755)


def _write_study(study_root: Path, *, study_id: str, quest_id: str) -> None:
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(
        "\n".join(
            [
                f"study_id: {study_id}",
                "title: Runtime storage maintenance study",
                "execution:",
                f"  quest_id: {quest_id}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (study_root / "runtime_binding.yaml").write_text(
        "\n".join(
            [
                "schema_version: 1",
                f"study_id: {study_id}",
                f"quest_id: {quest_id}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_quest(quest_root: Path, *, quest_id: str, status: str, active_run_id: str | None = None) -> None:
    quest_root.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\n", encoding="utf-8")
    runtime_state = {"quest_id": quest_id, "status": status, "active_run_id": active_run_id}
    ds_root = quest_root / ".ds"
    ds_root.mkdir(parents=True, exist_ok=True)
    (ds_root / "runtime_state.json").write_text(json.dumps(runtime_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_dataset_release(
    workspace_root: Path,
    *,
    family_id: str,
    version_id: str,
    dataset_id: str,
    supersedes_versions: list[str] | None = None,
    restore_handle: str | None = None,
    restore_index_path: str | None = None,
    checksum: str | None = None,
    rehydrate_verified: bool = False,
) -> Path:
    release_root = workspace_root / "datasets" / family_id / version_id
    release_root.mkdir(parents=True, exist_ok=True)
    (release_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    source_lines = ["source_release:"]
    if restore_handle:
        source_lines.append(f"  restore_handle: {restore_handle}")
    if restore_index_path:
        source_lines.append(f"  restore_index_path: {restore_index_path}")
    if checksum:
        source_lines.append(f"  sha256: {checksum}")
    if rehydrate_verified:
        source_lines.extend(
            [
                "  rehydrate_verification:",
                "    status: verified",
            ]
        )
    supersedes_lines = []
    if supersedes_versions is not None:
        supersedes_lines.append("supersedes_versions:")
        supersedes_lines.extend(f"- {version}" for version in supersedes_versions)
    (release_root / "dataset_manifest.yaml").write_text(
        "\n".join(
            [
                f"dataset_id: {dataset_id}",
                f"version: {version_id}",
                "main_outputs:",
                "  analysis_csv: analysis.csv",
                *source_lines,
                *supersedes_lines,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return release_root


def test_maintain_runtime_storage_runs_backend_and_writes_audit_report(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    _write_fake_mds_repo(profile.med_deepscientist_repo_root)

    study_id = "001-risk"
    quest_id = "quest-001"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_study(study_root, study_id=study_id, quest_id=quest_id)
    _write_quest(quest_root, quest_id=quest_id, status="stopped")
    hot_bucket = quest_root / ".ds" / "bash_exec" / "bash-001"
    hot_bucket.mkdir(parents=True, exist_ok=True)
    (hot_bucket / "terminal.log").write_text("runtime log\n", encoding="utf-8")

    result = module.maintain_runtime_storage(
        profile=profile,
        study_id=study_id,
        study_root=None,
    )

    assert result["status"] == "maintained"
    assert result["study_id"] == study_id
    assert result["quest_id"] == quest_id
    assert result["quest_root"] == str(quest_root.resolve())
    assert result["quest_runtime_before"]["status"] == "stopped"
    assert result["quest_runtime_after"]["status"] == "stopped"
    assert result["size_before"]["buckets"]["bash_exec"]["bytes"] > 0
    assert str((profile.med_deepscientist_repo_root / "src").resolve()) in result["maintenance"]["pythonpath"]
    assert result["maintenance"]["quest_root"] == str(quest_root.resolve())
    latest_report_path = Path(result["latest_report_path"])
    report_path = Path(result["report_path"])
    assert latest_report_path.is_file()
    assert report_path.is_file()
    latest_payload = json.loads(latest_report_path.read_text(encoding="utf-8"))
    assert latest_payload["status"] == "maintained"
    assert latest_payload["quest_id"] == quest_id


def test_maintain_runtime_storage_blocks_live_runtime_without_override(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)

    study_id = "002-risk"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / study_id
    _write_study(study_root, study_id=study_id, quest_id=study_id)
    _write_quest(quest_root, quest_id=study_id, status="running", active_run_id="run-live")

    result = module.maintain_runtime_storage(
        profile=profile,
        study_id=study_id,
        study_root=None,
    )

    assert result["status"] == "blocked_live_runtime"
    assert result["quest_id"] == study_id
    assert result["quest_runtime_before"]["status"] == "running"
    assert result["quest_runtime_before"]["active_run_id"] == "run-live"


def test_audit_workspace_storage_dry_run_reports_runtime_dataset_cache_and_git(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)

    live_study_id = "002-live"
    stopped_study_id = "004-stopped"
    _write_study(profile.studies_root / live_study_id, study_id=live_study_id, quest_id=live_study_id)
    _write_study(profile.studies_root / stopped_study_id, study_id=stopped_study_id, quest_id=stopped_study_id)
    _write_quest(profile.runtime_root / live_study_id, quest_id=live_study_id, status="running", active_run_id="run-live")
    _write_quest(profile.runtime_root / stopped_study_id, quest_id=stopped_study_id, status="stopped")
    (profile.runtime_root / stopped_study_id / ".ds" / "runs" / "run-001").mkdir(parents=True, exist_ok=True)
    (profile.runtime_root / stopped_study_id / ".ds" / "runs" / "run-001" / "stdout.jsonl").write_text(
        '{"line":"stdout"}\n',
        encoding="utf-8",
    )
    (profile.workspace_root / ".venv" / "bin").mkdir(parents=True, exist_ok=True)
    (profile.workspace_root / ".venv" / "bin" / "python").write_text("python\n", encoding="utf-8")
    (profile.workspace_root / ".git" / "objects" / "pack").mkdir(parents=True, exist_ok=True)
    tmp_pack = profile.workspace_root / ".git" / "objects" / "pack" / "tmp_pack_001"
    tmp_pack.write_text("pack\n", encoding="utf-8")
    stale_mtime = time.time() - 7 * 3600
    os.utime(tmp_pack, (stale_mtime, stale_mtime))
    _write_dataset_release(
        profile.workspace_root,
        family_id="master",
        version_id="v1",
        dataset_id="dm_master",
        restore_index_path="datasets/master/v1/restore_index.json",
        checksum="abc123",
        rehydrate_verified=True,
    )
    _write_dataset_release(
        profile.workspace_root,
        family_id="master",
        version_id="v2",
        dataset_id="dm_master",
        supersedes_versions=["v1"],
    )

    result = module.audit_workspace_storage(profile=profile, all_studies=True, apply=False)

    assert result["mode"] == "dry-run"
    assert result["summary"]["study_count"] == 2
    runtime_studies = result["categories"]["runtime"]["studies"]
    live_report = next(item for item in runtime_studies if item["study_id"] == live_study_id)
    stopped_report = next(item for item in runtime_studies if item["study_id"] == stopped_study_id)
    assert live_report["runtime"]["candidate_action"] == "audit-only"
    assert live_report["runtime"]["blockers"] == ["live_runtime_active"]
    assert stopped_report["runtime"]["candidate_action"] == "compress-online"
    assert stopped_report["artifact_lifecycle_registry"]["surface_kind"] == (
        "workspace_study_artifact_lifecycle_registry"
    )
    runtime_artifacts = stopped_report["artifact_lifecycle_registry"]["artifacts"]
    runtime_artifact = next(item for item in runtime_artifacts if item["path"].endswith("stdout.jsonl"))
    assert runtime_artifact["role"] == "runtime_ephemeral"
    assert runtime_artifact["cleanup_candidate_action"] == "archive-compress"
    dataset_releases = result["categories"]["dataset"]["releases"]
    v1_report = next(item for item in dataset_releases if item["version_id"] == "v1")
    v2_report = next(item for item in dataset_releases if item["version_id"] == "v2")
    assert v1_report["candidate_action"] == "archive-offline"
    assert v2_report["candidate_action"] == "keep-online"
    assert result["categories"]["cache"]["estimated_release_bytes"] > 0
    assert result["categories"]["git"]["tmp_pack_files"]
    assert result["categories"]["git"]["estimated_release_bytes"] > 0
    latest_report_path = profile.workspace_root / "storage_audit" / "latest.json"
    assert latest_report_path.is_file()
    assert json.loads(latest_report_path.read_text(encoding="utf-8"))["mode"] == "dry-run"


def test_audit_workspace_storage_blocks_superseded_dataset_without_restore_index(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    _write_dataset_release(
        profile.workspace_root,
        family_id="master",
        version_id="v1",
        dataset_id="dm_master",
    )
    _write_dataset_release(
        profile.workspace_root,
        family_id="master",
        version_id="v2",
        dataset_id="dm_master",
        supersedes_versions=["v1"],
    )

    result = module.audit_workspace_storage(profile=profile, all_studies=True, apply=False)

    v1_report = next(item for item in result["categories"]["dataset"]["releases"] if item["version_id"] == "v1")
    assert v1_report["candidate_action"] == "blocked"
    assert v1_report["blockers"] == [
        "missing_restore_index",
        "missing_checksum",
        "missing_rehydrate_verification",
    ]


def test_audit_workspace_storage_apply_runs_stopped_studies_and_blocks_live_runtime(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    _write_fake_mds_repo(profile.med_deepscientist_repo_root)

    live_study_id = "002-live"
    stopped_study_id = "004-stopped"
    _write_study(profile.studies_root / live_study_id, study_id=live_study_id, quest_id=live_study_id)
    _write_study(profile.studies_root / stopped_study_id, study_id=stopped_study_id, quest_id=stopped_study_id)
    _write_quest(profile.runtime_root / live_study_id, quest_id=live_study_id, status="running", active_run_id="run-live")
    _write_quest(profile.runtime_root / stopped_study_id, quest_id=stopped_study_id, status="stopped")

    result = module.audit_workspace_storage(profile=profile, all_studies=True, apply=True)

    runtime_studies = result["categories"]["runtime"]["studies"]
    live_report = next(item for item in runtime_studies if item["study_id"] == live_study_id)
    stopped_report = next(item for item in runtime_studies if item["study_id"] == stopped_study_id)
    assert live_report["apply_result"]["status"] == "blocked_live_runtime"
    assert stopped_report["status"] == "applied"
    assert stopped_report["apply_result"]["status"] == "maintained"
    assert (profile.studies_root / stopped_study_id / "artifacts" / "runtime" / "runtime_storage_maintenance" / "latest.json").is_file()


def test_audit_workspace_storage_apply_deletes_rebuildable_cache_candidates(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    cache_dir = profile.workspace_root / ".pytest_cache" / "v"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "cache.bin"
    cache_file.write_text("cache payload\n", encoding="utf-8")
    pycache_dir = profile.workspace_root / "src" / "pkg" / "__pycache__"
    pycache_dir.mkdir(parents=True, exist_ok=True)
    pyc_file = pycache_dir / "module.cpython-312.pyc"
    pyc_file.write_bytes(b"compiled")
    ds_store = profile.workspace_root / ".DS_Store"
    ds_store.write_text("finder\n", encoding="utf-8")
    expected_deleted_bytes = cache_file.stat().st_size + pyc_file.stat().st_size + ds_store.stat().st_size

    result = module.audit_workspace_storage(profile=profile, all_studies=False, apply=True)

    cache_report = result["categories"]["cache"]
    assert cache_report["estimated_release_bytes"] == expected_deleted_bytes
    assert cache_report["actual_release_bytes"] == expected_deleted_bytes
    assert cache_report["deleted_count"] == 3
    assert cache_report["deleted_bytes"] == expected_deleted_bytes
    assert cache_report["skipped"] == []
    assert cache_report["errors"] == []
    assert cache_report["apply_result"]["status"] == "deleted"
    assert result["summary"]["estimated_release_bytes"] == expected_deleted_bytes
    assert result["summary"]["actual_release_bytes"] == expected_deleted_bytes
    assert not (profile.workspace_root / ".pytest_cache").exists()
    assert not pycache_dir.exists()
    assert not ds_store.exists()


def test_audit_workspace_storage_study_id_scopes_cache_candidates_to_selected_study(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    _write_fake_mds_repo(profile.med_deepscientist_repo_root)
    selected_study_id = "004-stopped"
    live_study_id = "002-live"
    _write_study(profile.studies_root / selected_study_id, study_id=selected_study_id, quest_id=selected_study_id)
    _write_study(profile.studies_root / live_study_id, study_id=live_study_id, quest_id=live_study_id)
    _write_quest(profile.runtime_root / selected_study_id, quest_id=selected_study_id, status="stopped")
    _write_quest(profile.runtime_root / live_study_id, quest_id=live_study_id, status="running", active_run_id="run-live")

    selected_study_cache = profile.studies_root / selected_study_id / ".cache" / "study.bin"
    selected_quest_cache = profile.runtime_root / selected_study_id / ".ds" / "cache" / "quest.bin"
    live_study_cache = profile.studies_root / live_study_id / ".cache" / "study.bin"
    live_quest_cache = profile.runtime_root / live_study_id / ".ds" / "cache" / "quest.bin"
    workspace_cache = profile.workspace_root / ".pytest_cache" / "workspace.bin"
    for path in (selected_study_cache, selected_quest_cache, live_study_cache, live_quest_cache, workspace_cache):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{path.name}\n", encoding="utf-8")
    expected_selected_bytes = selected_study_cache.stat().st_size + selected_quest_cache.stat().st_size

    dry_run = module.audit_workspace_storage(profile=profile, study_id=selected_study_id, all_studies=False, apply=False)

    dry_run_candidate_paths = {Path(item["path"]) for item in dry_run["categories"]["cache"]["candidates"]}
    assert dry_run["categories"]["cache"]["estimated_release_bytes"] == expected_selected_bytes
    assert dry_run_candidate_paths == {selected_study_cache.parent, selected_quest_cache.parent}
    assert live_study_cache.exists()
    assert live_quest_cache.exists()
    assert workspace_cache.exists()

    result = module.audit_workspace_storage(profile=profile, study_id=selected_study_id, all_studies=False, apply=True)

    cache_report = result["categories"]["cache"]
    apply_deleted_paths = {Path(path) for path in cache_report["apply_result"]["deleted_paths"]}
    assert cache_report["estimated_release_bytes"] == expected_selected_bytes
    assert cache_report["actual_release_bytes"] == expected_selected_bytes
    assert apply_deleted_paths == {selected_study_cache.parent, selected_quest_cache.parent}
    assert not selected_study_cache.parent.exists()
    assert not selected_quest_cache.parent.exists()
    assert live_study_cache.exists()
    assert live_quest_cache.exists()
    assert workspace_cache.exists()


def test_audit_workspace_storage_git_only_does_not_scan_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)

    def fail_cache_scan(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("cache scan should not run for --git-only")

    monkeypatch.setattr(module, "_delete_safe_candidates", fail_cache_scan)

    result = module.audit_workspace_storage(profile=profile, all_studies=False, apply=True, git_only=True)

    assert result["categories"]["cache"]["candidate_action"] == "skipped-git_only"
    assert result["summary"]["cache_actual_release_bytes"] == 0


def test_audit_workspace_storage_apply_uses_actual_runtime_release_for_estimate(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    _write_fake_mds_repo(profile.med_deepscientist_repo_root)
    study_id = "004-stopped"
    _write_study(profile.studies_root / study_id, study_id=study_id, quest_id=study_id)
    _write_quest(profile.runtime_root / study_id, quest_id=study_id, status="stopped")
    run_log = profile.runtime_root / study_id / ".ds" / "runs" / "run-001" / "stdout.jsonl"
    run_log.parent.mkdir(parents=True, exist_ok=True)
    run_log.write_text('{"line":"stdout"}\n', encoding="utf-8")

    result = module.audit_workspace_storage(profile=profile, all_studies=True, apply=True)

    runtime_category = result["categories"]["runtime"]
    study_report = runtime_category["studies"][0]
    assert runtime_category["estimated_release_bytes"] == 0
    assert runtime_category["actual_release_bytes"] == 0
    assert runtime_category["actual_runtime_release_bytes"] == 0
    assert result["summary"]["estimated_release_bytes"] == 0
    assert result["summary"]["actual_release_bytes"] == 0
    assert result["summary"]["runtime_estimated_release_bytes"] == 0
    assert result["summary"]["runtime_actual_release_bytes"] == 0
    assert study_report["runtime"]["estimated_release_bytes"] == 0
    assert study_report["actual_runtime_release_bytes"] == 0


def test_audit_workspace_storage_restore_proof_compaction_archives_and_prunes_cold_runtime_buckets(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "004-completed"
    _write_study(profile.studies_root / study_id, study_id=study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    _write_quest(quest_root, quest_id=study_id, status="completed")
    payload_paths = [
        *(quest_root / ".ds" / "runs" / f"run-{index:03d}" / "stdout.jsonl" for index in range(12)),
        *(quest_root / ".ds" / "bash_exec" / f"bash-{index:03d}" / "terminal.log" for index in range(12)),
        *(quest_root / ".ds" / "codex_history" / f"events-{index:03d}.jsonl" for index in range(12)),
    ]
    for path in payload_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(("runtime payload\n" * 4096), encoding="utf-8")
    file_count_before = sum(1 for path in (quest_root / ".ds").rglob("*") if path.is_file())

    result = module.audit_workspace_storage(
        profile=profile,
        study_id=study_id,
        all_studies=False,
        apply=True,
        restore_proof_compaction=True,
    )

    study_report = result["categories"]["runtime"]["studies"][0]
    compaction = study_report["apply_result"]["restore_proof_compaction"]
    assert study_report["status"] == "applied"
    assert compaction["status"] == "compacted"
    assert compaction["restore_proof"]["status"] == "verified"
    assert compaction["files_before"] == len(payload_paths)
    assert study_report["runtime"]["candidate_action"] == "restore-proof-compaction"
    assert study_report["actual_runtime_release_bytes"] > 0
    assert result["summary"]["actual_release_bytes"] >= study_report["actual_runtime_release_bytes"]
    assert not (quest_root / ".ds" / "runs").exists()
    assert not (quest_root / ".ds" / "bash_exec").exists()
    assert not (quest_root / ".ds" / "codex_history").exists()
    assert Path(compaction["archive_ref"]["archive_path"]).is_file()
    assert Path(compaction["source_manifest_path"]).is_file()
    assert Path(compaction["restore_proof_path"]).is_file()
    assert sum(1 for path in (quest_root / ".ds").rglob("*") if path.is_file()) < file_count_before

    db_path = quest_root / "artifacts" / "runtime" / "domain_authority_refs.sqlite"
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT archive_id, archive_path, restore_proof_path, payload_json FROM archive_refs WHERE quest_root = ?",
            (str(quest_root.resolve()),),
        ).fetchone()
    assert row is not None
    assert row[0] == compaction["archive_ref"]["archive_id"]
    assert row[1] == compaction["archive_ref"]["archive_path"]
    assert row[2] == compaction["restore_proof_path"]
    assert json.loads(row[3])["sha256"] == compaction["archive_ref"]["sha256"]
    workspace_db_path = profile.workspace_root / "artifacts" / "runtime" / "domain_authority_refs.sqlite"
    with sqlite3.connect(workspace_db_path) as conn:
        workspace_row = conn.execute(
            "SELECT archive_id, archive_path, restore_proof_path, payload_json FROM archive_refs WHERE quest_root = ?",
            (str(quest_root.resolve()),),
        ).fetchone()
    assert workspace_row is not None
    assert workspace_row[0] == compaction["archive_ref"]["archive_id"]
    assert workspace_row[1] == compaction["archive_ref"]["archive_path"]
    assert workspace_row[2] == compaction["restore_proof_path"]
    assert json.loads(workspace_row[3])["sha256"] == compaction["archive_ref"]["sha256"]
    assert study_report["apply_result"]["runtime_lifecycle_workspace_archive_index"]["indexed_table"] == "archive_refs"


@pytest.mark.parametrize(
    ("status", "active_run_id", "expected_blocker"),
    [
        ("running", "run-live", "active_run_id_present"),
        ("paused", None, "not_stopped_cold:paused"),
        ("stopped", None, "not_stopped_cold:stopped"),
        ("", None, "not_stopped_cold:missing"),
    ],
)
def test_audit_workspace_storage_restore_proof_compaction_blocks_non_cold_runtime(
    tmp_path: Path,
    status: str,
    active_run_id: str | None,
    expected_blocker: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "004-noncold"
    _write_study(profile.studies_root / study_id, study_id=study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    _write_quest(quest_root, quest_id=study_id, status=status, active_run_id=active_run_id)
    payload = quest_root / ".ds" / "runs" / "run-001" / "stdout.jsonl"
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_text('{"line":"stdout"}\n', encoding="utf-8")

    result = module.audit_workspace_storage(
        profile=profile,
        study_id=study_id,
        all_studies=False,
        apply=True,
        restore_proof_compaction=True,
    )

    study_report = result["categories"]["runtime"]["studies"][0]
    compaction = study_report["apply_result"]["restore_proof_compaction"]
    assert study_report["status"] == "audited"
    assert study_report["runtime"]["candidate_action"] == "audit-only"
    assert study_report["actual_runtime_release_bytes"] == 0
    assert compaction["status"] == "blocked_not_stopped_cold"
    assert expected_blocker in compaction["blockers"]
    assert payload.exists()


@pytest.mark.parametrize("status", ["paused", "stopped"])
def test_audit_workspace_storage_restore_proof_compaction_can_include_parked_controller_stop(
    tmp_path: Path,
    status: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "004-parked"
    _write_study(profile.studies_root / study_id, study_id=study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    _write_quest(quest_root, quest_id=study_id, status=status)
    payload = quest_root / ".ds" / "runs" / "run-001" / "stdout.jsonl"
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_text("parked payload\n" * 4096, encoding="utf-8")

    result = module.audit_workspace_storage(
        profile=profile,
        study_id=study_id,
        all_studies=False,
        apply=True,
        restore_proof_compaction=True,
        include_parked_controller_stop=True,
    )

    study_report = result["categories"]["runtime"]["studies"][0]
    compaction = study_report["apply_result"]["restore_proof_compaction"]
    assert study_report["status"] == "applied"
    assert study_report["runtime"]["candidate_action"] == "restore-proof-compaction"
    assert compaction["status"] == "compacted"
    assert compaction["restore_proof"]["status"] == "verified"
    assert not payload.exists()


def test_audit_workspace_storage_restore_proof_compaction_can_include_operator_confirmed_parked_active(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "001-stale-active"
    _write_study(profile.studies_root / study_id, study_id=study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    _write_quest(quest_root, quest_id=study_id, status="active", active_run_id=None)
    payload = quest_root / ".ds" / "runs" / "run-001" / "stdout.jsonl"
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_text("operator confirmed parked payload\n" * 4096, encoding="utf-8")

    result = module.audit_workspace_storage(
        profile=profile,
        study_id=study_id,
        all_studies=False,
        apply=True,
        restore_proof_compaction=True,
        include_operator_confirmed_parked_active=True,
    )

    study_report = result["categories"]["runtime"]["studies"][0]
    compaction = study_report["apply_result"]["restore_proof_compaction"]
    assert study_report["status"] == "applied"
    assert study_report["runtime"]["candidate_action"] == "restore-proof-compaction"
    assert compaction["status"] == "compacted"
    assert compaction["restore_proof"]["status"] == "verified"
    assert not payload.exists()


def test_audit_workspace_storage_restore_proof_compaction_can_explicitly_compact_cold_archive_bucket(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "004-cold-archive"
    _write_study(profile.studies_root / study_id, study_id=study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    _write_quest(quest_root, quest_id=study_id, status="stopped")
    payload_paths = [
        quest_root / ".ds" / "cold_archive" / "prior-run" / f"payload-{index:03d}.jsonl"
        for index in range(18)
    ]
    for path in payload_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("already cold payload\n" * 4096, encoding="utf-8")
    file_count_before = sum(1 for path in (quest_root / ".ds").rglob("*") if path.is_file())

    result = module.audit_workspace_storage(
        profile=profile,
        study_id=study_id,
        all_studies=False,
        apply=True,
        restore_proof_compaction=True,
        include_parked_controller_stop=True,
        restore_proof_buckets=("cold_archive",),
    )

    study_report = result["categories"]["runtime"]["studies"][0]
    compaction = study_report["apply_result"]["restore_proof_compaction"]
    archive_path = Path(compaction["archive_ref"]["archive_path"])
    assert study_report["status"] == "applied"
    assert study_report["runtime"]["candidate_action"] == "restore-proof-compaction"
    assert study_report["runtime"]["restore_proof_compaction"]["eligible"] is True
    assert study_report["runtime"]["estimated_release_bytes"] == study_report["actual_runtime_release_bytes"]
    assert compaction["status"] == "compacted"
    assert compaction["source_buckets"] == ["cold_archive"]
    assert compaction["restore_proof"]["status"] == "verified"
    assert archive_path.is_file()
    assert "/.ds/restore_proof_archives/" in archive_path.as_posix()
    assert not (quest_root / ".ds" / "cold_archive").exists()
    assert sum(1 for path in (quest_root / ".ds").rglob("*") if path.is_file()) < file_count_before


def test_audit_workspace_storage_restore_proof_compaction_verifies_hardlinked_payloads(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "004-hardlinks"
    _write_study(profile.studies_root / study_id, study_id=study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    _write_quest(quest_root, quest_id=study_id, status="completed")
    source = quest_root / ".ds" / "worktrees" / "lane-a" / ".codex" / "sessions" / "rollout.jsonl"
    hardlink = quest_root / ".ds" / "worktrees" / "lane-b" / ".codex" / "sessions" / "rollout.jsonl"
    source.parent.mkdir(parents=True, exist_ok=True)
    hardlink.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("shared session payload\n" * 4096, encoding="utf-8")
    os.link(source, hardlink)

    result = module.audit_workspace_storage(
        profile=profile,
        study_id=study_id,
        all_studies=False,
        apply=True,
        restore_proof_compaction=True,
        restore_proof_buckets=("worktrees",),
    )

    study_report = result["categories"]["runtime"]["studies"][0]
    compaction = study_report["apply_result"]["restore_proof_compaction"]
    restore_proof = compaction["restore_proof"]
    assert study_report["status"] == "applied"
    assert compaction["status"] == "compacted"
    assert restore_proof["status"] == "verified"
    assert restore_proof["source_file_count"] == 2
    assert restore_proof["verified_file_count"] == 2
    assert restore_proof["errors"] == []
    assert not (quest_root / ".ds" / "worktrees").exists()


def test_maintain_quest_runtime_storage_compacts_legacy_unbound_quest(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    quest_root = profile.runtime_root / "legacy-quest"
    _write_quest(quest_root, quest_id="legacy-quest", status="paused")
    payload = quest_root / ".ds" / "runs" / "run-001" / "stdout.jsonl"
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_text("legacy payload\n" * 4096, encoding="utf-8")

    result = module.maintain_quest_runtime_storage(
        profile=profile,
        quest_root=quest_root,
        restore_proof_compaction=True,
        restore_proof_buckets=("runs",),
        include_parked_controller_stop=True,
    )

    compaction = result["restore_proof_compaction"]
    assert result["status"] == "maintained"
    assert result["study_id"] is None
    assert result["study_root"] is None
    assert result["orphan_quest_root_mode"] is True
    assert compaction["status"] == "compacted"
    assert compaction["restore_proof"]["status"] == "verified"
    assert not (quest_root / ".ds" / "runs").exists()
    assert Path(result["latest_report_path"]).is_file()


def test_audit_workspace_storage_restore_proof_compaction_archives_symlink_without_dereferencing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "004-completed"
    _write_study(profile.studies_root / study_id, study_id=study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    _write_quest(quest_root, quest_id=study_id, status="completed")
    payload = quest_root / ".ds" / "runs" / "run-001" / "stdout.jsonl"
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_text('{"line":"stdout"}\n', encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (quest_root / ".ds" / "runs" / "run-001" / "outside-link").symlink_to(outside)

    result = module.audit_workspace_storage(
        profile=profile,
        study_id=study_id,
        all_studies=False,
        apply=True,
        restore_proof_compaction=True,
    )

    study_report = result["categories"]["runtime"]["studies"][0]
    compaction = study_report["apply_result"]["restore_proof_compaction"]
    restore_proof = compaction["restore_proof"]
    manifest = json.loads(Path(compaction["source_manifest_path"]).read_text(encoding="utf-8"))
    symlink_entry = next(item for item in manifest["source_files"] if item["path"].endswith("outside-link"))
    proof_entry = next(item for item in restore_proof["verified_entries"] if item["path"].endswith("outside-link"))

    assert study_report["status"] == "applied"
    assert compaction["status"] == "compacted"
    assert restore_proof["status"] == "verified"
    assert symlink_entry["entry_type"] == "symlink"
    assert symlink_entry["link_target"] == str(outside)
    assert proof_entry == {
        "path": "runs/run-001/outside-link",
        "entry_type": "symlink",
        "link_target": str(outside),
    }
    assert not payload.exists()
    assert outside.exists()


def test_audit_workspace_storage_apply_does_not_count_offline_dataset_candidates_as_release(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    _write_dataset_release(
        profile.workspace_root,
        family_id="master",
        version_id="v1",
        dataset_id="dm_master",
        restore_index_path="datasets/master/v1/restore_index.json",
        checksum="abc123",
        rehydrate_verified=True,
    )
    _write_dataset_release(
        profile.workspace_root,
        family_id="master",
        version_id="v2",
        dataset_id="dm_master",
        supersedes_versions=["v1"],
    )

    result = module.audit_workspace_storage(profile=profile, all_studies=False, apply=True)

    assert result["categories"]["dataset"]["estimated_release_bytes"] > 0
    assert result["summary"]["dataset_archive_offline_candidate_bytes"] > 0
    assert result["summary"]["estimated_release_bytes"] == 0
    assert result["summary"]["actual_release_bytes"] == 0


def test_audit_workspace_storage_git_only_apply_removes_stale_git_temp_garbage(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    pack_root = profile.workspace_root / ".git" / "objects" / "pack"
    object_root = profile.workspace_root / ".git" / "objects" / "6b"
    pack_root.mkdir(parents=True, exist_ok=True)
    object_root.mkdir(parents=True, exist_ok=True)
    tmp_pack = pack_root / "tmp_pack_stale"
    tmp_obj = object_root / "tmp_obj_stale"
    tmp_pack.write_text("pack garbage\n", encoding="utf-8")
    tmp_obj.write_text("object garbage\n", encoding="utf-8")
    stale_mtime = time.time() - 7200
    os.utime(tmp_pack, (stale_mtime, stale_mtime))
    os.utime(tmp_obj, (stale_mtime, stale_mtime))

    result = module.audit_workspace_storage(
        profile=profile,
        all_studies=False,
        apply=True,
        git_only=True,
        older_than_seconds=3600,
    )

    assert result["mode"] == "apply"
    assert result["summary"]["study_count"] == 0
    assert result["categories"]["runtime"]["candidate_action"] == "skipped-git-only"
    git_report = result["categories"]["git"]
    assert git_report["apply_result"]["status"] == "deleted"
    assert git_report["apply_result"]["deleted_count"] == 2
    assert git_report["hardening_result"]["gitignore_status"] == "updated"
    assert "storage_audit/" in (profile.workspace_root / ".gitignore").read_text(encoding="utf-8")
    assert not tmp_pack.exists()
    assert not tmp_obj.exists()


def test_audit_workspace_storage_git_only_apply_keeps_fresh_git_temp_garbage(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    pack_root = profile.workspace_root / ".git" / "objects" / "pack"
    pack_root.mkdir(parents=True, exist_ok=True)
    tmp_pack = pack_root / "tmp_pack_fresh"
    tmp_pack.write_text("pack garbage\n", encoding="utf-8")

    result = module.audit_workspace_storage(
        profile=profile,
        all_studies=False,
        apply=True,
        git_only=True,
        older_than_seconds=3600,
    )

    git_report = result["categories"]["git"]
    assert git_report["estimated_release_bytes"] == 0
    assert git_report["apply_result"]["status"] == "nothing_to_delete"
    assert tmp_pack.exists()


def test_audit_workspace_storage_git_only_apply_blocks_when_git_lock_exists(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    pack_root = profile.workspace_root / ".git" / "objects" / "pack"
    pack_root.mkdir(parents=True, exist_ok=True)
    tmp_pack = pack_root / "tmp_pack_stale"
    tmp_pack.write_text("pack garbage\n", encoding="utf-8")
    stale_mtime = time.time() - 7200
    os.utime(tmp_pack, (stale_mtime, stale_mtime))
    (profile.workspace_root / ".git" / "index.lock").write_text("locked\n", encoding="utf-8")

    result = module.audit_workspace_storage(
        profile=profile,
        all_studies=False,
        apply=True,
        git_only=True,
        older_than_seconds=3600,
    )

    git_report = result["categories"]["git"]
    assert git_report["apply_result"]["status"] == "blocked_git_lock"
    assert "git_lock_present" in git_report["blockers"]
    assert tmp_pack.exists()


def test_audit_workspace_storage_git_only_reports_empty_repo_reinitialize_recommendation(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    workspace_root = profile.workspace_root
    workspace_root.mkdir(parents=True, exist_ok=True)
    module.git_garbage._run_git_command(["init"], workspace_root=workspace_root, check=True)
    objects_root = workspace_root / ".git" / "objects"
    large_object = objects_root / "ab" / "oversized"
    large_object.parent.mkdir(parents=True, exist_ok=True)
    large_object.write_bytes(b"x" * 2048)
    (workspace_root / "README.md").write_text("workspace source\n", encoding="utf-8")

    result = module.audit_workspace_storage(profile=profile, all_studies=False, git_only=True)

    git_report = result["categories"]["git"]
    health = git_report["health"]
    assert health["has_commits"] is False
    assert health["object_store_bytes"] >= 2048
    assert health["untracked_count"] >= 1
    assert health["recommended_action"] == "reinitialize_empty_workspace_git"
    assert "empty_repo_object_store_present" in health["reinitialize_eligibility"]["reasons"]


def test_audit_workspace_storage_git_only_reinitializes_only_when_explicitly_allowed(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    workspace_root = profile.workspace_root
    workspace_root.mkdir(parents=True, exist_ok=True)
    module.git_garbage._run_git_command(["init"], workspace_root=workspace_root, check=True)
    large_object = workspace_root / ".git" / "objects" / "ab" / "oversized"
    large_object.parent.mkdir(parents=True, exist_ok=True)
    large_object.write_bytes(b"x" * 2048)

    dry_run_result = module.audit_workspace_storage(profile=profile, all_studies=False, apply=True, git_only=True)
    dry_run_git = dry_run_result["categories"]["git"]
    assert dry_run_git["empty_repo_reinitialize_result"] is None
    assert large_object.exists()

    apply_result = module.audit_workspace_storage(
        profile=profile,
        all_studies=False,
        apply=True,
        git_only=True,
        reinitialize_empty_workspace_git=True,
    )

    git_report = apply_result["categories"]["git"]
    assert git_report["empty_repo_reinitialize_result"]["status"] == "reinitialized"
    assert not large_object.exists()
    assert (workspace_root / ".git").is_dir()
    assert (workspace_root / ".gitignore").is_file()
    assert "studies/*/artifacts/**" in (workspace_root / ".gitignore").read_text(encoding="utf-8")


def test_audit_workspace_storage_git_only_refuses_reinitialize_when_commits_exist(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    workspace_root = profile.workspace_root
    workspace_root.mkdir(parents=True, exist_ok=True)
    module.git_garbage._run_git_command(["init"], workspace_root=workspace_root, check=True)
    module.git_garbage._run_git_command(["config", "user.email", "test@example.com"], workspace_root=workspace_root, check=True)
    module.git_garbage._run_git_command(["config", "user.name", "Test User"], workspace_root=workspace_root, check=True)
    (workspace_root / "README.md").write_text("tracked\n", encoding="utf-8")
    module.git_garbage._run_git_command(["add", "README.md"], workspace_root=workspace_root, check=True)
    module.git_garbage._run_git_command(["commit", "-m", "baseline"], workspace_root=workspace_root, check=True)

    result = module.audit_workspace_storage(
        profile=profile,
        all_studies=False,
        apply=True,
        git_only=True,
        reinitialize_empty_workspace_git=True,
    )

    git_report = result["categories"]["git"]
    assert git_report["health"]["has_commits"] is True
    assert git_report["health"]["recommended_action"] != "reinitialize_empty_workspace_git"
    assert git_report["empty_repo_reinitialize_result"]["status"] == "blocked_not_eligible"
    assert "has_commits" in git_report["empty_repo_reinitialize_result"]["blockers"]
    assert module.git_garbage._run_git_command(
        ["rev-list", "--count", "HEAD"],
        workspace_root=workspace_root,
        check=True,
    ).stdout.strip() == "1"


def test_audit_workspace_storage_stopped_only_skips_live_runtime(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)

    live_study_id = "002-live"
    stopped_study_id = "004-stopped"
    _write_study(profile.studies_root / live_study_id, study_id=live_study_id, quest_id=live_study_id)
    _write_study(profile.studies_root / stopped_study_id, study_id=stopped_study_id, quest_id=stopped_study_id)
    _write_quest(profile.runtime_root / live_study_id, quest_id=live_study_id, status="running", active_run_id="run-live")
    _write_quest(profile.runtime_root / stopped_study_id, quest_id=stopped_study_id, status="stopped")

    result = module.audit_workspace_storage(profile=profile, all_studies=True, stopped_only=True)

    runtime_studies = result["categories"]["runtime"]["studies"]
    live_report = next(item for item in runtime_studies if item["study_id"] == live_study_id)
    stopped_report = next(item for item in runtime_studies if item["study_id"] == stopped_study_id)
    assert live_report["status"] == "skipped_stopped_only"
    assert stopped_report["status"] == "audited"
