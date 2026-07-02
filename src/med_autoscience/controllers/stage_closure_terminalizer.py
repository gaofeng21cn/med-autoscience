from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


SURFACE_KIND = "mas_stage_closure_decision"
SCHEMA_VERSION = 1

OUTCOME_OWNER_RECEIPT = "owner_receipt"
OUTCOME_TYPED_BLOCKER = "typed_blocker"
OUTCOME_HUMAN_GATE = "human_gate"
OUTCOME_NEXT_STAGE_TRANSITION = "next_stage_transition"
ALLOWED_OUTCOME_KINDS = frozenset(
    {
        OUTCOME_OWNER_RECEIPT,
        OUTCOME_TYPED_BLOCKER,
        OUTCOME_HUMAN_GATE,
        OUTCOME_NEXT_STAGE_TRANSITION,
    }
)

QUALITY_REPAIRABLE_BLOCKERS = frozenset(
    {
        "reviewer_first_concerns_unresolved",
        "claim_evidence_consistency_failed",
        "submission_hardening_incomplete",
        "forbidden_manuscript_terminology",
        "submission_surface_qc_failure_present",
        "medical_publication_surface_blocked",
        "medical_journal_prose_quality_blocked",
        "manuscript_story_surface_delta_missing",
        "typed_closeout_packet_required",
    }
)

MIRROR_SYNC_BLOCKERS = frozenset(
    {
        "stale_study_delivery_mirror",
        "delivery_manifest_source_changed",
        "current_package_missing",
        "current_package_stale",
        "study_delivery_current_package_missing",
        "manuscript_current_package_missing",
        "manuscript_current_package_stale",
    }
)

SUBMISSION_AUTHORITY_BLOCKERS = frozenset(
    {
        "stale_submission_minimal_authority",
        "authority_snapshot_missing",
        "bundle_build_allowed_missing",
        "bundle_build_allowed_false",
        "submission_ready_authority_missing",
        "paper_write_allowed_missing",
    }
)

HARD_AUTHORITY_BLOCKERS = frozenset(
    {
        "source_data_missing",
        "privacy_ethics_permission_boundary",
        "credential_boundary",
        "forbidden_write_target",
        "irreversible_external_submission_authorization_required",
    }
)

ROUTE_BACK_CHECKPOINT_BLOCKERS = frozenset(
    {
        "accepted_submission_milestone_candidate",
        "paper_mission_stage_route_domain_gate_pending",
        "route_back",
    }
)

FORBIDDEN_INTERPRETATIONS = [
    "provider_completion_is_domain_ready",
    "candidate_is_submission_ready",
    "inspection_package_is_submission_ready",
    "accepted_submission_milestone_candidate_is_durable_stop",
    "blocked_gate_is_final_without_typed_blocker_or_human_gate",
    "bundle_build_allowed_false_blocks_current_package_mirror",
    "continue_same_stage_without_semantic_delta",
    "opl_completed_is_paper_progress",
    "focused_tests_passed_is_paper_progress",
    "queue_empty_is_stage_closed",
]


