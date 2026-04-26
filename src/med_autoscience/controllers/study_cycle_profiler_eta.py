from __future__ import annotations

from typing import Any, Mapping


def _has_human_admin_marker(blocker: str) -> bool:
    lowered = blocker.lower()
    if "伦理" in blocker or "作者" in blocker:
        return True
    tokens = {
        token
        for token in lowered.replace("-", "_").replace("/", "_").split("_")
        if token
    }
    return bool(tokens & {"author", "authors", "affiliation", "affiliations", "metadata", "human", "admin"})


def eta_confidence_band(
    *,
    runtime_transition_summary: Mapping[str, Any],
    gate_blocker_summary: Mapping[str, Any],
    package_currentness: Mapping[str, Any],
    current_state_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(current_state_summary, Mapping) and current_state_summary.get("state") == "manual_finishing":
        return {
            "classification": "manual_finishing",
            "label": "manual finishing",
            "confidence": "blocked",
            "min_seconds": None,
            "max_seconds": None,
            "reason": "The study is parked at a milestone package/manual-finishing state; historical runtime churn in the window should not drive an autonomous completion ETA.",
        }
    health_counts = runtime_transition_summary.get("health_status_counts")
    if isinstance(health_counts, Mapping) and any(
        int(health_counts.get(status) or 0) > 0 for status in ("recovering", "degraded", "escalated")
    ):
        return {
            "classification": "runtime_recovering",
            "label": "runtime recovering",
            "confidence": "medium",
            "min_seconds": 1800,
            "max_seconds": 3600,
            "reason": "Runtime needs a live confirmation before downstream controller dispatch is reliable.",
        }
    if gate_blocker_summary.get("actionability_status") == "blocked_by_non_actionable_gate":
        return {
            "classification": "non_actionable_gate",
            "label": "non-actionable gate",
            "confidence": "blocked",
            "min_seconds": None,
            "max_seconds": None,
            "reason": "Gate blockers are label-only and must be narrowed to concrete claim, display, evidence, citation, metric, or package-artifact targets before automated execution.",
        }
    blockers = {
        str(item or "").strip()
        for item in (gate_blocker_summary.get("current_blockers") or [])
        if str(item or "").strip()
    }
    if any(_has_human_admin_marker(blocker) for blocker in blockers):
        return {
            "classification": "human_admin_missing",
            "label": "human/admin missing",
            "confidence": "blocked",
            "min_seconds": None,
            "max_seconds": None,
            "reason": "Remaining blockers require external human or administrative information before MAS/MDS can finish autonomously.",
        }
    delivery_markers = ("submission", "package", "delivery", "current_package", "bundle")
    if blockers and all(any(marker in blocker for marker in delivery_markers) for blocker in blockers):
        return {
            "classification": "delivery_only",
            "label": "delivery-only",
            "confidence": "high",
            "min_seconds": 1800,
            "max_seconds": 7200,
            "reason": "Only submission/package delivery surfaces remain; quality gates stay intact while package refresh runs.",
        }
    if any("claim" in blocker or "evidence" in blocker for blocker in blockers):
        return {
            "classification": "claim_evidence",
            "label": "claim-evidence",
            "confidence": "medium",
            "min_seconds": 7200,
            "max_seconds": 21600,
            "reason": "Claim/evidence alignment still needs bounded scientific repair before delivery-only closeout.",
        }
    if package_currentness.get("status") in {"stale", "missing"}:
        return {
            "classification": "delivery_only",
            "label": "delivery-only",
            "confidence": "high",
            "min_seconds": 1800,
            "max_seconds": 7200,
            "reason": "The human-facing package is stale or missing after authority surfaces moved.",
        }
    return {
        "classification": "delivery_only",
        "label": "delivery-only",
        "confidence": "medium",
        "min_seconds": 1800,
        "max_seconds": 7200,
        "reason": "No higher-risk runtime, claim-evidence, non-actionable, or human/admin blocker is visible.",
    }
