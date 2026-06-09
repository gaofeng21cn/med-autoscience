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
    dump_json(
        quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json",
        {
            "quest_id": "q-policy",
            "status": "running",
            "active_run_id": "run-1",
            "active_interaction_id": "progress-1",
        },
    )
    dump_json(
        quest_root / "experiments" / "main" / "run-1" / "RESULT.json",
        {
            "quest_id": "q-policy",
            "run_id": "run-1",
            "worktree_root": str(quest_root),
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
    paper_root = quest_root / "paper"
    dump_json(
        quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json",
        {
            "quest_id": "q-surface",
            "status": "running",
            "active_interaction_id": "progress-1",
        },
    )
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

    monkeypatch.setattr(controller.quest_state, "resolve_active_stdout_path", lambda *, quest_root, runtime_state: None)
    monkeypatch.setattr(controller.quest_state, "read_recent_stdout_lines", lambda stdout_path: [])
    monkeypatch.setattr(controller, "find_latest_gate_report", lambda quest_root: None)
    monkeypatch.setattr(controller.publication_gate_policy, "build_intervention_message", lambda report: "POLICY_GATE_MSG")

    result = controller.run_controller(quest_root=quest_root, apply=True)

    assert result["intervention_enqueued"] is False
    assert result["intervention_handoff"]["runtime_owner"] == "one-person-lab"
    assert result["intervention_handoff"]["message_body_included"] is False
    assert not (quest_root / ".ds" / "user_message_queue.json").exists()


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

    assert result["status"] == "blocked"
    assert result["intervention_enqueued"] is False
    assert result["intervention_handoff"]["queue_owner"] == "one-person-lab"
    assert not (quest_root / ".ds" / "user_message_queue.json").exists()


def test_medical_surface_policy_blocks_work_report_manuscript_residue() -> None:
    policy = importlib.import_module("med_autoscience.policies.medical_publication_surface")
    patterns = policy.get_publication_surface_residue_patterns()
    sample = """
    ## Results
    The first clinical question was whether the score worked. The answer was yes.

    ## Figure and Table Anchors
    Figure 1: cohort derivation

    Reviewers can identify the cohort restriction before reading the results. This figure defines the route.

    Final authorship has not yet been confirmed. Replace this placeholder with author-confirmed text.
    """

    pattern_ids = {
        pattern_id
        for pattern_id, _phrase, pattern in patterns
        if pattern.search(sample)
    }

    assert "work_report_question_answer_frame" in pattern_ids
    assert "figure_table_anchor_section_residue" in pattern_ids
    assert "figure_legend_work_report_residue" in pattern_ids
    assert "submission_placeholder_instruction_residue" in pattern_ids


def test_medical_surface_policy_blocks_invalid_analysis_history_as_main_story() -> None:
    policy = importlib.import_module("med_autoscience.policies.medical_publication_surface")
    patterns = policy.get_publication_surface_residue_patterns()
    sample = """
    ## Discussion
    The raw-scale sensitivity check showed that the earlier raw-scale transport result was
    dominated by a data-processing error. This unit-harmonization lesson defines the paper.
    """

    pattern_ids = {
        pattern_id
        for pattern_id, _phrase, pattern in patterns
        if pattern.search(sample)
    }

    assert "invalid_analysis_history_residue" in pattern_ids
    assert (
        "invalid_analysis_history_residue"
        in policy.medical_journal_prose_blocking_pattern_ids()
    )


def test_medical_surface_policy_message_names_journal_style_rewrite() -> None:
    policy = importlib.import_module("med_autoscience.policies.medical_publication_surface")

    message = policy.build_intervention_message(
        {
            "blockers": ["forbidden_manuscript_terms_present"],
            "top_hits": [
                {
                    "path": "paper/draft.md",
                    "location": "line 10",
                    "pattern_id": "work_report_question_answer_frame",
                    "phrase": "The first clinical question was / the answer was",
                }
            ],
        }
    )

    assert "work-report residue" in message
    assert "journal-style medical prose" in message
