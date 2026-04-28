from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

from med_autoscience.runtime_protocol.topology import PaperRootContext


def test_replay_post_submission_minimal_sync_restores_submission_minimal_after_gate_replay(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal_parts.post_materialization_sync")
    paper_root = tmp_path / "paper"
    submission_root = paper_root / "submission_minimal"
    current_package_root = tmp_path / "studies" / "001-risk" / "manuscript" / "current_package"
    submission_manuscript = submission_root / "manuscript_submission.md"
    current_package_manuscript = current_package_root / "manuscript_submission.md"
    submission_manuscript.parent.mkdir(parents=True, exist_ok=True)
    current_package_manuscript.parent.mkdir(parents=True, exist_ok=True)
    submission_manuscript.write_text("# Fresh Submission\n\nfirst-pass revision retained\n", encoding="utf-8")
    current_package_manuscript.write_text("# Old Current Package\n\nfirst-pass revision missing\n", encoding="utf-8")
    context = PaperRootContext(
        paper_root=paper_root,
        worktree_root=tmp_path / "paper-run",
        quest_root=tmp_path / "runtime" / "quests" / "quest-001",
        quest_id="quest-001",
        study_id="001-risk",
        study_root=tmp_path / "studies" / "001-risk",
    )
    calls: list[str] = []

    monkeypatch.setattr(module, "resolve_paper_root_context", lambda _paper_root: context)
    monkeypatch.setattr(
        module,
        "_resolve_profile_for_study_root",
        lambda study_root: (tmp_path / "profiles" / "test.local.toml", object()),
    )

    def fake_gate_run_controller(**_: object) -> dict[str, object]:
        calls.append("gate")
        current_package_manuscript.write_text("# Old Gate Projection\n\nfirst-pass revision missing\n", encoding="utf-8")
        return {
            "status": "blocked",
            "allow_write": False,
            "current_required_action": "complete_bundle_stage",
            "report_json": "/tmp/gate/latest.json",
            "journal_package_sync": {
                "status": "materialized",
            },
        }

    def fake_sync_study_delivery(**_: object) -> dict[str, object]:
        calls.append("final_sync")
        current_package_manuscript.write_text(submission_manuscript.read_text(encoding="utf-8"), encoding="utf-8")
        return {
            "stage": "submission_minimal",
            "status": "synced",
            "current_package_root": str(current_package_root),
        }

    monkeypatch.setattr(module.publication_gate, "run_controller", fake_gate_run_controller)
    monkeypatch.setattr(
        module,
        "study_delivery_sync",
        SimpleNamespace(
            can_sync_study_delivery=lambda *, paper_root: True,
            sync_study_delivery=fake_sync_study_delivery,
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "current_stage": "manual_finishing",
            "current_stage_summary": "投稿包里程碑已达成，当前保持 parked。",
            "next_system_action": "等待显式 resume 或提交元数据。",
            "refs": {},
        },
    )
    monkeypatch.setattr(
        module.study_outer_loop,
        "refresh_parked_submission_milestone_controller_decision",
        lambda **_: {"status": "refreshed"},
    )

    result = module.replay_post_submission_minimal_sync(paper_root=paper_root)

    assert calls == ["gate", "final_sync"]
    assert current_package_manuscript.read_text(encoding="utf-8") == submission_manuscript.read_text(encoding="utf-8")
    assert result["post_gate_delivery_sync"] == {
        "stage": "submission_minimal",
        "status": "synced",
        "current_package_root": str(current_package_root),
    }


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
    decision_refresh_calls: list[tuple[object, Path, str]] = []
    sync_calls: list[tuple[Path, str, str]] = []

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
    monkeypatch.setattr(
        module,
        "study_delivery_sync",
        SimpleNamespace(
            can_sync_study_delivery=lambda *, paper_root: True,
            sync_study_delivery=lambda *, paper_root, stage, publication_profile: (
                sync_calls.append((paper_root, stage, publication_profile)),
                {"status": "synced", "stage": stage, "publication_profile": publication_profile},
            )[1],
        ),
        raising=False,
    )
    monkeypatch.setattr(module.study_progress, "read_study_progress", fake_read_study_progress)
    monkeypatch.setattr(
        module.study_outer_loop,
        "refresh_parked_submission_milestone_controller_decision",
        lambda *, profile, study_root, study_id, source: (
            decision_refresh_calls.append((profile, study_root, study_id)),
            {
                "status": "refreshed",
                "decision_type": "continue_same_line",
                "route_target": "finalize",
            },
        )[1],
    )

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
    assert decision_refresh_calls == [
        (
            decision_refresh_calls[0][0],
            context.study_root,
            "001-risk",
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
        "post_gate_delivery_sync": {
            "status": "synced",
            "stage": "submission_minimal",
            "publication_profile": "general_medical_journal",
        },
        "progress_refresh": {
            "current_stage": "manual_finishing",
            "current_stage_summary": "投稿包里程碑已达成，当前保持 parked。",
            "next_system_action": "等待显式 resume 或提交元数据。",
            "evaluation_summary_path": "/tmp/eval/latest.json",
            "runtime_status_summary_path": "/tmp/runtime/runtime_status_summary.json",
            "publication_eval_path": "/tmp/publication_eval/latest.json",
        },
        "controller_decision_refresh": {
            "status": "refreshed",
            "decision_type": "continue_same_line",
            "route_target": "finalize",
        },
    }
    assert sync_calls == [(context.paper_root, "submission_minimal", "general_medical_journal")]


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
        module,
        "study_delivery_sync",
        SimpleNamespace(
            can_sync_study_delivery=lambda *, paper_root: True,
            sync_study_delivery=lambda *, paper_root, stage, publication_profile: {
                "status": "synced",
                "stage": stage,
                "publication_profile": publication_profile,
            },
        ),
        raising=False,
    )
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
    assert result["post_gate_delivery_sync"] == {
        "status": "synced",
        "stage": "submission_minimal",
        "publication_profile": "general_medical_journal",
    }
    assert result["progress_refresh"] == {
        "status": "skipped_profile_unresolved",
    }
