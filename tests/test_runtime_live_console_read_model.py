from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_live_console_read_model_projects_runtime_session_and_stream_refs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    stdout_path = tmp_path / "runtime" / "quests" / "quest-002" / ".ds" / "runs" / "run-002" / "stdout.jsonl"
    stderr_path = stdout_path.with_name("stderr.txt")
    _write_text(
        stdout_path,
        "\n".join(
            [
                '{"line":"first terminal line"}',
                '{"line":"second terminal line"}',
                '{"line":"third terminal line"}',
            ]
        )
        + "\n",
    )
    _write_text(stderr_path, "first log line\nsecond log line\n")

    read_model = module.build_live_console_read_model(
        profile_name="dm-cvd",
        workspace_root=tmp_path,
        study_id="002-dm-china-us-mortality-attribution",
        study_runtime_status={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-002",
            "active_run_id": "run-002",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "worker_state": "running",
            "last_seen_at": "2026-05-08T02:04:00+00:00",
            "last_event_cursor": "cursor-002",
            "last_stdout_ref": str(stdout_path),
            "worker_watchdog": {
                "monitor_kind": "mas_per_run_worker_wrapper",
                "monitor_state": "live",
                "heartbeat_age_seconds": 20,
                "last_output_at": "2026-05-08T02:04:40+00:00",
                "stdout_cursor": 123,
                "will_start_llm": False,
            },
        },
        runtime_health={"status": "recovering", "summary": "worker heartbeat is fresh"},
        runtime_supervision={"supervisor_tick_status": "fresh", "latest_event_at": "2026-05-08T02:04:30+00:00"},
        terminal_sources=[{"source": "codex_stdout", "path": stdout_path}],
        log_sources=[{"source": "codex_stderr", "path": stderr_path}],
        artifact_delta={"refs": ["studies/002/artifacts/runtime/runtime_supervision/latest.json"]},
        generated_at="2026-05-08T02:05:00+00:00",
        freshness_ttl_seconds=300,
    )

    assert read_model["surface_kind"] == "mas_live_console_read_model"
    assert read_model["read_only"] is True
    assert read_model["authority"] == {
        "kind": "read_only_runtime_projection",
        "writes_authority_surface": False,
        "controller_action_execution_allowed": False,
        "quality_authority_allowed": False,
        "publication_authority_allowed": False,
        "submission_authority_allowed": False,
    }
    assert read_model["workspace"]["profile_name"] == "dm-cvd"
    assert read_model["study"]["study_id"] == "002-dm-china-us-mortality-attribution"
    assert read_model["session"]["active_run_id"] == "run-002"
    assert read_model["session"]["worker_running"] is True
    assert read_model["watchdog"] == {
        "monitor_kind": "mas_per_run_worker_wrapper",
        "heartbeat_age_seconds": 20,
        "last_output_at": "2026-05-08T02:04:40+00:00",
        "stdout_cursor": 123,
        "monitor_state": "live",
        "will_start_llm": False,
    }
    assert read_model["runtime_health"]["status"] == "recovering"
    assert read_model["runtime_supervision"]["supervisor_tick_status"] == "fresh"
    assert read_model["terminal_sources"][0]["tail"] == ["first terminal line", "second terminal line", "third terminal line"]
    assert read_model["log_sources"][0]["tail"] == ["first log line", "second log line"]
    assert read_model["artifact_delta"]["refs"] == ["studies/002/artifacts/runtime/runtime_supervision/latest.json"]
    assert {topic["topic"] for topic in read_model["stream_topics"]} == {
        "workspace.status",
        "study.status",
        "runtime.health",
        "runtime.supervision",
        "runtime.watchdog",
        "terminal.tail",
        "log.tail",
        "artifact.delta",
    }
    assert all(topic["read_only"] is True for topic in read_model["stream_topics"])
    assert read_model["controller_action_links"][0]["direct_execution_allowed"] is False


