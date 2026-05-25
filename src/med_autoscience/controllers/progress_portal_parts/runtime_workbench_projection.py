from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .stage_review import runtime_stage_review_summary


PROGRESS_PORTAL_PAYLOAD_REF = "artifacts/runtime/progress_portal/latest.json"
PROGRESS_PORTAL_STUDY_PAYLOAD_REF_TEMPLATE = "artifacts/runtime/progress_portal/studies/{study_id}/latest.json"


def build_runtime_workbench_projection(
    *,
    workspace_root: Path,
    profile_ref: str | Path | None,
    profile_name: str,
    generated_at: str,
    study_id: str,
    workspace_overview_mode: bool,
    page_scope: str,
    workspace_study_rows: list[dict[str, Any]],
    user_visible: Mapping[str, Any],
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
    freshness: Mapping[str, Any],
    source_refs: list[str],
    conditions: Mapping[str, Any],
    study_workbench: Mapping[str, Any],
) -> dict[str, Any]:
    studies = [
        _workbench_study_row(
            row,
            fallback_freshness=freshness,
            fallback_source_refs=source_refs,
            selected_study_id=study_id,
        )
        for row in workspace_study_rows
        if _non_empty_text(row.get("study_id")) is not None
    ]
    if not workspace_overview_mode:
        selected_study = _selected_workbench_study(
            study_id=study_id,
            user_visible=user_visible,
            progress=progress,
            runtime=runtime,
            freshness=freshness,
            source_refs=source_refs,
            study_workbench=study_workbench,
        )
        replaced = False
        for index, item in enumerate(studies):
            if item["study_id"] == study_id:
                studies[index] = selected_study
                replaced = True
                break
        if not replaced:
            studies.append(selected_study)
    return {
        "surface_kind": "mas_opl_runtime_workbench_projection",
        "schema_version": 1,
        "generated_at": generated_at,
        "workspace": {
            "workspace_root": str(workspace_root),
            "profile_ref": str(profile_ref) if profile_ref is not None else None,
            "profile_name": profile_name,
        },
        "studies": studies,
        "terminal": _workbench_terminal_projection(
            study_id=study_id,
            active_run_id=_opl_active_run_id(study_workbench=study_workbench, progress=progress, runtime=runtime),
        ),
        "authority": {
            "opl_role": "projection_consumer_and_action_transport_only",
            "mas_truth_owner": True,
            "page_scope": page_scope,
            "forbidden_writes": [
                "study_truth",
                "publication_judgment",
                "quality_verdict",
                "runtime_authority",
                "artifact_authority",
                "runtime_state",
                "runtime_sqlite",
                "terminal_commands",
                "current_package",
                "evidence_ledger",
                "review_ledger",
            ],
        },
        "conditions": {
            "missing": _string_list(conditions.get("missing")),
            "stale": _string_list(conditions.get("stale")),
            "conflict": _string_list(conditions.get("conflict")),
        },
    }


