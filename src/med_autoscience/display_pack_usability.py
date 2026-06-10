from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from med_autoscience.display_pack_e2e_runtime import materialize_display_pack_publication_manifest
from med_autoscience.display_pack_loader import (
    LoadedDisplayTemplate,
    load_enabled_local_display_template_records,
)
from med_autoscience.display_pack_runtime import resolve_display_template_runtime
from med_autoscience.publication_display_contract import seed_publication_display_contracts_if_missing


SCAFFOLD_REVIEWER_HASH = "0" * 64


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _template_asset_status(record: LoadedDisplayTemplate) -> dict[str, Any]:
    template_root = record.template_path.parent
    render_r = template_root / "render.R"
    render_candidate_r = template_root / "render_candidate.R"
    golden_case_paths = list(record.template_manifest.golden_case_paths)
    return {
        "template_root": str(template_root),
        "descriptor_path": str(record.template_path),
        "render_r": _file_status(render_r),
        "render_candidate_r": _file_status(render_candidate_r),
        "golden_case_count": len(golden_case_paths),
        "golden_case_paths": golden_case_paths,
        "exemplar_ref_count": len(record.template_manifest.exemplar_refs),
        "exemplar_refs": list(record.template_manifest.exemplar_refs),
    }


def _file_status(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "missing", "path": str(path)}
    return {"status": "present", "path": str(path), "sha256": _sha256_file(path)}


def _source_config_entry(record: LoadedDisplayTemplate) -> dict[str, Any]:
    source = record.source_config
    return {
        "pack_id": source.pack_id,
        "kind": source.kind,
        "path": source.path,
        "package": source.package,
        "pack_subdir": source.pack_subdir,
        "version": source.version,
        "declared_in": source.declared_in,
        "config_path": str(source.config_path),
        "resolved_source_root": str(source.resolved_source_root),
        "resolved_root": str(source.resolved_root),
    }


def _template_entry(record: LoadedDisplayTemplate) -> dict[str, Any]:
    manifest = record.template_manifest
    assets = _template_asset_status(record)
    return {
        "pack_id": record.pack_manifest.pack_id,
        "pack_version": record.pack_manifest.version,
        "template_id": manifest.template_id,
        "full_template_id": manifest.full_template_id,
        "kind": manifest.kind,
        "display_name": manifest.display_name,
        "display_class_id": manifest.display_class_id,
        "audit_family": manifest.audit_family,
        "paper_family_ids": list(manifest.paper_family_ids),
        "renderer_family": manifest.renderer_family,
        "execution_mode": manifest.execution_mode,
        "entrypoint": manifest.entrypoint,
        "input_schema_ref": manifest.input_schema_ref,
        "qc_profile_ref": manifest.qc_profile_ref,
        "required_exports": list(manifest.required_exports),
        "allowed_paper_roles": list(manifest.allowed_paper_roles),
        "paper_proven": manifest.paper_proven,
        "has_render_r": assets["render_r"]["status"] == "present",
        "has_render_candidate": assets["render_candidate_r"]["status"] == "present",
        "golden_case_count": assets["golden_case_count"],
        "exemplar_ref_count": assets["exemplar_ref_count"],
    }


def _record_matches(
    record: LoadedDisplayTemplate,
    *,
    kind: str,
    renderer_family: str,
    audit_family: str,
    paper_family: str,
    query: str,
) -> bool:
    manifest = record.template_manifest
    if kind and manifest.kind != kind:
        return False
    if renderer_family and manifest.renderer_family != renderer_family:
        return False
    if audit_family and manifest.audit_family != audit_family:
        return False
    if paper_family and paper_family not in manifest.paper_family_ids:
        return False
    if query:
        haystack = " ".join(
            (
                manifest.template_id,
                manifest.full_template_id,
                manifest.display_name,
                manifest.audit_family,
                manifest.renderer_family,
                manifest.input_schema_ref,
            )
        ).lower()
        if query.lower() not in haystack:
            return False
    return True


