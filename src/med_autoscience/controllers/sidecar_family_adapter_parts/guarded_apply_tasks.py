from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile


def provider_hosted_guarded_apply_tasks(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    provider_availability: Mapping[str, Any],
    opl_production_proof_ref: str | Path | None,
) -> list[dict[str, Any]]:
    if provider_availability.get("provider_attempt_available") is not True:
        return []
    proof_ref = _text(opl_production_proof_ref)
    target = "DM002"
    dedupe_key = f"mas:{profile.name}:{target}:provider-hosted-guarded-apply:opl-temporal"
    return [
        {
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/guarded-apply",
            "priority": 30,
            "source": "mas-sidecar-export",
            "requires_approval": False,
            "dedupe_key": dedupe_key,
            "payload": {
                "profile": str(profile_ref),
                "study_id": target,
                "target_studies": [target],
                "provider_attempt_id": f"opl-temporal:{profile.name}:{target}:provider-hosted-guarded-apply",
                "idempotency_key": dedupe_key,
                "paper_autonomy_reason": "provider_hosted_guarded_apply_soak",
                "authority_boundary": "mas_owner_guarded_apply_only",
            },
            "dispatch_owner": "med-autoscience",
            "profile_name": profile.name,
            "source_refs": [
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
            ],
        }
    ]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
