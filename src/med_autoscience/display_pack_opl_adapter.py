from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.display_pack_loader import (
    LoadedDisplayTemplate,
    load_enabled_local_display_template_records,
)


DESCRIPTOR_MEDIA_TYPE = "application/vnd.opl.pack.descriptor.v1+json"
PACK_OS_CONTRACT_REF = "one-person-lab:contracts/opl-framework/pack-os-contract.json#descriptor_contract"
MAS_DISPLAY_PACK_CONTRACT_REF = "contracts/display-pack-contract.v2.json"
ADAPTER_CONTRACT_REF = "contracts/display_pack_opl_adapter.json"

_AUTHORITY_BOUNDARY = {
    "can_write_domain_truth": False,
    "can_mutate_artifact_body": False,
    "can_sign_domain_owner_receipt": False,
    "can_authorize_quality_verdict": False,
    "can_authorize_publication_readiness": False,
    "can_authorize_grant_readiness": False,
    "can_authorize_visual_export_readiness": False,
    "can_authorize_app_release_readiness": False,
    "provider_completion_is_pack_quality_ready": False,
}


def build_display_pack_opl_adapter_contract() -> dict[str, Any]:
    return {
        "surface_kind": "mas_display_pack_opl_adapter_contract",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "source_contract_ref": MAS_DISPLAY_PACK_CONTRACT_REF,
        "target_contract_ref": PACK_OS_CONTRACT_REF,
        "descriptor_media_type": DESCRIPTOR_MEDIA_TYPE,
        "adapter_callable": (
            "med_autoscience.display_pack_opl_adapter."
            "write_enabled_opl_generic_pack_descriptors"
        ),
        "domain_action": "display-pack-capability-discover",
        "domain_action_output_field": "opl_pack_descriptor_refs",
        "generic_descriptor_required_fields": [
            "schema_version",
            "pack_id",
            "version",
            "pack_kind",
            "owner",
            "capabilities",
            "resources",
            "artifact_lifecycle",
            "review_transport",
            "authority_boundary",
            "provenance",
        ],
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }


def build_enabled_opl_generic_pack_descriptors(
    *,
    repo_root: Path,
    paper_root: Path | None = None,
) -> list[dict[str, Any]]:
    records = load_enabled_local_display_template_records(
        Path(repo_root).expanduser().resolve(),
        paper_root=paper_root,
        inventory_scope="all",
    )
    return build_opl_generic_pack_descriptors(records)


def build_opl_generic_pack_descriptors(
    records: Sequence[LoadedDisplayTemplate],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, Path], list[LoadedDisplayTemplate]] = {}
    for record in records:
        key = (record.pack_manifest.pack_id, record.pack_root.resolve())
        grouped.setdefault(key, []).append(record)
    return [
        _build_descriptor(group)
        for _, group in sorted(grouped.items(), key=lambda item: item[0][0])
    ]


def write_enabled_opl_generic_pack_descriptors(
    *,
    repo_root: Path,
    output_dir: Path,
    paper_root: Path | None = None,
) -> list[dict[str, Any]]:
    descriptors = build_enabled_opl_generic_pack_descriptors(
        repo_root=repo_root,
        paper_root=paper_root,
    )
    return write_opl_generic_pack_descriptors(
        descriptors=descriptors,
        output_dir=output_dir,
    )


