from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.opl_artifact_operating_contract import (
    CONTRACT_REF as OPL_ARTIFACT_OPERATING_CONTRACT_REF,
    consumability_gate_projection,
    current_pointer_contract_projection,
    load_opl_artifact_operating_contract,
    operating_contract_projection,
    promotion_protocol_steps,
)
from med_autoscience.controllers.opl_physical_stage_kernel import (
    STAGE_ARTIFACT_RUNTIME_CONTRACT_REF,
    physical_artifact_classification,
    physical_stage_kernel_projection,
)
from med_autoscience.controllers.stage_artifact_index_parts.authority_projection import (
    authority_boundary as _authority_boundary,
    mas_authority_functions as _mas_authority_functions,
    provider_liveness as _provider_liveness,
    stale_platform_repairs as _stale_platform_repairs,
)
from med_autoscience.controllers.stage_artifact_index_parts.contract_refs import (
    contract_ref_set as _contract_ref_set,
    manifest_declared_support_refs as _manifest_declared_support_refs,
)
ALLOWED_ARTIFACT_STATUSES = (
    "missing",
    "missing_manifest_or_receipt",
    "partial",
    "artifact_delta_present",
    "ready_for_review",
    "blocked_by_required_artifact",
    "terminal_delivered",
)

_STATUS_MISSING = "missing"
_STATUS_MISSING_CONTRACT = "missing_manifest_or_receipt"
_STATUS_PARTIAL = "partial"
_STATUS_DELTA = "artifact_delta_present"
_STAGE_NATIVE_ARTIFACT_CONTRACT_REF = "mas-opl-stage-native-artifact-contract.v1"
_PAPER_STUDY_STAGE_PACK_REF = "contracts/mas-paper-study-stage-pack.json"
_PAPER_STUDY_STAGE_PACK_ROOT = Path(__file__).resolve().parents[3]
_MANIFEST_FILENAME = "stage_manifest.json"
_RECEIPT_FILENAME = "owner_receipt.json"
_RECEIPT_REF = f"receipts/{_RECEIPT_FILENAME}"


def build_stage_artifact_index(*, study_id: str, study_root: Path) -> dict[str, Any]:
    resolved_study_root = study_root.expanduser().resolve()
    operating_contract = load_opl_artifact_operating_contract()
    operating_projection = operating_contract_projection(operating_contract)
    promotion_protocol = promotion_protocol_steps(operating_contract)
    consumability_gate = consumability_gate_projection(operating_contract)
    current_pointer_contract = current_pointer_contract_projection(operating_contract)
    domain_stage_pack = _load_paper_study_stage_pack()
    stage_specs = _paper_study_stage_specs(domain_stage_pack)
    legacy_taxonomy_migration = _legacy_taxonomy_migration(domain_stage_pack)
    legacy_mappings_by_stage = _legacy_mappings_by_stage(legacy_taxonomy_migration)
    physical_kernel = physical_stage_kernel_projection(
        study_id=str(study_id),
        stage_ids=tuple(str(stage["stage_id"]) for stage in stage_specs),
        domain_stage_pack=domain_stage_pack,
    )
    stages = [
        _build_stage_artifact_state(
            stage_spec=stage_spec,
            legacy_stage_mappings=legacy_mappings_by_stage.get(str(stage_spec["stage_id"]), ()),
            study_root=resolved_study_root,
            operating_contract=operating_projection,
            promotion_protocol=promotion_protocol,
            consumability_gate=consumability_gate,
            physical_stage_kernel=_stage_physical_kernel(physical_kernel, str(stage_spec["stage_id"])),
        )
        for stage_spec in stage_specs
    ]
    current_stage = _current_stage(stages)
    stale_platform_repairs = _stale_platform_repairs(study_root=resolved_study_root, stages=stages)
    return {
        "schema_version": 1,
        "surface_kind": "stage_artifact_index",
        "stage_model": str(domain_stage_pack["stage_model"]),
        "domain_stage_pack_ref": _PAPER_STUDY_STAGE_PACK_REF,
        "stage_artifact_runtime_contract_ref": STAGE_ARTIFACT_RUNTIME_CONTRACT_REF,
        "study_id": str(study_id),
        "study_root": str(resolved_study_root),
        "allowed_artifact_statuses": list(ALLOWED_ARTIFACT_STATUSES),
        "artifact_native_contract_ref": _STAGE_NATIVE_ARTIFACT_CONTRACT_REF,
        "physical_stage_folder_kernel": physical_kernel,
        "operating_contract": operating_projection,
        "promotion_protocol": promotion_protocol,
        "consumability_gate": consumability_gate,
        "current_pointer_contract": current_pointer_contract,
        "authority_boundary": _authority_boundary(),
        "legacy_taxonomy_migration": legacy_taxonomy_migration,
        "current_stage": _current_stage_projection(current_stage),
        "next_owner_action": _next_owner_action(current_stage),
        "provider_liveness": _provider_liveness(study_root=resolved_study_root),
        "stale_platform_repairs": stale_platform_repairs,
        "stages": stages,
    }


