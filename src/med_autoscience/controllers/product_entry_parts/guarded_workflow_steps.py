from __future__ import annotations

from typing import Any

from med_autoscience.controllers.medical_paper_operator_actions import (
    guarded_operator_authority_contract,
    guarded_operator_command,
    guarded_pending_action_result,
)


def build_guarded_phase2_workflow_steps(*, workflow_command: str) -> list[dict[str, Any]]:
    return [
        dict(
            step_id=step_id,
            title=title,
            summary=summary,
            surface_kind="medical_paper_readiness_action_card",
            command=workflow_command,
            requires=["profile_ref", "study_id"],
            guarded_operator_command=guarded_operator_command(action_id=step_id, surface_key=surface_key),
            action_result=guarded_pending_action_result(missing_reason=None, next_action=summary),
            authority_contract=guarded_operator_authority_contract(),
            authority="observability_projection_only",
            quality_claim_authorized=False,
            mechanical_projection_can_authorize_quality=False,
        )
        for step_id, surface_key, title, summary in (
            (
                "run_provider_literature_scout",
                "literature_provider_runtime",
                "联网补文献",
                "运行 provider-backed 文献摄取，保留 provider provenance、检索日期和 citation ledger refs。",
            ),
            (
                "materialize_route_decision",
                "route_decision_orchestrator",
                "写入路线裁决",
                "把路线选择、route-back 或 switch-line 决策写入 controller decision 投影。",
            ),
            (
                "resolve_statistical_blockers",
                "statistical_discipline_operations",
                "处理统计 blocker",
                "逐项处理缺失值、precision、外部验证、多重性、临床效用和敏感性分析 blocker/waiver。",
            ),
            (
                "start_revision_rebuttal_loop",
                "revision_rebuttal_loop",
                "启动返修",
                "摄取 reviewer comments，生成 rebuttal action matrix、analysis repair 和 AI reviewer recheck。",
            ),
            (
                "authorize_manuscript_drafting",
                "authoring_runtime_authorization",
                "授权写作",
                "检查目标期刊层、claim/display map、ledger 和 AI reviewer provenance 后再授权 full manuscript drafting。",
            ),
            (
                "run_real_workspace_soak_monitor",
                "real_workspace_soak_monitor",
                "运行真实 soak",
                "从真实或脱敏 study workspace 只读检查多 study soak ready/partial/blocked 状态。",
            ),
        )
    ]
