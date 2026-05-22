from __future__ import annotations

from typing import Any


def _compact_record(value: Any, keys: tuple[str, ...]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    compact: dict[str, Any] = {}
    for key in keys:
        if key in value:
            compact[key] = value[key]
    return compact or None


def compact_open_auto_research_projection(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    compact = _compact_record(
        value,
        ("status", "counts", "actions", "delivery_journal_usability_guard", "authority", "refs"),
    )
    if compact is None:
        return None
    actions = value.get("actions")
    if isinstance(actions, list):
        compact["actions"] = [
            {
                key: item[key]
                for key in ("action_id", "status", "surface")
                if key in item
            }
            for item in actions
            if isinstance(item, dict)
        ][:4]
    guard = value.get("delivery_journal_usability_guard")
    if isinstance(guard, dict):
        compact["delivery_journal_usability_guard"] = {
            key: guard[key]
            for key in (
                "real_study_soak_role",
                "delivery_journal_usability",
                "submission_ready_authorized",
                "can_authorize_publication_quality",
                "next_required_action",
                "authority_surfaces",
            )
            if key in guard
        }
    return compact


def compact_open_auto_research_soak_for_mcp(
    payload: dict[str, Any],
    *,
    allow_controller_writes: bool = False,
) -> dict[str, Any]:
    if isinstance(payload.get("capability_results"), dict):
        raw_projection = dict(payload.get("capability_results") or {}).get("open_auto_research_projection")
    else:
        raw_projection = payload.get("open_auto_research_projection")
    projection = compact_open_auto_research_projection(raw_projection) or {}
    compact = {
        key: projection.get(key)
        for key in ("status", "counts", "actions", "delivery_journal_usability_guard", "authority", "refs")
        if key in projection
    }
    authority = dict(compact.get("authority") or {})
    authority["allow_controller_writes"] = bool(allow_controller_writes)
    authority["write_scope"] = (
        "controller-authorized surfaces only"
        if allow_controller_writes
        else "none"
    )
    compact["authority"] = authority

    refs = dict(compact.get("refs") or {})
    progress_refs = payload.get("refs") if isinstance(payload.get("refs"), dict) else {}
    if not progress_refs and isinstance(payload.get("input_refs"), dict):
        progress_refs = dict(payload.get("input_refs") or {})
    for key in (
        "open_auto_research_projection_path",
        "domain_health_diagnostic_report_path",
        "publication_eval_path",
        "controller_decision_path",
    ):
        value = str((progress_refs or {}).get(key) or "").strip()
        if value:
            refs[key] = value
    if refs:
        compact["refs"] = refs

    soak_report_summary = _compact_open_auto_research_soak_report_summary(payload)
    if soak_report_summary is not None:
        compact["soak_report_summary"] = soak_report_summary

    compact["mcp_projection"] = {
        "surface_kind": "mcp_open_auto_research_soak",
        "source_surface_kind": "open_auto_research_projection",
        "compacted": True,
    }
    return compact


def _compact_open_auto_research_soak_report_summary(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    if value.get("surface") == "open_auto_research_soak":
        verdict = value.get("verdict") if isinstance(value.get("verdict"), dict) else {}
        guard = (
            value.get("authority_guard_results")
            if isinstance(value.get("authority_guard_results"), dict)
            else {}
        )
        return {
            "status": verdict.get("status"),
            "mode": verdict.get("mode"),
            "remaining_gaps": list(value.get("remaining_gaps") or [])[:6],
            "forbidden_surface_unchanged": guard.get("forbidden_surface_unchanged"),
            "authorized_writes_only": guard.get("authorized_writes_only"),
        }
    v4_operations = value.get("v4_operations") if isinstance(value.get("v4_operations"), dict) else {}
    health = v4_operations.get("health") if isinstance(v4_operations.get("health"), dict) else {}
    soak_monitor_health = (
        health.get("soak_monitor_health")
        if isinstance(health.get("soak_monitor_health"), dict)
        else None
    )
    return _compact_record(
        soak_monitor_health,
        ("status", "missing_reason", "pending_action_count", "action_ids"),
    )


def render_mcp_open_auto_research_soak_markdown(payload: dict[str, Any]) -> str:
    compact = compact_open_auto_research_soak_for_mcp(
        payload,
        allow_controller_writes=bool(
            dict(payload.get("authority") or {}).get("allow_controller_writes")
        ),
    )
    counts = dict(compact.get("counts") or {})
    lines = [
        "# Open Auto Research Soak",
        "",
        f"- status: `{compact.get('status') or 'unknown'}`",
        f"- counts: ready `{counts.get('ready', 0)}`; "
        f"needs_review `{counts.get('needs_review', 0)}`; "
        f"blocked `{counts.get('blocked', 0)}`; total `{counts.get('total', 0)}`",
    ]
    authority = dict(compact.get("authority") or {})
    if authority:
        lines.append(
            f"- authority: read_only `{authority.get('read_only')}`; "
            f"allow_controller_writes `{authority.get('allow_controller_writes')}`"
        )
    guard = dict(compact.get("delivery_journal_usability_guard") or {})
    if guard:
        next_action = dict(guard.get("next_required_action") or {})
        lines.append(
            f"- delivery journal usability: `{guard.get('delivery_journal_usability') or 'unknown'}`; "
            f"submission_ready_authorized `{bool(guard.get('submission_ready_authorized'))}`"
        )
        if next_action:
            lines.append(
                f"- next quality authority action: `{next_action.get('action_id') or 'unknown_action'}` "
                f"({next_action.get('target_surface') or 'unknown_surface'})"
            )
    soak_report = dict(compact.get("soak_report_summary") or {})
    if soak_report:
        lines.append(
            f"- soak report: `{soak_report.get('status') or 'unknown'}` "
            f"({soak_report.get('missing_reason') or soak_report.get('mode') or 'clear'})"
        )
        remaining_gaps = [
            str(item).strip()
            for item in soak_report.get("remaining_gaps") or []
            if str(item).strip()
        ]
        if remaining_gaps:
            lines.append(f"- remaining gaps: {', '.join(f'`{item}`' for item in remaining_gaps)}")
    for action in compact.get("actions") or []:
        if not isinstance(action, dict):
            continue
        lines.append(
            f"- {action.get('action_id') or 'unknown_action'}: "
            f"`{action.get('status') or 'unknown'}` "
            f"({action.get('surface') or 'unknown_surface'})"
        )
    return "\n".join(lines) + "\n"
