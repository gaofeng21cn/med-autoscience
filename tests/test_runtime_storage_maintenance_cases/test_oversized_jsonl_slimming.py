from __future__ import annotations

import gzip
import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile


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


def _write_quest(quest_root: Path, *, quest_id: str, status: str) -> None:
    quest_root.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {quest_id}\n", encoding="utf-8")
    runtime_state = {"quest_id": quest_id, "status": status, "active_run_id": None}
    ds_root = quest_root / ".ds"
    ds_root.mkdir(parents=True, exist_ok=True)
    (ds_root / "runtime_state.json").write_text(
        json.dumps(runtime_state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def test_maintain_runtime_storage_slims_oversized_runtime_jsonl_without_backend(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    monkeypatch.setattr(module.backend_maintenance, "run_quest_storage_maintenance", lambda **_: None)

    study_id = "003-jsonl"
    quest_root = profile.runtime_root / study_id
    _write_study(profile.studies_root / study_id, study_id=study_id, quest_id=study_id)
    _write_quest(quest_root, quest_id=study_id, status="waiting_for_user")
    event_log = quest_root / "artifacts" / "runtime" / "mas_runtime_events.jsonl"
    event_log.parent.mkdir(parents=True, exist_ok=True)
    event_log.write_text(
        "".join(
            json.dumps(
                {
                    "event": "worker_lease_termination",
                    "recorded_at": "2026-05-22T10:25:22+00:00",
                    "terminations": [
                        {"lease_path": f"/tmp/run-{index}/worker_lease.json"} for index in range(800)
                    ],
                },
                ensure_ascii=False,
            )
            + "\n"
            for _ in range(80)
        ),
        encoding="utf-8",
    )
    size_before = event_log.stat().st_size

    result = module.maintain_runtime_storage(
        profile=profile,
        study_id=study_id,
        study_root=None,
        slim_jsonl_threshold_mb=1,
        head_lines=2,
        tail_lines=3,
    )

    assert result["status"] == "maintained"
    assert result["jsonl_slimming"]["status"] == "slimmed"
    slim_file = result["jsonl_slimming"]["files"][0]
    assert slim_file["path"] == str(event_log)
    assert slim_file["bytes_before"] == size_before
    assert slim_file["bytes_after"] < size_before
    assert slim_file["archive_bytes"] < size_before
    assert slim_file["released_bytes"] > 0
    archive_path = Path(slim_file["archive_path"])
    assert archive_path.is_file()
    with gzip.open(archive_path, "rt", encoding="utf-8") as handle:
        assert handle.readline().startswith('{"event": "worker_lease_termination"')
    slim_payload = json.loads(event_log.read_text(encoding="utf-8"))
    assert slim_payload["surface_kind"] == "runtime_oversized_jsonl_slimming"
    assert slim_payload["status"] == "slimmed_ref"
    assert slim_payload["line_count"] == 80
    assert len(slim_payload["retained_head_lines"]) == 2
    assert len(slim_payload["retained_tail_lines"]) == 3
    assert Path(result["latest_report_path"]).is_file()
