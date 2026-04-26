from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import yaml

from med_autoscience.controllers import autonomy_incidents
from med_autoscience.controllers import autonomy_observability
from med_autoscience.controllers import autonomy_slo
from med_autoscience.controllers import profile_sli
from med_autoscience.controllers import publication_work_units
from med_autoscience.controllers.study_cycle_profiler_current_state import (
    current_state_summary,
    publishability_gate_is_clear,
)
from med_autoscience.controllers.study_cycle_profiler_eta import eta_confidence_band
from med_autoscience.controllers.study_cycle_profiler_package_currentness import (
    package_currentness as resolve_package_currentness,
)
from med_autoscience.controllers.study_cycle_profiler_rendering import (
    render_study_cycle_profile_markdown,
    render_workspace_cycle_profile_markdown,
)
from med_autoscience.profiles import WorkspaceProfile


_TIMESTAMP_FIELDS = ("recorded_at", "generated_at", "emitted_at", "created_at", "updated_at")
_HISTORY_ALIAS_NAMES = frozenset({"latest.json"})


def add_cli_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("study-profile-cycle")
    parser.add_argument("--profile", required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--study-id", type=str)
    source.add_argument("--study-root", type=str)
    parser.add_argument("--since", type=str)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")


def add_workspace_cli_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("workspace-profile-cycles")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--since", type=str)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")


def run_cli_command(
    args: Any,
    *,
    profile_loader: Callable[[str], WorkspaceProfile],
    profile_study_cycle_runner: Callable[..., dict[str, Any]],
) -> int:
    profile = profile_loader(args.profile)
    result = profile_study_cycle_runner(
        profile=profile,
        study_id=args.study_id,
        study_root=Path(args.study_root) if args.study_root else None,
        since=args.since,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_study_cycle_profile_markdown(result), end="")
    return 0


def run_workspace_cli_command(
    args: Any,
    *,
    profile_loader: Callable[[str], WorkspaceProfile],
    profile_workspace_cycles_runner: Callable[..., dict[str, Any]],
) -> int:
    profile = profile_loader(args.profile)
    result = profile_workspace_cycles_runner(profile=profile, since=args.since)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_workspace_cycle_profile_markdown(result), end="")
    return 0


@dataclass(frozen=True)
class _CycleEvent:
    category: str
    path: Path
    timestamp: datetime
    payload: dict[str, Any]


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _parse_timestamp(value: object) -> datetime | None:
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


def _iso(timestamp: datetime | None) -> str | None:
    if timestamp is None:
        return None
    return timestamp.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _read_json_mapping(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return dict(payload)


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return dict(payload)


def _payload_timestamp(payload: Mapping[str, Any], path: Path) -> datetime:
    for field_name in _TIMESTAMP_FIELDS:
        parsed = _parse_timestamp(payload.get(field_name))
        if parsed is not None:
            return parsed
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)


def _iter_json_events(*, category: str, root: Path, since: datetime | None) -> Iterable[_CycleEvent]:
    if not root.exists():
        return
    for path in sorted(root.glob("*.json")):
        if path.name in _HISTORY_ALIAS_NAMES:
            continue
        payload = _read_json_mapping(path)
        if payload is None:
            continue
        timestamp = _payload_timestamp(payload, path)
        if since is not None and timestamp < since:
            continue
        yield _CycleEvent(category=category, path=path.resolve(), timestamp=timestamp, payload=payload)


def _resolve_study_root(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: Path | None,
) -> Path:
    if bool(study_id) == bool(study_root):
        raise ValueError("Specify exactly one of study_id or study_root")
    if study_root is not None:
        return Path(study_root).expanduser().resolve()
    return (profile.studies_root / str(study_id)).expanduser().resolve()


def _resolve_quest_root(*, profile: WorkspaceProfile, study_root: Path, study_id: str) -> tuple[str | None, Path | None]:
    binding = _read_yaml_mapping(study_root / "runtime_binding.yaml")
    quest_id = _non_empty_text(binding.get("quest_id")) or study_id
    runtime_root_text = _non_empty_text(binding.get("runtime_quests_root")) or _non_empty_text(binding.get("runtime_root"))
    runtime_root = Path(runtime_root_text).expanduser().resolve() if runtime_root_text else profile.runtime_root
    quest_root = (runtime_root / quest_id).expanduser().resolve() if quest_id else None
    return quest_id, quest_root


