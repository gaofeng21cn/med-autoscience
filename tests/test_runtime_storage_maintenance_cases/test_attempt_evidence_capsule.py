from __future__ import annotations

import json
from pathlib import PurePosixPath

from med_autoscience.controllers.runtime_storage_maintenance_parts.quest_root_maintenance import (
    maintain_quest_runtime_storage,
)

from tests.test_runtime_storage_maintenance_cases.runtime_storage_maintenance_helpers import (
    _write_quest,
    _write_study,
    make_profile,
)


def test_attempt_evidence_capsule_plan_writes_manifest_without_mutating_raw(tmp_path):
    profile = make_profile(tmp_path)
    quest_root = tmp_path / "runtime" / "quests" / "quest-alpha"
    _write_quest(quest_root, quest_id="quest-alpha", status="stopped")
    _write_attempt(
        quest_root,
        attempt_id="run-success",
        status="completed",
        stdout_text=("success line\n" * 8),
    )

    result = maintain_quest_runtime_storage(
        profile=profile,
        quest_root=quest_root,
        attempt_evidence_capsules=True,
        semantic_process_retention=True,
        semantic_process_retention_apply=False,
        semantic_retention_max_log_bytes=16,
        slim_jsonl_threshold_mb=None,
    )

    capsule_summary = result["attempt_evidence_capsules"]
    retention = result["semantic_process_retention"]
    assert capsule_summary["status"] == "planned"
    assert capsule_summary["capsule_count"] == 1
    assert retention["status"] == "planned"
    assert retention["candidate_count"] == 1
    stdout_path = quest_root / ".ds" / "runs" / "run-success" / "stdout.log"
    assert stdout_path.read_text(encoding="utf-8").startswith("success line")
    latest_path = quest_root / "artifacts" / "runtime" / "attempt_evidence" / "latest.json"
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    capsule_ref = latest["capsule_refs"][0]
    capsule = json.loads((quest_root / capsule_ref["capsule_path"]).read_text(encoding="utf-8"))
    assert capsule["surface_kind"] == "runtime_attempt_evidence_capsule"
    assert capsule["source_kind"] == "legacy_ds_intake"
    assert capsule["attempt_status"] == "completed"
    assert capsule["log_digest"]["files"][0]["sha256"]
    assert capsule["replay_manifest"]["status"] == "ready"
    assert capsule["replay_manifest"]["legacy_source_retained"] is True
    assert capsule["body_included"] is False


def test_semantic_process_retention_apply_migrates_success_attempt_and_keeps_failed_raw(tmp_path):
    profile = make_profile(tmp_path)
    quest_root = tmp_path / "runtime" / "quests" / "quest-alpha"
    _write_quest(quest_root, quest_id="quest-alpha", status="stopped")
    success_log = "success payload\n" * 64
    failed_log = "failed payload\n" * 64
    success_stdout = _write_attempt(
        quest_root,
        attempt_id="run-success",
        status="completed",
        stdout_text=success_log,
    )
    failed_stdout = _write_attempt(
        quest_root,
        attempt_id="run-failed",
        status="failed",
        stdout_text=failed_log,
    )
    authority_surface = quest_root / "artifacts" / "runtime" / "controller_decisions" / "latest.json"
    authority_surface.parent.mkdir(parents=True, exist_ok=True)
    authority_surface.write_text('{"status":"keep"}\n', encoding="utf-8")

    result = maintain_quest_runtime_storage(
        profile=profile,
        quest_root=quest_root,
        attempt_evidence_capsules=True,
        semantic_process_retention=True,
        semantic_process_retention_apply=True,
        semantic_retention_max_log_bytes=32,
        semantic_retention_max_raw_bytes=128,
        semantic_retention_keep_failed_raw=True,
        slim_jsonl_threshold_mb=None,
    )

    retention = result["semantic_process_retention"]
    assert retention["status"] == "applied"
    assert retention["applied_count"] == 1
    assert retention["candidate_count"] == 1
    assert retention["skipped_failed_raw_count"] == 1
    assert not success_stdout.exists()
    assert not (quest_root / ".ds" / "runs" / "run-success").exists()
    success_ref_path = (
        quest_root
        / "artifacts"
        / "runtime"
        / "attempt_evidence"
        / "run-success"
        / "semantic_process_ref.json"
    )
    success_ref = json.loads(success_ref_path.read_text(encoding="utf-8"))
    assert success_ref["surface_kind"] == "runtime_semantic_process_ref"
    assert success_ref["original_sha256"]
    assert success_ref["capsule_ref"].endswith("capsule.json")
    assert success_ref["legacy_attempt_root_removed"] is True
    assert success_ref["retained_head"]
    assert success_ref["retained_tail"]
    assert PurePosixPath(success_ref["archive_path"]).parts[:4] == (
        "artifacts",
        "runtime",
        "restore_index",
        "legacy_attempt_raw",
    )
    assert success_ref["restore_proof"]["status"] == "verified"
    assert failed_stdout.read_text(encoding="utf-8") == failed_log
    assert authority_surface.read_text(encoding="utf-8") == '{"status":"keep"}\n'


