from __future__ import annotations

import importlib


def test_progress_portal_html_renders_human_first_workspace_dashboard_without_losing_alert_provenance() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        cockpit_payload={
            "workspace_alerts": [
                "live worker 已超过 meaningful artifact delta 活动窗口，必须先恢复产物增量或写出平台修复终态。"
            ],
            "studies": [
                {
                    "study_id": "001-dm-cvd-mortality-risk",
                    "state_label": "用户暂停/手动停驻",
                    "current_stage": "parked",
                    "paper_stage": "write",
                    "monitoring": {"health_status": "await_explicit_resume", "supervisor_tick_status": "fresh"},
                    "progress_freshness": {"status": "fresh"},
                    "next_system_action": "优先收口同线质量硬阻塞",
                },
                {
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "state_label": "自动运行中",
                    "current_stage": "live",
                    "paper_stage": "analysis-campaign",
                    "monitoring": {
                        "active_run_id": "mas-run-002",
                        "health_status": "live",
                        "supervisor_tick_status": "fresh",
                    },
                    "progress_freshness": {"status": "fresh"},
                    "next_system_action": "优先完成有限补充分析",
                },
            ],
        },
        generated_at="2026-05-08T01:05:00+00:00",
    )

    html = module.render_progress_portal_html(payload)

    assert "workspace-dashboard" in html
    assert "attention-band" in html
    assert "需要关注的事项" in html
    assert '<span class="metric-label">需关注</span><strong>1</strong>' in html
    assert "论文线工作台" in html
    assert "study-card" in html
    assert "study-card__action" in html
    assert "Live Console" in html
    assert "字段明细" in html
    assert "workspace_cockpit.progress_freshness" in html
    assert "uv run python -m med_autoscience.cli runtime supervisor-reconcile --profile &lt;profile&gt;" in html
    assert "来源" in html
    assert "用途" in html
    assert "期望输出" in html
