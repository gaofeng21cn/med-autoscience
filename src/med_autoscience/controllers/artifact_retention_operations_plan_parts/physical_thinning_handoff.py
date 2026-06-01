from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
import hashlib
from typing import Any


PHYSICAL_THINNING_HANDOFF_SAMPLE_LIMIT = 25
PHYSICAL_THINNING_CANDIDATE_ACTIONS = frozenset(
    {
        "delete_safe_cache",
        "regenerate_projection_then_remove_stale",
        "restore_contract_required",
        "archive_compress_candidate_blocked",
        "terminal_archive_compact_after_manifest",
    }
)


def physical_thinning_handoff(
    operations: Iterable[Mapping[str, Any]],
    *,
    apply_blocker_refs: Mapping[str, Any],
    apply_blocker_ref_key: str,
    apply_blocker_count_key: str,
    apply_blocker_reason_counts_key: str,
) -> dict[str, Any]:
    candidate_counts: Counter[str] = Counter()
    candidate_refs: list[str] = []
    candidate_samples: list[dict[str, Any]] = []
    for operation in operations:
        action = _text(operation.get("retention_action"))
        if action in PHYSICAL_THINNING_CANDIDATE_ACTIONS:
            candidate_counts[action] += 1
            candidate_refs.append(_physical_thinning_candidate_ref(operation))
            if len(candidate_samples) < PHYSICAL_THINNING_HANDOFF_SAMPLE_LIMIT:
                candidate_samples.append(_physical_thinning_candidate_sample(operation))
    return physical_thinning_handoff_from_counts(
        candidate_counts=candidate_counts,
        apply_blocker_refs=apply_blocker_refs,
        apply_blocker_ref_key=apply_blocker_ref_key,
        apply_blocker_count_key=apply_blocker_count_key,
        apply_blocker_reason_counts_key=apply_blocker_reason_counts_key,
        candidate_refs=candidate_refs,
        candidate_samples=candidate_samples,
    )


