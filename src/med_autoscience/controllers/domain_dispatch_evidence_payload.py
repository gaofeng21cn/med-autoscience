from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from .body_free_evidence_packets import build_body_free_evidence_packet


DOMAIN_DISPATCH_EVIDENCE_PAYLOAD_CONTRACT = "mas-domain-dispatch-evidence-record-payload.v1"
DOMAIN_ID = "medautoscience"
OWNER = "MedAutoScience"


def build_domain_dispatch_evidence_record_payload(
    *,
    task_kind: str,
    study_id: str | None = None,
    stage_id: str | None = None,
    stage_evidence_stage_id: str | None = None,
    reason: str,
    evidence_refs: Sequence[str | Mapping[str, Any]] = (),
    expected_receipt_refs: Sequence[str | Mapping[str, Any]] = (),
    monitor_freshness_refs: Sequence[str | Mapping[str, Any]] = (),
    runtime_event_refs: Sequence[str | Mapping[str, Any]] = (),
    source_fingerprint: str | None = None,
    stage_attempt_source_fingerprint: str | None = None,
    profile_name: str | None = None,
) -> dict[str, Any]:
    normalized_task_kind = _text(task_kind) or "domain_route/owner-handoff"
    normalized_study_id = _text(study_id)
    normalized_stage_id = _text(stage_id)
    normalized_stage_evidence_stage_id = _text(stage_evidence_stage_id) or normalized_stage_id
    normalized_reason = _text(reason) or "owner_chain_receipt_pending"
    normalized_source_fingerprint = _text(source_fingerprint)
    normalized_stage_attempt_source_fingerprint = _text(stage_attempt_source_fingerprint)
    normalized_payload_source_fingerprint = (
        normalized_stage_attempt_source_fingerprint or normalized_source_fingerprint
    )
    normalized_profile_name = _text(profile_name)
    evidence_ref_values = _unique_refs(
        [
            *[_ref_text(ref) for ref in evidence_refs],
            (
                "contracts/production_acceptance/mas-production-acceptance.json"
                "#/paper_line_guarded_apply_evidence"
            ),
        ]
    )
    expected_receipt_ref_values = _unique_refs([_ref_text(ref) for ref in expected_receipt_refs])
    monitor_freshness_ref_values = _unique_refs([_ref_text(ref) for ref in monitor_freshness_refs])
    runtime_event_ref_values = _unique_refs([_ref_text(ref) for ref in runtime_event_refs])
    slug_scope = normalized_study_id or (
        normalized_stage_id if normalized_stage_id != normalized_task_kind else None
    )
    receipt_token = normalized_stage_attempt_source_fingerprint or normalized_source_fingerprint or _fingerprint(
        {
            "task_kind": normalized_task_kind,
            "study_id": normalized_study_id,
            "stage_id": normalized_stage_id,
            "reason": normalized_reason,
            "evidence_refs": evidence_ref_values,
        }
    )
    slug = _slug(":".join(item for item in (normalized_task_kind, slug_scope, normalized_reason) if item))
    identity_token = _slug(receipt_token)
    typed_blocker_slug = _typed_blocker_slug(slug=slug, identity_token=identity_token)
    typed_blocker_ref = (
        f"mas-domain-dispatch-typed-blocker:{DOMAIN_ID}:{typed_blocker_slug}:"
        "owner-receipt-or-live-paper-line-closeout-pending"
    )
    no_forbidden_write_ref = (
        f"mas-no-forbidden-write-proof:{DOMAIN_ID}:{typed_blocker_slug}:"
        "refs-only-dispatch-payload"
    )
    typed_blocker_packet = build_body_free_evidence_packet(
        ref=typed_blocker_ref,
        role="stable_typed_blocker_ref",
        owner=OWNER,
    )
    no_forbidden_write_packet = build_body_free_evidence_packet(
        ref=no_forbidden_write_ref,
        role="no_forbidden_write_proof_ref",
        owner=OWNER,
    )
    stage_evidence_handoff = _stage_evidence_handoff(
        task_kind=normalized_task_kind,
        stage_id=normalized_stage_evidence_stage_id,
        expected_receipt_refs=expected_receipt_ref_values,
        monitor_freshness_refs=monitor_freshness_ref_values,
        runtime_event_refs=runtime_event_ref_values,
    )
    stage_evidence_packets = _stage_evidence_packets(
        stage_evidence_handoff=stage_evidence_handoff,
    )
    owner_chain_refs = evidence_ref_values
    no_regression_evidence_refs = [no_forbidden_write_ref]
    accepted_payload_paths = {
        "success_refs_path": {
            "required_any_operator_payload_refs": [
                "domain_owner_receipt_refs",
                "no_regression_evidence_refs",
                "owner_chain_refs",
            ],
            "typed_blocker_refs_must_be_absent": True,
            "closes_owner_chain": False,
            "closes_domain_ready": False,
            "closes_production_ready": False,
        },
        "typed_blocker_path": {
            "required_operator_payload_refs": ["typed_blocker_refs"],
            "success_claimed": False,
            "closes_owner_chain": False,
            "closes_domain_ready": False,
            "closes_production_ready": False,
        },
    }
    record_payload = {
        "domain_id": DOMAIN_ID,
        "task_kind": normalized_task_kind,
        "domain_owner_receipt_refs": [],
        "typed_blocker_refs": [typed_blocker_ref],
        "owner_chain_refs": owner_chain_refs,
        "evidence_refs": evidence_ref_values,
        "no_regression_evidence_refs": no_regression_evidence_refs,
        "domain_receipt_refs": [],
        "no_regression_refs": no_regression_evidence_refs,
    }
    if expected_receipt_ref_values:
        record_payload["stage_expected_receipt_refs"] = expected_receipt_ref_values
    if monitor_freshness_ref_values:
        record_payload["stage_monitor_freshness_refs"] = monitor_freshness_ref_values
    if runtime_event_ref_values:
        record_payload["stage_runtime_event_refs"] = runtime_event_ref_values
    if normalized_study_id is not None:
        record_payload["study_id"] = normalized_study_id
    if normalized_stage_id is not None:
        record_payload["stage_id"] = normalized_stage_id
    identity_payload_fields = {
        "source_fingerprint": normalized_payload_source_fingerprint,
        "domain_source_fingerprint": normalized_source_fingerprint,
        "stage_attempt_source_fingerprint": normalized_stage_attempt_source_fingerprint,
        "profile_name": normalized_profile_name,
    }
    for key, value in identity_payload_fields.items():
        if value is not None:
            record_payload[key] = value
    top_level_identity_fields = {
        "source_fingerprint": normalized_payload_source_fingerprint,
        "domain_source_fingerprint": normalized_source_fingerprint,
        "stage_attempt_source_fingerprint": normalized_stage_attempt_source_fingerprint,
        "profile_name": normalized_profile_name,
    }
    identity_binding = _identity_binding(
        task_kind=normalized_task_kind,
        study_id=normalized_study_id,
        stage_id=normalized_stage_id,
        source_fingerprint=normalized_payload_source_fingerprint,
        domain_source_fingerprint=normalized_source_fingerprint,
        profile_name=normalized_profile_name,
        stage_attempt_source_fingerprint=normalized_stage_attempt_source_fingerprint,
    )
    stage_evidence_handoff["identity_binding"] = identity_binding
    opl_runtime_action_execute_usage = {
        "surface_kind": "mas_domain_dispatch_opl_runtime_action_execute_usage",
        "record_action_template": f"domain_dispatch:{DOMAIN_ID}:<stage_attempt_id>:record",
        "dry_run_command_template": (
            "opl runtime action execute "
            f"--action domain_dispatch:{DOMAIN_ID}:<stage_attempt_id>:record "
            "--dry-run --payload '<opl_runtime_action_execute_payload>'"
        ),
        "record_command_template": (
            "opl runtime action execute "
            f"--action domain_dispatch:{DOMAIN_ID}:<stage_attempt_id>:record "
            "--payload '<opl_runtime_action_execute_payload>'"
        ),
        "payload_field": "opl_runtime_action_execute_payload",
        "preflight_policy": "domain_dispatch_evidence_payload_must_pass_success_refs_or_typed_blocker_path_preflight",
        "required_preflight_status_before_record": "ready_to_record",
        "required_identity_binding_status_before_record": "matched",
        "operator_must_bind_to_matching_opl_target_identity": True,
        "stale_or_mismatched_attempt_policy": "do_not_record_payload_when_identity_binding_conflicts",
    }
    return {
        "surface_kind": "mas_domain_dispatch_evidence_record_payload",
        "version": DOMAIN_DISPATCH_EVIDENCE_PAYLOAD_CONTRACT,
        "mode": "refs_only_domain_owned_typed_blocker_payload",
        "domain_id": DOMAIN_ID,
        "task_kind": normalized_task_kind,
        **({"study_id": normalized_study_id} if normalized_study_id is not None else {}),
        **({"stage_id": normalized_stage_id} if normalized_stage_id is not None else {}),
        **{key: value for key, value in top_level_identity_fields.items() if value is not None},
        "reason": normalized_reason,
        "request_id_template": f"domain_dispatch:{DOMAIN_ID}:<stage_attempt_id>",
        "record_action_template": f"domain_dispatch:{DOMAIN_ID}:<stage_attempt_id>:record",
        "verify_action_template": f"domain_dispatch:{DOMAIN_ID}:<stage_attempt_id>:verify",
        "record_payload": record_payload,
        "opl_runtime_action_execute_payload": record_payload,
        "opl_runtime_action_execute_usage": opl_runtime_action_execute_usage,
        "identity_binding": identity_binding,
        "stage_evidence_handoff": stage_evidence_handoff,
        "required_return_shapes": [
            "domain_owner_receipt_ref",
            "no_regression_evidence_ref",
            "owner_chain_ref",
            "typed_blocker_ref",
        ],
        "payload_path_policy": (
            "operator_must_choose_success_refs_path_or_domain_owned_typed_blocker_path_empty_template_blocks"
        ),
        "accepted_payload_paths": accepted_payload_paths,
        "legacy_payload_field_aliases": {
            "domain_receipt_refs": "domain_owner_receipt_refs",
            "no_regression_refs": "no_regression_evidence_refs",
        },
        "domain_owner_receipt_refs": [],
        "typed_blocker_refs": [typed_blocker_ref],
        "owner_chain_refs": owner_chain_refs,
        "evidence_refs": evidence_ref_values,
        "no_regression_evidence_refs": no_regression_evidence_refs,
        "no_regression_refs": no_regression_evidence_refs,
        "ledger_receipt_ref_hint": (
            f"mas://domain-dispatch-evidence/{DOMAIN_ID}/{typed_blocker_slug}/{receipt_token}"
        ),
        "body_free_evidence_packets": [
            typed_blocker_packet,
            no_forbidden_write_packet,
            *stage_evidence_packets,
        ],
        "closeout_semantics": "typed_blocker_until_real_owner_receipt_or_live_paper_line_closeout",
        "body_included": False,
        "domain_ready_claimed": False,
        "publication_ready_claimed": False,
        "artifact_mutation_authorized": False,
        "current_package_mutation_authorized": False,
        "authority_boundary": {
            "owner": "med-autoscience",
            "opl_records_refs_only": True,
            "opl_writes_mas_truth": False,
            "opl_reads_memory_body": False,
            "opl_reads_artifact_body": False,
            "opl_authorizes_quality_or_publication": False,
            "provider_completion_is_domain_ready": False,
            "typed_blocker_is_domain_ready": False,
        },
        "forbidden_payload_fields": [
            "study_truth_body",
            "paper_body",
            "publication_verdict_body",
            "artifact_body",
            "memory_body",
            "current_package_body",
        ],
    }


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _ref_text(value: str | Mapping[str, Any]) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("ref"))
    return _text(value)