def list_display_pack_templates(
    *,
    repo_root: Path,
    paper_root: Path | None = None,
    kind: str = "",
    renderer_family: str = "",
    audit_family: str = "",
    paper_family: str = "",
    query: str = "",
) -> dict[str, Any]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    normalized_paper_root = Path(paper_root).expanduser().resolve() if paper_root is not None else None
    records = load_enabled_local_display_template_records(
        normalized_repo_root,
        paper_root=normalized_paper_root,
    )
    filtered_records = [
        record
        for record in records
        if _record_matches(
            record,
            kind=kind.strip(),
            renderer_family=renderer_family.strip(),
            audit_family=audit_family.strip(),
            paper_family=paper_family.strip(),
            query=query.strip(),
        )
    ]
    return {
        "schema_version": 1,
        "status": "listed",
        "repo_root": str(normalized_repo_root),
        "paper_root": str(normalized_paper_root) if normalized_paper_root is not None else "",
        "filters": {
            "kind": kind.strip(),
            "renderer_family": renderer_family.strip(),
            "audit_family": audit_family.strip(),
            "paper_family": paper_family.strip(),
            "query": query.strip(),
        },
        "total_count": len(filtered_records),
        "inventory_count": len(records),
        "templates": [_template_entry(record) for record in filtered_records],
        "authority_boundary": {
            "list_can_authorize_publication_readiness": False,
            "list_can_execute_renderer": False,
            "list_can_mutate_artifacts": False,
        },
    }


def describe_display_pack_template(
    *,
    repo_root: Path,
    template_id: str,
    paper_root: Path | None = None,
) -> dict[str, Any]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    normalized_paper_root = Path(paper_root).expanduser().resolve() if paper_root is not None else None
    runtime = resolve_display_template_runtime(
        repo_root=normalized_repo_root,
        paper_root=normalized_paper_root,
        template_id=template_id,
    )
    manifest = runtime.template_manifest
    return {
        "schema_version": 1,
        "status": "described",
        "repo_root": str(normalized_repo_root),
        "paper_root": str(normalized_paper_root) if normalized_paper_root is not None else "",
        "pack": asdict(runtime.pack_manifest),
        "source": _source_config_entry(runtime),
        "template": _template_entry(runtime),
        "runtime": {
            "execution_mode": manifest.execution_mode,
            "renderer_family": manifest.renderer_family,
            "entrypoint": manifest.entrypoint,
            "template_root": str(runtime.template_path.parent),
            "pack_root": str(runtime.pack_root),
        },
        "assets": _template_asset_status(runtime),
        "authority_boundary": {
            "describe_can_authorize_publication_readiness": False,
            "describe_can_execute_renderer": False,
            "describe_can_mutate_artifacts": False,
        },
    }


def _full_template_id(*, repo_root: Path, paper_root: Path | None, template_id: str) -> str:
    runtime = resolve_display_template_runtime(
        repo_root=repo_root,
        paper_root=paper_root,
        template_id=template_id,
    )
    return runtime.template_manifest.full_template_id


def _default_visual_audit_review() -> dict[str, Any]:
    return {
        "audit_mode": "human_visual_review",
        "reviewer": {
            "provider": "mas-display-pack-scaffold",
            "model": "deterministic-scaffold-review",
            "prompt_hash": SCAFFOLD_REVIEWER_HASH,
        },
        "findings": [],
        "final_status": "clear",
    }


def _seed_figure_style_reference_bundle(paper_root: Path, *, full_template_id: str) -> str | None:
    path = paper_root / "figure_style_reference_bundle.json"
    if path.exists():
        return None
    payload = {
        "schema_version": 1,
        "bundle_id": "display-pack-scaffold-style-v1",
        "references": [
            {
                "reference_id": "scaffold-style-baseline",
                "source_ref": "mas:display-pack-scaffold",
                "decision": "adopt",
                "applies_to": [full_template_id],
                "style_notes": ["Use publication_style_profile tokens as the scaffold style source."],
            }
        ],
    }
    _write_json(path, payload)
    return str(path)


def _seed_display_overrides(paper_root: Path, *, figure_id: str, full_template_id: str) -> None:
    path = paper_root / "display_overrides.json"
    if not path.exists():
        _write_json(
            path,
            {
                "schema_version": 1,
                "displays": [
                    {
                        "display_id": figure_id,
                        "template_id": full_template_id,
                        "layout_override": {},
                        "readability_override": {},
                    }
                ],
            },
        )
        return
    payload = _read_json_object(path)
    displays = payload.get("displays")
    if not isinstance(displays, list):
        raise ValueError(f"{path}.displays must be a list")
    for item in displays:
        if isinstance(item, dict) and item.get("display_id") == figure_id:
            return
    displays.append(
        {
            "display_id": figure_id,
            "template_id": full_template_id,
            "layout_override": {},
            "readability_override": {},
        }
    )
    payload["displays"] = displays
    _write_json(path, payload)


