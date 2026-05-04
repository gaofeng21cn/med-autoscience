from __future__ import annotations

from typing import Any, Mapping


PROGRAM_ID = "mas_mds_unified_enhancement_program"
SCHEMA_VERSION = 1

AUTHORITY_TRUTH_SURFACES = (
    "StudyTruthKernel",
    "RuntimeHealthKernel",
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "canonical artifact proof",
)

NO_LIVE_ARTIFACT_CONSTRAINTS = (
    "does_not_modify_live_study_workspace",
    "does_not_modify_current_package",
    "does_not_write_publication_eval",
    "does_not_write_controller_decisions",
    "does_not_write_delivery_truth",
)

PROGRAM_LANES = (
    {
        "lane_id": "L1_real_workspace_longitudinal_soak",
        "title": "Real workspace longitudinal soak",
        "owner": "MedAutoScience runtime + quality",
        "authority_mode": "evidence_only",
        "stage": "active",
        "primary_outputs": (
            "real disease workspace soak matrix",
            "latency and recovery acceptance proof",
            "replay evidence",
        ),
        "authority_boundary": "produces proof and evidence; publication readiness remains with quality truth, controller decision, and artifact rebuild proof",
    },
    {
        "lane_id": "L2_pi_action_projection",
        "title": "PI action projection",
        "owner": "MedAutoScience product entry",
        "authority_mode": "projection",
        "stage": "active",
        "primary_outputs": (
            "single PI-readable next-action payload",
            "study-progress source projection",
            "workspace-cockpit and product-frontdesk consumer projection",
        ),
        "authority_boundary": "does not independently calculate canonical next action from file state, provider state, or MDS oracle",
    },
    {
        "lane_id": "L3_outcome_calibration_and_provider_ops",
        "title": "Outcome calibration and provider ops",
        "owner": "MedAutoScience Observability OS",
        "authority_mode": "observability_only",
        "stage": "active",
        "primary_outputs": (
            "outcome calibration intake",
            "provider freshness and outage health projection",
            "journal-family fixture matrix",
        ),
        "authority_boundary": "updates calibration inputs, health projection, and regression evidence; cannot bypass AI reviewer or publication gate",
    },
    {
        "lane_id": "L4_delivery_and_legacy_upgrade_visibility",
        "title": "Delivery and legacy upgrade visibility",
        "owner": "MedAutoScience artifact/delivery projection",
        "authority_mode": "read_model",
        "stage": "active",
        "primary_outputs": (
            "doctor delivery traffic light",
            "legacy pending queue",
            "backfill blocker report",
        ),
        "authority_boundary": "legacy queue, traffic light, and blockers are projections; controller-authorized sync/apply owns delivery truth writes",
    },
    {
        "lane_id": "L5_natural_boundary_and_audit_compaction",
        "title": "Natural boundary and audit compaction",
        "owner": "MedAutoScience maintainability",
        "authority_mode": "maintainability_only",
        "stage": "active",
        "primary_outputs": (
            "worktree ownership audit",
            "Sentrux and line-budget structure target list",
            "audit compaction pre-contract",
        ),
        "authority_boundary": "maintainability lane does not change study truth, publication truth, delivery truth, or runtime action",
        "compaction_gates": ("restore", "index", "provenance"),
    },
)

