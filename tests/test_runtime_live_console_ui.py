from __future__ import annotations

import importlib
import json

from tests.test_cli_cases.shared import write_profile


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
        profile_ref="/workspace/DM-CVD/profile.local.toml",
        study_root="/workspace/DM-CVD/studies/002-dm-china-us-mortality-attribution",
        study_id="002-dm-china-us-mortality-attribution",
        progress_portal_href="../progress/index.html",
        stream_href="http://127.0.0.1:8765/events",
    )

    assert payload["surface_kind"] == "mas_live_console_ui"
    assert payload["generated_at_local"]["timezone"]
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
    assert payload["terminal_attach_gate"] == {
        "surface_kind": "mas_terminal_attach_gate",
        "status": "blocked_by_missing_terminal_input_owner",
        "threat_model": {
            "scope": "interactive_terminal_attach",
            "risks": [
                "unauthorized_terminal_input",
                "stale_or_replayed_resize",
                "duplicate_or_out_of_order_input",
                "detached_session_continuing_without_audit",
                "legacy_daemon_regaining_runtime_ownership",
            ],
            "fail_closed_without_owner": True,
        },
        "required_owner_contract": {
            "token": "MAS-issued attach token with explicit study/run scope and expiry",
            "lease": "single active terminal input lease with renewal and stale lease rejection",
            "idempotency": "dedupe key for each input, resize, and detach request",
            "audit": "append-only receipt for attach, input, resize, detach, denial, and expiry",
            "input": "MAS-owned terminal input route with authorization and run-state checks",
            "resize": "MAS-owned resize route with lease and run-state checks",
            "detach": "MAS-owned detach route with audited lease release",
        },
        "forbidden_owner": "legacy_mds_daemon_websocket",
        "read_only_default": True,
        "attach_started": False,
        "profile_ref": "/workspace/DM-CVD/profile.local.toml",
        "study_id": "002-dm-china-us-mortality-attribution",
        "study_root": "/workspace/DM-CVD/studies/002-dm-china-us-mortality-attribution",
    }

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
    assert "只读" in html
    assert 'href="../progress/index.html"' in html
    assert "返回进度入口" in html
    assert "论文运行表" in html
    assert "本机时间" in html
    assert "运行时间线" in html
    assert "终端输出" in html
    assert "日志输出" in html
    assert "Terminal Attach Gate" in html
    assert "blocked_by_missing_terminal_input_owner" in html
    assert "legacy_mds_daemon_websocket" in html
    assert "read_only_default=true" in html
    assert "token" in html
    assert "lease" in html
    assert "idempotency" in html
    assert "audit" in html
    assert "input" in html
    assert "resize" in html
    assert "detach" in html
    assert "产物来源" in html
    assert "事件来源" in html
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


def test_live_console_renders_terminal_attach_controls_when_mas_owner_is_available() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console_ui")
    owner = {
        "surface_kind": "mas_terminal_attach_owner",
        "status": "available",
        "owner": "mas_terminal_attach_loopback",
        "capabilities": ["attach", "input", "resize", "detach"],
        "owner_contract": ["token", "lease", "idempotency", "audit", "input", "resize", "detach"],
        "endpoints": {
            "attach": "/terminal/attach",
            "input": "/terminal/input",
            "resize": "/terminal/resize",
            "detach": "/terminal/detach",
        },
    }

    payload = module.build_live_console_ui_payload(
        live_console_snapshot={**_live_console_snapshot(), "terminal_attach_owner": owner},
        generated_at="2026-05-08T01:06:00+00:00",
        profile_ref="/workspace/DM-CVD/profile.local.toml",
        study_id="002-dm-china-us-mortality-attribution",
    )
    html = module.render_live_console_html(payload)

    assert payload["terminal_attach_gate"]["status"] == "available"
    assert payload["terminal_attach_gate"]["owner_surface_kind"] == "mas_terminal_attach_owner"
    assert payload["terminal_attach_gate"]["capabilities"] == ["attach", "input", "resize", "detach"]
    assert payload["terminal_attach_gate"]["attach_started"] is False
    assert "Attach Ready" in html
    assert "Terminal Attach" in html
    assert 'data-terminal-action="attach"' in html
    assert 'data-terminal-action="input"' in html
    assert 'data-terminal-action="resize"' in html
    assert 'data-terminal-action="detach"' in html
    assert "MAS-owned terminal input" in html
    assert "blocked_by_missing_terminal_input_owner" not in html