def _seed_scaffold_inputs(
    *,
    repo_root: Path,
    paper_root: Path,
    template_id: str,
    data_payload_file: Path,
    figure_id: str,
    claim_ref: str,
    cohort_ref: str,
    endpoint_ref: str,
    risk_horizon: str,
) -> dict[str, Any]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    normalized_paper_root = Path(paper_root).expanduser().resolve()
    normalized_paper_root.mkdir(parents=True, exist_ok=True)
    source_data_path = Path(data_payload_file).expanduser().resolve()
    if not source_data_path.is_file():
        raise FileNotFoundError(f"data payload file does not exist: {source_data_path}")
    full_template_id = _full_template_id(
        repo_root=normalized_repo_root,
        paper_root=normalized_paper_root,
        template_id=template_id,
    )
    seeded_files: list[str] = []
    data_target = normalized_paper_root / "data" / "frozen" / f"{figure_id}.payload.json"
    data_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_data_path, data_target)
    seeded_files.append(str(data_target))

    data_ref = f"paper/data/frozen/{figure_id}.payload.json"
    _write_json(
        normalized_paper_root / "figure_intent.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": figure_id,
                    "claim_ref": claim_ref,
                    "data_ref": data_ref,
                    "template_id": full_template_id,
                    "figure_kind": "evidence_figure",
                    "statistical_value_refs": [f"scaffold/statistics/{figure_id}"],
                }
            ],
        },
    )
    seeded_files.append(str(normalized_paper_root / "figure_intent.json"))
    _write_json(
        normalized_paper_root / "figure_specs.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": figure_id,
                    "intent_ref": f"paper/figure_intent.json#/figures/{figure_id}",
                    "template_id": full_template_id,
                    "figure_kind": "evidence_figure",
                    "medical_semantics": {
                        "cohort_ref": cohort_ref,
                        "endpoint_ref": endpoint_ref,
                        "model_ref": f"model:{figure_id}",
                        "risk_horizon": risk_horizon,
                        "effect_estimate_ref": f"scaffold/statistics/{figure_id}",
                        "claim_role": "scaffold_evidence",
                    },
                    "panels": [
                        {
                            "panel_id": "A",
                            "data_role": "primary",
                            "mark_role": "template_default",
                        }
                    ],
                }
            ],
        },
    )
    seeded_files.append(str(normalized_paper_root / "figure_specs.json"))
    seeded_files.extend(seed_publication_display_contracts_if_missing(paper_root=normalized_paper_root))
    _seed_display_overrides(normalized_paper_root, figure_id=figure_id, full_template_id=full_template_id)
    style_ref = _seed_figure_style_reference_bundle(normalized_paper_root, full_template_id=full_template_id)
    if style_ref is not None:
        seeded_files.append(style_ref)
    return {
        "created": True,
        "repo_root": str(normalized_repo_root),
        "paper_root": str(normalized_paper_root),
        "figure_id": figure_id,
        "template_id": full_template_id,
        "data_payload_source": str(source_data_path),
        "data_ref": data_ref,
        "seeded_files": seeded_files,
    }