def _unique_refs(values: Sequence[str | None]) -> list[str]:
    refs: list[str] = []
    for value in values:
        text = _text(value)
        if text and text not in refs:
            refs.append(text)
    return refs


def _stage_evidence_handoff(
    *,
    task_kind: str,
    stage_id: str | None,
    expected_receipt_refs: Sequence[str],
    monitor_freshness_refs: Sequence[str],
    runtime_event_refs: Sequence[str],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_domain_dispatch_stage_evidence_handoff",
        "status": "typed_blocker_pending_real_stage_receipts",
        "mode": "refs_only_stage_evidence_payload_hints",
        "task_kind": task_kind,
        **({"stage_id": stage_id} if stage_id is not None else {}),
        "expected_receipt_refs": list(expected_receipt_refs),
        "monitor_freshness_refs": list(monitor_freshness_refs),
        "runtime_event_refs": list(runtime_event_refs),
        "record_payload_ref_fields": [
            "stage_expected_receipt_refs",
            "stage_monitor_freshness_refs",
            "stage_runtime_event_refs",
            "typed_blocker_refs",
            "no_regression_evidence_refs",
        ],
        "closeout_requires": [
            "independent_stage_executor_receipt_ref_or_stable_typed_blocker_ref",
            "independent_reviewer_or_auditor_receipt_ref",
            "no_forbidden_write_proof_ref",
        ],
        "body_included": False,
        "domain_ready_claimed": False,
        "publication_ready_claimed": False,
        "artifact_mutation_authorized": False,
        "current_package_mutation_authorized": False,
        "authority_boundary": {
            "mas_owns_stage_receipt_refs": True,
            "opl_records_refs_only": True,
            "opl_writes_mas_truth": False,
            "opl_reads_memory_body": False,
            "opl_reads_artifact_body": False,
            "opl_authorizes_quality_or_publication": False,
            "typed_blocker_is_domain_ready": False,
            "stage_expected_receipt_refs_close_domain_ready": False,
        },
    }