def _stage_physical_kernel(
    physical_kernel: Mapping[str, Any],
    stage_id: str,
) -> dict[str, Any]:
    stages = physical_kernel.get("stages")
    if not isinstance(stages, Mapping):
        return {"status": "missing", "stage_id": stage_id}
    stage = stages.get(stage_id)
    return dict(stage) if isinstance(stage, Mapping) else {"status": "missing", "stage_id": stage_id}


def _build_stage_artifact_state(
    *,
    stage_spec: Mapping[str, Any],
    legacy_stage_mappings: tuple[Mapping[str, Any], ...],
    study_root: Path,
    operating_contract: Mapping[str, Any],
    promotion_protocol: list[str],
    consumability_gate: Mapping[str, Any],
    physical_stage_kernel: Mapping[str, Any],
) -> dict[str, Any]:
    stage_id = str(stage_spec["stage_id"])
    stage_folder_contract = _stage_folder_contract(stage_id, physical_stage_kernel=physical_stage_kernel)
    manifest_requirements = _manifest_requirements(stage_folder_contract)
    receipt_requirements = _receipt_requirements(stage_folder_contract)
    required_refs = [
        {
            "role": role,
            "ref": ref,
            "source": "mas_paper_study_stage_pack_stable_role",
            "role_contract_ref": role_contract_ref,
            "interface_is_artifact_role": True,
            "ref_is_locator_only": True,
            "body_included": False,
            "native_contract_required": True,
        }
        for role, ref, role_contract_ref in _required_output_surfaces(stage_spec)
    ]
    current_declared_observed_refs = [
        {
            "role": item["role"],
            "ref": item["ref"],
            "path": str(study_root / str(item["ref"])),
            "body_included": False,
            "classification": "declared_current_stage_role",
            "counts_as_current_artifact_delta": False,
        }
        for item in required_refs
        if (study_root / str(item["ref"])).exists()
    ]
    legacy_observed_refs = [
        {
            "legacy_route_id": str(item["legacy_route_id"]),
            "role": str(item["role"]),
            "target_role": str(item["target_role"]),
            "ref": str(item["ref"]),
            "path": str(study_root / str(item["ref"])),
            "body_included": False,
            "classification": "migration_historical_declared_ref",
            "projection_role": "migration_historical_declared_ref",
            "migration_semantics": "tombstone_backfilled_current_pointer",
            "workbench_display_current_truth": "paper_study_stage_pack",
            "legacy_route_is_current_truth": False,
            "counts_as_current_artifact_delta": False,
        }
        for item in _legacy_role_refs_for_stage(legacy_stage_mappings)
        if (study_root / str(item["ref"])).exists()
    ]
    declared_observed_refs = current_declared_observed_refs + legacy_observed_refs
    artifact_classification = _artifact_classification(
        stage_id=stage_id,
        stage_folder_contract=stage_folder_contract,
        manifest_requirements=manifest_requirements,
        receipt_requirements=receipt_requirements,
        required_refs=required_refs,
        legacy_observed_refs=declared_observed_refs,
        study_root=study_root,
        physical_stage_kernel=physical_stage_kernel,
    )
    observed_refs = [
        {
            "role": item["role"],
            "ref": item["ref"],
            "path": str(study_root / str(item["ref"])),
            "body_included": False,
            "classification": "current",
            "manifest_ref": manifest_requirements["ref"],
            "receipt_ref": receipt_requirements["ref"],
        }
        for item in required_refs
        if str(item["ref"]) in set(artifact_classification["current"])
    ]
    artifact_status = _artifact_status(required_refs=required_refs, observed_refs=observed_refs)
    if (
        artifact_status == _STATUS_MISSING
        and artifact_classification["missing_manifest_or_receipt"]
    ):
        artifact_status = _STATUS_MISSING_CONTRACT
    if artifact_status != _STATUS_DELTA and (
        artifact_classification["broken"] or artifact_classification["orphan"]
    ):
        artifact_status = "blocked_by_required_artifact"
    next_missing = _next_missing_surface(required_refs=required_refs, observed_refs=observed_refs)
    current_pointer = _current_pointer(
        stage_folder_contract=stage_folder_contract,
        artifact_classification=artifact_classification,
        operating_contract=operating_contract,
        promotion_protocol=promotion_protocol,
    )
    return {
        "surface_kind": "stage_artifact_state",
        "stage_id": stage_id,
        "display_name": str(stage_spec.get("display_name") or stage_id),
        "domain_stage_pack_ref": _PAPER_STUDY_STAGE_PACK_REF,
        "artifact_native_contract_ref": _STAGE_NATIVE_ARTIFACT_CONTRACT_REF,
        "stage_folder_contract": stage_folder_contract,
        "manifest_requirements": manifest_requirements,
        "receipt_requirements": receipt_requirements,
        "required_output_refs": required_refs,
        "observed_artifact_refs": observed_refs,
        "legacy_observed_artifact_refs": legacy_observed_refs,
        "artifact_classification": artifact_classification,
        "physical_stage_folder_kernel": dict(physical_stage_kernel),
        "current_pointer": current_pointer,
        "consumability_gate": _stage_consumability_gate(
            consumability_gate=consumability_gate,
            current_pointer=current_pointer,
        ),
        "artifact_status": artifact_status,
        "freshness": _freshness(artifact_status),
        "stage_progress_status": _stage_progress_status(artifact_status),
        "next_missing_surface": next_missing,
        "next_routes": list(stage_spec.get("next_stage_ids") or ()),
        "authority_boundary": _authority_boundary(),
    }


