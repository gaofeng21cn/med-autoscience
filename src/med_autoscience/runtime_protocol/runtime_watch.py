from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from med_autoscience.adapters import report_store


def load_watch_state(quest_root: Path) -> dict[str, Any]:
    return report_store.load_watch_state(quest_root)


def save_watch_state(quest_root: Path, payload: Mapping[str, Any]) -> None:
    report_store.save_watch_state(quest_root, payload)


def write_watch_report(*, quest_root: Path, report: Mapping[str, Any], markdown: str) -> tuple[Path, Path]:
    return report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="runtime_watch",
        timestamp=report["scanned_at"],
        report=report,
        markdown=markdown,
    )


def plan_controller_intervention(
    *,
    previous_controller_state: Mapping[str, Any],
    dry_run_result: Mapping[str, Any],
    fingerprint: str,
    apply: bool,
    scanned_at: str,
    intervention_statuses: Sequence[str],
) -> dict[str, Any]:
    status = dry_run_result.get("status")
    suppression_reason = dry_run_result.get("suppression_reason")
    action = "clear"
    should_apply = False
    if status in intervention_statuses:
        seen_before = previous_controller_state.get("last_applied_fingerprint") == fingerprint
        should_apply = apply and not seen_before
        if should_apply:
            action = "applied"
            suppression_reason = None
        else:
            action = "suppressed"
            suppression_reason = "duplicate_fingerprint" if apply else "apply_disabled"

    controller_state = {
        "last_seen_fingerprint": fingerprint,
        "last_applied_fingerprint": fingerprint if action == "applied" else previous_controller_state.get("last_applied_fingerprint"),
        "last_applied_at": scanned_at if action == "applied" else previous_controller_state.get("last_applied_at"),
        "last_status": status,
        "last_suppression_reason": suppression_reason,
    }

    return {
        "action": action,
        "should_apply": should_apply,
        "suppression_reason": suppression_reason,
        "controller_state": controller_state,
    }
