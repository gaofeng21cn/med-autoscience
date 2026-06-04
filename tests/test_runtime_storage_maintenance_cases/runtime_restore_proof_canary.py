from __future__ import annotations

from tests.test_runtime_storage_maintenance_cases.runtime_storage_maintenance_helpers import *


def test_restore_proof_canary_archives_bounded_sample_and_retains_sources(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    study_id = "004-canary"
    quest_id = "quest-canary"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_study(study_root, study_id=study_id, quest_id=quest_id)
    _write_quest(quest_root, quest_id=quest_id, status="stopped")
    payloads = [
        quest_root / ".ds" / "runs" / "run-a" / "stdout.jsonl",
        quest_root / ".ds" / "runs" / "run-b" / "stdout.jsonl",
        quest_root / ".ds" / "runs" / "run-c" / "stdout.jsonl",
    ]
    for index, payload in enumerate(payloads, start=1):
        payload.parent.mkdir(parents=True, exist_ok=True)
        payload.write_text(f"runtime payload {index}\n", encoding="utf-8")

    result = module.maintain_runtime_storage(
        profile=profile,
        study_id=study_id,
        study_root=None,
        restore_proof_canary=True,
        restore_proof_canary_entry_limit=2,
        restore_proof_buckets=("runs",),
        include_parked_controller_stop=True,
        refs_only_state_index_pilot=True,
        refs_only_state_index_only=True,
        include_worktrees=False,
        dedupe_worktree_min_mb=None,
        slim_jsonl_threshold_mb=None,
    )

    assert result["status"] == "maintained"
    assert result["legacy_backend_status"] == "skipped_by_restore_proof_canary_and_refs_only_state_index_only"
    assert result["refs_only_state_index_pilot"]["status"] == "indexed"
    canary = result["restore_proof_canary"]
    assert canary["status"] == "verified"
    assert canary["entry_limit_per_bucket"] == 2
    assert canary["bounded_source_path_count"] == 2
    assert canary["archive_created"] is True
    assert canary["source_retained"] is True
    assert canary["mutated_runtime_payload"] is False
    assert canary["actual_release_bytes"] == 0
    assert canary["archive_ref"]["source_retained"] is True
    assert canary["restore_proof"]["status"] == "verified"
    assert canary["restore_proof"]["source_file_count"] == 2
    assert canary["bucket_samples"][0]["has_more_than_limit"] is True
    assert Path(canary["archive_path"]).is_file()
    assert Path(canary["source_manifest_path"]).is_file()
    assert Path(canary["restore_proof_path"]).is_file()
    assert Path(canary["receipt_path"]).is_file()
    assert all(payload.exists() for payload in payloads)
    latest_payload = json.loads(Path(result["latest_report_path"]).read_text(encoding="utf-8"))
    assert latest_payload["restore_proof_canary"]["receipt_ref"] == canary["receipt_ref"]
    assert "runtime payload" not in json.dumps(latest_payload["restore_proof_canary"], ensure_ascii=False)


def test_orphan_quest_restore_proof_canary_blocks_without_parked_gate(tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.runtime_storage_maintenance_parts.quest_root_maintenance"
    )
    profile = make_profile(tmp_path)
    quest_id = "quest-paused"
    quest_root = profile.runtime_root / quest_id
    _write_quest(quest_root, quest_id=quest_id, status="paused")
    payload = quest_root / ".ds" / "codex_homes" / "run-a" / ".codex" / "sessions" / "rollout.jsonl"
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_text("paused payload\n", encoding="utf-8")

    result = module.maintain_quest_runtime_storage(
        profile=profile,
        quest_root=quest_root,
        restore_proof_canary=True,
        restore_proof_buckets=("codex_homes",),
        include_worktrees=False,
        dedupe_worktree_min_mb=None,
        slim_jsonl_threshold_mb=None,
    )

    canary = result["restore_proof_canary"]
    assert result["status"] == "blocked_restore_proof_canary"
    assert canary["status"] == "blocked_not_stopped_cold"
    assert "not_stopped_cold:paused" in canary["blockers"]
    assert canary["archive_created"] is False
    assert canary["mutated_runtime_payload"] is False
    assert payload.exists()
