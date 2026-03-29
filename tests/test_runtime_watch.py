from __future__ import annotations

import importlib
import json
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_quest(tmp_path: Path, name: str, status: str = "running") -> Path:
    quest_root = tmp_path / "runtime" / "quests" / name
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": name,
            "status": status,
            "active_run_id": "run-1" if status in {"running", "active"} else None,
        },
    )
    return quest_root


def test_applies_new_blocker_once(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[tuple[str, bool]] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append((quest_root.name, apply))
        return {
            "status": "blocked",
            "blockers": ["missing_post_main_publishability_gate"],
            "allow_write": False,
            "missing_non_scalar_deliverables": ["calibration_plot"],
            "submission_minimal_present": False,
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=True,
    )

    assert calls == [("q001", False), ("q001", True)]
    assert result["controllers"]["publication_gate"]["action"] == "applied"


def test_suppresses_duplicate_blocker(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["forbidden_manuscript_terms_present"],
            "report_json": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.md"),
            "top_hits": [{"path": "paper/draft.md", "location": "line 1", "phrase": "deployment-facing"}],
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_publication_surface"]["action"] == "applied"
    assert second["controllers"]["medical_publication_surface"]["action"] == "suppressed"
    assert calls == [False, True, False]


def test_blocked_with_apply_disabled_records_suppression_without_second_apply(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["missing_post_main_publishability_gate"],
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
        }

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"publication_gate": fake_runner},
        apply=False,
    )

    assert result["controllers"]["publication_gate"]["action"] == "suppressed"
    assert result["controllers"]["publication_gate"]["suppression_reason"] == "apply_disabled"
    assert calls == [False]


def test_reapplies_when_fingerprint_changes(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, "q001", status="running")
    state = {"value": "deployment-facing"}
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["forbidden_manuscript_terms_present"],
            "report_json": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.md"),
            "top_hits": [{"path": "paper/draft.md", "location": "line 1", "phrase": state["value"]}],
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )
    state["value"] = "baseline-comparable"
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"medical_publication_surface": fake_runner},
        apply=True,
    )

    assert first["controllers"]["medical_publication_surface"]["action"] == "applied"
    assert second["controllers"]["medical_publication_surface"]["action"] == "applied"
    assert calls == [False, True, False, True]


def test_scan_runtime_only_processes_active_quests(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    runtime_root = tmp_path / "runtime" / "quests"
    make_quest(tmp_path, "q-running", status="running")
    make_quest(tmp_path, "q-active", status="active")
    make_quest(tmp_path, "q-stopped", status="stopped")
    make_quest(tmp_path, "q-completed", status="completed")
    seen: list[str] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        seen.append(quest_root.name)
        return {
            "status": "clear",
            "blockers": [],
            "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            "intervention_enqueued": False,
        }

    result = module.run_watch_for_runtime(
        runtime_root=runtime_root,
        controller_runners={"publication_gate": fake_runner},
        apply=False,
    )

    assert sorted(seen) == ["q-active", "q-running"]
    assert sorted(result["scanned_quests"]) == ["q-active", "q-running"]


def test_suppresses_duplicate_data_asset_gate_blocker(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["outdated_private_release"],
            "study_id": quest_root.name,
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "suppressed"
    assert calls == [False, True, False]


def test_applies_data_asset_gate_advisory_once(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "advisory",
            "blockers": [],
            "advisories": ["public_data_extension_available"],
            "study_id": quest_root.name,
            "public_support_dataset_ids": ["geo-gse000001"],
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["status"] == "advisory"
    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "suppressed"
    assert calls == [False, True, False]


def test_reapplies_data_asset_gate_when_unresolved_dataset_ids_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []
    state = {"unresolved_dataset_ids": ["ds_a"]}

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["unresolved_private_data_contract"],
            "advisories": [],
            "study_id": quest_root.name,
            "outdated_dataset_ids": [],
            "unresolved_dataset_ids": list(state["unresolved_dataset_ids"]),
            "public_support_dataset_ids": [],
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    state["unresolved_dataset_ids"] = ["ds_b"]
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "applied"
    assert calls == [False, True, False, True]
