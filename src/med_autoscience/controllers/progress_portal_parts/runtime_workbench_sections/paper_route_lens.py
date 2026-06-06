from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .common import (
    dedupe_refs,
    first_mapping,
    first_non_empty_text,
    mapping,
    mapping_list,
    non_empty_text,
    projection_source_refs,
    receipt_refs,
    string_list,
)


def build_paper_route_lens(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
    study_workbench: Mapping[str, Any],
    stage_review: Mapping[str, Any],
    source_refs: list[str],
) -> dict[str, Any]:
    explicit = first_mapping(
        progress.get("paper_route_lens"),
        progress.get("paper_route_projection"),
        runtime.get("paper_route_lens"),
    )
    route_decision_trail = mapping(study_workbench.get("route_decision_trail"))
    route_nodes = mapping_list(route_decision_trail.get("nodes"))
    explicit_attempts = mapping_list(
        explicit.get("route_attempts")
        or explicit.get("attempts")
        or progress.get("route_attempts")
        or progress.get("paper_route_attempts")
    )
    route_attempts = (
        _explicit_route_attempts(explicit_attempts)
        if explicit_attempts
        else _route_attempts_from_nodes(route_nodes)
    )
    current_route = _current_route(
        explicit=explicit,
        route_decision_trail=route_decision_trail,
        route_attempts=route_attempts,
    )
    artifact_refs = _artifact_refs_from_study_workbench(study_workbench)
    reviewer_gate_refs = _reviewer_gate_refs(
        progress=progress,
        stage_review=stage_review,
        explicit=explicit,
    )
    owner_receipt_refs = dedupe_refs(
        [
            *receipt_refs(explicit.get("owner_receipt_refs")),
            *receipt_refs(progress.get("owner_receipt_refs")),
            *receipt_refs(progress.get("domain_owner_receipt_refs")),
            *[
                ref
                for attempt in route_attempts
                for ref in string_list(attempt.get("owner_receipt_refs"))
            ],
        ]
    )
    typed_blocker_refs = dedupe_refs(
        [
            *receipt_refs(explicit.get("typed_blocker_refs")),
            *receipt_refs(explicit.get("blocker_refs")),
            *receipt_refs(progress.get("typed_blocker_refs")),
            *receipt_refs(progress.get("blocker_refs")),
            *receipt_refs(progress.get("stable_typed_blocker_refs")),
            *[
                ref
                for attempt in route_attempts
                for ref in string_list(attempt.get("typed_blocker_refs"))
                + string_list(attempt.get("blocker_refs"))
            ],
        ]
    )
    stage_review_refs = _stage_review_refs(stage_review=stage_review, explicit=explicit)
    next_route_refs = dedupe_refs(
        [
            *receipt_refs(explicit.get("next_route_refs")),
            *receipt_refs(explicit.get("next_refs")),
            *receipt_refs(route_decision_trail.get("source_refs")),
        ]
    )
    next_action_refs = dedupe_refs(
        [
            *receipt_refs(explicit.get("next_action_refs")),
            *receipt_refs(progress.get("next_action_refs")),
            *receipt_refs(progress.get("runtime_owner_route_handoffs")),
        ]
    )
    workspace_refs = _workspace_refs(progress=progress, runtime=runtime, explicit=explicit)
    lens_source_refs = dedupe_refs(
        [
            *source_refs,
            *projection_source_refs(explicit),
            *receipt_refs(route_decision_trail.get("source_refs")),
            *reviewer_gate_refs,
            *artifact_refs,
            *workspace_refs,
            *next_route_refs,
            *next_action_refs,
            *stage_review_refs,
        ]
    )
    missing = []
    if not current_route:
        missing.append("current_route")
    if not route_attempts:
        missing.append("route_attempts")
    if not owner_receipt_refs:
        missing.append("owner_receipt_refs")
    if not typed_blocker_refs:
        missing.append("typed_blocker_refs")
    if not reviewer_gate_refs:
        missing.append("reviewer_gate_refs")
    if not artifact_refs:
        missing.append("artifact_refs")
    if not workspace_refs:
        missing.append("workspace_refs")
    if not next_route_refs and not next_action_refs:
        missing.append("next_route_or_action_refs")
    return {
        "surface_kind": "mas_opl_paper_route_lens",
        "schema_version": 1,
        "mode": "refs_only_paper_route_lens",
        "study_id": study_id,
        "status": "available" if current_route and route_attempts else "pending",
        "body_included": False,
        "manuscript_body_included": False,
        "artifact_body_included": False,
        "claims_publication_ready": False,
        "publication_ready_authorized": False,
        "current_route": current_route,
        "route_attempts": route_attempts,
        "route_attempt_counts": _route_attempt_counts(route_attempts),
        "owner_receipt_refs": owner_receipt_refs,
        "blocker_refs": typed_blocker_refs,
        "typed_blocker_refs": typed_blocker_refs,
        "stage_review_refs": stage_review_refs,
        "reviewer_gate_refs": reviewer_gate_refs,
        "artifact_refs": artifact_refs,
        "source_refs": lens_source_refs,
        "workspace_refs": workspace_refs,
        "next_route_refs": next_route_refs,
        "next_action_refs": next_action_refs,
        "authority": _paper_route_lens_authority(),
        "conditions": {"missing": missing, "stale": [], "conflict": []},
    }