def _workbench_study_row(
    row: Mapping[str, Any],
    *,
    fallback_freshness: Mapping[str, Any],
    fallback_source_refs: list[str],
    selected_study_id: str,
) -> dict[str, Any]:
    study_id = _non_empty_text(row.get("study_id")) or "unknown-study"
    freshness = {
        "status": _non_empty_text(row.get("progress_freshness_status")) or _non_empty_text(fallback_freshness.get("status")),
        "summary": _non_empty_text(row.get("progress_freshness_summary")) or _non_empty_text(fallback_freshness.get("summary")),
        "latest_event_at": _non_empty_text(row.get("latest_event_at")) or _non_empty_text(fallback_freshness.get("latest_event_at")),
    }
    active_run_id = _non_empty_text(row.get("active_run_id"))
    worker_state = _first_non_empty_text(
        row.get("worker_state"),
        row.get("runtime_health_status"),
        row.get("supervisor_tick_status"),
    )
    return {
        "study_id": study_id,
        "display_title": _non_empty_text(row.get("display_title")) or _non_empty_text(row.get("title")) or study_id,
        "macro_state": _first_non_empty_text(
            row.get("macro_state"),
            row.get("state_label"),
            row.get("current_stage"),
            row.get("paper_stage"),
        ) or "unknown",
        "user_next": _first_non_empty_text(row.get("user_next"), row.get("next_system_action"), row.get("operator_focus")),
        "current_stage": _non_empty_text(row.get("current_stage")),
        "active_run_id": active_run_id,
        "worker_state": worker_state,
        "last_seen_at": _first_non_empty_text(row.get("last_seen_at"), freshness["latest_event_at"]),
        "freshness": freshness,
        "blocker_summary": _first_non_empty_text(row.get("blocker_summary"), row.get("progress_freshness_summary")),
        "next_action_summary": _first_non_empty_text(row.get("next_action_summary"), row.get("next_system_action"), row.get("operator_focus")),
        "source_refs": fallback_source_refs[:12],
        "links": _workbench_links(study_id, selected=study_id == selected_study_id),
        "actions": _workbench_actions(),
    }


def _selected_workbench_study(
    *,
    study_id: str,
    user_visible: Mapping[str, Any],
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
    freshness: Mapping[str, Any],
    source_refs: list[str],
    study_workbench: Mapping[str, Any],
) -> dict[str, Any]:
    runtime_projection = _mapping(study_workbench.get("runtime"))
    active_run_id = _opl_active_run_id(study_workbench=study_workbench, progress=progress, runtime=runtime)
    stage_review = runtime_stage_review_summary(_mapping(study_workbench.get("stage_review_index")))
    paper_route_lens = _paper_route_lens(
        study_id=study_id,
        progress=progress,
        runtime=runtime,
        study_workbench=study_workbench,
        stage_review=stage_review,
        source_refs=source_refs,
    )
    reference_projection = _reference_projection(
        progress=progress,
        runtime=runtime,
        freshness=freshness,
        stage_review=stage_review,
        paper_route_lens=paper_route_lens,
    )
    return {
        "study_id": study_id,
        "display_title": study_id,
        "macro_state": _first_non_empty_text(user_visible.get("state_label"), user_visible.get("writer_state")) or "unknown",
        "user_next": _non_empty_text(user_visible.get("user_next")) or _non_empty_text(user_visible.get("next_system_action")),
        "current_stage": _non_empty_text(user_visible.get("current_stage")),
        "active_run_id": active_run_id,
        "worker_state": _first_non_empty_text(
            runtime_projection.get("health_status"),
            runtime.get("health_status"),
        ),
        "last_seen_at": _first_non_empty_text(freshness.get("latest_event_at")),
        "freshness": dict(freshness),
        "blocker_summary": "; ".join(_string_list(user_visible.get("current_blockers"))) or None,
        "next_action_summary": _non_empty_text(user_visible.get("next_system_action")),
        "source_refs": source_refs[:12],
        "links": _workbench_links(study_id, selected=True, artifact_refs=_stage_review_artifact_refs(stage_review)),
        "actions": _workbench_actions(),
        "workbench": dict(study_workbench),
        "stage_review": stage_review,
        "paper_route_lens": paper_route_lens,
        "reference_projection": reference_projection,
    }