def physical_thinning_handoff_from_summary(
    *,
    summary: Mapping[str, Any],
    apply_blocker_refs: Mapping[str, Any],
    apply_blocker_ref_key: str,
    apply_blocker_count_key: str,
    apply_blocker_reason_counts_key: str,
    candidate_refs: Iterable[str] = (),
    candidate_samples: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    action_counts = _mapping(summary.get("action_counts"))
    candidate_counts = Counter(
        {
            action: _int(count)
            for action, count in action_counts.items()
            if str(action) in PHYSICAL_THINNING_CANDIDATE_ACTIONS and _int(count)
        }
    )
    return physical_thinning_handoff_from_counts(
        candidate_counts=candidate_counts,
        apply_blocker_refs=apply_blocker_refs,
        apply_blocker_ref_key=apply_blocker_ref_key,
        apply_blocker_count_key=apply_blocker_count_key,
        apply_blocker_reason_counts_key=apply_blocker_reason_counts_key,
        candidate_refs=candidate_refs,
        candidate_samples=candidate_samples,
    )


def normalize_physical_thinning_handoff(
    handoff: Mapping[str, Any],
    *,
    apply_blocker_refs: Mapping[str, Any],
    apply_blocker_ref_key: str,
    apply_blocker_count_key: str,
    apply_blocker_reason_counts_key: str,
) -> dict[str, Any]:
    candidate_counts = Counter(
        {
            str(action): _int(count)
            for action, count in _mapping(handoff.get("candidate_counts_by_action")).items()
            if str(action) and _int(count)
        }
    )
    if not candidate_counts and _int(handoff.get("candidate_count")):
        candidate_counts["unknown"] = _int(handoff.get("candidate_count"))
    normalized = physical_thinning_handoff_from_counts(
        candidate_counts=candidate_counts,
        apply_blocker_refs=apply_blocker_refs,
        apply_blocker_ref_key=apply_blocker_ref_key,
        apply_blocker_count_key=apply_blocker_count_key,
        apply_blocker_reason_counts_key=apply_blocker_reason_counts_key,
        candidate_refs=_string_list(handoff.get("candidate_refs")),
        candidate_samples=[
            item for item in _list(handoff.get("candidate_sample")) if isinstance(item, Mapping)
        ],
    )
    receipt_refs = _string_list(handoff.get("receipt_refs"))
    if receipt_refs:
        normalized["receipt_refs"] = receipt_refs
        normalized["selected_payload_path"] = "success_refs_path"
    return normalized


def physical_thinning_handoff_from_counts(
    *,
    candidate_counts: Counter[str],
    apply_blocker_refs: Mapping[str, Any],
    apply_blocker_ref_key: str,
    apply_blocker_count_key: str,
    apply_blocker_reason_counts_key: str,
    candidate_refs: Iterable[str] = (),
    candidate_samples: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    typed_blocker_refs = _string_list(apply_blocker_refs.get(apply_blocker_ref_key))
    candidate_count = sum(candidate_counts.values())
    bounded_candidate_refs, candidate_refs_truncated = _bounded_strings(
        candidate_refs,
        limit=PHYSICAL_THINNING_HANDOFF_SAMPLE_LIMIT,
    )
    bounded_candidate_samples = [
        dict(item)
        for item in list(candidate_samples)[:PHYSICAL_THINNING_HANDOFF_SAMPLE_LIMIT]
        if isinstance(item, Mapping)
    ]
    selected_payload_path = "typed_blocker_path" if typed_blocker_refs else "success_refs_path"
    handoff_ref = _physical_thinning_handoff_ref(
        candidate_counts=candidate_counts,
        typed_blocker_refs=typed_blocker_refs,
        candidate_refs=bounded_candidate_refs,
    )
    return {
        "surface_kind": "artifact_lifecycle_physical_thinning_handoff",
        "domain_owner": "MedAutoScience",
        "apply_owner": "one-person-lab",
        "handoff_ref": handoff_ref,
        "handoff_ref_role": "artifact_lifecycle_physical_thinning_handoff_ref",
        "body_free": True,
        "candidate_count": candidate_count,
        "candidate_counts_by_action": dict(sorted(candidate_counts.items())),
        "candidate_refs": bounded_candidate_refs,
        "candidate_ref_count": max(candidate_count, len(_dedupe(_string_list(candidate_refs)))),
        "candidate_refs_truncated": candidate_refs_truncated or candidate_count > len(bounded_candidate_refs),
        "candidate_sample": bounded_candidate_samples,
        "candidate_sample_limit": PHYSICAL_THINNING_HANDOFF_SAMPLE_LIMIT,
        "candidate_sample_truncated": candidate_count > len(bounded_candidate_samples),
        "selected_payload_path": selected_payload_path,
        "receipt_refs": [] if typed_blocker_refs else _string_list(apply_blocker_refs.get("cleanup_receipt_refs")),
        "typed_blocker_refs": typed_blocker_refs,
        "typed_blocker_ref_count": _int(apply_blocker_refs.get(apply_blocker_count_key)),
        "typed_blocker_reason_counts": dict(
            _mapping(apply_blocker_refs.get(apply_blocker_reason_counts_key))
        ),
        "next_owner_action": {
            "owner": "one-person-lab",
            "action": "generic_lifecycle_apply",
            "requires_restore_or_regeneration_receipt_before_cleanup": True,
            "accepts_handoff_ref": handoff_ref,
            "selected_payload_path": selected_payload_path,
        },
        "authority_boundary": physical_thinning_handoff_authority_boundary(),
    }


def physical_thinning_handoff_authority_boundary() -> dict[str, Any]:
    return {
        "mas_authorizes_candidate_identity": True,
        "mas_executes_physical_cleanup": False,
        "opl_executes_generic_lifecycle_apply": True,
        "requires_restore_or_regeneration_receipt_before_cleanup": True,
        "can_authorize_artifact_mutation": False,
        "can_claim_domain_ready": False,
        "can_claim_production_ready": False,
    }


def _physical_thinning_candidate_ref(operation: Mapping[str, Any]) -> str:
    action = _text(operation.get("retention_action"))
    relative_ref = _text(operation.get("workspace_relative_path")) or _text(operation.get("path"))
    digest = _fingerprint_text(f"{action}\0{relative_ref}")
    return f"mas-artifact-lifecycle-candidate:medautoscience:{_slug(action)}:{digest}"


def _physical_thinning_candidate_sample(operation: Mapping[str, Any]) -> dict[str, Any]:
    sample = {
        "candidate_ref": _physical_thinning_candidate_ref(operation),
        "workspace_relative_path": _text(operation.get("workspace_relative_path")),
        "retention_action": _text(operation.get("retention_action")),
        "role": _text(operation.get("role")),
        "lifecycle": _text(operation.get("lifecycle")),
        "physical_delete_allowed": bool(operation.get("physical_delete_allowed")),
        "physical_archive_compress_allowed": bool(operation.get("physical_archive_compress_allowed")),
        "blocker_refs": _string_list(operation.get("artifact_lifecycle_apply_blocker_refs")),
        "blockers": _string_list(operation.get("blockers")),
        "canonical_regeneration_gate": dict(_mapping(operation.get("canonical_regeneration_gate"))),
        "restore_contract_gate": dict(_mapping(operation.get("restore_contract_gate"))),
    }
    return {key: value for key, value in sample.items() if value not in ("", [], {})}


def _physical_thinning_handoff_ref(
    *,
    candidate_counts: Mapping[str, int],
    typed_blocker_refs: Iterable[str],
    candidate_refs: Iterable[str],
) -> str:
    basis = "|".join(
        [
            *[f"{key}={_int(value)}" for key, value in sorted(candidate_counts.items())],
            *sorted(_string_list(typed_blocker_refs)),
            *sorted(_string_list(candidate_refs)),
        ]
    )
    return f"mas-artifact-lifecycle-handoff:medautoscience:physical-thinning:{_fingerprint_text(basis)}"


def _bounded_strings(values: Iterable[str], *, limit: int) -> tuple[list[str], bool]:
    deduped = _dedupe([str(item).strip() for item in values if str(item).strip()])
    bounded = deduped[:limit]
    return bounded, len(deduped) > len(bounded)


def _fingerprint_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _slug(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace("_", "-")
        .replace(" ", "-")
        .replace("/", "-")
        or "unknown"
    )


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


__all__ = [
    "PHYSICAL_THINNING_HANDOFF_SAMPLE_LIMIT",
    "normalize_physical_thinning_handoff",
    "physical_thinning_handoff",
    "physical_thinning_handoff_from_summary",
]