RECOMMENDATION_MAPPING = (
    {
        "recommendation_id": "automatic_research_1",
        "source_label": "自动科研 1",
        "lane_id": "L1_real_workspace_longitudinal_soak",
        "handling": "real disease workspace longitudinal soak across pre-submission, revision, reopen, route change, final rebuild, latency, and replay",
    },
    {
        "recommendation_id": "automatic_research_2",
        "source_label": "自动科研 2",
        "lane_id": "L2_pi_action_projection",
        "handling": "single PI-readable action projection shared by product entry surfaces",
    },
    {
        "recommendation_id": "automatic_research_3",
        "source_label": "自动科研 3",
        "lane_id": "L3_outcome_calibration_and_provider_ops",
        "handling": "submission outcome calibration regression evidence",
    },
    {
        "recommendation_id": "automatic_research_4",
        "source_label": "自动科研 4",
        "lane_id": "L3_outcome_calibration_and_provider_ops",
        "handling": "provider freshness, partial outage, and citation drift health projection",
    },
    {
        "recommendation_id": "automatic_research_5",
        "source_label": "自动科研 5",
        "lane_id": "L2_pi_action_projection",
        "secondary_lane_id": "L3_outcome_calibration_and_provider_ops",
        "handling": "journal-family pack as reviewer/authoring input and archetype fixture, without becoming writing authority",
    },
    {
        "recommendation_id": "automatic_research_6",
        "source_label": "自动科研 6",
        "lane_id": "L1_real_workspace_longitudinal_soak",
        "handling": "draft authorization to submission package rebuild latency and recovery proof",
    },
    {
        "recommendation_id": "file_management_1",
        "source_label": "文件管理 1",
        "lane_id": "L4_delivery_and_legacy_upgrade_visibility",
        "handling": "workspace-level legacy upgrade queue read model",
    },
    {
        "recommendation_id": "file_management_2",
        "source_label": "文件管理 2",
        "lane_id": "L4_delivery_and_legacy_upgrade_visibility",
        "handling": "doctor-friendly current_package README projection template",
    },
    {
        "recommendation_id": "file_management_3",
        "source_label": "文件管理 3",
        "lane_id": "L5_natural_boundary_and_audit_compaction",
        "handling": "large-file structure slimming through maintainability targets",
    },
    {
        "recommendation_id": "file_management_4",
        "source_label": "文件管理 4",
        "lane_id": "L3_outcome_calibration_and_provider_ops",
        "handling": "journal profile fixture matrix for cover letters, checklists, and supplement naming",
    },
    {
        "recommendation_id": "file_management_5",
        "source_label": "文件管理 5",
        "lane_id": "L4_delivery_and_legacy_upgrade_visibility",
        "handling": "delivery traffic-light read model for current, stale, legacy pending, and missing states",
    },
    {
        "recommendation_id": "control_plane_1",
        "source_label": "控制面 1",
        "lane_id": "L4_delivery_and_legacy_upgrade_visibility",
        "handling": "read-only backfill blocker report; writes require explicit controller apply",
    },
    {
        "recommendation_id": "control_plane_2",
        "source_label": "控制面 2",
        "lane_id": "L5_natural_boundary_and_audit_compaction",
        "handling": "audit compaction policy blocked until restore, index, and provenance contract exists",
    },
    {
        "recommendation_id": "control_plane_3",
        "source_label": "控制面 3",
        "lane_id": "L5_natural_boundary_and_audit_compaction",
        "handling": "old worktree ownership audit as cleanup safety gate",
    },
    {
        "recommendation_id": "control_plane_4",
        "source_label": "控制面 4",
        "lane_id": "L5_natural_boundary_and_audit_compaction",
        "handling": "historical large-file and high-complexity function split list",
    },
)