def test_semantic_process_retention_apply_migrates_legacy_codex_homes_bucket(tmp_path):
    profile = make_profile(tmp_path)
    quest_root = tmp_path / "runtime" / "quests" / "quest-alpha"
    _write_quest(quest_root, quest_id="quest-alpha", status="stopped")
    codex_home = quest_root / ".ds" / "codex_homes" / "run-success"
    codex_home.mkdir(parents=True)
    (codex_home / "config.json").write_text('{"model":"codex"}\n', encoding="utf-8")
    (codex_home / "sessions").mkdir()
    (codex_home / "sessions" / "trace.jsonl").write_text('{"event":"ok"}\n', encoding="utf-8")

    result = maintain_quest_runtime_storage(
        profile=profile,
        quest_root=quest_root,
        attempt_evidence_capsules=True,
        semantic_process_retention=True,
        semantic_process_retention_apply=True,
        slim_jsonl_threshold_mb=None,
    )

    home_retention = result["legacy_codex_homes_retention"]
    assert home_retention["status"] == "applied"
    assert home_retention["actual_release_bytes"] >= 0
    assert not (quest_root / ".ds" / "codex_homes").exists()
    latest_path = quest_root / "artifacts" / "runtime" / "restore_index" / "legacy_executor_home" / "latest.json"
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest["surface_kind"] == "legacy_codex_homes_migration_receipt"
    assert latest["restore_proof"]["status"] == "verified"
    assert latest["legacy_codex_homes_removed"] is True


def test_workspace_storage_audit_semantic_retention_stopped_only_migrates_completed_projects(tmp_path):
    module = __import__(
        "med_autoscience.controllers.runtime_storage_maintenance",
        fromlist=["audit_workspace_storage"],
    )
    profile = make_profile(tmp_path)
    live_study_id = "002-live"
    completed_study_id = "004-completed"
    _write_quest(profile.runtime_root / live_study_id, quest_id=live_study_id, status="running", active_run_id="run-live")
    _write_quest(profile.runtime_root / completed_study_id, quest_id=completed_study_id, status="completed")
    _write_study(profile.studies_root / live_study_id, study_id=live_study_id, quest_id=live_study_id)
    _write_study(profile.studies_root / completed_study_id, study_id=completed_study_id, quest_id=completed_study_id)
    _write_attempt(
        profile.runtime_root / completed_study_id,
        attempt_id="run-success",
        status="completed",
        stdout_text="completed payload\n" * 64,
    )
    live_home = profile.runtime_root / live_study_id / ".ds" / "codex_homes" / "run-live"
    live_home.mkdir(parents=True)
    (live_home / "session.jsonl").write_text('{"event":"live"}\n', encoding="utf-8")
    completed_home = profile.runtime_root / completed_study_id / ".ds" / "codex_homes" / "run-success"
    completed_home.mkdir(parents=True)
    (completed_home / "session.jsonl").write_text('{"event":"done"}\n', encoding="utf-8")

    result = module.audit_workspace_storage(
        profile=profile,
        all_studies=True,
        stopped_only=True,
        apply=True,
        semantic_process_retention=True,
        semantic_process_retention_apply=True,
        semantic_retention_max_log_bytes=16,
        semantic_retention_max_raw_bytes=32,
        slim_jsonl_threshold_mb=None,
    )

    runtime_studies = result["categories"]["runtime"]["studies"]
    live_report = next(item for item in runtime_studies if item["study_id"] == live_study_id)
    completed_report = next(item for item in runtime_studies if item["study_id"] == completed_study_id)
    completed_apply = completed_report["apply_result"]
    assert live_report["status"] == "skipped_stopped_only"
    assert completed_report["status"] == "applied"
    assert completed_apply["semantic_process_retention"]["status"] == "applied"
    assert completed_apply["legacy_codex_homes_retention"]["status"] == "applied"
    assert not (profile.runtime_root / completed_study_id / ".ds" / "runs" / "run-success").exists()
    assert not (profile.runtime_root / completed_study_id / ".ds" / "codex_homes").exists()
    assert live_home.exists()
    latest = (
        profile.runtime_root
        / completed_study_id
        / "artifacts"
        / "runtime"
        / "restore_index"
        / "legacy_executor_home"
        / "latest.json"
    )
    assert json.loads(latest.read_text(encoding="utf-8"))["legacy_codex_homes_removed"] is True


