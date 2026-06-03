from __future__ import annotations

from tests.test_runtime_storage_maintenance_cases.runtime_storage_maintenance_helpers import *

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
    assert "/artifacts/runtime/runtime_storage_maintenance/restore_proof_archives/" in compaction["archive_ref"][
        "archive_path"
    ]
    assert "/.ds/restore_proof_archives/" not in compaction["archive_ref"]["archive_path"]
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


@pytest.mark.parametrize("status", ["active", "waiting_for_user"])
def test_audit_workspace_storage_restore_proof_compaction_can_include_operator_confirmed_parked_runtime(
    tmp_path: Path,
    status: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "001-stale-active"
    _write_study(profile.studies_root / study_id, study_id=study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    _write_quest(quest_root, quest_id=study_id, status=status, active_run_id=None)
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


def test_audit_workspace_storage_restore_proof_compaction_shards_codex_homes(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "004-sharded-codex-homes"
    _write_study(profile.studies_root / study_id, study_id=study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    _write_quest(quest_root, quest_id=study_id, status="waiting_for_user")
    payload_paths = [
        quest_root / ".ds" / "codex_homes" / "mas-run-a" / ".codex" / "sessions" / "rollout-a.jsonl",
        quest_root / ".ds" / "codex_homes" / "mas-run-b" / ".cache" / "runtime-cache.bin",
    ]
    for path in payload_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{path.name}\n" * 4096, encoding="utf-8")

    result = module.audit_workspace_storage(
        profile=profile,
        study_id=study_id,
        all_studies=False,
        apply=True,
        restore_proof_compaction=True,
        include_operator_confirmed_parked_active=True,
        restore_proof_buckets=("codex_homes",),
    )

    study_report = result["categories"]["runtime"]["studies"][0]
    compaction = study_report["apply_result"]["restore_proof_compaction"]
    archive_refs_index = json.loads(Path(compaction["archive_refs_path"]).read_text(encoding="utf-8"))
    archive_refs = archive_refs_index["archive_refs"]

    assert study_report["status"] == "applied"
    assert compaction["status"] == "compacted"
    assert compaction["archive_ref"] is None
    assert compaction["archive_ref_count"] == 2
    assert compaction["archive_refs_inlined"] is False
    assert "archive_refs" not in compaction
    assert archive_refs_index["archive_ref_count"] == 2
    assert compaction["shard_count"] == 2
    assert compaction["shards_inlined"] is False
    assert "shards" not in compaction
    assert compaction["restore_proofs_inlined"] is False
    assert "restore_proofs" not in compaction
    assert len(compaction["archive_ref_samples"]) == 2
    assert len(compaction["shard_samples"]) == 2
    assert {proof["status"] for proof in compaction["restore_proof_samples"]} == {"verified"}
    assert all(
        "/artifacts/runtime/runtime_storage_maintenance/restore_proof_archives/" in ref["archive_path"]
        for ref in archive_refs
    )
    assert all(Path(ref["archive_path"]).is_file() for ref in archive_refs)
    assert all(Path(ref["source_manifest_path"]).is_file() for ref in archive_refs)
    assert all(Path(ref["restore_proof_path"]).is_file() for ref in archive_refs)
    assert not (quest_root / ".ds" / "codex_homes" / "mas-run-a").exists()
    assert not (quest_root / ".ds" / "codex_homes" / "mas-run-b").exists()
    assert study_report["apply_result"]["domain_authority_archive_ref_index"]["indexed_count"] == 2
    assert study_report["apply_result"]["domain_authority_archive_ref_index"]["indexed_results_inlined"] is False
    assert "indexed_results" not in study_report["apply_result"]["domain_authority_archive_ref_index"]
    assert study_report["apply_result"]["runtime_lifecycle_workspace_archive_index"]["indexed_count"] == 2
    assert study_report["apply_result"]["runtime_lifecycle_workspace_archive_index"]["indexed_results_inlined"] is False
    assert "indexed_results" not in study_report["apply_result"]["runtime_lifecycle_workspace_archive_index"]

    db_path = quest_root / "artifacts" / "runtime" / "domain_authority_refs.sqlite"
    with sqlite3.connect(db_path) as conn:
        quest_ref_count = conn.execute(
            "SELECT COUNT(*) FROM archive_refs WHERE quest_root = ?",
            (str(quest_root.resolve()),),
        ).fetchone()[0]
    workspace_db_path = profile.workspace_root / "artifacts" / "runtime" / "domain_authority_refs.sqlite"
    with sqlite3.connect(workspace_db_path) as conn:
        workspace_ref_count = conn.execute(
            "SELECT COUNT(*) FROM archive_refs WHERE quest_root = ?",
            (str(quest_root.resolve()),),
        ).fetchone()[0]
    assert quest_ref_count == 2
    assert workspace_ref_count == 2


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
    assert "/artifacts/runtime/runtime_storage_maintenance/restore_proof_archives/" in archive_path.as_posix()
    assert "/.ds/restore_proof_archives/" not in archive_path.as_posix()
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
    assert_storage_refs_only_adapter_boundary(
        result,
        report_mode="orphan_quest_runtime_storage_maintenance",
    )
    assert result["study_id"] is None
    assert result["study_root"] is None
    assert result["orphan_quest_root_mode"] is True
    assert compaction["status"] == "compacted"
    assert compaction["restore_proof"]["status"] == "verified"
    assert not (quest_root / ".ds" / "runs").exists()
    assert Path(result["latest_report_path"]).is_file()


def test_maintain_quest_runtime_storage_slims_sharded_codex_home_report(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    quest_root = profile.runtime_root / "legacy-codex-homes"
    _write_quest(quest_root, quest_id="legacy-codex-homes", status="waiting_for_user")
    payload_paths = [
        quest_root / ".ds" / "codex_homes" / "mas-run-a" / ".codex" / "sessions" / "rollout-a.jsonl",
        quest_root / ".ds" / "codex_homes" / "mas-run-b" / ".cache" / "runtime-cache.bin",
        quest_root / ".ds" / "codex_homes" / "mas-run-c" / ".codex" / "sessions" / "rollout-c.jsonl",
    ]
    for path in payload_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{path.name}\n" * 4096, encoding="utf-8")

    result = module.maintain_quest_runtime_storage(
        profile=profile,
        quest_root=quest_root,
        restore_proof_compaction=True,
        restore_proof_buckets=("codex_homes",),
        include_operator_confirmed_parked_active=True,
    )

    compaction = result["restore_proof_compaction"]
    archive_refs_index = json.loads(Path(compaction["archive_refs_path"]).read_text(encoding="utf-8"))
    assert result["status"] == "maintained"
    assert compaction["status"] == "compacted"
    assert compaction["archive_ref_count"] == 3
    assert compaction["archive_refs_inlined"] is False
    assert "archive_refs" not in compaction
    assert archive_refs_index["archive_ref_count"] == 3
    assert all(Path(ref["archive_path"]).is_file() for ref in archive_refs_index["archive_refs"])
    assert compaction["shard_count"] == 3
    assert compaction["shards_inlined"] is False
    assert "shards" not in compaction
    assert compaction["restore_proofs_inlined"] is False
    assert "restore_proofs" not in compaction
    assert compaction["pruned_path_count"] == 3
    assert compaction["pruned_paths_inlined"] is False
    assert "pruned_paths" not in compaction
    assert result["domain_authority_archive_ref_index"]["indexed_count"] == 3
    assert result["domain_authority_archive_ref_index"]["indexed_results_inlined"] is False
    assert "indexed_results" not in result["domain_authority_archive_ref_index"]
    assert len(json.dumps(result, ensure_ascii=False)) < 30_000


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
