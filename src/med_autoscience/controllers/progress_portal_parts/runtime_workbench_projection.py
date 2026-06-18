from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .progress_first_operator import build_progress_first_operator_projection
from .runtime_workbench_sections import build_paper_route_lens, paper_route_lens_summary
from .runtime_workbench_sections.common import (
    dedupe_refs as _dedupe_refs,
    first_mapping as _first_mapping,
    first_non_empty_list as _first_non_empty_list,
    first_non_empty_text as _first_non_empty_text,
    mapping as _mapping,
    non_empty_text as _non_empty_text,
    projection_source_refs as _projection_source_refs,
    receipt_refs as _receipt_refs,
    string_list as _string_list,
)
from .stage_review import runtime_stage_review_summary


PROGRESS_PORTAL_PAYLOAD_REF = "runtime/artifacts/progress_portal/latest.json"
PROGRESS_PORTAL_STUDY_PAYLOAD_REF_TEMPLATE = "runtime/artifacts/progress_portal/studies/{study_id}/latest.json"
STAGE_KERNEL_TRUTH_SOURCE = "stage_kernel_projection"
REQUIRED_CROSS_DOMAIN_SOAK_LANES = ("MAS", "MAG", "OMA", "RCA")


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
        "projection_boundary": _runtime_workbench_projection_boundary(),
        "authority": {
            "opl_role": "workbench_readback_projection_consumer_only",
            "mas_truth_owner": True,
            "page_scope": page_scope,
            "writes_mas_truth": False,
            "claims_publication_ready": False,
            "current_truth_source": STAGE_KERNEL_TRUTH_SOURCE,
            "can_transport_operator_action": False,
            "can_emit_runtime_command": False,
            "operator_intent_refs_are_inert": True,
            "external_opl_workbench_shell_required": True,
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
    result = {
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
        "next_action_summary_role": "read_only_drilldown_summary",
        "next_action_summary_is_controller_action": False,
        "next_action_summary_can_generate_action": False,
        "next_action_summary_requires_opl_current_control_readback": True,
        "source_refs": fallback_source_refs[:12],
        "links_role": "read_only_drilldown_refs",
        "links_can_execute": False,
        "links": _workbench_links(study_id, selected=study_id == selected_study_id),
        "actions_role": "operator_intent_projection_refs",
        "actions_can_execute": False,
        "actions_deprecated": True,
        "actions_authority": False,
        "actions_are_operator_intent_refs": True,
        "operator_intent_projection": _workbench_actions(),
    }
    paper_route_lens = paper_route_lens_summary(row.get("paper_route_lens"))
    if paper_route_lens:
        result["paper_route_lens"] = paper_route_lens
    return result


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
    paper_route_lens = build_paper_route_lens(
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
    progress_first = build_progress_first_operator_projection(progress)
    stage_artifact_index = _stage_artifact_index_projection(progress)
    stage_operating_layer = _stage_operating_layer_projection(progress)
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
        "next_action_summary_role": "read_only_drilldown_summary",
        "next_action_summary_is_controller_action": False,
        "next_action_summary_can_generate_action": False,
        "next_action_summary_requires_opl_current_control_readback": True,
        "source_refs": source_refs[:12],
        "links_role": "read_only_drilldown_refs",
        "links_can_execute": False,
        "links": _workbench_links(study_id, selected=True, artifact_refs=_stage_review_artifact_refs(stage_review)),
        "actions_role": "operator_intent_projection_refs",
        "actions_can_execute": False,
        "actions_deprecated": True,
        "actions_authority": False,
        "actions_are_operator_intent_refs": True,
        "operator_intent_projection": _workbench_actions(),
        "information_hierarchy": _workbench_information_hierarchy(),
        "stage_operating_layer": stage_operating_layer,
        "workbench": dict(study_workbench),
        "stage_review": stage_review,
        **({"stage_artifact_index": stage_artifact_index} if stage_artifact_index else {}),
        "progress_first": progress_first,
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
    progress_first = build_progress_first_operator_projection(progress)
    stage_artifact_index = _stage_artifact_index_lane(progress)
    lanes = {
        "provider_attempt": provider_attempt,
        "guarded_apply": guarded_apply,
        "stage_review_index": _stage_review_lane(stage_review),
        "memory_receipt": memory_receipt,
        "freshness": freshness_lane,
        "runtime_owner_route_handoffs": runtime_owner_route_handoffs,
        "progress_first": progress_first,
        "stage_artifact_index": stage_artifact_index,
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
        "provider_attempt_claim_role": "opl_readback_observation_only",
        "can_mark_running": False,
        "can_mark_paper_progress": False,
        "can_authorize_provider_admission": False,
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
        "stage_log_summary": dict(_mapping(stage_review.get("stage_log_summary"))),
        "research_pack_progress_summary": dict(_mapping(stage_review.get("research_pack_progress_summary"))),
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


def _stage_artifact_index_projection(progress: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(progress.get("stage_artifact_index"))
    if _non_empty_text(payload.get("surface_kind")) != "stage_artifact_index":
        return {}
    return dict(payload)


def _stage_artifact_index_lane(progress: Mapping[str, Any]) -> dict[str, Any]:
    payload = _stage_artifact_index_projection(progress)
    if not payload:
        return _pending_lane(
            lane_id="stage_artifact_index",
            summary="等待 MAS stage_artifact_index projection；OPL App 只能显示 pending lane。",
            required_surface="stage_artifact_index",
        )
    return {
        "lane_id": "stage_artifact_index",
        "status": "observed",
        "diagnostic_tier": "secondary",
        "derived_projection": True,
        "is_truth_source": False,
        "current_truth_source": STAGE_KERNEL_TRUTH_SOURCE,
        "surface_kind": "stage_artifact_index",
        "current_stage": _non_empty_text(payload.get("current_stage")),
        "next_owner_action": _read_only_action_ref(
            _mapping(payload.get("next_owner_action")),
            role="stage_artifact_index_next_owner_action_ref",
        ),
        "stale_platform_repairs": [dict(item) for item in payload.get("stale_platform_repairs") or [] if isinstance(item, Mapping)],
        "stage_count": len([item for item in payload.get("stages") or [] if isinstance(item, Mapping)]),
        "stages": [dict(item) for item in payload.get("stages") or [] if isinstance(item, Mapping)],
        "authority": _workbench_projection_authority(),
    }


def _stage_operating_layer_projection(progress: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(progress.get(STAGE_KERNEL_TRUTH_SOURCE))
    if _non_empty_text(payload.get("surface_kind")) != STAGE_KERNEL_TRUTH_SOURCE:
        return {
            "surface_kind": "mas_opl_stage_operating_layer",
            "schema_version": 1,
            "status": "pending",
            "display_role": "primary_progress",
            "current_truth_source": STAGE_KERNEL_TRUTH_SOURCE,
            "summary": "等待 MAS stage_kernel_projection；Workbench fail-closed 为 pending lane。",
            "pending_lane": {
                "required_surface": STAGE_KERNEL_TRUTH_SOURCE,
                "display_only": True,
                "fail_closed": True,
            },
            "authority": _stage_operating_layer_authority(),
        }
    return {
        "surface_kind": "mas_opl_stage_operating_layer",
        "schema_version": 1,
        "status": "observed",
        "display_role": "primary_progress",
        "current_truth_source": STAGE_KERNEL_TRUTH_SOURCE,
        "current_stage": _non_empty_text(payload.get("current_stage")),
        "artifact_roles": _mapping_items(payload.get("artifact_roles")),
        "missing_outputs": _string_list(payload.get("missing_outputs")),
        "accepted_receipts": _string_list(payload.get("accepted_receipts")),
        "semantic_validation": dict(_mapping(payload.get("semantic_validation"))),
        "consumability": dict(_mapping(payload.get("consumability"))),
        "lineage": dict(_mapping(payload.get("lineage"))),
        "retention": dict(_mapping(payload.get("retention"))),
        "current_pointer": dict(_mapping(payload.get("current_pointer"))),
        "promotion": dict(_mapping(payload.get("promotion"))),
        "lineage_retention": dict(_mapping(payload.get("lineage_retention"))),
        "state_index": dict(_mapping(payload.get("state_index"))),
        "blocker": dict(_mapping(payload.get("blocker"))),
        "next_owner": dict(_mapping(payload.get("next_owner"))),
        "provider_liveness": dict(_mapping(payload.get("provider_liveness"))),
        **_cross_domain_soak_projection_entry(payload),
        "authority": _stage_operating_layer_authority(),
    }


def _cross_domain_soak_projection_entry(stage_kernel_projection: Mapping[str, Any]) -> dict[str, Any]:
    projection = _cross_domain_soak_projection(
        _mapping(stage_kernel_projection.get("cross_domain_soak"))
    )
    return {"cross_domain_soak": projection} if projection else {}


def _cross_domain_soak_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not payload:
        return {}
    lanes = [_cross_domain_soak_lane(item) for item in _mapping_items(payload.get("lanes"))]
    lanes = [lane for lane in lanes if lane["domain_id"] is not None]
    lane_counts = _cross_domain_soak_lane_counts(lanes)
    seen_domain_ids = {lane["domain_id"] for lane in lanes}
    missing_required_lanes = [
        lane_id for lane_id in REQUIRED_CROSS_DOMAIN_SOAK_LANES if lane_id not in seen_domain_ids
    ]
    return {
        "surface_kind": "mas_opl_stage_kernel_cross_domain_soak_projection",
        "schema_version": 1,
        "status": _cross_domain_soak_status(lane_counts),
        "display_role": "primary_stage_operating_layer_readiness_summary",
        "current_truth_source": STAGE_KERNEL_TRUTH_SOURCE,
        "summary": _non_empty_text(payload.get("readiness_summary"))
        or _non_empty_text(payload.get("summary")),
        "required_domain_lanes": list(REQUIRED_CROSS_DOMAIN_SOAK_LANES),
        "missing_required_lanes": missing_required_lanes,
        "all_required_lanes_present": not missing_required_lanes,
        "lane_counts": lane_counts,
        "lanes": lanes,
        "source_refs": _dedupe_refs(
            [
                *_projection_source_refs(payload),
                *[ref for lane in lanes for ref in _string_list(lane.get("source_refs"))],
            ]
        ),
        "authority_summary": _cross_domain_soak_authority_summary(),
        "authority": _cross_domain_soak_authority(),
    }


def _cross_domain_soak_lane(value: Mapping[str, Any]) -> dict[str, Any]:
    authority_owner = _first_non_empty_text(
        value.get("authority_owner"),
        value.get("domain_authority_owner"),
    )
    refs = _dedupe_refs(
        [
            *_projection_source_refs(value),
            _non_empty_text(value.get("stage_folder_ref")),
            _non_empty_text(value.get("app_workbench_ref")),
            _non_empty_text(value.get("artifact_gallery_ref")),
            _non_empty_text(value.get("stage_progress_log_ref")),
        ]
    )
    return {
        "domain_id": _non_empty_text(value.get("domain_id")),
        "status": _cross_domain_soak_lane_status(value),
        "readiness": _first_non_empty_text(value.get("readiness"), value.get("readiness_state")),
        "authority_owner": authority_owner,
        "authority_function": _non_empty_text(value.get("authority_function")),
        "artifact_role": _non_empty_text(value.get("artifact_role")),
        "human_gate_state": _non_empty_text(value.get("human_gate_state")),
        "export_readiness": _non_empty_text(value.get("export_readiness")),
        "stage_folder_ref": _non_empty_text(value.get("stage_folder_ref")),
        "app_workbench_ref": _non_empty_text(value.get("app_workbench_ref")),
        "artifact_gallery_ref": _non_empty_text(value.get("artifact_gallery_ref")),
        "stage_progress_log_ref": _non_empty_text(value.get("stage_progress_log_ref")),
        "artifact_delta_refs": _string_list(value.get("artifact_delta_refs")),
        "next_owner": dict(_mapping(value.get("next_owner"))),
        "typed_blocker": dict(_mapping(value.get("typed_blocker"))),
        "source_refs": refs,
        "authority": {
            "domain_authority_owner": authority_owner,
            "domain_authority_retained": authority_owner is not None,
            "workbench_can_write_domain_truth": False,
            "workbench_can_authorize_domain_readiness": False,
            "workbench_can_mutate_artifact_body": False,
        },
    }


def _cross_domain_soak_lane_status(value: Mapping[str, Any]) -> str:
    status = _non_empty_text(value.get("status")) or _non_empty_text(value.get("lane_status"))
    if status is not None:
        return _normalize_cross_domain_soak_status(status)
    if _mapping(value.get("typed_blocker")):
        return "blocked"
    if (
        _string_list(value.get("artifact_delta_refs"))
        and _non_empty_text(value.get("controller_freshness")) == "stale"
    ):
        return "stale_controller_with_artifact_delta"
    if bool(value.get("running_provider_attempt")) is True or bool(value.get("active_stage_attempt")) is True:
        return "running"
    return "no_live_run"


def _normalize_cross_domain_soak_status(status: str) -> str:
    known_statuses = {
        "blocked": "blocked",
        "no-live-run": "no_live_run",
        "no_live_run": "no_live_run",
        "running": "running",
        "stale-controller-with-artifact-delta": "stale_controller_with_artifact_delta",
        "stale_controller_with_artifact_delta": "stale_controller_with_artifact_delta",
    }
    return known_statuses.get(status, status)


def _cross_domain_soak_lane_counts(lanes: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "total": len(lanes),
        "running": 0,
        "blocked": 0,
        "stale_controller_with_artifact_delta": 0,
        "no_live_run": 0,
    }
    for lane in lanes:
        status = _non_empty_text(lane.get("status"))
        if status in counts and status != "total":
            counts[status] += 1
    return counts


def _cross_domain_soak_status(lane_counts: Mapping[str, int]) -> str:
    if lane_counts.get("blocked", 0) > 0:
        return "blocked"
    if lane_counts.get("stale_controller_with_artifact_delta", 0) > 0:
        return "stale_controller_with_artifact_delta"
    if lane_counts.get("running", 0) > 0:
        return "running"
    return "no_live_run"


def _cross_domain_soak_authority_summary() -> dict[str, Any]:
    return {
        "stage_kernel_owner": "one-person-lab",
        "workbench_role": "read_only_projection",
        "writes_domain_truth": False,
        "writes_mas_truth": False,
        "can_authorize_domain_readiness": False,
        "can_authorize_artifact_mutation": False,
        "current_truth_source": STAGE_KERNEL_TRUTH_SOURCE,
    }


def _cross_domain_soak_authority() -> dict[str, Any]:
    return {
        "opl_role": "stage_kernel_cross_domain_soak_projection_consumer_only",
        "writes_domain_truth": False,
        "writes_mas_truth": False,
        "claims_publication_ready": False,
        "can_authorize_domain_readiness": False,
        "can_authorize_artifact_mutation": False,
        "can_write_artifact_body": False,
        "current_truth_source": STAGE_KERNEL_TRUTH_SOURCE,
    }


def _mapping_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


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


def _workbench_projection_authority() -> dict[str, Any]:
    return {
        "opl_role": "workbench_projection_consumer_only",
        "writes_mas_truth": False,
        "claims_publication_ready": False,
        "body_free": True,
        "can_authorize_publication_readiness": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_artifact_mutation": False,
        "can_write_memory_body": False,
        "current_truth_source": STAGE_KERNEL_TRUTH_SOURCE,
    }


def _runtime_workbench_projection_boundary() -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_runtime_workbench_projection_boundary",
        "projection_only": True,
        "actions_role": "operator_intent_projection_refs",
        "operator_intent_refs_are_inert": True,
        "links_role": "read_only_drilldown_refs",
        "next_summary_role": "read_only_drilldown_summary",
        "must_not_be_used_as_next_action_authority": True,
        "must_not_be_used_as_provider_admission": True,
        "must_not_be_used_as_publication_ready": True,
        "must_not_be_used_as_paper_progress": True,
        "can_execute_controller_action": False,
        "can_generate_next_action_authority": False,
        "can_authorize_provider_admission": False,
        "can_authorize_worker_attempt": False,
        "can_transport_operator_action": False,
        "can_emit_runtime_command": False,
        "can_open_runtime_endpoint": False,
        "can_retry_or_dead_letter": False,
        "can_authorize_publication_ready": False,
        "can_authorize_quality_verdict": False,
        "can_write_domain_truth": False,
    }


def _stage_operating_layer_authority() -> dict[str, Any]:
    return {
        "opl_role": "stage_operating_layer_projection_consumer_only",
        "writes_mas_truth": False,
        "claims_publication_ready": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_artifact_mutation": False,
        "can_write_artifact_body": False,
        "current_truth_source": STAGE_KERNEL_TRUTH_SOURCE,
    }


def _workbench_information_hierarchy() -> dict[str, Any]:
    return {
        "primary_progress": ["stage_operating_layer"],
        "secondary_diagnostics": [
            "stage_artifact_index",
            "progress_first",
            "paper_route_lens",
            "reference_projection",
        ],
        "diagnostic_surfaces_are_primary_progress": False,
        "current_truth_source": STAGE_KERNEL_TRUTH_SOURCE,
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
            "intent_id": action,
            "surface_kind": "workbench_operator_intent_projection_ref",
            "authority": False,
            "allowed": False,
            "owner": "one-person-lab",
            "endpoint_ref": None,
            "command": None,
            "runtime_endpoint_ref": None,
            "can_execute": False,
            "can_generate_action": False,
            "can_authorize_provider_admission": False,
            "can_transport_operator_action": False,
            "can_emit_runtime_command": False,
            "execute_authority": False,
            "controller_action": False,
            "projection_only": True,
            "intent_ref_only": True,
            "transport_authority": False,
            "display_command_ref_only": True,
            "requires_opl_current_control_readback": True,
            "handled_by_external_opl_workbench_shell": True,
            "must_read_back_mas_owner_receipt": True,
            "idempotency_required": True,
            "external_authority_confirmation_required": False,
            "confirmation_required": False,
        }
        for action in ("pause", "resume", "stop", "reconcile_dry_run", "reconcile_apply")
    }


def _read_only_action_ref(payload: Mapping[str, Any], *, role: str) -> dict[str, Any]:
    if not payload:
        return {}
    return {
        **dict(payload),
        "action_ref_role": role,
        "authority": False,
        "can_execute": False,
        "can_generate_action": False,
        "can_authorize_provider_admission": False,
        "display_command_ref_only": True,
        "requires_opl_current_control_readback": True,
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