def terminalize_stage_closure(
    *,
    study_id: str,
    stage_id: str,
    work_unit_id: str,
    work_unit_fingerprint: str | None = None,
    identity: Mapping[str, Any] | None = None,
    inputs: Mapping[str, Any] | None = None,
    gate_replay: Mapping[str, Any] | None = None,
    delivery_readback: Mapping[str, Any] | None = None,
    opl_closeout: Mapping[str, Any] | None = None,
    semantic_delta: Mapping[str, Any] | None = None,
    repair_budget: Mapping[str, Any] | None = None,
    previous_signature: str | None = None,
) -> dict[str, Any]:
    """Reduce stage closeout evidence to one MAS-consumable terminal outcome.

    The reducer is intentionally side-effect free: it does not write owner receipts,
    typed blockers, human gates, packages, Yang workspace files, or runtime queues.
    """

    gate = _mapping(gate_replay)
    delivery = _mapping(delivery_readback)
    closeout = _closeout_with_explicit_accounting(_mapping(opl_closeout))
    delta = _semantic_delta(semantic_delta)
    budget = _repair_budget(repair_budget)
    blockers = _unique_texts(
        [
            *_blockers_from_gate(gate),
            *_blockers_from_delivery(delivery),
            *_blockers_from_closeout(closeout),
        ]
    )
    classes = classify_stage_closure_blockers(blockers)
    signature = stage_closure_signature(
        study_id=study_id,
        stage_id=stage_id,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        blockers=blockers,
        semantic_delta=delta,
    )
    repeated_without_delta = previous_signature == signature and not _has_semantic_delta(delta)
    outcome = _select_outcome(
        blockers=blockers,
        classes=classes,
        gate=gate,
        delivery=delivery,
        semantic_delta=delta,
        repair_budget=budget,
        repeated_without_delta=repeated_without_delta,
    )
    observability_gaps = _observability_gaps(closeout)
    decision = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "stage_id": stage_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "decision_signature": signature,
        "identity": _compact(_mapping(identity)),
        "inputs": _compact(_mapping(inputs)),
        "semantic_delta": delta,
        "gate_replay": _input_summary(gate, status_key="gate_replay_status"),
        "delivery_readback": _delivery_summary(delivery),
        "opl_closeout": _input_summary(closeout, status_key="status"),
        "blocker_taxonomy": classes,
        "known_blockers": blockers,
        "repair_budget": budget,
        "repeated_without_semantic_delta": repeated_without_delta,
        "observability_gaps": observability_gaps,
        "outcome": outcome,
        "forbidden_interpretations": FORBIDDEN_INTERPRETATIONS,
        "authority_boundary": {
            "authority_materialized": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_submission_ready_package": False,
            "writes_runtime_queue_or_provider_attempt": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
        },
    }
    return _compact(decision)


def classify_stage_closure_blockers(blockers: Sequence[str] | None) -> dict[str, list[str]]:
    result = {
        "quality_repairable": [],
        "mirror_sync": [],
        "submission_authority": [],
        "hard_authority": [],
        "route_back_checkpoint": [],
        "unknown": [],
    }
    for blocker in _unique_texts(blockers or []):
        if blocker in QUALITY_REPAIRABLE_BLOCKERS:
            result["quality_repairable"].append(blocker)
        elif blocker in MIRROR_SYNC_BLOCKERS:
            result["mirror_sync"].append(blocker)
        elif blocker in SUBMISSION_AUTHORITY_BLOCKERS:
            result["submission_authority"].append(blocker)
        elif blocker in HARD_AUTHORITY_BLOCKERS:
            result["hard_authority"].append(blocker)
        elif _is_route_back_checkpoint_blocker(blocker):
            result["route_back_checkpoint"].append(blocker)
        else:
            result["unknown"].append(blocker)
    return result


