from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience import display_layout_qc
from med_autoscience.display_pack_dependency_environment import (
    dependency_environment_status,
    dependency_environment_authority_boundary,
)
from med_autoscience.display_pack_lock import write_display_pack_lock
from med_autoscience.display_pack_loader import load_enabled_local_display_template_records
from med_autoscience.display_pack_provenance_bundle import (
    PROVENANCE_INDEX_REF,
    materialize_figure_provenance_bundles,
)
from med_autoscience.display_pack_runtime import resolve_display_template_runtime
from med_autoscience.figure_polish_lifecycle_contract import load_figure_polish_lifecycle
from med_autoscience.medical_figure_spec_contract import (
    MEDICAL_FIGURE_SPEC_BASENAME,
    MEDICAL_FIGURE_SPECS_BASENAME,
    load_medical_figure_spec,
    load_medical_figure_specs,
)
from .figure_render_receipt import (
    FIGURE_RENDER_RECEIPT_REF,
    write_figure_render_receipt,
)
from .subprocess_renderers import (
    run_candidate_subprocess_renderer as _run_candidate_subprocess_renderer,
    run_subprocess_renderer as _run_subprocess_renderer,
    safe_artifact_stem as _safe_artifact_stem,
    subprocess,
)
from med_autoscience.publication_display_contract import (
    load_display_overrides,
    load_publication_style_profile,
    resolve_style_roles,
)
from med_autoscience.publication_figure_quality_contract import (
    collect_publication_figure_quality_refs,
    load_figure_intent,
    load_figure_style_reference_bundle,
    load_figure_visual_audit_receipt,
)
from med_autoscience.display_pack_e2e_runtime.artifact_manifest import build_display_artifact_manifest


PUBLICATION_MANIFEST_BASENAME = "display_pack_publication_manifest.json"
DISPLAY_PACK_LOCK_REF = "paper/build/display_pack_lock.json"
FIGURE_VISUAL_AUDIT_RECEIPT_REF = "paper/figure_visual_audit_receipt.json"
FIGURE_POLISH_LIFECYCLE_REF = "paper/figure_polish_lifecycle.json"
FIGURE_WORKFLOW_PACKET_REF = "paper/figure_workflow_packet.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _json_compatible(value: object, *, field_name: str) -> object:
    try:
        json.dumps(value, ensure_ascii=False)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be JSON-serializable") from exc
    return value


def _workspace_ref(path: Path, *, paper_root: Path) -> str:
    return path.resolve().relative_to(paper_root.resolve().parent).as_posix()


def _resolve_workspace_ref(ref: str, *, paper_root: Path) -> Path:
    normalized = str(ref or "").strip()
    if not normalized:
        raise ValueError("workspace ref must be non-empty")
    path = Path(normalized).expanduser()
    if path.is_absolute():
        return path.resolve()
    if path.parts and path.parts[0] == paper_root.name:
        return (paper_root.parent / path).resolve()
    return (paper_root / path).resolve()


def _intent_figure(intent_payload: Mapping[str, Any], *, figure_id: str) -> dict[str, Any]:
    figures = intent_payload.get("figures")
    if not isinstance(figures, list):
        raise ValueError("figure_intent.figures must be a list")
    matches = [item for item in figures if isinstance(item, dict) and item.get("figure_id") == figure_id]
    if len(matches) != 1:
        raise ValueError(f"figure_intent must contain exactly one figure for `{figure_id}`")
    return dict(matches[0])


