from __future__ import annotations


def quality_floor_refs(*, study_id: str) -> list[str]:
    return [
        "quality-floor-ref:mas/high-quality-medical-manuscript",
        f"quality-floor-ref:mas/{study_id}/publication-ai-reviewer",
    ]


def owner_route_refs(*, study_id: str) -> list[str]:
    return [
        f"owner-route:mas/{study_id}/write",
        f"owner-route:mas/{study_id}/publication-gate",
        f"owner-route-attempt-protocol:mas/{study_id}/v1",
        f"owner-reason-registry:mas/{study_id}",
        f"owner-route-currentness-basis:mas/{study_id}",
    ]


def failure_delta_refs(
    *,
    study_id: str,
    prose_status: str,
    blocker_refs: list[str],
    feedback_ref: str | None,
) -> list[str]:
    refs = [
        f"failure-delta:mas/{study_id}/medical-manuscript-quality:{prose_status}",
        f"evidence-delta:mas/{study_id}/medical-manuscript-quality-routeback",
        f"failure-delta:mas/{study_id}/owner-chain-authority-monotonicity",
        f"failure-delta:mas/{study_id}/quality-repair-writer-handoff-currentness",
        f"failure-delta:mas/{study_id}/publication-work-unit-registry-consistency",
        f"failure-delta:mas/{study_id}/story-surface-delta-or-typed-blocker",
        f"failure-delta:mas/{study_id}/medical-manuscript-quality-floor",
    ]
    refs.extend(f"failure-delta:{ref}" for ref in blocker_refs)
    if feedback_ref is not None:
        refs.append(f"evidence-delta:mas/{study_id}/reviewer-feedback-intake")
    return _unique_refs(refs)


def _unique_refs(refs: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        if ref in seen:
            continue
        unique.append(ref)
        seen.add(ref)
    return unique
