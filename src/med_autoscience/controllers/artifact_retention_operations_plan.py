from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
import hashlib
from pathlib import Path
from typing import Any

from med_autoscience.controllers.body_free_evidence_packets import build_body_free_evidence_packet
from med_autoscience.controllers.artifact_retention_operations_plan_parts.physical_thinning_handoff import (
    PHYSICAL_THINNING_HANDOFF_SAMPLE_LIMIT,
    normalize_physical_thinning_handoff,
    physical_thinning_handoff,
    physical_thinning_handoff_from_summary,
)


SCHEMA_VERSION = 1
SURFACE_KIND = "artifact_retention_operations_plan"
TERMINAL_STUDY_SURFACE_KIND = "terminal_study_file_lifecycle_plan"
ALLOWED_PHYSICAL_ACTIONS = ("delete-safe-cache",)
DEFAULT_OPERATION_SAMPLE_LIMIT = 50
RECEIPT_REF_SAMPLE_LIMIT = 50
_RECEIPT_REF_FAMILY_KEYS = (
    "artifact_lifecycle_receipt_refs",
    "artifact_authority_receipt_refs",
    "cleanup_receipt_refs",
    "restore_proof_refs",
    "retention_receipt_refs",
)
_APPLY_BLOCKER_REF_KEY = "artifact_lifecycle_apply_blocker_refs"
_APPLY_BLOCKER_COUNT_KEY = "artifact_lifecycle_apply_blocker_ref_count"
_APPLY_BLOCKER_TRUNCATED_KEY = "artifact_lifecycle_apply_blocker_refs_truncated"
_APPLY_BLOCKER_REASON_COUNTS_KEY = "artifact_lifecycle_apply_blocker_reason_counts"
_APPLY_BLOCKER_AUTHORITY_BOUNDARY_KEY = "artifact_lifecycle_apply_blocker_authority_boundary"
_PHYSICAL_THINNING_HANDOFF_KEY = "physical_thinning_handoff"
_KEEP_ONLINE_ROLES = frozenset(
    {
        "canonical_source",
        "data_release",
        "audit_log",
        "human_handoff_mirror",
    }
)
_REGENERATE_BEFORE_REMOVE_MARKER = "regenerate-before-remove"
_TERMINAL_STOP_LOSS_REQUIRED_MACRO_STATE = {
    "writer_state": "parked",
    "user_next": "none",
    "reason": "stop_loss",
    "details.reopen_allowed": False,
}


