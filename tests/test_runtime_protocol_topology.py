from __future__ import annotations

from pathlib import Path

from med_autoscience.runtime_protocol.topology import (
    resolve_paper_root_context,
    resolve_worktree_root_from_paper_root,
)


def test_resolve_worktree_root_from_paper_root_accepts_ds_layout(tmp_path: Path) -> None:
    paper_root = tmp_path / "runtime" / "quests" / "q001" / ".ds" / "worktrees" / "run-001" / "paper"
    paper_root.mkdir(parents=True)

    worktree_root = resolve_worktree_root_from_paper_root(paper_root)

    assert worktree_root == paper_root.parent


def test_resolve_paper_root_context_reads_study_id_from_worktree_quest_yaml(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    paper_root = (
        workspace_root
        / "ops"
        / "med-deepscientist"
        / "runtime"
        / "quests"
        / "001-risk"
        / ".ds"
        / "worktrees"
        / "paper-main"
        / "paper"
    )
    paper_root.mkdir(parents=True)
    (paper_root.parent / "quest.yaml").write_text("quest_id: 001-risk\n", encoding="utf-8")
    study_root = workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    context = resolve_paper_root_context(paper_root)

    assert context.study_id == "001-risk"
    assert context.study_root == study_root
    assert context.worktree_root == paper_root.parent


def test_resolve_paper_root_context_parses_quest_id_with_inline_comment(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    paper_root = (
        workspace_root
        / "ops"
        / "med-deepscientist"
        / "runtime"
        / "quests"
        / "001-risk"
        / ".ds"
        / "worktrees"
        / "paper-main"
        / "paper"
    )
    paper_root.mkdir(parents=True)
    (paper_root.parent / "quest.yaml").write_text("quest_id: 001-risk  # stable identifier\n", encoding="utf-8")
    study_root = workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    context = resolve_paper_root_context(paper_root)

    assert context.study_id == "001-risk"


def test_resolve_paper_root_context_prefers_runtime_reentry_gate_study_id(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    paper_root = (
        workspace_root
        / "ops"
        / "med-deepscientist"
        / "runtime"
        / "quests"
        / "001-risk-reentry-20260403"
        / ".ds"
        / "worktrees"
        / "paper-main"
        / "paper"
    )
    paper_root.mkdir(parents=True)
    (paper_root.parent / "quest.yaml").write_text(
        "quest_id: 001-risk-reentry-20260403\n"
        "startup_contract:\n"
        "  runtime_reentry_gate:\n"
        "    study_id: 001-risk\n",
        encoding="utf-8",
    )
    study_root = workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    context = resolve_paper_root_context(paper_root)

    assert context.study_id == "001-risk"
    assert context.study_root == study_root
