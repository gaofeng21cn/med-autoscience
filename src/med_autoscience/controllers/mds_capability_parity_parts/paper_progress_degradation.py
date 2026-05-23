from __future__ import annotations

import copy
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 1

ALLOWED_PAPER_PROGRESS_DEGRADATION_CLASSES: tuple[str, ...] = (
    "production_degrading",
    "production_risk",
    "diagnostic_degrading",
    "acceptable_design_difference",
    "retired_non_goal",
)
REQUIRED_PRODUCTION_DEGRADING_OVERLAY_IDS: tuple[str, ...] = (
    "owner_handoff_dispatch",
    "repeat_suppression",
    "work_unit_redrive",
)

PAPER_PROGRESS_DEGRADATION_BY_SURFACE: dict[str, dict[str, Any]] = {
    "daemon_residency": {
        "classification": "production_risk",
        "affects_automatic_paper_production": True,
        "production_path": "outer_supervision_recovery_latency",
        "rationale": "Scheduled supervision can delay stale-run detection and recovery, but MAS turn continuation no longer depends on resident MDS.",
        "required_guard_surface": "OPL current_control_state plus MAS owner receipt/typed blocker",
    },
    "supervision_cadence": {
        "classification": "production_risk",
        "affects_automatic_paper_production": True,
        "production_path": "outer_supervision_recovery_latency",
        "rationale": "The five-minute tick is acceptable only while per-turn continuation and stale recovery receipts remain healthy.",
        "required_guard_surface": "OPL scheduler replacement tick receipt plus MAS owner receipt",
    },
    "turn_completion_continuation": {
        "classification": "acceptable_design_difference",
        "affects_automatic_paper_production": True,
        "production_path": "opl_stage_attempt_continuation",
        "rationale": "The production behavior is preserved by OPL stage attempt reconciliation; MAS only consumes typed closeout, owner receipt, or blocker refs.",
        "required_guard_surface": "OPL stage attempt ledger plus MAS owner receipt/typed blocker",
    },
    "quest_create_resume_pause_stop": {
        "classification": "acceptable_design_difference",
        "affects_automatic_paper_production": True,
        "production_path": "opl_stage_runtime_lifecycle_controls",
        "rationale": "Lifecycle controls move through OPL stage runtime while MAS supplies DomainIntent, owner receipt, or typed blocker.",
        "required_guard_surface": "OPL current_control_state plus MAS domain authority refs",
    },
    "live_worker_session_tracking": {
        "classification": "production_risk",
        "affects_automatic_paper_production": True,
        "production_path": "opl_provider_liveness_and_stale_attempt_detection",
        "rationale": "Durable OPL liveness is safer than an in-memory daemon store, but stale domain receipts can still stall production if not reconciled.",
        "required_guard_surface": "OPL current_control_state/domain_authority_refs_index",
    },
    "crash_recovery_auto_resume": {
        "classification": "production_risk",
        "affects_automatic_paper_production": True,
        "production_path": "crash_recovery_and_auto_resume",
        "rationale": "Recovery is OPL-owned and MDS-independent; MAS must return owner receipts, route-back, or typed blockers when provider recovery closes.",
        "required_guard_surface": "OPL current_control_state plus MAS domain_health_diagnostic typed blocker",
    },
    "queued_user_messages_mailbox": {
        "classification": "production_risk",
        "affects_automatic_paper_production": True,
        "production_path": "task_intake_owner_handoff_and_user_queue",
        "rationale": "Quest-local queueing is covered, but routing drift in broader task intake can starve production work.",
        "required_guard_surface": "owner_route/consumer latest/dispatch receipts",
    },
    "progress_visibility": {
        "classification": "diagnostic_degrading",
        "affects_automatic_paper_production": False,
        "production_path": "operator_progress_diagnostics",
        "rationale": "Portal and route/decision views improve supervision visibility without writing paper production truth.",
        "required_guard_surface": "progress_portal read-only source refs",
    },
    "webui_websocket_terminal_streaming": {
        "classification": "diagnostic_degrading",
        "affects_automatic_paper_production": False,
        "production_path": "opl_current_control_state_terminal_diagnostics",
        "rationale": "Terminal/log/provider drilldown is owned by OPL current_control_state; missing interactive attach should not block MAS paper work.",
        "required_guard_surface": "opl_current_control_state_or_typed_blocker_ref",
    },
    "connector_channel_background_delivery": {
        "classification": "retired_non_goal",
        "affects_automatic_paper_production": False,
        "production_path": "retired_connector_delivery",
        "rationale": "Background chat connectors are outside default MAS paper production.",
        "required_guard_surface": "durable handoff refs only",
    },
    "mcp_surface": {
        "classification": "acceptable_design_difference",
        "affects_automatic_paper_production": False,
        "production_path": "adapter_status_access",
        "rationale": "MAS MCP reads owner surfaces directly and remains adapter-only.",
        "required_guard_surface": "MAS MCP truth refs",
    },
    "gitops_state_management": {
        "classification": "retired_non_goal",
        "affects_automatic_paper_production": False,
        "production_path": "retired_gitops_lifecycle",
        "rationale": "Runtime lifecycle is OPL-owned; MAS keeps only domain authority refs and restore-proof provenance. MDS quest Git is not a production goal.",
        "required_guard_surface": "domain_authority_refs_index/restore provenance",
    },
    "memory_lesson_store": {
        "classification": "production_risk",
        "affects_automatic_paper_production": True,
        "production_path": "incident_learning_and_repeat_avoidance",
        "rationale": "Memory is evidence-only, but losing lesson intake can reintroduce repeated failed work patterns.",
        "required_guard_surface": "portfolio/research_memory and incident learning read models",
    },
    "team_multiagent_coordination": {
        "classification": "production_risk",
        "affects_automatic_paper_production": True,
        "production_path": "owner_route_controller_coordination",
        "rationale": "MAS controller routing replaces MDS team service; routing drift can strand publication work units.",
        "required_guard_surface": "owner_route -> consumer latest -> executor dispatch -> rescan",
    },
    "artifact_interaction_handoff": {
        "classification": "production_risk",
        "affects_automatic_paper_production": True,
        "production_path": "artifact_inventory_package_locator",
        "rationale": "Artifact discovery feeds package production; interactive mutation APIs remain outside default MAS.",
        "required_guard_surface": "Artifact OS inventory/package locator/rebuild proof",
    },
    "system_update_daemon_lifecycle_controls": {
        "classification": "retired_non_goal",
        "affects_automatic_paper_production": False,
        "production_path": "retired_external_daemon_admin",
        "rationale": "MDS daemon lifecycle controls are retired because MAS has no default MDS daemon dependency.",
        "required_guard_surface": "opl_current_control_state lifecycle receipt",
    },
    "workspace_local_host_service": {
        "classification": "retired_non_goal",
        "affects_automatic_paper_production": False,
        "production_path": "retired_workspace_local_service",
        "rationale": "Old workspace-local host services are cleanup evidence, not an active production owner.",
        "required_guard_surface": "opl_provider_runtime_manager registration and explicit local legacy cleanup proof",
    },
}

PAPER_PROGRESS_DEGRADATION_OVERLAYS: tuple[dict[str, Any], ...] = (
    {
        "risk_id": "owner_handoff_dispatch",
        "classification": "production_degrading",
        "affects_automatic_paper_production": True,
        "covered_by_behavior_surface": "queued_user_messages_mailbox",
        "production_path": "task_intake_to_controller_to_executor_dispatch",
        "rationale": "If owner handoff cannot route actionable paper work to the executor, automatic production stalls even when progress surfaces render.",
        "required_guard_surface": "owner_route/consumer latest/dispatch receipts",
    },
    {
        "risk_id": "repeat_suppression",
        "classification": "production_degrading",
        "affects_automatic_paper_production": True,
        "covered_by_behavior_surface": "memory_lesson_store",
        "production_path": "no_op_suppression_and_incident_learning",
        "rationale": "If repeat suppression fails, the runtime can burn turns on unchanged blockers instead of advancing the manuscript or package.",
        "required_guard_surface": "managed_study_no_op_suppressions/runtime efficiency projection",
    },
    {
        "risk_id": "work_unit_redrive",
        "classification": "production_degrading",
        "affects_automatic_paper_production": True,
        "covered_by_behavior_surface": "crash_recovery_auto_resume",
        "production_path": "opl_publication_work_unit_attempt_reconcile",
        "rationale": "If failed or stale work units cannot be reconciled by OPL and closed by MAS owner receipt or typed blocker, automatic paper production cannot recover without manual repair.",
        "required_guard_surface": "OPL current_control_state/gate-clearing batch/work-unit owner receipts",
    },
)


def paper_progress_degradation_for_surface(surface_id: str) -> dict[str, Any]:
    if surface_id not in PAPER_PROGRESS_DEGRADATION_BY_SURFACE:
        raise ValueError(f"missing paper progress degradation classification: {surface_id}")
    return copy.deepcopy(PAPER_PROGRESS_DEGRADATION_BY_SURFACE[surface_id])


def build_mds_paper_progress_degradation_classifier(
    behavior_surfaces: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    behavior_classifications = [
        _paper_progress_classification_projection(surface)
        for surface in behavior_surfaces
    ]
    overlay_risks = [copy.deepcopy(risk) for risk in PAPER_PROGRESS_DEGRADATION_OVERLAYS]
    return {
        "surface": "mds_paper_progress_degradation_classifier",
        "schema_version": SCHEMA_VERSION,
        "owner": "MedAutoScience",
        "scope": "mds_behavior_equivalence_paper_progress_impact",
        "allowed_degradation_classes": list(ALLOWED_PAPER_PROGRESS_DEGRADATION_CLASSES),
        "behavior_surface_classifications": behavior_classifications,
        "overlay_risks": overlay_risks,
        "summary": _paper_progress_degradation_summary(behavior_classifications, overlay_risks),
    }


def validate_behavior_surface_paper_progress(
    surface: Mapping[str, Any],
    surface_id: str,
    issues: list[dict[str, Any]],
) -> None:
    classification = surface.get("paper_progress_degradation")
    if not isinstance(classification, Mapping):
        issues.append({"code": "behavior_surface_missing_paper_progress_degradation", "surface_id": surface_id})
        return
    if _text(classification.get("classification")) not in ALLOWED_PAPER_PROGRESS_DEGRADATION_CLASSES:
        issues.append(
            {
                "code": "behavior_surface_invalid_paper_progress_degradation_class",
                "surface_id": surface_id,
                "classification": _text(classification.get("classification")),
            }
        )
    if not isinstance(classification.get("affects_automatic_paper_production"), bool):
        issues.append({"code": "behavior_surface_invalid_paper_progress_impact_flag", "surface_id": surface_id})
    for field in ("production_path", "rationale", "required_guard_surface"):
        if not _text(classification.get(field)):
            issues.append({"code": f"behavior_surface_missing_paper_progress_{field}", "surface_id": surface_id})


def validate_paper_progress_degradation_classifier(
    matrix: Mapping[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    classifier = matrix.get("paper_progress_degradation_classifier")
    if not isinstance(classifier, Mapping):
        issues.append({"code": "paper_progress_degradation_classifier_missing"})
        return
    if _text(classifier.get("surface")) != "mds_paper_progress_degradation_classifier":
        issues.append({"code": "paper_progress_degradation_classifier_wrong_surface"})
    if list(classifier.get("allowed_degradation_classes") or []) != list(ALLOWED_PAPER_PROGRESS_DEGRADATION_CLASSES):
        issues.append({"code": "paper_progress_degradation_allowed_classes_drift"})
    behavior_ids, embedded_classifications = _paper_progress_behavior_surface_index(matrix)
    classification_items = _list(classifier.get("behavior_surface_classifications"))
    overlay_items = _list(classifier.get("overlay_risks"))
    _validate_paper_progress_classifier_behavior_items(
        behavior_ids=behavior_ids,
        embedded_classifications=embedded_classifications,
        classification_items=classification_items,
        issues=issues,
    )
    _validate_paper_progress_classifier_overlay_items(overlay_items, issues)
    _validate_paper_progress_classifier_summary(
        matrix=matrix,
        classifier=classifier,
        classification_items=classification_items,
        overlay_items=overlay_items,
        issues=issues,
    )


def _paper_progress_behavior_surface_index(
    matrix: Mapping[str, Any],
) -> tuple[list[str], dict[str, object]]:
    behavior_surfaces = [surface for surface in _list(matrix.get("behavior_surfaces")) if isinstance(surface, Mapping)]
    behavior_ids = [_text(surface.get("surface_id")) for surface in behavior_surfaces]
    embedded_classifications = {
        _text(surface.get("surface_id")): surface.get("paper_progress_degradation")
        for surface in behavior_surfaces
    }
    return behavior_ids, embedded_classifications


def _validate_paper_progress_classifier_behavior_items(
    *,
    behavior_ids: Sequence[str],
    embedded_classifications: Mapping[str, object],
    classification_items: Sequence[object],
    issues: list[dict[str, Any]],
) -> None:
    classification_ids = [
        _text(item.get("surface_id"))
        for item in classification_items
        if isinstance(item, Mapping)
    ]
    if sorted(classification_ids) != sorted(behavior_ids):
        issues.append(
            {
                "code": "paper_progress_degradation_behavior_surface_coverage_drift",
                "expected_surface_ids": sorted(behavior_ids),
                "observed_surface_ids": sorted(classification_ids),
            }
        )
    for item in classification_items:
        if isinstance(item, Mapping):
            _validate_paper_progress_classification_item(item, "surface_id", issues)
            _validate_paper_progress_classifier_matches_embedded_surface(
                item,
                embedded_classifications.get(_text(item.get("surface_id"))),
                issues,
            )


def _validate_paper_progress_classifier_overlay_items(
    overlay_items: Sequence[object],
    issues: list[dict[str, Any]],
) -> None:
    for item in overlay_items:
        if isinstance(item, Mapping):
            _validate_paper_progress_classification_item(item, "risk_id", issues)
    required_overlays = set(REQUIRED_PRODUCTION_DEGRADING_OVERLAY_IDS)
    production_degrading_overlays = {
        _text(item.get("risk_id"))
        for item in overlay_items
        if isinstance(item, Mapping) and _text(item.get("classification")) == "production_degrading"
    }
    missing_overlays = required_overlays - production_degrading_overlays
    if missing_overlays:
        issues.append(
            {
                "code": "paper_progress_degradation_missing_required_production_overlay",
                "missing_overlay_ids": sorted(missing_overlays),
            }
        )


def _validate_paper_progress_classifier_summary(
    *,
    matrix: Mapping[str, Any],
    classifier: Mapping[str, Any],
    classification_items: Sequence[object],
    overlay_items: Sequence[object],
    issues: list[dict[str, Any]],
) -> None:
    summary = classifier.get("summary")
    expected_summary = _paper_progress_degradation_summary(
        [item for item in classification_items if isinstance(item, Mapping)],
        [item for item in overlay_items if isinstance(item, Mapping)],
    )
    if not isinstance(summary, Mapping) or dict(summary) != expected_summary:
        issues.append({"code": "paper_progress_degradation_summary_drift"})
    matrix_summary = matrix.get("paper_progress_degradation_summary")
    if not isinstance(matrix_summary, Mapping) or dict(matrix_summary) != expected_summary:
        issues.append({"code": "paper_progress_degradation_matrix_summary_drift"})


def _paper_progress_classification_projection(surface: Mapping[str, Any]) -> dict[str, Any]:
    classification = surface.get("paper_progress_degradation")
    payload = classification if isinstance(classification, Mapping) else {}
    projection = copy.deepcopy(dict(payload))
    projection["surface_id"] = _text(surface.get("surface_id"))
    return projection


def _paper_progress_degradation_summary(
    behavior_classifications: Sequence[Mapping[str, Any]],
    overlay_risks: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    behavior_counts = _classifier_counts(behavior_classifications)
    overlay_counts = _classifier_counts(overlay_risks)
    combined_counts = {
        classification: behavior_counts[classification] + overlay_counts[classification]
        for classification in ALLOWED_PAPER_PROGRESS_DEGRADATION_CLASSES
    }
    return {
        "behavior_surface_count": len(behavior_classifications),
        "overlay_risk_count": len(overlay_risks),
        "total_classifier_entry_count": len(behavior_classifications) + len(overlay_risks),
        "automatic_paper_production_behavior_surface_count": sum(
            1 for item in behavior_classifications if item.get("affects_automatic_paper_production") is True
        ),
        "automatic_paper_production_entry_count": sum(
            1
            for item in (*behavior_classifications, *overlay_risks)
            if item.get("affects_automatic_paper_production") is True
        ),
        "production_degrading_entry_count": combined_counts["production_degrading"],
        "behavior_surface_classification_counts": behavior_counts,
        "overlay_classification_counts": overlay_counts,
        "combined_classification_counts": combined_counts,
        "production_degrading_risk_ids": [
            _text(item.get("risk_id"))
            for item in overlay_risks
            if _text(item.get("classification")) == "production_degrading"
        ],
    }


def _classifier_counts(items: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        classification: sum(1 for item in items if _text(item.get("classification")) == classification)
        for classification in ALLOWED_PAPER_PROGRESS_DEGRADATION_CLASSES
    }


def _validate_paper_progress_classifier_matches_embedded_surface(
    item: Mapping[str, Any],
    embedded: object,
    issues: list[dict[str, Any]],
) -> None:
    surface_id = _text(item.get("surface_id"))
    if not isinstance(embedded, Mapping):
        issues.append({"code": "paper_progress_degradation_missing_embedded_surface_classification", "surface_id": surface_id})
        return
    for field in (
        "classification",
        "affects_automatic_paper_production",
        "production_path",
        "rationale",
        "required_guard_surface",
    ):
        if item.get(field) != embedded.get(field):
            issues.append(
                {
                    "code": "paper_progress_degradation_classifier_surface_projection_drift",
                    "surface_id": surface_id,
                    "field": field,
                }
            )


def _validate_paper_progress_classification_item(
    item: Mapping[str, Any],
    id_field: str,
    issues: list[dict[str, Any]],
) -> None:
    item_id = _text(item.get(id_field))
    if not item_id:
        issues.append({"code": "paper_progress_degradation_missing_id", "id_field": id_field})
    if _text(item.get("classification")) not in ALLOWED_PAPER_PROGRESS_DEGRADATION_CLASSES:
        issues.append(
            {
                "code": "paper_progress_degradation_invalid_class",
                id_field: item_id,
                "classification": _text(item.get("classification")),
            }
        )
    if not isinstance(item.get("affects_automatic_paper_production"), bool):
        issues.append({"code": "paper_progress_degradation_invalid_impact_flag", id_field: item_id})
    for field in ("production_path", "rationale", "required_guard_surface"):
        if not _text(item.get(field)):
            issues.append({"code": f"paper_progress_degradation_missing_{field}", id_field: item_id})


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str:
    return str(value or "").strip()