def build_artifact_retention_operations_plan(
    *,
    workspace_root: Path,
    artifacts: Iterable[Mapping[str, Any]],
    terminal_study_compaction_eligible: bool = False,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    operations = [
        _retention_operation(workspace_root=resolved_workspace_root, artifact=dict(artifact))
        for artifact in artifacts
    ]
    if terminal_study_compaction_eligible:
        operations = [_terminal_retention_operation(operation) for operation in operations]
    receipt_ref_families = _artifact_lifecycle_receipt_ref_families(operations)
    apply_blocker_refs = _artifact_lifecycle_apply_blockers_from_operations(
        operations,
        sample_limit=RECEIPT_REF_SAMPLE_LIMIT,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "workspace_root": str(resolved_workspace_root),
        "mutation_policy": _mutation_policy(),
        "retention_policy_catalog": retention_policy_catalog(),
        "summary": _summary(operations),
        **receipt_ref_families,
        **apply_blocker_refs,
        _PHYSICAL_THINNING_HANDOFF_KEY: physical_thinning_handoff(
            operations,
            apply_blocker_refs=apply_blocker_refs,
            apply_blocker_ref_key=_APPLY_BLOCKER_REF_KEY,
            apply_blocker_count_key=_APPLY_BLOCKER_COUNT_KEY,
            apply_blocker_reason_counts_key=_APPLY_BLOCKER_REASON_COUNTS_KEY,
        ),
        "operations": operations,
    }


def aggregate_artifact_retention_operations_plans(
    plans: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    action_counts: dict[str, int] = {}
    applyable_action_counts: dict[str, int] = {}
    receipt_ref_families = _empty_artifact_lifecycle_receipt_ref_families()
    apply_blocker_refs = _empty_artifact_lifecycle_apply_blockers()
    physical_thinning_candidate_refs: list[str] = []
    physical_thinning_candidate_samples: list[Mapping[str, Any]] = []
    operation_count = 0
    for plan in plans:
        summary = _mapping(plan.get("summary"))
        operation_count += int(summary.get("operation_count") or 0)
        _merge_counts(action_counts, _mapping(summary.get("action_counts")))
        _merge_counts(applyable_action_counts, _mapping(summary.get("applyable_action_counts")))
        _merge_artifact_lifecycle_receipt_ref_families(
            receipt_ref_families,
            _artifact_lifecycle_receipt_ref_families_from_plan(
                plan,
                sample_limit=RECEIPT_REF_SAMPLE_LIMIT,
            ),
        )
        handoff = _mapping(plan.get(_PHYSICAL_THINNING_HANDOFF_KEY))
        physical_thinning_candidate_refs.extend(_string_list(handoff.get("candidate_refs")))
        physical_thinning_candidate_samples.extend(
            item for item in _list(handoff.get("candidate_sample")) if isinstance(item, Mapping)
        )
        _merge_artifact_lifecycle_apply_blockers(
            apply_blocker_refs,
            _artifact_lifecycle_apply_blockers_from_plan(
                plan,
                sample_limit=RECEIPT_REF_SAMPLE_LIMIT,
            ),
        )
    receipt_ref_families = _bounded_artifact_lifecycle_receipt_ref_families(
        receipt_ref_families,
        sample_limit=RECEIPT_REF_SAMPLE_LIMIT,
    )
    apply_blocker_refs = _bounded_artifact_lifecycle_apply_blockers(
        apply_blocker_refs,
        sample_limit=RECEIPT_REF_SAMPLE_LIMIT,
    )
    return {
        "surface_kind": SURFACE_KIND,
        "summary": {
            "operation_count": operation_count,
            "action_counts": dict(sorted(action_counts.items())),
            "applyable_action_counts": dict(sorted(applyable_action_counts.items())),
        },
        "mutation_policy": _mutation_policy(),
        "retention_policy_catalog": retention_policy_catalog(),
        **receipt_ref_families,
        **apply_blocker_refs,
        _PHYSICAL_THINNING_HANDOFF_KEY: physical_thinning_handoff_from_summary(
            summary={
                "operation_count": operation_count,
                "action_counts": action_counts,
                "applyable_action_counts": applyable_action_counts,
            },
            apply_blocker_refs=apply_blocker_refs,
            apply_blocker_ref_key=_APPLY_BLOCKER_REF_KEY,
            apply_blocker_count_key=_APPLY_BLOCKER_COUNT_KEY,
            apply_blocker_reason_counts_key=_APPLY_BLOCKER_REASON_COUNTS_KEY,
            candidate_refs=physical_thinning_candidate_refs,
            candidate_samples=physical_thinning_candidate_samples,
        ),
    }


def compact_artifact_retention_operations_plan(
    plan: Mapping[str, Any],
    *,
    operation_sample_limit: int = DEFAULT_OPERATION_SAMPLE_LIMIT,
) -> dict[str, Any]:
    operations = _list(plan.get("operations"))
    sample = operations[:operation_sample_limit]
    receipt_ref_families = _artifact_lifecycle_receipt_ref_families_from_plan(
        plan,
        sample_limit=RECEIPT_REF_SAMPLE_LIMIT,
    )
    apply_blocker_refs = _artifact_lifecycle_apply_blockers_from_plan(
        plan,
        sample_limit=RECEIPT_REF_SAMPLE_LIMIT,
    )
    return {
        "schema_version": int(plan.get("schema_version") or SCHEMA_VERSION),
        "surface_kind": _text(plan.get("surface_kind")) or SURFACE_KIND,
        "workspace_root": _text(plan.get("workspace_root")),
        "mutation_policy": dict(_mapping(plan.get("mutation_policy"))) or _mutation_policy(),
        "retention_policy_catalog": dict(_mapping(plan.get("retention_policy_catalog")))
        or retention_policy_catalog(),
        "summary": dict(_mapping(plan.get("summary"))),
        **receipt_ref_families,
        **apply_blocker_refs,
        _PHYSICAL_THINNING_HANDOFF_KEY: _physical_thinning_handoff_from_plan(
            plan,
            apply_blocker_refs=apply_blocker_refs,
        ),
        "operation_listing": "bounded",
        "operation_sample": [dict(item) for item in sample if isinstance(item, Mapping)],
        "operation_sample_limit": operation_sample_limit,
        "operation_sample_truncated": len(operations) > operation_sample_limit,
    }


def build_terminal_study_file_lifecycle_plan(
    *,
    workspace_root: Path,
    study_root: Path,
    study_macro_state: Mapping[str, Any],
    artifacts: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_study_root = Path(study_root).expanduser().resolve()
    macro_state = dict(study_macro_state)
    eligible, blockers = _terminal_stop_loss_eligibility(macro_state)
    retention_plan = build_artifact_retention_operations_plan(
        workspace_root=resolved_workspace_root,
        artifacts=artifacts,
        terminal_study_compaction_eligible=eligible,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": TERMINAL_STUDY_SURFACE_KIND,
        "mode": "dry_run",
        "workspace_root": str(resolved_workspace_root),
        "study_root": str(resolved_study_root),
        "eligible": eligible,
        "eligibility": {
            "required_macro_state": dict(_TERMINAL_STOP_LOSS_REQUIRED_MACRO_STATE),
            "blockers": blockers,
        },
        "study_macro_state": macro_state,
        "archive_manifest_contract": _terminal_archive_manifest_contract(),
        "preserve_roles": sorted(_KEEP_ONLINE_ROLES),
        "mutation_policy": _mutation_policy(),
        "retention_plan": retention_plan,
        "candidate_summary": _terminal_candidate_summary(_list(retention_plan.get("operations"))),
    }


def _retention_operation(*, workspace_root: Path, artifact: Mapping[str, Any]) -> dict[str, Any]:
    role = _text(artifact.get("role"))
    lifecycle = _text(artifact.get("lifecycle"))
    cleanup_candidate_action = _text(artifact.get("cleanup_candidate_action") or artifact.get("cleanup_candidate"))
    blockers = _string_list(artifact.get("cleanup_blockers"))
    base = {
        "path": _artifact_path(artifact),
        "workspace_relative_path": _workspace_relative_path(artifact, workspace_root),
        "role": role,
        "lifecycle": lifecycle,
        "cleanup_candidate_action": cleanup_candidate_action,
        "blockers": blockers,
        "physical_delete_allowed": False,
        "physical_archive_compress_allowed": False,
        "canonical_regeneration_gate": {"required": False, "status": "not_required"},
        "restore_contract_gate": {"required": False, "status": "not_required"},
        "projection_status": "not_projection",
        "runtime_retention_mode": "not_runtime",
    }
    base["body_free_evidence_packet"] = _artifact_lifecycle_packet(
        workspace_root=workspace_root,
        operation=base,
    )
    if cleanup_candidate_action == "delete-safe-cache":
        payload = {
            **base,
            "retention_action": "delete_safe_cache",
            "physical_delete_allowed": True,
            "target_sha256": _target_sha256(base["path"]),
        }
        return _with_artifact_lifecycle_packet(workspace_root=workspace_root, operation=payload)
    if role in _KEEP_ONLINE_ROLES or cleanup_candidate_action == "keep-online":
        payload = {
            **base,
            "retention_action": "keep_online",
        }
        return _with_artifact_lifecycle_packet(workspace_root=workspace_root, operation=payload)
    if role == "derived_projection" or lifecycle == "rebuildable_projection":
        payload = {
            **base,
            "retention_action": "regenerate_projection_then_remove_stale",
            "removal_marker": _REGENERATE_BEFORE_REMOVE_MARKER,
            "projection_status": "stale_or_rebuildable_projection",
            "canonical_regeneration_gate": {
                "required": True,
                "status": "required_before_physical_removal",
            },
            "blockers": _dedupe(
                [
                    *blockers,
                    "canonical_regeneration_required_before_projection_removal",
                ]
            ),
        }
        return _with_artifact_lifecycle_packet(workspace_root=workspace_root, operation=payload)
    if role == "runtime_ephemeral" and cleanup_candidate_action == "archive-compress":
        payload = {
            **base,
            "retention_action": "archive_compress_candidate_blocked",
            "runtime_retention_mode": "terminal_archive_compress_candidate",
            "restore_contract_gate": {
                "required": True,
                "status": "apply_implementation_required",
            },
            "blockers": _dedupe(
                [
                    *blockers,
                    "physical_archive_compress_not_open",
                    "restore_contract_apply_implementation_required",
                ]
            ),
        }
        return _with_artifact_lifecycle_packet(workspace_root=workspace_root, operation=payload)
    if role == "runtime_ephemeral":
        payload = {
            **base,
            "retention_action": "keep_online",
            "runtime_retention_mode": "audit_only",
        }
        return _with_artifact_lifecycle_packet(workspace_root=workspace_root, operation=payload)
    if role == "cold_archive" or cleanup_candidate_action == "restore-gated":
        payload = {
            **base,
            "retention_action": "restore_contract_required",
            "restore_contract_gate": {
                "required": True,
                "status": "required_before_cleanup",
            },
        }
        return _with_artifact_lifecycle_packet(workspace_root=workspace_root, operation=payload)
    payload = {
        **base,
        "retention_action": "keep_online",
    }
    return _with_artifact_lifecycle_packet(workspace_root=workspace_root, operation=payload)


def _terminal_retention_operation(operation: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(operation)
    if (
        _text(payload.get("role")) == "runtime_ephemeral"
        and _text(payload.get("cleanup_candidate_action")) == "archive-compress"
    ):
        blockers = _string_list(payload.get("blockers"))
        updated = {
            **payload,
            "retention_action": "terminal_archive_compact_after_manifest",
            "runtime_retention_mode": "terminal_archive_compact_after_manifest",
            "physical_archive_compress_allowed": False,
            "restore_contract_gate": {
                "required": True,
                "status": "manifest_and_restore_proof_required_before_apply",
            },
            "blockers": _dedupe(
                [
                    *blockers,
                    "terminal_stop_loss_manifest_required",
                    "restore_proof_required_before_terminal_compaction_apply",
                ]
            ),
        }
        workspace_root = Path(_text(updated.get("path")) or ".").resolve()
        return {
            **updated,
            "body_free_evidence_packet": _artifact_lifecycle_packet(
                workspace_root=workspace_root,
                operation=updated,
            ),
        }
    return payload


def _with_artifact_lifecycle_packet(*, workspace_root: Path, operation: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(operation)
    payload["body_free_evidence_packet"] = _artifact_lifecycle_packet(
        workspace_root=workspace_root,
        operation=payload,
    )
    apply_blocker_reasons = _artifact_lifecycle_apply_blocker_reasons(payload)
    if apply_blocker_reasons:
        payload["artifact_lifecycle_apply_blocker_reasons"] = apply_blocker_reasons
        payload["artifact_lifecycle_apply_blocker_refs"] = [
            _artifact_lifecycle_apply_blocker_ref(
                workspace_root=workspace_root,
                operation=payload,
                reason=reason,
            )
            for reason in apply_blocker_reasons
        ]
    return payload


def _artifact_lifecycle_packet(*, workspace_root: Path, operation: Mapping[str, Any]) -> dict[str, Any]:
    role = _text(operation.get("role"))
    action = _text(operation.get("retention_action")) or _text(operation.get("cleanup_candidate_action"))
    packet_role = _artifact_lifecycle_packet_role(action=action, role=role)
    relative_ref = _text(operation.get("workspace_relative_path")) or _workspace_relative_path(operation, workspace_root)
    receipt_id = f"artifact-lifecycle:{packet_role}:{_fingerprint_text(relative_ref or _text(operation.get('path')))}"
    return build_body_free_evidence_packet(
        ref=relative_ref or _text(operation.get("path")),
        role=packet_role,
        owner="MedAutoScience",
        receipt_id=receipt_id,
    )


def _artifact_lifecycle_packet_role(*, action: str, role: str) -> str:
    if action in {"regenerate_projection_then_remove_stale", "delete_safe_cache"}:
        return "artifact_mutation_receipt_ref"
    if action in {"restore_contract_required", "archive_compress_candidate_blocked", "terminal_archive_compact_after_manifest"}:
        return "artifact_restore_receipt_ref"
    if role in {"canonical_source", "data_release", "audit_log", "human_handoff_mirror"} or action == "keep_online":
        return "artifact_retention_receipt_ref"
    return "artifact_lifecycle_receipt_ref"


def _summary(operations: list[Mapping[str, Any]]) -> dict[str, Any]:
    action_counts = Counter(str(operation.get("retention_action") or "") for operation in operations)
    applyable_action_counts = Counter(
        str(operation.get("retention_action") or "")
        for operation in operations
        if bool(operation.get("physical_delete_allowed"))
    )
    return {
        "operation_count": len(operations),
        "action_counts": dict(sorted(action_counts.items())),
        "applyable_action_counts": dict(sorted(applyable_action_counts.items())),
    }


def _artifact_lifecycle_receipt_ref_families(operations: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    families = _empty_artifact_lifecycle_receipt_ref_families()
    for operation in operations:
        packet = _mapping(operation.get("body_free_evidence_packet"))
        receipt_id = _text(packet.get("receipt_id"))
        if not receipt_id:
            continue
        role = _text(packet.get("role"))
        action = _text(operation.get("retention_action"))
        families["artifact_lifecycle_receipt_refs"].append(receipt_id)
        families["artifact_authority_receipt_refs"].append(receipt_id)
        if action == "delete_safe_cache":
            families["cleanup_receipt_refs"].append(receipt_id)
        if role == "artifact_restore_receipt_ref":
            families["restore_proof_refs"].append(receipt_id)
        if role == "artifact_retention_receipt_ref":
            families["retention_receipt_refs"].append(receipt_id)
    return _bounded_artifact_lifecycle_receipt_ref_families(
        families,
        sample_limit=RECEIPT_REF_SAMPLE_LIMIT,
    )


def _artifact_lifecycle_receipt_ref_families_from_plan(
    plan: Mapping[str, Any],
    *,
    sample_limit: int | None = None,
) -> dict[str, Any]:
    existing = _empty_artifact_lifecycle_receipt_ref_families()
    for key in _RECEIPT_REF_FAMILY_KEYS:
        refs = _string_list(plan.get(key))
        existing[key] = refs
        existing[_receipt_count_key(key)] = _int(plan.get(_receipt_count_key(key))) or len(refs)
        existing[_receipt_truncated_key(key)] = bool(plan.get(_receipt_truncated_key(key)))
    if any(existing.values()):
        return _bounded_artifact_lifecycle_receipt_ref_families(
            existing,
            sample_limit=sample_limit,
        )
    operations = [
        operation
        for operation in [*_list(plan.get("operations")), *_list(plan.get("operation_sample"))]
        if isinstance(operation, Mapping)
    ]
    return _bounded_artifact_lifecycle_receipt_ref_families(
        _artifact_lifecycle_receipt_ref_families(operations),
        sample_limit=sample_limit,
    )


def _artifact_lifecycle_apply_blockers_from_plan(
    plan: Mapping[str, Any],
    *,
    sample_limit: int | None = None,
) -> dict[str, Any]:
    existing = _empty_artifact_lifecycle_apply_blockers()
    refs = _string_list(plan.get(_APPLY_BLOCKER_REF_KEY))
    reason_counts = _mapping(plan.get(_APPLY_BLOCKER_REASON_COUNTS_KEY))
    if refs or _int(plan.get(_APPLY_BLOCKER_COUNT_KEY)) or reason_counts:
        existing[_APPLY_BLOCKER_REF_KEY] = refs
        existing[_APPLY_BLOCKER_COUNT_KEY] = _int(plan.get(_APPLY_BLOCKER_COUNT_KEY)) or len(refs)
        existing[_APPLY_BLOCKER_TRUNCATED_KEY] = bool(plan.get(_APPLY_BLOCKER_TRUNCATED_KEY))
        existing[_APPLY_BLOCKER_REASON_COUNTS_KEY] = {
            str(reason): _int(count)
            for reason, count in reason_counts.items()
            if str(reason) and _int(count)
        }
        return _bounded_artifact_lifecycle_apply_blockers(existing, sample_limit=sample_limit)
    operations = [
        operation
        for operation in [*_list(plan.get("operations")), *_list(plan.get("operation_sample"))]
        if isinstance(operation, Mapping)
    ]
    return _artifact_lifecycle_apply_blockers_from_operations(operations, sample_limit=sample_limit)


def _artifact_lifecycle_apply_blockers_from_operations(
    operations: Iterable[Mapping[str, Any]],
    *,
    sample_limit: int | None = None,
) -> dict[str, Any]:
    blocker_refs = _empty_artifact_lifecycle_apply_blockers()
    seen: set[str] = set()
    for operation in operations:
        for reason in _artifact_lifecycle_apply_blocker_reasons(operation):
            ref = _artifact_lifecycle_apply_blocker_ref(
                workspace_root=Path(_text(operation.get("path")) or ".").resolve(),
                operation=operation,
                reason=reason,
            )
            if ref in seen:
                continue
            seen.add(ref)
            blocker_refs[_APPLY_BLOCKER_REF_KEY].append(ref)
            reason_counts = blocker_refs[_APPLY_BLOCKER_REASON_COUNTS_KEY]
            reason_counts[reason] = _int(reason_counts.get(reason)) + 1
    blocker_refs[_APPLY_BLOCKER_COUNT_KEY] = len(blocker_refs[_APPLY_BLOCKER_REF_KEY])
    return _bounded_artifact_lifecycle_apply_blockers(blocker_refs, sample_limit=sample_limit)


def _artifact_lifecycle_apply_blocker_reasons(operation: Mapping[str, Any]) -> list[str]:
    blockers = _string_list(operation.get("blockers"))
    if blockers:
        return blockers
    action = _text(operation.get("retention_action"))
    if action == "delete_safe_cache":
        return ["cleanup_apply_authority_required_before_safe_cache_delete"]
    if action == "restore_contract_required" or bool(_mapping(operation.get("restore_contract_gate")).get("required")):
        return ["restore_contract_required_before_cleanup"]
    return []


def _artifact_lifecycle_apply_blocker_ref(
    *,
    workspace_root: Path,
    operation: Mapping[str, Any],
    reason: str,
) -> str:
    relative_ref = _text(operation.get("workspace_relative_path")) or _workspace_relative_path(
        operation,
        workspace_root,
    )
    digest = _fingerprint_text(f"{reason}\0{relative_ref or _text(operation.get('path'))}")
    return f"mas-artifact-lifecycle-typed-blocker:medautoscience:{_slug(reason)}:{digest}"


def _empty_artifact_lifecycle_apply_blockers() -> dict[str, Any]:
    return {
        _APPLY_BLOCKER_REF_KEY: [],
        _APPLY_BLOCKER_COUNT_KEY: 0,
        _APPLY_BLOCKER_TRUNCATED_KEY: False,
        _APPLY_BLOCKER_REASON_COUNTS_KEY: {},
        _APPLY_BLOCKER_AUTHORITY_BOUNDARY_KEY: _artifact_lifecycle_apply_blocker_authority_boundary(),
    }


def _bounded_artifact_lifecycle_apply_blockers(
    blocker_refs: Mapping[str, Any],
    *,
    sample_limit: int | None = None,
) -> dict[str, Any]:
    refs = _dedupe(_string_list(blocker_refs.get(_APPLY_BLOCKER_REF_KEY)))
    count = _int(blocker_refs.get(_APPLY_BLOCKER_COUNT_KEY)) or len(refs)
    limit = sample_limit if sample_limit is not None else len(refs)
    bounded_refs = refs[:limit]
    reason_counts = {
        str(reason): _int(value)
        for reason, value in _mapping(blocker_refs.get(_APPLY_BLOCKER_REASON_COUNTS_KEY)).items()
        if str(reason) and _int(value)
    }
    return {
        _APPLY_BLOCKER_REF_KEY: bounded_refs,
        _APPLY_BLOCKER_COUNT_KEY: max(count, len(refs)),
        _APPLY_BLOCKER_TRUNCATED_KEY: bool(blocker_refs.get(_APPLY_BLOCKER_TRUNCATED_KEY))
        or len(refs) > len(bounded_refs),
        _APPLY_BLOCKER_REASON_COUNTS_KEY: dict(sorted(reason_counts.items())),
        _APPLY_BLOCKER_AUTHORITY_BOUNDARY_KEY: _artifact_lifecycle_apply_blocker_authority_boundary(),
    }


def _merge_artifact_lifecycle_apply_blockers(
    target: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    target[_APPLY_BLOCKER_REF_KEY] = _dedupe(
        [
            *_string_list(target.get(_APPLY_BLOCKER_REF_KEY)),
            *_string_list(source.get(_APPLY_BLOCKER_REF_KEY)),
        ]
    )
    target[_APPLY_BLOCKER_COUNT_KEY] = _int(target.get(_APPLY_BLOCKER_COUNT_KEY)) + (
        _int(source.get(_APPLY_BLOCKER_COUNT_KEY))
        or len(_string_list(source.get(_APPLY_BLOCKER_REF_KEY)))
    )
    target[_APPLY_BLOCKER_TRUNCATED_KEY] = bool(target.get(_APPLY_BLOCKER_TRUNCATED_KEY)) or bool(
        source.get(_APPLY_BLOCKER_TRUNCATED_KEY)
    )
    reason_counts = dict(_mapping(target.get(_APPLY_BLOCKER_REASON_COUNTS_KEY)))
    for reason, value in _mapping(source.get(_APPLY_BLOCKER_REASON_COUNTS_KEY)).items():
        reason_counts[str(reason)] = _int(reason_counts.get(str(reason))) + _int(value)
    target[_APPLY_BLOCKER_REASON_COUNTS_KEY] = reason_counts


def _physical_thinning_handoff_from_plan(
    plan: Mapping[str, Any],
    *,
    apply_blocker_refs: Mapping[str, Any],
) -> dict[str, Any]:
    existing = _mapping(plan.get(_PHYSICAL_THINNING_HANDOFF_KEY))
    if existing:
        return normalize_physical_thinning_handoff(
            existing,
            apply_blocker_refs=apply_blocker_refs,
            apply_blocker_ref_key=_APPLY_BLOCKER_REF_KEY,
            apply_blocker_count_key=_APPLY_BLOCKER_COUNT_KEY,
            apply_blocker_reason_counts_key=_APPLY_BLOCKER_REASON_COUNTS_KEY,
        )
    operations = [
        operation
        for operation in [*_list(plan.get("operations")), *_list(plan.get("operation_sample"))]
        if isinstance(operation, Mapping)
    ]
    if operations:
        return physical_thinning_handoff(
            operations,
            apply_blocker_refs=apply_blocker_refs,
            apply_blocker_ref_key=_APPLY_BLOCKER_REF_KEY,
            apply_blocker_count_key=_APPLY_BLOCKER_COUNT_KEY,
            apply_blocker_reason_counts_key=_APPLY_BLOCKER_REASON_COUNTS_KEY,
        )
    return physical_thinning_handoff_from_summary(
        summary=_mapping(plan.get("summary")),
        apply_blocker_refs=apply_blocker_refs,
        apply_blocker_ref_key=_APPLY_BLOCKER_REF_KEY,
        apply_blocker_count_key=_APPLY_BLOCKER_COUNT_KEY,
        apply_blocker_reason_counts_key=_APPLY_BLOCKER_REASON_COUNTS_KEY,
    )


def _artifact_lifecycle_apply_blocker_authority_boundary() -> dict[str, Any]:
    return {
        "owner": "MedAutoScience",
        "stable_typed_blocker_refs_only": True,
        "read_only": True,
        "writes_workspace": False,
        "physical_cleanup_performed": False,
        "can_authorize_cleanup_apply": False,
        "can_authorize_artifact_mutation": False,
        "can_claim_domain_ready": False,
        "can_claim_production_ready": False,
    }


def _empty_artifact_lifecycle_receipt_ref_families() -> dict[str, Any]:
    families: dict[str, Any] = {}
    for key in _RECEIPT_REF_FAMILY_KEYS:
        families[key] = []
        families[_receipt_count_key(key)] = 0
        families[_receipt_truncated_key(key)] = False
    return families


def _bounded_artifact_lifecycle_receipt_ref_families(
    families: Mapping[str, Any],
    *,
    sample_limit: int | None = None,
) -> dict[str, Any]:
    bounded = _empty_artifact_lifecycle_receipt_ref_families()
    for key in _RECEIPT_REF_FAMILY_KEYS:
        refs = _dedupe(_string_list(families.get(key)))
        count_key = _receipt_count_key(key)
        truncated_key = _receipt_truncated_key(key)
        count = _int(families.get(count_key)) or len(refs)
        limit = sample_limit if sample_limit is not None else len(refs)
        bounded_refs = refs[:limit]
        bounded[key] = bounded_refs
        bounded[count_key] = max(count, len(refs))
        bounded[truncated_key] = bool(families.get(truncated_key)) or len(refs) > len(bounded_refs)
    return bounded


def _merge_artifact_lifecycle_receipt_ref_families(
    target: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    for key in _RECEIPT_REF_FAMILY_KEYS:
        count_key = _receipt_count_key(key)
        truncated_key = _receipt_truncated_key(key)
        target[key] = _dedupe([*_string_list(target.get(key)), *_string_list(source.get(key))])
        target[count_key] = _int(target.get(count_key)) + (
            _int(source.get(count_key)) or len(_string_list(source.get(key)))
        )
        target[truncated_key] = bool(target.get(truncated_key)) or bool(source.get(truncated_key))


def _receipt_count_key(key: str) -> str:
    return key.removesuffix("_refs") + "_ref_count"


def _receipt_truncated_key(key: str) -> str:
    return f"{key}_truncated"


def _terminal_stop_loss_eligibility(macro_state: Mapping[str, Any]) -> tuple[bool, list[str]]:
    details = _mapping(macro_state.get("details"))
    eligible = (
        _text(macro_state.get("writer_state")) == "parked"
        and _text(macro_state.get("user_next")) == "none"
        and _text(macro_state.get("reason")) == "stop_loss"
        and details.get("reopen_allowed") is False
    )
    if eligible:
        return True, []
    return False, ["macro_state_not_terminal_non_reopenable_stop_loss"]


def _terminal_archive_manifest_contract() -> dict[str, Any]:
    return {
        "required": True,
        "format": "manifest_with_sha256_and_restore_index",
        "restore_proof_required": True,
        "summary_required": True,
    }


def _terminal_candidate_summary(operations: list[object]) -> dict[str, int]:
    runtime_count = 0
    projection_count = 0
    for item in operations:
        operation = _mapping(item)
        action = _text(operation.get("retention_action"))
        if action == "terminal_archive_compact_after_manifest":
            runtime_count += 1
        if action == "regenerate_projection_then_remove_stale":
            projection_count += 1
    return {
        "runtime_archive_compact_candidates": runtime_count,
        "derived_projection_refresh_candidates": projection_count,
    }


def _mutation_policy() -> dict[str, Any]:
    return {
        "read_only": True,
        "writes_workspace": False,
        "physical_cleanup_performed": False,
        "allowed_physical_actions": list(ALLOWED_PHYSICAL_ACTIONS),
        "archive_compress_apply_supported": False,
    }


def retention_policy_catalog() -> dict[str, Any]:
    return {
        "default_keep_online_roles": sorted(_KEEP_ONLINE_ROLES),
        "derived_projection_removal_marker": _REGENERATE_BEFORE_REMOVE_MARKER,
        "derived_projection_rule": "regenerate_projection_then_remove_stale",
        "live_runtime_rule": "audit-only",
        "payload_restore_gate": {
            "required_fields": [
                "restore_index_path",
                "sha256",
                "rehydrate_verification.status=verified",
            ],
            "status": "required_before_physical_cleanup",
        },
        "physical_apply_allowlist": list(ALLOWED_PHYSICAL_ACTIONS),
        "report_default": {
            "read_only": True,
            "operation_listing": "bounded",
        },
    }


def _artifact_path(artifact: Mapping[str, Any]) -> str:
    raw_path = _text(artifact.get("path"))
    return raw_path


def _target_sha256(path_text: str) -> str | None:
    path = Path(path_text)
    if not path.exists():
        return None
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(child.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _fingerprint_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _slug(value: str) -> str:
    text = value.lower().replace("_", "-")
    return "".join(character if character.isalnum() or character == "-" else "-" for character in text).strip("-")


def _workspace_relative_path(artifact: Mapping[str, Any], workspace_root: Path) -> str:
    raw_relative = _text(artifact.get("workspace_relative_path"))
    if raw_relative:
        return raw_relative
    raw_path = _text(artifact.get("path"))
    if not raw_path:
        return ""
    path = Path(raw_path)
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(workspace_root))
        except ValueError:
            return str(path)
    return str(path)


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _merge_counts(target: dict[str, int], values: Mapping[str, Any]) -> None:
    for key, value in values.items():
        target[str(key)] = target.get(str(key), 0) + int(value or 0)


__all__ = [
    "ALLOWED_PHYSICAL_ACTIONS",
    "DEFAULT_OPERATION_SAMPLE_LIMIT",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "TERMINAL_STUDY_SURFACE_KIND",
    "aggregate_artifact_retention_operations_plans",
    "build_artifact_retention_operations_plan",
    "build_terminal_study_file_lifecycle_plan",
    "compact_artifact_retention_operations_plan",
    "retention_policy_catalog",
]