def test_live_console_read_model_projects_output_blocker_impact_without_writes() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")

    read_model = module.build_live_console_read_model(
        profile_name="dm-cvd",
        workspace_root="/workspace",
        study_id="001-risk",
        study_runtime_status={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "runtime_liveness_status": "stale",
            "worker_running": False,
            "worker_state": "stale",
            "runtime_session": {"freshness_state": "stale"},
            "recovery_intent": {
                "current_action": "safe_reconcile_ready",
                "next_owner": "mas_controller",
                "dedupe_fingerprint": "runtime-continuity-001",
            },
            "runtime_reconcile_trigger": {
                "safe_to_request": True,
                "recommended_command": (
                    "uv run python -m med_autoscience.cli runtime-supervisor-reconcile "
                    "--profile /workspace/profile.toml --studies 001-risk --dry-run"
                ),
                "will_start_llm": False,
                "dedupe_fingerprint": "runtime-continuity-001",
                "source_refs": ["studies/001-risk/artifacts/runtime/owner_route/latest.json"],
            },
            "owner_route": {
                "next_owner": "mas_controller",
                "owner_reason": "runtime_stale",
                "source_fingerprint": "runtime-continuity-001",
            },
            "paper_progress_stall": {
                "why_not_running": "worker heartbeat stale",
                "same_fingerprint_or_handoff": "same_fingerprint",
            },
        },
        generated_at="2026-05-08T02:05:00+00:00",
    )

    impact = read_model["production_blocker_impact"]
    assert impact["surface_kind"] == "mas_production_blocker_impact_projection"
    assert impact["affects_output"] is True
    assert impact["next_owner"] == "mas_controller"
    assert impact["why_not_running"] == "worker heartbeat stale"
    assert impact["same_fingerprint_or_handoff"] == "same_fingerprint"
    assert impact["will_start_llm"] is False
    assert impact["safe_reconcile_command"].endswith("--studies 001-risk --dry-run")
    assert impact["route"]["source_fingerprint"] == "runtime-continuity-001"
    assert impact["authority"]["writes_authority_surface"] is False
    assert "studies/001-risk/artifacts/runtime/owner_route/latest.json" in impact["source_refs"]


def test_live_console_materialization_writes_only_live_console_read_model(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    status_path = tmp_path / "studies" / "002" / "artifacts" / "runtime" / "status.json"
    _write_json(
        status_path,
        {
            "study_id": "002",
            "quest_id": "quest-002",
            "runtime_liveness_status": "unknown",
            "worker_running": True,
            "active_run_id": "run-stale",
            "last_seen_at": "2026-05-08T02:00:00+00:00",
        },
    )
    before = status_path.stat().st_mtime_ns

    result = module.materialize_live_console_read_model(
        workspace_root=tmp_path,
        profile_name="dm-cvd",
        study_id="002",
        study_runtime_status_path=status_path,
        generated_at="2026-05-08T02:05:00+00:00",
    )

    latest_path = tmp_path / "artifacts" / "runtime" / "live_console" / "session_read_model" / "latest.json"
    assert result["read_model_ref"] == str(latest_path)
    assert json.loads(latest_path.read_text(encoding="utf-8"))["surface_kind"] == "mas_live_console_read_model"
    assert status_path.stat().st_mtime_ns == before
    assert not (tmp_path / "artifacts" / "controller_decisions").exists()
    assert not (tmp_path / "artifacts" / "publication_eval").exists()


def test_live_console_stream_events_are_read_only_and_ordered() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")

    events = module.build_live_console_stream_events(
        {
            "surface_kind": "mas_live_console_read_model",
            "generated_at": "2026-05-08T02:05:00+00:00",
            "workspace": {"workspace_root": "/workspace"},
            "study": {"study_id": "002"},
            "session": {"active_run_id": "run-002"},
            "runtime_health": {"status": "recovering"},
            "runtime_supervision": {"supervisor_tick_status": "fresh"},
            "watchdog": {"monitor_state": "live"},
            "terminal_sources": [{"source_ref": "/tmp/stdout.jsonl", "tail": ["terminal line"]}],
            "log_sources": [{"source_ref": "/tmp/stderr.txt", "tail": ["log line"]}],
            "artifact_delta": {"refs": ["artifact.json"]},
        }
    )

    assert [event["sequence"] for event in events] == list(range(1, len(events) + 1))
    assert {event["topic"] for event in events} == {
        "workspace.status",
        "study.status",
        "runtime.health",
        "runtime.supervision",
        "runtime.watchdog",
        "terminal.tail",
        "log.tail",
        "artifact.delta",
    }
    assert all(event["read_only"] is True for event in events)
    assert all(event["source_ref"] for event in events)


def test_runtime_live_console_controller_exposes_cli_snapshot_alias() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")

    snapshot = module.read_live_console_snapshot(
        profile_name="dm-cvd",
        workspace_root="/workspace",
        study_id="002",
        study_runtime_status={
            "study_id": "002",
            "quest_id": "quest-002",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "active_run_id": "run-002",
        },
        generated_at="2026-05-08T02:05:00+00:00",
    )

    assert snapshot["surface_kind"] == "mas_live_console_read_model"
    assert snapshot["study"]["study_id"] == "002"
    assert snapshot["session"]["active_run_id"] == "run-002"


def _write_study_status(
    *,
    profile,
    study_id: str,
    quest_id: str,
    active_run_id: str | None,
    quest_status: str,
) -> None:
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        study_root / "artifacts" / "runtime" / "study_runtime_status" / "latest.json",
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "active_run_id": active_run_id,
            "quest_status": quest_status,
            "worker_running": active_run_id is not None,
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "health" / "latest.json",
        {
            "study_id": study_id,
            "health_status": quest_status,
            "active_run_id": active_run_id,
            "worker_running": active_run_id is not None,
            "artifact_delta": {"status": "fresh" if active_run_id else "missing"},
        },
    )


