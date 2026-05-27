from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)
from med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export_parts.shared import (
    authority_boundary as dispatch_authority_boundary,
    mapping,
    sequence,
    text,
    texts,
    unique,
)


SURFACE_KIND = "mas_stage_production_evidence_payload_export"
TASK_KIND = "stage_production_evidence"
PAYLOAD_REASON = "stage_production_evidence_typed_blocker_pending_real_owner_receipt_or_monitor_freshness"
SUCCESS_PAYLOAD_REASON = "stage_production_evidence_review_quality_gate_refs_observed"


def build_stage_evidence_payload_export(
    *,
    profile: Any,
    profile_ref: object,
    workorder: Mapping[str, Any],
) -> dict[str, Any]:
    stage_id = text(workorder.get("stage_id"))
    if stage_id is None:
        return _blocked(
            profile=profile,
            profile_ref=profile_ref,
            workorder=workorder,
            blocked_reason="workorder_stage_id_missing",
        )
    if text(workorder.get("command_domain_id")) != "medautoscience":
        return _blocked(
            profile=profile,
            profile_ref=profile_ref,
            workorder=workorder,
            blocked_reason="workorder_domain_not_medautoscience",
        )

    success_path_requires = mapping(workorder.get("success_path_requires"))
    source_scope_refs = _required_refs(success_path_requires, "source_scope_refs_cover")
    runtime_event_refs = _required_refs(success_path_requires, "runtime_event_refs_cover")
    monitor_freshness_refs = _required_refs(
        success_path_requires,
        "evidence_refs_cover_monitor_freshness",
    )
    expected_receipt_refs = unique(
        [
            *texts(sequence(success_path_requires.get("domain_receipt_refs_cover"))),
            *texts(
                sequence(
                    success_path_requires.get(
                        "domain_receipt_instance_required_for_declared_refs"
                    )
                )
            ),
        ]
    )
    evidence_refs = unique(
        [
            text(workorder.get("request_id")),
            text(workorder.get("request_pack_id")),
            text(workorder.get("action_id")),
            *monitor_freshness_refs,
            *source_scope_refs,
            *runtime_event_refs,
        ]
    )
    typed_blocker_ref = _typed_blocker_ref(stage_id)
    no_regression_ref = (
        "mas-no-forbidden-write-proof:medautoscience:"
        f"stage-production-evidence:{stage_id}:refs-only-payload"
    )
    success_receipt_refs = _stage_success_receipt_refs(profile=profile, stage_id=stage_id)
    if success_receipt_refs:
        evidence_payload = build_domain_dispatch_evidence_record_payload(
            task_kind=TASK_KIND,
            stage_id=stage_id,
            stage_evidence_stage_id=stage_id,
            reason=SUCCESS_PAYLOAD_REASON,
            evidence_refs=[*evidence_refs, *success_receipt_refs],
            domain_owner_receipt_refs=success_receipt_refs,
            no_regression_evidence_refs=[no_regression_ref],
            expected_receipt_refs=success_receipt_refs,
            monitor_freshness_refs=monitor_freshness_refs,
            runtime_event_refs=runtime_event_refs,
            source_fingerprint=_source_fingerprint(workorder),
            profile_name=profile.name,
        )
        opl_payload = {
            "domain_receipt_refs": success_receipt_refs,
            "evidence_refs": monitor_freshness_refs,
            "typed_blocker_refs": [],
            "no_regression_refs": [no_regression_ref],
            "owner_chain_refs": success_receipt_refs,
            "source_scope_refs": source_scope_refs,
            "runtime_event_refs": runtime_event_refs,
        }
        return {
            "surface_kind": SURFACE_KIND,
            "status": "success_payload_ready",
            "profile": str(profile_ref),
            "profile_name": profile.name,
            "workorder_action_id": text(workorder.get("action_id")),
            "request_id": text(workorder.get("request_id")),
            "request_pack_id": text(workorder.get("request_pack_id")),
            "stage_id": stage_id,
            "payload_reason": SUCCESS_PAYLOAD_REASON,
            "stage_expected_receipt_refs": success_receipt_refs,
            "stage_monitor_freshness_refs": monitor_freshness_refs,
            "stage_source_scope_refs": source_scope_refs,
            "stage_runtime_event_refs": runtime_event_refs,
            "domain_dispatch_evidence_record_payload": evidence_payload,
            "opl_runtime_action_execute_payload": opl_payload,
            "authority_boundary": authority_boundary(
                payload_kind="refs_only_stage_production_evidence_success_payload"
            ),
        }
    evidence_payload = build_domain_dispatch_evidence_record_payload(
        task_kind=TASK_KIND,
        stage_id=stage_id,
        stage_evidence_stage_id=stage_id,
        reason=PAYLOAD_REASON,
        evidence_refs=evidence_refs,
        typed_blocker_refs=[typed_blocker_ref],
        no_regression_evidence_refs=[no_regression_ref],
        expected_receipt_refs=expected_receipt_refs,
        monitor_freshness_refs=monitor_freshness_refs,
        runtime_event_refs=runtime_event_refs,
        source_fingerprint=_source_fingerprint(workorder),
        profile_name=profile.name,
    )
    opl_payload = {
        "domain_receipt_refs": [],
        "evidence_refs": [],
        "typed_blocker_refs": [typed_blocker_ref],
        "no_regression_refs": [no_regression_ref],
        "owner_chain_refs": [],
        "source_scope_refs": [],
        "runtime_event_refs": [],
    }
    return {
        "surface_kind": SURFACE_KIND,
        "status": "typed_blocker_payload_ready",
        "profile": str(profile_ref),
        "profile_name": profile.name,
        "workorder_action_id": text(workorder.get("action_id")),
        "request_id": text(workorder.get("request_id")),
        "request_pack_id": text(workorder.get("request_pack_id")),
        "stage_id": stage_id,
        "payload_reason": PAYLOAD_REASON,
        "stage_expected_receipt_refs": expected_receipt_refs,
        "stage_monitor_freshness_refs": monitor_freshness_refs,
        "stage_source_scope_refs": source_scope_refs,
        "stage_runtime_event_refs": runtime_event_refs,
        "domain_dispatch_evidence_record_payload": evidence_payload,
        "opl_runtime_action_execute_payload": opl_payload,
        "authority_boundary": authority_boundary(
            payload_kind="refs_only_stage_production_evidence_typed_blocker_payload"
        ),
    }


