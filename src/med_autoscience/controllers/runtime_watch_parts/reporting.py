from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_runtime_family_orchestration as family_orchestration
from med_autoscience.controllers.study_progress_parts.runtime_efficiency import _runtime_efficiency_markdown_lines
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import runtime_watch as runtime_watch_protocol


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_latest_watch_alias(*, report_dir: Path, report: Mapping[str, Any], markdown: str) -> tuple[Path, Path]:
    latest_json = report_dir / "latest.json"
    latest_markdown = report_dir / "latest.md"
    report_dir.mkdir(parents=True, exist_ok=True)
    latest_json.write_text(json.dumps(dict(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest_markdown.write_text(markdown, encoding="utf-8")
    return latest_json, latest_markdown


def _watch_human_gates_for_quest_report(
    *,
    report: Mapping[str, Any],
    scanned_at: str,
) -> list[dict[str, Any]]:
    publication_gate_payload = report.get("controllers", {}).get("publication_gate")
    if not isinstance(publication_gate_payload, Mapping):
        return []
    if str(publication_gate_payload.get("current_required_action") or "").strip() != "human_confirmation_required":
        return []
    evidence_ref = str(publication_gate_payload.get("report_json") or "").strip()
    return [
        family_orchestration.build_family_human_gate(
            gate_id=f"watch-gate-{_stable_gate_id_seed(report)}",
            gate_kind="publication_gate_human_confirmation",
            requested_at=scanned_at,
            request_surface_kind="runtime_watch",
            request_surface_id="runtime_watch",
            evidence_refs=[
                {
                    "ref_kind": "repo_path",
                    "ref": evidence_ref,
                    "label": "publication_gate_report",
                }
            ]
            if evidence_ref
            else [],
            decision_options=["approve", "request_changes", "reject"],
        )
    ]


def _stable_gate_id_seed(report: Mapping[str, Any]) -> str:
    quest_root = str(report.get("quest_root") or "").strip()
    scanned_at = str(report.get("scanned_at") or "").strip()
    return family_orchestration.resolve_active_run_id(quest_root, scanned_at) or "runtime-watch"


def _attach_family_companion_to_quest_report(report: dict[str, Any], *, quest_root: Path) -> None:
    runtime_state = quest_state.load_runtime_state(quest_root)
    active_run_id = family_orchestration.resolve_active_run_id(runtime_state.get("active_run_id"))
    scanned_at = str(report.get("scanned_at") or "").strip() or utc_now()
    human_gates = _watch_human_gates_for_quest_report(report=report, scanned_at=scanned_at)
    controller_refs = []
    for name, payload in (report.get("controllers") or {}).items():
        if not isinstance(payload, Mapping):
            continue
        report_json = str(payload.get("report_json") or "").strip()
        if not report_json:
            continue
        controller_refs.append(
            {
                "ref_kind": "repo_path",
                "ref": report_json,
                "label": f"{name}_report",
            }
        )
    companion = family_orchestration.build_family_orchestration_companion(
        surface_kind="runtime_watch",
        surface_id="runtime_watch/latest.json",
        event_name="runtime_watch.quest_scanned",
        source_surface="runtime_watch",
        session_id=f"runtime-watch:{quest_root.name}",
        program_id=None,
        study_id=quest_root.name,
        quest_id=quest_root.name,
        active_run_id=active_run_id,
        runtime_decision=None,
        runtime_reason=None,
        payload={
            "quest_status": report.get("quest_status"),
            "controller_count": len(report.get("controllers") or {}),
        },
        event_time=scanned_at,
        checkpoint_id=f"runtime-watch-quest:{quest_root.name}:{report.get('quest_status')}",
        checkpoint_label="runtime watch quest scan",
        audit_refs=controller_refs,
        state_refs=[
            {
                "role": "audit",
                "ref_kind": "repo_path",
                "ref": str(quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"),
                "label": "runtime_watch_latest",
            }
        ],
        restoration_evidence=controller_refs,
        action_graph_id="mas_runtime_orchestration",
        node_id="runtime_watch_quest_scan",
        gate_id=(human_gates[0].get("gate_id") if human_gates else None),
        resume_mode="reenter_human_gate" if human_gates else "resume_from_checkpoint",
        resume_handle=f"runtime_watch:{quest_root.name}",
        human_gate_required=bool(human_gates),
        human_gates=human_gates,
    )
    report["family_event_envelope"] = companion["family_event_envelope"]
    report["family_checkpoint_lineage"] = companion["family_checkpoint_lineage"]
    report["family_human_gates"] = companion["family_human_gates"]


def _attach_family_companion_to_runtime_report(report: dict[str, Any], *, runtime_root: Path) -> None:
    scanned_at = str(report.get("scanned_at") or "").strip() or utc_now()
    human_gates: list[dict[str, Any]] = []
    for quest_report in report.get("reports") or []:
        if not isinstance(quest_report, Mapping):
            continue
        for gate in quest_report.get("family_human_gates") or []:
            if isinstance(gate, Mapping):
                human_gates.append(dict(gate))
    companion = family_orchestration.build_family_orchestration_companion(
        surface_kind="runtime_watch",
        surface_id="runtime_watch/runtime_tick",
        event_name="runtime_watch.runtime_scanned",
        source_surface="runtime_watch",
        session_id=f"runtime-watch:{runtime_root}",
        program_id=None,
        study_id=None,
        quest_id=None,
        active_run_id=None,
        runtime_decision=None,
        runtime_reason=None,
        payload={
            "scanned_quest_count": len(report.get("scanned_quests") or []),
            "managed_study_action_count": len(report.get("managed_study_actions") or []),
            "managed_study_auto_recovery_count": len(report.get("managed_study_auto_recoveries") or []),
        },
        event_time=scanned_at,
        checkpoint_id=f"runtime-watch-runtime:{runtime_root.name}:{len(report.get('scanned_quests') or [])}",
        checkpoint_label="runtime watch runtime scan",
        audit_refs=[
            {
                "ref_kind": "repo_path",
                "ref": str(item.get("latest_report_json") or item.get("report_json") or "").strip(),
                "label": "runtime_watch_quest_report",
            }
            for item in (report.get("reports") or [])
            if isinstance(item, Mapping) and str(item.get("latest_report_json") or item.get("report_json") or "").strip()
        ],
        state_refs=[
            {
                "role": "workspace",
                "ref_kind": "repo_path",
                "ref": str(runtime_root),
                "label": "runtime_root",
            }
        ],
        action_graph_id="mas_runtime_orchestration",
        node_id="runtime_watch_runtime_scan",
        gate_id=(human_gates[0].get("gate_id") if human_gates else None),
        resume_mode="reenter_human_gate" if human_gates else "resume_from_checkpoint",
        resume_handle=f"runtime_watch:{runtime_root}",
        human_gate_required=bool(human_gates),
        human_gates=human_gates,
    )
    report["family_event_envelope"] = companion["family_event_envelope"]
    report["family_checkpoint_lineage"] = companion["family_checkpoint_lineage"]
    report["family_human_gates"] = companion["family_human_gates"]


def render_watch_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Runtime Watch Report",
        "",
        f"- scanned_at: `{report['scanned_at']}`",
        f"- quest_root: `{report['quest_root']}`",
        f"- quest_status: `{report['quest_status']}`",
        "",
    ]
    runtime_efficiency = report.get("runtime_efficiency")
    if isinstance(runtime_efficiency, dict) and runtime_efficiency:
        lines.extend(
            [
                "## Runtime Efficiency",
                "",
                *_runtime_efficiency_markdown_lines(runtime_efficiency),
                "",
            ]
        )
    lines.extend(
        [
            "## Controllers",
            "",
        ]
    )
    for name, item in (report.get("controllers") or {}).items():
        lines.extend(
            [
                f"### {name}",
                "",
                f"- status: `{item.get('status')}`",
                f"- action: `{item.get('action')}`",
                f"- blockers: `{', '.join(item.get('blockers') or ['none'])}`",
                f"- advisories: `{', '.join(item.get('advisories') or ['none'])}`",
                f"- report_json: `{item.get('report_json')}`",
                f"- report_markdown: `{item.get('report_markdown')}`",
                f"- suppression_reason: `{item.get('suppression_reason') or 'none'}`",
                "",
            ]
        )
        if name == "publication_gate" and item.get("supervisor_phase"):
            lines.extend(
                [
                    "#### Publication Supervisor",
                    "",
                    f"- supervisor_phase: `{item.get('supervisor_phase')}`",
                    f"- phase_owner: `{item.get('phase_owner')}`",
                    f"- upstream_scientific_anchor_ready: `{str(item.get('upstream_scientific_anchor_ready')).lower()}`",
                    f"- bundle_tasks_downstream_only: `{str(item.get('bundle_tasks_downstream_only')).lower()}`",
                    f"- current_required_action: `{item.get('current_required_action')}`",
                    f"- deferred_downstream_actions: `{', '.join(item.get('deferred_downstream_actions') or ['none'])}`",
                    f"- controller_stage_note: `{item.get('controller_stage_note')}`",
                    "",
                ]
            )
    outer_loop_dispatch = dict(report.get("managed_study_outer_loop_dispatch") or {})
    if outer_loop_dispatch:
        lines.extend(
            [
                "## Managed Study Outer-Loop Dispatch",
                "",
                f"- study_id: `{outer_loop_dispatch.get('study_id') or 'none'}`",
                f"- decision_type: `{outer_loop_dispatch.get('decision_type') or 'none'}`",
                f"- route_target: `{outer_loop_dispatch.get('route_target') or 'none'}`",
                f"- route_key_question: `{outer_loop_dispatch.get('route_key_question') or 'none'}`",
                f"- controller_action_type: `{outer_loop_dispatch.get('controller_action_type') or 'none'}`",
                f"- study_decision_ref: `{outer_loop_dispatch.get('study_decision_ref') or 'none'}`",
                f"- dispatch_status: `{outer_loop_dispatch.get('dispatch_status') or 'none'}`",
                f"- source: `{outer_loop_dispatch.get('source') or 'none'}`",
                "",
            ]
        )
    no_op_suppressions = [
        dict(item)
        for item in (report.get("managed_study_no_op_suppressions") or [])
        if isinstance(item, Mapping)
    ]
    if no_op_suppressions:
        lines.extend(["## Managed Study No-Op Suppression", ""])
        for item in no_op_suppressions[:5]:
            next_work_unit = item.get("next_work_unit") if isinstance(item.get("next_work_unit"), Mapping) else {}
            lines.extend(
                [
                    f"- study_id: `{item.get('study_id') or 'none'}`",
                    f"  outcome: `{item.get('outcome') or 'none'}`",
                    f"  blocker_fingerprint: `{item.get('work_unit_fingerprint') or 'none'}`",
                    f"  next_work_unit: `{next_work_unit.get('unit_id') or 'none'}`",
                    f"  operator_summary: `{item.get('operator_summary') or 'none'}`",
                ]
            )
        lines.append("")
    return "\n".join(lines)


def write_watch_report(quest_root: Path, report: dict[str, Any]) -> tuple[Path, Path, Path, Path]:
    markdown = render_watch_markdown(report)
    json_path, md_path = runtime_watch_protocol.write_watch_report(
        quest_root=quest_root,
        report=report,
        markdown=markdown,
    )
    latest_json, latest_markdown = _write_latest_watch_alias(
        report_dir=json_path.parent,
        report=report,
        markdown=markdown,
    )
    return json_path, md_path, latest_json, latest_markdown