def _stage_folder_contract(
    stage_id: str,
    *,
    physical_stage_kernel: Mapping[str, Any],
) -> dict[str, Any]:
    if physical_stage_kernel.get("status") == "observed":
        return {
            "surface_kind": "stage_folder_contract",
            "contract_ref": f"{STAGE_ARTIFACT_RUNTIME_CONTRACT_REF}#/state_root_layout",
            "source_of_truth": "opl_physical_stage_folder_kernel",
            "stage_folder_ref": str(physical_stage_kernel["stage_folder_ref"]),
            "attempt_root": str(physical_stage_kernel["attempt_root"]),
            "manifest_ref": str(physical_stage_kernel["manifest_ref"]),
            "receipt_ref": str(physical_stage_kernel["receipt_ref"]),
            "current_pointer_ref": str(physical_stage_kernel["current_pointer_ref"]),
            "latest_pointer_ref": str(physical_stage_kernel["latest_pointer_ref"]),
            "legacy_declared_refs_fallback": False,
            "body_included": False,
            "authority_boundary": _authority_boundary(),
        }
    stage_folder_ref = f"artifacts/stage_outputs/{stage_id}"
    return {
        "surface_kind": "stage_folder_contract",
        "contract_ref": f"{_STAGE_NATIVE_ARTIFACT_CONTRACT_REF}#/stage_folder",
        "source_of_truth": "mas_declared_stage_artifact_projection",
        "stage_folder_ref": stage_folder_ref,
        "manifest_ref": f"{stage_folder_ref}/{_MANIFEST_FILENAME}",
        "receipt_ref": f"{stage_folder_ref}/{_RECEIPT_REF}",
        "legacy_declared_refs_fallback": True,
        "body_included": False,
        "authority_boundary": _authority_boundary(),
    }


def _manifest_requirements(stage_folder_contract: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": "stage_artifact_manifest_requirements",
        "contract_ref": f"{_STAGE_NATIVE_ARTIFACT_CONTRACT_REF}#/manifest",
        "required": True,
        "ref": str(stage_folder_contract["manifest_ref"]),
        "required_fields": ["surface_kind", "schema_version", "stage_id", "artifact_refs"],
        "artifact_refs_must_cover_required_outputs": True,
        "body_included": False,
    }


def _receipt_requirements(stage_folder_contract: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": "stage_artifact_receipt_requirements",
        "contract_ref": f"{_STAGE_NATIVE_ARTIFACT_CONTRACT_REF}#/receipt",
        "required": True,
        "ref": str(stage_folder_contract["receipt_ref"]),
        "required_fields": [
            "surface_kind",
            "schema_version",
            "stage_id",
            "owner",
            "receipt_kind",
            "artifact_refs",
        ],
        "artifact_refs_must_cover_required_outputs": True,
        "body_included": False,
    }


def _load_paper_study_stage_pack() -> dict[str, Any]:
    path = _PAPER_STUDY_STAGE_PACK_ROOT / _PAPER_STUDY_STAGE_PACK_REF
    payload = _read_contract_json(path)
    if payload is None or payload.get("_invalid_json") is True:
        raise ValueError(f"invalid paper/study stage pack contract: {_PAPER_STUDY_STAGE_PACK_REF}")
    _validate_paper_study_stage_pack(payload)
    return payload