def stage_closure_decision_projection(
    *,
    readback: Mapping[str, Any],
    handoff: Mapping[str, Any] | None = None,
    opl_runtime_submission: Mapping[str, Any] | None = None,
    consumption_ledger_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    explicit = _first_mapping(
        _mapping(readback.get("stage_closure_decision")),
        _mapping(_mapping(readback.get("paper_mission_transaction")).get("stage_closure_decision")),
        _mapping(_mapping(readback.get("consume_readback")).get("stage_closure_decision")),
        _mapping(_mapping(consumption_ledger_readback).get("stage_closure_decision")),
    )
    if explicit and _stage_closure_outcome_kind(explicit) in ALLOWED_OUTCOME_KINDS:
        return _normalize_stage_closure_decision(
            explicit,
            fallback_ref=_stage_closure_decision_ref(readback),
        )
    if not _readback_needs_stage_closure_decision(
        readback=readback,
        handoff=handoff,
        opl_runtime_submission=opl_runtime_submission,
        consumption_ledger_readback=consumption_ledger_readback,
    ):
        return {}
    return _missing_stage_closure_decision(
        readback=readback,
        handoff=handoff,
        opl_runtime_submission=opl_runtime_submission,
        consumption_ledger_readback=consumption_ledger_readback,
    )


def stage_closure_decision_missing(decision: Mapping[str, Any]) -> bool:
    return _text(decision.get("projection_status")) == "stage_closure_decision_missing"


def stage_closure_signature(
    *,
    study_id: str,
    stage_id: str,
    work_unit_id: str,
    work_unit_fingerprint: str | None,
    blockers: Sequence[str],
    semantic_delta: Mapping[str, Any],
) -> str:
    payload = {
        "study_id": study_id,
        "stage_id": stage_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "blockers": sorted(_unique_texts(blockers)),
        "semantic_delta_refs": _semantic_delta_refs(semantic_delta),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _stage_closure_outcome_kind(payload: Mapping[str, Any]) -> str | None:
    outcome = _mapping(payload.get("outcome"))
    return _first_text(outcome.get("kind"), payload.get("outcome_kind"))


def _normalize_stage_closure_decision(
    payload: Mapping[str, Any],
    *,
    fallback_ref: str | None,
) -> dict[str, Any]:
    outcome = _mapping(payload.get("outcome"))
    blockers = _texts(payload.get("known_blockers"))
    outcome = _normalize_legacy_checkpoint_outcome(outcome=outcome, blockers=blockers)
    outcome_kind = _first_text(outcome.get("kind"), _stage_closure_outcome_kind(payload))
    return _compact(
        {
            **dict(payload),
            "surface_kind": _first_text(payload.get("surface_kind"), SURFACE_KIND),
            "decision_ref": _first_text(
                payload.get("decision_ref"),
                payload.get("stage_closure_decision_ref"),
                fallback_ref,
            ),
            "outcome": _compact({**outcome, "kind": outcome_kind}),
            "outcome_kind": outcome_kind,
            "repair_budget": _first_mapping(
                _mapping(payload.get("repair_budget")),
                _mapping(payload.get("route_back_budget")),
            )
            or None,
            "package_kind": _text(payload.get("package_kind")),
            "known_blockers": blockers,
            "projection_status": "terminalizer_outcome_observed",
            "target_ref": "docs/runtime/designs/stage_closure_terminalizer_target.md",
        }
    )


def _readback_needs_stage_closure_decision(
    *,
    readback: Mapping[str, Any],
    handoff: Mapping[str, Any] | None,
    opl_runtime_submission: Mapping[str, Any] | None,
    consumption_ledger_readback: Mapping[str, Any] | None = None,
) -> bool:
    consume_result = _mapping(_mapping(consumption_ledger_readback).get("consume_result"))
    if _text(consume_result.get("paper_facing_delta_ref")) is not None:
        return False
    decision = _mapping(readback.get("stage_terminal_decision")) or _mapping(
        _mapping(readback.get("paper_mission_transaction")).get("stage_terminal_decision")
    )
    decision_kind = _text(decision.get("decision_kind"))
    if decision_kind in {"typed_blocker", "human_gate", "mission_complete"}:
        return False
    if decision_kind in {"route_back", "continue_same_stage"}:
        return True
    terms = {
        _text(readback.get("consume_candidate_status")),
        _text(readback.get("transaction_state")),
        _text(readback.get("opl_runtime_readback_status")),
        _text(_mapping(readback.get("opl_runtime_carrier_readback")).get("carrier_status")),
        _text(_mapping(opl_runtime_submission).get("status")),
        _text(_mapping(handoff).get("route_command_kind")),
    }
    return any(
        term
        in {
            "accepted_submission_milestone_candidate",
            "route_back",
            "continue_same_stage",
            "opl_runtime_terminal_readback_observed",
            "submitted",
            "idempotent_noop",
        }
        for term in terms
        if term is not None
    )


def _missing_stage_closure_decision(
    *,
    readback: Mapping[str, Any],
    handoff: Mapping[str, Any] | None,
    opl_runtime_submission: Mapping[str, Any] | None,
    consumption_ledger_readback: Mapping[str, Any] | None,
) -> dict[str, Any]:
    decision = _mapping(readback.get("stage_terminal_decision")) or _mapping(
        _mapping(readback.get("paper_mission_transaction")).get("stage_terminal_decision")
    )
    return _compact(
        {
            "surface_kind": "mas_stage_closure_decision_projection",
            "projection_status": "stage_closure_decision_missing",
            "missing": True,
            "target_ref": "docs/runtime/designs/stage_closure_terminalizer_target.md",
            "decision_ref": _stage_closure_decision_ref(readback),
            "outcome": {
                "kind": "stage_closure_decision_missing",
                "authority_materialized": False,
                "next_owner": "MedAutoScience.stage_closure_terminalizer",
                "next_action": "run_stage_closure_terminalizer",
            },
            "outcome_kind": "stage_closure_decision_missing",
            "repair_budget": _first_mapping(
                _mapping(readback.get("route_back_budget")),
                _mapping(decision.get("repair_budget")),
            )
            or None,
            "package_kind": _first_text(
                readback.get("package_kind"),
                _mapping(readback.get("candidate_manifest")).get("package_kind"),
                _mapping(readback.get("output_manifest")).get("milestone_kind"),
            ),
            "known_blockers": _stage_closure_known_blockers(
                readback=readback,
                handoff=handoff,
                opl_runtime_submission=opl_runtime_submission,
                consumption_ledger_readback=consumption_ledger_readback,
            ),
            "forbidden_interpretations": [
                "accepted_submission_milestone_candidate_is_durable_final",
                "bundle_build_allowed_false_is_durable_final",
                "continue_same_stage_without_terminalizer_outcome",
            ],
            "fail_closed": True,
            "can_continue_same_stage": False,
            "can_claim_durable_final": False,
            "can_claim_paper_progress": False,
            "authority_materialized": False,
        }
    )


def _stage_closure_decision_ref(readback: Mapping[str, Any]) -> str | None:
    explicit = _first_text(
        readback.get("stage_closure_decision_ref"),
        _mapping(readback.get("stage_closure_decision")).get("decision_ref"),
    )
    if explicit is not None:
        return explicit
    transaction_ref = _first_text(
        _mapping(readback.get("paper_mission_transaction")).get("transaction_id"),
        readback.get("paper_mission_transaction_ref"),
    )
    return f"{transaction_ref}#stage_closure_decision" if transaction_ref else None


def _stage_closure_known_blockers(
    *,
    readback: Mapping[str, Any],
    handoff: Mapping[str, Any] | None,
    opl_runtime_submission: Mapping[str, Any] | None,
    consumption_ledger_readback: Mapping[str, Any] | None,
) -> list[str]:
    decision = _mapping(readback.get("stage_terminal_decision"))
    carrier = _mapping(readback.get("opl_runtime_carrier_readback"))
    return _unique_texts(
        [
            readback.get("blocked_reason"),
            readback.get("consume_candidate_status"),
            decision.get("reason"),
            decision.get("blocker_id"),
            _mapping(readback.get("terminal_owner_gate")).get("blocked_reason"),
            _mapping(handoff).get("blocked_reason"),
            _mapping(opl_runtime_submission).get("reason"),
            _mapping(consumption_ledger_readback).get("consume_candidate_status"),
            carrier.get("blocked_reason"),
        ]
    )


def _select_outcome(
    *,
    blockers: list[str],
    classes: Mapping[str, Sequence[str]],
    gate: Mapping[str, Any],
    delivery: Mapping[str, Any],
    semantic_delta: Mapping[str, Any],
    repair_budget: Mapping[str, Any],
    repeated_without_delta: bool,
) -> dict[str, Any]:
    gate_status = _text(gate.get("gate_replay_status")) or _text(gate.get("status"))
    mirror_blockers = list(classes.get("mirror_sync") or [])
    submission_authority_blockers = list(classes.get("submission_authority") or [])
    quality_blockers = list(classes.get("quality_repairable") or [])
    hard_authority_blockers = list(classes.get("hard_authority") or [])
    route_back_checkpoint_blockers = list(classes.get("route_back_checkpoint") or [])
    unknown_blockers = list(classes.get("unknown") or [])
    budget_status = _text(repair_budget.get("repair_budget_status"))

    if hard_authority_blockers:
        return _typed_blocker_outcome(
            blocker_type="hard_authority_blocker",
            blockers=hard_authority_blockers,
            next_owner="MedAutoScience",
            resume_condition="resolve hard authority boundary before stage closure can proceed",
        )
    if route_back_checkpoint_blockers and budget_status == "exhausted":
        return {
            "kind": OUTCOME_NEXT_STAGE_TRANSITION,
            "transition_kind": "degraded_handoff",
            "next_owner": "human_review",
            "next_action": "review_degraded_handoff_package",
            "package_kind": "degraded_handoff_package",
            "can_submit": False,
            "requires_bundle_build_allowed": False,
            "known_blockers": blockers,
            "resume_condition": (
                "route-back checkpoint consumed the repair budget; ship a "
                "bounded low-quality handoff package or record a human/MAS decision"
            ),
            "authority_materialized": False,
        }
    if route_back_checkpoint_blockers and repeated_without_delta:
        return _typed_blocker_outcome(
            blocker_type="route_back_checkpoint_without_semantic_delta",
            blockers=route_back_checkpoint_blockers,
            next_owner="MedAutoScience",
            resume_condition=(
                "stop redriving the same PaperMission stage; materialize a degraded "
                "handoff, owner decision, human gate, or typed blocker"
            ),
        )
    if route_back_checkpoint_blockers and not hard_authority_blockers:
        return {
            "kind": OUTCOME_NEXT_STAGE_TRANSITION,
            "transition_kind": "route_back_candidate_checkpoint",
            "next_owner": "MedAutoScience",
            "next_action": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
            "package_kind": _text(delivery.get("package_kind")),
            "can_submit": False,
            "requires_bundle_build_allowed": False,
            "known_blockers": blockers,
            "resume_condition": (
                "route-back candidate checkpoint must be consumed into owner "
                "receipt, typed blocker, human gate, or next stage transition"
            ),
            "authority_materialized": False,
        }
    if unknown_blockers and not (quality_blockers or mirror_blockers or submission_authority_blockers):
        return _typed_blocker_outcome(
            blocker_type="unclassified_stage_closure_blocker",
            blockers=unknown_blockers,
            next_owner="MedAutoScience",
            resume_condition="classify blocker into MAS stage closure taxonomy",
        )
    if mirror_blockers and not quality_blockers and not hard_authority_blockers:
        return {
            "kind": OUTCOME_NEXT_STAGE_TRANSITION,
            "transition_kind": "current_package_mirror_sync",
            "next_owner": "MedAutoScience",
            "next_action": "sync_current_package_mirror",
            "package_kind": "current_package",
            "can_submit": False,
            "requires_bundle_build_allowed": False,
            "known_blockers": blockers,
            "resume_condition": "refresh human-facing current_package mirror from current source package",
            "authority_materialized": False,
        }
    if quality_blockers and budget_status == "exhausted":
        return {
            "kind": OUTCOME_NEXT_STAGE_TRANSITION,
            "transition_kind": "degraded_handoff",
            "next_owner": "human_review",
            "next_action": "review_degraded_handoff_package",
            "package_kind": "degraded_handoff_package",
            "can_submit": False,
            "requires_bundle_build_allowed": False,
            "known_blockers": blockers,
            "resume_condition": "human or MAS owner accepts carry-forward risk, narrows scope, or requests targeted repair",
            "authority_materialized": False,
        }
    if repeated_without_delta:
        return _typed_blocker_outcome(
            blocker_type="same_signature_without_semantic_delta",
            blockers=blockers,
            next_owner="MedAutoScience",
            resume_condition="produce a paper-facing delta, owner decision, human gate, or scoped carry-forward decision before retry",
        )
    if quality_blockers:
        return {
            "kind": OUTCOME_NEXT_STAGE_TRANSITION,
            "transition_kind": "bounded_quality_repair_iteration",
            "next_owner": "analysis-campaign",
            "next_action": "run_quality_repair_batch",
            "package_kind": "current_package" if mirror_blockers else None,
            "can_submit": False,
            "requires_bundle_build_allowed": False,
            "known_blockers": blockers,
            "resume_condition": "produce a new semantic repair delta or terminal owner answer",
            "authority_materialized": False,
        }
    if submission_authority_blockers:
        return _human_gate_outcome(
            gate_type="submission_authority_required",
            blockers=submission_authority_blockers,
            resume_condition="MAS owner or human authorizes submission-ready package authority, or records a typed blocker",
        )
    if gate_status in {"passed", "clear", "cleared"} or not blockers:
        return {
            "kind": OUTCOME_OWNER_RECEIPT,
            "next_owner": "MedAutoScience",
            "next_action": "materialize_stage_owner_receipt_or_next_stage_transition",
            "package_kind": _text(delivery.get("package_kind")),
            "can_submit": delivery.get("can_submit") is True,
            "quality_gate_status": gate_status,
            "freshness": _text(delivery.get("freshness")),
            "generated_from_current_source": delivery.get("generated_from_current_source") is True,
            "source_signature": _text(delivery.get("source_signature")),
            "root": _text(delivery.get("root")),
            "zip_path": _text(delivery.get("zip_path")),
            "zip_exists": delivery.get("zip_exists") is True,
            "known_blockers": blockers,
            "resume_condition": "owner receipt materialization remains MAS authority action",
            "authority_materialized": False,
        }
    return _typed_blocker_outcome(
        blocker_type="stage_closure_unresolved",
        blockers=blockers,
        next_owner="MedAutoScience",
        resume_condition="stage closure reducer could not select a legal next transition",
    )


def _typed_blocker_outcome(
    *,
    blocker_type: str,
    blockers: Sequence[str],
    next_owner: str,
    resume_condition: str,
) -> dict[str, Any]:
    return {
        "kind": OUTCOME_TYPED_BLOCKER,
        "blocker_type": blocker_type,
        "next_owner": next_owner,
        "next_action": "materialize_typed_blocker_or_route_redesign",
        "known_blockers": _unique_texts(blockers),
        "resume_condition": resume_condition,
        "authority_materialized": False,
    }


def _human_gate_outcome(
    *,
    gate_type: str,
    blockers: Sequence[str],
    resume_condition: str,
) -> dict[str, Any]:
    return {
        "kind": OUTCOME_HUMAN_GATE,
        "gate_type": gate_type,
        "next_owner": "human",
        "next_action": "answer_stage_closure_authority_gate",
        "known_blockers": _unique_texts(blockers),
        "resume_condition": resume_condition,
        "authority_materialized": False,
    }


def _is_route_back_checkpoint_blocker(blocker: str) -> bool:
    return (
        blocker in ROUTE_BACK_CHECKPOINT_BLOCKERS
        or "MAS mission executor consumed route-back" in blocker
    )


def _normalize_legacy_checkpoint_outcome(
    *,
    outcome: Mapping[str, Any],
    blockers: Sequence[str],
) -> dict[str, Any]:
    if _text(outcome.get("blocker_type")) != "unclassified_stage_closure_blocker":
        return dict(outcome)
    classes = classify_stage_closure_blockers(blockers)
    route_back_blockers = classes.get("route_back_checkpoint") or []
    unknown_blockers = classes.get("unknown") or []
    if not route_back_blockers or unknown_blockers:
        return dict(outcome)
    return {
        **dict(outcome),
        "kind": OUTCOME_NEXT_STAGE_TRANSITION,
        "transition_kind": "route_back_candidate_checkpoint",
        "blocker_type": None,
        "next_owner": "MedAutoScience",
        "next_action": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
        "requires_bundle_build_allowed": False,
        "can_submit": False,
        "resume_condition": (
            "route-back candidate checkpoint must be consumed into owner "
            "receipt, typed blocker, human gate, or next stage transition"
        ),
    }


def _blockers_from_gate(gate: Mapping[str, Any]) -> list[str]:
    return _unique_texts(
        [
            *_texts(gate.get("gate_replay_blockers")),
            *_texts(gate.get("blockers")),
            *_texts(gate.get("blocked_reasons")),
            _text(gate.get("blocked_reason")),
            _text(gate.get("reason")) if _text(gate.get("status")) == "blocked" else None,
        ]
    )


def _blockers_from_delivery(delivery: Mapping[str, Any]) -> list[str]:
    blockers: list[str | None] = [
        *_texts(delivery.get("blockers")),
        *_texts(delivery.get("blocked_reasons")),
        _text(delivery.get("blocked_reason")),
        _text(delivery.get("freshness_reason")),
    ]
    freshness = _text(delivery.get("freshness")) or _text(delivery.get("current_package_freshness"))
    if freshness in {"stale", "missing"}:
        blockers.append("current_package_stale" if freshness == "stale" else "current_package_missing")
    if delivery.get("current_package_exists") is False:
        blockers.append("current_package_missing")
    if delivery.get("current_package_current") is False:
        blockers.append("current_package_stale")
    return _unique_texts(blockers)


def _blockers_from_closeout(closeout: Mapping[str, Any]) -> list[str]:
    return _unique_texts(
        [
            *_texts(closeout.get("blockers")),
            *_texts(closeout.get("blocked_reasons")),
            _text(closeout.get("blocked_reason")),
            _text(closeout.get("terminal_reason")),
            _text(closeout.get("reason")) if _text(closeout.get("status")) == "blocked" else None,
        ]
    )


def _repair_budget(value: Mapping[str, Any] | None) -> dict[str, Any]:
    budget = _select_repair_budget_mapping(_mapping(value))
    max_count = _int(budget.get("repair_budget_max") or budget.get("max_attempts"))
    attempt_count = _int(budget.get("repair_attempt_count") or budget.get("attempt_count"))
    status = _text(budget.get("repair_budget_status"))
    if status is None and max_count is not None and attempt_count is not None:
        status = "exhausted" if attempt_count >= max_count else "remaining"
    return _compact(
        {
            "repair_budget_max": max_count,
            "repair_attempt_count": attempt_count,
            "repair_budget_status": status,
            "on_exhausted": _text(budget.get("on_exhausted")) or (
                "degraded_handoff" if status == "exhausted" else None
            ),
        }
    )


def _select_repair_budget_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    direct = _mapping(value)
    if _budget_has_attempt_fields(direct):
        return direct
    nested_candidates = [
        _mapping(direct.get("quality_repair_batch")),
        _mapping(direct.get("gate_clearing_batch")),
    ]
    for candidate in nested_candidates:
        if _text(candidate.get("repair_budget_status")) == "exhausted":
            return candidate
    for candidate in nested_candidates:
        if _budget_has_attempt_fields(candidate):
            return candidate
    return direct


def _budget_has_attempt_fields(value: Mapping[str, Any]) -> bool:
    return any(
        key in value
        for key in (
            "repair_budget_max",
            "max_attempts",
            "repair_attempt_count",
            "attempt_count",
            "repair_budget_status",
        )
    )


def _semantic_delta(value: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(value)
    return {
        "paper_delta_refs": _texts(payload.get("paper_delta_refs")),
        "reviewer_delta_refs": _texts(payload.get("reviewer_delta_refs")),
        "gate_delta_refs": _texts(payload.get("gate_delta_refs")),
        "delivery_delta_refs": _texts(payload.get("delivery_delta_refs")),
        "owner_decision_refs": _texts(payload.get("owner_decision_refs")),
    }


def _semantic_delta_refs(semantic_delta: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in (
        "paper_delta_refs",
        "reviewer_delta_refs",
        "gate_delta_refs",
        "delivery_delta_refs",
        "owner_decision_refs",
    ):
        refs.extend(_texts(semantic_delta.get(key)))
    return sorted(_unique_texts(refs))


def _has_semantic_delta(semantic_delta: Mapping[str, Any]) -> bool:
    return bool(_semantic_delta_refs(semantic_delta))


def _observability_gaps(closeout: Mapping[str, Any]) -> list[str]:
    gaps: list[str] = []
    for field, keys in {
        "duration": ("duration", "duration_ms"),
        "token_usage": ("token_usage",),
        "cost": ("cost", "cost_usd"),
    }.items():
        if not any(_has_observability_value(closeout.get(key)) for key in keys):
            gaps.append(f"{field}_missing")
    return gaps


def _closeout_with_explicit_accounting(closeout: Mapping[str, Any]) -> dict[str, Any]:
    if not closeout:
        return {}
    status = _text(closeout.get("status")) or "stage_closeout_status_missing"
    return {
        **dict(closeout),
        "duration": _first_mapping(
            _mapping(closeout.get("duration")),
            _explicit_missing_accounting(
                status=status,
                field="duration",
                reason_field="missing_duration_reason",
                null_fields={"seconds": None},
            ),
        ),
        "token_usage": _first_mapping(
            _mapping(closeout.get("token_usage")),
            _explicit_missing_accounting(
                status=status,
                field="token_usage",
                reason_field="missing_token_usage_reason",
                null_fields={"total_tokens": None},
            ),
        ),
        "cost": _first_mapping(
            _mapping(closeout.get("cost")),
            _explicit_missing_accounting(
                status=status,
                field="cost",
                reason_field="missing_cost_reason",
                null_fields={"usd": None},
            ),
        ),
    }


def _explicit_missing_accounting(
    *,
    status: str,
    field: str,
    reason_field: str,
    null_fields: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "status": "missing",
        **dict(null_fields),
        reason_field: f"{status}::{field}_not_recorded",
    }


def _has_observability_value(value: object) -> bool:
    if value in (None, "", [], {}):
        return False
    if isinstance(value, Mapping):
        return any(item not in (None, "", [], {}) for item in value.values())
    return True


def _input_summary(payload: Mapping[str, Any], *, status_key: str) -> dict[str, Any]:
    return _compact(
        {
            "status": _text(payload.get(status_key)) or _text(payload.get("status")),
            "ref": _text(payload.get("ref")) or _text(payload.get("latest_record_path")),
            "source_eval_id": _text(payload.get("source_eval_id")),
            "stage_attempt_id": _text(payload.get("stage_attempt_id")),
            "work_unit_id": _text(payload.get("work_unit_id")),
            "duration": _mapping(payload.get("duration")) or None,
            "token_usage": _mapping(payload.get("token_usage")) or None,
            "cost": _mapping(payload.get("cost")) or None,
        }
    )


def _delivery_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _compact(
        {
            "status": _text(payload.get("status")),
            "freshness": _text(payload.get("freshness")) or _text(payload.get("current_package_freshness")),
            "freshness_reason": _text(payload.get("freshness_reason")),
            "current_package_exists": payload.get("current_package_exists"),
            "current_package_current": payload.get("current_package_current"),
            "package_kind": _text(payload.get("package_kind")),
            "can_submit": payload.get("can_submit") is True,
            "bundle_build_allowed": payload.get("bundle_build_allowed") is True,
        }
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_mapping(*values: Mapping[str, Any]) -> dict[str, Any]:
    for value in values:
        if value:
            return dict(value)
    return {}


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


def _texts(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if isinstance(value, Mapping):
        return _unique_texts(
            [
                value.get("code"),
                value.get("reason"),
                value.get("blocked_reason"),
                value.get("blocker_type"),
                value.get("id"),
            ]
        )
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        result.extend(_texts(item))
    return _unique_texts(result)


def _unique_texts(values: Sequence[object | None]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = _text(value)
        if text is not None and text not in result:
            result.append(text)
    return result


def _int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


__all__ = [
    "ALLOWED_OUTCOME_KINDS",
    "SURFACE_KIND",
    "classify_stage_closure_blockers",
    "stage_closure_signature",
    "terminalize_stage_closure",
]
