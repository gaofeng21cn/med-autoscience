from __future__ import annotations


_PAPER_STAGE_LABELS = {
    "write": "论文写作与结果收紧",
    "analysis-campaign": "补充分析与稳健性验证",
    "review": "独立审阅与质控",
    "finalize": "定稿与投稿收尾",
    "scientific_anchor_missing": "科学锚点仍缺失",
    "write_stage_ready": "论文写作阶段已放行",
    "publishability_gate_blocked": "论文可发表性门控未放行",
    "bundle_stage_blocked": "投稿打包阶段存在硬阻塞",
    "bundle_stage_ready": "投稿打包阶段已放行",
    "manual_hold": "手动停驻待新方案",
}
_CURRENT_STAGE_LABELS = {
    "study_completed": "研究已进入收尾/交付",
    "auto_runtime_parked": "自动运行已停驻",
    "manual_finishing": "人工收尾与兼容保护",
    "managed_runtime_recovering": "托管运行恢复中",
    "managed_runtime_degraded": "托管运行健康降级",
    "managed_runtime_escalated": "托管运行已升级告警",
    "managed_runtime_supervision_gap": "OPL runtime manager 托管监管存在缺口",
    "waiting_physician_decision": "等待用户判断",
    "waiting_user_decision": "等待用户判断",
    "publication_supervision": "论文可发表性监管",
    "managed_runtime_active": "托管运行正在推进",
    "runtime_blocked": "自动推进被阻断",
    "runtime_preflight": "研究准备或预检阶段",
}
_DECISION_TYPE_LABELS = {
    "continue_same_line": "继续当前主线",
    "bounded_analysis": "有限补充分析",
    "relaunch_branch": "重启当前分支",
    "reroute_study": "改换研究主线",
    "stop_loss": "止损停题",
    "promote_to_delivery": "推进到交付线",
}
_CONTROLLER_ACTION_LABELS = {
    "ensure_study_runtime": "继续托管推进当前研究运行",
    "ensure_study_runtime_relaunch_stopped": "显式重启已经停止的研究运行",
    "pause_runtime": "先暂停当前运行",
    "stop_runtime": "停止当前运行",
}
_REASON_LABELS = {
    "publishability_gate_blocked": "论文可发表性门控尚未放行。",
    "quest_completion_requested_before_publication_gate_clear": "运行时过早申请结题，论文门控仍要求继续自修。",
    "quest_parked_on_unchanged_finalize_state": "投稿包/人审包已到可交付节点；MAS/MDS 已释放自动运行资源，等待用户审阅、显式 resume 或新的修订输入。",
    "quest_waiting_for_submission_metadata": "浅层投稿包已经交付，当前只差作者、单位、伦理、基金和声明等人工前置信息；系统已停车，等待显式唤醒。",
    "quest_drifting_into_write_without_gate_approval": "运行时已经漂进写作/定稿，但发表门控尚未放行，MAS 正在把它拉回论文门控主线。",
    "quest_stale_decision_after_write_stage_ready": "论文写作阶段已经放行，但运行时仍停在旧 decision，MAS 正在把它切回写作主线。",
    "quest_stopped_by_controller_guard": "运行时被 MAS 纠偏控制器短暂停下，MAS 将自动继续修复当前论文硬阻塞。",
    "quest_stopped_requires_explicit_rerun": "当前 quest 已停止；如需继续，必须显式 rerun 或 relaunch。",
    "quest_waiting_for_explicit_wakeup_after_manual_hold": "当前论文线已按用户任务手动停驻；等待新方案和显式唤醒。",
    "study_completion_contract_not_ready": "study-level 完成声明已存在，但 final submission 证据还未补齐，当前不能按完成态收口。",
    "startup_boundary_not_ready_for_resume": "运行前置条件尚未满足，系统不能直接续跑。",
    "runtime_reentry_not_ready_for_resume": "运行重入条件尚未满足，系统不能直接续跑。",
    "quest_already_running": "托管运行时已经处于自动推进状态。",
}
_WATCH_BLOCKER_LABELS = {
    "active_run_drifting_into_write_without_gate_approval": "当前 live run 已经漂进写作或定稿，但发表门控仍未放行，必须先拉回论文门控主线。",
    "missing_post_main_publishability_gate": "论文可发表性门控尚未放行。",
    "medical_publication_surface_blocked": "论文叙事或方法/结果书写面仍有硬阻塞。",
    "registry_contract_mismatch": "论文展示注册表与 reporting contract 不一致，需要先修正稿面契约。",
    "claim_evidence_map_missing_or_incomplete": "关键 claim-to-evidence 对照仍不完整。",
    "figure_loop_budget_exceeded": "图表推进陷入重复打磨循环，当前 run 应被拉回主线。",
    "figure_reopened_after_resolution": "已经收住的图表又被重新打开，当前 run 存在质量回退风险。",
    "accepted_figure_reopened": "已接受的图表又被重新打开，当前 run 存在质量回退风险。",
    "references_below_floor_during_figure_loop": "图表循环期间参考文献数量低于下限，当前稿件质量不达标。",
    "reference_gaps_present": "关键参考文献仍有缺口。",
    "missing_reporting_guideline_checklist": "报告规范核对表仍未补齐。",
    "forbidden_manuscript_terms_present": "当前稿件仍含不允许的术语表达，需要清理。",
    "figure_catalog_missing_or_incomplete": "关键图表目录仍不完整。",
    "table_catalog_missing_or_incomplete": "关键表格目录仍不完整。",
    "required_display_catalog_coverage_incomplete": "论文关键展示面覆盖仍不完整。",
    "public_evidence_decisions_missing_or_incomplete": "公开数据进入论文前缺少明确的 earned/drop 决策记录。",
    "paper_facing_public_data_without_earned_evidence": "公开数据已经写入论文面，但还没有真正 earned 的结果支撑。",
    "ama_pdf_defaults_missing": "AMA 稿件导出默认配置仍未补齐。",
    "results_narrative_map_missing_or_incomplete": "结果叙事映射仍不完整。",
    "methods_section_structure_missing_or_incomplete": "方法学章节结构仍不完整。",
    "figure_semantics_manifest_missing_or_incomplete": "图表语义清单仍不完整。",
    "derived_analysis_manifest_missing_or_incomplete": "衍生分析清单仍不完整。",
    "submission_checklist_contains_unclassified_blocking_items": "投稿检查清单里仍有未归类的硬阻塞。",
    "methods_completeness_incomplete": "医学论文方法报告仍不完整，需补齐研究设计、队列、变量、模型、验证和统计分析说明。",
    "statistical_reporting_incomplete": "统计报告仍不完整，需补齐汇总格式、P 值和亚组检验说明。",
    "table_figure_claim_map_missing_or_incomplete": "表图与论文 claim 的对应关系仍未补齐。",
    "clinical_actionability_incomplete": "分型/真实世界论文仍缺少临床可行动性说明，包括治疗缺口和随访或结局相关性。",
    "prediction_model_methods_reporting_incomplete": "预测模型方法报告仍不完整，需补齐 TRIPOD/TRIPOD+AI 关键方法字段。",
    "time_to_event_prediction_reporting_incomplete": "时间到事件预测报告仍不完整，需补齐 PH、非线性、竞争事件 screen 和绝对风险校准说明。",
    "decision_curve_clinical_utility_incomplete": "DCA 临床效用表述仍不完整，需绑定阈值范围、临床动作和使用边界。",
    "prediction_performance_reporting_incomplete": "预测性能报告仍不完整，需补齐验证样本、事件数、C-index/校准和高风险尾部结果。",
    "baseline_balance_reporting_incomplete": "基线表平衡报告仍不完整，需补齐变量级缺失和标准化差异。",
    "competing_risk_reporting_incomplete": "竞争风险报告仍不完整，需说明非目标死亡处理和绝对风险敏感性验证。",
}
_BLOCKER_LABELS = {
    "active_run_drifting_into_write_without_gate_approval": "当前 live run 已经漂进写作或定稿，但发表门控仍未放行，必须先拉回论文门控主线。",
    "missing_submission_minimal": "缺少最小投稿包导出。",
    "submission_grade_active_figure_floor_unmet": "活跃主稿图数量仍低于投稿级下限，当前图证不足以支撑投稿级稿件。",
    "registry_contract_mismatch": "论文展示注册表与 reporting contract 不一致，需要先修正稿面契约。",
    "stale_study_delivery_mirror": "study 目录里的投稿包镜像已经过期，仍停在旧版本，不能当作当前包。",
    "medical_publication_surface_blocked": "论文叙事或方法/结果书写面仍有硬阻塞。",
    "forbidden_manuscript_terminology": "当前稿件仍含不允许的术语表达，需要清理。",
    "public_evidence_decisions_missing_or_incomplete": "公开数据进入论文前缺少明确的 earned/drop 决策记录。",
    "paper_facing_public_data_without_earned_evidence": "公开数据已经写入论文面，但还没有真正 earned 的结果支撑。",
    "submission_checklist_contains_unclassified_blocking_items": "投稿检查清单里仍有未归类的硬阻塞。",
    "methods_completeness_incomplete": "医学论文方法报告仍不完整，需补齐研究设计、队列、变量、模型、验证和统计分析说明。",
    "statistical_reporting_incomplete": "统计报告仍不完整，需补齐汇总格式、P 值和亚组检验说明。",
    "table_figure_claim_map_missing_or_incomplete": "表图与论文 claim 的对应关系仍未补齐。",
    "clinical_actionability_incomplete": "分型/真实世界论文仍缺少临床可行动性说明，包括治疗缺口和随访或结局相关性。",
    "prediction_model_methods_reporting_incomplete": "预测模型方法报告仍不完整，需补齐 TRIPOD/TRIPOD+AI 关键方法字段。",
    "time_to_event_prediction_reporting_incomplete": "时间到事件预测报告仍不完整，需补齐 PH、非线性、竞争事件 screen 和绝对风险校准说明。",
    "decision_curve_clinical_utility_incomplete": "DCA 临床效用表述仍不完整，需绑定阈值范围、临床动作和使用边界。",
    "prediction_performance_reporting_incomplete": "预测性能报告仍不完整，需补齐验证样本、事件数、C-index/校准和高风险尾部结果。",
    "baseline_balance_reporting_incomplete": "基线表平衡报告仍不完整，需补齐变量级缺失和标准化差异。",
    "competing_risk_reporting_incomplete": "竞争风险报告仍不完整，需说明非目标死亡处理和绝对风险敏感性验证。",
}
_ACTION_LABELS = {
    "return_to_publishability_gate": "先补齐论文证据与叙事，再回到发表门控复核。",
    "continue_write_stage": "继续当前论文写作阶段。",
    "continue_bundle_stage": "继续当前投稿打包阶段。",
    "complete_bundle_stage": "完成当前投稿打包阶段。",
    "controller_review_required": "需要控制面重新判断下一步。",
    "refresh_startup_hydration": "需要刷新运行前置上下文后再继续。",
    "human_confirmation_required": "等待用户明确确认下一步。",
    "supervise_runtime_only": "当前以监督托管运行时为主，不直接接管执行。",
}
_ROUTE_REPAIR_ACTION_TYPES = {"continue_same_line", "route_back_same_line", "bounded_analysis"}
_ROUTE_REPAIR_MODE_LABELS = {
    "same_line_route_back": "同线质量修复",
    "bounded_analysis": "有限补充分析",
}
_RUNTIME_DECISION_LABELS = {
    "noop": "无需额外动作",
    "blocked": "当前被阻断",
    "resume": "继续托管续跑",
    "relaunch_stopped": "重新拉起已停止运行",
    "create_and_start": "创建并启动新运行",
    "create_only": "仅创建研究运行",
    "completed": "研究运行已完成",
    "lightweight": "仅做轻量监管",
}
_RUNTIME_HEALTH_LABELS = {
    "live": "运行健康在线",
    "recovering": "恢复中",
    "degraded": "健康降级",
    "escalated": "已升级告警",
    "unknown": "状态未知",
    "none": "未检测到在线 worker",
}
_SUPERVISOR_TICK_STATUS_LABELS = {
    "fresh": "监管心跳新鲜",
    "stale": "监管心跳已陈旧",
    "missing": "监管心跳缺失",
    "invalid": "监管心跳记录无效",
    "not_required": "当前不要求监管心跳",
}
_PROGRESS_FRESHNESS_STATUS_LABELS = {
    "fresh": "研究推进信号新鲜",
    "stale": "研究推进信号已陈旧",
    "missing": "研究推进信号缺失",
    "not_required": "当前不要求新的自动推进信号",
}
_INTERVENTION_SEVERITY_LABELS = {
    "critical": "高优先级",
    "warning": "需要尽快处理",
    "handoff": "等待人工判断",
    "observe": "继续监督",
}
_RECOVERY_ACTION_MODE_LABELS = {
    "refresh_supervision": "优先刷新 OPL runtime manager 托管监管",
    "continue_or_relaunch": "继续或重新拉起当前 study",
    "inspect_progress": "先读取当前进度与阻塞",
    "human_decision_review": "等待用户判断",
    "auto_runtime_parked": "自动运行停驻",
    "maintain_manual_finish_guard": "保持人工收尾显式保护",
    "monitor_only": "继续监督当前 study",
}
_OPERATOR_STATUS_HANDLING_LABELS = {
    "runtime_supervision_recovering": "监管恢复中",
    "runtime_recovering": "运行恢复中",
    "publication_gate_specificity_required": "发表门控需具体化",
    "paper_surface_refresh_in_progress": "人类查看面刷新中",
    "scientific_or_quality_repair_in_progress": "论文硬阻塞处理中",
    "waiting_human_decision": "等待用户判断",
    "waiting_user_decision": "等待用户判断",
    "package_ready_handoff": "投稿包/人审包交付停驻",
    "external_metadata_pending": "外部投稿元数据待补",
    "external_input_pending": "等待外部输入",
    "external_upstream_pending": "等待上游服务恢复",
    "platform_startup_noise": "平台启动噪声退避",
    "explicit_resume_pending": "等待显式恢复",
    "platform_repair_pending": "等待 MAS/MDS 平台修复",
    "preflight_contract_pending": "等待运行前置合同满足",
    "auto_runtime_parked": "自动运行已停驻",
    "manual_finishing": "人工收尾显式保护",
    "monitor_only": "持续监督中",
}
_OPERATOR_STATUS_TRUTH_SOURCE_LABELS = {
    "runtime_supervision": "runtime_supervision/latest.json",
    "supervisor_tick_audit": "supervisor_tick_audit",
    "publication_eval": "publication_eval/latest.json",
    "controller_confirmation": "controller_confirmation_summary.json",
    "controller_decision": "controller_decisions/latest.json",
    "runtime_watch": "runtime_watch",
    "latest_event": "latest_events[0]",
}
_CONTINUATION_REASON_LABELS = {
    "unchanged_finalize_state": "运行停在未变化的定稿总结态",
}
_TEXT_LABELS = {
    "bundle suggestions are downstream-only until the publication gate allows write": "在发表门控放行写作前，投稿包相关建议都只是后续件。",
    "the publication gate allows write; writing-stage work is now on the critical path": "发表门控已经放行写作，论文写作阶段进入关键路径。",
    "bundle-stage work is unlocked and can proceed on the critical path": "投稿打包阶段已被全局门控放行，可以进入关键路径。",
    "bundle-stage blockers are now on the critical path for this paper line": "当前论文线的关键路径已经进入投稿打包阻塞修复。",
    "paper bundle exists, but the active blockers still belong to the publishability surface; bundle suggestions stay downstream-only until the gate clears": "论文包雏形已经存在，但当前硬阻塞仍在论文可发表性面；在门控放行前，投稿包相关建议都只是后续件。",
}
_TEXT_REPLACEMENTS = (
    ("paper bundle exists", "论文包雏形已经存在"),
    ("the active blockers still belong to the publishability surface", "当前硬阻塞仍在论文可发表性面"),
    ("bundle suggestions stay downstream-only until the gate clears", "在门控放行前，投稿包相关建议都只是后续件"),
    ("publishability surface", "论文可发表性面"),
    ("publication gate allows write", "发表门控放行写作"),
    ("gate clears", "门控放行"),
    ("submission bundle", "最小投稿包"),
    ("bundle 相关建议", "投稿包相关建议"),
    ("publishability gate blocked", "论文可发表性门控未放行"),
    ("missing submission minimal", "缺少最小投稿包导出"),
    ("forbidden manuscript terminology", "当前稿件仍含不允许的术语表达，需要清理"),
    ("physician decision", "user decision"),
    ("医生或 PI", "用户"), ("医生/PI", "用户"),
    ("医生追加确认", "用户追加确认"), ("医生确认", "用户确认"),
    ("需要医生", "需要用户"), ("live 状态", "在线状态"),
    (", but ", "，但"),
    ("; ", "；"),
)
_SUPERVISOR_TICK_GAP_STATUSES = {"missing", "invalid", "stale"}
_PROGRESS_STALE_AFTER_SECONDS = 12 * 60 * 60

__all__ = [name for name in globals() if name.startswith("_")]