def _category_roots(*, study_root: Path, quest_root: Path | None) -> tuple[tuple[str, Path], ...]:
    roots: list[tuple[str, Path]] = [
        ("task_intake", study_root / "artifacts" / "controller" / "task_intake"),
        ("runtime_supervision", study_root / "artifacts" / "runtime" / "runtime_supervision"),
        ("controller_decision", study_root / "artifacts" / "controller_decisions"),
        ("publication_eval", study_root / "artifacts" / "publication_eval"),
        ("gate_clearing_batch", study_root / "artifacts" / "controller" / "gate_clearing_batch"),
        ("quality_repair_batch", study_root / "artifacts" / "controller" / "quality_repair_batch"),
    ]
    if quest_root is not None:
        roots.extend(
            [
                ("publishability_gate", quest_root / "artifacts" / "reports" / "publishability_gate"),
                ("runtime_watch", quest_root / "artifacts" / "reports" / "runtime_watch"),
            ]
        )
    return tuple(roots)


def _category_windows(events: tuple[_CycleEvent, ...]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[_CycleEvent]] = {}
    for event in events:
        grouped.setdefault(event.category, []).append(event)
    windows: dict[str, dict[str, Any]] = {}
    for category, category_events in sorted(grouped.items()):
        ordered = sorted(category_events, key=lambda event: event.timestamp)
        first = ordered[0].timestamp
        latest = ordered[-1].timestamp
        windows[category] = {
            "event_count": len(ordered),
            "first_at": _iso(first),
            "latest_at": _iso(latest),
            "duration_seconds": int((latest - first).total_seconds()),
            "latest_event_path": str(ordered[-1].path),
        }
    return windows


def _runtime_transition_summary(events: tuple[_CycleEvent, ...]) -> dict[str, Any]:
    runtime_events = sorted(
        (event for event in events if event.category == "runtime_supervision"),
        key=lambda event: event.timestamp,
    )
    health_statuses = [
        str(event.payload.get("health_status") or "").strip()
        for event in runtime_events
        if str(event.payload.get("health_status") or "").strip()
    ]
    reasons = [
        str(event.payload.get("runtime_reason") or "").strip()
        for event in runtime_events
        if str(event.payload.get("runtime_reason") or "").strip()
    ]
    transitions: Counter[str] = Counter()
    for previous, current in zip(health_statuses, health_statuses[1:]):
        if previous != current:
            transitions[f"{previous}->{current}"] += 1
    return {
        "event_count": len(runtime_events),
        "health_status_counts": dict(sorted(Counter(health_statuses).items())),
        "runtime_reason_counts": dict(sorted(Counter(reasons).items())),
        "transition_counts": dict(sorted(transitions.items())),
    }


def _decision_fingerprint(payload: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    controller_actions = payload.get("controller_actions")
    action_types: list[str] = []
    if isinstance(controller_actions, list):
        for action in controller_actions:
            if isinstance(action, Mapping):
                action_type = _non_empty_text(action.get("action_type"))
                if action_type:
                    action_types.append(action_type)
    parts = {
        "decision_type": _non_empty_text(payload.get("decision_type")),
        "route_target": _non_empty_text(payload.get("route_target")),
        "route_key_question": _non_empty_text(payload.get("route_key_question")),
        "reason": _non_empty_text(payload.get("reason")),
        "controller_actions": tuple(sorted(action_types)),
    }
    encoded = json.dumps(parts, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16], parts


def _controller_decision_fingerprints(events: tuple[_CycleEvent, ...]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    examples: dict[str, dict[str, Any]] = {}
    latest_paths: dict[str, str] = {}
    latest_times: dict[str, datetime] = {}
    for event in events:
        if event.category != "controller_decision":
            continue
        fingerprint, parts = _decision_fingerprint(event.payload)
        counts[fingerprint] += 1
        examples.setdefault(fingerprint, parts)
        latest_paths[fingerprint] = str(event.path)
        latest_times[fingerprint] = event.timestamp
    top_repeats = [
        {
            "fingerprint": fingerprint,
            "count": count,
            "decision": examples[fingerprint],
            "latest_event_path": latest_paths[fingerprint],
            "latest_event_at": _iso(latest_times[fingerprint]),
        }
        for fingerprint, count in counts.most_common()
        if count > 1
    ]
    return {
        "unique_fingerprint_count": len(counts),
        "top_repeats": top_repeats,
    }


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := str(item or "").strip())]


