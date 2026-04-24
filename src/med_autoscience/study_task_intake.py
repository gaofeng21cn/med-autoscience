from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from med_autoscience.profiles import WorkspaceProfile

SCHEMA_VERSION = 1
TASK_INTAKE_RELATIVE_ROOT = Path("artifacts") / "controller" / "task_intake"
STARTUP_BRIEF_BLOCK_BEGIN = "<!-- MAS_TASK_INTAKE:BEGIN -->"
STARTUP_BRIEF_BLOCK_END = "<!-- MAS_TASK_INTAKE:END -->"

_ENTRY_MODE_LABELS = {
    "full_research": "完整研究（full_research）",
}
_DIRECT_FINALIZE_DOWNGRADE_MARKERS = (
    "不能按已达投稿包里程碑直接收口",
    "不得直接按外投收口",
    "submission-ready/finalize 判断降回",
    "降回待修订后再评估",
    "downgrade the current submission-ready/finalize judgment",
)
_ANALYSIS_ROUTE_MARKERS = (
    "统计分析",
    "subgroup",
    "association analysis",
    "补充分析",
    "分层",
    "卡方",
    "analysis-campaign",
)
_REVIEWER_REVISION_MARKERS = (
    "reviewer feedback",
    "reviewer comment",
    "review comments",
    "reviewer revision",
    "manuscript revision",
    "manuscript-change",
    "paper revision",
    "revise manuscript",
    "revision checklist",
    "导师反馈",
    "专家反馈",
    "审稿意见",
    "审稿人意见",
    "论文修改",
    "稿件修改",
    "修改意见",
    "补分析",
    "改表",
    "改图",
    "introduction feedback",
    "methods feedback",
    "results feedback",
    "figure feedback",
    "table feedback",
)
_REVISION_INTAKE_CHECKLIST: tuple[tuple[str, str, str], ...] = (
    ("text_revisions", "text revisions", "Introduction/Methods/Results/Discussion 等文字修订点已逐条定位。"),
    ("methods_completeness", "methods completeness", "方法学补充、数据来源、纳排、变量和流程说明已补齐或记录为缺口。"),
    ("statistical_analysis", "statistical analysis", "新增或修订统计分析、敏感性/亚组/稳健性需求已绑定证据来源。"),
    ("tables_figures", "tables/figures", "表格、图片、图注和补充材料改动范围已列明。"),
    ("follow_up_evidence", "follow-up evidence", "后续证据、补充结果和不可完成项有明确状态。"),
    ("discussion_claim_guardrails", "discussion/claim guardrails", "讨论、结论和 claim 边界没有越过当前证据包。"),
    ("handoff_evidence_surface", "handoff/evidence surface", "durable handoff 写明数据源、脚本入口、输出表图、改动范围、claim guardrails 与 canonical source 回灌状态。"),
)
_BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS = frozenset({"continue_bundle_stage", "complete_bundle_stage"})
_DETERMINISTIC_SUBMISSION_CLOSEOUT_BLOCKERS = frozenset(
    {
        "stale_submission_minimal_authority",
        "stale_study_delivery_mirror",
        "submission_surface_qc_failure_present",
        "submission_hardening_incomplete",
    }
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalized_strings(values: Iterable[object]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            normalized.append(text)
    return normalized


def _entry_mode_label(value: object) -> str:
    text = _non_empty_text(value) or "full_research"
    return _ENTRY_MODE_LABELS.get(text, text)


def _normalize_timestamp(value: object) -> datetime | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def task_intake_root(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / TASK_INTAKE_RELATIVE_ROOT


def latest_task_intake_json_path(*, study_root: Path) -> Path:
    return task_intake_root(study_root=study_root) / "latest.json"


def latest_task_intake_markdown_path(*, study_root: Path) -> Path:
    return task_intake_root(study_root=study_root) / "latest.md"


def _timestamped_task_intake_json_path(*, study_root: Path, slug: str) -> Path:
    return task_intake_root(study_root=study_root) / f"{slug}.json"


def _timestamped_task_intake_markdown_path(*, study_root: Path, slug: str) -> Path:
    return task_intake_root(study_root=study_root) / f"{slug}.md"


def read_latest_task_intake(*, study_root: Path) -> dict[str, Any] | None:
    latest_path = latest_task_intake_json_path(study_root=study_root)
    if not latest_path.exists():
        return None
    payload = json.loads(latest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"task intake payload must be a JSON object: {latest_path}")
    return payload


def summarize_task_intake(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    task_intent = _non_empty_text(payload.get("task_intent"))
    entry_mode = _non_empty_text(payload.get("entry_mode")) or "full_research"
    if task_intent is None and entry_mode is None:
        return None
    summary = {
        "task_id": _non_empty_text(payload.get("task_id")),
        "study_id": _non_empty_text(payload.get("study_id")),
        "emitted_at": _non_empty_text(payload.get("emitted_at")),
        "entry_mode": entry_mode,
        "task_intent": task_intent,
        "journal_target": _non_empty_text(payload.get("journal_target")),
        "constraints": _normalized_strings(payload.get("constraints") or []),
        "evidence_boundary": _normalized_strings(payload.get("evidence_boundary") or []),
        "trusted_inputs": _normalized_strings(payload.get("trusted_inputs") or []),
        "reference_papers": _normalized_strings(payload.get("reference_papers") or []),
        "first_cycle_outputs": _normalized_strings(payload.get("first_cycle_outputs") or []),
    }
    revision_intake = build_reviewer_revision_intake(payload)
    if revision_intake is not None:
        summary["revision_intake"] = revision_intake
    return summary


def _task_intake_text_corpus(payload: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()
    values: list[object] = [
        payload.get("task_intent"),
        *(payload.get("constraints") or []),
        *(payload.get("evidence_boundary") or []),
        *(payload.get("trusted_inputs") or []),
        *(payload.get("reference_papers") or []),
        *(payload.get("first_cycle_outputs") or []),
    ]
    return tuple(_normalized_strings(values))


def _task_intake_contains_any(payload: dict[str, Any] | None, markers: tuple[str, ...]) -> bool:
    corpus = _task_intake_text_corpus(payload)
    if not corpus:
        return False
    for text in corpus:
        lowered = text.lower()
        if any(marker.lower() in lowered for marker in markers):
            return True
    return False


def task_intake_is_reviewer_revision(payload: dict[str, Any] | None) -> bool:
    return _task_intake_contains_any(payload, _REVIEWER_REVISION_MARKERS)


def build_reviewer_revision_intake(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not task_intake_is_reviewer_revision(payload):
        return None
    return {
        "kind": "reviewer_revision",
        "status": "active",
        "checklist": [item_id for item_id, _, _ in _REVISION_INTAKE_CHECKLIST],
        "checklist_items": [
            {"id": item_id, "label": label, "status": "pending", "requirement": requirement}
            for item_id, label, requirement in _REVISION_INTAKE_CHECKLIST
        ],
        "handoff_required": True,
        "handoff_evidence_surface": {
            "required": True,
            "read_before_mds_resume": True,
            "minimum_fields": [
                "data sources",
                "script entrypoints",
                "changed tables/figures",
                "change scope",
                "claim guardrails",
                "canonical source reconciliation status",
                "next owner: MAS controller or MDS paper surface",
            ],
        },
    }


def task_intake_overrides_auto_manual_finish(payload: dict[str, Any] | None) -> bool:
    # 这里只接受 durable task intake 中明确写出的强语义，不做泛化 NLP 推断。
    return _task_intake_contains_any(payload, _DIRECT_FINALIZE_DOWNGRADE_MARKERS)


def _integer_value(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return int(text)
    return None


def _mapping_value(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _surface_emitted_at(payload: dict[str, Any] | None) -> datetime | None:
    if not isinstance(payload, dict):
        return None
    return _normalize_timestamp(payload.get("emitted_at") or payload.get("generated_at"))


def _closeout_surface_is_fresher_than_task_intake(
    payload: dict[str, Any] | None,
    *surfaces: dict[str, Any] | None,
) -> bool:
    task_intake_emitted_at = _surface_emitted_at(payload)
    if task_intake_emitted_at is None:
        return False
    latest_surface_emitted_at = max(
        (
            surface_emitted_at
            for surface_emitted_at in (_surface_emitted_at(surface) for surface in surfaces)
            if surface_emitted_at is not None
        ),
        default=None,
    )
    return latest_surface_emitted_at is not None and latest_surface_emitted_at >= task_intake_emitted_at


def _task_intake_yields_to_blocked_submission_closeout(
    publishability_gate_report: dict[str, Any] | None,
) -> bool:
    if not isinstance(publishability_gate_report, dict):
        return False
    if _non_empty_text(publishability_gate_report.get("status")) != "blocked":
        return False
    blockers = {
        str(item or "").strip()
        for item in (publishability_gate_report.get("blockers") or [])
        if str(item or "").strip()
    }
    if not blockers or blockers - _DETERMINISTIC_SUBMISSION_CLOSEOUT_BLOCKERS:
        return False
    open_supplementary_count = _integer_value(
        publishability_gate_report.get("paper_line_open_supplementary_count")
    )
    if open_supplementary_count != 0:
        return False
    if _non_empty_text(publishability_gate_report.get("medical_publication_surface_status")) == "blocked":
        return False
    if publishability_gate_report.get("medical_publication_surface_current") is False:
        return False
    return True


def _task_intake_yields_to_bundle_only_submission_closeout(
    *,
    payload: dict[str, Any] | None,
    publishability_gate_report: dict[str, Any] | None,
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    quality_closure_truth = _mapping_value((evaluation_summary or {}).get("quality_closure_truth"))
    quality_review_loop = _mapping_value((evaluation_summary or {}).get("quality_review_loop"))
    quality_assessment = _mapping_value((evaluation_summary or {}).get("quality_assessment"))
    human_review_readiness = _mapping_value(quality_assessment.get("human_review_readiness"))
    closure_state = (
        _non_empty_text(quality_closure_truth.get("state"))
        or _non_empty_text(quality_review_loop.get("closure_state"))
    )
    if closure_state != "bundle_only_remaining":
        return False
    human_review_status = _non_empty_text(human_review_readiness.get("status"))
    if human_review_status not in {None, "ready"}:
        return False
    if isinstance(publishability_gate_report, dict):
        if _non_empty_text(publishability_gate_report.get("status")) not in {None, "clear"}:
            return False
        gate_blockers = {
            str(item or "").strip()
            for item in (publishability_gate_report.get("blockers") or [])
            if str(item or "").strip()
        }
        if gate_blockers:
            return False
        current_required_action = _non_empty_text(publishability_gate_report.get("current_required_action"))
        if (
            current_required_action is not None
            and current_required_action not in _BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS
        ):
            return False
        if publishability_gate_report.get("bundle_tasks_downstream_only") is True:
            return False
    return _closeout_surface_is_fresher_than_task_intake(
        payload,
        publishability_gate_report,
        evaluation_summary,
    )


def task_intake_yields_to_deterministic_submission_closeout(
    payload: dict[str, Any] | None,
    *,
    publishability_gate_report: dict[str, Any] | None,
    evaluation_summary: dict[str, Any] | None = None,
) -> bool:
    if not task_intake_overrides_auto_manual_finish(payload):
        return False
    if _task_intake_yields_to_blocked_submission_closeout(publishability_gate_report):
        return True
    return _task_intake_yields_to_bundle_only_submission_closeout(
        payload=payload,
        publishability_gate_report=publishability_gate_report,
        evaluation_summary=evaluation_summary,
    )


def build_task_intake_progress_override(
    payload: dict[str, Any] | None,
    *,
    publishability_gate_report: dict[str, Any] | None = None,
    evaluation_summary: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not task_intake_overrides_auto_manual_finish(payload):
        return None
    if task_intake_yields_to_deterministic_submission_closeout(
        payload,
        publishability_gate_report=publishability_gate_report,
        evaluation_summary=evaluation_summary,
    ):
        return None
    route_target = "analysis-campaign" if _task_intake_contains_any(payload, _ANALYSIS_ROUTE_MARKERS) else "write"
    route_target_label = {
        "analysis-campaign": "补充分析与稳健性验证",
        "write": "论文写作与结果收紧",
    }[route_target]
    current_required_action = {
        "analysis-campaign": "return_to_analysis_campaign",
        "write": "continue_write_stage",
    }[route_target]
    same_line_state = "bounded_analysis" if route_target == "analysis-campaign" else "same_line_route_back"
    same_line_state_label = {
        "bounded_analysis": "有限补充分析",
        "same_line_route_back": "同线质量修复",
    }[same_line_state]
    first_cycle_outputs = _normalized_strings(payload.get("first_cycle_outputs") or [])
    current_focus = (
        first_cycle_outputs[0]
        if first_cycle_outputs
        else "当前最新 task intake 指定的首轮修订产出是否已经补齐并写回 manuscript？"
    )
    blocker_summary = (
        "最新 task intake 已明确要求回到待修订状态；旧的 submission-ready/finalize 收口判断不能继续作为当前真相。"
    )
    route_summary = (
        f"最新 task intake 已明确重开同一论文线修订；先回到“{route_target_label}”，"
        f"完成“{current_focus}”，再重新评估 submission-ready/finalize。"
    )
    execution_summary = (
        f"当前质量执行线服从最新 task intake；先回到“{route_target_label}”，完成“{current_focus}”。"
    )
    quality_closure_summary = (
        f"{blocker_summary} 当前应先完成“{current_focus}”，再进入下一轮论文质量复评。"
    )
    return {
        "blocker_summary": blocker_summary,
        "current_stage_summary": blocker_summary,
        "next_system_action": route_summary,
        "current_required_action": current_required_action,
        "paper_stage": route_target,
        "paper_stage_summary": route_summary,
        "quality_closure_truth": {
            "state": "quality_repair_required",
            "summary": quality_closure_summary,
            "current_required_action": current_required_action,
            "route_target": route_target,
        },
        "quality_execution_lane": {
            "lane_id": "general_quality_repair",
            "lane_label": "质量修复",
            "repair_mode": same_line_state,
            "route_target": route_target,
            "route_key_question": current_focus,
            "summary": execution_summary,
            "why_now": blocker_summary,
        },
        "same_line_route_truth": {
            "surface_kind": "same_line_route_truth",
            "same_line_state": same_line_state,
            "same_line_state_label": same_line_state_label,
            "route_mode": "return",
            "route_target": route_target,
            "route_target_label": route_target_label,
            "summary": route_summary,
            "current_focus": current_focus,
        },
        "same_line_route_surface": {
            "surface_kind": "same_line_route_surface",
            "lane_id": "general_quality_repair",
            "repair_mode": same_line_state,
            "route_target": route_target,
            "route_target_label": route_target_label,
            "route_key_question": current_focus,
            "summary": execution_summary,
            "why_now": blocker_summary,
            "current_required_action": current_required_action,
            "closure_state": "quality_repair_required",
        },
    }


def render_task_intake_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Study Task Intake",
        "",
        f"- 当前 study: `{payload['study_id']}`",
        f"- 写入时间: `{payload['emitted_at']}`",
        f"- 当前入口模式: {_entry_mode_label(payload.get('entry_mode'))}",
        f"- 当前投稿目标: `{payload.get('journal_target') or 'none'}`",
        "",
        "## 当前任务意图",
        "",
        str(payload.get("task_intent") or "").strip() or "未提供",
        "",
        "## 约束",
        "",
    ]
    constraints = list(payload.get("constraints") or [])
    if constraints:
        lines.extend(f"- {item}" for item in constraints)
    else:
        lines.append("- None")
    lines.extend(["", "## 证据边界", ""])
    evidence_boundary = list(payload.get("evidence_boundary") or [])
    if evidence_boundary:
        lines.extend(f"- {item}" for item in evidence_boundary)
    else:
        lines.append("- None")
    lines.extend(["", "## 可信输入", ""])
    trusted_inputs = list(payload.get("trusted_inputs") or [])
    if trusted_inputs:
        lines.extend(f"- {item}" for item in trusted_inputs)
    else:
        lines.append("- None")
    lines.extend(["", "## 参考文献", ""])
    reference_papers = list(payload.get("reference_papers") or [])
    if reference_papers:
        lines.extend(f"- {item}" for item in reference_papers)
    else:
        lines.append("- None")
    lines.extend(["", "## 首轮交付", ""])
    first_cycle_outputs = list(payload.get("first_cycle_outputs") or [])
    if first_cycle_outputs:
        lines.extend(f"- {item}" for item in first_cycle_outputs)
    else:
        lines.append("- None")
    revision_intake = build_reviewer_revision_intake(payload)
    if revision_intake is not None:
        lines.extend(["", "## Revision Intake Checklist", ""])
        for item in revision_intake["checklist_items"]:
            lines.append(f"- [{item['status']}] {item['label']}: {item['requirement']}")
        lines.extend(
            [
                "",
                "## Revision Handoff Constraint",
                "",
                "- 前台直接改稿必须留下 durable handoff/evidence surface。",
                "- MDS 恢复前必须优先读取 latest revision handoff/evidence surface。",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def render_task_intake_runtime_context(payload: dict[str, Any]) -> str:
    lines = [
        f"Task intent: {payload.get('task_intent') or '未提供'}",
        f"Entry mode: {payload.get('entry_mode') or 'full_research'}",
    ]
    journal_target = _non_empty_text(payload.get("journal_target"))
    if journal_target is not None:
        lines.append(f"Journal target: {journal_target}")
    constraints = _normalized_strings(payload.get("constraints") or [])
    if constraints:
        lines.append("Constraints:")
        lines.extend(f"- {item}" for item in constraints)
    evidence_boundary = _normalized_strings(payload.get("evidence_boundary") or [])
    if evidence_boundary:
        lines.append("Evidence boundary:")
        lines.extend(f"- {item}" for item in evidence_boundary)
    trusted_inputs = _normalized_strings(payload.get("trusted_inputs") or [])
    if trusted_inputs:
        lines.append("Trusted inputs:")
        lines.extend(f"- {item}" for item in trusted_inputs)
    first_cycle_outputs = _normalized_strings(payload.get("first_cycle_outputs") or [])
    if first_cycle_outputs:
        lines.append("First-cycle outputs:")
        lines.extend(f"- {item}" for item in first_cycle_outputs)
    revision_intake = build_reviewer_revision_intake(payload)
    if revision_intake is not None:
        checklist = ", ".join(item["id"] for item in revision_intake["checklist_items"])
        lines.extend(
            [
                "Revision intake: reviewer_revision",
                f"Revision checklist: {checklist}",
                "Foreground manuscript edits require durable handoff/evidence surface.",
                "Latest revision handoff/evidence surface must be read before MDS resume.",
            ]
        )
    return "\n".join(lines)


def render_startup_brief_task_block(payload: dict[str, Any]) -> str:
    body = render_task_intake_markdown(payload).strip()
    return f"{STARTUP_BRIEF_BLOCK_BEGIN}\n{body}\n{STARTUP_BRIEF_BLOCK_END}"


def upsert_startup_brief_task_block(*, existing_text: str, payload: dict[str, Any]) -> str:
    existing = str(existing_text or "").strip()
    replacement = render_startup_brief_task_block(payload)
    if STARTUP_BRIEF_BLOCK_BEGIN in existing and STARTUP_BRIEF_BLOCK_END in existing:
        prefix, rest = existing.split(STARTUP_BRIEF_BLOCK_BEGIN, 1)
        _, suffix = rest.split(STARTUP_BRIEF_BLOCK_END, 1)
        rebuilt = prefix.rstrip()
        if rebuilt:
            rebuilt += "\n\n"
        rebuilt += replacement
        suffix = suffix.strip()
        if suffix:
            rebuilt += f"\n\n{suffix}"
        return rebuilt.strip() + "\n"
    if not existing:
        existing = "# Startup brief"
    return f"{existing.rstrip()}\n\n{replacement}\n"


def write_task_intake(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    entry_mode: str,
    task_intent: str,
    journal_target: str | None = None,
    constraints: Iterable[object] = (),
    evidence_boundary: Iterable[object] = (),
    trusted_inputs: Iterable[object] = (),
    reference_papers: Iterable[object] = (),
    first_cycle_outputs: Iterable[object] = (),
) -> dict[str, Any]:
    emitted_at = _utc_now()
    slug = _timestamp_slug()
    resolved_study_root = Path(study_root).expanduser().resolve()
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task_id": f"study-task::{study_id}::{slug}",
        "emitted_at": emitted_at,
        "study_id": study_id,
        "study_root": str(resolved_study_root),
        "entry_mode": _non_empty_text(entry_mode) or "full_research",
        "task_intent": _non_empty_text(task_intent) or "",
        "journal_target": _non_empty_text(journal_target),
        "constraints": _normalized_strings(constraints),
        "evidence_boundary": _normalized_strings(evidence_boundary),
        "trusted_inputs": _normalized_strings(trusted_inputs),
        "reference_papers": _normalized_strings(reference_papers),
        "first_cycle_outputs": _normalized_strings(first_cycle_outputs),
        "workspace_locator": {
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "studies_root": str(profile.studies_root),
            "runtime_root": str(profile.runtime_root),
        },
        "runtime_session_contract": {
            "managed_runtime_backend_id": profile.managed_runtime_backend_id,
            "runtime_root": str(profile.runtime_root),
            "hermes_agent_repo_root": str(profile.hermes_agent_repo_root) if profile.hermes_agent_repo_root else None,
            "hermes_home_root": str(profile.hermes_home_root),
        },
        "return_surface_contract": {
            "runtime_supervision_path": str(
                resolved_study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
            ),
            "publication_eval_path": str(
                resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
            ),
            "controller_decision_path": str(
                resolved_study_root / "artifacts" / "controller_decisions" / "latest.json"
            ),
        },
    }
    revision_intake = build_reviewer_revision_intake(payload)
    if revision_intake is not None:
        payload["revision_intake"] = revision_intake
    latest_json_path = latest_task_intake_json_path(study_root=resolved_study_root)
    latest_markdown_path = latest_task_intake_markdown_path(study_root=resolved_study_root)
    timestamped_json_path = _timestamped_task_intake_json_path(study_root=resolved_study_root, slug=slug)
    timestamped_markdown_path = _timestamped_task_intake_markdown_path(study_root=resolved_study_root, slug=slug)
    markdown = render_task_intake_markdown(payload)
    for path, content in (
        (timestamped_json_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"),
        (latest_json_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"),
        (timestamped_markdown_path, markdown + "\n"),
        (latest_markdown_path, markdown + "\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return {
        **payload,
        "artifact_refs": {
            "latest_json": str(latest_json_path),
            "latest_markdown": str(latest_markdown_path),
            "timestamped_json": str(timestamped_json_path),
            "timestamped_markdown": str(timestamped_markdown_path),
        },
    }
