from __future__ import annotations

import importlib
import json
import re
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_gate_quest(tmp_path: Path) -> Path:
    quest_root = tmp_path / "runtime" / "quests" / "q-policy"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-run-1"
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "q-policy",
            "status": "running",
            "active_run_id": "run-1",
            "active_interaction_id": "progress-1",
        },
    )
    dump_json(
        worktree_root / "experiments" / "main" / "run-1" / "RESULT.json",
        {
            "quest_id": "q-policy",
            "run_id": "run-1",
            "worktree_root": str(worktree_root),
            "metric_contract": {"required_non_scalar_deliverables": []},
            "metrics_summary": {
                "roc_auc": 0.81,
                "average_precision": 0.45,
                "brier_score": 0.11,
                "calibration_intercept": 0.02,
                "calibration_slope": 1.01,
            },
            "baseline_comparisons": {"items": []},
            "results_summary": "summary",
            "conclusion": "conclusion",
        },
    )
    return quest_root


def make_surface_quest(tmp_path: Path) -> Path:
    quest_root = tmp_path / "runtime" / "quests" / "q-surface"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "q-surface",
            "status": "running",
            "active_interaction_id": "progress-1",
        },
    )
    dump_json(
        quest_root / ".ds" / "user_message_queue.json",
        {"version": 1, "pending": [], "completed": []},
    )
    (quest_root / ".ds" / "interaction_journal.jsonl").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / ".ds" / "interaction_journal.jsonl").write_text("", encoding="utf-8")
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {"schema_version": 1},
    )
    (paper_root / "draft.md").write_text("Extended preoperative model.\n", encoding="utf-8")
    (paper_root / "build").mkdir(parents=True, exist_ok=True)
    (paper_root / "build" / "review_manuscript.md").write_text("Extended preoperative model.\n", encoding="utf-8")
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    (paper_root / "latex").mkdir(parents=True, exist_ok=True)
    (paper_root / "latex" / "american-medical-association.csl").write_text("csl", encoding="utf-8")
    (paper_root / "latex" / "review_defaults.yaml").write_text(
        "csl: american-medical-association.csl\n",
        encoding="utf-8",
    )
    (paper_root / "paper.pdf").write_text("%PDF", encoding="utf-8")
    return quest_root


def test_publication_gate_uses_policy_message_builder(tmp_path: Path, monkeypatch) -> None:
    controller = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_gate_quest(tmp_path)

    monkeypatch.setattr(controller.runtime, "resolve_active_stdout_path", lambda *, quest_root, runtime_state: None)
    monkeypatch.setattr(controller.runtime, "read_recent_stdout_lines", lambda stdout_path: [])
    monkeypatch.setattr(controller, "find_latest_gate_report", lambda quest_root: None)
    monkeypatch.setattr(controller.publication_gate_policy, "build_intervention_message", lambda report: "POLICY_GATE_MSG")

    result = controller.run_controller(quest_root=quest_root, apply=True)

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert result["intervention_enqueued"] is True
    assert queue["pending"][0]["content"] == "POLICY_GATE_MSG"


def test_medical_surface_uses_policy_forbidden_patterns_and_message_builder(tmp_path: Path, monkeypatch) -> None:
    controller = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_surface_quest(tmp_path)

    monkeypatch.setattr(
        controller.medical_surface_policy,
        "get_forbidden_patterns",
        lambda: [("extended", "Extended preoperative model", re.compile(r"Extended preoperative model"))],
    )
    monkeypatch.setattr(
        controller.medical_surface_policy,
        "build_intervention_message",
        lambda report: "POLICY_SURFACE_MSG",
    )

    result = controller.run_controller(quest_root=quest_root, apply=True, daemon_url=None)

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert result["status"] == "blocked"
    assert result["intervention_enqueued"] is True
    assert queue["pending"][0]["content"] == "POLICY_SURFACE_MSG"
