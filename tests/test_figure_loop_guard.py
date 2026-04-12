from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from med_autoscience.figure_routes import (
    FIGURE_ROUTE_ILLUSTRATION_PROGRAM,
    FIGURE_ROUTE_SCRIPT_FIX,
    build_figure_route,
)


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def make_quest(tmp_path: Path) -> tuple[Path, Path]:
    quest_root = tmp_path / "runtime" / "quests" / "002-early-residual-risk"
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "002-early-residual-risk",
            "status": "running",
            "active_run_id": "run-loop",
            "active_interaction_id": "progress-loop",
            "pending_user_message_count": 0,
        },
    )
    append_jsonl(
        quest_root / ".ds" / "runs" / "run-loop" / "stdout.jsonl",
        [
            {
                "timestamp": "2026-03-28T23:54:00+00:00",
                "line": '{"type":"turn.started"}',
            }
        ],
    )
    dump_json(quest_root / ".ds" / "user_message_queue.json", {"version": 1, "pending": [], "completed": []})
    (quest_root / ".ds" / "interaction_journal.jsonl").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / ".ds" / "interaction_journal.jsonl").write_text("", encoding="utf-8")
    references = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "references.bib"
    references.parent.mkdir(parents=True, exist_ok=True)
    references.write_text(
        "\n".join(f"@article{{ref{i}, title={{{{Ref {i}}}}}}}" for i in range(1, 8)) + "\n",
        encoding="utf-8",
    )
    outbox_path = tmp_path / "runtime" / "logs" / "connectors" / "local" / "outbox.jsonl"
    append_jsonl(
        outbox_path,
        [
            {
                "sent_at": "2026-03-28T23:55:14+00:00",
                "quest_id": "002-early-residual-risk",
                "quest_root": str(quest_root),
                "kind": "assistant",
                "message": "`Figure 4B` 已收住，之后不再继续修改。",
            },
            {
                "sent_at": "2026-03-28T23:58:14+00:00",
                "quest_id": "002-early-residual-risk",
                "quest_root": str(quest_root),
                "kind": "progress",
                "message": "我继续只处理 `Figure 4B`，先把真实成品、回归和导出层重新对齐。",
            },
            {
                "sent_at": "2026-03-29T00:01:14+00:00",
                "quest_id": "002-early-residual-risk",
                "quest_root": str(quest_root),
                "kind": "progress",
                "message": "现在真实数值已经复出来了：`Figure 4B` 的短中间行仍然右漂。",
            },
            {
                "sent_at": "2026-03-29T00:04:14+00:00",
                "quest_id": "002-early-residual-risk",
                "quest_root": str(quest_root),
                "kind": "progress",
                "message": "我又往前确认了一层：单靠整组三行一起左右平移，不可能把 `Figure 4B` 同时压稳。",
            },
        ],
    )
    return quest_root, outbox_path


