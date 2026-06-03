from __future__ import annotations

from tests.test_runtime_storage_maintenance_cases.runtime_storage_maintenance_helpers import *

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
    assert_storage_refs_only_adapter_boundary(result, report_mode="study_runtime_storage_maintenance")
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
    assert_storage_refs_only_adapter_boundary(
        latest_payload,
        report_mode="study_runtime_storage_maintenance",
    )
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
    assert_storage_refs_only_adapter_boundary(result, report_mode="workspace_storage_audit")
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
