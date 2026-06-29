from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


SURFACE_KIND = "mas_next_action_envelope"
SCHEMA_VERSION = 1

FAMILY_PAPER_WRITE_PROSE_REPAIR = "paper.write.prose_repair"
FAMILY_PAPER_REVIEW_AI_REVIEWER = "paper.review.ai_reviewer"
FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY = "paper.gate.publishability_replay"
FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL = "paper.package.submission_minimal"
FAMILY_PAPER_DELIVERY_SYNC = "paper.delivery.sync"
FAMILY_HUMAN_APPROVAL = "human.approval"
FAMILY_BLOCKED_TYPED = "blocked.typed"
FAMILY_RUNTIME_WAIT_RECEIPT = "runtime.wait_receipt"
FAMILY_RUNTIME_OPL_ROUTE = "runtime.opl_route"
FAMILY_MISSION_COMPLETE = "mission.complete"

ACTION_FAMILIES = frozenset(
    {
        FAMILY_PAPER_WRITE_PROSE_REPAIR,
        FAMILY_PAPER_REVIEW_AI_REVIEWER,
        FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY,
        FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL,
        FAMILY_PAPER_DELIVERY_SYNC,
        FAMILY_HUMAN_APPROVAL,
        FAMILY_BLOCKED_TYPED,
        FAMILY_RUNTIME_WAIT_RECEIPT,
        FAMILY_RUNTIME_OPL_ROUTE,
        FAMILY_MISSION_COMPLETE,
    }
)

FAMILY_OWNER = {
    FAMILY_PAPER_WRITE_PROSE_REPAIR: "write",
    FAMILY_PAPER_REVIEW_AI_REVIEWER: "ai_reviewer",
    FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY: "publication_gate",
    FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL: "mission_executor",
    FAMILY_PAPER_DELIVERY_SYNC: "delivery",
    FAMILY_HUMAN_APPROVAL: "human",
    FAMILY_BLOCKED_TYPED: "typed_blocker_owner",
    FAMILY_RUNTIME_WAIT_RECEIPT: "one-person-lab",
    FAMILY_RUNTIME_OPL_ROUTE: "one-person-lab",
    FAMILY_MISSION_COMPLETE: "MedAutoScience",
}

FAMILY_KIND = {
    FAMILY_PAPER_WRITE_PROSE_REPAIR: "paper_write",
    FAMILY_PAPER_REVIEW_AI_REVIEWER: "owner_review",
    FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY: "quality_gate_replay",
    FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL: "package_materialization",
    FAMILY_PAPER_DELIVERY_SYNC: "delivery_sync",
    FAMILY_HUMAN_APPROVAL: "wait_for_human",
    FAMILY_BLOCKED_TYPED: "stop_with_typed_blocker",
    FAMILY_RUNTIME_WAIT_RECEIPT: "wait_for_runtime_receipt",
    FAMILY_RUNTIME_OPL_ROUTE: "submit_to_opl_runtime",
    FAMILY_MISSION_COMPLETE: "complete_mission",
}

FAMILY_EXECUTOR_TARGET = {
    FAMILY_PAPER_WRITE_PROSE_REPAIR: "mas_owner_callable",
    FAMILY_PAPER_REVIEW_AI_REVIEWER: "mas_owner_callable",
    FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY: "mas_owner_callable",
    FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL: "mas_owner_callable",
    FAMILY_PAPER_DELIVERY_SYNC: "mas_owner_callable",
    FAMILY_HUMAN_APPROVAL: "human_gate",
    FAMILY_BLOCKED_TYPED: "mas_authority_kernel",
    FAMILY_RUNTIME_WAIT_RECEIPT: "opl_runtime_readback",
    FAMILY_RUNTIME_OPL_ROUTE: "opl_domain_progress_transition_runtime",
    FAMILY_MISSION_COMPLETE: "mas_terminal",
}

