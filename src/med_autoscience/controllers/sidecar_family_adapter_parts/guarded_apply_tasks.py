from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile


GUARDED_APPLY_OWNER_RECEIPT_CONTRACT = "mas-guarded-apply-owner-receipt.v2"


def provider_hosted_guarded_apply_tasks(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    provider_availability: Mapping[str, Any],
    opl_production_proof_ref: str | Path | None,
    owner_source_refs: list[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if provider_availability.get("provider_attempt_available") is not True:
        return []
    proof_ref = _text(opl_production_proof_ref)
    target = "DM002"
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
            "owner_source_refs": owner_source_refs or [],
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
            "role": "mas_guarded_apply_owner_receipt_contract",
            "ref": GUARDED_APPLY_OWNER_RECEIPT_CONTRACT,
            "exists": True,
        },
        *[dict(ref) for ref in owner_source_refs or []],
    ]
    return [
        {
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/guarded-apply",
            "priority": 30,
            "source": "mas-sidecar-export",
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
            },
            "dispatch_owner": "med-autoscience",
            "profile_name": profile.name,
            "source_refs": source_refs,
        }
    ]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _fingerprint(value: object) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]
