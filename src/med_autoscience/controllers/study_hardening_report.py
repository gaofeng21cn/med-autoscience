from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


_RUNTIME_ACTION_MODES = frozenset(
    {
        "runtime_reconcile_then_resume",
        "platform_repair_required",
        "inspect_before_resume",
        "external_fix_required",
        "provider_backoff_and_recheck",
        "wait_for_user_or_explicit_resume",
    }
)
_HUMAN_ETA_CLASSES = frozenset({"human_admin_missing", "manual_finishing"})
_QUALITY_ETA_CLASSES = frozenset({"claim_evidence", "non_actionable_gate"})
_DELIVERY_ETA_CLASSES = frozenset({"delivery_only"})
_QUALITY_BOTTLENECKS = frozenset({"publication_gate_blocked", "non_actionable_gate"})


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _bool(value: object) -> bool:
    return bool(value) if isinstance(value, bool) else False


def _parse_timestamp(value: object) -> datetime | None:
    text = _text(value)
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


def _elapsed_seconds(start: object, end: object) -> int | None:
    started_at = _parse_timestamp(start)
    ended_at = _parse_timestamp(end)
    if started_at is None or ended_at is None:
        return None
    return max(int((ended_at - started_at).total_seconds()), 0)


def _ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _runtime_failure(profile_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    autonomy_slo = _mapping(profile_payload.get("autonomy_slo"))
    nested = _mapping(autonomy_slo.get("runtime_failure_classification"))
    if nested:
        return nested
    return _mapping(profile_payload.get("runtime_failure_classification"))


def _bottleneck_ids(profile_payload: Mapping[str, Any]) -> set[str]:
    return {
        bottleneck_id
        for item in _list(profile_payload.get("bottlenecks"))
        if isinstance(item, Mapping)
        if (bottleneck_id := _text(item.get("bottleneck_id"))) is not None
    }


def _current_blockers(profile_payload: Mapping[str, Any]) -> list[str]:
    gate_summary = _mapping(profile_payload.get("gate_blocker_summary"))
    return [
        blocker
        for item in _list(gate_summary.get("current_blockers"))
        if (blocker := _text(item)) is not None
    ]


def _gate_assessment(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime_failure = _runtime_failure(profile_payload)
    eta_band = _mapping(profile_payload.get("eta_confidence_band"))
    package_currentness = _mapping(profile_payload.get("package_currentness"))
    bottleneck_ids = _bottleneck_ids(profile_payload)
    blockers = _current_blockers(profile_payload)
    eta_classification = _text(eta_band.get("classification"))
    action_mode = _text(runtime_failure.get("action_mode"))
    blocker_class = _text(runtime_failure.get("blocker_class")) or ""
    external_blocker = _bool(runtime_failure.get("external_blocker"))
    requires_human_gate = _bool(runtime_failure.get("requires_human_gate"))
    runtime_gate = (
        "runtime_recovery_churn" in bottleneck_ids
        or eta_classification == "runtime_recovering"
        or action_mode in _RUNTIME_ACTION_MODES
        or "runtime" in blocker_class
        or "platform_protocol" in blocker_class
    )
    provider_gate = (
        external_blocker
        or blocker_class.startswith("external_provider")
        or action_mode in {"external_fix_required", "provider_backoff_and_recheck"}
    )
    human_gate = (
        requires_human_gate
        or eta_classification in _HUMAN_ETA_CLASSES
        or action_mode == "wait_for_user_or_explicit_resume"
    )
    quality_gate = (
        bool(blockers)
        or bool(bottleneck_ids & _QUALITY_BOTTLENECKS)
        or eta_classification in _QUALITY_ETA_CLASSES
    )
    delivery_gate = (
        package_currentness.get("status") in {"stale", "missing"}
        or eta_classification in _DELIVERY_ETA_CLASSES
    )
    primary_gate = "monitor"
    for gate_name, active in (
        ("provider_gate", provider_gate),
        ("human_gate", human_gate),
        ("runtime_gate", runtime_gate),
        ("quality_gate", quality_gate),
        ("delivery_gate", delivery_gate),
    ):
        if active:
            primary_gate = gate_name
            break
    return {
        "runtime_gate": runtime_gate,
        "provider_gate": provider_gate,
        "human_gate": human_gate,
        "quality_gate": quality_gate,
        "delivery_gate": delivery_gate,
        "primary_gate": primary_gate,
    }


def _controller_events(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    fingerprints = _mapping(profile_payload.get("controller_decision_fingerprints"))
    top_repeats = [
        dict(item)
        for item in _list(fingerprints.get("top_repeats"))
        if isinstance(item, Mapping)
    ]
    repeated_dispatch_count = sum(max(_int(item.get("count")) - 1, 0) for item in top_repeats)
    dedupe_summary = dict(_mapping(profile_payload.get("runtime_watch_wakeup_dedupe_summary")))
    dedupe_status = _text(dedupe_summary.get("status"))
    duplicate_dispatch_active = bool(top_repeats) and dedupe_status not in {
        "dedupe_confirmed",
        "work_unit_dispatched",
    }
    return {
        "repeated_dispatch_count": repeated_dispatch_count,
        "duplicate_dispatch_active": duplicate_dispatch_active,
        "top_repeated_decision": top_repeats[0] if top_repeats else None,
        "runtime_watch_wakeup_dedupe_summary": dedupe_summary,
    }


def _timing(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    profiling_window = _mapping(profile_payload.get("profiling_window"))
    window_seconds = _elapsed_seconds(profiling_window.get("since"), profiling_window.get("until"))
    if window_seconds is None:
        category_windows = _mapping(profile_payload.get("category_windows"))
        first_times = [
            parsed
            for item in category_windows.values()
            if isinstance(item, Mapping)
            if (parsed := _parse_timestamp(item.get("first_at"))) is not None
        ]
        latest_times = [
            parsed
            for item in category_windows.values()
            if isinstance(item, Mapping)
            if (parsed := _parse_timestamp(item.get("latest_at"))) is not None
        ]
        if first_times and latest_times:
            window_seconds = max(int((max(latest_times) - min(first_times)).total_seconds()), 0)
    step_timings = [
        dict(item)
        for item in _list(profile_payload.get("step_timings"))
        if isinstance(item, Mapping)
    ]
    slowest_step = max(step_timings, key=lambda item: _int(item.get("duration_seconds")), default=None)
    package_currentness = _mapping(profile_payload.get("package_currentness"))
    return {
        "window_seconds": window_seconds,
        "event_count": _int(profiling_window.get("event_count")),
        "slowest_step": slowest_step,
        "step_timings": step_timings,
        "package_stale_seconds": _int(package_currentness.get("stale_seconds")),
        "mtime": {
            "authority_latest_mtime": _text(package_currentness.get("authority_latest_mtime")),
            "current_package_latest_mtime": _text(
                package_currentness.get("current_package_latest_mtime")
            ),
            "control_surface_latest_mtime": _text(
                package_currentness.get("control_surface_latest_mtime")
            ),
        },
        "category_windows": dict(_mapping(profile_payload.get("category_windows"))),
    }


def _stuck_at(*, gate_assessment: Mapping[str, Any], controller_events: Mapping[str, Any]) -> str:
    primary_gate = _text(gate_assessment.get("primary_gate"))
    if primary_gate == "provider_gate":
        return "external_provider"
    if primary_gate == "human_gate":
        return "human_or_admin_gate"
    if primary_gate == "runtime_gate":
        return "runtime_watch"
    if primary_gate == "quality_gate":
        return "publication_gate"
    if _bool(controller_events.get("duplicate_dispatch_active")):
        return "controller_dispatch"
    if primary_gate == "delivery_gate":
        return "current_package"
    return "no_active_blocker_visible"


def _where_stuck(
    *,
    profile_payload: Mapping[str, Any],
    gate_assessment: Mapping[str, Any],
    controller_events: Mapping[str, Any],
) -> dict[str, Any]:
    stuck_at = _stuck_at(gate_assessment=gate_assessment, controller_events=controller_events)
    bottleneck_ids = sorted(_bottleneck_ids(profile_payload))
    blockers = _current_blockers(profile_payload)
    next_work_unit = _mapping(_mapping(profile_payload.get("gate_blocker_summary")).get("next_work_unit"))
    return {
        "stuck_at": stuck_at,
        "primary_gate": gate_assessment.get("primary_gate"),
        "bottleneck_ids": bottleneck_ids,
        "current_blockers": blockers,
        "next_work_unit_id": _text(next_work_unit.get("unit_id")),
    }


def _regression_manifest(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    replay_case = _mapping(profile_payload.get("study_soak_replay_case"))
    cases = [dict(replay_case)] if replay_case else []
    required_truth_surfaces = sorted(
        {
            surface
            for case in cases
            for item in _list(case.get("required_truth_surfaces"))
            if (surface := _text(item)) is not None
        }
    )
    must_assert = _ordered_unique(
        assertion
        for case in cases
        for item in _list(case.get("must_assert"))
        if (assertion := _text(item)) is not None
    )
    return {
        "surface": "study_hardening_regression_manifest",
        "schema_version": 1,
        "generated_from": "profile_study_cycle_payload",
        "case_count": len(cases),
        "cases": cases,
        "required_truth_surfaces": required_truth_surfaces,
        "must_assert": must_assert,
        "gate_relaxation_allowed": any(_bool(case.get("gate_relaxation_allowed")) for case in cases),
        "edits_paper_body": any(_bool(case.get("edits_paper_body")) for case in cases),
    }


def build_study_hardening_report(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    gate_assessment = _gate_assessment(profile_payload)
    controller_events = _controller_events(profile_payload)
    timing = _timing(profile_payload)
    where_stuck = _where_stuck(
        profile_payload=profile_payload,
        gate_assessment=gate_assessment,
        controller_events=controller_events,
    )
    eta_band = dict(_mapping(profile_payload.get("eta_confidence_band")))
    return {
        "surface": "study_hardening_report",
        "schema_version": 1,
        "study_id": _text(profile_payload.get("study_id")),
        "quest_id": _text(profile_payload.get("quest_id")),
        "answers": {
            "where_stuck": where_stuck,
            "timing": timing,
            "eta": eta_band,
            "gate_assessment": gate_assessment,
            "controller_events": controller_events,
        },
        "evidence": {
            "profiling_window": dict(_mapping(profile_payload.get("profiling_window"))),
            "category_windows": dict(_mapping(profile_payload.get("category_windows"))),
            "runtime_transition_summary": dict(
                _mapping(profile_payload.get("runtime_transition_summary"))
            ),
            "gate_blocker_summary": dict(_mapping(profile_payload.get("gate_blocker_summary"))),
            "package_currentness": dict(_mapping(profile_payload.get("package_currentness"))),
        },
        "regression_manifest": _regression_manifest(profile_payload),
    }


def render_study_hardening_report_markdown(report: Mapping[str, Any]) -> str:
    answers = _mapping(report.get("answers"))
    where_stuck = _mapping(answers.get("where_stuck"))
    timing = _mapping(answers.get("timing"))
    eta = _mapping(answers.get("eta"))
    controller_events = _mapping(answers.get("controller_events"))
    regression_manifest = _mapping(report.get("regression_manifest"))
    lines = [
        f"# Study Hardening Report: {report.get('study_id')}",
        "",
        f"- Quest id: `{report.get('quest_id')}`",
        (
            "- 卡点: "
            f"{where_stuck.get('stuck_at')} / {where_stuck.get('primary_gate')}"
        ),
        (
            "- 耗时: "
            f"window {timing.get('window_seconds')}s, "
            f"package stale {timing.get('package_stale_seconds')}s"
        ),
        (
            "- ETA: "
            f"{eta.get('classification')} "
            f"({eta.get('confidence') or 'unknown'})"
        ),
        (
            "- Controller events: "
            f"repeated dispatch {controller_events.get('repeated_dispatch_count', 0)}"
        ),
        f"- Regression manifest: {regression_manifest.get('case_count', 0)} case",
    ]
    blockers = where_stuck.get("current_blockers")
    if isinstance(blockers, list) and blockers:
        lines.append(f"- Current blockers: {', '.join(str(item) for item in blockers)}")
    lines.append("")
    return "\n".join(lines)