def write_opl_generic_pack_descriptors(
    *,
    descriptors: Sequence[Mapping[str, Any]],
    output_dir: Path,
) -> list[dict[str, Any]]:
    normalized_output_dir = Path(output_dir).expanduser().resolve()
    normalized_output_dir.mkdir(parents=True, exist_ok=True)
    refs: list[dict[str, Any]] = []
    for descriptor in descriptors:
        filename = f"{_filename_part(descriptor['pack_id'])}@{_filename_part(descriptor['version'])}.json"
        path = normalized_output_dir / filename
        path.write_text(
            json.dumps(descriptor, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        refs.append(
            {
                "pack_id": descriptor["pack_id"],
                "version": descriptor["version"],
                "descriptor_ref": str(path),
                "descriptor_media_type": DESCRIPTOR_MEDIA_TYPE,
                "target_contract_ref": PACK_OS_CONTRACT_REF,
            }
        )
    return refs


def _build_descriptor(records: Sequence[LoadedDisplayTemplate]) -> dict[str, Any]:
    if not records:
        raise ValueError("Display Pack -> OPL adapter requires at least one template record")
    ordered = sorted(records, key=lambda item: item.template_manifest.full_template_id)
    sample = ordered[0]
    manifest = sample.pack_manifest
    source = sample.source_config
    source_ref = _text(source.source_ref) or sample.pack_root.resolve().as_uri()
    capabilities = []
    resources: list[dict[str, str]] = [
        {
            "resource_id": "pack.descriptor",
            "role": "descriptor",
            "ref": _join_ref(source_ref, "display_pack.toml"),
        },
        {
            "resource_id": "mas.display_pack_contract",
            "role": "schema",
            "ref": f"mas:{MAS_DISPLAY_PACK_CONTRACT_REF}",
        },
    ]
    for record in ordered:
        template = record.template_manifest
        template_root_ref = _join_ref(source_ref, f"templates/{template.template_id}")
        template_ref = _join_ref(template_root_ref, "template.toml")
        input_contract_ref = _external_ref("mas-schema", template.input_schema_ref)
        output_contract_ref = "mas:contracts/publication_figure_quality_contract.json"
        capabilities.append(
            {
                "capability_id": template.full_template_id,
                "capability_kind": template.kind,
                "entrypoint_ref": template_ref,
                "input_contract_ref": input_contract_ref,
                "output_contract_ref": output_contract_ref,
            }
        )
        resources.extend(
            (
                {
                    "resource_id": f"template.{template.template_id}",
                    "role": "template",
                    "ref": template_ref,
                },
                {
                    "resource_id": f"schema.{template.template_id}",
                    "role": "schema",
                    "ref": input_contract_ref,
                },
                {
                    "resource_id": f"qc.{template.template_id}",
                    "role": "qc_profile",
                    "ref": _external_ref("mas-qc", template.qc_profile_ref),
                },
            )
        )
        for index, golden_ref in enumerate(template.golden_case_paths):
            resources.append(
                {
                    "resource_id": f"golden.{template.template_id}.{index}",
                    "role": "golden",
                    "ref": _join_ref(template_root_ref, golden_ref),
                }
            )
        for index, exemplar_ref in enumerate(template.exemplar_refs):
            resources.append(
                {
                    "resource_id": f"exemplar.{template.template_id}.{index}",
                    "role": "exemplar_ref",
                    "ref": _external_ref("mas-exemplar", exemplar_ref),
                }
            )
    return {
        "surface_kind": "opl_generic_capability_pack_descriptor",
        "schema_version": 1,
        "descriptor_media_type": DESCRIPTOR_MEDIA_TYPE,
        "pack_id": manifest.pack_id,
        "version": manifest.version,
        "pack_kind": "display_pack",
        "owner": _text(manifest.maintainer) or _text(source.source_owner) or "MedAutoScience",
        "capabilities": capabilities,
        "resources": _dedupe_resources(resources),
        "artifact_lifecycle": {
            "states": [
                "declared",
                "resolved",
                "locked",
                "review_receipts_observed",
                "handoff_ready",
                "retained",
                "restored",
                "retired",
            ],
            "current_state": "declared",
            "artifact_locator_refs": [
                "mas:paper/build/display_pack_lock.json",
                "mas:contracts/publication_figure_quality_contract.json",
            ],
            "retention": {
                "policy_ref": "mas:policy/display-pack-publication-lock-retention",
                "restore_proof_required": True,
            },
        },
        "review_transport": {
            "receipt_refs": [
                "mas:paper/figure_visual_audit_receipt.json",
                "mas:paper/figure_render_receipt.json",
                "mas:paper/figure_polish_lifecycle.json",
            ],
            "reviewer_adapter_refs": [
                "mas-scholar-skills:medical-display-qc",
                "mas:display-pack-agent/visual-audit",
            ],
            "receipt_transport_only": True,
            "quality_verdict_owner": "MedAutoScience",
        },
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
        "provenance": {
            "source_ref": source_ref,
            "license_ref": _external_ref("license", manifest.license or "internal"),
            "release_ref": f"{source_ref}@{manifest.version}",
            "descriptor_created_by": "med_autoscience.display_pack_opl_adapter",
        },
    }


def _dedupe_resources(resources: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, str]] = []
    for resource in resources:
        key = (resource["role"], resource["ref"])
        if key in seen:
            continue
        seen.add(key)
        result.append(dict(resource))
    return result


def _external_ref(prefix: str, value: str) -> str:
    normalized = value.strip()
    if re.match(r"^[a-z][a-z0-9+.-]*:", normalized, re.IGNORECASE):
        return normalized
    return f"{prefix}:{normalized}"


def _join_ref(base: str, relative: str) -> str:
    return f"{base.rstrip('/')}/{relative.lstrip('/')}"


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _filename_part(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("_") or "pack"


__all__ = [
    "ADAPTER_CONTRACT_REF",
    "DESCRIPTOR_MEDIA_TYPE",
    "PACK_OS_CONTRACT_REF",
    "build_display_pack_opl_adapter_contract",
    "build_enabled_opl_generic_pack_descriptors",
    "build_opl_generic_pack_descriptors",
    "write_enabled_opl_generic_pack_descriptors",
    "write_opl_generic_pack_descriptors",
]
