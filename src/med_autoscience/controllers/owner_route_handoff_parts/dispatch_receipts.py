from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable, Mapping

from med_autoscience.profiles import WorkspaceProfile


JsonReader = Callable[[Path], dict[str, Any] | None]
JsonWriter = Callable[[Path, Mapping[str, Any]], None]
RelativePath = Callable[[Path], str]
Now = Callable[[], str]
Text = Callable[[object], str | None]
MappingCoercer = Callable[[object], Mapping[str, Any]]
ForbiddenWriteGuardBuilder = Callable[..., Mapping[str, Any]]
AuthorityBoundaryBuilder = Callable[[], Mapping[str, Any]]


def write_dispatch_receipt(
    *,
    receipt: dict[str, Any],
    profile: WorkspaceProfile | None,
    task_id: str,
    source_fingerprint: str | None = None,
    owner_capability_fingerprint: str | None = None,
    read_json_object: JsonReader,
    write_json: JsonWriter,
    workspace_relative: RelativePath,
    text: Text,
    mapping: MappingCoercer,
    now_iso: Now,
    authority_boundary_payload: AuthorityBoundaryBuilder,
    forbidden_write_guard_proof: ForbiddenWriteGuardBuilder,
) -> dict[str, Any]:
    if profile is None:
        return receipt
    if owner_capability_fingerprint:
        receipt["owner_capability_fingerprint"] = owner_capability_fingerprint
    path = _receipt_path(
        profile=profile,
        task_id=task_id,
        source_fingerprint=source_fingerprint,
        owner_capability_fingerprint=owner_capability_fingerprint,
    )
    if path.exists():
        existing = read_json_object(path)
        if existing is not None:
            existing_result = mapping(mapping(existing.get("dispatch")).get("result"))
            new_result = mapping(mapping(receipt.get("dispatch")).get("result"))
            if text(existing_result.get("source_fingerprint")) != text(new_result.get("source_fingerprint")):
                return _conflicting_dispatch_receipt(
                    existing=existing,
                    receipt=receipt,
                    path=path,
                    workspace_relative=workspace_relative,
                    text=text,
                    mapping=mapping,
                    now_iso=now_iso,
                    authority_boundary_payload=authority_boundary_payload,
                    forbidden_write_guard_proof=forbidden_write_guard_proof,
                )
            existing["idempotent_noop"] = True
            return existing
    receipt["receipt_ref"] = workspace_relative(path)
    write_json(path, receipt)
    return receipt


def _receipt_path(
    *,
    profile: WorkspaceProfile,
    task_id: str,
    source_fingerprint: str | None = None,
    owner_capability_fingerprint: str | None = None,
) -> Path:
    parts = [task_id]
    if source_fingerprint is not None:
        parts.append(source_fingerprint)
    if owner_capability_fingerprint is not None:
        parts.append(owner_capability_fingerprint)
    receipt_key = ":".join(parts)
    digest = hashlib.sha256(receipt_key.encode("utf-8")).hexdigest()[:20]
    return profile.workspace_root / "artifacts" / "runtime" / "opl_family_sidecar" / "dispatch_receipts" / f"{digest}.json"


def _conflicting_dispatch_receipt(
    *,
    existing: Mapping[str, Any],
    receipt: Mapping[str, Any],
    path: Path,
    workspace_relative: RelativePath,
    text: Text,
    mapping: MappingCoercer,
    now_iso: Now,
    authority_boundary_payload: AuthorityBoundaryBuilder,
    forbidden_write_guard_proof: ForbiddenWriteGuardBuilder,
) -> dict[str, Any]:
    existing_result = mapping(mapping(existing.get("dispatch")).get("result"))
    new_result = mapping(mapping(receipt.get("dispatch")).get("result"))
    return {
        "surface_kind": "mas_family_sidecar_dispatch_receipt",
        "version": "mas-family-sidecar.v1",
        "accepted": False,
        "task_id": text(receipt.get("task_id")) or text(existing.get("task_id")),
        "task_kind": text(receipt.get("task_kind")) or text(existing.get("task_kind")),
        "generated_at": now_iso(),
        "reason": "idempotency_key_intent_conflict",
        "existing_receipt_ref": workspace_relative(path),
        "existing_source_fingerprint": text(existing_result.get("source_fingerprint")),
        "requested_source_fingerprint": text(new_result.get("source_fingerprint")),
        "forbidden_domain_truth_write": False,
        "authority_boundary": dict(authority_boundary_payload()),
        "forbidden_write_guard_proof": dict(
            forbidden_write_guard_proof(
                result="blocked",
                task_id=text(receipt.get("task_id")),
                task_kind=text(receipt.get("task_kind")),
                requested_writes=(),
            )
        ),
    }


__all__ = ["write_dispatch_receipt"]
