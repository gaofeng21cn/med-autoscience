from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.controllers.study_paper_context import (
    StudyPaperContext,
    resolve_study_paper_context,
    resolve_study_root_from_quest_root,
)


def _write_explicit_context(
    workspace_root: Path,
    *,
    quest_id: str = "quest-001",
    study_id: str = "study-001",
) -> tuple[Path, Path, Path]:
    quest_root = workspace_root / "runtime" / "quests" / quest_id
    paper_root = quest_root / "paper"
    study_root = workspace_root / "studies" / study_id
    paper_root.mkdir(parents=True)
    study_root.mkdir(parents=True)
    (quest_root / "quest.yaml").write_text(
        f"quest_id: {quest_id}\nstudy_id: {study_id}\n",
        encoding="utf-8",
    )
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    return paper_root, quest_root, study_root


def test_canonical_quest_paper_context_reads_explicit_identity_contracts(tmp_path: Path) -> None:
    paper_root, quest_root, study_root = _write_explicit_context(tmp_path / "workspace")

    context = resolve_study_paper_context(paper_root)

    assert context == StudyPaperContext(
        paper_root=paper_root.resolve(),
        context_root=quest_root.resolve(),
        quest_root=quest_root.resolve(),
        quest_id="quest-001",
        study_id="study-001",
        study_root=study_root.resolve(),
    )
    assert resolve_study_root_from_quest_root(quest_root) == ("study-001", study_root.resolve())


def test_stage_native_body_authority_binds_through_explicit_quest_and_study(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    _, quest_root, study_root = _write_explicit_context(workspace_root)
    paper_root = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "manuscript"
    )
    paper_root.mkdir(parents=True)

    context = resolve_study_paper_context(paper_root)

    assert context.paper_root == paper_root.resolve()
    assert context.context_root == paper_root.parent.resolve()
    assert context.quest_root == quest_root.resolve()
    assert context.quest_id == "quest-001"
    assert context.study_id == "study-001"
    assert context.study_root == study_root.resolve()


def test_conflicting_explicit_study_identity_fails_closed(tmp_path: Path) -> None:
    paper_root, _, study_root = _write_explicit_context(tmp_path / "workspace")
    (study_root / "study.yaml").write_text("study_id: other-study\n", encoding="utf-8")

    with pytest.raises(ValueError, match="conflicting study_id declarations"):
        resolve_study_paper_context(paper_root)


def test_conflicting_explicit_quest_identity_fails_closed(tmp_path: Path) -> None:
    paper_root, quest_root, _ = _write_explicit_context(tmp_path / "workspace")
    (quest_root / "quest.yaml").write_text(
        "quest_id: other-quest\nstudy_id: study-001\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="conflicting quest_id declarations"):
        resolve_study_paper_context(paper_root)


def test_nonexplicit_study_identity_is_not_a_fallback(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    paper_root, quest_root, _ = _write_explicit_context(workspace_root)
    (quest_root / "quest.yaml").write_text(
        "quest_id: quest-001\nstudy:\n  id: study-001\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing explicit study_id"):
        resolve_study_paper_context(paper_root)


def test_stage_native_binding_requires_one_explicit_quest_identity(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    _, _, study_root = _write_explicit_context(workspace_root)
    second_quest_root = workspace_root / "runtime" / "quests" / "quest-002"
    second_quest_root.mkdir(parents=True)
    (second_quest_root / "quest.yaml").write_text(
        "quest_id: quest-002\nstudy_id: study-001\n",
        encoding="utf-8",
    )
    paper_root = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
    )
    paper_root.mkdir(parents=True)

    with pytest.raises(ValueError, match="multiple canonical quest identities"):
        resolve_study_paper_context(paper_root)


def test_requested_quest_identity_must_match_explicit_contract(tmp_path: Path) -> None:
    _, quest_root, _ = _write_explicit_context(tmp_path / "workspace")

    with pytest.raises(ValueError, match="conflicting quest_id declarations"):
        resolve_study_root_from_quest_root(quest_root, quest_id="other-quest")