def _validate_paper_study_stage_pack(payload: Mapping[str, Any]) -> None:
    if payload.get("surface_kind") != "mas_paper_study_stage_pack":
        raise ValueError("paper/study stage pack surface_kind mismatch")
    stages = payload.get("stages")
    if not isinstance(stages, list) or len(stages) != 8:
        raise ValueError("paper/study stage pack must declare exactly 8 stages")
    seen_stage_ids: set[str] = set()
    for stage in stages:
        if not isinstance(stage, Mapping):
            raise ValueError("paper/study stage entries must be mappings")
        stage_id = _text(stage.get("stage_id"))
        if stage_id is None:
            raise ValueError("paper/study stage entry missing stage_id")
        if stage_id in seen_stage_ids:
            raise ValueError(f"duplicate paper/study stage_id: {stage_id}")
        seen_stage_ids.add(stage_id)
        roles = stage.get("stable_artifact_roles")
        if not isinstance(roles, list) or not roles:
            raise ValueError(f"paper/study stage {stage_id} must declare stable artifact roles")
        for role in roles:
            if not isinstance(role, Mapping) or _text(role.get("role")) is None:
                raise ValueError(f"paper/study stage {stage_id} has invalid artifact role")
            if _text(role.get("artifact_ref")) is None:
                raise ValueError(f"paper/study stage {stage_id} has invalid artifact ref")
    boundary = payload.get("authority_boundary")
    if not isinstance(boundary, Mapping):
        raise ValueError("paper/study stage pack missing authority boundary")
    functions = _text_list(boundary.get("mas_authority_functions"))
    if functions != _mas_authority_functions():
        raise ValueError("paper/study stage pack authority functions mismatch")
    migration = payload.get("legacy_taxonomy_migration")
    if not isinstance(migration, Mapping):
        raise ValueError("paper/study stage pack missing legacy taxonomy migration")


