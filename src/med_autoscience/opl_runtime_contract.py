from __future__ import annotations

from collections.abc import Mapping
from typing import Any

OPL_HOSTED_STAGE_RUNTIME_ID = "opl_hosted_stage_runtime"
MAS_DOMAIN_INTENT_ADAPTER_ID = "mas_domain_intent_adapter"
MAS_DOMAIN_INTENT_ADAPTER_ENGINE_ID = "mas-domain-intent-adapter"
OPL_RUNTIME_OWNER = "one-person-lab"
MAS_DOMAIN_OWNER = "med-autoscience"
MAS_DOMAIN_RUNTIME_ADAPTER_ROLE = "mas_domain_owner_receipt_adapter"
CONTROLLED_RESEARCH_BACKEND_EXECUTOR_OWNER = "controlled_research_backend"
EXTERNAL_MDS_ALLOWED_USES = (
    "source_provenance_ref",
    "historical_fixture_ref",
)
DEFAULT_AUTONOMOUS_RUNTIME_CONTRACT: dict[str, object] = {
    "enabled_by_default": True,
    "hosted_runtime_owner": OPL_RUNTIME_OWNER,
    "hosted_runtime_provider": "temporal",
    "runtime_substrate": OPL_HOSTED_STAGE_RUNTIME_ID,
    "persistent_online_control_plane": "opl_temporal",
    "task_start_handoff": "mas_domain_intent_to_opl_stage_attempt",
    "wakeup_retry_resume_owner": OPL_RUNTIME_OWNER,
    "codex_app_outer_driver_required": False,
    "mas_daemon_scheduler_attempt_loop_allowed": False,
}


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def explicit_opl_runtime_ref(execution: Mapping[str, Any] | None) -> str | None:
    if not isinstance(execution, Mapping):
        return None
    return (
        _non_empty_text(execution.get("opl_runtime_ref"))
        or _non_empty_text(execution.get("runtime_backend_id"))
        or _non_empty_text(execution.get("runtime_backend"))
    )


def is_opl_hosted_research_execution(execution: Mapping[str, Any] | None) -> bool:
    if not isinstance(execution, Mapping):
        return False
    auto_entry = _non_empty_text(execution.get("auto_entry"))
    if auto_entry != "on_managed_research_intent":
        return False
    runtime_ref = explicit_opl_runtime_ref(execution)
    if runtime_ref is None:
        return True
    return runtime_ref in {
        OPL_HOSTED_STAGE_RUNTIME_ID,
        "opl_provider_backed_stage_runtime",
        "opl-provider-backed-stage-runtime",
    }


def engine_id_for_runtime_ref(runtime_ref: str | None) -> str:
    normalized = _non_empty_text(runtime_ref)
    if normalized in {None, OPL_HOSTED_STAGE_RUNTIME_ID, "opl_provider_backed_stage_runtime"}:
        return "opl-hosted-stage-runtime"
    if normalized == "opl-provider-backed-stage-runtime":
        return normalized
    raise ValueError(f"unsupported MAS runtime ref; OPL owns runtime hydration: {normalized}")


def controlled_research_backend_metadata_for_runtime_ref(runtime_ref: str | None) -> tuple[str, str]:
    engine_id_for_runtime_ref(runtime_ref)
    return MAS_DOMAIN_INTENT_ADAPTER_ID, MAS_DOMAIN_INTENT_ADAPTER_ENGINE_ID


