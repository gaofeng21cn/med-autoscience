from __future__ import annotations

import importlib


def _live_console_snapshot() -> dict[str, object]:
    return {
        "workspace": {
            "profile_name": "dm-cvd",
            "workspace_root": "/workspace/DM-CVD",
            "workspace_status": "running",
        },
        "studies": [
            {
                "study_id": "002-dm-china-us-mortality-attribution",
                "state_label": "自动运行中",
                "current_stage": "analysis-campaign",
                "active_run_id": "mas-run-dm002",
                "runtime_health_status": "recovering",
                "supervisor_tick_status": "fresh",
                "worker_running": True,
                "runs": [
                    {
                        "run_id": "mas-run-dm002",
                        "status": "running",
                        "started_at": "2026-05-08T01:00:00+00:00",
                        "last_seen_at": "2026-05-08T01:04:00+00:00",
                    }
                ],
                "timeline": [
                    {
                        "observed_at": "2026-05-08T01:01:00+00:00",
                        "topic": "runtime.health",
                        "summary": "worker lease observed",
                        "source_ref": "artifacts/runtime/session/dm002/latest.json",
                    }
                ],
                "terminal_sources": [
                    {
                        "label": "bash stdout",
                        "source_ref": "runtime/quests/dm002/.ds/bash_exec/stdout.tail",
                        "tail": ["python analysis.py", "analysis rows: 42"],
                    }
                ],
                "log_sources": [
                    {
                        "label": "worker log",
                        "source_ref": "artifacts/runtime/logs/dm002.log",
                        "tail": ["runner started", "artifact delta written"],
                    }
                ],
                "artifact_refs": ["studies/dm002/manuscript/current_package"],
                "event_refs": ["artifacts/runtime/events/dm002.ndjson"],
            },
            {
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "state_label": "自动运行中",
                "current_stage": "write",
                "active_run_id": "mas-run-dpcc003",
                "runtime_health_status": "running",
                "supervisor_tick_status": "fresh",
                "worker_running": True,
                "runs": [
                    {
                        "run_id": "mas-run-dpcc003",
                        "status": "running",
                        "started_at": "2026-05-08T01:02:00+00:00",
                        "last_seen_at": "2026-05-08T01:05:00+00:00",
                    }
                ],
                "timeline": [
                    {
                        "observed_at": "2026-05-08T01:03:00+00:00",
                        "topic": "artifact.delta",
                        "summary": "draft section refreshed",
                        "source_ref": "artifacts/runtime/events/dpcc003.ndjson",
                    }
                ],
                "terminal_sources": [
                    {
                        "label": "bash stdout",
                        "source_ref": "runtime/quests/dpcc003/.ds/bash_exec/stdout.tail",
                        "tail": ["python write.py", "draft refreshed"],
                    }
                ],
                "log_sources": [
                    {
                        "label": "worker log",
                        "source_ref": "artifacts/runtime/logs/dpcc003.log",
                        "tail": ["runner started", "draft artifact refreshed"],
                    }
                ],
                "artifact_refs": ["studies/dpcc003/paper/submission_minimal"],
                "event_refs": ["artifacts/runtime/events/dpcc003.ndjson"],
            },
        ],
    }


def test_live_console_payload_projects_read_only_ui_shell_contract() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console_ui")

    payload = module.build_live_console_ui_payload(
        live_console_snapshot=_live_console_snapshot(),
        generated_at="2026-05-08T01:06:00+00:00",
        progress_portal_href="../progress/index.html",
        stream_href="http://127.0.0.1:8765/events",
    )

    assert payload["surface_kind"] == "mas_live_console_ui"
    assert payload["html_ref"] == "ops/mas/live-console/index.html"
    assert payload["authority"]["read_only"] is True
    assert payload["authority"]["writes_authority_surface"] is False
    assert payload["authority"]["state_interpretation_owner"] == "runtime_session_read_model"
    assert payload["portal_handoff"] == {
        "progress_portal_href": "../progress/index.html",
        "relationship": "navigation_return_link",
        "portal_owns_live_console_state_interpretation": False,
    }
    assert payload["stream"]["href"] == "http://127.0.0.1:8765/events"
    assert payload["stream"]["mode"] == "read_only_observation"

    studies = payload["studies"]
    assert [item["study_id"] for item in studies] == [
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    ]
    assert studies[0]["runs"][0]["run_id"] == "mas-run-dm002"
    assert studies[1]["runs"][0]["run_id"] == "mas-run-dpcc003"
    assert payload["source_refs"] == [
        "artifacts/runtime/session/dm002/latest.json",
        "runtime/quests/dm002/.ds/bash_exec/stdout.tail",
        "artifacts/runtime/logs/dm002.log",
        "studies/dm002/manuscript/current_package",
        "artifacts/runtime/events/dm002.ndjson",
        "artifacts/runtime/events/dpcc003.ndjson",
        "runtime/quests/dpcc003/.ds/bash_exec/stdout.tail",
        "artifacts/runtime/logs/dpcc003.log",
        "studies/dpcc003/paper/submission_minimal",
    ]


def test_live_console_html_renders_static_shell_without_legacy_webui_assets() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console_ui")
    payload = module.build_live_console_ui_payload(
        live_console_snapshot=_live_console_snapshot(),
        generated_at="2026-05-08T01:06:00+00:00",
        progress_portal_href="../progress/index.html",
        stream_href="http://127.0.0.1:8765/events",
    )

    html = module.render_live_console_html(payload)

    assert "<!doctype html>" in html
    assert "READ ONLY" in html
    assert 'href="../progress/index.html"' in html
    assert "返回 Progress Portal" in html
    assert "workspace/study/run" in html
    assert "状态 timeline" in html
    assert "Terminal stream" in html
    assert "Log stream" in html
    assert "Artifact refs" in html
    assert "Event refs" in html
    assert "002-dm-china-us-mortality-attribution" in html
    assert "003-dpcc-primary-care-phenotype-treatment-gap" in html
    assert "mas-run-dm002" in html
    assert "mas-run-dpcc003" in html
    assert "analysis rows: 42" in html
    assert "draft refreshed" in html
    assert "https://cdn" not in html
    assert "unpkg.com" not in html
    assert "med-deepscientist" not in html.lower()
    assert "MDS WebUI" not in html