def test_build_guard_report_flags_reopened_accepted_figure_and_reference_floor(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.figure_loop_guard")
    quest_root, outbox_path = make_quest(tmp_path)

    state = module.build_guard_state(
        quest_root,
        outbox_path=outbox_path,
        accepted_figures={"F4B": "teacher approved final layout"},
        figure_tickets={"F3C": "text overflow outside panel boxes"},
        required_routes=[
            "literature_scout",
            "expand_references",
            "revise_manuscript_body",
            build_figure_route(FIGURE_ROUTE_SCRIPT_FIX, "F3C"),
            build_figure_route(FIGURE_ROUTE_ILLUSTRATION_PROGRAM, "F5A"),
        ],
        min_figure_mentions=3,
        min_reference_count=12,
    )
    report = module.build_guard_report(state)

    assert report["dominant_figure_id"] == "F4B"
    assert report["dominant_figure_mentions"] == 4
    assert report["reopen_detected"] is True
    assert report["reference_count"] == 7
    assert "figure_loop_budget_exceeded" in report["blockers"]
    assert "accepted_figure_reopened" in report["blockers"]
    assert "references_below_floor_during_figure_loop" in report["blockers"]
    assert report["recommended_action"] == "stop_current_run_and_route_mainline"
    assert report["accepted_figures"] == {"F4B": "teacher approved final layout"}
    assert report["figure_tickets"] == {"F3C": "text overflow outside panel boxes"}
    assert report["required_routes"] == [
        "literature_scout",
        "expand_references",
        "revise_manuscript_body",
        build_figure_route(FIGURE_ROUTE_SCRIPT_FIX, "F3C"),
        build_figure_route(FIGURE_ROUTE_ILLUSTRATION_PROGRAM, "F5A"),
    ]


def test_figure_loop_guard_reuses_shared_figure_token_normalizer() -> None:
    guard_module = importlib.import_module("med_autoscience.controllers.figure_loop_guard")
    routes_module = importlib.import_module("med_autoscience.figure_routes")

    assert guard_module.normalize_figure_token is routes_module.normalize_figure_token


def test_build_guard_state_rejects_ambiguous_sidecar_route(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.figure_loop_guard")
    quest_root, outbox_path = make_quest(tmp_path)

    with pytest.raises(ValueError, match="Ambiguous figure sidecar route"):
        module.build_guard_state(
            quest_root,
            outbox_path=outbox_path,
            required_routes=["literature_scout", "sidecar:F3C"],
        )


def test_build_guard_state_filters_outbox_rows_by_normalized_quest_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.figure_loop_guard")
    quest_root, outbox_path = make_quest(tmp_path)
    existing_rows = [
        json.loads(line)
        for line in outbox_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    append_jsonl(
        outbox_path,
        existing_rows
        + [
            {
                "sent_at": "2026-03-29T00:05:14+00:00",
                "quest_id": quest_root.name,
                "quest_root": str((tmp_path / "runtime" / "quests" / "legacy-root").resolve()),
                "kind": "progress",
                "message": "我继续只处理 `Figure 4B` 的旧路径遗留问题。",
            },
            {
                "sent_at": "2026-03-29T00:06:14+00:00",
                "quest_id": quest_root.name,
                "quest_root": str(quest_root),
                "kind": "progress",
                "message": "当前 quest 只剩 `Figure 3A` 的一处注释重叠。",
            },
        ],
    )

    state = module.build_guard_state(
        quest_root,
        outbox_path=outbox_path,
        min_figure_mentions=4,
    )

    assert state.figure_counts["F4B"] == 4
    assert state.figure_counts["F3A"] == 1
    assert state.dominant_figure_id == "F4B"
    assert state.dominant_figure_mentions == 4


def test_build_guard_state_ignores_figure_mentions_before_active_run_start(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.figure_loop_guard")
    quest_root, outbox_path = make_quest(tmp_path)
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": quest_root.name,
            "status": "running",
            "active_run_id": "run-loop",
            "active_interaction_id": "progress-loop",
            "pending_user_message_count": 0,
            "last_resume_at": "2026-03-29T00:09:59+00:00",
        },
    )
    append_jsonl(
        quest_root / ".ds" / "runs" / "run-loop" / "stdout.jsonl",
        [
            {
                "timestamp": "2026-03-29T00:10:00+00:00",
                "line": '{"type":"turn.started"}',
            }
        ],
    )

    state = module.build_guard_state(
        quest_root,
        outbox_path=outbox_path,
        min_figure_mentions=3,
    )
    report = module.build_guard_report(state)

    assert state.figure_counts == {}
    assert state.recent_outbox_rows == []
    assert report["status"] == "clear"
    assert report["blockers"] == []


def test_build_guard_report_does_not_block_without_active_run(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.figure_loop_guard")
    quest_root, outbox_path = make_quest(tmp_path)
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": quest_root.name,
            "status": "active",
            "active_run_id": None,
            "active_interaction_id": "progress-loop",
            "pending_user_message_count": 0,
        },
    )

    state = module.build_guard_state(
        quest_root,
        outbox_path=outbox_path,
        min_figure_mentions=3,
    )
    report = module.build_guard_report(state)

    assert report["status"] == "clear"
    assert report["blockers"] == []
    assert report["recommended_action"] == "continue_current_run"


def test_run_controller_stops_then_enqueues_route_message(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.figure_loop_guard")
    quest_root, outbox_path = make_quest(tmp_path)
    stopped: list[tuple[str | None, str | None, str, str]] = []

    def fake_stop_quest(
        *,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
        quest_id: str,
        source: str,
    ) -> dict:
        stopped.append((daemon_url, str(runtime_root) if runtime_root is not None else None, quest_id, source))
        return {"ok": True, "interrupted": True, "status": "stopped", "source": source}

    monkeypatch.setattr(module.managed_runtime_transport, "stop_quest", fake_stop_quest)

    result = module.run_controller(
        quest_root=quest_root,
        apply=True,
        outbox_path=outbox_path,
        daemon_url="http://127.0.0.1:20999",
        accepted_figures={"F4B": "teacher approved final layout"},
        figure_tickets={"F3C": "text overflow outside panel boxes"},
        required_routes=[
            "literature_scout",
            "expand_references",
            "revise_manuscript_body",
            build_figure_route(FIGURE_ROUTE_SCRIPT_FIX, "F3C"),
            build_figure_route(FIGURE_ROUTE_ILLUSTRATION_PROGRAM, "F5A"),
        ],
        min_figure_mentions=3,
        min_reference_count=12,
    )

    assert module.managed_runtime_transport is module.med_deepscientist_transport
    assert stopped == [
        (
            "http://127.0.0.1:20999",
            str((quest_root.parent.parent).resolve()),
            "002-early-residual-risk",
            "medautosci-figure-loop-guard",
        )
    ]
    assert result["intervention_enqueued"] is True
    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert len(queue["pending"]) == 1
    content = queue["pending"][0]["content"]
    assert "F4B" in content
    assert "F3C" in content
    assert "F5A" in content
    assert "literature_scout" in content
    assert build_figure_route(FIGURE_ROUTE_SCRIPT_FIX, "F3C") in content
    assert build_figure_route(FIGURE_ROUTE_ILLUSTRATION_PROGRAM, "F5A") in content
    assert "script/data repair route" in content
    assert "programmatic illustration route" in content


def test_build_guard_state_uses_runtime_protocol_quest_state(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.figure_loop_guard")
    quest_root, outbox_path = make_quest(tmp_path)
    original_load_json = module.load_json
    seen: dict[str, object] = {}

    def fake_load_runtime_state(path: Path) -> dict[str, object]:
        seen["quest_root"] = path
        return {"status": "patched", "quest_id": quest_root.name}

    def fake_find_latest(paths: list[Path]) -> Path | None:
        seen["candidate_count"] = len(paths)
        return next(iter(paths), None)

    monkeypatch.setattr(module.quest_state, "load_runtime_state", fake_load_runtime_state)
    monkeypatch.setattr(module.quest_state, "find_latest", fake_find_latest)
    monkeypatch.setattr(module, "load_json", lambda path, default=None: {} if path.name == "runtime_state.json" else original_load_json(path, default))

    state = module.build_guard_state(quest_root, outbox_path=outbox_path)

    assert seen["quest_root"] == quest_root
    assert seen["candidate_count"] >= 1
    assert state.runtime_state["status"] == "patched"


def test_write_guard_files_uses_runtime_protocol_report_store(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.figure_loop_guard")
    quest_root, _ = make_quest(tmp_path)
    seen: dict[str, object] = {}

    def fake_write_timestamped_report(
        *,
        quest_root: Path,
        report_group: str,
        timestamp: str,
        report: dict[str, object],
        markdown: str,
    ) -> tuple[Path, Path]:
        seen["quest_root"] = quest_root
        seen["report_group"] = report_group
        seen["timestamp"] = timestamp
        seen["report"] = report
        seen["markdown"] = markdown
        return quest_root / "artifacts" / "reports" / report_group / "latest.json", quest_root / "artifacts" / "reports" / report_group / "latest.md"

    monkeypatch.setattr(module.runtime_protocol_report_store, "write_timestamped_report", fake_write_timestamped_report)

    report = {
        "generated_at": "2026-03-29T03:50:50+00:00",
        "quest_id": quest_root.name,
        "status": "blocked",
        "recommended_action": "stop_current_run_and_route_mainline",
        "dominant_figure_id": "F4B",
        "dominant_figure_mentions": 4,
        "reopen_detected": True,
        "reference_count": 7,
        "reference_floor": 12,
        "accepted_figures": {},
        "figure_tickets": {},
        "required_routes": [],
        "controller_note": "note",
    }

    json_path, md_path = module.write_guard_files(quest_root, report)

    assert seen["quest_root"] == quest_root
    assert seen["report_group"] == "figure_loop_guard"
    assert seen["timestamp"] == "2026-03-29T03:50:50+00:00"
    assert json_path.name == "latest.json"
    assert md_path.name == "latest.md"
