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