PROSE_REPAIR_HINTS = frozenset(
    {
        "paper_write",
        "write",
        "prose",
        "story",
        "story_surface",
        "medical_prose",
        "quality_repair",
        "claim_evidence",
        "terminology",
        "surface_qc",
        "publication_surface_repair",
        "manuscript_story_surface_delta_missing",
    }
)
AI_REVIEWER_HINTS = frozenset({"ai_reviewer", "reviewer", "publication_eval"})
GATE_REPLAY_HINTS = frozenset({"gate_replay", "gate-clearing", "gate_clearing", "publishability_gate"})
SUBMISSION_PACKAGE_HINTS = frozenset(
    {"submission_minimal", "submission_milestone", "submission_materialize", "package-candidate"}
)
DELIVERY_SYNC_HINTS = frozenset({"delivery_sync", "mirror_sync", "current_package_mirror_sync"})
RUNTIME_HINTS = frozenset({"opl", "runtime", "stage_attempt", "provider", "live_readback"})


def compile_next_action_envelope(
    *,
    stage_outcome: Mapping[str, Any],
    study_id: str | None = None,
    stage_id: str | None = None,
    outcome_ref: str | None = None,
    route_command: Mapping[str, Any] | None = None,
    owner_route: Mapping[str, Any] | None = None,
    authority_boundary: Mapping[str, Any] | None = None,
    diagnostic_refs: Sequence[Mapping[str, Any] | str] | None = None,
) -> dict[str, Any]:
    """Compile MAS stage outcome evidence into one authoritative next-action envelope.

    The compiler is side-effect free. It does not authorize domain truth writes,
    OPL queues, provider attempts, owner receipts, typed blockers, or human gates.
    """

    outcome = _mapping(stage_outcome)
    route = _mapping(route_command)
    owner = _mapping(owner_route)
    resolved_study_id = _text(study_id) or _text(outcome.get("study_id")) or _text(route.get("study_id"))
    resolved_stage_id = _text(stage_id) or _text(outcome.get("stage_id")) or _text(route.get("stage_id"))
    work_unit_id = _work_unit_id(
        outcome.get("work_unit_id"),
        outcome.get("next_work_unit"),
        route.get("work_unit_id"),
        route.get("next_work_unit"),
        owner.get("work_unit_id"),
        owner.get("next_work_unit"),
    )
    work_unit_fingerprint = _first_text(
        (outcome, route, owner),
        ("work_unit_fingerprint", "action_fingerprint", "source_fingerprint"),
    )
    family = resolve_action_family(
        stage_outcome=outcome,
        route_command=route,
        owner_route=owner,
        work_unit_id=work_unit_id,
    )
    action_kind = FAMILY_KIND[family]
    if family in {FAMILY_RUNTIME_OPL_ROUTE, FAMILY_RUNTIME_WAIT_RECEIPT}:
        owner_name = _text(route.get("runtime_owner")) or FAMILY_OWNER[family]
    else:
        owner_name = (
            _text(owner.get("next_owner"))
            or _text(owner.get("owner"))
            or _text(outcome.get("next_owner"))
            or FAMILY_OWNER[family]
        )
    idempotency_key = (
        _text(route.get("request_idempotency_key"))
        or _text(route.get("attempt_idempotency_key"))
        or _text(owner.get("idempotency_key"))
        or _stable_key(
            "next-action",
            resolved_study_id,
            resolved_stage_id,
            outcome_ref,
            family,
            work_unit_id,
            work_unit_fingerprint,
        )
    )
    action_id = _stable_key(
        SURFACE_KIND,
        resolved_study_id,
        resolved_stage_id,
        outcome_ref,
        family,
        action_kind,
        idempotency_key,
    )
    envelope = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "action_id": action_id,
        "study_id": resolved_study_id,
        "stage_id": resolved_stage_id,
        "outcome_ref": _text(outcome_ref) or _text(outcome.get("stage_closure_decision_ref")),
        "action_family": family,
        "action_kind": action_kind,
        "owner": owner_name,
        "executor_target": FAMILY_EXECUTOR_TARGET[family],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "required_input_refs": _required_input_refs(outcome, route, owner),
        "expected_output_contract": expected_output_contract_for_family(family),
        "authority_boundary": _authority_boundary(family, authority_boundary),
        "idempotency_key": idempotency_key,
        "semantic_progress_signature": (
            _text(outcome.get("decision_signature"))
            or _text(outcome.get("semantic_progress_signature"))
            or _stable_key("semantic-progress", resolved_study_id, resolved_stage_id, family, work_unit_id)
        ),
        "retry_or_stop_policy": retry_or_stop_policy_for_family(family),
        "supersedes_refs": _text_items(outcome.get("supersedes_refs")),
        "diagnostic_refs": _diagnostic_refs(diagnostic_refs, outcome, route, owner),
        "authority_source": "mas_next_action_compiler",
        "legacy_fields_are_diagnostic": True,
        "legacy_field_diagnostic_roles": {
            "work_unit_id": "diagnostic_currentness_id",
            "work_unit_fingerprint": "diagnostic_currentness_signature",
            "current_work_unit": "diagnostic_readback_only",
            "current_executable_owner_action": "diagnostic_readback_only",
        },
        "completion_authority": "stage_outcome_only",
        "runtime_receipt_authority": "opl_transition_receipt_only",
    }
    return _compact(envelope)


