from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import escape
from typing import Any


def progress_section_explanations(
    *,
    workspace_overview_mode: bool,
    has_workspace_studies: bool,
    has_workspace_alerts: bool,
    has_diagnostics: bool,
    has_latest_events: bool,
    has_source_refs: bool,
) -> list[dict[str, str]]:
    scope = "workspace" if workspace_overview_mode else "study"
    items = [
        _item(
            "工作区概要",
            "workspace_cockpit",
            "确认当前页面代表哪个 workspace、何时生成、是否存在状态缺口。",
            "工作区名称、本机时间、UTC 时间、进度新鲜度、当前论文线、状态缺口。",
            "工作区身份清楚；本机时间带 IANA timezone；状态缺口必须 fail-closed 显示。",
        ),
        _item(
            "论文线概览",
            "workspace_cockpit.studies",
            "在同一 workspace 内区分多篇论文，避免把 DM002、DPCC003 或 paused 线混在一起。",
            "每条 study 的 study_id、运行编号、运行健康、监管心跳、进度新鲜度、论文阶段和焦点。",
            "active study 应有 live worker 或明确 blocker；parked/manual_hold 不应被自动唤醒。",
        ),
        _item(
            "当前状态",
            "study_progress.user_visible_projection" if scope == "study" else "workspace_cockpit",
            "给医生/PI 一句话说明当前状态。",
            "单篇视图显示 study progress；workspace 视图显示总览状态。",
            "避免重复同一句状态；运行异常要优先暴露 runtime blocker。",
        ),
        _item(
            "下一步",
            "study_progress.user_visible_projection.next_system_action",
            "说明系统下一步准备做什么，以及是否需要医生/PI 判断。",
            "下一步动作加 human gate 投影。",
            "如果没有明确动作，应显示需要重新生成 canonical progress projection。",
        ),
        _item(
            "OPL 控制面交接",
            "study_progress.domain_authority_handoff + OPL current_control_state",
            "解释 MAS 当前 domain owner refs 如何交给 OPL 唯一控制面承载。",
            "owner route、typed blocker、handoff status、next owner 和 progress freshness。",
            "不能把 provider/worker 状态误报成 MAS domain completion。",
        ),
        _item(
            "论文与质量",
            "publication_eval/latest.json + workspace_cockpit.studies",
            "展示质量门禁、AI reviewer 和 publication gate 的只读摘要。",
            "workspace 模式只给数量级总览；单篇模式读取 publication eval 摘要。",
            "不能在 workspace 总览中伪造单篇 publication readiness。",
        ),
        _item(
            "文件与交付",
            "delivery/package projection",
            "展示 current package 或交付文件状态。",
            "workspace 模式说明交付由单篇持有；单篇模式显示 package status/refs。",
            "不得直接修改 paper/current_package 或 manuscript/current_package。",
        ),
        _item(
            "工作区告警",
            "workspace_alert_projection",
            "把当前仍需关注的 workspace 级异常放到可操作表格。",
            "当前输出、来源、用途、期望输出、修复/查看命令。",
            "只显示仍有效的告警；旧噪声降级到诊断与修复建议。",
        ),
        _item(
            "诊断与修复建议",
            "workspace.diagnostics.suppressed_alert_items",
            "保留低信息或 legacy 诊断，说明它是否真实以及如何处理。",
            "例如 Hermes supervision 未注册、泛化状态检查、inactive study projection。",
            "真实 blocker 必须给出 owner/命令；泛化文案不能替代具体 study blocker。",
        ),
        _item(
            "最近进展",
            "study_progress.evidence.latest_events",
            "展示最近可见研究推进事件。",
            "事件时间按本机时区显示，同时保留原始时间来源。",
            "如果只有监管心跳而没有 artifact delta，应显示为进度证据不足。",
        ),
        _item(
            "数据来源",
            "source_refs",
            "给维护者审计当前页面到底读了哪些 durable surface。",
            "优先列 runtime health、runtime supervision、controller decisions、publication eval 等 refs。",
            "历史外部 runtime 路径只能作为 legacy provenance，不作为默认 truth。",
        ),
    ]
    if not has_workspace_studies:
        items[1]["expected"] = "应先发现 profile 下的 studies；否则检查 workspace profile 和 studies root。"
    if not has_workspace_alerts:
        items[7]["expected"] = "当前可为空；一旦出现 workspace blocker，必须显示来源、用途、期望输出和修复/查看命令。"
    if not has_diagnostics:
        items[8]["expected"] = "当前可为空；旧噪声或真实 supervision blocker 出现时必须保留解释与命令。"
    if not has_latest_events:
        items[9]["expected"] = "如果没有可展示事件，应明确写出“当前没有带时间戳的进展事件”。"
    if not has_source_refs:
        items[10]["expected"] = "没有 source refs 时必须 fail-closed 显示来源缺失。"
    return items


def render_section_explanations_section(items: Iterable[Mapping[str, Any]]) -> str:
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td>{escape(str(item.get('current_output') or ''))}</td>"
            f"<td>{escape(str(item.get('source') or ''))}</td>"
            f"<td>{escape(str(item.get('purpose') or ''))}</td>"
            f"<td>{escape(str(item.get('expected') or ''))}</td>"
            "</tr>"
        )
    if not rows:
        return ""
    return (
        '<section class="panel wide">'
        "<h2>页面条目说明</h2>"
        '<div class="table-wrap"><table>'
        "<thead><tr><th>条目</th><th>来源</th><th>用途</th><th>期望输出</th></tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table></div></section>"
    )


def _item(current_output: str, source: str, purpose: str, output: str, expected: str) -> dict[str, str]:
    return {
        "current_output": current_output,
        "source": source,
        "purpose": f"{purpose} 当前输出：{output}",
        "expected": expected,
    }


__all__ = ["progress_section_explanations", "render_section_explanations_section"]