def _load_required_quality_inputs(paper_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    intent = load_figure_intent(paper_root / "figure_intent.json")
    batch_spec_path = paper_root / MEDICAL_FIGURE_SPECS_BASENAME
    if batch_spec_path.exists():
        figure_specs = list(load_medical_figure_specs(batch_spec_path)["figures"])
    else:
        figure_specs = [load_medical_figure_spec(paper_root / MEDICAL_FIGURE_SPEC_BASENAME)]
    style_reference_bundle = load_figure_style_reference_bundle(paper_root / "figure_style_reference_bundle.json")
    return intent, figure_specs, style_reference_bundle


def _dependency_environment_for_figure_specs(
    *,
    repo_root: Path,
    paper_root: Path,
    figure_specs: list[Mapping[str, Any]],
) -> dict[str, Any]:
    template_ids = {str(spec.get("template_id") or "").strip() for spec in figure_specs}
    template_ids.discard("")
    records = [
        record
        for record in load_enabled_local_display_template_records(repo_root, paper_root=paper_root)
        if record.template_manifest.full_template_id in template_ids
        or record.template_manifest.template_id in template_ids
    ]
    status = dependency_environment_status(repo_root=repo_root, paper_root=paper_root, records=records)
    if status.get("required") is not True:
        return {}
    if status.get("status") == "prepared":
        return status
    return {}


def _validate_intent_spec_binding(*, intent_figure: Mapping[str, Any], figure_spec: Mapping[str, Any]) -> None:
    for field_name in ("figure_id", "template_id", "figure_kind"):
        if intent_figure.get(field_name) != figure_spec.get(field_name):
            raise ValueError(
                f"figure_intent.{field_name} and medical_figure_spec.{field_name} must match "
                f"for `{figure_spec.get('figure_id')}`"
            )


def _declared_panel_ids(figure_spec: Mapping[str, Any]) -> set[str]:
    panel_ids: set[str] = set()
    for panel in figure_spec.get("panels") or []:
        if isinstance(panel, Mapping):
            panel_id = str(panel.get("panel_id") or "").strip()
            if panel_id:
                panel_ids.add(panel_id)
    return panel_ids


def _sidecar_panel_ids(layout_sidecar: Mapping[str, Any]) -> set[str]:
    panel_ids: set[str] = set()
    metrics = layout_sidecar.get("metrics")
    if isinstance(metrics, Mapping):
        raw_metric_panel_ids = metrics.get("panel_ids") or []
        if isinstance(raw_metric_panel_ids, str):
            metric_panel_ids = [raw_metric_panel_ids]
        else:
            metric_panel_ids = raw_metric_panel_ids
        for panel_id in metric_panel_ids:
            normalized = str(panel_id or "").strip()
            if normalized:
                panel_ids.add(normalized)
    raw_panel_boxes = layout_sidecar.get("panel_boxes") or []
    if isinstance(raw_panel_boxes, Mapping):
        panel_boxes = [raw_panel_boxes]
    else:
        panel_boxes = raw_panel_boxes
    for panel_box in panel_boxes:
        if isinstance(panel_box, Mapping):
            panel_id = str(panel_box.get("panel_id") or "").strip()
            if panel_id:
                panel_ids.add(panel_id)
    return panel_ids


def _validate_declared_panel_layout_contract(
    *,
    figure_spec: Mapping[str, Any],
    layout_sidecar: Mapping[str, Any],
) -> None:
    expected_panel_ids = _declared_panel_ids(figure_spec)
    if not expected_panel_ids:
        return
    observed_panel_ids = _sidecar_panel_ids(layout_sidecar)
    missing_panel_ids = sorted(expected_panel_ids - observed_panel_ids)
    if missing_panel_ids:
        figure_id = str(figure_spec.get("figure_id") or "").strip()
        observed = ", ".join(sorted(observed_panel_ids)) or "<none>"
        missing = ", ".join(missing_panel_ids)
        raise ValueError(
            "display renderer did not implement declared panel semantics "
            f"for `{figure_id}`; missing panel_id(s): {missing}; "
            "layout sidecar must expose declared medical_figure_spec.panels IDs "
            f"in panel_boxes[].panel_id or metrics.panel_ids; observed: {observed}"
        )


def _style_render_context(
    *,
    paper_root: Path,
    figure_id: str,
    full_template_id: str,
    short_template_id: str,
) -> dict[str, Any]:
    style_profile_path = paper_root / "publication_style_profile.json"
    style_profile = load_publication_style_profile(style_profile_path)
    overrides = load_display_overrides(paper_root / "display_overrides.json")
    override = (
        overrides.get((figure_id, full_template_id))
        or overrides.get((figure_id, short_template_id))
    )
    style_roles = resolve_style_roles(
        style_profile=style_profile,
        template_id=short_template_id,
    )
    return {
        "style_profile_id": style_profile.style_profile_id,
        "style_profile_ref": _workspace_ref(style_profile_path, paper_root=paper_root),
        "style_profile_sha256": _sha256_file(style_profile_path),
        "journal_palette_ref": style_profile.journal_palette_ref,
        "palette": dict(style_profile.palette),
        "semantic_roles": dict(style_profile.semantic_roles),
        "style_roles": style_roles,
        "typography": dict(style_profile.typography),
        "stroke": dict(style_profile.stroke),
        "grid": dict(style_profile.grid),
        "layout_override": dict(override.layout_override) if override is not None else {},
        "readability_override": dict(override.readability_override) if override is not None else {},
    }


def _style_profile_entry_from_render_context(render_context: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "style_profile_id": render_context["style_profile_id"],
        "ref": render_context["style_profile_ref"],
        "sha256": render_context["style_profile_sha256"],
        "journal_palette_ref": render_context.get("journal_palette_ref", ""),
        "palette_keys": sorted(dict(render_context.get("palette") or {}).keys()),
        "semantic_roles": dict(render_context.get("semantic_roles") or {}),
        "typography": dict(render_context.get("typography") or {}),
        "stroke": dict(render_context.get("stroke") or {}),
        "grid": dict(render_context.get("grid") or {}),
    }


def _data_payload_and_digest(*, paper_root: Path, data_ref: str) -> tuple[dict[str, Any], str]:
    data_path = _resolve_workspace_ref(data_ref, paper_root=paper_root)
    data_payload = _read_json_object(data_path)
    digest = str(data_payload.get("source_data_digest") or "").strip()
    if not digest:
        digest = _sha256_file(data_path)
    return data_payload, digest


def _render_figure(
    *,
    repo_root: Path,
    paper_root: Path,
    figure_spec: Mapping[str, Any],
    intent_figure: Mapping[str, Any],
    dependency_environment: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    figure_id = str(figure_spec["figure_id"])
    full_template_id = str(figure_spec["template_id"])
    runtime = resolve_display_template_runtime(
        repo_root=repo_root,
        paper_root=paper_root,
        template_id=full_template_id,
    )
    template_manifest = runtime.template_manifest
    data_payload, data_digest = _data_payload_and_digest(
        paper_root=paper_root,
        data_ref=str(intent_figure["data_ref"]),
    )
    stem = _safe_artifact_stem(figure_id)
    output_dir = paper_root / "figures" / "generated"
    output_png_path = output_dir / f"{stem}.png"
    output_pdf_path = output_dir / f"{stem}.pdf"
    layout_sidecar_path = output_dir / f"{stem}.layout.json"
    render_context = _style_render_context(
        paper_root=paper_root,
        figure_id=figure_id,
        full_template_id=full_template_id,
        short_template_id=template_manifest.template_id,
    )
    display_payload = {
        "figure_id": figure_id,
        "template_id": full_template_id,
        "figure_kind": figure_spec["figure_kind"],
        "medical_semantics": dict(figure_spec["medical_semantics"]),
        "panels": list(figure_spec.get("panels") or []),
        "claim_ref": intent_figure["claim_ref"],
        "data_ref": intent_figure["data_ref"],
        "data_payload": data_payload,
        "render_context": render_context,
    }
    reporting_flow_shell_allowed = (
        template_manifest.kind == "illustration_shell"
        and template_manifest.template_id == "cohort_flow_figure"
        and template_manifest.renderer_family == "r_ggplot2"
        and template_manifest.execution_mode == "subprocess"
    )
    if template_manifest.kind != "evidence_figure" and not reporting_flow_shell_allowed:
        raise ValueError(
            "display pack publication manifest evidence path only materializes evidence_figure templates; "
            f"observed `{template_manifest.kind}` for `{full_template_id}`"
        )
    if template_manifest.renderer_family != "r_ggplot2":
        raise ValueError(
            "display pack publication manifest evidence path requires renderer_family `r_ggplot2`; "
            f"observed `{template_manifest.renderer_family}` for `{full_template_id}`"
        )
    if template_manifest.execution_mode != "subprocess":
        raise ValueError(
            "display pack publication manifest evidence path requires subprocess execution; "
            f"observed `{template_manifest.execution_mode}` for `{full_template_id}`"
        )
    render_result = _run_subprocess_renderer(
        runtime_template_root=runtime.template_path.parent,
        pack_root=runtime.pack_root,
        template_manifest=template_manifest,
        paper_root=paper_root,
        figure_id=figure_id,
        full_template_id=full_template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
        dependency_environment=dependency_environment,
    )
    for path in (output_png_path, output_pdf_path, layout_sidecar_path):
        if not path.exists():
            raise FileNotFoundError(f"display pack renderer did not write required artifact: {path}")
    layout_sidecar = _read_json_object(layout_sidecar_path)
    _validate_declared_panel_layout_contract(
        figure_spec=figure_spec,
        layout_sidecar=layout_sidecar,
    )
    qc_result = display_layout_qc.run_display_layout_qc(
        qc_profile=template_manifest.qc_profile_ref,
        layout_sidecar=layout_sidecar,
    )
    qc_path = paper_root / "qc" / f"{stem}.layout_qc.json"
    _write_json(qc_path, qc_result)
    if qc_result.get("status") != "pass":
        raise ValueError(f"deterministic QC failed for `{figure_id}`: {qc_result.get('failure_reason')}")
    return {
        "figure_id": figure_id,
        "template_id": full_template_id,
        "short_template_id": template_manifest.template_id,
        "figure_kind": figure_spec["figure_kind"],
        "renderer_family": template_manifest.renderer_family,
        "execution_mode": template_manifest.execution_mode,
        "required_exports": list(template_manifest.required_exports),
        "claim_ref": intent_figure["claim_ref"],
        "data_ref": intent_figure["data_ref"],
        "data_digest": data_digest,
        "publication_style_profile": _style_profile_entry_from_render_context(render_context),
        "statistical_value_refs": list(intent_figure.get("statistical_value_refs") or []),
        "qc_profile": template_manifest.qc_profile_ref,
        "render_result": _json_compatible(render_result, field_name="display_pack_renderer.render_result"),
        "dependency_environment": dict(dependency_environment or {}),
        "rendered_artifacts": {
            "png_path": str(output_png_path),
            "pdf_path": str(output_pdf_path),
            "layout_sidecar_path": str(layout_sidecar_path),
            "png_ref": _workspace_ref(output_png_path, paper_root=paper_root),
            "pdf_ref": _workspace_ref(output_pdf_path, paper_root=paper_root),
            "layout_sidecar_ref": _workspace_ref(layout_sidecar_path, paper_root=paper_root),
            "png_sha256": _sha256_file(output_png_path),
            "pdf_sha256": _sha256_file(output_pdf_path),
            "layout_sidecar_sha256": _sha256_file(layout_sidecar_path),
        },
        "deterministic_qc": {
            **qc_result,
            "path": str(qc_path),
            "ref": _workspace_ref(qc_path, paper_root=paper_root),
            "sha256": _sha256_file(qc_path),
        },
    }


def _visual_audit_receipt_payload(
    *,
    figure_entries: list[dict[str, Any]],
    visual_audit_review: Mapping[str, Any],
) -> dict[str, Any]:
    audit_mode = str(visual_audit_review.get("audit_mode") or "").strip() or "human_visual_review"
    final_status = str(visual_audit_review.get("final_status") or "").strip() or "clear"
    reviewer = visual_audit_review.get("reviewer")
    if not isinstance(reviewer, Mapping):
        review_label = json.dumps(visual_audit_review, ensure_ascii=False, sort_keys=True)
        reviewer = {
            "provider": "mas-local-reviewer",
            "model": "structured-visual-review",
            "prompt_hash": _sha256_text(review_label),
        }
    findings = visual_audit_review.get("findings")
    if findings is None:
        findings = []
    if not isinstance(findings, list):
        raise ValueError("visual_audit_review.findings must be a list when provided")
    return {
        "schema_version": 1,
        "receipt_id": f"display-pack-visual-audit-{_utc_now()}",
        "audit_mode": audit_mode,
        "inspected_artifacts": [
            {
                "figure_id": entry["figure_id"],
                "artifact_path": entry["rendered_artifacts"]["png_ref"],
                "artifact_sha256": entry["rendered_artifacts"]["png_sha256"],
            }
            for entry in figure_entries
        ],
        "findings": findings,
        "reviewer": dict(reviewer),
        "final_status": final_status,
    }


def _write_visual_audit_receipt(
    *,
    paper_root: Path,
    figure_entries: list[dict[str, Any]],
    visual_audit_review: Mapping[str, Any],
) -> dict[str, Any]:
    receipt_path = paper_root / "figure_visual_audit_receipt.json"
    payload = _visual_audit_receipt_payload(
        figure_entries=figure_entries,
        visual_audit_review=visual_audit_review,
    )
    _write_json(receipt_path, payload)
    return load_figure_visual_audit_receipt(receipt_path)


def _write_figure_polish_lifecycle(
    *,
    paper_root: Path,
    figure_entries: list[dict[str, Any]],
    audit_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    if audit_receipt.get("final_status") != "clear":
        raise ValueError("publication manifest requires clear visual audit status")
    audit_actor = str(audit_receipt.get("audit_mode") or "").strip() or "human_visual_review"
    events: list[dict[str, Any]] = []
    for entry in figure_entries:
        figure_id = str(entry["figure_id"])
        artifact_ref = str(entry["rendered_artifacts"]["png_ref"])
        qc_ref = str(entry["deterministic_qc"]["ref"])
        events.extend(
            [
                {
                    "state": "draft_rendered",
                    "figure_id": figure_id,
                    "artifact_ref": artifact_ref,
                    "actor": "display_pack_builder",
                    "evidence_ref": DISPLAY_PACK_LOCK_REF,
                    "mutates_data": False,
                    "carries_publication_verdict": False,
                },
                {
                    "state": "deterministic_qc_clear",
                    "figure_id": figure_id,
                    "artifact_ref": artifact_ref,
                    "actor": "deterministic_qc",
                    "evidence_ref": qc_ref,
                    "mutates_data": False,
                    "carries_publication_verdict": False,
                },
                {
                    "state": "visual_audit_findings",
                    "figure_id": figure_id,
                    "artifact_ref": artifact_ref,
                    "actor": audit_actor,
                    "evidence_ref": FIGURE_VISUAL_AUDIT_RECEIPT_REF,
                    "reviewer_ref": "paper/figure_visual_audit_receipt.json#/reviewer",
                    "mutates_data": False,
                    "carries_publication_verdict": False,
                },
                {
                    "state": "revised",
                    "figure_id": figure_id,
                    "artifact_ref": artifact_ref,
                    "actor": "display_pack_builder",
                    "evidence_ref": qc_ref,
                    "mutates_data": False,
                    "carries_publication_verdict": False,
                },
                {
                    "state": "audit_clear",
                    "figure_id": figure_id,
                    "artifact_ref": artifact_ref,
                    "actor": audit_actor,
                    "evidence_ref": FIGURE_VISUAL_AUDIT_RECEIPT_REF,
                    "reviewer_ref": "paper/figure_visual_audit_receipt.json#/reviewer",
                    "mutates_data": False,
                    "carries_publication_verdict": False,
                },
                {
                    "state": "publication_manifested",
                    "figure_id": figure_id,
                    "artifact_ref": artifact_ref,
                    "actor": "display_pack_builder",
                    "evidence_ref": "paper/build/display_pack_publication_manifest.json",
                    "mutates_data": False,
                    "carries_publication_verdict": False,
                },
            ]
        )
    lifecycle_payload = {
        "schema_version": 1,
        "lifecycle_id": "display-pack-polish",
        "relationship_refs": {
            "figure_visual_audit_receipt": FIGURE_VISUAL_AUDIT_RECEIPT_REF,
            "display_pack_lock_publication_figure_quality_refs": (
                f"{DISPLAY_PACK_LOCK_REF}#/publication_figure_quality_refs"
            ),
        },
        "events": events,
    }
    lifecycle_path = paper_root / "figure_polish_lifecycle.json"
    _write_json(lifecycle_path, lifecycle_payload)
    return load_figure_polish_lifecycle(lifecycle_path)


def _write_figure_workflow_packet(
    *,
    paper_root: Path,
    figure_entries: list[dict[str, Any]],
    audit_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    from med_autoscience.display_pack_agent.figure_workflow import (
        build_rendered_figure_workflow_packet,
    )

    receipt_refs = {
        "display_pack_lock": DISPLAY_PACK_LOCK_REF,
        "publication_manifest": f"paper/build/{PUBLICATION_MANIFEST_BASENAME}",
        "visual_audit_receipt": FIGURE_VISUAL_AUDIT_RECEIPT_REF,
        "figure_render_receipt": FIGURE_RENDER_RECEIPT_REF,
        "polish_lifecycle": FIGURE_POLISH_LIFECYCLE_REF,
        "figure_workflow_packet": FIGURE_WORKFLOW_PACKET_REF,
    }
    packet = build_rendered_figure_workflow_packet(
        figure_entries=figure_entries,
        audit_receipt=audit_receipt,
        receipt_refs=receipt_refs,
    )
    packet_path = paper_root / "figure_workflow_packet.json"
    _write_json(packet_path, packet)
    return packet


def _write_display_artifact_manifest(
    *,
    paper_root: Path,
    figure_entry: Mapping[str, Any],
) -> dict[str, Any]:
    statistical_value_refs = list(figure_entry.get("statistical_value_refs") or [])
    if not statistical_value_refs:
        statistical_value_refs = [f"{figure_entry['data_ref']}#/source_data_digest"]
    manifest = build_display_artifact_manifest(
        artifact_id=str(figure_entry["figure_id"]),
        artifact_kind=str(figure_entry["figure_kind"]),
        source_data_refs=[str(figure_entry["data_ref"])],
        source_data_digests={str(figure_entry["data_ref"]): str(figure_entry["data_digest"])},
        claim_refs=[str(figure_entry["claim_ref"])],
        statistical_value_refs=statistical_value_refs,
        rendered_artifact_ref=str(figure_entry["rendered_artifacts"]["png_ref"]),
        rendered_artifact_digest=str(figure_entry["rendered_artifacts"]["png_sha256"]),
        placement={"placement": "single_column", "paper_role": "main_text"},
        scalable=True,
        protected=True,
        visual_qa_receipt_refs=[FIGURE_VISUAL_AUDIT_RECEIPT_REF],
        currentness={
            "status": "current",
            "checked_at": _utc_now(),
            "display_pack_lock_ref": DISPLAY_PACK_LOCK_REF,
        },
    )
    output_path = paper_root / "build" / f"display_artifact_manifest.{figure_entry['figure_id']}.json"
    _write_json(output_path, manifest)
    return {
        "path": str(output_path),
        "ref": _workspace_ref(output_path, paper_root=paper_root),
        "sha256": _sha256_file(output_path),
        "payload": manifest,
    }


def _sync_figure_catalog_from_render(
    *,
    paper_root: Path,
    figure_entries: list[dict[str, Any]],
    visual_audit_receipt: Mapping[str, Any],
    display_pack_lock_sha256: str,
) -> dict[str, Any]:
    catalog_path = paper_root / "figures" / "figure_catalog.json"
    if not catalog_path.exists():
        return {
            "status": "skipped",
            "reason": "figure_catalog_missing",
            "ref": _workspace_ref(catalog_path, paper_root=paper_root),
            "updated_figure_ids": [],
        }
    catalog = _read_json_object(catalog_path)
    figures = catalog.get("figures")
    if not isinstance(figures, list):
        return {
            "status": "skipped",
            "reason": "figure_catalog_figures_missing",
            "ref": _workspace_ref(catalog_path, paper_root=paper_root),
            "updated_figure_ids": [],
        }
    audit_artifacts = {
        str(item.get("figure_id")): dict(item)
        for item in visual_audit_receipt.get("inspected_artifacts", [])
        if isinstance(item, Mapping)
    }
    changed = False
    updated_figure_ids: list[str] = []
    for entry in figure_entries:
        figure_id = str(entry["figure_id"])
        rendered = dict(entry.get("rendered_artifacts") or {})
        qc = dict(entry.get("deterministic_qc") or {})
        matches = [item for item in figures if isinstance(item, dict) and str(item.get("figure_id") or "") == figure_id]
        if not matches:
            continue
        item = matches[0]
        item["template_id"] = str(entry["template_id"])
        item["renderer_family"] = str(entry["renderer_family"])
        item["execution_mode"] = str(entry["execution_mode"])
        item["qc_profile"] = str(entry["qc_profile"])
        item["qc_result"] = qc
        item["qc_result"]["layout_sidecar_path"] = str(rendered["layout_sidecar_ref"])
        item["export_paths"] = [str(rendered["png_ref"]), str(rendered["pdf_ref"])]
        item["source_paths"] = [str(entry["data_ref"])]
        item["source_data_digests"] = {str(entry["data_ref"]): str(entry["data_digest"])}
        item["statistics_refs"] = list(entry.get("statistical_value_refs") or [])
        item["rendered_artifact_refs"] = [
            str(rendered["png_ref"]),
            str(rendered["pdf_ref"]),
            str(rendered["layout_sidecar_ref"]),
        ]
        item["rendered_artifact_digests"] = {
            str(rendered["png_ref"]): str(rendered["png_sha256"]),
            str(rendered["pdf_ref"]): str(rendered["pdf_sha256"]),
            str(rendered["layout_sidecar_ref"]): str(rendered["layout_sidecar_sha256"]),
        }
        item["render_receipt_ref"] = FIGURE_RENDER_RECEIPT_REF
        item["visual_audit_receipt_ref"] = FIGURE_VISUAL_AUDIT_RECEIPT_REF
        item["polish_lifecycle_ref"] = FIGURE_POLISH_LIFECYCLE_REF
        item["workflow_packet_ref"] = FIGURE_WORKFLOW_PACKET_REF
        item["publication_manifest_ref"] = f"paper/build/{PUBLICATION_MANIFEST_BASENAME}"
        item["display_artifact_manifest_ref"] = f"paper/build/display_artifact_manifest.{figure_id}.json"
        item["display_pack_lock_ref"] = DISPLAY_PACK_LOCK_REF
        item["display_pack_lock_sha256"] = display_pack_lock_sha256
        item["visual_audit"] = {
            "status": str(visual_audit_receipt.get("final_status") or ""),
            "receipt_id": str(visual_audit_receipt.get("receipt_id") or ""),
            "artifact_path": str(audit_artifacts.get(figure_id, {}).get("artifact_path") or rendered["png_ref"]),
            "artifact_sha256": str(audit_artifacts.get(figure_id, {}).get("artifact_sha256") or rendered["png_sha256"]),
            "finding_count": len(visual_audit_receipt.get("findings") or []),
        }
        item["backend_exclusivity_proof"] = {
            "selected_backend": str(entry["renderer_family"]),
            "observed_renderer_family": str(entry["renderer_family"]),
            "cross_backend_visual_fallback_used": False,
            "non_selected_backend_rendered_artifacts": [],
            "render_result_ref": f"{FIGURE_RENDER_RECEIPT_REF}#/figures/{figure_id}/render_result",
        }
        item["render_context"] = dict(entry.get("publication_style_profile") or {})
        changed = True
        updated_figure_ids.append(figure_id)
    if changed:
        _write_json(catalog_path, catalog)
    return {
        "status": "synced" if changed else "no_matching_catalog_entries",
        "ref": _workspace_ref(catalog_path, paper_root=paper_root),
        "path": str(catalog_path),
        "sha256": _sha256_file(catalog_path),
        "updated_figure_ids": updated_figure_ids,
    }


def materialize_display_pack_publication_manifest(
    *,
    repo_root: Path,
    paper_root: Path,
    visual_audit_review: Mapping[str, Any],
    figure_ids: list[str] | tuple[str, ...] | None = None,
    dependency_environment: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    normalized_paper_root = Path(paper_root).expanduser().resolve()
    intent, loaded_figure_specs, _style_reference_bundle = _load_required_quality_inputs(normalized_paper_root)
    requested_figure_ids = [str(item).strip() for item in (figure_ids or []) if str(item).strip()]
    if requested_figure_ids:
        specs_by_id = {str(item["figure_id"]): item for item in loaded_figure_specs}
        missing = [figure_id for figure_id in requested_figure_ids if figure_id not in specs_by_id]
        if missing:
            raise ValueError(f"requested figure_id not found in medical figure specs: {missing[0]}")
        figure_specs = [specs_by_id[figure_id] for figure_id in requested_figure_ids]
    else:
        figure_specs = loaded_figure_specs

    render_dependency_environment = (
        dict(dependency_environment)
        if dependency_environment is not None
        else _dependency_environment_for_figure_specs(
            repo_root=normalized_repo_root,
            paper_root=normalized_paper_root,
            figure_specs=figure_specs,
        )
    )

    figure_entries = []
    for figure_spec in figure_specs:
        figure_id = str(figure_spec["figure_id"])
        intent_figure = _intent_figure(intent, figure_id=figure_id)
        _validate_intent_spec_binding(intent_figure=intent_figure, figure_spec=figure_spec)
        figure_entries.append(
            _render_figure(
                repo_root=normalized_repo_root,
                paper_root=normalized_paper_root,
                figure_spec=figure_spec,
                intent_figure=intent_figure,
                dependency_environment=render_dependency_environment,
            )
        )
    audit_receipt = _write_visual_audit_receipt(
        paper_root=normalized_paper_root,
        figure_entries=figure_entries,
        visual_audit_review=visual_audit_review,
    )
    render_receipt = write_figure_render_receipt(
        paper_root=normalized_paper_root,
        figure_entries=figure_entries,
        timestamp_factory=_utc_now,
        write_json=_write_json,
        dependency_environment=render_dependency_environment,
    )
    lifecycle = _write_figure_polish_lifecycle(
        paper_root=normalized_paper_root,
        figure_entries=figure_entries,
        audit_receipt=audit_receipt,
    )
    workflow_packet = _write_figure_workflow_packet(
        paper_root=normalized_paper_root,
        figure_entries=figure_entries,
        audit_receipt=audit_receipt,
    )
    artifact_manifest_refs = [
        _write_display_artifact_manifest(
            paper_root=normalized_paper_root,
            figure_entry=entry,
        )
        for entry in figure_entries
    ]
    lock_path = write_display_pack_lock(
        paper_root=normalized_paper_root,
        repo_root=normalized_repo_root,
    )
    display_pack_lock = _read_json_object(lock_path)
    publication_style_profile_lock = dict(display_pack_lock.get("publication_style_profile") or {})
    quality_refs = collect_publication_figure_quality_refs(paper_root=normalized_paper_root)
    catalog_sync = _sync_figure_catalog_from_render(
        paper_root=normalized_paper_root,
        figure_entries=figure_entries,
        visual_audit_receipt=audit_receipt,
        display_pack_lock_sha256=_sha256_file(lock_path),
    )
    manifest_path = normalized_paper_root / "build" / PUBLICATION_MANIFEST_BASENAME
    manifest = {
        "schema_version": 1,
        "status": "publication_manifested",
        "manifest_path": str(manifest_path),
        "created_at": _utc_now(),
        "repo_root": str(normalized_repo_root),
        "paper_root": str(normalized_paper_root),
        "display_pack_lock_path": str(lock_path),
        "display_pack_lock_ref": _workspace_ref(lock_path, paper_root=normalized_paper_root),
        "display_pack_lock_sha256": _sha256_file(lock_path),
        "publication_style_profile": publication_style_profile_lock,
        "dependency_environment": render_dependency_environment,
        "publication_readiness_verdict": False,
        "authority_boundary": {
            "mas_display_artifact_authority": True,
            "mas_publication_quality_authority": True,
            "opl_pack_os_lifecycle_owner": True,
            **dependency_environment_authority_boundary(),
            "display_pack_lock_can_authorize_publication_readiness": False,
            "ai_visual_audit_can_mutate_data_or_statistics": False,
        },
        "publication_figure_quality_refs": quality_refs,
        "figure_provenance_index_ref": PROVENANCE_INDEX_REF,
        "figure_polish_lifecycle": {
            "path": str(normalized_paper_root / "figure_polish_lifecycle.json"),
            "ref": FIGURE_POLISH_LIFECYCLE_REF,
            "states": [event["state"] for event in lifecycle["events"]],
        },
        "figure_workflow_packet": {
            "path": str(normalized_paper_root / "figure_workflow_packet.json"),
            "ref": FIGURE_WORKFLOW_PACKET_REF,
            "workflow_status": workflow_packet["workflow_status"],
            "figure_count": len(workflow_packet["figures"]),
            "payload": workflow_packet,
        },
        "visual_audit": {
            "path": str(normalized_paper_root / "figure_visual_audit_receipt.json"),
            "ref": FIGURE_VISUAL_AUDIT_RECEIPT_REF,
            "final_status": audit_receipt["final_status"],
            "finding_count": len(audit_receipt["findings"]),
        },
        "figure_render_receipt": {
            "path": str(normalized_paper_root / "figure_render_receipt.json"),
            "ref": FIGURE_RENDER_RECEIPT_REF,
            "figure_count": len(render_receipt["figures"]),
            "dependency_environment": dict(render_receipt.get("dependency_environment") or {}),
        },
        "figure_catalog_sync": catalog_sync,
        "display_artifact_manifests": [
            {key: value for key, value in item.items() if key != "payload"}
            for item in artifact_manifest_refs
        ],
        "figures": figure_entries,
    }
    _write_json(manifest_path, manifest)
    provenance_index = materialize_figure_provenance_bundles(
        repo_root=normalized_repo_root,
        paper_root=normalized_paper_root,
    )
    provenance_entries_by_id = {
        str(item["figure_id"]): item
        for item in provenance_index["bundles"]
    }
    for figure in manifest["figures"]:
        entry = provenance_entries_by_id.get(str(figure.get("figure_id") or ""))
        if entry is None:
            continue
        figure["provenance_bundle_ref"] = str(entry["provenance_bundle_ref"])
        figure["provenance_bundle_hash"] = str(entry["provenance_bundle_hash"])
        figure["provenance_readback_ref"] = str(entry["provenance_readback_ref"])
        figure["provenance_typed_issue_codes"] = list(entry.get("typed_issue_codes") or [])
    return {
        **manifest,
        "figure_provenance_index": {
            "path": provenance_index["path"],
            "ref": provenance_index["ref"],
            "sha256": provenance_index["sha256"],
            "bundle_count": provenance_index["bundle_count"],
            "bundles": provenance_index["bundles"],
        },
    }


def render_display_pack_candidate_asset(
    *,
    repo_root: Path,
    template_id: str,
    display_payload_file: Path,
    output_dir: Path,
) -> dict[str, Any]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    normalized_output_dir = Path(output_dir).expanduser().resolve()
    payload_path = Path(display_payload_file).expanduser().resolve()
    display_payload = _read_json_object(payload_path)
    runtime = resolve_display_template_runtime(
        repo_root=normalized_repo_root,
        paper_root=None,
        template_id=template_id,
        inventory_scope="all",
    )
    template_manifest = runtime.template_manifest
    candidate_script_path = runtime.template_path.parent / "render_candidate.R"
    if not candidate_script_path.is_file():
        raise ValueError(
            f"display template `{template_id}` does not provide render_candidate.R"
        )
    figure_id = f"candidate-{template_manifest.template_id}"
    stem = _safe_artifact_stem(template_manifest.template_id)
    output_png_path = normalized_output_dir / f"{stem}.png"
    output_pdf_path = normalized_output_dir / f"{stem}.pdf"
    layout_sidecar_path = normalized_output_dir / f"{stem}.layout.json"
    render_result = _run_candidate_subprocess_renderer(
        runtime_template_root=runtime.template_path.parent,
        pack_root=runtime.pack_root,
        paper_root=normalized_output_dir,
        figure_id=figure_id,
        full_template_id=template_manifest.full_template_id,
        short_template_id=template_manifest.template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )
    for path in (output_png_path, output_pdf_path, layout_sidecar_path):
        if not path.exists():
            raise FileNotFoundError(f"candidate display renderer did not write required artifact: {path}")
    return {
        "schema_version": 1,
        "status": "rendered",
        "candidate_only": True,
        "comparison_only": True,
        "publication_readiness_verdict": False,
        "repo_root": str(normalized_repo_root),
        "template_id": template_manifest.full_template_id,
        "short_template_id": template_manifest.template_id,
        "display_payload_path": str(payload_path),
        "candidate_entrypoint": "Rscript render_candidate.R --request {request_json}",
        "comparison_entrypoint": "Rscript render_candidate.R --request {request_json}",
        "default_renderer": {
            "renderer_family": template_manifest.renderer_family,
            "execution_mode": template_manifest.execution_mode,
            "entrypoint": template_manifest.entrypoint,
        },
        "authority_boundary": {
            "candidate_can_authorize_publication_readiness": False,
            "candidate_can_mutate_data_or_statistics": False,
            "candidate_can_replace_default_renderer": False,
            "comparison_receipt_can_authorize_publication_readiness": False,
            "comparison_receipt_can_replace_default_renderer": False,
            "default_renderer_promotion_already_landed": (
                template_manifest.renderer_family == "r_ggplot2"
                and template_manifest.execution_mode == "subprocess"
                and template_manifest.entrypoint == "Rscript render.R --request {request_json}"
            ),
        },
        "render_result": render_result,
        "rendered_artifacts": {
            "png_path": str(output_png_path),
            "pdf_path": str(output_pdf_path),
            "layout_sidecar_path": str(layout_sidecar_path),
            "png_ref": _workspace_ref(output_png_path, paper_root=normalized_output_dir),
            "pdf_ref": _workspace_ref(output_pdf_path, paper_root=normalized_output_dir),
            "layout_sidecar_ref": _workspace_ref(layout_sidecar_path, paper_root=normalized_output_dir),
            "png_sha256": _sha256_file(output_png_path),
            "pdf_sha256": _sha256_file(output_pdf_path),
            "layout_sidecar_sha256": _sha256_file(layout_sidecar_path),
        },
    }


__all__ = [
    "PUBLICATION_MANIFEST_BASENAME",
    "materialize_display_pack_publication_manifest",
    "render_display_pack_candidate_asset",
]