PARALLEL_WORKTREE_LANDING = (
    {
        "branch": "codex/mas-soak-matrix-read-model",
        "lane_id": "L1_real_workspace_longitudinal_soak",
        "scope": "real workspace longitudinal soak matrix read model and latency/recovery proof acceptance",
        "absorb_order": 1,
    },
    {
        "branch": "codex/mas-pi-action-projection",
        "lane_id": "L2_pi_action_projection",
        "scope": "single PI action payload shared by frontdesk, cockpit, and progress projections",
        "absorb_order": 2,
    },
    {
        "branch": "codex/mas-calibration-provider-ops",
        "lane_id": "L3_outcome_calibration_and_provider_ops",
        "scope": "outcome calibration, provider health, and journal fixture matrix read model",
        "absorb_order": 3,
    },
    {
        "branch": "codex/mas-delivery-legacy-visibility",
        "lane_id": "L4_delivery_and_legacy_upgrade_visibility",
        "scope": "legacy upgrade queue, doctor README template, and delivery traffic light",
        "absorb_order": 4,
    },
    {
        "branch": "codex/mas-structure-audit-compaction",
        "lane_id": "L5_natural_boundary_and_audit_compaction",
        "scope": "ownership audit, structure target list, and audit compaction pre-contract",
        "absorb_order": 5,
    },
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _lane_by_id() -> dict[str, dict[str, Any]]:
    return {str(lane["lane_id"]): _materialize_lane(lane) for lane in PROGRAM_LANES}


def _materialize_lane(lane: Mapping[str, Any]) -> dict[str, Any]:
    materialized = dict(lane)
    for key in ("primary_outputs", "compaction_gates"):
        if key in materialized:
            materialized[key] = list(materialized[key])
    return materialized


def build_unified_enhancement_program_board(progress_payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    progress = _mapping(progress_payload)
    lane_progress = _mapping(progress.get("lane_progress"))
    lanes: list[dict[str, Any]] = []
    for lane_id, lane in _lane_by_id().items():
        override = _mapping(lane_progress.get(lane_id))
        status = _text(override.get("status")) or _text(lane.get("stage")) or "active"
        lanes.append(
            {
                **lane,
                "status": status,
                "commit": _text(override.get("commit")),
                "verification": list(_list(override.get("verification"))),
                "blocks_usable_target": status not in {"completed", "absorbed"},
            }
        )
    completed = [lane for lane in lanes if lane["status"] in {"completed", "absorbed"}]
    blocked = [lane for lane in lanes if lane["status"] == "blocked"]
    return {
        "surface": "mas_mds_unified_enhancement_program_board",
        "schema_version": SCHEMA_VERSION,
        "program_id": PROGRAM_ID,
        "target_status": {
            "usable_surface": "repo_read_model",
            "runtime_ready_when": "all_lanes_completed_or_absorbed_in_l1_to_l5_order",
            "current_live_artifact_status": "out_of_scope",
            "publication_readiness_claim": "not_claimed_by_this_board",
        },
        "authority_boundaries": {
            "authority_truth_surfaces": list(AUTHORITY_TRUTH_SURFACES),
            "projection_lanes": [
                "L2_pi_action_projection",
                "L3_outcome_calibration_and_provider_ops",
                "L4_delivery_and_legacy_upgrade_visibility",
            ],
            "projection_pending_authority_allowed": True,
            "projection_authority_allowed": False,
        },
        "quality_constraints": {
            "gate_relaxation_allowed": False,
            "projection_can_claim_publication_readiness": False,
            "projection_can_write_submission_authority": False,
            "no_live_artifact_constraints": list(NO_LIVE_ARTIFACT_CONSTRAINTS),
        },
        "lanes": lanes,
        "recommendation_mapping": [dict(item) for item in RECOMMENDATION_MAPPING],
        "parallel_worktree_landing": [dict(item) for item in PARALLEL_WORKTREE_LANDING],
        "absorb_plan": [
            {"lane_id": item["lane_id"], "branch": item["branch"], "absorb_order": item["absorb_order"]}
            for item in PARALLEL_WORKTREE_LANDING
        ],
        "status_summary": {
            "lane_count": len(lanes),
            "recommendation_count": len(RECOMMENDATION_MAPPING),
            "completed_or_absorbed_count": len(completed),
            "blocked_count": len(blocked),
            "usable_target_ready": len(completed) == len(lanes) and not blocked,
        },
    }


def validate_unified_enhancement_program_board(board: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if _text(board.get("surface")) != "mas_mds_unified_enhancement_program_board":
        issues.append({"code": "invalid_surface", "message": "unified enhancement program board surface mismatch"})
    expected_lanes = set(_lane_by_id())
    actual_lanes = {
        str(lane.get("lane_id"))
        for lane in _list(board.get("lanes"))
        if isinstance(lane, Mapping) and _text(lane.get("lane_id"))
    }
    for lane_id in sorted(expected_lanes - actual_lanes):
        issues.append({"code": "missing_lane", "lane_id": lane_id})
    expected_recommendations = {str(item["recommendation_id"]) for item in RECOMMENDATION_MAPPING}
    actual_recommendations = {
        str(item.get("recommendation_id"))
        for item in _list(board.get("recommendation_mapping"))
        if isinstance(item, Mapping) and _text(item.get("recommendation_id"))
    }
    for recommendation_id in sorted(expected_recommendations - actual_recommendations):
        issues.append({"code": "missing_recommendation", "recommendation_id": recommendation_id})
    lane_ids = expected_lanes
    for item in _list(board.get("recommendation_mapping")):
        if not isinstance(item, Mapping):
            issues.append({"code": "invalid_recommendation", "message": "recommendation mapping must be an object"})
            continue
        lane_id = _text(item.get("lane_id"))
        secondary_lane_id = _text(item.get("secondary_lane_id"))
        if lane_id and lane_id not in lane_ids:
            issues.append({"code": "recommendation_unknown_lane", "recommendation_id": _text(item.get("recommendation_id")), "lane_id": lane_id})
        if secondary_lane_id and secondary_lane_id not in lane_ids:
            issues.append(
                {
                    "code": "recommendation_unknown_lane",
                    "recommendation_id": _text(item.get("recommendation_id")),
                    "lane_id": secondary_lane_id,
                }
            )
    projection_lanes = {"L2_pi_action_projection", "L3_outcome_calibration_and_provider_ops", "L4_delivery_and_legacy_upgrade_visibility"}
    for lane in _list(board.get("lanes")):
        if not isinstance(lane, Mapping):
            issues.append({"code": "invalid_lane", "message": "lane must be an object"})
            continue
        lane_id = _text(lane.get("lane_id")) or "<unknown>"
        if not _text(lane.get("owner")):
            issues.append({"code": "lane_missing_owner", "lane_id": lane_id})
        if not _text(lane.get("authority_boundary")):
            issues.append({"code": "lane_missing_authority_boundary", "lane_id": lane_id})
        if lane_id in projection_lanes and _text(lane.get("authority_mode")) not in {"projection", "observability_only", "read_model"}:
            issues.append({"code": "projection_lane_claims_authority", "lane_id": lane_id})
        if lane_id == "L5_natural_boundary_and_audit_compaction":
            gates = {str(gate) for gate in _list(lane.get("compaction_gates"))}
            for gate in ("restore", "index", "provenance"):
                if gate not in gates:
                    issues.append({"code": "l5_missing_compaction_gate", "lane_id": lane_id, "gate": gate})
    absorb_plan = _list(board.get("absorb_plan"))
    absorb_lane_order = [
        _text(item.get("lane_id"))
        for item in absorb_plan
        if isinstance(item, Mapping)
    ]
    expected_absorb_order = [item["lane_id"] for item in PARALLEL_WORKTREE_LANDING]
    if absorb_lane_order != expected_absorb_order:
        issues.append({"code": "invalid_absorb_order", "expected": expected_absorb_order, "actual": absorb_lane_order})
    constraints = _mapping(board.get("quality_constraints"))
    if constraints.get("gate_relaxation_allowed") is not False:
        issues.append({"code": "quality_gate_relaxation_allowed"})
    if constraints.get("projection_can_claim_publication_readiness") is not False:
        issues.append({"code": "projection_can_claim_publication_readiness"})
    if constraints.get("projection_can_write_submission_authority") is not False:
        issues.append({"code": "projection_can_write_submission_authority"})
    no_live_constraints = set(str(item) for item in _list(constraints.get("no_live_artifact_constraints")))
    for constraint in NO_LIVE_ARTIFACT_CONSTRAINTS:
        if constraint not in no_live_constraints:
            issues.append({"code": "missing_no_live_artifact_constraint", "constraint": constraint})
    return {
        "surface": "mas_mds_unified_enhancement_program_board_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }
