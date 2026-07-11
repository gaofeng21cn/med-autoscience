from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.research_memory_contract import SCHEMA_VERSION


SURFACE = "stage_research_frontier_board"
SUMMARY_SURFACE = "stage_research_frontier_board_summary"
OPL_PROJECTION_SURFACE = "stage_research_frontier_board_opl_refs_projection"
ROLLBACK_POLICY_SURFACE = "stage_research_frontier_rollback_target_policy"
FRONTIER_STATUSES = ("active", "testing", "rejected", "deferred", "stop_loss")
PACK_ROLLBACK_TARGETS = (
    "01-study_intake",
    "02-protocol_and_analysis_plan",
    "03-data_asset_and_cohort_build",
    "04-analysis_execution",
    "05-evidence_synthesis",
    "06-manuscript_authoring",
    "07-independent_review_and_revision",
    "08-publication_package_handoff",
)
STAGE_TO_PACK_TARGET = {
    "scout": "01-study_intake",
    "idea": "02-protocol_and_analysis_plan",
    "baseline": "03-data_asset_and_cohort_build",
    "experiment": "04-analysis_execution",
    "analysis-campaign": "04-analysis_execution",
    "write": "06-manuscript_authoring",
    "review": "07-independent_review_and_revision",
    "decision": "07-independent_review_and_revision",
    "finalize": "08-publication_package_handoff",
}
FAILURE_SCOPE_TARGETS = {
    "clinical_question": (
        "01-study_intake",
        "clinical question, publication angle, or source fit failed at intake scope",
    ),
    "publication_angle": (
        "01-study_intake",
        "clinical question, publication angle, or source fit failed at intake scope",
    ),
    "study_intake": (
        "01-study_intake",
        "clinical question, publication angle, or source fit failed at intake scope",
    ),
    "protocol": (
        "02-protocol_and_analysis_plan",
        "protocol, endpoint, SAP, comparator, or primary claim definition needs redesign",
    ),
    "endpoint": (
        "02-protocol_and_analysis_plan",
        "protocol, endpoint, SAP, comparator, or primary claim definition needs redesign",
    ),
    "sap": (
        "02-protocol_and_analysis_plan",
        "protocol, endpoint, SAP, comparator, or primary claim definition needs redesign",
    ),
    "primary_claim": (
        "02-protocol_and_analysis_plan",
        "protocol, endpoint, SAP, comparator, or primary claim definition needs redesign",
    ),
    "cohort_definition": (
        "02-protocol_and_analysis_plan",
        "protocol, endpoint, SAP, comparator, or primary claim definition needs redesign",
    ),
    "data_asset": (
        "03-data_asset_and_cohort_build",
        "data asset, cohort build, variable availability, or endpoint construction failed",
    ),
    "cohort_build": (
        "03-data_asset_and_cohort_build",
        "data asset, cohort build, variable availability, or endpoint construction failed",
    ),
    "variable_availability": (
        "03-data_asset_and_cohort_build",
        "data asset, cohort build, variable availability, or endpoint construction failed",
    ),
    "analysis_execution": (
        "04-analysis_execution",
        "analysis execution, sensitivity, subgroup, or statistical blocker needs bounded repair",
    ),
    "statistical_blocker": (
        "04-analysis_execution",
        "analysis execution, sensitivity, subgroup, or statistical blocker needs bounded repair",
    ),
    "claim_evidence": (
        "05-evidence_synthesis",
        "claim and evidence relationship must be synthesized before route continuation",
    ),
    "evidence_synthesis": (
        "05-evidence_synthesis",
        "claim and evidence relationship must be synthesized before route continuation",
    ),
    "manuscript_claim": (
        "06-manuscript_authoring",
        "manuscript claim wording or evidence expression needs authoring repair",
    ),
    "manuscript_authoring": (
        "06-manuscript_authoring",
        "manuscript claim wording or evidence expression needs authoring repair",
    ),
    "reviewer_quality": (
        "07-independent_review_and_revision",
        "reviewer or AI-reviewer quality issue needs revision routing before package handoff",
    ),
    "quality_review": (
        "07-independent_review_and_revision",
        "reviewer or AI-reviewer quality issue needs revision routing before package handoff",
    ),
    "publication_package": (
        "08-publication_package_handoff",
        "publication package, artifact currentness, or submission authority issue belongs to handoff",
    ),
    "artifact_authority": (
        "08-publication_package_handoff",
        "publication package, artifact currentness, or submission authority issue belongs to handoff",
    ),
}

STATUS_KEYS = {
    "active": ("active_candidates", "active_paths", "active_routes"),
    "testing": ("testing_candidates", "candidate_tests", "in_flight_candidates"),
    "rejected": ("rejected_candidates", "rejected_paths", "failed_candidates"),
    "deferred": ("deferred_candidates", "deferred_paths", "parking_lot_candidates"),
    "stop_loss": ("stop_loss_candidates", "stop_loss_paths", "stop_candidates"),
}
CONTAINER_KEYS = (
    "research_frontier_board",
    "frontier_board",
    "candidate_frontier",
    "medical_research_frontier",
    "bounded_analysis_frontier",
    "research_frontier",
)
GENERIC_CANDIDATE_KEYS = ("candidates", "candidate_routes", "routes", "paths")
WRITEBACK_REF_KEYS = (
    "writeback_refs",
    "memory_writeback_refs",
    "accepted_writeback_refs",
    "rejected_writeback_refs",
    "blocked_writeback_refs",
)


def frontier_board_authority_boundary() -> dict[str, Any]:
    return {
        "surface_role": "stage_local_working_board_and_memory_delta",
        "can_authorize_stage_completion": False,
        "can_replace_next_action": False,
        "can_write_domain_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
        "can_write_runtime_queue": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_memory_body": False,
        "can_authorize_route_back": False,
    }


def build_research_frontier_board(
    *,
    study_id: str,
    stage: str,
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    candidates = _dedupe_candidates(_collect_candidates(packet, source="packet"))
    writeback_refs = _dedupe_dicts([*_packet_writeback_refs(packet), *_candidate_writeback_refs(candidates)])
    rollback_policy = _rollback_policy(stage=stage, packet=packet, candidates=candidates)
    summary = _summary(
        candidates=candidates,
        writeback_refs=writeback_refs,
        rollback_policy=rollback_policy,
        next_hypothesis_suggestion=_next_hypothesis(packet=packet, candidates=candidates),
    )
    refs = [_candidate_ref(candidate) for candidate in candidates]
    source_fingerprint = _fingerprint(
        {
            "refs": refs,
            "writeback_refs": writeback_refs,
            "rollback_policy": rollback_policy,
            "next_hypothesis_suggestion": summary.get("next_hypothesis_suggestion"),
        }
    )
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": _required_text("study_id", study_id),
        "stage": _required_text("stage", stage),
        "status": "has_candidates" if candidates else "empty",
        "candidates": candidates,
        "frontier_board_refs": refs,
        "memory_writeback_refs": writeback_refs,
        "summary": summary,
        "rollback_target_policy": rollback_policy,
        "opl_refs_only_projection": _opl_projection(
            summary=summary,
            refs=refs,
            writeback_refs=writeback_refs,
            rollback_policy=rollback_policy,
        ),
        "source_fingerprint": source_fingerprint,
        "authority_boundary": frontier_board_authority_boundary(),
        "idempotency_key": (
            f"stage_research_frontier_board:{_required_text('study_id', study_id)}:"
            f"{_required_text('stage', stage)}:{source_fingerprint}"
        ),
    }


def frontier_board_packet_fields(board: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "research_frontier_board_summary": dict(board["summary"]),
        "research_frontier_board_refs": [dict(ref) for ref in board["frontier_board_refs"]],
        "opl_research_frontier_projection": dict(board["opl_refs_only_projection"]),
    }


def adopt_frontier_route_back_terminal_decision(
    *,
    board: Mapping[str, Any],
    selected_target_stage: str,
    repair_scope: str | None = None,
    candidate_id: str | None = None,
    signal: str | None = None,
    reason: str | None = None,
    next_owner: str = "mission_executor",
) -> dict[str, Any]:
    target_stage = _pack_target_for_stage(selected_target_stage)
    suggestion = _selected_frontier_suggestion(
        board=board,
        target_stage=target_stage,
        candidate_id=candidate_id,
        signal=signal,
    )
    if not suggestion:
        raise ValueError(
            "frontier route-back adoption requires an observed rollback target suggestion"
        )
    selected_reason = _text(reason) or _text(suggestion.get("reason"))
    return _drop_empty(
        {
            "decision_kind": "route_back",
            "status": "frontier_route_back_adopted",
            "reason": selected_reason
            or "MAS stage closeout adopted a research frontier rollback suggestion",
            "next_owner": _required_text("next_owner", next_owner),
            "target_stage_id": target_stage,
            "repair_scope": _text(repair_scope) or selected_reason,
            "frontier_advisory_ref": _frontier_advisory_ref(
                board=board,
                suggestion=suggestion,
                target_stage=target_stage,
            ),
            "frontier_candidate_id": _text(suggestion.get("candidate_id")),
            "frontier_signal": _text(suggestion.get("signal")),
            "frontier_advisory_authority": False,
            "stage_closeout_authority_required": True,
        }
    )


def _collect_candidates(packet: Mapping[str, Any], *, source: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for status, keys in STATUS_KEYS.items():
        for key in keys:
            candidates.extend(_items(packet.get(key), status=status, source=f"{source}.{key}"))

    for key in ("failed_paths", "failed_path_refs"):
        candidates.extend(_items(packet.get(key), status="rejected", source=f"{source}.{key}", failed_path=True))

    candidates.extend(
        _items(packet.get("claim_boundary_decisions"), status="deferred", source=f"{source}.claim_boundary_decisions")
    )

    for key in GENERIC_CANDIDATE_KEYS:
        candidates.extend(_items(packet.get(key), status="active", source=f"{source}.{key}"))

    for key in CONTAINER_KEYS:
        container = packet.get(key)
        if isinstance(container, Mapping):
            candidates.extend(_collect_candidates(container, source=f"{source}.{key}"))
        else:
            candidates.extend(_items(container, status="active", source=f"{source}.{key}"))

    normalized_closeout = packet.get("normalized_closeout")
    if isinstance(normalized_closeout, Mapping):
        candidates.extend(_collect_candidates(normalized_closeout, source=f"{source}.normalized_closeout"))
    return candidates


def _items(value: object, *, status: str, source: str, failed_path: bool = False) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        nested = _collect_candidates(value, source=source)
        return nested or [_candidate(value, default_status=status, source=source, failed_path=failed_path)]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [
            _candidate(item, default_status=status, source=source, failed_path=failed_path)
            for item in value
            if isinstance(item, (Mapping, str))
        ]
    if _text(value):
        return [_candidate(_text(value), default_status=status, source=source, failed_path=failed_path)]
    return []


def _candidate(
    item: Mapping[str, Any] | str,
    *,
    default_status: str,
    source: str,
    failed_path: bool,
) -> dict[str, Any]:
    payload = dict(item) if isinstance(item, Mapping) else {"candidate_id": item, "summary": item}
    status = _status(payload, default_status=default_status)
    if failed_path and _has_stop_loss_signal(payload):
        status = "stop_loss"
    candidate_id = _candidate_id(payload=payload, source=source, status=status)
    failed_path_refs = _refs(payload, "failed_path_refs", "failed_path_ref")
    if failed_path and not failed_path_refs:
        failed_path_refs = _dedupe_text([_text(payload.get("ref")), _text(payload.get("write_id")), candidate_id])
    return _drop_empty(
        {
            "candidate_id": candidate_id,
            "status": status,
            "source_key": source,
            "candidate_kind": "failed_path" if failed_path else _text(payload.get("candidate_kind")),
            "title": _text(payload.get("title") or payload.get("name")),
            "summary": _text(payload.get("summary") or payload.get("reason") or payload.get("decision_reason")),
            "route_impact": _text(payload.get("route_impact") or payload.get("next_route")),
            "failure_scope": _text(payload.get("failure_scope") or payload.get("scope")),
            "missing_evidence_refs": _refs(payload, "missing_evidence_refs", "missing_evidence"),
            "evidence_refs": _refs(payload, "evidence_refs", "source_refs", "result_refs"),
            "negative_result_refs": _refs(payload, "negative_result_refs", "negative_refs"),
            "failed_path_refs": failed_path_refs,
            "route_back_refs": _refs(payload, "route_back_refs", "route_back_ref", "route_back"),
            "writeback_refs": _packet_writeback_refs(payload),
            "signals": _signals(payload=payload, status=status),
            "authority_boundary": "advisory_stage_frontier_ref_not_progress_authority",
        }
    )


def _status(payload: Mapping[str, Any], *, default_status: str) -> str:
    for key in ("frontier_status", "candidate_status", "status", "decision", "route_meaning"):
        value = _text(payload.get(key)).lower().replace("-", "_").replace(" ", "_")
        if value in FRONTIER_STATUSES:
            return value
        if value in {"test", "in_test", "in_flight", "debug", "exploit", "fusion"}:
            return "testing"
        if value in {"reject", "failed", "negative"}:
            return "rejected"
        if value in {"defer", "parked", "parking_lot"}:
            return "deferred"
        if value in {"stop", "stoploss", "stop_loss_candidate", "terminate"}:
            return "stop_loss"
        if value in {"explore", "candidate", "open"}:
            return "active"
    return default_status


def _candidate_id(*, payload: Mapping[str, Any], source: str, status: str) -> str:
    explicit = _text(
        payload.get("candidate_id")
        or payload.get("path_id")
        or payload.get("route_id")
        or payload.get("write_id")
        or payload.get("ref")
        or payload.get("id")
    )
    return explicit or f"{source}:{status}:{_fingerprint(payload)}"


def _signals(*, payload: Mapping[str, Any], status: str) -> list[str]:
    signals = []
    if status == "stop_loss" or _has_stop_loss_signal(payload):
        signals.append("stop_loss")
    if _refs(payload, "missing_evidence_refs", "missing_evidence"):
        signals.append("missing_evidence")
    if _refs(payload, "negative_result_refs", "negative_refs"):
        signals.append("negative_result")
    route_impact = _text(payload.get("route_impact") or payload.get("next_route"))
    if route_impact:
        signals.append(f"route_impact:{route_impact}")
    failure_scope = _text(payload.get("failure_scope") or payload.get("scope"))
    if failure_scope:
        signals.append(f"failure_scope:{failure_scope}")
    decision = _text(payload.get("decision") or payload.get("claim_boundary_decision"))
    if "downgrade" in decision.lower():
        signals.append("claim_downgrade")
    return _dedupe_text(signals)


def _has_stop_loss_signal(payload: Mapping[str, Any]) -> bool:
    if payload.get("stop_loss") is True or payload.get("stop_loss_candidate") is True:
        return True
    rendered = " ".join(
        _text(payload.get(key)).lower()
        for key in ("status", "decision", "route_impact", "next_route", "reason", "candidate_kind")
    )
    return any(token in rendered for token in ("stop_loss", "stop-loss", "stop loss", "terminate"))


def _summary(
    *,
    candidates: Sequence[Mapping[str, Any]],
    writeback_refs: Sequence[Mapping[str, Any]],
    rollback_policy: Mapping[str, Any],
    next_hypothesis_suggestion: str,
) -> dict[str, Any]:
    counts = {status: sum(1 for item in candidates if item.get("status") == status) for status in FRONTIER_STATUSES}
    return {
        "surface": SUMMARY_SURFACE,
        "status": "has_candidates" if candidates else "empty",
        "counts_by_status": counts,
        "candidate_count": len(candidates),
        "failed_path_ref_count": sum(len(item.get("failed_path_refs") or []) for item in candidates),
        "negative_result_ref_count": sum(len(item.get("negative_result_refs") or []) for item in candidates),
        "route_back_ref_count": sum(len(item.get("route_back_refs") or []) for item in candidates),
        "memory_writeback_ref_count": len(writeback_refs),
        "next_hypothesis_suggestion": next_hypothesis_suggestion,
        "rollback_target_suggestions": list(rollback_policy.get("suggested_targets") or []),
        "authority_boundary": frontier_board_authority_boundary(),
    }


def _candidate_ref(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return _drop_empty(
        {
            "ref_kind": "research_frontier_candidate_ref",
            "candidate_id": _text(candidate.get("candidate_id")),
            "status": _text(candidate.get("status")),
            "source_key": _text(candidate.get("source_key")),
            "route_impact": _text(candidate.get("route_impact")),
            "failure_scope": _text(candidate.get("failure_scope")),
            "evidence_refs": _text_list(candidate.get("evidence_refs")),
            "negative_result_refs": _text_list(candidate.get("negative_result_refs")),
            "failed_path_refs": _text_list(candidate.get("failed_path_refs")),
            "route_back_refs": _text_list(candidate.get("route_back_refs")),
            "signals": _text_list(candidate.get("signals")),
            "authority_boundary": "ref_only_not_stage_completion_or_next_action_authority",
        }
    )


def _rollback_policy(
    *,
    stage: str,
    packet: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    rules = [
        _rule(
            "stop_loss",
            "07-independent_review_and_revision",
            "formal stop-loss remains a quality review or controller decision input before package handoff",
        ),
        _rule(
            "claim_downgrade",
            "05-evidence_synthesis",
            "claim downgrade must revisit evidence synthesis before manuscript wording continues",
        ),
        _rule(
            "missing_evidence",
            "04-analysis_execution",
            "missing evidence needs bounded analysis execution before claim expansion",
        ),
        _rule(
            "route_impact:return_to_scout",
            "01-study_intake",
            "frontier reset returns to study intake and clinical question framing",
        ),
        _rule(
            "route_impact:switch_line",
            "02-protocol_and_analysis_plan",
            "candidate line switch belongs to protocol and analysis-plan selection",
        ),
        _rule(
            "failure_scope:stage_local",
            _pack_target_for_stage(stage),
            "stage-local failure can retry inside the matching 8-stage pack lane",
        ),
    ]
    suggestions = []
    for candidate in candidates:
        for signal in _text_list(candidate.get("signals")):
            target = _target_for_signal(signal=signal, stage=stage)
            if target:
                suggestions.append(
                    {
                        "signal": signal,
                        "candidate_id": _text(candidate.get("candidate_id")),
                        "suggested_target_stage": target[0],
                        "reason": target[1],
                        "advisory_only": True,
                    }
                )
    if _text_list(packet.get("literature_gaps")) or _refs(_mapping(packet.get("citation_readiness")), "stale_refs"):
        suggestions.append(
            {
                "signal": "missing_evidence",
                "candidate_id": "",
                "suggested_target_stage": "05-evidence_synthesis",
                "reason": "literature or citation gaps need evidence synthesis before claim expansion",
                "advisory_only": True,
            }
        )
    return {
        "surface": ROLLBACK_POLICY_SURFACE,
        "advisory_only": True,
        "can_control_progress": False,
        "pack_stage_set": list(PACK_ROLLBACK_TARGETS),
        "pack_advisory_mapping": _pack_advisory_mapping(),
        "rules": rules,
        "suggested_targets": _dedupe_dicts(suggestions),
        "authority_boundary": frontier_board_authority_boundary(),
    }


def _rule(signal: str, target_stage: str, reason: str) -> dict[str, str]:
    return {"signal": signal, "suggested_target_stage": target_stage, "reason": reason}


def _target_for_signal(*, signal: str, stage: str) -> tuple[str, str] | None:
    normalized_signal = signal.replace("-", "_").replace(" ", "_")
    if signal == "stop_loss":
        return (
            "07-independent_review_and_revision",
            "formal stop-loss remains a quality review or controller decision input before package handoff",
        )
    if signal == "claim_downgrade":
        return (
            "05-evidence_synthesis",
            "claim downgrade must revisit evidence synthesis before manuscript wording continues",
        )
    if signal == "missing_evidence":
        return (
            "04-analysis_execution",
            "missing evidence needs bounded analysis execution before claim expansion",
        )
    if signal.startswith("route_impact:return_to_scout"):
        return ("01-study_intake", "frontier reset returns to study intake and clinical question framing")
    if signal.startswith("route_impact:switch_line"):
        return (
            "02-protocol_and_analysis_plan",
            "candidate line switch belongs to protocol and analysis-plan selection",
        )
    for prefix in ("failure_scope:", "route_impact:"):
        if normalized_signal.startswith(prefix):
            target = FAILURE_SCOPE_TARGETS.get(normalized_signal.removeprefix(prefix))
            if target:
                return target
    if signal == "failure_scope:stage_local":
        return (_pack_target_for_stage(stage), "stage-local failure can retry inside the matching 8-stage pack lane")
    return None


def _pack_target_for_stage(stage: str) -> str:
    normalized = _text(stage)
    if normalized in PACK_ROLLBACK_TARGETS:
        return normalized
    return STAGE_TO_PACK_TARGET.get(normalized, "05-evidence_synthesis")


def _pack_advisory_mapping() -> list[dict[str, str]]:
    return [
        {
            "target_stage": "01-study_intake",
            "advisory_role": "return to study question, source fit, cohort feasibility, or intake boundary",
        },
        {
            "target_stage": "02-protocol_and_analysis_plan",
            "advisory_role": "revise candidate line, protocol, endpoint, comparator, or analysis plan",
        },
        {
            "target_stage": "03-data_asset_and_cohort_build",
            "advisory_role": "repair data asset, cohort, inclusion/exclusion, or endpoint construction",
        },
        {
            "target_stage": "04-analysis_execution",
            "advisory_role": "rerun bounded analysis, failed comparator checks, or evidence-generating repair",
        },
        {
            "target_stage": "05-evidence_synthesis",
            "advisory_role": "reconcile claim boundary, literature gaps, citation readiness, and evidence refs",
        },
        {
            "target_stage": "06-manuscript_authoring",
            "advisory_role": "adjust manuscript wording, claim expression, and paper-native presentation",
        },
        {
            "target_stage": "07-independent_review_and_revision",
            "advisory_role": "route reviewer, stop-loss, downgrade, or revision risk before handoff",
        },
        {
            "target_stage": "08-publication_package_handoff",
            "advisory_role": "check package handoff, declarations, freshness, and submission-readiness inputs",
        },
    ]


def _opl_projection(
    *,
    summary: Mapping[str, Any],
    refs: Sequence[Mapping[str, Any]],
    writeback_refs: Sequence[Mapping[str, Any]],
    rollback_policy: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface": OPL_PROJECTION_SURFACE,
        "consumer": "OPL/Aion",
        "display_role": "refs_and_summary_only",
        "body_included": False,
        "can_read_memory_body": False,
        "can_write_memory_body": False,
        "summary": dict(summary),
        "frontier_board_refs": [dict(ref) for ref in refs],
        "memory_writeback_refs": [dict(ref) for ref in writeback_refs],
        "rollback_target_suggestions": list(rollback_policy.get("suggested_targets") or []),
        "authority_boundary": frontier_board_authority_boundary(),
    }


def _next_hypothesis(*, packet: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]]) -> str:
    direct = _text(
        packet.get("next_hypothesis_suggestion")
        or packet.get("next_hypothesis")
        or packet.get("next_hypothesis_ref")
    )
    if direct:
        return direct
    for key in CONTAINER_KEYS:
        container = _mapping(packet.get(key))
        direct = _text(container.get("next_hypothesis_suggestion") or container.get("next_hypothesis"))
        if direct:
            return direct
    for candidate in candidates:
        if _text(candidate.get("status")) in {"active", "testing"}:
            return _text(candidate.get("candidate_id"))
    return ""


def _selected_frontier_suggestion(
    *,
    board: Mapping[str, Any],
    target_stage: str,
    candidate_id: str | None,
    signal: str | None,
) -> dict[str, Any]:
    requested_candidate = _text(candidate_id)
    requested_signal = _text(signal)
    for suggestion in _frontier_suggestions(board):
        suggestion_target = _pack_target_for_stage(
            _text(
                suggestion.get("suggested_target_stage")
                or suggestion.get("target_stage_id")
                or suggestion.get("rollback_target_ref")
            )
        )
        if suggestion_target != target_stage:
            continue
        if requested_candidate and _text(suggestion.get("candidate_id")) != requested_candidate:
            continue
        if requested_signal and _text(suggestion.get("signal")) != requested_signal:
            continue
        return suggestion
    return {}


def _frontier_suggestions(board: Mapping[str, Any]) -> list[dict[str, Any]]:
    return _dedupe_dicts(
        [
            *_mapping_list(board.get("rollback_target_suggestions")),
            *_mapping_list(_mapping(board.get("summary")).get("rollback_target_suggestions")),
            *_mapping_list(_mapping(board.get("rollback_target_policy")).get("suggested_targets")),
            *_mapping_list(_mapping(board.get("opl_refs_only_projection")).get("rollback_target_suggestions")),
        ]
    )


def _frontier_advisory_ref(
    *,
    board: Mapping[str, Any],
    suggestion: Mapping[str, Any],
    target_stage: str,
) -> str:
    return "research-frontier-advisory:" + _fingerprint(
        {
            "study_id": board.get("study_id"),
            "stage": board.get("stage"),
            "source_fingerprint": board.get("source_fingerprint"),
            "candidate_id": suggestion.get("candidate_id"),
            "signal": suggestion.get("signal"),
            "target_stage": target_stage,
        }
    )


def _candidate_writeback_refs(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(ref) for candidate in candidates for ref in _mapping_list(candidate.get("writeback_refs"))]


def _packet_writeback_refs(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs = []
    for key in WRITEBACK_REF_KEYS:
        refs.extend(_mapping_list(packet.get(key)))
    refs.extend(_refs_from_writes(packet.get("proposed_writes"), status="proposed"))
    refs.extend(_refs_from_writes(packet.get("accepted_writes"), status="accepted"))
    refs.extend(_refs_from_writes(packet.get("rejected_writes"), status="rejected"))
    return _dedupe_dicts([_writeback_ref(ref) for ref in refs])


def _refs_from_writes(value: object, *, status: str) -> list[dict[str, Any]]:
    refs = []
    for write in _mapping_list(value):
        if _text(write.get("destination")) != "workspace_research_memory_proposal":
            continue
        payload = _mapping(write.get("payload"))
        refs.append(
            _drop_empty(
                {
                    "write_id": _text(write.get("write_id")),
                    "memory_id": _text(write.get("memory_id")),
                    "route_family": _text(payload.get("route_family")),
                    "stage_applicability": _text_list(payload.get("stage_applicability")),
                    "proposal_ref": _text(write.get("proposal_ref")),
                    "receipt_ref": _text(write.get("receipt_ref")),
                    "source_receipt_ref": _text(write.get("source_receipt_ref")),
                    "writeback_receipt_ref": _text(write.get("writeback_receipt_ref")),
                    "status": status,
                    "authority_boundary": "ref_only_not_memory_body_or_writeback_authority",
                }
            )
        )
    return refs


def _writeback_ref(ref: Mapping[str, Any]) -> dict[str, Any]:
    return _drop_empty(
        {
            "write_id": _text(ref.get("write_id")),
            "memory_id": _text(ref.get("memory_id")),
            "route_family": _text(ref.get("route_family")),
            "stage_applicability": _text_list(ref.get("stage_applicability")),
            "proposal_ref": _text(ref.get("proposal_ref")),
            "receipt_ref": _text(ref.get("receipt_ref")),
            "source_receipt_ref": _text(ref.get("source_receipt_ref")),
            "writeback_receipt_ref": _text(ref.get("writeback_receipt_ref")),
            "status": _text(ref.get("status")),
            "authority_boundary": "ref_only_not_memory_body_or_writeback_authority",
        }
    )


def _refs(payload: Mapping[str, Any], *keys: str) -> list[str]:
    refs = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            refs.append(_text(value))
        else:
            refs.extend(_text_list(value))
    return _dedupe_text(refs)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text(value: object) -> str:
    return str(value or "").strip()


def _text_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [_text(item) for item in value if _text(item)]


def _dedupe_text(items: Sequence[str]) -> list[str]:
    return list(dict.fromkeys([item for item in items if item]))


def _dedupe_dicts(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        key = json.dumps(dict(item), ensure_ascii=False, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            deduped.append(dict(item))
    return deduped


def _dedupe_candidates(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for candidate in candidates:
        key = (_text(candidate.get("candidate_id")), _text(candidate.get("status")))
        if key not in seen:
            seen.add(key)
            deduped.append(dict(candidate))
    return deduped


def _drop_empty(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in ("", None, [], {})}


def _required_text(field: str, value: object) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"{field} must be a non-empty string")
    return text


def _fingerprint(payload: object) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


__all__ = [
    "adopt_frontier_route_back_terminal_decision",
    "build_research_frontier_board",
    "frontier_board_packet_fields",
    "frontier_board_authority_boundary",
]