def test_live_console_profile_session_read_model_does_not_default_select_first_study(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    for study_id in (
        "001-dm-cvd-mortality-risk",
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    ):
        study_root = profile.studies_root / study_id
        _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")

    payload = module.build_live_console_session_read_model(profile, generated_at="2026-05-08T02:05:00+00:00")

    assert payload["surface_kind"] == "mas_live_console_session_read_model"
    assert payload["selected_study_id"] is None
    assert payload["empty_state"]["reason"] == "no_live_run"
    assert payload["empty_state"]["study_count"] == 3
    assert all(study["runtime_observation_status"] == "no_live_run" for study in payload["studies"])
    assert {study["study_id"] for study in payload["studies"]} == {
        "001-dm-cvd-mortality-risk",
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    }
    assert all(study["selected"] is False for study in payload["studies"])


def test_live_console_session_read_model_uses_workspace_cockpit_labels_when_study_progress_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        profile.workspace_root / "artifacts" / "runtime" / "workspace_cockpit" / "latest.json",
        {
            "workspace_status": "blocked",
            "studies": [
                {
                    "study_id": study_id,
                    "state_label": "自动运行中",
                    "current_stage": "live",
                    "paper_stage": "analysis-campaign",
                    "next_system_action": "观察自动运行推进。",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "health" / "latest.json",
        {
            "study_id": study_id,
            "attempt_state": "escalated",
            "blocking_reasons": [
                "quest_marked_running_but_no_live_session",
                "runtime_recovery_retry_budget_exhausted",
            ],
            "canonical_runtime_action": "external_supervisor_required",
            "worker_liveness_state": {"worker_running": False, "active_run_id": None},
            "supervisor_state": {"status": "stale"},
        },
    )

    payload = module.build_live_console_session_read_model(profile, generated_at="2026-05-08T02:05:00+00:00")
    study = payload["studies"][0]

    assert study["state_label"] == "自动运行中"
    assert study["current_stage"] == "live"
    assert study["paper_stage"] == "analysis-campaign"
    assert study["next_action_summary"] == "观察自动运行推进。"
    assert study["runtime_observation_status"] == "no_live_run"
    assert study["blocking_reasons"] == [
        "quest_marked_running_but_no_live_session",
        "runtime_recovery_retry_budget_exhausted",
    ]


def test_live_console_session_read_model_derives_readable_state_from_health_when_progress_missing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        study_root / "artifacts" / "runtime" / "health" / "latest.json",
        {
            "study_id": study_id,
            "attempt_state": "escalated",
            "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            "canonical_runtime_action": "external_supervisor_required",
            "worker_liveness_state": {"worker_running": None, "active_run_id": None},
            "supervisor_state": {"status": "fresh"},
        },
    )

    payload = module.build_live_console_session_read_model(profile, generated_at="2026-05-08T02:05:00+00:00")
    study = payload["studies"][0]

    assert study["state_label"] == "需要外层 supervisor"
    assert study["current_stage"] == "runtime_repair_required"
    assert study["runtime_health_status"] == "escalated"
    assert study["supervisor_tick_status"] == "fresh"
    assert study["runtime_observation_status"] == "no_live_run"


def test_live_console_session_read_model_distinguishes_dm002_and_dpcc003(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    _write_study_status(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        active_run_id="run-dm002-live",
        quest_status="running",
    )
    _write_study_status(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        quest_id="quest-dpcc003",
        active_run_id=None,
        quest_status="recovering",
    )

    payload = module.build_live_console_session_read_model(
        profile,
        study_id="002-dm-china-us-mortality-attribution",
        generated_at="2026-05-08T02:05:00+00:00",
    )

    assert [study["study_id"] for study in payload["studies"]] == [
        "002-dm-china-us-mortality-attribution",
    ]
    assert payload["selected_study_id"] == "002-dm-china-us-mortality-attribution"
    assert payload["runs"] == [
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-dm002",
            "active_run_id": "run-dm002-live",
            "status": "running",
            "worker_running": True,
        }
    ]
    assert {source["study_id"] for source in payload["stream_sources"]} == {
        "002-dm-china-us-mortality-attribution"
    }
    assert {event.get("study_id") for event in payload["events"] if event.get("study_id")} == {
        "002-dm-china-us-mortality-attribution"
    }
    serialized_refs = json.dumps(payload["source_refs"], ensure_ascii=False)
    assert "003-dpcc-primary-care-phenotype-treatment-gap" not in serialized_refs


def test_live_console_session_read_model_filters_to_selected_study_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    _write_study_status(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        active_run_id="run-dm002-live",
        quest_status="running",
    )
    _write_study_status(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        quest_id="quest-dpcc003",
        active_run_id="run-dpcc003-live",
        quest_status="running",
    )

    payload = module.build_live_console_session_read_model(
        profile,
        study_root=profile.studies_root / "003-dpcc-primary-care-phenotype-treatment-gap",
        generated_at="2026-05-08T02:05:00+00:00",
    )

    assert payload["selected_study_id"] == "003-dpcc-primary-care-phenotype-treatment-gap"
    assert [study["study_id"] for study in payload["studies"]] == [
        "003-dpcc-primary-care-phenotype-treatment-gap"
    ]
    assert [run["study_id"] for run in payload["runs"]] == [
        "003-dpcc-primary-care-phenotype-treatment-gap"
    ]
    assert {source["study_id"] for source in payload["stream_sources"]} == {
        "003-dpcc-primary-care-phenotype-treatment-gap"
    }


def test_live_console_session_read_model_ignores_file_runtime_artifact_ref_for_terminal_source(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_root = profile.runtime_root / study_id
    study_root = profile.studies_root / study_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_status_summary.json",
        {
            "study_id": study_id,
            "quest_id": study_id,
            "runtime_artifact_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        },
    )
    _write_json(
        quest_root / ".ds" / "bash_exec" / "summary.json",
        {"status": "available", "tail": ["real quest terminal tail"]},
    )

    payload = module.build_live_console_session_read_model(profile, generated_at="2026-05-08T02:05:00+00:00")

    stream_by_topic = {(source["topic"], source["study_id"]): source for source in payload["stream_sources"]}
    terminal = stream_by_topic[("terminal.tail", study_id)]
    assert terminal["status"] == "available"
    assert terminal["source_ref"] == str(quest_root / ".ds" / "bash_exec" / "summary.json")
    assert "last_launch_report.json/.ds" not in json.dumps(payload, ensure_ascii=False)


def test_live_console_profile_snapshot_materializes_current_ui_payload_and_html(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    _write_study_status(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        active_run_id="run-dm002-live",
        quest_status="running",
    )
    _write_study_status(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        quest_id="quest-dpcc003",
        active_run_id=None,
        quest_status="recovering",
    )

    result = module.serve_live_console_stream(
        profile,
        profile_ref=tmp_path / "profile.toml",
        host="127.0.0.1",
        port=4812,
        interval_seconds=30,
    )

    html_path = profile.workspace_root / "ops" / "mas" / "live-console" / "index.html"
    ui_payload_path = profile.workspace_root / "artifacts" / "runtime" / "live_console" / "ui_payload" / "latest.json"
    assert result["html_path"] == str(html_path)
    assert result["ui_payload_path"] == str(ui_payload_path)
    assert json.loads(ui_payload_path.read_text(encoding="utf-8"))["surface_kind"] == "mas_live_console_ui"
    html = html_path.read_text(encoding="utf-8")
    assert "diabetes" in html
    assert "002-dm-china-us-mortality-attribution" in html
    assert "003-dpcc-primary-care-phenotype-treatment-gap" in html
    assert "run-dm002-live" in html
    assert "http://127.0.0.1:4812/events" in html
    assert "本机时间" in html
    assert "med-deepscientist" not in html.lower()


def test_live_console_study_snapshot_materializes_study_scoped_ui_and_progress_return_link(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    selected_study_id = "002-dm-china-us-mortality-attribution"
    _write_study_status(
        profile=profile,
        study_id=selected_study_id,
        quest_id="quest-dm002",
        active_run_id="run-dm002-live",
        quest_status="running",
    )
    _write_study_status(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        quest_id="quest-dpcc003",
        active_run_id="run-dpcc003-live",
        quest_status="running",
    )
    per_study_progress = (
        profile.workspace_root
        / "ops"
        / "mas"
        / "progress"
        / "studies"
        / selected_study_id
        / "index.html"
    )
    _write_text(per_study_progress, "selected progress\n")

    result = module.serve_live_console_stream(
        profile,
        profile_ref=tmp_path / "profile.toml",
        study_id=selected_study_id,
        host="127.0.0.1",
        port=4812,
        interval_seconds=30,
    )

    ui_payload = result["ui_payload"]
    assert ui_payload["scope"] == "study"
    assert ui_payload["selected_study_id"] == selected_study_id
    assert ui_payload["terminal_attach_gate"]["profile_ref"] == str(tmp_path / "profile.toml")
    assert ui_payload["terminal_attach_gate"]["study_id"] == selected_study_id
    assert ui_payload["portal_handoff"]["progress_portal_href"] == (
        f"../progress/studies/{selected_study_id}/index.html"
    )
    assert [study["study_id"] for study in ui_payload["studies"]] == [selected_study_id]
    html = Path(result["html_path"]).read_text(encoding="utf-8")
    assert "控制台范围" in html
    assert selected_study_id in html
    assert "run-dm002-live" in html
    assert "003-dpcc-primary-care-phenotype-treatment-gap" not in html
    assert f'href="../progress/studies/{selected_study_id}/index.html"' in html


def test_portal_console_soak_materializes_read_only_evidence_without_truth_writes(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.portal_console_soak")
    profile = make_profile(tmp_path)
    _write_soak_study(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        active_run_id="run-dm002-live",
        quest_status="running",
    )
    _write_soak_study(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        quest_id="quest-dpcc003",
        active_run_id="run-dpcc003-recovering",
        quest_status="recovering",
    )

    report = module.run_portal_console_soak(
        profile=profile,
        profile_ref=tmp_path / "profile.toml",
        generated_at="2026-05-08T02:05:00+00:00",
    )

    assert report["surface_kind"] == "mas_portal_console_soak"
    assert report["status"] == "blocked"
    evidence = report["evidence"]
    assert evidence["portal_refresh"]["status"] == "passed"
    assert evidence["per_study_workbench"]["status"] == "passed"
    assert evidence["per_study_deep_link"]["status"] == "passed"
    assert evidence["route_decision_trail"]["status"] == "passed"
    assert evidence["route_decision_trail"]["missing_count"] == 0
    assert evidence["route_decision_trail"]["active_paths"] == ["study_progress_gap"]
    assert evidence["route_decision_trail"]["source_ref_count"] > 0
    assert "missing_route_nodes" not in evidence["route_decision_trail"]["blockers"]
    assert evidence["conversation_read_model"]["status"] == "passed"
    assert evidence["conversation_read_model"]["surface_kind"] == "mas_runtime_conversation_read_model"
    assert evidence["study_scoped_console"]["status"] == "blocked"
    assert "missing_selected_study_id" in evidence["study_scoped_console"]["blockers"]
    assert evidence["action_receipts"]["status"] == "passed"
    assert evidence["action_receipts"]["intent_count"] == 6
    assert evidence["action_receipts"]["receipt_or_command_count"] == 6
    assert evidence["action_receipts"]["direct_execution_intents"] == []
    assert evidence["terminal_attach_gate"]["status"] == "passed"
    assert evidence["terminal_attach_gate"]["attach_started"] is False
    assert evidence["latency_slo_source_refs"]["status"] == "blocked"
    assert "missing_outer_supervision_slo" in evidence["latency_slo_source_refs"]["blockers"]
    assert evidence["live_console_study_run_disambiguation"]["study_ids"] == [
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    ]
    assert evidence["live_console_study_run_disambiguation"]["run_ids"] == [
        "run-dm002-live",
        "run-dpcc003-recovering",
    ]
    assert evidence["terminal_log_refs"]["status"] == "passed"
    assert evidence["source_ref_cleanliness"]["forbidden_refs"] == []
    assert evidence["product_identity"]["forbidden_identity_tokens"] == []
    assert Path(report["report_path"]).is_file()
    assert (profile.workspace_root / "ops" / "mas" / "progress" / "index.html").is_file()
    assert (profile.workspace_root / "ops" / "mas" / "live-console" / "index.html").is_file()
    assert not (profile.workspace_root / "publication_eval" / "latest.json").exists()
    assert not (profile.workspace_root / "controller_decisions" / "latest.json").exists()
    assert not (profile.workspace_root / "runtime_lifecycle.sqlite").exists()


def test_portal_console_soak_blocks_legacy_identity_and_mds_truth_refs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.portal_console_soak")
    profile = make_profile(tmp_path)
    portal_payload = {
        "source_refs": [
            str(profile.workspace_root / "ops" / "med-deepscientist" / "runtime" / "truth.json"),
        ],
    }
    console_payload = {"source_refs": []}
    console_ui_payload = {"source_refs": []}
    portal_payload_path = profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "latest.json"
    console_payload_path = (
        profile.workspace_root / "artifacts" / "runtime" / "live_console" / "session_read_model" / "latest.json"
    )
    console_ui_payload_path = (
        profile.workspace_root / "artifacts" / "runtime" / "live_console" / "ui_payload" / "latest.json"
    )
    portal_html_path = profile.workspace_root / "ops" / "mas" / "progress" / "index.html"
    console_html_path = profile.workspace_root / "ops" / "mas" / "live-console" / "index.html"
    _write_json(portal_payload_path, portal_payload)
    _write_json(console_payload_path, console_payload)
    _write_json(console_ui_payload_path, console_ui_payload)
    _write_text(portal_html_path, "Med Auto Science\n")
    _write_text(console_html_path, "MDS WebUI\n")

    report = module.build_portal_console_soak_report(
        profile=profile,
        profile_ref=tmp_path / "profile.toml",
        portal_result={
            "status": "materialized",
            "payload_path": str(portal_payload_path),
            "html_path": str(portal_html_path),
            "hosted_package_path": str(
                profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "hosted_package.json"
            ),
        },
        console_result={
            "payload_path": str(console_payload_path),
            "ui_payload_path": str(console_ui_payload_path),
            "html_path": str(console_html_path),
            "session_read_model": {"studies": [], "stream_sources": []},
        },
        generated_at="2026-05-08T02:05:00+00:00",
    )

    assert report["status"] == "blocked"
    assert report["evidence"]["source_ref_cleanliness"]["forbidden_refs"] == portal_payload["source_refs"]
    assert report["evidence"]["product_identity"]["forbidden_identity_tokens"] == ["MDS WebUI"]


def test_conversation_read_model_projects_user_messages_turn_receipts_and_blockers(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = "quest-dm002"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        study_root / "artifacts" / "runtime" / "study_runtime_status" / "latest.json",
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "active_run_id": "run-dm002",
            "quest_status": "waiting_for_user",
            "worker_running": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "health" / "latest.json",
        {
            "study_id": study_id,
            "health_status": "blocked",
            "blocking_reasons": ["awaiting_user_decision"],
            "canonical_runtime_action": "await_explicit_resume",
            "allowed_controller_actions": ["resume_runtime"],
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": quest_id,
            "status": "waiting_for_user",
            "last_completed_run_id": "run-dm002",
            "stop_requested": True,
            "pending_turn_reason": "manual_replan",
            "blocking_decision_request": {
                "interaction_id": "interaction-001",
                "reason": "confirm next analysis branch",
            },
            "pending_user_message_count": 1,
            "updated_at": "2026-05-08T02:06:00+00:00",
        },
    )
    _write_json(
        quest_root / "artifacts" / "runtime" / "user_message_queue.json",
        {
            "schema_version": 1,
            "pending": [
                {
                    "message_id": "msg-pending",
                    "content": "继续，但先解释阻塞。",
                    "recorded_at": "2026-05-08T02:05:00+00:00",
                    "status": "pending",
                }
            ],
            "completed": [
                {
                    "message_id": "msg-completed",
                    "content": "上一轮先停。",
                    "recorded_at": "2026-05-08T02:01:00+00:00",
                    "status": "completed",
                    "claimed_by_run_id": "run-dm002",
                    "claimed_at": "2026-05-08T02:02:00+00:00",
                }
            ],
        },
    )
    _write_text(
        quest_root / "artifacts" / "runtime" / "turn_receipts.jsonl",
        json.dumps(
            {
                "quest_id": quest_id,
                "run_id": "run-dm002",
                "reason": "user_message",
                "source": "test",
                "status": "started",
                "started": True,
                "queued": False,
                "idempotency_key": "idem-001",
                "recorded_at": "2026-05-08T02:02:00+00:00",
                "claimed_user_messages": [
                    {
                        "message_id": "msg-completed",
                        "status": "completed",
                        "claimed_at": "2026-05-08T02:02:00+00:00",
                    }
                ],
                "runner_receipt": {
                    "runner_kind": "codex_exec",
                    "stdout_path": str(quest_root / ".ds" / "runs" / "run-dm002" / "stdout.jsonl"),
                    "stderr_path": str(quest_root / ".ds" / "runs" / "run-dm002" / "stderr.txt"),
                },
            },
            ensure_ascii=False,
        )
        + "\n",
    )
    _write_text(
        quest_root / "artifacts" / "runtime" / "mas_runtime_events.jsonl",
        json.dumps(
            {
                "event": "turn_finished",
                "recorded_at": "2026-05-08T02:06:00+00:00",
                "snapshot": {
                    "quest_id": quest_id,
                    "status": "waiting_for_user",
                    "last_completed_run_id": "run-dm002",
                    "turn_reason": "user_message",
                    "stop_requested": True,
                    "blocking_decision_request": {"interaction_id": "interaction-001"},
                },
            },
            ensure_ascii=False,
        )
        + "\n",
    )

    payload = module.build_conversation_read_model(
        profile,
        study_id=study_id,
        generated_at="2026-05-08T02:07:00+00:00",
    )

    assert payload["surface_kind"] == "mas_runtime_conversation_read_model"
    assert payload["read_only"] is True
    assert payload["authority"]["writes_authority_surface"] is False
    assert payload["authority"]["can_write_runtime_sqlite_authority"] is False
    assert payload["selected_study_id"] == study_id
    timeline = payload["timeline"]
    assert {item["item_kind"] for item in timeline} >= {
        "user_message",
        "turn_receipt",
        "runtime_lifecycle_event",
        "runtime_control_ref",
        "action_or_blocker_ref",
        "live_console_run_ref",
    }
    user_items = [item for item in timeline if item["item_kind"] == "user_message"]
    assert {item["message_id"] for item in user_items} == {"msg-pending", "msg-completed"}
    receipt = next(item for item in timeline if item["item_kind"] == "turn_receipt")
    assert receipt["tool_refs"]
    assert receipt["assistant_refs"]
    assert receipt["claimed_user_message_refs"] == [
        {
            "message_id": "msg-completed",
            "status": "completed",
            "claimed_at": "2026-05-08T02:02:00+00:00",
        }
    ]
    control_refs = [item for item in timeline if item["item_kind"] == "runtime_control_ref"]
    assert {item["event_name"] for item in control_refs} >= {
        "stop_requested",
        "replan_or_pending_turn",
        "blocked_waiting_for_user",
    }
    assert any(ref["kind"] == "blocking_decision_request" for item in control_refs for ref in item["blocker_refs"])
    assert any(
        ref["surface_kind"] == "turn_receipts_jsonl"
        and ref["source_ref"] == str(quest_root / "artifacts" / "runtime" / "turn_receipts.jsonl")
        for ref in payload["source_refs"]
    )
    assert all(ref["read_only"] is True for ref in payload["source_refs"])


def test_conversation_read_model_fail_closed_missing_fields_without_guessing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = "quest-dm002"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        study_root / "artifacts" / "runtime" / "study_runtime_status" / "latest.json",
        {"study_id": study_id, "quest_id": quest_id, "quest_root": str(quest_root)},
    )
    _write_json(
        quest_root / "artifacts" / "runtime" / "user_message_queue.json",
        {"schema_version": 1, "pending": [{"content": "missing metadata"}], "completed": []},
    )
    _write_text(
        quest_root / "artifacts" / "runtime" / "turn_receipts.jsonl",
        json.dumps({"run_id": "run-missing", "status": "started"}, ensure_ascii=False) + "\n",
    )

    payload = module.build_conversation_read_model(
        profile,
        study_id=study_id,
        generated_at="2026-05-08T02:07:00+00:00",
    )

    user_item = next(item for item in payload["timeline"] if item["item_kind"] == "user_message")
    receipt_item = next(item for item in payload["timeline"] if item["item_kind"] == "turn_receipt")
    assert user_item["message_id"] is None
    assert user_item["message_status"] == "pending"
    assert user_item["missing_fields"] == ["message_id", "recorded_at"]
    assert receipt_item["turn_reason"] is None
    assert receipt_item["turn_status"] == "started"
    assert receipt_item["missing_fields"] == ["reason", "recorded_at"]
    assert payload["timeline_summary"]["missing_field_item_count"] >= 2


def test_conversation_read_model_materializes_latest_and_history_without_truth_writes(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = "quest-dm002"
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    status_path = study_root / "artifacts" / "runtime" / "study_runtime_status" / "latest.json"
    _write_json(status_path, {"study_id": study_id, "quest_id": quest_id, "quest_root": str(quest_root)})
    before = status_path.stat().st_mtime_ns

    result = module.materialize_conversation_read_model(
        profile,
        study_id=study_id,
        generated_at="2026-05-08T02:07:00+00:00",
    )

    latest_path = profile.workspace_root / "artifacts" / "runtime" / "conversation_read_model" / "latest.json"
    history_path = profile.workspace_root / "artifacts" / "runtime" / "conversation_read_model" / "history.jsonl"
    assert result["payload_path"] == str(latest_path.resolve())
    assert result["history_path"] == str(history_path.resolve())
    assert json.loads(latest_path.read_text(encoding="utf-8"))["surface_kind"] == "mas_runtime_conversation_read_model"
    assert len(history_path.read_text(encoding="utf-8").splitlines()) == 1
    assert status_path.stat().st_mtime_ns == before
    assert not (profile.workspace_root / "artifacts" / "publication_eval").exists()
    assert not (profile.workspace_root / "artifacts" / "controller_decisions").exists()
    assert not (profile.workspace_root / "runtime_lifecycle.sqlite").exists()


def _write_soak_study(
    *,
    profile,
    study_id: str,
    quest_id: str,
    active_run_id: str,
    quest_status: str,
) -> None:
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        study_root / "artifacts" / "runtime" / "study_runtime_status" / "latest.json",
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "active_run_id": active_run_id,
            "quest_status": quest_status,
            "worker_running": True,
            "last_seen_at": "2026-05-08T02:04:00+00:00",
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "health" / "latest.json",
        {
            "study_id": study_id,
            "health_status": quest_status,
            "active_run_id": active_run_id,
            "worker_running": True,
            "last_seen_at": "2026-05-08T02:04:00+00:00",
            "artifact_delta": {
                "status": "fresh",
                "latest_meaningful_delta_at": "2026-05-08T02:03:00+00:00",
                "artifact_kind": "read_model_fixture",
            },
        },
    )
    _write_json(
        quest_root / ".ds" / "bash_exec" / "summary.json",
        {"status": "available", "tail": [f"{study_id} terminal tail"]},
    )
    _write_text(quest_root / "logs" / "worker.log", f"{study_id} worker log\n")
