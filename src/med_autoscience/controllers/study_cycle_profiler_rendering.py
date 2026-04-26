from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def render_study_cycle_profile_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        f"# Study Cycle Profile: {payload.get('study_id')}",
        "",
        f"- Study root: `{payload.get('study_root')}`",
        f"- Quest id: `{payload.get('quest_id')}`",
        f"- Quest root: `{payload.get('quest_root')}`",
        f"- Package currentness: {dict(payload.get('package_currentness') or {}).get('status')}",
    ]
    autonomy_slo_payload = dict(payload.get("autonomy_slo") or {})
    long_run_health = dict(autonomy_slo_payload.get("long_run_health") or {})
    incident_loop = dict(autonomy_slo_payload.get("incident_loop") or {})
    if autonomy_slo_payload:
        lines.append(
            "- Autonomy SLO: "
            f"{long_run_health.get('state')} "
            f"(restore: {incident_loop.get('restore_priority')} "
            f"{incident_loop.get('top_action_type')})"
        )
    lines.extend(["", "## Bottlenecks"])
    bottlenecks = payload.get("bottlenecks")
    if isinstance(bottlenecks, list) and bottlenecks:
        for item in bottlenecks:
            if isinstance(item, Mapping):
                lines.append(f"- {item.get('bottleneck_id')}: {item.get('summary')}")
    else:
        lines.append("- none")
    lines.extend(["", "## Recommendations"])
    recommendations = payload.get("optimization_recommendations")
    if isinstance(recommendations, list) and recommendations:
        for item in recommendations:
            if isinstance(item, Mapping):
                lines.append(f"- {item.get('recommendation_id')}: {item.get('summary')}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def render_workspace_cycle_profile_markdown(payload: Mapping[str, Any]) -> str:
    totals = dict(payload.get("workspace_totals") or {})
    lines = [
        f"# Workspace Cycle Profile: {payload.get('profile_name')}",
        "",
        f"- Workspace root: `{payload.get('workspace_root')}`",
        f"- Active studies: {payload.get('study_count')}",
        (
            "- Totals: "
            f"repeated dispatch: {totals.get('repeated_controller_dispatch_count', 0)}, "
            f"runtime recovery churn: {totals.get('runtime_recovery_churn_count', 0)}, "
            f"runtime flapping transitions: {totals.get('runtime_flapping_transition_count', 0)}, "
            f"package stale seconds: {totals.get('package_stale_seconds', 0)}"
        ),
        "",
        "## Studies",
    ]
    studies = payload.get("studies")
    if isinstance(studies, list) and studies:
        for study in studies:
            if not isinstance(study, Mapping):
                continue
            summary = dict(study.get("cycle_summary") or {})
            bottlenecks = study.get("bottlenecks")
            bottleneck_ids = (
                [
                    str(item.get("bottleneck_id"))
                    for item in bottlenecks
                    if isinstance(item, Mapping) and item.get("bottleneck_id")
                ]
                if isinstance(bottlenecks, list)
                else []
            )
            lines.append(
                "- "
                f"{study.get('study_id')} "
                f"(score {study.get('bottleneck_score')}): "
                f"autonomy SLO: {dict(study.get('autonomy_slo') or {}).get('surface', 'unknown')}, "
                f"repeated dispatch: {summary.get('repeated_controller_dispatch_count', 0)}, "
                f"runtime recovery churn: {summary.get('runtime_recovery_churn_count', 0)}, "
                f"runtime flapping transitions: {summary.get('runtime_flapping_transition_count', 0)}, "
                f"package stale seconds: {summary.get('package_stale_seconds', 0)}, "
                f"bottlenecks: {', '.join(bottleneck_ids) if bottleneck_ids else 'none'}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Optimization Action Queue"])
    action_units = payload.get("optimization_action_units")
    if isinstance(action_units, list) and action_units:
        for action in action_units:
            if not isinstance(action, Mapping):
                continue
            lines.append(
                "- "
                f"{action.get('priority')}: "
                f"{action.get('study_id')} "
                f"{action.get('action_type')} "
                f"via {action.get('controller_surface')}"
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)
