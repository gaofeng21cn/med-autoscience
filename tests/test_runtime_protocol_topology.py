from __future__ import annotations

from pathlib import Path

import pytest

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


def test_resolve_paper_root_context_accepts_projected_quest_paper_root(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    quest_root = (
        workspace_root
        / "ops"
        / "med-deepscientist"
        / "runtime"
        / "quests"
        / "004-invasive-architecture-managed-20260408"
    )
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    projected_paper_root = quest_root / "paper"
    worktree_paper_root.mkdir(parents=True)
    projected_paper_root.mkdir(parents=True)
    (worktree_paper_root.parent / "quest.yaml").write_text(
        "quest_id: 004-invasive-architecture-managed-20260408\n"
        "runtime_reentry_gate:\n"
        "  study_id: 004-invasive-architecture\n",
        encoding="utf-8",
    )
    (quest_root / "quest.yaml").write_text(
        "quest_id: 004-invasive-architecture-managed-20260408\n"
        "runtime_reentry_gate:\n"
        "  study_id: 004-invasive-architecture\n",
        encoding="utf-8",
    )
    (projected_paper_root / "paper_bundle_manifest.json").write_text("{}\n", encoding="utf-8")
    (projected_paper_root / "paper_line_state.json").write_text(
        "{\n"
        f'  "paper_root": "{worktree_paper_root.resolve().as_posix()}"\n'
        "}\n",
        encoding="utf-8",
    )
    study_root = workspace_root / "studies" / "004-invasive-architecture"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 004-invasive-architecture\n", encoding="utf-8")

    context = resolve_paper_root_context(projected_paper_root)

    assert context.paper_root == worktree_paper_root.resolve()
    assert context.worktree_root == worktree_paper_root.parent.resolve()
    assert context.quest_root == quest_root.resolve()
    assert context.quest_id == "004-invasive-architecture-managed-20260408"
    assert context.study_id == "004-invasive-architecture"
    assert context.study_root == study_root.resolve()


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


def test_resolve_paper_root_context_uses_runtime_reentry_gate_study_id_for_managed_quest(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    paper_root = (
        workspace_root
        / "ops"
        / "med-deepscientist"
        / "runtime"
        / "quests"
        / "001-risk-managed-20260402"
        / ".ds"
        / "worktrees"
        / "paper-main"
        / "paper"
    )
    paper_root.mkdir(parents=True)
    (paper_root.parent / "quest.yaml").write_text(
        "\n".join(
            [
                "quest_id: 001-risk-managed-20260402",
                "runtime_reentry_gate:",
                "  study_id: 001-risk",
                "",
            ]
        ),
        encoding="utf-8",
    )
    study_root = workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    context = resolve_paper_root_context(paper_root)

    assert context.study_id == "001-risk"
    assert context.study_root == study_root


def test_resolve_paper_root_context_uses_nested_startup_contract_runtime_reentry_gate_study_id(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    paper_root = (
        workspace_root
        / "ops"
        / "med-deepscientist"
        / "runtime"
        / "quests"
        / "001-risk-managed-20260402"
        / ".ds"
        / "worktrees"
        / "paper-main"
        / "paper"
    )
    paper_root.mkdir(parents=True)
    (paper_root.parent / "quest.yaml").write_text(
        "\n".join(
            [
                "quest_id: 001-risk-managed-20260402",
                "startup_contract:",
                "  runtime_reentry_gate:",
                "    study_id: 001-risk",
                "",
            ]
        ),
        encoding="utf-8",
    )
    study_root = workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    context = resolve_paper_root_context(paper_root)

    assert context.study_id == "001-risk"
    assert context.study_root == study_root


def test_resolve_paper_root_context_uses_nested_startup_contract_study_id(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    paper_root = (
        workspace_root
        / "ops"
        / "med-deepscientist"
        / "runtime"
        / "quests"
        / "001-risk-managed-20260402"
        / ".ds"
        / "worktrees"
        / "paper-main"
        / "paper"
    )
    paper_root.mkdir(parents=True)
    (paper_root.parent / "quest.yaml").write_text(
        "\n".join(
            [
                "quest_id: 001-risk-managed-20260402",
                "startup_contract:",
                "  study_id: 001-risk",
                "",
            ]
        ),
        encoding="utf-8",
    )
    study_root = workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    context = resolve_paper_root_context(paper_root)

    assert context.study_id == "001-risk"
    assert context.study_root == study_root


def test_resolve_paper_root_context_reads_reentry_study_id_from_quest_root_nested_startup_contract(tmp_path: Path) -> None:
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


def test_resolve_paper_root_context_reads_reentry_study_id_from_quest_root_startup_contract(tmp_path: Path) -> None:
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

    assert context.quest_id == "003-endocrine-burden-followup-managed-20260402"
    assert context.study_id == "003-endocrine-burden-followup"
    assert context.study_root == study_root


def test_resolve_paper_root_context_rejects_conflicting_declared_study_ids(tmp_path: Path) -> None:
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
    (paper_root.parent / "quest.yaml").write_text(
        """quest_id: 001-risk-reentry-20260401
runtime_reentry_gate:
  study_id: 001-risk
""",
        encoding="utf-8",
    )
    (quest_root / "quest.yaml").write_text(
        """quest_id: 001-risk-reentry-20260401
startup_contract:
  study_id: 002-risk
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="conflicting study_id declarations"):
        resolve_paper_root_context(paper_root)