def _extract_blockers(payload: Mapping[str, Any] | None) -> list[str]:
    if payload is None:
        return []
    blockers: list[str] = []
    blockers.extend(_text_list(payload.get("blockers")))
    blockers.extend(_text_list(payload.get("medical_publication_surface_blockers")))
    gaps = payload.get("gaps")
    if isinstance(gaps, list):
        for gap in gaps:
            if not isinstance(gap, Mapping):
                continue
            text = _non_empty_text(gap.get("summary")) or _non_empty_text(gap.get("gap_id"))
            if text:
                blockers.append(text)
    return sorted(dict.fromkeys(blockers))


def _latest_current_payloads(*, study_root: Path, quest_root: Path | None) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    publication_eval_latest = _read_json_mapping(study_root / "artifacts" / "publication_eval" / "latest.json")
    publishability_gate_latest = (
        _read_json_mapping(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")
        if quest_root is not None
        else None
    )
    return publication_eval_latest, publishability_gate_latest


def _runtime_watch_wakeup_dedupe_summary(
    *,
    study_root: Path,
    controller_decision_fingerprints: Mapping[str, Any],
) -> dict[str, Any]:
    latest_path = study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json"
    payload = _read_json_mapping(latest_path)
    if payload is None:
        return {"status": "not_observed"}
    recorded_at = _payload_timestamp(payload, latest_path)
    top_repeats = controller_decision_fingerprints.get("top_repeats")
    latest_repeat_at = None
    if isinstance(top_repeats, list):
        latest_repeat_at = _max_dt(
            *(
                _parse_timestamp(item.get("latest_event_at"))
                for item in top_repeats
                if isinstance(item, Mapping)
            )
        )
    outcome = _non_empty_text(payload.get("outcome"))
    dedupe_confirmed = (
        outcome == "skipped_matching_work_unit"
        and (latest_repeat_at is None or recorded_at >= latest_repeat_at)
    )
    work_unit_dispatched = (
        outcome == "dispatched"
        and _non_empty_text(payload.get("work_unit_dispatch_key")) is not None
    )
    return {
        "status": (
            "dedupe_confirmed"
            if dedupe_confirmed
            else "work_unit_dispatched"
            if work_unit_dispatched
            else "not_confirmed"
        ),
        "outcome": outcome,
        "reason": _non_empty_text(payload.get("reason")),
        "recorded_at": _iso(recorded_at),
        "latest_repeated_decision_at": _iso(latest_repeat_at),
        "work_unit_dispatch_key": _non_empty_text(payload.get("work_unit_dispatch_key")),
        "work_unit_fingerprint": _non_empty_text(payload.get("work_unit_fingerprint")),
    }


def _gate_blocker_summary(*, publication_eval_latest: Mapping[str, Any] | None, publishability_gate_latest: Mapping[str, Any] | None) -> dict[str, Any]:
    blocker_sources: list[Mapping[str, Any] | None]
    if publishability_gate_is_clear(publishability_gate_latest):
        blocker_sources = [publishability_gate_latest]
    else:
        blocker_sources = [publication_eval_latest, publishability_gate_latest]
    blockers = sorted(dict.fromkeys(blocker for payload in blocker_sources for blocker in _extract_blockers(payload)))
    actions: list[dict[str, Any]] = []
    for payload in (publication_eval_latest, publishability_gate_latest):
        if not isinstance(payload, Mapping):
            continue
        raw_actions = payload.get("recommended_actions")
        if not isinstance(raw_actions, list):
            continue
        for action in raw_actions:
            if isinstance(action, Mapping):
                actions.append(
                    {
                        "action_type": _non_empty_text(action.get("action_type")),
                        "route_target": _non_empty_text(action.get("route_target")),
                        "reason": _non_empty_text(action.get("reason")),
                    }
                )
    gate_report_for_work_units = dict(publishability_gate_latest or publication_eval_latest or {})
    gate_report_for_work_units["blockers"] = blockers
    work_unit_payload = publication_work_units.derive_publication_work_units(gate_report_for_work_units)
    return {
        "status": "blocked" if blockers else "clear_or_not_materialized",
        "current_blockers": blockers,
        "recommended_actions": actions,
        "actionability_status": work_unit_payload.get("actionability_status"),
        "specificity_questions": work_unit_payload.get("specificity_questions") or [],
        "blocking_work_units": work_unit_payload.get("blocking_work_units") or [],
        "next_work_unit": work_unit_payload.get("next_work_unit"),
    }


def _latest_dt_from_window(category_windows: Mapping[str, Any], category: str) -> datetime | None:
    window = category_windows.get(category)
    if not isinstance(window, Mapping):
        return None
    return _parse_timestamp(window.get("latest_at"))


def _first_dt_from_window(category_windows: Mapping[str, Any], category: str) -> datetime | None:
    window = category_windows.get(category)
    if not isinstance(window, Mapping):
        return None
    return _parse_timestamp(window.get("first_at"))


def _max_dt(*values: datetime | None) -> datetime | None:
    candidates = [value for value in values if value is not None]
    return max(candidates) if candidates else None


def _step_latest_times(
    *,
    category_windows: Mapping[str, Any],
    package_currentness: Mapping[str, Any],
) -> dict[str, str]:
    step_times = {
        "task_intake": _latest_dt_from_window(category_windows, "task_intake"),
        "controller_decision": _latest_dt_from_window(category_windows, "controller_decision"),
        "run_start": _first_dt_from_window(category_windows, "runtime_supervision"),
        "durable_artifact": _max_dt(
            _latest_dt_from_window(category_windows, "gate_clearing_batch"),
            _latest_dt_from_window(category_windows, "quality_repair_batch"),
        ),
        "gate_refresh": _max_dt(
            _latest_dt_from_window(category_windows, "publication_eval"),
            _latest_dt_from_window(category_windows, "publishability_gate"),
        ),
        "package_refresh": _parse_timestamp(package_currentness.get("current_package_latest_mtime")),
    }
    return {
        step: _iso(timestamp)
        for step, timestamp in step_times.items()
        if timestamp is not None and _iso(timestamp) is not None
    }


def _step_timings(step_latest_times: Mapping[str, str]) -> list[dict[str, Any]]:
    parsed_steps = {
        step: parsed
        for step, timestamp in step_latest_times.items()
        if (parsed := _parse_timestamp(timestamp)) is not None
    }
    package_refresh = parsed_steps.get("package_refresh")
    if package_refresh is not None and any(
        step != "package_refresh" and timestamp > package_refresh
        for step, timestamp in parsed_steps.items()
    ):
        parsed_steps.pop("package_refresh", None)
    ordered = sorted(parsed_steps.items(), key=lambda item: item[1])
    timings: list[dict[str, Any]] = []
    for (from_step, from_at), (to_step, to_at) in zip(ordered, ordered[1:]):
        timings.append(
            {
                "from_step": from_step,
                "to_step": to_step,
                "from_at": _iso(from_at),
                "to_at": _iso(to_at),
                "duration_seconds": int((to_at - from_at).total_seconds()),
            }
        )
    return timings


def _bottlenecks(
    *,
    runtime_transition_summary: Mapping[str, Any],
    controller_decision_fingerprints: Mapping[str, Any],
    runtime_watch_wakeup_dedupe_summary: Mapping[str, Any],
    gate_blocker_summary: Mapping[str, Any],
    package_currentness: Mapping[str, Any],
    current_state_summary: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if isinstance(current_state_summary, Mapping) and current_state_summary.get("state") == "manual_finishing":
        return []
    bottlenecks: list[dict[str, Any]] = []
    health_counts = runtime_transition_summary.get("health_status_counts")
    if isinstance(health_counts, Mapping) and any(
        int(health_counts.get(status) or 0) > 0 for status in ("recovering", "degraded", "escalated")
    ):
        bottlenecks.append(
            {
                "bottleneck_id": "runtime_recovery_churn",
                "severity": "high",
                "summary": "Runtime supervision contains recovery or dropout states in the profiling window.",
            }
        )
    top_repeats = controller_decision_fingerprints.get("top_repeats")
    if (
        isinstance(top_repeats, list)
        and top_repeats
        and runtime_watch_wakeup_dedupe_summary.get("status")
        not in {"dedupe_confirmed", "work_unit_dispatched"}
    ):
        bottlenecks.append(
            {
                "bottleneck_id": "repeated_controller_decision",
                "severity": "medium",
                "summary": "The same controller decision fingerprint repeats, indicating dispatch churn.",
            }
        )
    current_blockers = gate_blocker_summary.get("current_blockers")
    if isinstance(current_blockers, list) and current_blockers:
        if gate_blocker_summary.get("actionability_status") == "blocked_by_non_actionable_gate":
            bottlenecks.append(
                {
                    "bottleneck_id": "non_actionable_gate",
                    "severity": "high",
                    "summary": "Publication gate blockers are label-only and need concrete repair targets before dispatch.",
                }
            )
        bottlenecks.append(
            {
                "bottleneck_id": "publication_gate_blocked",
                "severity": "high",
                "summary": "Publication gate blockers remain active and should be narrowed into work units.",
            }
        )
    upstream_scientific_blocked = (
        any(
            "claim" in str(blocker or "").lower()
            or "evidence" in str(blocker or "").lower()
            or "medical_publication_surface" in str(blocker or "").lower()
            for blocker in current_blockers
        )
        if isinstance(current_blockers, list)
        else False
    )
    if package_currentness.get("status") == "stale" and not upstream_scientific_blocked:
        bottlenecks.append(
            {
                "bottleneck_id": "stale_current_package",
                "severity": "medium",
                "summary": "Human-facing current_package is older than controller or paper authority surfaces.",
            }
        )
    return bottlenecks


def _optimization_recommendations(bottlenecks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recommendation_by_bottleneck = {
        "runtime_recovery_churn": {
            "recommendation_id": "stabilize-runtime-observations",
            "priority": "now",
            "summary": "Require consecutive live observations before calling the runtime stable, and flag live-to-recovery flapping.",
            "expected_effect": "Reduces false confidence and makes no-live-session failures actionable at MAS control level.",
        },
        "repeated_controller_decision": {
            "recommendation_id": "dedupe-controller-dispatch",
            "priority": "now",
            "summary": "Fingerprint repeated controller decisions and route the blocker set to a single next work unit.",
            "expected_effect": "Reduces repeated outer-loop dispatch without changing publication quality gates.",
        },
        "publication_gate_blocked": {
            "recommendation_id": "narrow-publication-blockers",
            "priority": "now",
            "summary": "Convert publication blockers into explicit blocking work units with one next work unit.",
            "expected_effect": "Keeps quality gates intact while making the next MAS/MDS action deterministic.",
        },
        "non_actionable_gate": {
            "recommendation_id": "request-gate-specificity",
            "priority": "now",
            "summary": "Ask the gate to identify concrete claim, display, evidence, citation, metric, or package-artifact targets before dispatch.",
            "expected_effect": "Prevents repeated bounded-analysis runs when the gate has not supplied an executable repair object.",
        },
        "stale_current_package": {
            "recommendation_id": "refresh-human-facing-package",
            "priority": "next",
            "summary": "Refresh current_package only after the authority paper and controller surfaces are current.",
            "expected_effect": "Prevents stale human-review packages from becoming a progress ambiguity.",
        },
    }
    recommendations: list[dict[str, Any]] = []
    for bottleneck in bottlenecks:
        bottleneck_id = str(bottleneck.get("bottleneck_id") or "").strip()
        recommendation = recommendation_by_bottleneck.get(bottleneck_id)
        if recommendation is not None:
            recommendations.append(dict(recommendation))
    return recommendations


def _active_study_roots(profile: WorkspaceProfile) -> tuple[Path, ...]:
    if not profile.studies_root.exists():
        return ()
    return tuple(
        study_root
        for study_root in sorted(path for path in profile.studies_root.iterdir() if path.is_dir())
        if (study_root / "study.yaml").exists()
    )


def _cycle_summary(payload: Mapping[str, Any]) -> dict[str, int]:
    decision_fingerprints = payload.get("controller_decision_fingerprints")
    top_repeats = (
        decision_fingerprints.get("top_repeats")
        if isinstance(decision_fingerprints, Mapping)
        else None
    )
    repeated_dispatch_count = 0
    if isinstance(top_repeats, list):
        for item in top_repeats:
            if isinstance(item, Mapping):
                repeated_dispatch_count += max(int(item.get("count") or 0) - 1, 0)
    runtime_summary = payload.get("runtime_transition_summary")
    health_counts = runtime_summary.get("health_status_counts") if isinstance(runtime_summary, Mapping) else None
    recovery_churn_count = 0
    if isinstance(health_counts, Mapping):
        recovery_churn_count = sum(int(health_counts.get(status) or 0) for status in ("recovering", "degraded", "escalated"))
    transition_counts = runtime_summary.get("transition_counts") if isinstance(runtime_summary, Mapping) else None
    flapping_transition_count = sum(int(count or 0) for count in transition_counts.values()) if isinstance(transition_counts, Mapping) else 0
    package_currentness = payload.get("package_currentness")
    package_stale_seconds = (
        int(package_currentness.get("stale_seconds") or 0)
        if isinstance(package_currentness, Mapping)
        else 0
    )
    gate_summary = payload.get("gate_blocker_summary")
    non_actionable_gate_count = (
        1
        if isinstance(gate_summary, Mapping)
        and gate_summary.get("actionability_status") == "blocked_by_non_actionable_gate"
        else 0
    )
    return {
        "repeated_controller_dispatch_count": repeated_dispatch_count,
        "runtime_recovery_churn_count": recovery_churn_count,
        "runtime_flapping_transition_count": flapping_transition_count,
        "package_stale_seconds": package_stale_seconds,
        "non_actionable_gate_count": non_actionable_gate_count,
    }


def _bottleneck_score(*, bottlenecks: object, cycle_summary: Mapping[str, int]) -> int:
    severity_score = {"high": 5, "medium": 3, "low": 1}
    score = 0
    if isinstance(bottlenecks, list):
        for bottleneck in bottlenecks:
            if isinstance(bottleneck, Mapping):
                score += severity_score.get(str(bottleneck.get("severity") or ""), 1)
    score += int(cycle_summary.get("repeated_controller_dispatch_count") or 0)
    score += int(cycle_summary.get("runtime_recovery_churn_count") or 0)
    score += int(cycle_summary.get("runtime_flapping_transition_count") or 0)
    if int(cycle_summary.get("package_stale_seconds") or 0) > 0:
        score += 1
    return score


def _workspace_totals(studies: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    totals = {
        "repeated_controller_dispatch_count": 0,
        "runtime_recovery_churn_count": 0,
        "runtime_flapping_transition_count": 0,
        "package_stale_seconds": 0,
        "non_actionable_gate_count": 0,
    }
    for study in studies:
        summary = study.get("cycle_summary")
        if not isinstance(summary, Mapping):
            continue
        for key in totals:
            totals[key] += int(summary.get(key) or 0)
    return totals


def _optimization_action_units_for_study(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    action_by_bottleneck = {
        "runtime_recovery_churn": {
            "action_type": "probe_runtime_recovery",
            "controller_surface": "runtime_watch",
            "priority": "now",
            "summary": "Run a runtime recovery probe before any blind resume.",
        },
        "repeated_controller_decision": {
            "action_type": "dedupe_controller_dispatch",
            "controller_surface": "runtime_watch",
            "priority": "now",
            "summary": "Suppress repeated controller dispatches for the same blocker fingerprint.",
        },
        "publication_gate_blocked": {
            "action_type": "run_publication_work_unit",
            "controller_surface": "gate_clearing_batch",
            "priority": "now",
            "summary": "Route active publication blockers into the next bounded work unit.",
        },
        "stale_current_package": {
            "action_type": "refresh_current_package_after_settle",
            "controller_surface": "gate_clearing_batch",
            "priority": "next",
            "summary": "Refresh the human-facing current package after authority surfaces settle.",
        },
        "non_actionable_gate": {
            "action_type": "request_gate_specificity",
            "controller_surface": "publication_gate",
            "priority": "now",
            "summary": "Request concrete blocker targets before dispatching another research run.",
        },
    }
    study_id = str(study.get("study_id") or "").strip()
    action_units: list[dict[str, Any]] = []
    bottlenecks = study.get("bottlenecks")
    if not isinstance(bottlenecks, list):
        return action_units
    for index, bottleneck in enumerate(bottlenecks, start=1):
        if not isinstance(bottleneck, Mapping):
            continue
        bottleneck_id = str(bottleneck.get("bottleneck_id") or "").strip()
        action = action_by_bottleneck.get(bottleneck_id)
        if action is None:
            continue
        action_units.append(
            {
                "action_unit_id": f"optimization-action::{study_id}::{bottleneck_id}",
                "study_id": study_id,
                "study_root": study.get("study_root"),
                "quest_id": study.get("quest_id"),
                "source_bottleneck_id": bottleneck_id,
                "source_bottleneck_severity": str(bottleneck.get("severity") or "").strip() or None,
                "schedule_rank": index,
                "apply_mode": "controller_only",
                **action,
            }
        )
    return action_units


def _workspace_scheduler(action_units: list[dict[str, Any]]) -> dict[str, Any]:
    priority_weight = {"now": 0, "next": 1, "later": 2}
    ordered = sorted(
        action_units,
        key=lambda item: (
            priority_weight.get(str(item.get("priority") or ""), 9),
            int(item.get("schedule_rank") or 999),
            str(item.get("study_id") or ""),
            str(item.get("action_unit_id") or ""),
        ),
    )
    return {
        "ready_count": len(ordered),
        "ready_action_unit_ids": [str(item["action_unit_id"]) for item in ordered],
        "ready_action_units": ordered,
    }


def profile_study_cycle(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: Path | None,
    since: str | None = None,
) -> dict[str, Any]:
    resolved_study_root = _resolve_study_root(profile=profile, study_id=study_id, study_root=study_root)
    resolved_study_id = study_id or resolved_study_root.name
    quest_id, quest_root = _resolve_quest_root(profile=profile, study_root=resolved_study_root, study_id=resolved_study_id)
    since_dt = _parse_timestamp(since)
    events = tuple(
        event
        for category, root in _category_roots(study_root=resolved_study_root, quest_root=quest_root)
        for event in _iter_json_events(category=category, root=root, since=since_dt)
    )
    ordered_events = sorted(events, key=lambda event: event.timestamp)
    category_windows = _category_windows(tuple(ordered_events))
    runtime_summary = _runtime_transition_summary(tuple(ordered_events))
    decision_fingerprints = _controller_decision_fingerprints(tuple(ordered_events))
    publication_eval_latest, publishability_gate_latest = _latest_current_payloads(
        study_root=resolved_study_root,
        quest_root=quest_root,
    )
    gate_summary = _gate_blocker_summary(
        publication_eval_latest=publication_eval_latest,
        publishability_gate_latest=publishability_gate_latest,
    )
    current_state = current_state_summary(
        study_root=resolved_study_root,
        publishability_gate_latest=publishability_gate_latest,
    )
    runtime_watch_wakeup_dedupe = _runtime_watch_wakeup_dedupe_summary(
        study_root=resolved_study_root,
        controller_decision_fingerprints=decision_fingerprints,
    )
    package_currentness = resolve_package_currentness(
        study_root=resolved_study_root,
        publication_eval_latest=publication_eval_latest,
        publishability_gate_latest=publishability_gate_latest,
    )
    step_latest_times = _step_latest_times(
        category_windows=category_windows,
        package_currentness=package_currentness,
    )
    bottlenecks = _bottlenecks(
        runtime_transition_summary=runtime_summary,
        controller_decision_fingerprints=decision_fingerprints,
        runtime_watch_wakeup_dedupe_summary=runtime_watch_wakeup_dedupe,
        gate_blocker_summary=gate_summary,
        package_currentness=package_currentness,
        current_state_summary=current_state,
    )
    eta_band = eta_confidence_band(
        runtime_transition_summary=runtime_summary,
        gate_blocker_summary=gate_summary,
        package_currentness=package_currentness,
        current_state_summary=current_state,
    )
    sli_summary = profile_sli.build_sli_summary(
        {
            "runtime_transition_summary": runtime_summary,
            "runtime_watch_wakeup_dedupe_summary": runtime_watch_wakeup_dedupe,
            "gate_blocker_summary": gate_summary,
            "package_currentness": package_currentness,
        }
    )
    autonomy_incident_candidates = autonomy_incidents.incident_candidates_from_profile(
        {
            "study_id": resolved_study_id,
            "bottlenecks": bottlenecks,
            "sli_summary": sli_summary,
            "gate_blocker_summary": gate_summary,
        }
    )
    optimization_recommendations = _optimization_recommendations(bottlenecks)
    autonomy_slo_signals = autonomy_slo.build_autonomy_slo_signals(
        {
            "study_id": resolved_study_id,
            "quest_id": quest_id,
            "runtime_transition_summary": runtime_summary,
            "runtime_watch_wakeup_dedupe_summary": runtime_watch_wakeup_dedupe,
            "gate_blocker_summary": gate_summary,
            "package_currentness": package_currentness,
            "eta_confidence_band": eta_band,
            "sli_summary": sli_summary,
            "bottlenecks": bottlenecks,
            "autonomy_incident_candidates": autonomy_incident_candidates,
            "optimization_recommendations": optimization_recommendations,
        }
    )
    cycle_observability = autonomy_observability.build_cycle_observability(
        {
            "study_id": resolved_study_id,
            "quest_id": quest_id,
            "profiling_window": {
                "since": since,
                "until": _iso(ordered_events[-1].timestamp) if ordered_events else None,
                "event_count": len(ordered_events),
            },
            "category_windows": category_windows,
            "runtime_transition_summary": runtime_summary,
            "controller_decision_fingerprints": decision_fingerprints,
            "gate_blocker_summary": gate_summary,
            "step_timings": _step_timings(step_latest_times),
            "sli_summary": sli_summary,
            "autonomy_slo": autonomy_slo_signals,
        }
    )
    return {
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root) if quest_root is not None else None,
        "profiling_window": {
            "since": since,
            "until": _iso(ordered_events[-1].timestamp) if ordered_events else None,
            "event_count": len(ordered_events),
        },
        "category_windows": category_windows,
        "runtime_transition_summary": runtime_summary,
        "controller_decision_fingerprints": decision_fingerprints,
        "runtime_watch_wakeup_dedupe_summary": runtime_watch_wakeup_dedupe,
        "current_state_summary": current_state,
        "gate_blocker_summary": gate_summary,
        "package_currentness": package_currentness,
        "step_latest_times": step_latest_times,
        "step_timings": _step_timings(step_latest_times),
        "eta_confidence_band": eta_band,
        "sli_summary": sli_summary,
        "bottlenecks": bottlenecks,
        "autonomy_incident_candidates": autonomy_incident_candidates,
        "autonomy_slo": autonomy_slo_signals,
        "cycle_observability": cycle_observability,
        "optimization_recommendations": optimization_recommendations,
    }


def profile_workspace_cycles(*, profile: WorkspaceProfile, since: str | None = None) -> dict[str, Any]:
    studies: list[dict[str, Any]] = []
    for study_root in _active_study_roots(profile):
        study_payload = profile_study_cycle(profile=profile, study_id=None, study_root=study_root, since=since)
        cycle_summary = _cycle_summary(study_payload)
        studies.append(
            {
                "study_id": study_payload["study_id"],
                "study_root": study_payload["study_root"],
                "quest_id": study_payload["quest_id"],
                "profiling_window": study_payload["profiling_window"],
                "cycle_summary": cycle_summary,
                "eta_confidence_band": study_payload["eta_confidence_band"],
                "bottleneck_score": _bottleneck_score(
                    bottlenecks=study_payload.get("bottlenecks"),
                    cycle_summary=cycle_summary,
                ),
                "bottlenecks": study_payload["bottlenecks"],
                "autonomy_slo": study_payload["autonomy_slo"],
                "cycle_observability": study_payload["cycle_observability"],
                "optimization_recommendations": study_payload["optimization_recommendations"],
            }
        )
    studies.sort(key=lambda item: (-int(item["bottleneck_score"]), str(item["study_id"])))
    action_units = [
        action_unit
        for study in studies
        for action_unit in _optimization_action_units_for_study(study)
    ]
    scheduler = _workspace_scheduler(action_units)
    return {
        "profile_name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "profiling_window": {"since": since},
        "study_count": len(studies),
        "workspace_totals": _workspace_totals(studies),
        "optimization_action_units": scheduler["ready_action_units"],
        "workspace_scheduler": scheduler,
        "studies": studies,
    }