def _blocked(
    *,
    profile: Any,
    profile_ref: object,
    workorder: Mapping[str, Any],
    blocked_reason: str,
) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "status": "blocked",
        "blocked_reason": blocked_reason,
        "profile": str(profile_ref),
        "profile_name": profile.name,
        "workorder_action_id": text(workorder.get("action_id")),
        "request_id": text(workorder.get("request_id")),
        "request_pack_id": text(workorder.get("request_pack_id")),
        "stage_id": text(workorder.get("stage_id")),
        "authority_boundary": authority_boundary(payload_kind="blocked"),
    }


def _required_refs(payload: Mapping[str, Any], key: str) -> list[str]:
    return texts(sequence(payload.get(key)))


def _typed_blocker_ref(stage_id: str) -> str:
    return (
        "mas-stage-typed-blocker:"
        f"medautoscience:{stage_id}:"
        "real-paper-line-owner-receipt-or-monitor-freshness-pending"
    )


def _stage_success_receipt_refs(*, profile: Any, stage_id: str) -> list[str]:
    if stage_id != "review_and_quality_gate":
        return []
    studies_root = getattr(profile, "studies_root", None)
    if not isinstance(studies_root, Path) or not studies_root.exists():
        return []
    refs: list[str] = []
    for study_root in sorted(path for path in studies_root.iterdir() if path.is_dir()):
        publication_eval_ref = study_root / "artifacts" / "publication_eval" / "latest.json"
        payload = _read_json_mapping(publication_eval_ref)
        provenance = mapping(payload.get("assessment_provenance"))
        reviewer_os = mapping(payload.get("reviewer_operating_system"))
        if (
            text(provenance.get("owner")) == "ai_reviewer"
            and text(payload.get("eval_id"))
            and reviewer_os
        ):
            refs.append(str(publication_eval_ref))
    return unique(refs)


def _read_json_mapping(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _source_fingerprint(workorder: Mapping[str, Any]) -> str:
    explicit = text(workorder.get("source_fingerprint"))
    if explicit:
        return explicit
    return ":".join(
        value
        for value in (
            text(workorder.get("request_id")),
            text(workorder.get("request_pack_id")),
            text(workorder.get("action_id")),
            text(workorder.get("stage_id")),
        )
        if value
    )


def authority_boundary(*, payload_kind: str = "refs_only_stage_production_evidence_payload") -> dict[str, object]:
    return {
        **dispatch_authority_boundary(),
        "payload_kind": payload_kind,
        "creates_owner_receipt": False,
        "claims_stage_ready": False,
        "claims_monitor_freshness": False,
    }


__all__ = ["build_stage_evidence_payload_export"]