def resolve_action_family(
    *,
    stage_outcome: Mapping[str, Any] | None = None,
    route_command: Mapping[str, Any] | None = None,
    owner_route: Mapping[str, Any] | None = None,
    work_unit_id: str | None = None,
) -> str:
    outcome = _mapping(stage_outcome)
    route = _mapping(route_command)
    owner = _mapping(owner_route)
    outcome_kind = (
        _text(_mapping(outcome.get("outcome")).get("kind"))
        or _text(outcome.get("kind"))
        or _text(outcome.get("decision_kind"))
    )
    command_kind = _text(route.get("command_kind"))
    explicit_family = _first_text((outcome, route, owner), ("action_family", "next_action_family"))
    if explicit_family in ACTION_FAMILIES:
        return explicit_family
    if outcome_kind == "human_gate" or command_kind == "wait_for_human":
        return FAMILY_HUMAN_APPROVAL
    if outcome_kind == "typed_blocker" or command_kind == "stop_with_typed_blocker":
        return FAMILY_BLOCKED_TYPED
    if outcome_kind == "owner_receipt" and _owner_receipt_is_submission_ready_terminal(outcome):
        return FAMILY_MISSION_COMPLETE
    if outcome_kind == "mission_complete" or command_kind == "complete_mission":
        return FAMILY_MISSION_COMPLETE
    if command_kind in {"resume_stage", "start_next_stage", "route_back"} and _has_hint(
        [route, owner, outcome],
        RUNTIME_HINTS,
    ):
        return FAMILY_RUNTIME_OPL_ROUTE

    tokens = _tokens(
        work_unit_id,
        _first_text((outcome, route, owner), ("action_type", "controller_action_type", "controller_action")),
        _first_text((outcome, route, owner), ("transition_kind", "next_action", "route_target")),
        *_text_items(owner.get("allowed_actions")),
        *_text_items(route.get("allowed_actions")),
    )
    if _contains_any(tokens, SUBMISSION_PACKAGE_HINTS):
        return FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL
    if _contains_any(tokens, DELIVERY_SYNC_HINTS):
        return FAMILY_PAPER_DELIVERY_SYNC
    if _contains_any(tokens, GATE_REPLAY_HINTS):
        return FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY
    if _contains_any(tokens, PROSE_REPAIR_HINTS):
        return FAMILY_PAPER_WRITE_PROSE_REPAIR
    if _contains_any(tokens, AI_REVIEWER_HINTS):
        return FAMILY_PAPER_REVIEW_AI_REVIEWER
    if _contains_any(tokens, RUNTIME_HINTS):
        return FAMILY_RUNTIME_WAIT_RECEIPT
    return FAMILY_PAPER_WRITE_PROSE_REPAIR


def _owner_receipt_is_submission_ready_terminal(outcome: Mapping[str, Any]) -> bool:
    quality_gate_status = _text(outcome.get("quality_gate_status"))
    package_status = _first_text(
        (outcome,),
        ("freshness", "status", "freshness_status", "delivery_status"),
    )
    blockers = _text_items(outcome.get("known_blockers"))
    return (
        _text(outcome.get("package_kind")) == "submission_ready_package"
        and package_status in {"current", "fresh", "synced"}
        and outcome.get("can_submit") is True
        and quality_gate_status in {"clear", "passed", "cleared"}
        and outcome.get("generated_from_current_source") is True
        and _text(outcome.get("root")) is not None
        and outcome.get("zip_exists") is True
        and not blockers
    )


