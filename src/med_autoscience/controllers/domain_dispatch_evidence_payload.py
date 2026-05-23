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
    study_id: str,
    reason: str,
    evidence_refs: Sequence[str | Mapping[str, Any]] = (),
    source_fingerprint: str | None = None,
    stage_attempt_source_fingerprint: str | None = None,
    profile_name: str | None = None,
) -> dict[str, Any]:
    normalized_task_kind = _text(task_kind) or "domain_route/owner-handoff"
    normalized_study_id = _text(study_id) or "unknown-study"
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
    slug = _slug(f"{normalized_task_kind}:{normalized_study_id}:{normalized_reason}")
    receipt_token = normalized_stage_attempt_source_fingerprint or normalized_source_fingerprint or _fingerprint(
        {
            "task_kind": normalized_task_kind,
            "study_id": normalized_study_id,
            "reason": normalized_reason,
            "evidence_refs": evidence_ref_values,
        }
    )
    typed_blocker_ref = (
        f"mas-domain-dispatch-typed-blocker:{DOMAIN_ID}:{slug}:"
        "owner-receipt-or-live-paper-line-closeout-pending"
    )
    no_forbidden_write_ref = (
        f"mas-no-forbidden-write-proof:{DOMAIN_ID}:{slug}:refs-only-dispatch-payload"
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
    record_payload = {
        "domain_id": DOMAIN_ID,
        "task_kind": normalized_task_kind,
        "study_id": normalized_study_id,
        "typed_blocker_refs": [typed_blocker_ref],
        "evidence_refs": evidence_ref_values,
        "no_regression_refs": [no_forbidden_write_ref],
    }
    identity_payload_fields = {
        "source_fingerprint": normalized_payload_source_fingerprint,
        "domain_source_fingerprint": normalized_source_fingerprint,
        "profile_name": normalized_profile_name,
    }
    for key, value in identity_payload_fields.items():
        if value is not None:
            record_payload[key] = value
    top_level_identity_fields = {
        "source_fingerprint": normalized_payload_source_fingerprint,
        "domain_source_fingerprint": normalized_source_fingerprint,
        "profile_name": normalized_profile_name,
    }
    return {
        "surface_kind": "mas_domain_dispatch_evidence_record_payload",
        "version": DOMAIN_DISPATCH_EVIDENCE_PAYLOAD_CONTRACT,
        "mode": "refs_only_domain_owned_typed_blocker_payload",
        "domain_id": DOMAIN_ID,
        "task_kind": normalized_task_kind,
        "study_id": normalized_study_id,
        **{key: value for key, value in top_level_identity_fields.items() if value is not None},
        "reason": normalized_reason,
        "request_id_template": f"domain_dispatch:{DOMAIN_ID}:<stage_attempt_id>",
        "record_action_template": f"domain_dispatch:{DOMAIN_ID}:<stage_attempt_id>:record",
        "verify_action_template": f"domain_dispatch:{DOMAIN_ID}:<stage_attempt_id>:verify",
        "record_payload": record_payload,
        "typed_blocker_refs": [typed_blocker_ref],
        "evidence_refs": evidence_ref_values,
        "no_regression_refs": [no_forbidden_write_ref],
        "ledger_receipt_ref_hint": f"mas://domain-dispatch-evidence/{DOMAIN_ID}/{slug}/{receipt_token}",
        "body_free_evidence_packets": [
            typed_blocker_packet,
            no_forbidden_write_packet,
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


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value).strip("-").lower()
    return slug[:120] or "domain-dispatch"


def _fingerprint(value: object) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


__all__ = [
    "DOMAIN_DISPATCH_EVIDENCE_PAYLOAD_CONTRACT",
    "build_domain_dispatch_evidence_record_payload",
]
