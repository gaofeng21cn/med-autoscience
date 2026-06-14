from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


MAS_RUNTIME_GUARD_STAGE_IDS = (
    "direction_and_route_selection",
    "baseline_and_evidence_setup",
    "bounded_analysis_campaign",
    "manuscript_authoring",
    "review_and_quality_gate",
    "finalize_and_publication_handoff",
)


def build_stage_expected_receipt_payload_summary(
    payloads: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    success_payload_count = sum(
        1
        for payload in payloads
        if _text(payload.get("mode")) == "refs_only_domain_owned_success_payload"
    )
    typed_blocker_payload_count = sum(
        1
        for payload in payloads
        if _text(payload.get("mode")) == "refs_only_domain_owned_typed_blocker_payload"
    )
    stage_payloads = [
        stage
        for stage in (
            _stage_expected_receipt_stage_payload(stage_id, payloads)
            for stage_id in _stage_ids(payloads)
        )
        if stage
    ]
    return {
        "surface_kind": "mas_stage_expected_receipt_payload_summary",
        "owner": "med-autoscience",
        "consumer": "one_person_lab",
        "status": "per_stage_expected_receipt_payload_refs_ready_with_live_evidence_typed_blockers",
        "payload_kind": "stage_expected_receipt_or_monitor_freshness_refs",
        "payload_path_policy": (
            "operator_must_choose_success_refs_path_or_domain_owned_typed_blocker_path_empty_template_blocks"
        ),
        "payload_body_allowed": False,
        "empty_payload_template_is_success_evidence": False,
        "body_included": False,
        "summary_source_surface": "domain_dispatch_payload_summaries",
        "paper_line_count": len(payloads),
        "success_payload_count": success_payload_count,
        "typed_blocker_payload_count": typed_blocker_payload_count,
        "domain_ready_claim_count": 0,
        "production_ready_claim_count": 0,
        "publication_ready_claim_count": 0,
        "artifact_mutation_authorized_count": 0,
        "current_package_mutation_authorized_count": 0,
        "required_operator_payload_refs": [
            "domain_receipt_refs",
            "monitor_freshness_refs",
            "runtime_event_refs",
            "typed_blocker_refs",
        ],
        "required_return_shapes": [
            "domain_receipt_ref",
            "monitor_freshness_ref",
            "runtime_event_ref",
            "typed_blocker_ref",
        ],
        "accepted_payload_paths_ref": (
            "/real_paper_autonomy_guarded_apply_proof/paper_line_provider_canary_closeout/"
            "stage_expected_receipt_payload_summary"
        ),
        "stage_count": len(stage_payloads),
        "stages": stage_payloads,
    }


def stage_expected_receipt_refs(
    *,
    owner_receipt_refs: Sequence[str],
    stable_blocker_refs: Sequence[str],
    live_evidence_refs: Mapping[str, Any],
    no_forbidden_write_ref: str | None,
) -> list[str]:
    return _dedupe_text(
        [
            *owner_receipt_refs,
            *_sequence(live_evidence_refs.get("progress_delta_refs")),
            *_sequence(live_evidence_refs.get("ai_reviewer_gate_receipt_refs")),
            *_sequence(live_evidence_refs.get("artifact_movement_refs")),
            *_sequence(live_evidence_refs.get("publication_route_memory_writeback_receipt_refs")),
            *_sequence(live_evidence_refs.get("artifact_lifecycle_receipt_refs")),
            *_sequence(live_evidence_refs.get("human_gate_or_resume_refs")),
            *stable_blocker_refs,
            *_sequence(live_evidence_refs.get("stable_typed_blocker_refs")),
            no_forbidden_write_ref,
        ]
    )


def stage_monitor_freshness_refs(
    *,
    owner_receipt_refs: Sequence[str],
    stable_blocker_refs: Sequence[str],
    live_evidence_refs: Mapping[str, Any],
    no_forbidden_write_ref: str | None,
) -> list[str]:
    return _dedupe_text(
        [
            *_sequence(live_evidence_refs.get("progress_delta_refs")),
            *_sequence(live_evidence_refs.get("ai_reviewer_gate_receipt_refs")),
            *_sequence(live_evidence_refs.get("artifact_movement_refs")),
            *_sequence(live_evidence_refs.get("publication_route_memory_writeback_receipt_refs")),
            *_sequence(live_evidence_refs.get("artifact_lifecycle_receipt_refs")),
            *_sequence(live_evidence_refs.get("human_gate_or_resume_refs")),
            *stable_blocker_refs,
            *_sequence(live_evidence_refs.get("stable_typed_blocker_refs")),
            *owner_receipt_refs,
            no_forbidden_write_ref,
        ]
    )


def _stage_expected_receipt_stage_payload(
    stage_id: str,
    payloads: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    stage_payloads = [
        payload for payload in payloads if _record_stage_id(payload) == stage_id
    ]
    success_payloads = [
        payload
        for payload in stage_payloads
        if _text(payload.get("mode")) == "refs_only_domain_owned_success_payload"
    ]
    typed_blocker_payloads = [
        payload
        for payload in stage_payloads
        if _record_payload_refs(payload, "typed_blocker_refs")
    ]
    domain_owner_receipt_refs = _dedupe_text(
        ref
        for payload in success_payloads
        for ref in _record_payload_refs(payload, "domain_owner_receipt_refs")
    )
    expected_receipt_refs = _dedupe_text(
        ref
        for payload in success_payloads
        for ref in _record_payload_refs(payload, "stage_expected_receipt_refs")
    )
    monitor_freshness_refs = _dedupe_text(
        ref
        for payload in success_payloads
        for ref in _record_payload_refs(payload, "stage_monitor_freshness_refs")
    )
    runtime_event_refs = _dedupe_text(
        ref
        for payload in success_payloads
        for ref in _record_payload_refs(payload, "stage_runtime_event_refs")
    )
    typed_blocker_refs = _dedupe_text(
        ref
        for payload in typed_blocker_payloads
        for ref in _record_payload_refs(payload, "typed_blocker_refs")
    )
    if not typed_blocker_refs and stage_id in MAS_RUNTIME_GUARD_STAGE_IDS:
        typed_blocker_refs = [_stage_typed_blocker_ref(stage_id)]
    if not (
        expected_receipt_refs
        or monitor_freshness_refs
        or runtime_event_refs
        or typed_blocker_refs
    ):
        return {}
    stage_payload_count = len(stage_payloads)
    return {
        "stage_id": stage_id,
        "sequence": _stage_sequence(stage_id),
        "paper_line_count": stage_payload_count or len(payloads),
        "success_payload_count": len(success_payloads),
        "typed_blocker_payload_count": len(typed_blocker_payloads) or int(bool(typed_blocker_refs)),
        "domain_owner_receipt_ref_count": len(domain_owner_receipt_refs),
        "stable_typed_blocker_ref_count": len(typed_blocker_refs),
        "stage_expected_receipt_ref_count": len(expected_receipt_refs),
        "stage_monitor_freshness_ref_count": len(monitor_freshness_refs),
        "no_forbidden_write_guard_ref_count": sum(
            len(_record_payload_refs(payload, "forbidden_write_guard_refs"))
            for payload in stage_payloads
        ),
        "payload_kind": "stage_expected_receipt_or_monitor_freshness_refs",
        "current_payload_template": {
            "domain_receipt_refs": [],
            "monitor_freshness_refs": [],
            "runtime_event_refs": [],
            "typed_blocker_refs": [],
        },
        "success_refs_path_source": (
            "domain_dispatch_payload_summaries[mode=refs_only_domain_owned_success_payload]"
        ),
        "typed_blocker_path_source": (
            "domain_dispatch_payload_summaries[mode=refs_only_domain_owned_typed_blocker_payload]"
        ),
        "success_refs_path_payload": {
            "domain_receipt_refs": expected_receipt_refs,
            "monitor_freshness_refs": monitor_freshness_refs,
            "runtime_event_refs": runtime_event_refs,
            "typed_blocker_refs": [],
        },
        "typed_blocker_path_payload": {
            "domain_receipt_refs": [],
            "monitor_freshness_refs": _dedupe_text(
                ref
                for payload in typed_blocker_payloads
                for ref in _record_payload_refs(payload, "stage_monitor_freshness_refs")
            ),
            "runtime_event_refs": [],
            "typed_blocker_refs": typed_blocker_refs,
        },
        "monitor_status": (
            "success_refs_observed_with_typed_blocker_tail"
            if expected_receipt_refs and typed_blocker_refs
            else "success_refs_observed"
            if expected_receipt_refs or monitor_freshness_refs or runtime_event_refs
            else "typed_blocker_path_available"
        ),
        "operator_payload_submitted": False,
        "recommended_current_payload_path": (
            "typed_blocker_path" if typed_blocker_refs else "success_refs_path"
        ),
        "success_refs_visible_is_completion": False,
        "typed_blocker_visible_is_domain_ready": False,
        "payload_body_allowed": False,
        "domain_readiness_claimed": False,
        "production_readiness_claimed": False,
        "publication_readiness_claimed": False,
        "publication_ready_claimed": False,
        "artifact_mutation_authorized": False,
        "current_package_mutation_authorized": False,
        "production_soak_complete_claimed": False,
    }


def _stage_ids(payloads: Sequence[Mapping[str, Any]]) -> list[str]:
    return _dedupe_text([*MAS_RUNTIME_GUARD_STAGE_IDS, *(_record_stage_id(payload) for payload in payloads)])


def _stage_typed_blocker_ref(stage_id: str) -> str:
    return (
        "mas-stage-typed-blocker:"
        f"medautoscience:{stage_id}:"
        "real-paper-line-owner-receipt-or-monitor-freshness-pending"
    )


def _record_stage_id(payload: Mapping[str, Any]) -> str:
    return _text(_mapping(payload.get("record_payload")).get("stage_id")) or _text(payload.get("stage_id"))


def _record_payload_refs(payload: Mapping[str, Any], key: str) -> list[str]:
    record_payload = _mapping(payload.get("record_payload"))
    refs = _sequence(record_payload.get(key))
    return _dedupe_text(refs or _sequence(payload.get(key)))


def _stage_sequence(stage_id: str) -> int:
    return {
        "direction_and_route_selection": 1,
        "baseline_and_evidence_setup": 2,
        "bounded_analysis_campaign": 3,
        "manuscript_authoring": 4,
        "review_and_quality_gate": 5,
        "finalize_and_publication_handoff": 6,
    }.get(stage_id, 0)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[Any]:
    return list(value) if isinstance(value, Sequence) and not isinstance(value, str | bytes) else []


def _text(value: object) -> str:
    return str(value or "").strip()


def _dedupe_text(values: Iterable[object]) -> list[str]:
    return list(dict.fromkeys(_text(value) for value in values if _text(value)))
