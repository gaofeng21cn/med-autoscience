from __future__ import annotations

import importlib
from pathlib import Path

from med_autoscience.runtime_protocol.topology import PaperRootContext


def test_replay_post_submission_minimal_sync_refreshes_gate_and_progress(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal_parts.post_materialization_sync")
    paper_root = tmp_path / "paper"
    context = PaperRootContext(
        paper_root=paper_root,
        worktree_root=tmp_path / "paper-run",
        quest_root=tmp_path / "runtime" / "quests" / "quest-001",
        quest_id="quest-001",
        study_id="001-risk",
        study_root=tmp_path / "studies" / "001-risk",
    )
    gate_calls: list[tuple[Path, bool, str, bool]] = []
    progress_calls: list[tuple[object, Path, str, Path]] = []

    monkeypatch.setattr(module, "resolve_paper_root_context", lambda _paper_root: context)
    monkeypatch.setattr(
        module,
        "_resolve_profile_for_study_root",
        lambda study_root: (tmp_path / "profiles" / "test.local.toml", object()),
    )

    def fake_gate_run_controller(
        *,
        quest_root: Path,
        apply: bool,
        source: str,
        enqueue_intervention: bool,
    ) -> dict[str, object]:
        gate_calls.append((quest_root, apply, source, enqueue_intervention))
        return {
            "status": "clear",
            "allow_write": True,
            "current_required_action": "continue_bundle_stage",
            "journal_package_sync": {
                "status": "materialized",
            },
            "report_json": "/tmp/gate/latest.json",
        }

    def fake_read_study_progress(
        *,
        profile: object,
        profile_ref: Path,
        study_id: str,
        study_root: Path,
    ) -> dict[str, object]:
        progress_calls.append((profile, profile_ref, study_id, study_root))
        return {
            "current_stage": "manual_finishing",
            "current_stage_summary": "投稿包里程碑已达成，当前保持 parked。",
            "next_system_action": "等待显式 resume 或提交元数据。",
            "refs": {
                "evaluation_summary_path": "/tmp/eval/latest.json",
                "runtime_status_summary_path": "/tmp/runtime/runtime_status_summary.json",
                "publication_eval_path": "/tmp/publication_eval/latest.json",
            },
        }

    monkeypatch.setattr(module.publication_gate, "run_controller", fake_gate_run_controller)
    monkeypatch.setattr(module.study_progress, "read_study_progress", fake_read_study_progress)

    result = module.replay_post_submission_minimal_sync(paper_root=paper_root)

    assert gate_calls == [
        (
            context.quest_root,
            True,
            "submission-minimal-post-materialization",
            False,
        )
    ]
    assert progress_calls == [
        (
            progress_calls[0][0],
            tmp_path / "profiles" / "test.local.toml",
            "001-risk",
            context.study_root,
        )
    ]
    assert result == {
        "status": "synced",
        "quest_root": str(context.quest_root),
        "study_root": str(context.study_root),
        "gate_replay": {
            "status": "clear",
            "allow_write": True,
            "current_required_action": "continue_bundle_stage",
            "report_json": "/tmp/gate/latest.json",
            "journal_package_sync": {
                "status": "materialized",
            },
        },
        "progress_refresh": {
            "current_stage": "manual_finishing",
            "current_stage_summary": "投稿包里程碑已达成，当前保持 parked。",
            "next_system_action": "等待显式 resume 或提交元数据。",
            "evaluation_summary_path": "/tmp/eval/latest.json",
            "runtime_status_summary_path": "/tmp/runtime/runtime_status_summary.json",
            "publication_eval_path": "/tmp/publication_eval/latest.json",
        },
    }


def test_replay_post_submission_minimal_sync_skips_progress_refresh_when_profile_is_unresolved(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal_parts.post_materialization_sync")
    paper_root = tmp_path / "paper"
    context = PaperRootContext(
        paper_root=paper_root,
        worktree_root=tmp_path / "paper-run",
        quest_root=tmp_path / "runtime" / "quests" / "quest-001",
        quest_id="quest-001",
        study_id="001-risk",
        study_root=tmp_path / "studies" / "001-risk",
    )

    monkeypatch.setattr(module, "resolve_paper_root_context", lambda _paper_root: context)
    monkeypatch.setattr(module, "_resolve_profile_for_study_root", lambda study_root: (None, None))
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {
            "status": "clear",
            "allow_write": True,
            "current_required_action": "continue_bundle_stage",
            "report_json": "/tmp/gate/latest.json",
            "journal_package_sync": None,
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: (_ for _ in ()).throw(AssertionError("progress refresh should be skipped")),
    )

    result = module.replay_post_submission_minimal_sync(paper_root=paper_root)

    assert result["status"] == "gate_replayed_profile_unresolved"
    assert result["progress_refresh"] == {
        "status": "skipped_profile_unresolved",
    }