def paper_route_lens_summary(value: object) -> dict[str, Any]:
    lens = mapping(value)
    if not lens:
        return {}
    current_route = _summary_current_route(lens.get("current_route"))
    route_attempt_counts = mapping(lens.get("route_attempt_counts"))
    return {
        "surface_kind": "mas_opl_paper_route_lens_summary",
        "schema_version": 1,
        "mode": "refs_only_paper_route_lens_summary",
        "body_included": False,
        "claims_publication_ready": False,
        "current_route": current_route,
        "route_attempt_counts": _summary_route_attempt_counts(route_attempt_counts),
        "blocker_refs": receipt_refs(lens.get("blocker_refs") or lens.get("typed_blocker_refs")),
        "next_route_refs": receipt_refs(lens.get("next_route_refs")),
        "next_action_refs": receipt_refs(lens.get("next_action_refs")),
        "stage_review_refs": receipt_refs(lens.get("stage_review_refs")),
        "authority": _paper_route_lens_authority(),
    }


def _explicit_route_attempts(attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, attempt in enumerate(attempts, start=1):
        attempt_id = (
            first_non_empty_text(attempt.get("attempt_id"), attempt.get("id"))
            or f"route-attempt-{index}"
        )
        route_id = first_non_empty_text(
            attempt.get("route_id"),
            attempt.get("route"),
            attempt.get("current_route"),
        )
        result.append(
            {
                "attempt_id": attempt_id,
                "route_id": route_id or attempt_id,
                "status": _route_attempt_status(attempt),
                "owner": first_non_empty_text(
                    attempt.get("owner"),
                    attempt.get("next_owner"),
                    attempt.get("route_owner"),
                ),
                "owner_receipt_refs": receipt_refs(attempt.get("owner_receipt_refs")),
                "typed_blocker_refs": dedupe_refs(
                    [
                        *receipt_refs(attempt.get("typed_blocker_refs")),
                        *receipt_refs(attempt.get("blocker_refs")),
                    ]
                ),
                "reviewer_gate_refs": receipt_refs(attempt.get("reviewer_gate_refs")),
                "artifact_refs": receipt_refs(attempt.get("artifact_refs")),
                "source_refs": projection_source_refs(attempt),
                "workspace_refs": receipt_refs(attempt.get("workspace_refs")),
                "next_route_refs": receipt_refs(attempt.get("next_route_refs")),
                "next_action_refs": receipt_refs(attempt.get("next_action_refs")),
                "body_included": False,
            }
        )
    return result


def _route_attempts_from_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for node in nodes:
        route_id = non_empty_text(node.get("route_id"))
        if route_id is None:
            continue
        result.append(
            {
                "attempt_id": route_id,
                "route_id": route_id,
                "status": "blocked" if non_empty_text(node.get("blocker_reason")) else "explored",
                "owner": non_empty_text(node.get("next_owner")),
                "owner_receipt_refs": [],
                "typed_blocker_refs": [],
                "reviewer_gate_refs": [],
                "artifact_refs": [],
                "source_refs": string_list(node.get("source_refs")),
                "workspace_refs": [],
                "next_route_refs": [],
                "next_action_refs": [],
                "body_included": False,
            }
        )
    return result


def _current_route(
    *,
    explicit: Mapping[str, Any],
    route_decision_trail: Mapping[str, Any],
    route_attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    current = mapping(explicit.get("current_route"))
    if current:
        route_id = first_non_empty_text(current.get("route_id"), current.get("id"), current.get("route"))
        return {
            "route_id": route_id,
            "status": _route_attempt_status(current),
            "owner": first_non_empty_text(
                current.get("owner"),
                current.get("next_owner"),
                current.get("route_owner"),
            ),
            "source_refs": projection_source_refs(current),
            "next_route_refs": receipt_refs(current.get("next_route_refs")),
            "next_action_refs": receipt_refs(current.get("next_action_refs")),
        }
    route_id = first_non_empty_text(
        explicit.get("current_route"),
        explicit.get("active_route"),
        route_decision_trail.get("winning_path"),
        route_decision_trail.get("active_path"),
    )
    if route_id is None:
        return {}
    matching_attempt = next(
        (attempt for attempt in route_attempts if non_empty_text(attempt.get("route_id")) == route_id),
        {},
    )
    return {
        "route_id": route_id,
        "status": non_empty_text(matching_attempt.get("status")) or "current",
        "owner": first_non_empty_text(matching_attempt.get("owner"), route_decision_trail.get("next_owner")),
        "source_refs": dedupe_refs(
            [
                *string_list(matching_attempt.get("source_refs")),
                *string_list(route_decision_trail.get("source_refs")),
            ]
        ),
        "next_route_refs": string_list(matching_attempt.get("next_route_refs")),
        "next_action_refs": string_list(matching_attempt.get("next_action_refs")),
    }


def _route_attempt_status(attempt: Mapping[str, Any]) -> str:
    status = first_non_empty_text(attempt.get("status"), attempt.get("outcome"), attempt.get("decision"))
    normalized = (status or "unknown").strip().lower().replace("-", "_")
    if normalized in {"success", "succeeded", "accepted", "completed", "observed"}:
        return "success"
    if normalized in {"failure", "failed", "rejected", "dead_lettered"}:
        return "failure"
    if normalized in {"blocked", "typed_blocker", "blocker"}:
        return "blocked"
    if normalized in {"explored", "superseded", "active", "active_winning", "winning", "current"}:
        return "explored"
    return "unknown"


def _route_attempt_counts(attempts: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"total": len(attempts), "success": 0, "failure": 0, "blocked": 0, "explored": 0, "unknown": 0}
    for attempt in attempts:
        status = non_empty_text(attempt.get("status")) or "unknown"
        counts[status if status in counts else "unknown"] += 1
    return counts


def _summary_current_route(value: object) -> dict[str, Any]:
    if isinstance(value, str):
        route_id = non_empty_text(value)
        return {"route_id": route_id} if route_id is not None else {}
    current = mapping(value)
    route_id = first_non_empty_text(current.get("route_id"), current.get("id"), current.get("route"))
    if route_id is None:
        return {}
    return {"route_id": route_id}


def _summary_route_attempt_counts(value: Mapping[str, Any]) -> dict[str, int]:
    return {
        key: int(raw_value)
        for key, raw_value in value.items()
        if key in {"success", "failure", "blocked"} and isinstance(raw_value, int) and not isinstance(raw_value, bool)
    }


def _stage_review_refs(
    *,
    stage_review: Mapping[str, Any],
    explicit: Mapping[str, Any],
) -> list[str]:
    return dedupe_refs(
        [
            *receipt_refs(explicit.get("stage_review_refs")),
            non_empty_text(stage_review.get("latest_review_page_ref")),
            non_empty_text(stage_review.get("deliverable_index_ref")),
        ]
    )


def _reviewer_gate_refs(
    *,
    progress: Mapping[str, Any],
    stage_review: Mapping[str, Any],
    explicit: Mapping[str, Any],
) -> list[str]:
    refs = [
        *receipt_refs(explicit.get("reviewer_gate_refs")),
        *receipt_refs(explicit.get("reviewer_refs")),
        *receipt_refs(explicit.get("gate_refs")),
        *receipt_refs(progress.get("reviewer_gate_refs")),
        *receipt_refs(progress.get("ai_reviewer_refs")),
        *receipt_refs(progress.get("publication_gate_refs")),
        non_empty_text(mapping(progress.get("refs")).get("publication_eval")),
        non_empty_text(mapping(progress.get("refs")).get("review_ledger")),
        non_empty_text(mapping(progress.get("refs")).get("evidence_ledger")),
        non_empty_text(stage_review.get("latest_review_page_ref")),
        non_empty_text(stage_review.get("deliverable_index_ref")),
    ]
    return dedupe_refs(refs)


def _artifact_refs_from_study_workbench(study_workbench: Mapping[str, Any]) -> list[str]:
    artifact_groups = mapping(study_workbench.get("artifact_groups"))
    refs: list[str] = []
    for group in artifact_groups.values():
        for item in mapping_list(mapping(group).get("items")):
            refs.append(non_empty_text(item.get("ref")))
    return dedupe_refs(refs)


def _workspace_refs(
    *,
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
    explicit: Mapping[str, Any],
) -> list[str]:
    refs = [
        *receipt_refs(explicit.get("workspace_refs")),
        *receipt_refs(progress.get("workspace_refs")),
        *receipt_refs(runtime.get("workspace_refs")),
        non_empty_text(progress.get("study_root")),
        non_empty_text(mapping(progress.get("refs")).get("study_root")),
        non_empty_text(runtime.get("workspace_root")),
    ]
    return dedupe_refs(refs)


def _paper_route_lens_authority() -> dict[str, Any]:
    return {
        "opl_role": "workbench_projection_consumer_only",
        "writes_mas_truth": False,
        "body_free": True,
        "can_authorize_publication_readiness": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_artifact_mutation": False,
        "can_write_memory_body": False,
    }