def _paper_study_stage_specs(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    return tuple(stage for stage in payload["stages"] if isinstance(stage, Mapping))


def _legacy_taxonomy_migration(payload: Mapping[str, Any]) -> dict[str, Any]:
    migration = payload["legacy_taxonomy_migration"]
    if not isinstance(migration, Mapping):
        raise ValueError("legacy taxonomy migration must be a mapping")
    mappings = [
        _legacy_mapping_projection(item)
        for item in _mapping_items(migration.get("mappings"))
    ]
    role_mapping: dict[str, list[dict[str, str]]] = {}
    for item in mappings:
        stage_id = str(item["target_stage_id"])
        stage_roles = role_mapping.setdefault(stage_id, [])
        for role in item["legacy_artifact_roles"]:
            stage_roles.append(
                {
                    "legacy_route_id": str(item["legacy_route_id"]),
                    "legacy_role": str(role["role"]),
                    "legacy_ref": str(role["ref"]),
                    "target_role": str(role["target_role"]),
                }
            )
    policy = migration.get("current_truth_policy")
    if not isinstance(policy, Mapping):
        policy = {}
    return {
        "surface_kind": str(migration.get("surface_kind") or "mas_paper_study_legacy_taxonomy_migration"),
        "status": str(migration.get("status") or "migration_manifest"),
        "contract_ref": f"{_PAPER_STUDY_STAGE_PACK_REF}#/legacy_taxonomy_migration",
        "current_truth_policy": {
            "workbench_must_not_display_two_current_truths": bool(
                policy.get("workbench_must_not_display_two_current_truths", True)
            ),
            "legacy_route_is_current_truth": bool(policy.get("legacy_route_is_current_truth", False)),
            "current_truth_surface": str(policy.get("current_truth_surface") or "paper_study_stage_pack"),
            "legacy_semantics": str(
                policy.get("legacy_semantics") or "tombstone_backfilled_current_pointer"
            ),
        },
        "mappings": mappings,
        "role_mapping": role_mapping,
        "body_included": False,
        "authority_boundary": _authority_boundary(),
    }


def _legacy_mapping_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    legacy_route_id = _required_text(value.get("legacy_route_id"), "legacy_route_id")
    target_stage_id = _required_text(value.get("target_stage_id"), "target_stage_id")
    return {
        "legacy_route_id": legacy_route_id,
        "target_stage_id": target_stage_id,
        "migration_semantics": "tombstone_backfilled_current_pointer",
        "workbench_display_current_truth": "paper_study_stage_pack",
        "legacy_route_is_current_truth": False,
        "legacy_artifact_roles": [
            {
                "role": _required_text(role.get("role"), "role"),
                "ref": _required_text(role.get("ref"), "ref"),
                "target_role": _required_text(role.get("target_role"), "target_role"),
            }
            for role in _mapping_items(value.get("legacy_artifact_roles"))
        ],
    }


def _legacy_mappings_by_stage(
    legacy_taxonomy_migration: Mapping[str, Any],
) -> dict[str, tuple[Mapping[str, Any], ...]]:
    by_stage: dict[str, list[Mapping[str, Any]]] = {}
    for item in _mapping_items(legacy_taxonomy_migration.get("mappings")):
        stage_id = _text(item.get("target_stage_id"))
        if stage_id is None:
            continue
        by_stage.setdefault(stage_id, []).append(item)
    return {stage_id: tuple(items) for stage_id, items in by_stage.items()}


def _legacy_role_refs_for_stage(
    legacy_stage_mappings: tuple[Mapping[str, Any], ...],
) -> tuple[dict[str, str], ...]:
    refs: list[dict[str, str]] = []
    for mapping in legacy_stage_mappings:
        legacy_route_id = _required_text(mapping.get("legacy_route_id"), "legacy_route_id")
        for role in _mapping_items(mapping.get("legacy_artifact_roles")):
            refs.append(
                {
                    "legacy_route_id": legacy_route_id,
                    "role": _required_text(role.get("role"), "role"),
                    "target_role": _required_text(role.get("target_role"), "target_role"),
                    "ref": _required_text(role.get("ref"), "ref"),
                }
            )
    return tuple(refs)


def _artifact_classification(
    *,
    stage_id: str,
    stage_folder_contract: Mapping[str, Any],
    manifest_requirements: Mapping[str, Any],
    receipt_requirements: Mapping[str, Any],
    required_refs: list[dict[str, Any]],
    legacy_observed_refs: list[dict[str, Any]],
    study_root: Path,
    physical_stage_kernel: Mapping[str, Any],
) -> dict[str, Any]:
    if physical_stage_kernel.get("status") == "observed":
        del stage_id
        return physical_artifact_classification(
            stage_folder_contract=stage_folder_contract,
            physical_stage_kernel=physical_stage_kernel,
        )
    required = [str(item["ref"]) for item in required_refs]
    legacy_observed = [str(item["ref"]) for item in legacy_observed_refs]
    manifest_ref = str(manifest_requirements["ref"])
    receipt_ref = str(receipt_requirements["ref"])
    manifest = _read_contract_json(study_root / manifest_ref)
    receipt = _read_contract_json(study_root / receipt_ref)
    missing_contract_refs = [
        ref for ref, payload in ((manifest_ref, manifest), (receipt_ref, receipt)) if payload is None
    ]
    broken = _broken_contract_refs(
        stage_id=stage_id,
        required_refs=required,
        manifest_ref=manifest_ref,
        manifest=manifest,
        receipt_ref=receipt_ref,
        receipt=receipt,
    )
    orphan = _orphan_stage_artifact_refs(
        stage_folder_ref=str(stage_folder_contract["stage_folder_ref"]),
        required_refs=required,
        contract_refs=_contract_ref_set(
            stage_folder_ref=str(stage_folder_contract["stage_folder_ref"]),
            refs=[
                manifest_ref,
                receipt_ref,
                *_manifest_declared_support_refs(
                    manifest,
                    stage_folder_ref=str(stage_folder_contract["stage_folder_ref"]),
                ),
            ],
        ),
        study_root=study_root,
    )
    legacy_orphan_residue = _legacy_contract_residue_refs(
        stage_folder_ref=str(stage_folder_contract["stage_folder_ref"]),
        orphan_refs=orphan,
    )
    blocking_orphan = [ref for ref in orphan if ref not in set(legacy_orphan_residue)]
    existing_artifacts = set(required).issubset(legacy_observed)
    manifest_valid = _contract_payload_valid(
        stage_id=stage_id,
        required_refs=required,
        payload=manifest,
        required_fields=("surface_kind", "schema_version", "stage_id", "artifact_refs"),
    )
    receipt_accepted = _contract_payload_valid(
        stage_id=stage_id,
        required_refs=required,
        payload=receipt,
        required_fields=(
            "surface_kind",
            "schema_version",
            "stage_id",
            "owner",
            "receipt_kind",
            "artifact_refs",
        ),
    )
    contract_complete = existing_artifacts and manifest_valid and receipt_accepted and not blocking_orphan
    current = sorted(required) if contract_complete else []
    historical = sorted(ref for ref in legacy_observed if ref not in current)
    missing_outputs = sorted(ref for ref in required if ref not in legacy_observed)
    missing_manifest_or_receipt = sorted(historical) if missing_contract_refs else []
    status = _classification_status(
        current=current,
        historical=historical,
        missing_manifest_or_receipt=missing_manifest_or_receipt,
        broken=broken,
        orphan=blocking_orphan,
        missing_outputs=missing_outputs,
        required_refs=required,
    )
    return {
        "surface_kind": "stage_artifact_classification",
        "contract_ref": f"{_STAGE_NATIVE_ARTIFACT_CONTRACT_REF}#/classification",
        "status": status,
        "current": current,
        "historical": historical,
        "missing_manifest_or_receipt": missing_manifest_or_receipt,
        "orphan": blocking_orphan,
        "legacy_orphan_residue": legacy_orphan_residue,
        "broken": broken,
        "missing": missing_outputs,
        "fail_closed": status != "current",
        "fail_closed_reason": _fail_closed_reason(
            status=status,
            missing_contract_refs=missing_contract_refs,
            broken=broken,
            missing_outputs=missing_outputs,
        ),
        "manifest_ref": manifest_ref,
        "receipt_ref": receipt_ref,
        "current_pointer_basis": {
            "existing_artifacts": existing_artifacts,
            "manifest_valid": manifest_valid,
            "receipt_accepted": receipt_accepted,
        },
        "legacy_declared_refs_fallback": True,
        "source_of_truth": "mas_declared_stage_artifact_projection",
        "manifest_hash_refs": [],
        "evidence_hash_refs": [],
        "receipt_hash_refs": [],
        "owner_receipt_refs": [],
        "typed_blocker_refs": [],
        "decision_receipt_refs": [],
        "conformance_refs": {},
        "body_included": False,
    }


def _read_contract_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"_invalid_json": True}
    return dict(payload) if isinstance(payload, Mapping) else {"_invalid_json": True}


