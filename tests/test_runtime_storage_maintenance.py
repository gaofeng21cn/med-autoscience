from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

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
    checksum: str | None = None,
) -> Path:
    release_root = workspace_root / "datasets" / family_id / version_id
    release_root.mkdir(parents=True, exist_ok=True)
    (release_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    source_lines = ["source_release:"]
    if restore_handle:
        source_lines.append(f"  restore_handle: {restore_handle}")
    if checksum:
        source_lines.append(f"  sha256: {checksum}")
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
    (profile.workspace_root / ".git" / "objects" / "pack" / "tmp_pack_001").write_text("pack\n", encoding="utf-8")
    _write_dataset_release(
        profile.workspace_root,
        family_id="master",
        version_id="v1",
        dataset_id="dm_master",
        restore_handle="s3://archive/dm_master/v1.tar.gz",
        checksum="abc123",
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
    dataset_releases = result["categories"]["dataset"]["releases"]
    v1_report = next(item for item in dataset_releases if item["version_id"] == "v1")
    v2_report = next(item for item in dataset_releases if item["version_id"] == "v2")
    assert v1_report["candidate_action"] == "archive-offline"
    assert v2_report["candidate_action"] == "keep-online"
    assert result["categories"]["cache"]["estimated_release_bytes"] > 0
    assert result["categories"]["git"]["tmp_pack_files"]
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
    assert v1_report["blockers"] == ["missing_restore_handle", "missing_checksum"]


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