def scaffold_display_pack_render(
    *,
    repo_root: Path,
    paper_root: Path,
    template_id: str,
    data_payload_file: Path,
    figure_id: str = "F1",
    claim_ref: str = "claim:display-pack-scaffold",
    cohort_ref: str = "cohort:display-pack-scaffold",
    endpoint_ref: str = "endpoint:display-pack-scaffold",
    risk_horizon: str = "unspecified",
    visual_audit_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scaffold = _seed_scaffold_inputs(
        repo_root=repo_root,
        paper_root=paper_root,
        template_id=template_id,
        data_payload_file=data_payload_file,
        figure_id=figure_id,
        claim_ref=claim_ref,
        cohort_ref=cohort_ref,
        endpoint_ref=endpoint_ref,
        risk_horizon=risk_horizon,
    )
    result = materialize_display_pack_publication_manifest(
        repo_root=repo_root,
        paper_root=paper_root,
        visual_audit_review=visual_audit_review or _default_visual_audit_review(),
        figure_ids=[figure_id],
    )
    return {
        **result,
        "scaffold": scaffold,
        "authority_boundary": {
            **dict(result.get("authority_boundary") or {}),
            "scaffold_can_authorize_publication_readiness": False,
            "scaffold_can_replace_paper_intent_authoring": False,
        },
    }


def _golden_manifest_path(golden_root: Path, *, template_id: str) -> Path:
    safe_template = template_id.split("::")[-1].replace("/", "_")
    return golden_root / safe_template / "golden_manifest.json"


def _copy_golden_artifacts(
    *,
    figure_entry: dict[str, Any],
    golden_manifest_path: Path,
) -> dict[str, Any]:
    golden_dir = golden_manifest_path.parent
    golden_dir.mkdir(parents=True, exist_ok=True)
    artifact_specs = {
        "png": Path(str(figure_entry["rendered_artifacts"]["png_path"])),
        "pdf": Path(str(figure_entry["rendered_artifacts"]["pdf_path"])),
        "layout_sidecar": Path(str(figure_entry["rendered_artifacts"]["layout_sidecar_path"])),
    }
    artifacts: dict[str, Any] = {}
    for artifact_kind, source_path in artifact_specs.items():
        suffix = source_path.suffix or ".artifact"
        target_path = golden_dir / f"{artifact_kind}{suffix}"
        shutil.copyfile(source_path, target_path)
        artifacts[artifact_kind] = {
            "path": str(target_path),
            "sha256": _sha256_file(target_path),
        }
    return artifacts


def _golden_manifest_payload(
    *,
    render_result: dict[str, Any],
    golden_manifest_path: Path,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    figure_entry = dict(render_result["figures"][0])
    return {
        "schema_version": 1,
        "surface": "display_pack_golden_manifest",
        "status": "golden_refreshed",
        "template_id": figure_entry["template_id"],
        "short_template_id": figure_entry["short_template_id"],
        "renderer_family": figure_entry["renderer_family"],
        "execution_mode": figure_entry["execution_mode"],
        "qc_profile": figure_entry["qc_profile"],
        "deterministic_qc_status": figure_entry["deterministic_qc"]["status"],
        "publication_style_profile_sha256": figure_entry["publication_style_profile"]["sha256"],
        "display_pack_lock_sha256": render_result["display_pack_lock_sha256"],
        "required_match_artifacts": ["png", "layout_sidecar"],
        "observed_only_artifacts": ["pdf"],
        "artifacts": artifacts,
        "golden_manifest_path": str(golden_manifest_path),
        "authority_boundary": {
            "golden_can_authorize_publication_readiness": False,
            "golden_can_mutate_data_or_statistics": False,
            "golden_can_replace_visual_audit": False,
        },
    }


def refresh_display_pack_golden(
    *,
    repo_root: Path,
    paper_root: Path,
    template_id: str,
    data_payload_file: Path,
    golden_root: Path,
    figure_id: str = "G1",
) -> dict[str, Any]:
    render_result = scaffold_display_pack_render(
        repo_root=repo_root,
        paper_root=paper_root,
        template_id=template_id,
        data_payload_file=data_payload_file,
        figure_id=figure_id,
        claim_ref="claim:display-pack-golden",
        cohort_ref="cohort:display-pack-golden",
        endpoint_ref="endpoint:display-pack-golden",
        risk_horizon="golden",
    )
    normalized_golden_root = Path(golden_root).expanduser().resolve()
    golden_manifest_path = _golden_manifest_path(
        normalized_golden_root,
        template_id=str(render_result["figures"][0]["template_id"]),
    )
    artifacts = _copy_golden_artifacts(
        figure_entry=dict(render_result["figures"][0]),
        golden_manifest_path=golden_manifest_path,
    )
    manifest = _golden_manifest_payload(
        render_result=render_result,
        golden_manifest_path=golden_manifest_path,
        artifacts=artifacts,
    )
    _write_json(golden_manifest_path, manifest)
    return {
        "schema_version": 1,
        "status": "golden_refreshed",
        "golden_manifest_path": str(golden_manifest_path),
        "golden_manifest_sha256": _sha256_file(golden_manifest_path),
        "template_id": manifest["template_id"],
        "artifacts": artifacts,
        "render": {
            "paper_root": str(Path(paper_root).expanduser().resolve()),
            "figure_id": figure_id,
            "deterministic_qc_status": manifest["deterministic_qc_status"],
        },
        "authority_boundary": manifest["authority_boundary"],
    }


def check_display_pack_golden(
    *,
    repo_root: Path,
    paper_root: Path,
    template_id: str,
    data_payload_file: Path,
    golden_root: Path,
    figure_id: str = "G1",
) -> dict[str, Any]:
    normalized_golden_root = Path(golden_root).expanduser().resolve()
    full_template_id = _full_template_id(
        repo_root=Path(repo_root).expanduser().resolve(),
        paper_root=Path(paper_root).expanduser().resolve(),
        template_id=template_id,
    )
    golden_manifest_path = _golden_manifest_path(normalized_golden_root, template_id=full_template_id)
    if not golden_manifest_path.is_file():
        raise FileNotFoundError(f"golden manifest does not exist: {golden_manifest_path}")
    golden_manifest = _read_json_object(golden_manifest_path)
    render_result = scaffold_display_pack_render(
        repo_root=repo_root,
        paper_root=paper_root,
        template_id=template_id,
        data_payload_file=data_payload_file,
        figure_id=figure_id,
        claim_ref="claim:display-pack-golden",
        cohort_ref="cohort:display-pack-golden",
        endpoint_ref="endpoint:display-pack-golden",
        risk_horizon="golden",
    )
    figure_entry = dict(render_result["figures"][0])
    current_artifacts = {
        "png": Path(str(figure_entry["rendered_artifacts"]["png_path"])),
        "pdf": Path(str(figure_entry["rendered_artifacts"]["pdf_path"])),
        "layout_sidecar": Path(str(figure_entry["rendered_artifacts"]["layout_sidecar_path"])),
    }
    required_match_artifacts = set(golden_manifest.get("required_match_artifacts") or ("png", "layout_sidecar"))
    comparison: dict[str, Any] = {}
    for artifact_kind, current_path in current_artifacts.items():
        expected = dict(dict(golden_manifest["artifacts"])[artifact_kind])
        current_sha = _sha256_file(current_path)
        comparison[artifact_kind] = {
            "match": current_sha == expected["sha256"],
            "required_match": artifact_kind in required_match_artifacts,
            "expected_sha256": expected["sha256"],
            "actual_sha256": current_sha,
            "expected_path": expected["path"],
            "actual_path": str(current_path),
        }
    contract_comparison = {
        "deterministic_qc_status": {
            "match": figure_entry["deterministic_qc"]["status"] == golden_manifest["deterministic_qc_status"],
            "expected": golden_manifest["deterministic_qc_status"],
            "actual": figure_entry["deterministic_qc"]["status"],
        },
        "publication_style_profile_sha256": {
            "match": figure_entry["publication_style_profile"]["sha256"]
            == golden_manifest["publication_style_profile_sha256"],
            "expected": golden_manifest["publication_style_profile_sha256"],
            "actual": figure_entry["publication_style_profile"]["sha256"],
        },
    }
    required_artifacts_match = all(
        item["match"] for item in comparison.values() if item["required_match"]
    )
    required_contracts_match = all(item["match"] for item in contract_comparison.values())
    status = "golden_match" if required_artifacts_match and required_contracts_match else "golden_mismatch"
    return {
        "schema_version": 1,
        "status": status,
        "golden_manifest_path": str(golden_manifest_path),
        "template_id": figure_entry["template_id"],
        "comparison": comparison,
        "contract_comparison": contract_comparison,
        "render": {
            "paper_root": str(Path(paper_root).expanduser().resolve()),
            "figure_id": figure_id,
            "deterministic_qc_status": figure_entry["deterministic_qc"]["status"],
        },
        "authority_boundary": {
            "golden_check_can_authorize_publication_readiness": False,
            "golden_check_can_mutate_data_or_statistics": False,
            "golden_check_can_replace_visual_audit": False,
        },
    }