def _stage_evidence_packets(*, stage_evidence_handoff: Mapping[str, Any]) -> list[dict[str, Any]]:
    packet_specs = [
        ("expected_receipt_refs", "stage_expected_receipt_ref"),
        ("monitor_freshness_refs", "stage_monitor_freshness_ref"),
        ("runtime_event_refs", "stage_runtime_event_ref"),
    ]
    packets = []
    for field, role in packet_specs:
        refs = _unique_refs([_text(ref) for ref in stage_evidence_handoff.get(field, [])])
        if not refs:
            continue
        packets.append(
            build_body_free_evidence_packet(
                ref="|".join(refs),
                role=role,
                owner=OWNER,
                freshness={
                    "status": "refs_declared_body_free",
                    "exists": True,
                    "mtime_epoch": None,
                    "size_bytes": 0,
                },
            )
        )
    return packets


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value).strip("-").lower()
    return slug[:120] or "domain-dispatch"


def _fingerprint(value: object) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


def _typed_blocker_slug(*, slug: str, identity_token: str) -> str:
    if not identity_token:
        return slug
    suffix = f":{identity_token}"
    max_slug_length = max(1, 120 - len(suffix))
    return f"{slug[:max_slug_length].rstrip('-:_')}{suffix}"


def _identity_binding(
    *,
    task_kind: str,
    study_id: str | None,
    stage_id: str | None,
    source_fingerprint: str | None,
    domain_source_fingerprint: str | None,
    profile_name: str | None,
    stage_attempt_source_fingerprint: str | None,
) -> dict[str, Any]:
    payload_identity = {
        "domain_id": DOMAIN_ID,
        "task_kind": task_kind,
        **({"study_id": study_id} if study_id else {}),
        **({"stage_id": stage_id} if stage_id else {}),
        **({"source_fingerprint": source_fingerprint} if source_fingerprint else {}),
        **(
            {"domain_source_fingerprint": domain_source_fingerprint}
            if domain_source_fingerprint
            else {}
        ),
        **({"profile_name": profile_name} if profile_name else {}),
        **(
            {"stage_attempt_source_fingerprint": stage_attempt_source_fingerprint}
            if stage_attempt_source_fingerprint
            else {}
        ),
    }
    return {
        "surface_kind": "mas_domain_dispatch_evidence_identity_binding",
        "payload_identity": payload_identity,
        "target_identity_source": "opl_app_operator_drilldown.domain_dispatch_evidence.target_identity",
        "policy": "record_only_when_payload_identity_matches_opl_target_identity",
        "conflict_error_kind": "domain_dispatch_evidence_receipt_conflict",
        "match_fields": [
            "domain_id",
            "task_kind",
            "study_id",
            "stage_id",
            "profile_name",
            "source_fingerprint",
            "domain_source_fingerprint",
            "stage_attempt_source_fingerprint",
        ],
        "source_fingerprint_semantics": {
            "stage_attempt_source_fingerprint": (
                "binds a specific OPL provider stage attempt when present"
            ),
            "domain_source_fingerprint": (
                "binds MAS owner-route currentness when the OPL target exposes domain_source_fingerprint"
            ),
            "source_fingerprint": (
                "acts as stage-attempt fingerprint only when the OPL target has no domain_source_fingerprint"
            ),
        },
        "stale_attempt_policy": "payload_must_not_be_used_to_close_a_different_or_stale_stage_attempt",
    }


__all__ = [
    "DOMAIN_DISPATCH_EVIDENCE_PAYLOAD_CONTRACT",
    "build_domain_dispatch_evidence_record_payload",
]
