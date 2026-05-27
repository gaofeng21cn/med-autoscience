from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from med_autoscience.profiles import WorkspaceProfile

from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)


GUARDED_APPLY_OWNER_RECEIPT_CONTRACT = "mas-guarded-apply-owner-receipt.v2"
PAPER_LINE_GUARDED_APPLY_EVIDENCE_REF = (
    "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence"
)
DEFAULT_GUARDED_APPLY_TARGETS = ("DM002", "DM003", "Obesity")


def provider_hosted_guarded_apply_tasks(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    provider_availability: Mapping[str, Any],
    opl_production_proof_ref: str | Path | None,
    owner_source_refs_by_target: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    target_studies: Sequence[str] = DEFAULT_GUARDED_APPLY_TARGETS,
) -> list[dict[str, Any]]:
    if provider_availability.get("provider_attempt_available") is not True:
        return []
    proof_ref = _text(opl_production_proof_ref)
    tasks: list[dict[str, Any]] = []
    for target in target_studies:
        target_text = _text(target)
        if target_text is None:
            continue
        target_owner_refs = [
            dict(ref)
            for ref in (owner_source_refs_by_target or {}).get(target_text, [])
        ]
        tasks.append(
            _provider_hosted_guarded_apply_task(
                profile=profile,
                profile_ref=profile_ref,
                provider_availability=provider_availability,
                proof_ref=proof_ref,
                target=target_text,
                owner_source_refs=target_owner_refs,
            )
        )
    return tasks


def _provider_hosted_guarded_apply_task(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    provider_availability: Mapping[str, Any],
    proof_ref: str | None,
    target: str,
    owner_source_refs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    dedupe_key = f"mas:{profile.name}:{target}:provider-hosted-guarded-apply:opl-temporal"
    provider_attempt_id = f"opl-temporal:{profile.name}:{target}:provider-hosted-guarded-apply"
    source_fingerprint = _fingerprint(
        {
            "provider_attempt_id": provider_attempt_id,
            "dedupe_key": dedupe_key,
            "profile": profile.name,
            "target": target,
            "opl_production_proof_ref": proof_ref,
            "provider_availability": provider_availability,
            "guarded_apply_owner_receipt_contract": GUARDED_APPLY_OWNER_RECEIPT_CONTRACT,
            "paper_line_guarded_apply_evidence_ref": PAPER_LINE_GUARDED_APPLY_EVIDENCE_REF,
            "owner_source_refs": owner_source_refs,
        }
    )
    source_refs = [
        {
            "role": "opl_production_proof",
            "ref": proof_ref,
            "exists": proof_ref is not None,
        },
        {
            "role": "provider_guarded_soak_read_model",
            "ref": "/provider_ready_adapter/provider_guarded_soak_read_model",
            "exists": True,
        },
        {
            "role": "paper_line_guarded_apply_evidence",
            "ref": PAPER_LINE_GUARDED_APPLY_EVIDENCE_REF,
            "exists": True,
            "body_included": False,
        },
        {
            "role": "mas_guarded_apply_owner_receipt_contract",
            "ref": GUARDED_APPLY_OWNER_RECEIPT_CONTRACT,
            "exists": True,
        },
        *[dict(ref) for ref in owner_source_refs],
    ]
    evidence_record_payload = build_domain_dispatch_evidence_record_payload(
        task_kind="paper_autonomy/guarded-apply",
        study_id=target,
        reason="real_paper_line_owner_receipt_or_stable_typed_blocker_pending",
        evidence_refs=source_refs,
        source_fingerprint=source_fingerprint,
        profile_name=profile.name,
    )
    return {
        "task_id": dedupe_key,
        "domain_id": "medautoscience",
        "task_kind": "paper_autonomy/guarded-apply",
        "priority": 30,
        "source": "mas-domain-handler-export",
        "requires_approval": False,
        "dedupe_key": dedupe_key,
        "source_fingerprint": source_fingerprint,
        "payload": {
            "profile": str(profile_ref),
            "study_id": target,
            "target_studies": [target],
            "provider_attempt_id": provider_attempt_id,
            "idempotency_key": dedupe_key,
            "paper_autonomy_reason": "provider_hosted_guarded_apply_soak",
            "authority_boundary": "mas_owner_guarded_apply_only",
            "selected_evidence_surface": PAPER_LINE_GUARDED_APPLY_EVIDENCE_REF,
            "canary_gate_id": "real_paper_line_provider_canary",
            "closeout_requires_mas_owner_receipt_or_typed_blocker": True,
        },
        "dispatch_owner": "med-autoscience",
        "profile_name": profile.name,
        "domain_dispatch_evidence_record_payload": evidence_record_payload,
        "source_refs": source_refs,
    }


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _fingerprint(value: object) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]