def _reference_projection(
    *,
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
    freshness: Mapping[str, Any],
    stage_review: Mapping[str, Any],
    paper_route_lens: Mapping[str, Any],
) -> dict[str, Any]:
    provider_attempt = _provider_attempt_lane(progress)
    guarded_apply = _guarded_apply_lane(progress)
    memory_receipt = _memory_receipt_lane(progress)
    freshness_lane = _freshness_lane(freshness=freshness, stage_review=stage_review)
    runtime_owner_route_handoffs = _runtime_owner_route_handoff_lane(progress=progress, runtime=runtime)
    lanes = {
        "provider_attempt": provider_attempt,
        "guarded_apply": guarded_apply,
        "stage_review_index": _stage_review_lane(stage_review),
        "memory_receipt": memory_receipt,
        "freshness": freshness_lane,
        "runtime_owner_route_handoffs": runtime_owner_route_handoffs,
        "paper_route_lens": dict(paper_route_lens),
    }
    return {
        "surface_kind": "mas_opl_workbench_reference_projection",
        "schema_version": 1,
        "mode": "read_only_drilldown",
        "lanes": lanes,
        "source_refs": _dedupe_refs(
            ref
            for lane in lanes.values()
            for ref in _string_list(_mapping(lane).get("source_refs"))
        ),
        "typed_blockers": [
            blocker
            for lane in lanes.values()
            for blocker in [_mapping(_mapping(lane).get("typed_blocker"))]
            if blocker
        ],
        "pending_lanes": [
            lane_id
            for lane_id, lane in lanes.items()
            if _non_empty_text(_mapping(lane).get("status")) == "pending"
        ],
        "authority": _reference_authority(),
    }