def _broken_contract_refs(
    *,
    stage_id: str,
    required_refs: list[str],
    manifest_ref: str,
    manifest: Mapping[str, Any] | None,
    receipt_ref: str,
    receipt: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    broken: list[dict[str, Any]] = []
    for ref, payload, required_fields in (
        (manifest_ref, manifest, ("surface_kind", "schema_version", "stage_id", "artifact_refs")),
        (
            receipt_ref,
            receipt,
            ("surface_kind", "schema_version", "stage_id", "owner", "receipt_kind", "artifact_refs"),
        ),
    ):
        if payload is None:
            continue
        if payload.get("_invalid_json") is True:
            broken.append({"ref": ref, "reason": "invalid_json_or_non_mapping"})
            continue
        missing_fields = [field for field in required_fields if field not in payload]
        if missing_fields:
            broken.append({"ref": ref, "reason": "missing_required_fields", "fields": missing_fields})
            continue
        if str(payload.get("stage_id")) != stage_id:
            broken.append({"ref": ref, "reason": "stage_id_mismatch", "expected_stage_id": stage_id})
            continue
        artifact_refs = _artifact_ref_set(payload.get("artifact_refs"))
        missing_artifact_refs = [required_ref for required_ref in required_refs if required_ref not in artifact_refs]
        if missing_artifact_refs:
            broken.append(
                {
                    "ref": ref,
                    "reason": "required_output_refs_not_declared",
                    "missing_refs": missing_artifact_refs,
                }
            )
    return broken


def _contract_payload_valid(
    *,
    stage_id: str,
    required_refs: list[str],
    payload: Mapping[str, Any] | None,
    required_fields: tuple[str, ...],
) -> bool:
    if payload is None or payload.get("_invalid_json") is True:
        return False
    if any(field not in payload for field in required_fields):
        return False
    if str(payload.get("stage_id")) != stage_id:
        return False
    artifact_refs = _artifact_ref_set(payload.get("artifact_refs"))
    return all(required_ref in artifact_refs for required_ref in required_refs)


def _artifact_ref_set(value: object) -> set[str]:
    if isinstance(value, str):
        text = value.strip()
        return {text} if text else set()
    if not isinstance(value, list | tuple | set):
        return set()
    refs: set[str] = set()
    for item in value:
        if isinstance(item, str) and item.strip():
            refs.add(item.strip())
        elif isinstance(item, Mapping) and isinstance(item.get("ref"), str) and item["ref"].strip():
            refs.add(item["ref"].strip())
    return refs


def _orphan_stage_artifact_refs(
    *,
    stage_folder_ref: str,
    required_refs: list[str],
    contract_refs: list[str],
    study_root: Path,
) -> list[str]:
    stage_folder = study_root / stage_folder_ref
    if not stage_folder.exists():
        return []
    known = set(required_refs) | set(contract_refs)
    orphan: list[str] = []
    for path in stage_folder.rglob("*"):
        if not path.is_file():
            continue
        ref = path.relative_to(study_root).as_posix()
        if ref not in known:
            orphan.append(ref)
    return sorted(orphan)


def _legacy_contract_residue_refs(*, stage_folder_ref: str, orphan_refs: list[str]) -> list[str]:
    retired_names = {
        "current.json",
        "owner_receipt.json",
        "stage_artifact_manifest.json",
        "typed_blocker.json",
    }
    return sorted(
        ref
        for ref in orphan_refs
        if ref.startswith(f"{stage_folder_ref}/") and Path(ref).name in retired_names
    )


def _classification_status(
    *,
    current: list[str],
    historical: list[str],
    missing_manifest_or_receipt: list[str],
    broken: list[dict[str, Any]],
    orphan: list[str],
    missing_outputs: list[str],
    required_refs: list[str],
) -> str:
    if broken:
        return "broken"
    if orphan:
        return "orphan"
    if current and len(current) == len(required_refs) and not missing_outputs:
        return "current"
    if missing_manifest_or_receipt:
        return "missing_manifest_or_receipt"
    if historical:
        return "historical"
    return "missing"


def _fail_closed_reason(
    *,
    status: str,
    missing_contract_refs: list[str],
    broken: list[dict[str, Any]],
    missing_outputs: list[str],
) -> str | None:
    if status == "current":
        return None
    if missing_contract_refs:
        return "missing_manifest_or_receipt"
    if broken:
        return "broken_stage_native_contract"
    if missing_outputs:
        return "missing_required_output"
    return status


def _required_output_surfaces(stage_spec: Mapping[str, Any]) -> tuple[tuple[str, str, str], ...]:
    stage_id = _required_text(stage_spec.get("stage_id"), "stage_id")
    surfaces: list[tuple[str, str, str]] = []
    for index, item in enumerate(_mapping_items(stage_spec.get("stable_artifact_roles"))):
        role = _required_text(item.get("role"), "role")
        ref = _required_text(item.get("artifact_ref"), "artifact_ref")
        role_contract_ref = (
            f"{_PAPER_STUDY_STAGE_PACK_REF}#/stages/{stage_id}/stable_artifact_roles/{index}"
        )
        surfaces.append((role, ref, role_contract_ref))
    return tuple(surfaces)


def _artifact_status(*, required_refs: list[dict[str, Any]], observed_refs: list[dict[str, Any]]) -> str:
    if not observed_refs:
        return _STATUS_MISSING
    if len(observed_refs) < len(required_refs):
        return _STATUS_PARTIAL
    return _STATUS_DELTA


def _stage_progress_status(artifact_status: str) -> str:
    if artifact_status == _STATUS_MISSING:
        return "artifact_required"
    if artifact_status == _STATUS_MISSING_CONTRACT:
        return "artifact_contract_required"
    if artifact_status == _STATUS_PARTIAL:
        return "artifact_partial"
    if artifact_status == "blocked_by_required_artifact":
        return "artifact_contract_broken"
    return "artifact_delta_present"


def _freshness(artifact_status: str) -> dict[str, Any]:
    if artifact_status == _STATUS_MISSING:
        return {
            "status": "red_missing",
            "meaning": "required stage artifact refs are missing",
            "blocks_auto_advance_by_default": False,
        }
    if artifact_status == _STATUS_PARTIAL:
        return {
            "status": "yellow_partial",
            "meaning": "some required stage artifact refs are present",
            "blocks_auto_advance_by_default": False,
        }
    if artifact_status == _STATUS_MISSING_CONTRACT:
        return {
            "status": "red_missing_manifest_or_receipt",
            "meaning": "legacy declared artifact refs exist but the stage-native manifest or receipt is missing",
            "blocks_auto_advance_by_default": True,
        }
    if artifact_status == "blocked_by_required_artifact":
        return {
            "status": "red_broken_stage_artifact_contract",
            "meaning": "stage-native artifact manifest or receipt is invalid",
            "blocks_auto_advance_by_default": True,
        }
    return {
        "status": "green_artifact_delta_present",
        "meaning": "required stage artifact refs are present",
        "blocks_auto_advance_by_default": False,
    }


def _next_missing_surface(
    *,
    required_refs: list[dict[str, Any]],
    observed_refs: list[dict[str, Any]],
) -> str | None:
    observed = {str(item["ref"]) for item in observed_refs}
    for item in required_refs:
        ref = str(item["ref"])
        if ref not in observed:
            return ref
    return None


def _current_pointer(
    *,
    stage_folder_contract: Mapping[str, Any],
    artifact_classification: Mapping[str, Any],
    operating_contract: Mapping[str, Any],
    promotion_protocol: list[str],
) -> dict[str, Any]:
    basis = dict(artifact_classification["current_pointer_basis"])
    promotion_state = _current_pointer_promotion_state(
        basis=basis,
        classification_status=str(artifact_classification["status"]),
    )
    return {
        "surface_kind": "stage_artifact_current_pointer_projection",
        "contract_ref": f"{OPL_ARTIFACT_OPERATING_CONTRACT_REF}#/current_pointer",
        "pointer_ref": str(
            stage_folder_contract.get("current_pointer_ref")
            or f"{stage_folder_contract['stage_folder_ref']}/current_pointer.json"
        ),
        "attempt_id": artifact_classification.get("latest_attempt_id"),
        "basis": basis,
        "progress_basis": list(operating_contract["progress_basis"]),
        "promotion_protocol": list(promotion_protocol),
        "promotion_state": promotion_state,
        "projection_rebuild_required": promotion_state == "current_pointer_promoted",
        "manifest_validity_is_semantic_receipt_validity": operating_contract[
            "manifest_validity_is_semantic_receipt_validity"
        ],
        "controller_read_model_currentness_role": operating_contract[
            "controller_read_model_currentness_role"
        ],
        "body_included": False,
    }


def _current_pointer_promotion_state(
    *,
    basis: Mapping[str, Any],
    classification_status: str,
) -> str:
    if basis.get("existing_artifacts") is not True:
        return "attempt_output_required"
    if basis.get("manifest_valid") is not True:
        return "manifest_required"
    if basis.get("receipt_accepted") is not True:
        return "receipt_required"
    if classification_status != "current":
        return "projection_blocked"
    return "current_pointer_promoted"


def _stage_consumability_gate(
    *,
    consumability_gate: Mapping[str, Any],
    current_pointer: Mapping[str, Any],
) -> dict[str, Any]:
    status = (
        "ready_for_consumability_validation"
        if current_pointer["promotion_state"] == "current_pointer_promoted"
        else "blocked"
    )
    return {
        **dict(consumability_gate),
        "status": status,
        "blocked_reason": None if status != "blocked" else current_pointer["promotion_state"],
        "current_pointer_promotion_state": current_pointer["promotion_state"],
    }


def _current_stage(stages: list[dict[str, Any]]) -> dict[str, Any]:
    furthest_observed_index = max(
        (
            index
            for index, stage in enumerate(stages)
            if stage["observed_artifact_refs"]
        ),
        default=-1,
    )
    if furthest_observed_index >= 0:
        for stage in stages[: furthest_observed_index + 1]:
            if not stage["observed_artifact_refs"]:
                return stage
        next_index = min(furthest_observed_index + 1, len(stages) - 1)
        return stages[next_index]
    for stage in stages:
        if stage["artifact_status"] != _STATUS_DELTA:
            return stage
    return stages[-1]


def _current_stage_projection(stage: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "stage_id": stage["stage_id"],
        "artifact_status": stage["artifact_status"],
        "stage_progress_status": stage["stage_progress_status"],
        "next_missing_surface": stage["next_missing_surface"],
    }


def _next_owner_action(stage: Mapping[str, Any]) -> dict[str, Any]:
    if stage["stage_id"] == "08-publication_package_handoff" and stage["artifact_status"] == _STATUS_DELTA:
        return {
            "owner": stage["stage_id"],
            "next_owner": "publication_gate_owner",
            "action_type": "publication_handoff_owner_gate",
            "allowed_actions": ["publication_handoff_owner_gate"],
            "required_delta_kind": "publication_handoff_owner_receipt_or_typed_blocker",
            "work_unit_id": "publication_handoff_owner_gate",
            "required_output_surface": None,
            "artifact_native_contract_ref": stage["artifact_native_contract_ref"],
            "domain_stage_pack_ref": stage["domain_stage_pack_ref"],
            "manifest_ref": stage["manifest_requirements"]["ref"],
            "receipt_ref": stage["receipt_requirements"]["ref"],
            "authority_boundary": _authority_boundary(),
            "artifact_first_authority": True,
            "terminal_publication_handoff": True,
            "owner_receipt_required": True,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_readiness": False,
            "can_authorize_submission_readiness": False,
        }
    if stage["artifact_status"] == _STATUS_DELTA and stage["next_missing_surface"] is None:
        return {}
    return {
        "owner": stage["stage_id"],
        "next_owner": stage["stage_id"],
        "action_type": "materialize_stage_artifact_delta",
        "allowed_actions": ["materialize_stage_artifact_delta"],
        "required_delta_kind": "stage_artifact_delta",
        "required_output_surface": stage["next_missing_surface"],
        "artifact_native_contract_ref": stage["artifact_native_contract_ref"],
        "domain_stage_pack_ref": stage["domain_stage_pack_ref"],
        "manifest_ref": stage["manifest_requirements"]["ref"],
        "receipt_ref": stage["receipt_requirements"]["ref"],
        "authority_boundary": _authority_boundary(),
        "artifact_first_authority": True,
        "owner_receipt_required": True,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
    }


def _mapping_items(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _required_text(value: object, field: str) -> str:
    text = _text(value)
    if text is None:
        raise ValueError(f"missing required text field: {field}")
    return text


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None:
            result.append(text)
    return result


__all__ = [
    "ALLOWED_ARTIFACT_STATUSES",
    "build_stage_artifact_index",
]