def opl_runtime_default_operation_contract(runtime_ref: str | None = None) -> dict[str, object]:
    engine_id = engine_id_for_runtime_ref(runtime_ref)
    research_backend_id, research_engine_id = controlled_research_backend_metadata_for_runtime_ref(runtime_ref)
    return {
        "runtime_owner": OPL_RUNTIME_OWNER,
        "runtime_substrate": OPL_HOSTED_STAGE_RUNTIME_ID,
        "runtime_ref": OPL_HOSTED_STAGE_RUNTIME_ID,
        "runtime_engine_id": engine_id,
        "runtime_backend_role": MAS_DOMAIN_RUNTIME_ADAPTER_ROLE,
        "runtime_backend_is_generic_owner": False,
        "default_autonomous_runtime": dict(DEFAULT_AUTONOMOUS_RUNTIME_CONTRACT),
        "default_runtime_backend_is_opl_provider_owned": True,
        "delegated_domain_adapter_id": MAS_DOMAIN_INTENT_ADAPTER_ID,
        "delegated_domain_adapter_engine_id": MAS_DOMAIN_INTENT_ADAPTER_ENGINE_ID,
        "domain_runtime_adapter_id": MAS_DOMAIN_INTENT_ADAPTER_ID,
        "domain_runtime_adapter_role": MAS_DOMAIN_RUNTIME_ADAPTER_ROLE,
        "generic_runtime_owner": OPL_RUNTIME_OWNER,
        "generic_runtime_substrate": OPL_HOSTED_STAGE_RUNTIME_ID,
        "domain_truth_owner": MAS_DOMAIN_OWNER,
        "domain_authority_retained": [
            "study_truth",
            "publication_quality_verdict",
            "artifact_authority",
            "memory_accept_reject_receipt",
            "owner_receipt",
            "typed_blocker",
        ],
        "mas_runtime_backend_registry_retired": True,
        "provider_attempt_owner": OPL_RUNTIME_OWNER,
        "provider_completion_is_domain_completion": False,
        "domain_progression_requires": [
            "mas_owner_receipt",
            "mas_typed_blocker",
            "ai_reviewer_backed_verdict",
            "publication_gate_receipt",
        ],
        "runtime_backend_retirement_gate": {
            "no_active_default_caller_required": True,
            "opl_replacement_parity_required": True,
            "domain_receipt_parity_required": True,
            "history_tombstone_required": True,
        },
        "research_backend_id": research_backend_id,
        "research_engine_id": research_engine_id,
        "external_mds_required_for_default_operation": False,
        "external_mds_runnable_dependency": False,
        "external_mds_retained_role": "frozen_source_archive_or_historical_fixture",
        "external_mds_allowed_uses": list(EXTERNAL_MDS_ALLOWED_USES),
    }


def provider_admission_required_blocker(*, operation: str, quest_id: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "ok": False,
        "status": "provider_admission_required",
        "source": f"{OPL_HOSTED_STAGE_RUNTIME_ID}.{operation}",
        "runtime_owner": OPL_RUNTIME_OWNER,
        "domain_owner": MAS_DOMAIN_OWNER,
        "provider_completion_is_domain_completion": False,
        "typed_blocker": {
            "blocker_type": "opl_provider_admission_required",
            "owner": OPL_RUNTIME_OWNER,
            "domain_owner": MAS_DOMAIN_OWNER,
            "reason": "mas_private_runtime_backend_retired",
            "required_handoff": "MAS DomainIntent must be hydrated by OPL queue/stage attempt ledger.",
        },
    }
    if quest_id:
        payload["quest_id"] = quest_id
    return payload


__all__ = [
    "CONTROLLED_RESEARCH_BACKEND_EXECUTOR_OWNER",
    "DEFAULT_AUTONOMOUS_RUNTIME_CONTRACT",
    "EXTERNAL_MDS_ALLOWED_USES",
    "MAS_DOMAIN_INTENT_ADAPTER_ENGINE_ID",
    "MAS_DOMAIN_INTENT_ADAPTER_ID",
    "MAS_DOMAIN_OWNER",
    "MAS_DOMAIN_RUNTIME_ADAPTER_ROLE",
    "OPL_HOSTED_STAGE_RUNTIME_ID",
    "OPL_RUNTIME_OWNER",
    "controlled_research_backend_metadata_for_runtime_ref",
    "engine_id_for_runtime_ref",
    "explicit_opl_runtime_ref",
    "is_opl_hosted_research_execution",
    "opl_runtime_default_operation_contract",
    "provider_admission_required_blocker",
]
