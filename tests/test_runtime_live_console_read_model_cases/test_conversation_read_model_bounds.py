from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_conversation_read_model_reads_jsonl_as_bounded_tail_without_full_file_scan(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    conversation = importlib.import_module("med_autoscience.runtime_protocol.runtime_conversation_read_model")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = "quest-dm002"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        study_root / "artifacts" / "runtime" / "progress_projection" / "latest.json",
        {"study_id": study_id, "quest_id": quest_id, "quest_root": str(quest_root)},
    )
    events_path = quest_root / "artifacts" / "runtime" / "mas_runtime_events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    filler = "x" * (conversation.JSONL_TAIL_READ_BYTES + 4096)
    events_path.write_text(
        json.dumps(
            {
                "event": "old_event",
                "recorded_at": "2026-05-08T01:00:00+00:00",
                "snapshot": {"quest_id": quest_id, "status": "old"},
                "payload": filler,
            },
            ensure_ascii=False,
        )
        + "\n"
        + json.dumps(
            {
                "event": "recent_event",
                "recorded_at": "2026-05-08T02:00:00+00:00",
                "snapshot": {
                    "quest_id": quest_id,
                    "status": "running",
                    "last_completed_run_id": "run-recent",
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = module.build_conversation_read_model(
        profile,
        study_id=study_id,
        generated_at="2026-05-08T02:07:00+00:00",
    )

    runtime_events = [item for item in payload["timeline"] if item["item_kind"] == "runtime_lifecycle_event"]
    assert [item["event_name"] for item in runtime_events] == ["recent_event"]
    events_ref = next(ref for ref in payload["source_refs"] if ref["surface_kind"] == "runtime_events_jsonl")
    assert events_ref["truncated"] is True
    assert events_ref["bytes_read"] == conversation.JSONL_TAIL_READ_BYTES
    assert events_ref["size_bytes"] > conversation.JSONL_TAIL_READ_BYTES
