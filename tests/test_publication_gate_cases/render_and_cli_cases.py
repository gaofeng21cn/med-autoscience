from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_build_gate_report_prefers_runtime_paper_worktree_over_stale_projected_mirror(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    current_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    idea_worktree_root = quest_root / ".ds" / "worktrees" / "idea-run-1"

    dump_json(
        quest_root / ".ds" / "worktrees" / "paper-run-1" / "experiments" / "main" / "run-1" / "RESULT.json",
        {
            "quest_id": "002-early-residual-risk",
            "run_id": "run-1",
            "worktree_root": str(idea_worktree_root),
            "metric_contract": {
                "required_non_scalar_deliverables": [],
            },
            "metrics_summary": {
                "roc_auc": 0.81,
            },
            "baseline_comparisons": {"items": []},
            "results_summary": "summary",
            "conclusion": "conclusion",
        },
    )
    dump_json(
        current_paper_root / "paper_line_state.json",
        {
            "paper_root": str(current_paper_root.resolve()),
            "paper_branch": "paper/run-1",
        },
    )
    dump_json(
        projected_paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/stale-mirror",
            "compile_report_path": "paper/build/compile_report.json",
        },
    )
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "paper_root": str(projected_paper_root.resolve()),
            "paper_branch": "paper/stale-mirror",
        },
    )
    dump_json(
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json",
        {
            "paper_root": str(projected_paper_root.resolve()),
            "status": "blocked",
            "blockers": ["forbidden_manuscript_terms_present"],
        },
    )
    dump_json(
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:33Z.json",
        {
            "paper_root": str(current_paper_root.resolve()),
            "status": "clear",
            "blockers": [],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.paper_bundle_manifest_path == current_paper_root / "paper_bundle_manifest.json"
    assert report["paper_root"] == str(current_paper_root.resolve())
    assert report["medical_publication_surface_status"] == "clear"
    assert "medical_publication_surface_blocked" not in report["blockers"]
def test_build_gate_report_allows_clinical_cohort_wording_without_internal_labels(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        manuscript_files={
            "draft.md": (
                "We analyzed the institutional first-surgery NF-PitNET cohort and "
                "ascertained outcomes through June 30, 2024.\n"
            )
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert "forbidden_manuscript_terminology" not in report["blockers"]
    assert report["manuscript_terminology_violations"] == []
def test_run_controller_enqueues_message_when_blocked(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)

    result = module.run_controller(
        quest_root=quest_root,
        apply=True,
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert result["status"] == "blocked"
    assert result["intervention_enqueued"] is True
    assert len(queue["pending"]) == 1
    assert "publishability gate" in queue["pending"][0]["content"]
def test_build_gate_report_keeps_blocker_logic_in_controller_after_adapter_patch(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)

    monkeypatch.setattr(
        module.quest_state,
        "resolve_active_stdout_path",
        lambda *, quest_root, runtime_state: quest_root / ".ds" / "runs" / "run-1" / "stdout.jsonl",
    )
    monkeypatch.setattr(module.quest_state, "read_recent_stdout_lines", lambda stdout_path: ["route -> write"])
    monkeypatch.setattr(module.paper_artifacts, "resolve_artifact_manifest_from_main_result", lambda main_result: None)
    monkeypatch.setattr(module.paper_artifacts, "resolve_paper_bundle_manifest", lambda quest_root: None)
    monkeypatch.setattr(module.paper_artifacts, "resolve_submission_minimal_manifest", lambda paper_bundle_manifest_path: None)
    monkeypatch.setattr(
        module.paper_artifacts,
        "resolve_submission_minimal_output_paths",
        lambda *, paper_bundle_manifest_path, submission_minimal_manifest: (None, None),
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "missing_post_main_publishability_gate" in report["blockers"]
    assert "active_run_drifting_into_write_without_gate_approval" in report["blockers"]
    assert "missing_required_non_scalar_deliverables" not in report["blockers"]
def test_build_gate_report_ignores_live_agent_write_drift_when_active_run_differs_from_main_result(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    runtime_state["active_run_id"] = "run-live-agent"
    dump_json(runtime_state_path, runtime_state)
    write_text(
        quest_root / ".ds" / "runs" / "run-live-agent" / "stdout.jsonl",
        json.dumps({"line": "route -> write"}) + "\n",
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.active_run_stdout_path is None
    assert state.recent_stdout_lines == []
    assert report["status"] == "blocked"
    assert "missing_post_main_publishability_gate" in report["blockers"]
    assert "active_run_drifting_into_write_without_gate_approval" not in report["blockers"]
def test_detect_write_drift_ignores_write_drift_gate_path_noise() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    noisy_line = (
        "progress watchdog note: route change needed after inspection; "
        "cwd=.ds/worktrees/analysis-analysis-d47ce8e6-write-drift-gate"
    )

    assert module.detect_write_drift([noisy_line]) is False
def test_detect_write_drift_ignores_stop_messages_about_write_stage() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    control_line = (
        "Hard control message: immediately stop the current transition into `write` / outline generation."
    )

    assert module.detect_write_drift([control_line]) is False
def test_detect_write_drift_ignores_agent_messages_that_quote_examples() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    quoted_example_line = json.dumps(
        {
            "type": "item.completed",
            "item": {
                "id": "item-1",
                "type": "agent_message",
                "text": "保留 `route -> write` 这类真阳性，但这里是在解释测试，不是真实路由切换。",
            },
        },
        ensure_ascii=False,
    )

    assert module.detect_write_drift([quoted_example_line]) is False
def test_detect_write_drift_ignores_non_artifact_tool_output_examples() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    tool_output_line = json.dumps(
        {
            "type": "item.completed",
            "item": {
                "id": "item-2",
                "type": "mcp_tool_call",
                "server": "bash_exec",
                "tool": "bash_exec",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Next anchor: `write`\nroute -> write",
                        }
                    ]
                },
            },
        },
        ensure_ascii=False,
    )

    assert module.detect_write_drift([tool_output_line]) is False
def test_detect_write_drift_accepts_structured_next_anchor_signal() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    structured_signal_line = json.dumps(
        {
            "type": "item.completed",
            "item": {
                "id": "item-3",
                "type": "mcp_tool_call",
                "server": "artifact",
                "tool": "activate_branch",
                "result": {
                    "structured_content": {
                        "next_anchor": "write",
                    }
                },
            },
        },
        ensure_ascii=False,
    )

    assert module.detect_write_drift([structured_signal_line]) is True
def test_write_gate_files_uses_runtime_protocol_report_store(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=False)
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
        "generated_at": "2026-04-03T04:00:00+00:00",
        "quest_id": quest_root.name,
        "run_id": "run-1",
        "status": "blocked",
        "allow_write": False,
        "recommended_action": "stop",
        "blockers": ["missing_post_main_publishability_gate"],
        "missing_non_scalar_deliverables": [],
        "paper_bundle_manifest_path": None,
        "submission_minimal_manifest_path": None,
        "submission_minimal_present": False,
        "submission_minimal_docx_present": False,
        "submission_minimal_pdf_present": False,
        "headline_metrics": {},
        "results_summary": "summary",
        "conclusion": "conclusion",
        "controller_note": "note",
    }

    json_path, md_path = module.write_gate_files(quest_root, report)

    assert seen["quest_root"] == quest_root
    assert seen["report_group"] == "publishability_gate"
    assert seen["timestamp"] == "2026-04-03T04:00:00+00:00"
    assert json_path.name == "latest.json"
    assert md_path.name == "latest.md"
