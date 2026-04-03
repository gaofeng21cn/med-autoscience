from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_load_and_save_watch_state_round_trip(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.runtime_watch")
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    initial = module.load_watch_state(quest_root)
    assert initial == module.RuntimeWatchState(
        schema_version=1,
        updated_at=None,
        controllers={},
    )

    module.save_watch_state(
        quest_root,
        module.RuntimeWatchState(
            schema_version=1,
            updated_at="2026-04-02T12:00:00+00:00",
            controllers={
                "publication_gate": module.RuntimeWatchControllerState(
                    last_seen_fingerprint="fp-1",
                    last_applied_fingerprint=None,
                    last_applied_at=None,
                    last_status=None,
                    last_suppression_reason=None,
                )
            },
        ),
    )

    stored = module.load_watch_state(quest_root)
    assert stored == module.RuntimeWatchState(
        schema_version=1,
        updated_at="2026-04-02T12:00:00+00:00",
        controllers={
            "publication_gate": module.RuntimeWatchControllerState(
                last_seen_fingerprint="fp-1",
                last_applied_fingerprint=None,
                last_applied_at=None,
                last_status=None,
                last_suppression_reason=None,
            )
        },
    )


def test_write_watch_report_uses_runtime_protocol_paths(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.runtime_watch")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    report = {
        "scanned_at": "2026-04-02T12:00:00+00:00",
        "quest_root": str(quest_root),
        "quest_status": "running",
    }

    json_path, md_path = module.write_watch_report(
        quest_root=quest_root,
        report=report,
        markdown="# Runtime Watch Report\n",
    )

    assert json_path == quest_root / "artifacts" / "reports" / "runtime_watch" / "2026-04-02T120000Z.json"
    assert md_path == quest_root / "artifacts" / "reports" / "runtime_watch" / "2026-04-02T120000Z.md"
    assert json.loads(json_path.read_text(encoding="utf-8"))["quest_status"] == "running"
    assert md_path.read_text(encoding="utf-8") == "# Runtime Watch Report\n"


def test_plan_controller_intervention_applies_once_and_persists_fingerprint() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.runtime_watch")

    result = module.plan_controller_intervention(
        previous_controller_state=module.RuntimeWatchControllerState(),
        dry_run_result={"status": "blocked", "blockers": ["b1"]},
        fingerprint="fp-1",
        apply=True,
        scanned_at="2026-04-02T12:00:00+00:00",
        intervention_statuses={"blocked"},
    )

    assert result == module.RuntimeWatchInterventionPlan(
        action=module.RuntimeWatchControllerAction.APPLIED,
        should_apply=True,
        suppression_reason=None,
        controller_state=module.RuntimeWatchControllerState(
            last_seen_fingerprint="fp-1",
            last_applied_fingerprint="fp-1",
            last_applied_at="2026-04-02T12:00:00+00:00",
            last_status="blocked",
            last_suppression_reason=None,
        ),
    )


def test_plan_controller_intervention_suppresses_duplicate_fingerprint() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.runtime_watch")

    result = module.plan_controller_intervention(
        previous_controller_state=module.RuntimeWatchControllerState(
            last_seen_fingerprint=None,
            last_applied_fingerprint="fp-1",
            last_applied_at="earlier",
            last_status=None,
            last_suppression_reason=None,
        ),
        dry_run_result={"status": "blocked", "blockers": ["b1"]},
        fingerprint="fp-1",
        apply=True,
        scanned_at="2026-04-02T12:00:00+00:00",
        intervention_statuses={"blocked"},
    )

    assert result == module.RuntimeWatchInterventionPlan(
        action=module.RuntimeWatchControllerAction.SUPPRESSED,
        should_apply=False,
        suppression_reason="duplicate_fingerprint",
        controller_state=module.RuntimeWatchControllerState(
            last_seen_fingerprint="fp-1",
            last_applied_fingerprint="fp-1",
            last_applied_at="earlier",
            last_status="blocked",
            last_suppression_reason="duplicate_fingerprint",
        ),
    )


def test_runtime_watch_uses_shared_report_store_helpers(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.runtime_watch")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    seen: dict[str, object] = {}

    def fake_load_watch_state(path: Path) -> dict[str, object]:
        seen["loaded"] = str(path)
        return {"schema_version": 1, "updated_at": "2026-04-02T12:00:00+00:00", "controllers": {}}

    def fake_save_watch_state(path: Path, payload: dict[str, object]) -> None:
        seen["saved"] = (str(path), payload)

    def fake_write_timestamped_report(
        *,
        quest_root: Path,
        report_group: str,
        timestamp: str,
        report: dict[str, object],
        markdown: str,
    ) -> tuple[Path, Path]:
        seen["reported"] = (str(quest_root), report_group, timestamp, report, markdown)
        return quest_root / "artifacts" / "reports" / report_group / "latest.json", quest_root / "artifacts" / "reports" / report_group / "latest.md"

    monkeypatch.setattr(module.report_store, "load_watch_state", fake_load_watch_state)
    monkeypatch.setattr(module.report_store, "save_watch_state", fake_save_watch_state)
    monkeypatch.setattr(module.report_store, "write_timestamped_report", fake_write_timestamped_report)

    loaded = module.load_watch_state(quest_root)
    module.save_watch_state(
        quest_root,
        module.RuntimeWatchState(
            schema_version=1,
            updated_at="2026-04-02T12:00:00+00:00",
            controllers={},
        ),
    )
    json_path, md_path = module.write_watch_report(
        quest_root=quest_root,
        report={"scanned_at": "2026-04-02T12:00:00+00:00", "quest_status": "running"},
        markdown="# Runtime Watch Report\n",
    )

    assert loaded == module.RuntimeWatchState(
        schema_version=1,
        updated_at="2026-04-02T12:00:00+00:00",
        controllers={},
    )
    assert seen["loaded"] == str(quest_root)
    assert seen["saved"] == (
        str(quest_root),
        {"schema_version": 1, "updated_at": "2026-04-02T12:00:00+00:00", "controllers": {}},
    )
    assert seen["reported"] == (
        str(quest_root),
        "runtime_watch",
        "2026-04-02T12:00:00+00:00",
        {"scanned_at": "2026-04-02T12:00:00+00:00", "quest_status": "running"},
        "# Runtime Watch Report\n",
    )
    assert json_path.name == "latest.json"
    assert md_path.name == "latest.md"
