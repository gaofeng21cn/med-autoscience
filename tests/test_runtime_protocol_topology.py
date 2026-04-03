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


def test_resolve_paper_root_context_reads_reentry_study_id_from_nested_startup_contract(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    quest_root = (
        workspace_root
        / "ops"
        / "med-deepscientist"
        / "runtime"
        / "quests"
        / "001-risk-reentry-20260401"
    )
    paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    paper_root.mkdir(parents=True)
    (paper_root.parent / "quest.yaml").write_text("quest_id: 001-risk-reentry-20260401\n", encoding="utf-8")
    (quest_root / "quest.yaml").write_text(
        """quest_id: 001-risk-reentry-20260401
startup_contract:
  runtime_reentry_gate:
    study_id: 001-risk
""",
        encoding="utf-8",
    )
    study_root = workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    context = resolve_paper_root_context(paper_root)

    assert context.study_id == "001-risk"
    assert context.study_root == study_root


def test_resolve_paper_root_context_uses_runtime_binding_for_managed_quest_ids(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    paper_root = (
        workspace_root
        / "ops"
        / "med-deepscientist"
        / "runtime"
        / "quests"
        / "003-endocrine-burden-followup-managed-20260402"
        / ".ds"
        / "worktrees"
        / "paper-main"
        / "paper"
    )
    paper_root.mkdir(parents=True)
    (paper_root.parent / "quest.yaml").write_text(
        "quest_id: 003-endocrine-burden-followup-managed-20260402\n",
        encoding="utf-8",
    )
    study_root = workspace_root / "studies" / "003-endocrine-burden-followup"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 003-endocrine-burden-followup\n", encoding="utf-8")
    (study_root / "runtime_binding.yaml").write_text(
        "\n".join(
            [
                "schema_version: 1",
                "engine: med-deepscientist",
                "study_id: 003-endocrine-burden-followup",
                "quest_id: 003-endocrine-burden-followup-managed-20260402",
                "",
            ]
        ),
        encoding="utf-8",
    )

    context = resolve_paper_root_context(paper_root)

    assert context.study_id == "003-endocrine-burden-followup"
    assert context.study_root == study_root