def _paper_route_lens(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
    study_workbench: Mapping[str, Any],
    stage_review: Mapping[str, Any],
    source_refs: list[str],
) -> dict[str, Any]:
    explicit = _first_mapping(
        progress.get("paper_route_lens"),
        progress.get("paper_route_projection"),
        runtime.get("paper_route_lens"),
    )
    route_decision_trail = _mapping(study_workbench.get("route_decision_trail"))
    route_nodes = _mapping_list(route_decision_trail.get("nodes"))
    explicit_attempts = _mapping_list(
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
    reviewer_gate_refs = _reviewer_gate_refs(progress=progress, stage_review=stage_review, explicit=explicit)
    owner_receipt_refs = _dedupe_refs(
        [
            *_receipt_refs(explicit.get("owner_receipt_refs")),
            *_receipt_refs(progress.get("owner_receipt_refs")),
            *_receipt_refs(progress.get("domain_owner_receipt_refs")),
            *[
                ref
                for attempt in route_attempts
                for ref in _string_list(attempt.get("owner_receipt_refs"))
            ],
        ]
    )
    typed_blocker_refs = _dedupe_refs(
        [
            *_receipt_refs(explicit.get("typed_blocker_refs")),
            *_receipt_refs(progress.get("typed_blocker_refs")),
            *_receipt_refs(progress.get("stable_typed_blocker_refs")),
            *[
                ref
                for attempt in route_attempts
                for ref in _string_list(attempt.get("typed_blocker_refs"))
            ],
        ]
    )
    next_route_refs = _dedupe_refs(
        [
            *_receipt_refs(explicit.get("next_route_refs")),
            *_receipt_refs(explicit.get("next_refs")),
            *_receipt_refs(route_decision_trail.get("source_refs")),
        ]
    )
    next_action_refs = _dedupe_refs(
        [
            *_receipt_refs(explicit.get("next_action_refs")),
            *_receipt_refs(progress.get("next_action_refs")),
            *_receipt_refs(progress.get("runtime_owner_route_handoffs")),
        ]
    )
    workspace_refs = _workspace_refs(progress=progress, runtime=runtime, explicit=explicit)
    lens_source_refs = _dedupe_refs(
        [
            *source_refs,
            *_projection_source_refs(explicit),
            *_receipt_refs(route_decision_trail.get("source_refs")),
            *reviewer_gate_refs,
            *artifact_refs,
            *workspace_refs,
            *next_route_refs,
            *next_action_refs,
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
        "typed_blocker_refs": typed_blocker_refs,
        "reviewer_gate_refs": reviewer_gate_refs,
        "artifact_refs": artifact_refs,
        "source_refs": lens_source_refs,
        "workspace_refs": workspace_refs,
        "next_route_refs": next_route_refs,
        "next_action_refs": next_action_refs,
        "authority": {
            "opl_role": "workbench_projection_consumer_only",
            "writes_mas_truth": False,
            "body_free": True,
            "can_authorize_publication_readiness": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_artifact_mutation": False,
            "can_write_memory_body": False,
        },
        "conditions": {"missing": missing, "stale": [], "conflict": []},
    }


def _explicit_route_attempts(attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, attempt in enumerate(attempts, start=1):
        attempt_id = _first_non_empty_text(attempt.get("attempt_id"), attempt.get("id")) or f"route-attempt-{index}"
        route_id = _first_non_empty_text(attempt.get("route_id"), attempt.get("route"), attempt.get("current_route"))
        result.append(
            {
                "attempt_id": attempt_id,
                "route_id": route_id or attempt_id,
                "status": _route_attempt_status(attempt),
                "owner": _first_non_empty_text(attempt.get("owner"), attempt.get("next_owner"), attempt.get("route_owner")),
                "owner_receipt_refs": _receipt_refs(attempt.get("owner_receipt_refs")),
                "typed_blocker_refs": _receipt_refs(attempt.get("typed_blocker_refs")),
                "reviewer_gate_refs": _receipt_refs(attempt.get("reviewer_gate_refs")),
                "artifact_refs": _receipt_refs(attempt.get("artifact_refs")),
                "source_refs": _projection_source_refs(attempt),
                "workspace_refs": _receipt_refs(attempt.get("workspace_refs")),
                "next_route_refs": _receipt_refs(attempt.get("next_route_refs")),
                "next_action_refs": _receipt_refs(attempt.get("next_action_refs")),
                "body_included": False,
            }
        )
    return result


def _route_attempts_from_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for node in nodes:
        route_id = _non_empty_text(node.get("route_id"))
        if route_id is None:
            continue
        result.append(
            {
                "attempt_id": route_id,
                "route_id": route_id,
                "status": "blocked" if _non_empty_text(node.get("blocker_reason")) else "explored",
                "owner": _non_empty_text(node.get("next_owner")),
                "owner_receipt_refs": [],
                "typed_blocker_refs": [],
                "reviewer_gate_refs": [],
                "artifact_refs": [],
                "source_refs": _string_list(node.get("source_refs")),
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
    current = _mapping(explicit.get("current_route"))
    if current:
        route_id = _first_non_empty_text(current.get("route_id"), current.get("id"), current.get("route"))
        return {
            "route_id": route_id,
            "status": _route_attempt_status(current),
            "owner": _first_non_empty_text(current.get("owner"), current.get("next_owner"), current.get("route_owner")),
            "source_refs": _projection_source_refs(current),
            "next_route_refs": _receipt_refs(current.get("next_route_refs")),
            "next_action_refs": _receipt_refs(current.get("next_action_refs")),
        }
    route_id = _first_non_empty_text(
        explicit.get("current_route"),
        explicit.get("active_route"),
        route_decision_trail.get("winning_path"),
        route_decision_trail.get("active_path"),
    )
    if route_id is None:
        return {}
    matching_attempt = next(
        (attempt for attempt in route_attempts if _non_empty_text(attempt.get("route_id")) == route_id),
        {},
    )
    return {
        "route_id": route_id,
        "status": _non_empty_text(matching_attempt.get("status")) or "current",
        "owner": _first_non_empty_text(matching_attempt.get("owner"), route_decision_trail.get("next_owner")),
        "source_refs": _dedupe_refs(
            [
                *_string_list(matching_attempt.get("source_refs")),
                *_string_list(route_decision_trail.get("source_refs")),
            ]
        ),
        "next_route_refs": _string_list(matching_attempt.get("next_route_refs")),
        "next_action_refs": _string_list(matching_attempt.get("next_action_refs")),
    }


def _route_attempt_status(attempt: Mapping[str, Any]) -> str:
    status = _first_non_empty_text(attempt.get("status"), attempt.get("outcome"), attempt.get("decision"))
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
        status = _non_empty_text(attempt.get("status")) or "unknown"
        counts[status if status in counts else "unknown"] += 1
    return counts


def _reviewer_gate_refs(
    *,
    progress: Mapping[str, Any],
    stage_review: Mapping[str, Any],
    explicit: Mapping[str, Any],
) -> list[str]:
    refs = [
        *_receipt_refs(explicit.get("reviewer_gate_refs")),
        *_receipt_refs(explicit.get("reviewer_refs")),
        *_receipt_refs(explicit.get("gate_refs")),
        *_receipt_refs(progress.get("reviewer_gate_refs")),
        *_receipt_refs(progress.get("ai_reviewer_refs")),
        *_receipt_refs(progress.get("publication_gate_refs")),
        _non_empty_text(_mapping(progress.get("refs")).get("publication_eval")),
        _non_empty_text(_mapping(progress.get("refs")).get("review_ledger")),
        _non_empty_text(_mapping(progress.get("refs")).get("evidence_ledger")),
        _non_empty_text(stage_review.get("latest_review_page_ref")),
        _non_empty_text(stage_review.get("deliverable_index_ref")),
    ]
    return _dedupe_refs(refs)


def _artifact_refs_from_study_workbench(study_workbench: Mapping[str, Any]) -> list[str]:
    artifact_groups = _mapping(study_workbench.get("artifact_groups"))
    refs: list[str] = []
    for group in artifact_groups.values():
        for item in _mapping_list(_mapping(group).get("items")):
            refs.append(_non_empty_text(item.get("ref")))
    return _dedupe_refs(refs)


def _workspace_refs(
    *,
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
    explicit: Mapping[str, Any],
) -> list[str]:
    refs = [
        *_receipt_refs(explicit.get("workspace_refs")),
        *_receipt_refs(progress.get("workspace_refs")),
        *_receipt_refs(runtime.get("workspace_refs")),
        _non_empty_text(progress.get("study_root")),
        _non_empty_text(_mapping(progress.get("refs")).get("study_root")),
        _non_empty_text(runtime.get("workspace_root")),
    ]
    return _dedupe_refs(refs)


def _provider_attempt_lane(progress: Mapping[str, Any]) -> dict[str, Any]:
    attempt = _first_mapping(
        progress.get("provider_attempt_projection"),
        progress.get("provider_attempt"),
        progress.get("provider_attempt_receipt"),
        progress.get("provider_hosted_attempt"),
    )
    attempt_id = _first_non_empty_text(
        attempt.get("attempt_id"),
        attempt.get("provider_attempt_id"),
        progress.get("provider_attempt_id"),
    )
    source_refs = _projection_source_refs(attempt)
    if attempt_id is None:
        return _typed_blocker_lane(
            lane_id="provider_attempt",
            blocker_id="provider_attempt_proof_missing",
            summary="缺少真实 provider attempt proof；OPL App 只能显示 pending lane。",
            required_surface="provider_attempt_receipt",
            source_refs=source_refs,
        )
    return {
        "lane_id": "provider_attempt",
        "status": "observed",
        "attempt_id": attempt_id,
        "attempt_owner": _first_non_empty_text(attempt.get("attempt_owner"), attempt.get("owner")),
        "provider_attempt_is_truth": bool(attempt.get("provider_attempt_is_truth")) is True,
        "provider_attempt_wrote_workspace": bool(attempt.get("provider_attempt_wrote_workspace")) is True,
        "source_refs": source_refs,
        "authority": _lane_authority(),
    }


def _guarded_apply_lane(progress: Mapping[str, Any]) -> dict[str, Any]:
    proof = _first_mapping(
        progress.get("guarded_apply_projection"),
        progress.get("guarded_apply_proof"),
        progress.get("provider_hosted_guarded_apply_receipt"),
        progress.get("real_paper_autonomy_guarded_apply_proof"),
    )
    guarded_status = _first_non_empty_text(proof.get("guarded_apply_status"), proof.get("status"))
    receipt_refs = _dedupe_refs(
        [
            *_projection_source_refs(proof),
            *_receipt_refs(proof.get("guarded_apply_receipts")),
            *_receipt_refs(proof.get("guarded_apply_receipt_refs")),
        ]
    )
    if guarded_status is None and not receipt_refs:
        return _pending_lane(
            lane_id="guarded_apply",
            summary="等待 MAS owner guarded apply proof；provider attempt 不能证明 paper progress 已推进。",
            required_surface="real_paper_autonomy_guarded_apply_proof",
        )
    performed = bool(_mapping(proof.get("summary")).get("guarded_apply_performed")) or bool(
        proof.get("guarded_apply_performed")
    )
    return {
        "lane_id": "guarded_apply",
        "status": "observed" if performed else "typed_blocker",
        "guarded_apply_status": guarded_status,
        "guarded_apply_performed": performed,
        "paper_closure_authorized": False,
        "source_refs": receipt_refs,
        "typed_blocker": None
        if performed
        else {
            "blocker_id": "mas_owner_apply_receipt_missing",
            "required_owner_surface": "MAS owner guarded apply receipt",
        },
        "authority": _lane_authority(),
    }


def _stage_review_lane(stage_review: Mapping[str, Any]) -> dict[str, Any]:
    refs = _dedupe_refs(
        [
            _non_empty_text(stage_review.get("latest_review_page_ref")),
            _non_empty_text(stage_review.get("deliverable_index_ref")),
        ]
    )
    status = _non_empty_text(stage_review.get("status")) or "missing"
    if status != "available":
        return _pending_lane(
            lane_id="stage_review_index",
            summary="缺少显式 Stage Review Page / Deliverable Index；不能从文件名或 stage 文案推断。",
            required_surface="mas_progress_portal_stage_review_index",
            source_refs=refs,
        )
    return {
        "lane_id": "stage_review_index",
        "status": "observed",
        "current_stage": _non_empty_text(stage_review.get("current_stage")),
        "latest_review_page_ref": _non_empty_text(stage_review.get("latest_review_page_ref")),
        "deliverable_index_ref": _non_empty_text(stage_review.get("deliverable_index_ref")),
        "freshness_state": _non_empty_text(stage_review.get("freshness_state")),
        "paper_asset_delta_types": _string_list(stage_review.get("paper_asset_delta_types")),
        "claim_impact_state": _non_empty_text(stage_review.get("claim_impact_state")),
        "human_review_state": _non_empty_text(stage_review.get("human_review_state")),
        "next_owner": _non_empty_text(stage_review.get("next_owner")),
        "blockers": _string_list(stage_review.get("blockers")),
        "continue_state": _non_empty_text(stage_review.get("continue_state")),
        "source_refs": refs,
        "can_authorize_publication_readiness": False,
        "can_authorize_quality_verdict": False,
        "can_mark_publication_ready": False,
        "authority": _lane_authority(),
    }


def _memory_receipt_lane(progress: Mapping[str, Any]) -> dict[str, Any]:
    receipt = _first_mapping(
        progress.get("memory_receipt_projection"),
        progress.get("publication_route_memory_final_proof"),
        progress.get("paper_soak_memory_apply_proof"),
    )
    refs = _dedupe_refs(
        [
            *_projection_source_refs(receipt),
            *_receipt_refs(receipt.get("writeback_receipt_refs")),
            *_receipt_refs(receipt.get("mas_router_receipt_refs")),
            *_receipt_refs(receipt.get("workspace_writeback_receipt_refs")),
            *_receipt_refs(receipt.get("opl_aion_readonly_receipt_refs")),
        ]
    )
    if not refs:
        return _pending_lane(
            lane_id="memory_receipt",
            summary="缺少 domain-owned memory receipt locator；OPL 不能写 memory body。",
            required_surface="memory_write_router_receipt",
        )
    return {
        "lane_id": "memory_receipt",
        "status": "observed",
        "receipt_status": _first_non_empty_text(receipt.get("status"), receipt.get("receipt_status")),
        "writeback_receipt_refs": refs,
        "source_refs": refs,
        "can_write_memory_body": False,
        "authority": _lane_authority(),
    }


def _freshness_lane(*, freshness: Mapping[str, Any], stage_review: Mapping[str, Any]) -> dict[str, Any]:
    portal_status = _non_empty_text(freshness.get("status")) or "missing"
    refs = _dedupe_refs(
        [
            _non_empty_text(stage_review.get("latest_review_page_ref")),
            _non_empty_text(stage_review.get("deliverable_index_ref")),
        ]
    )
    return {
        "lane_id": "freshness",
        "status": "observed" if portal_status not in {"missing", "unknown"} else "pending",
        "portal_freshness_status": portal_status,
        "portal_freshness_summary": _non_empty_text(freshness.get("summary")),
        "latest_event_at": _non_empty_text(freshness.get("latest_event_at")),
        "stage_review_freshness_state": _non_empty_text(stage_review.get("freshness_state")),
        "source_refs": refs,
        "can_authorize_publication_readiness": False,
        "authority": _lane_authority(),
    }


def _runtime_owner_route_handoff_lane(
    *,
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> dict[str, Any]:
    handoffs = _first_non_empty_list(
        progress.get("runtime_owner_route_handoffs"),
        progress.get("owner_route_handoffs"),
        progress.get("owner_route_refs"),
        runtime.get("owner_route_handoffs"),
    )
    refs = _receipt_refs(handoffs)
    if not refs:
        return _pending_lane(
            lane_id="runtime_owner_route_handoffs",
            summary="尚未观察到 domain-handler runtime owner route handoff；UI 只能显示 OPL owner-route handoff refs。",
            required_surface="mas_runtime_owner_route_handoff",
            source_refs=["artifacts/supervision/owner_route_handoff"],
        )
    return {
        "lane_id": "runtime_owner_route_handoffs",
        "status": "observed",
        "handoff_refs": refs,
        "source_refs": refs,
        "direct_execution_intents": [],
        "can_execute_without_mas_receipt": False,
        "owner_route_handoff_policy": _owner_route_handoff_policy(),
        "authority": _lane_authority(),
    }


def _typed_blocker_lane(
    *,
    lane_id: str,
    blocker_id: str,
    summary: str,
    required_surface: str,
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "lane_id": lane_id,
        "status": "typed_blocker",
        "summary": summary,
        "source_refs": list(source_refs or []),
        "typed_blocker": {
            "blocker_id": blocker_id,
            "required_surface": required_surface,
            "opl_can_override": False,
        },
        "authority": _lane_authority(),
    }


def _pending_lane(
    *,
    lane_id: str,
    summary: str,
    required_surface: str,
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "lane_id": lane_id,
        "status": "pending",
        "summary": summary,
        "source_refs": list(source_refs or []),
        "pending_lane": {
            "required_surface": required_surface,
            "display_only": True,
        },
        "authority": _lane_authority(),
    }


def _owner_route_handoff_policy() -> dict[str, Any]:
    return {
        "policy": "safe_action_requires_owner_receipt",
        "required_receipt_surface": "mas_runtime_owner_route_handoff",
        "action_transport_owner": "OPL provider transport",
        "domain_owner": "MedAutoScience",
        "can_execute_without_mas_receipt": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_artifact_mutation": False,
    }


def _reference_authority() -> dict[str, Any]:
    return {
        "opl_role": "read_model_drilldown_consumer_only",
        "writes_mas_truth": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_quality_verdict": False,
        "can_apply_guarded_mutation": False,
        "can_write_memory_body": False,
    }


def _lane_authority() -> dict[str, Any]:
    return {
        "writes_authority_surface": False,
        "display_and_drilldown_only": True,
        "can_authorize_publication_readiness": False,
        "can_authorize_quality_verdict": False,
    }


def _workbench_links(
    study_id: str,
    *,
    selected: bool,
    artifact_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "progress_payload_ref": (
            PROGRESS_PORTAL_PAYLOAD_REF
            if selected
            else PROGRESS_PORTAL_STUDY_PAYLOAD_REF_TEMPLATE.format(study_id=study_id)
        ),
        "artifact_refs": list(artifact_refs or []),
    }


def _stage_review_artifact_refs(stage_review: Mapping[str, Any]) -> list[str]:
    refs = [
        _non_empty_text(stage_review.get("latest_review_page_ref")),
        _non_empty_text(stage_review.get("deliverable_index_ref")),
        *_string_list(stage_review.get("source_map_refs")),
        *_string_list(stage_review.get("page_block_anchor_refs")),
        *_string_list(stage_review.get("figure_near_claim_refs")),
        _non_empty_text(stage_review.get("paper_presentation_note_ref")),
        *_string_list(stage_review.get("paper_presentation_evidence_spine_refs")),
    ]
    result: list[str] = []
    for ref in refs:
        if ref is not None and ref not in result:
            result.append(ref)
    return result


def _workbench_actions() -> dict[str, dict[str, Any]]:
    return {
        action: {
            "allowed": False,
            "owner": "one-person-lab",
            "endpoint_ref": None,
            "idempotency_required": True,
            "confirmation_required": action in {"stop", "reconcile_apply"},
        }
        for action in ("pause", "resume", "stop", "reconcile_dry_run", "reconcile_apply")
    }


def _opl_active_run_id(
    *,
    study_workbench: Mapping[str, Any],
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> str | None:
    runtime_projection = _mapping(study_workbench.get("runtime"))
    progress_opl_control = _mapping(progress.get("opl_current_control_state")) or _mapping(progress.get("current_control_state"))
    runtime_opl_control = _mapping(runtime.get("opl_current_control_state")) or _mapping(runtime.get("current_control_state"))
    return (
        _non_empty_text(runtime_projection.get("active_run_id"))
        or _non_empty_text(runtime_opl_control.get("active_run_id"))
        or _non_empty_text(progress_opl_control.get("active_run_id"))
        or _non_empty_text(runtime.get("active_run_id"))
    )


def _workbench_terminal_projection(
    *,
    study_id: str,
    active_run_id: str | None,
) -> dict[str, Any]:
    return {
        "mode": "external_control_plane_required",
        "reason": "terminal_and_log_projection_owned_by_opl_current_control_state",
        "study_id": study_id,
        "active_run_id": active_run_id,
        "endpoints": None,
        "token_required": True,
        "lease_required": True,
        "audit_ref": "OPL current_control_state projection",
    }


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _first_non_empty_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _first_mapping(*values: object) -> dict[str, Any]:
    for value in values:
        if isinstance(value, Mapping) and value:
            return dict(value)
    return {}


def _first_non_empty_list(*values: object) -> list[Any]:
    for value in values:
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
            items = list(value)
            if items:
                return items
    return []


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _projection_source_refs(value: Mapping[str, Any]) -> list[str]:
    return _dedupe_refs(
        [
            *_string_list(value.get("source_refs")),
            *_string_list(value.get("evidence_refs")),
            _non_empty_text(value.get("source_ref")),
            _non_empty_text(value.get("receipt_ref")),
            _non_empty_text(value.get("audit_ref")),
            _non_empty_text(value.get("ref")),
        ]
    )


def _receipt_refs(value: object) -> list[str]:
    refs: list[str] = []
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if isinstance(value, Mapping):
        refs.extend(_projection_source_refs(value))
        for key in ("refs", "receipt_refs", "writeback_receipt_refs"):
            refs.extend(_receipt_refs(value.get(key)))
    elif isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        for item in value:
            refs.extend(_receipt_refs(item))
    return _dedupe_refs(refs)


def _dedupe_refs(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = _non_empty_text(value)
        if text is not None and text not in result:
            result.append(text)
    return result