def expected_output_contract_for_family(action_family: str) -> dict[str, Any]:
    if action_family == FAMILY_PAPER_WRITE_PROSE_REPAIR:
        return {
            "output_kind": "paper_facing_delta_or_owner_receipt",
            "accepted_refs": ["paper_facing_delta_ref", "domain_owner_receipt_ref", "route_back_evidence_ref"],
        }
    if action_family == FAMILY_PAPER_REVIEW_AI_REVIEWER:
        return {
            "output_kind": "ai_reviewer_publication_eval",
            "accepted_refs": ["publication_eval_record_ref", "publication_eval_latest_ref"],
        }
    if action_family == FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY:
        return {
            "output_kind": "quality_gate_receipt",
            "accepted_refs": ["quality_gate_receipt_ref", "publishability_gate_report_ref"],
        }
    if action_family == FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL:
        return {
            "output_kind": "non_authority_submission_candidate",
            "accepted_refs": ["candidate_package_manifest_ref", "owner_consumption_request_ref"],
        }
    if action_family == FAMILY_PAPER_DELIVERY_SYNC:
        return {
            "output_kind": "delivery_sync_receipt",
            "accepted_refs": ["delivery_sync_receipt_ref", "delivery_inspect_ref"],
        }
    if action_family == FAMILY_RUNTIME_OPL_ROUTE:
        return {
            "output_kind": "opl_transition_receipt",
            "accepted_refs": ["opl_transition_receipt_ref", "stage_attempt_ref", "runtime_closeout_ref"],
        }
    if action_family == FAMILY_RUNTIME_WAIT_RECEIPT:
        return {
            "output_kind": "opl_runtime_readback",
            "accepted_refs": ["opl_transition_receipt_ref", "typed_runtime_blocker_ref"],
        }
    if action_family == FAMILY_HUMAN_APPROVAL:
        return {"output_kind": "human_gate_receipt", "accepted_refs": ["human_gate_ref"]}
    if action_family == FAMILY_BLOCKED_TYPED:
        return {"output_kind": "typed_blocker", "accepted_refs": ["typed_blocker_ref"]}
    return {"output_kind": "mission_terminal_receipt", "accepted_refs": ["mission_package_ref"]}


def retry_or_stop_policy_for_family(action_family: str) -> dict[str, Any]:
    if action_family in {FAMILY_RUNTIME_OPL_ROUTE, FAMILY_RUNTIME_WAIT_RECEIPT}:
        return {
            "retry_owner": "one-person-lab",
            "semantic_budget_resets_from_transport": False,
            "stop_requires": "opl_transition_receipt_or_typed_runtime_blocker",
        }
    if action_family in {FAMILY_BLOCKED_TYPED, FAMILY_HUMAN_APPROVAL, FAMILY_MISSION_COMPLETE}:
        return {"retry_owner": None, "retry_allowed": False, "stop_requires": "terminal_owner_result"}
    return {
        "retry_owner": "MedAutoScience",
        "semantic_budget_resets_from_transport": False,
        "stop_requires": "semantic_delta_owner_receipt_typed_blocker_or_human_gate",
    }


def _authority_boundary(action_family: str, authority_boundary: Mapping[str, Any] | None) -> dict[str, Any]:
    boundary = dict(authority_boundary or {})
    boundary.setdefault("can_claim_stage_complete", False)
    boundary.setdefault("can_claim_submission_ready", False)
    boundary.setdefault("can_claim_publication_ready", False)
    boundary.setdefault("can_write_owner_receipt", False)
    boundary.setdefault("can_write_typed_blocker", False)
    boundary.setdefault("can_write_human_gate", False)
    boundary.setdefault("can_write_runtime_queue", False)
    boundary.setdefault("can_write_provider_attempt", False)
    boundary.setdefault("can_write_runtime_queue_or_provider_attempt", False)
    boundary["next_action_authority"] = True
    boundary["authority_owner"] = "MedAutoScience"
    boundary["runtime_owner"] = "one-person-lab"
    boundary["action_family_authority"] = True
    boundary["exact_work_unit_id_authority"] = False
    boundary["can_submit_to_opl_runtime"] = action_family == FAMILY_RUNTIME_OPL_ROUTE
    return boundary