def test_workspace_storage_audit_semantic_retention_study_id_migrates_manual_selection_only(tmp_path):
    module = __import__(
        "med_autoscience.controllers.runtime_storage_maintenance",
        fromlist=["audit_workspace_storage"],
    )
    profile = make_profile(tmp_path)
    selected_study_id = "004-selected"
    other_study_id = "005-other"
    for study_id in (selected_study_id, other_study_id):
        _write_study(profile.studies_root / study_id, study_id=study_id, quest_id=study_id)
        _write_quest(profile.runtime_root / study_id, quest_id=study_id, status="completed")
        _write_attempt(
            profile.runtime_root / study_id,
            attempt_id="run-success",
            status="completed",
            stdout_text=f"{study_id} payload\n" * 64,
        )
        home = profile.runtime_root / study_id / ".ds" / "codex_homes" / "run-success"
        home.mkdir(parents=True)
        (home / "session.jsonl").write_text(f'{{"study":"{study_id}"}}\n', encoding="utf-8")

    result = module.audit_workspace_storage(
        profile=profile,
        study_id=selected_study_id,
        all_studies=False,
        apply=True,
        semantic_process_retention=True,
        semantic_process_retention_apply=True,
        semantic_retention_max_log_bytes=16,
        semantic_retention_max_raw_bytes=32,
        slim_jsonl_threshold_mb=None,
    )

    runtime_studies = result["categories"]["runtime"]["studies"]
    assert [item["study_id"] for item in runtime_studies] == [selected_study_id]
    selected_apply = runtime_studies[0]["apply_result"]
    assert selected_apply["semantic_process_retention"]["status"] == "applied"
    assert selected_apply["legacy_codex_homes_retention"]["status"] == "applied"
    assert not (profile.runtime_root / selected_study_id / ".ds" / "runs" / "run-success").exists()
    assert not (profile.runtime_root / selected_study_id / ".ds" / "codex_homes").exists()
    assert (profile.runtime_root / other_study_id / ".ds" / "runs" / "run-success").exists()
    assert (profile.runtime_root / other_study_id / ".ds" / "codex_homes").exists()


def _write_attempt(
    quest_root,
    *,
    attempt_id: str,
    status: str,
    stdout_text: str,
):
    attempt_root = quest_root / ".ds" / "runs" / attempt_id
    attempt_root.mkdir(parents=True, exist_ok=True)
    (attempt_root / "attempt.json").write_text(
        json.dumps(
            {
                "attempt_id": attempt_id,
                "status": status,
                "command": ["python", "analysis.py"],
                "cwd": str(quest_root),
                "env_keys": ["PYTHONPATH"],
                "inputs": ["inputs/source.csv"],
                "outputs": ["outputs/result.json"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (attempt_root / "inputs").mkdir()
    (attempt_root / "inputs" / "source.csv").write_text("id\n1\n", encoding="utf-8")
    (attempt_root / "outputs").mkdir()
    (attempt_root / "outputs" / "result.json").write_text('{"ok":true}\n', encoding="utf-8")
    stdout_path = attempt_root / "stdout.log"
    stdout_path.write_text(stdout_text, encoding="utf-8")
    return stdout_path