def test_live_console_terminal_attach_gate_cli_fails_closed_without_owner(monkeypatch, tmp_path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)

    class FakeRuntimeLiveConsole:
        @staticmethod
        def materialize_live_console_session_read_model(**kwargs):
            raise AssertionError("terminal attach gate must fail before starting live console materialization")

    monkeypatch.setattr(cli, "runtime_live_console", FakeRuntimeLiveConsole)

    exit_code = cli.main(
        [
            "runtime",
            "live-console",
            "--profile",
            str(profile_path),
            "--enable-terminal-attach",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 2
    assert payload["surface_kind"] == "mas_terminal_attach_gate"
    assert payload["status"] == "blocked_by_missing_terminal_input_owner"
    assert payload["forbidden_owner"] == "legacy_mds_daemon_websocket"
    assert payload["read_only_default"] is True
    assert set(payload["required_owner_contract"]) == {
        "token",
        "lease",
        "idempotency",
        "audit",
        "input",
        "resize",
        "detach",
    }
    assert payload["attach_started"] is False


def test_live_console_terminal_attach_gate_preempts_snapshot_and_once(monkeypatch, tmp_path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)

    class FakeRuntimeLiveConsole:
        @staticmethod
        def serve_live_console_stream(**kwargs):
            raise AssertionError("terminal attach gate must fail before stream/snapshot starts")

        @staticmethod
        def materialize_live_console_session_read_model(**kwargs):
            raise AssertionError("terminal attach gate must fail before read model materialization")

    monkeypatch.setattr(cli, "runtime_live_console", FakeRuntimeLiveConsole)

    for extra_args in (
        ["--snapshot", "--format", "json"],
        ["--once", "--format", "json"],
    ):
        exit_code = cli.main(
            [
                "runtime",
                "live-console",
                "--profile",
                str(profile_path),
                "--enable-terminal-attach",
                *extra_args,
            ]
        )
        payload = json.loads(capsys.readouterr().out)
        assert exit_code == 2
        assert payload["status"] == "blocked_by_missing_terminal_input_owner"
        assert payload["attach_started"] is False


def test_live_console_terminal_attach_serve_starts_with_blocked_terminal_status(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    live_console_commands = importlib.import_module("med_autoscience.cli_parts.live_console_commands")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    served: dict[str, object] = {}

    class FakeRuntimeLiveConsole:
        @staticmethod
        def serve_live_console_stream(**kwargs):
            raise AssertionError("serve startup must not need a runtime stream read")

    class FakeServer:
        def __init__(self, address, handler):
            self.server_address = address
            served["address"] = address
            served["handler"] = handler

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            served["closed"] = True

        def serve_forever(self):
            served["served"] = True

    monkeypatch.setattr(cli, "runtime_live_console", FakeRuntimeLiveConsole)
    monkeypatch.setattr(live_console_commands.http.server, "ThreadingHTTPServer", FakeServer)

    exit_code = cli.main(
        [
            "runtime",
            "live-console",
            "--profile",
            str(profile_path),
            "--enable-terminal-attach",
            "--serve",
            "--port",
            "4812",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert served["address"] == ("127.0.0.1", 4812)
    assert served["served"] is True
    assert served["closed"] is True
    assert payload["status"] == "serving"
    assert payload["read_only"] is True
    assert payload["terminal_attach"]["status"] == "blocked_by_missing_terminal_input_owner"
    assert payload["terminal_attach"]["reason"] == "no_attach_capable_live_run"
    assert payload["terminal_attach"]["attach_started"] is False


def test_live_console_terminal_attach_cli_reports_available_owner_without_materializing(monkeypatch, tmp_path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    owner_path = workspace_root / "artifacts" / "runtime" / "terminal_attach" / "owner.json"
    owner_path.parent.mkdir(parents=True)
    owner_path.write_text(
        json.dumps(
            {
                "surface_kind": "mas_terminal_attach_owner",
                "status": "available",
                "owner": "mas_terminal_attach_loopback",
                "capabilities": ["attach", "input", "resize", "detach"],
                "owner_contract": ["token", "lease", "idempotency", "audit", "input", "resize", "detach"],
                "endpoints": {
                    "attach": "/terminal/attach",
                    "input": "/terminal/input",
                    "resize": "/terminal/resize",
                    "detach": "/terminal/detach",
                },
            }
        ),
        encoding="utf-8",
    )

    class FakeRuntimeLiveConsole:
        @staticmethod
        def materialize_live_console_session_read_model(**kwargs):
            raise AssertionError("terminal attach API probe must not materialize live console")

    monkeypatch.setattr(cli, "runtime_live_console", FakeRuntimeLiveConsole)

    exit_code = cli.main(
        [
            "runtime",
            "live-console",
            "--profile",
            str(profile_path),
            "--enable-terminal-attach",
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["surface_kind"] == "mas_terminal_attach_gate"
    assert payload["status"] == "available"
    assert payload["owner_surface_kind"] == "mas_terminal_attach_owner"
    assert payload["capabilities"] == ["attach", "input", "resize", "detach"]
    assert payload["attach_started"] is False


def test_live_console_no_live_run_renders_meaningful_empty_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console_ui")
    snapshot = {
        "workspace": {
            "profile_name": "dm-cvd",
            "workspace_root": "/workspace/DM-CVD",
            "workspace_status": "attention_required",
        },
        "studies": [
            {
                "study_id": "002-dm-china-us-mortality-attribution",
                "state_label": "自动运行中",
                "current_stage": "analysis-campaign",
                "active_run_id": None,
                "runtime_health_status": "escalated",
                "supervisor_tick_status": "stale",
                "worker_running": False,
                "blocking_reasons": [
                    "quest_marked_running_but_no_live_session",
                    "runtime_recovery_retry_budget_exhausted",
                ],
                "canonical_runtime_action": "external_supervisor_required",
                "next_action_summary": "需要外层 supervisor 处理 no-live-session。",
                "allowed_controller_actions": ["read_runtime_status", "manual_runtime_review"],
                "runs": [],
                "timeline": [],
                "terminal_sources": [
                    {
                        "label": "terminal",
                        "source_ref": "/workspace/runtime/quests/002/.ds/bash_exec/summary.json",
                        "status": "missing",
                        "tail": [],
                    }
                ],
                "log_sources": [
                    {
                        "label": "worker log",
                        "source_ref": "/workspace/runtime/quests/002/logs/worker.log",
                        "status": "missing",
                        "tail": [],
                    }
                ],
                "artifact_refs": ["/workspace/studies/002/artifacts/runtime/health/latest.json"],
                "event_refs": ["/workspace/studies/002/artifacts/runtime/runtime_supervision/latest.json"],
            }
        ],
        "controller_action_intents": [
            {
                "intent": "request_reconcile",
                "authority": "controller_required",
                "executes_directly": False,
                "command": "medautosci runtime supervisor-reconcile --profile <profile>",
            }
        ],
    }

    payload = module.build_live_console_ui_payload(
        live_console_snapshot=snapshot,
        generated_at="2026-05-08T01:06:00+00:00",
    )
    html = module.render_live_console_html(payload)

    assert payload["empty_state"]["reason"] == "no_live_run"
    assert payload["empty_state"]["study_blockers"][0]["study_id"] == "002-dm-china-us-mortality-attribution"
    assert "当前没有 live run" in html
    assert "标记运行但没有 live session" in html
    assert "runtime 恢复重试预算耗尽" in html
    assert "需要外层 supervisor" in html
    assert "medautosci runtime supervisor-reconcile --profile &lt;profile&gt;" in html
    assert "No stream tail supplied." not in html
    assert ">unknown<" not in html
    assert ">none<" not in html
    assert "source</h3>" not in html
    assert "study.status" not in html
    assert "runtime.health" not in html
    assert "最后可见时间" in html


def test_live_console_static_shell_is_mas_authored_and_read_only() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    html = module.render_live_console_static_shell()

    assert "<!doctype html>" in html
    assert "MAS 运行控制台" in html
    assert "只读" in html
    assert "返回进度入口" in html
    assert "终端 / 日志来源" in html
    assert "控制器动作意图" in html
    assert "artifacts/runtime/live_console/session_read_model/latest.json" in html
    assert "medautosci runtime live-console --profile &lt;profile&gt; --serve" in html
    assert "Terminal Attach" in html
    assert "Attach" in html
    assert "Input" in html
    assert "Resize" in html
    assert "Detach" in html
    assert "DeepScientist" not in html
    assert "MDS WebUI" not in html


def test_live_console_static_shell_does_not_inject_runtime_payload_with_inner_html() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    html = module.render_live_console_static_shell()
    script = html.split("<script>", 1)[1].split("</script>", 1)[0]

    assert ".textContent" in script
    assert ".innerHTML" not in script