def _required_input_refs(*payloads: Mapping[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for payload in payloads:
        for key in ("required_input_refs", "required_currentness_refs", "artifact_delta_refs", "source_refs"):
            value = payload.get(key)
            if isinstance(value, Mapping):
                for role, ref in value.items():
                    text = _text(ref)
                    if text is not None:
                        refs.append({"role": str(role), "ref": text})
            else:
                for ref in _text_items(value):
                    refs.append({"role": key, "ref": ref})
    return _dedupe_refs(refs)


def _diagnostic_refs(
    explicit_refs: Sequence[Mapping[str, Any] | str] | None,
    *payloads: Mapping[str, Any],
) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for item in explicit_refs or []:
        if isinstance(item, Mapping):
            ref = _text(item.get("ref")) or _text(item.get("uri"))
            role = _text(item.get("role")) or _text(item.get("ref_kind")) or "diagnostic"
            if ref is not None:
                refs.append({"role": role, "ref": ref})
        elif text := _text(item):
            refs.append({"role": "diagnostic", "ref": text})
    for payload in payloads:
        for key in ("diagnostic_refs", "legacy_refs", "closeout_refs"):
            for ref in _text_items(payload.get(key)):
                refs.append({"role": key, "ref": ref})
    return _dedupe_refs(refs)


def _dedupe_refs(refs: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for ref in refs:
        role = str(ref.get("role") or "ref")
        uri = str(ref.get("ref") or "").strip()
        if not uri or (role, uri) in seen:
            continue
        seen.add((role, uri))
        result.append({"role": role, "ref": uri})
    return result


def _has_hint(payloads: Sequence[Mapping[str, Any]], hints: frozenset[str]) -> bool:
    return _contains_any(_tokens(*(json.dumps(payload, sort_keys=True) for payload in payloads)), hints)


def _contains_any(tokens: Sequence[str], hints: frozenset[str]) -> bool:
    return any(hint in token for token in tokens for hint in hints)


def _tokens(*values: object) -> list[str]:
    return [text.lower().replace("-", "_") for value in values if (text := _text(value)) is not None]


def _work_unit_id(*values: object) -> str | None:
    for value in values:
        if isinstance(value, Mapping):
            text = _text(value.get("unit_id")) or _text(value.get("work_unit_id")) or _text(value.get("id"))
        else:
            text = _text(value)
        if text is not None:
            return text
    return None


def _first_text(payloads: Sequence[Mapping[str, Any]], keys: Sequence[str]) -> str | None:
    for payload in payloads:
        for key in keys:
            text = _text(payload.get(key))
            if text is not None:
                return text
    return None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if isinstance(value, Mapping):
        return [text for text in (_text(item) for item in value.values()) if text is not None]
    if isinstance(value, Sequence):
        return [text for text in (_text(item) for item in value) if text is not None]
    return []


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _stable_key(*parts: object) -> str:
    payload = json.dumps([part for part in parts if part is not None], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _compact(value: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        if item is None or item == [] or item == {}:
            continue
        result[key] = item
    return result


__all__ = [
    "ACTION_FAMILIES",
    "FAMILY_BLOCKED_TYPED",
    "FAMILY_HUMAN_APPROVAL",
    "FAMILY_MISSION_COMPLETE",
    "FAMILY_PAPER_DELIVERY_SYNC",
    "FAMILY_PAPER_GATE_PUBLISHABILITY_REPLAY",
    "FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL",
    "FAMILY_PAPER_REVIEW_AI_REVIEWER",
    "FAMILY_PAPER_WRITE_PROSE_REPAIR",
    "FAMILY_RUNTIME_OPL_ROUTE",
    "FAMILY_RUNTIME_WAIT_RECEIPT",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "compile_next_action_envelope",
    "expected_output_contract_for_family",
    "resolve_action_family",
    "retry_or_stop_policy_for_family",
]
