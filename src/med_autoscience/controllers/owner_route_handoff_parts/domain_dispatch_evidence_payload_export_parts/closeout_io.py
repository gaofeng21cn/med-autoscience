from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export_parts.shared import (
    mapping,
    text,
    texts,
    unique,
)


def relative_stage_attempt_closeout_ref(*, study_id: str, stage_attempt_id: str) -> str:
    return (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/"
        f"{stage_attempt_id}.closeout.json"
    )


def default_executor_execution_latest_ref(study_id: str) -> str:
    return f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/latest.json"


def default_executor_execution_history_ref(study_id: str) -> str:
    return f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/history.jsonl"


def closeout_authority_boundary() -> dict[str, Any]:
    return {
        "record_only_surface": True,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "paper_package_mutation_allowed": False,
        "publication_eval_latest_write_allowed": False,
        "controller_decision_write_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "provider_completion_is_domain_completion": False,
    }


def closeout_does_not_claim_domain_completion(closeout: Mapping[str, Any]) -> bool:
    return (
        closeout.get("provider_completion_is_domain_completion") is not True
        and closeout.get("provider_completion_is_domain_ready") is not True
        and closeout.get("domain_completion_claimed") is not True
    )


def is_matching_owner_receipt_closeout(
    *,
    closeout: Mapping[str, Any],
    owner_receipt: Mapping[str, Any],
    domain_execution: Mapping[str, Any],
    target_identity: Mapping[str, Any],
    study_id: str,
    stage_attempt_id: str,
    action_type: str,
) -> bool:
    return (
        matches_stage_attempt_identity(
            closeout=closeout,
            target_identity=target_identity,
            study_id=study_id,
            stage_attempt_id=stage_attempt_id,
            action_type=action_type,
        )
        and text(closeout.get("status")) in {"executed", "closed_with_domain_owner_refs"}
        and owner_receipt_is_refs_only(owner_receipt)
        and text(domain_execution.get("execution_status")) in {
            "executed",
            "closed_with_domain_owner_refs",
        }
        and closeout_does_not_claim_domain_completion(closeout)
    )


def matches_stage_attempt_identity(
    *,
    closeout: Mapping[str, Any],
    target_identity: Mapping[str, Any],
    study_id: str,
    stage_attempt_id: str,
    action_type: str,
) -> bool:
    return (
        text(closeout.get("surface_kind")) == "stage_attempt_closeout_packet"
        and text(closeout.get("stage_attempt_id")) == stage_attempt_id
        and text(closeout.get("stage_id")) == text(target_identity.get("stage_id"))
        and text(closeout.get("study_id")) == study_id
        and text(closeout.get("action_type")) == action_type
    )


def owner_receipt_is_refs_only(owner_receipt: Mapping[str, Any]) -> bool:
    owner_status = text(owner_receipt.get("status"))
    publication_eval_ref = text(owner_receipt.get("publication_eval_ref")) or text(
        owner_receipt.get("publication_eval_record_ref")
    )
    return (
        owner_status in {"executed", "closed_with_domain_owner_refs"}
        and (
            text(owner_receipt.get("owner")) is not None
            or text(owner_receipt.get("authority")) is not None
        )
        and publication_eval_ref is not None
        and owner_receipt.get("publication_eval_latest_write_authorized") is not True
        and owner_receipt.get("controller_decision_write_authorized") is not True
        and owner_receipt.get("paper_package_mutation_allowed") is not True
        and owner_receipt.get("manual_study_patch_allowed") is not True
        and owner_receipt.get("medical_claim_authoring_allowed") is not True
        and owner_receipt.get("quality_gate_relaxation_allowed") is not True
        and owner_receipt.get("quality_authorized") is False
        and owner_receipt.get("submission_authorized") is False
        and owner_receipt.get("current_package_write_authorized") is False
    )


def read_dispatch_packet(*, profile: Any, dispatch_ref: str | None) -> dict[str, Any] | None:
    if dispatch_ref is None:
        return None
    return read_json_object(profile_ref_path(dispatch_ref, workspace_root=profile.workspace_root))


def profile_ref_path(ref: str, *, workspace_root: Any) -> Path:
    path = Path(ref).expanduser()
    if path.is_absolute():
        return path
    return Path(workspace_root).expanduser() / ref


def dispatch_packet_refs(
    *,
    dispatch_ref: str | None,
    dispatch_packet: Mapping[str, Any] | None,
    workspace_root: Any,
) -> list[str]:
    refs = [dispatch_ref]
    packet_refs = mapping(dispatch_packet.get("refs") if dispatch_packet is not None else None)
    refs.extend(
        [
            workspace_relative_ref(packet_refs.get("dispatch_path"), workspace_root=workspace_root),
            workspace_relative_ref(packet_refs.get("immutable_dispatch_path"), workspace_root=workspace_root),
            workspace_relative_ref(packet_refs.get("stage_packet_path"), workspace_root=workspace_root),
        ]
    )
    return unique(texts(refs))


def workspace_relative_ref(value: object, *, workspace_root: Any) -> str | None:
    path_text = text(value)
    if path_text is None:
        return None
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        return path_text
    try:
        return str(path.resolve().relative_to(Path(workspace_root).expanduser().resolve()))
    except (OSError, ValueError):
        return str(path.resolve())


def read_json_object(path: object) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))  # type: ignore[attr-defined]
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def write_json_object(path: object, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)  # type: ignore[attr-defined]
    path.write_text(  # type: ignore[attr-defined]
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
