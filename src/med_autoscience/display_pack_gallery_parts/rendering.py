from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import subprocess

from med_autoscience.display_pack_gallery_catalog import TemplateRecord
from med_autoscience.display_pack_gallery_parts import paths
from med_autoscience.display_pack_gallery_parts.assets import (
    RenderedAsset,
    _image_size,
    _relative_ref,
    _square_gallery_preview,
    _strip_trailing_whitespace,
    write_json,
)
from med_autoscience.display_pack_gallery_parts.payloads import (
    LEGACY_PYTHON_BASELINE_EXCLUDED,
    _load_r_gallery_payload,
    _python_display_payload,
    _style_context_for,
)

def _render_r_template(record: TemplateRecord, seed_payloads: dict[str, dict[str, Any]]) -> RenderedAsset:
    payload = _load_r_gallery_payload(record.template_id, seed_payloads)
    payload_path = paths.ASSET_ROOT / f"{record.template_id}.payload.json"
    output_png = paths.ASSET_ROOT / f"{record.template_id}.png"
    output_pdf = paths.ASSET_ROOT / f"{record.template_id}.pdf"
    output_layout = paths.ASSET_ROOT / f"{record.template_id}.layout.json"
    request_path = paths.ASSET_ROOT / f"{record.template_id}.render_request.json"
    write_json(payload_path, payload)
    request = {
        "schema_version": 1,
        "execution_mode": record.execution_mode,
        "renderer_family": record.renderer_family,
        "figure_id": record.template_id,
        "template_id": record.full_template_id,
        "short_template_id": record.template_id,
        "display_payload": payload,
        "output_png_path": str(output_png),
        "output_pdf_path": str(output_pdf),
        "layout_sidecar_path": str(output_layout),
    }
    write_json(request_path, request)
    env = {
        **dict(os.environ),
        "MAS_DISPLAY_OUTPUT_WIDTH_IN": "5",
        "MAS_DISPLAY_OUTPUT_HEIGHT_IN": "5",
    }
    result = subprocess.run(
        ["Rscript", "render.R", "--request", str(request_path)],
        cwd=record.template_dir,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        env=env,
    )
    request_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"{record.template_id} render failed with code {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    for path in (output_png, output_pdf, output_layout):
        if not path.is_file():
            raise FileNotFoundError(f"{record.template_id} did not write {path}")
    preview_path, preview_size = _square_gallery_preview(output_png)
    return RenderedAsset(
        status="rendered",
        image_ref=_relative_ref(output_png),
        preview_image_ref=_relative_ref(preview_path),
        payload_ref=_relative_ref(payload_path),
        layout_ref=_relative_ref(output_layout),
        pdf_ref=_relative_ref(output_pdf),
        image_size_px=_image_size(output_png),
        preview_image_size_px=preview_size,
    )
def _render_python_template(
    record: TemplateRecord,
    payload: dict[str, Any],
    *,
    output_root: Path,
    suffix: str,
) -> RenderedAsset:
    output_root.mkdir(parents=True, exist_ok=True)
    output_png = output_root / f"{record.template_id}.{suffix}.png"
    output_pdf = output_root / f"{record.template_id}.{suffix}.pdf"
    output_svg = output_root / f"{record.template_id}.{suffix}.svg"
    output_layout = output_root / f"{record.template_id}.{suffix}.layout.json"
    payload_path = output_root / f"{record.template_id}.{suffix}.payload.json"
    render_payload = json.loads(json.dumps(payload))
    render_context = _style_context_for(record.template_id)
    if record.kind == "evidence_figure":
        render_payload["render_context"] = render_context
    write_json(payload_path, render_payload)
    if record.kind == "evidence_figure":
        from fenggaolab_org_medical_display_core.evidence_figures import render_python_evidence_figure

        try:
            render_python_evidence_figure(
                template_id=record.full_template_id,
                display_payload=render_payload,
                output_png_path=output_png,
                output_pdf_path=output_pdf,
                output_svg_path=output_svg,
                layout_sidecar_path=output_layout,
            )
        except TypeError as exc:
            if "output_svg_path" not in str(exc):
                raise
            render_python_evidence_figure(
                template_id=record.full_template_id,
                display_payload=render_payload,
                output_png_path=output_png,
                output_pdf_path=output_pdf,
                layout_sidecar_path=output_layout,
            )
    elif record.kind == "illustration_shell":
        from fenggaolab_org_medical_display_core.illustration_shells import render_illustration_shell

        render_illustration_shell(
            template_id=record.full_template_id,
            shell_payload=render_payload,
            render_context=render_context,
            output_svg_path=output_svg,
            output_png_path=output_png,
            output_pdf_path=output_pdf,
            output_layout_path=output_layout,
            payload_path=payload_path,
        )
    else:
        raise RuntimeError(f"unsupported python gallery kind `{record.kind}`")
    for path in (output_png, output_layout):
        if not path.is_file():
            raise FileNotFoundError(f"{record.template_id} did not write {path}")
    _strip_trailing_whitespace(output_svg)
    preview_path, preview_size = _square_gallery_preview(output_png)
    return RenderedAsset(
        status="rendered",
        image_ref=_relative_ref(output_png),
        preview_image_ref=_relative_ref(preview_path),
        payload_ref=_relative_ref(payload_path),
        layout_ref=_relative_ref(output_layout),
        pdf_ref=_relative_ref(output_pdf) if output_pdf.is_file() else "",
        svg_ref=_relative_ref(output_svg) if output_svg.is_file() else "",
        image_size_px=_image_size(output_png),
        preview_image_size_px=preview_size,
    )


def _legacy_python_baseline_payload(
    record: TemplateRecord,
    fixture_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    try:
        return _python_display_payload(record, fixture_payloads)
    except RuntimeError:
        return None


def _render_legacy_python_baseline(record: TemplateRecord, payload: dict[str, Any] | None) -> RenderedAsset:
    if record.template_id in LEGACY_PYTHON_BASELINE_EXCLUDED:
        return RenderedAsset(status="excluded", reason="legacy_python_baseline_failed_previous_render")
    if record.previous_renderer_family != "python" or not record.previous_entrypoint:
        return RenderedAsset(status="not_applicable")
    if payload is None:
        return RenderedAsset(status="not_available", reason="legacy_python_fixture_missing")
    previous_record = TemplateRecord(
        template_id=record.template_id,
        full_template_id=record.full_template_id,
        display_name=record.display_name,
        kind=record.kind,
        audit_family=record.audit_family,
        renderer_family="python",
        execution_mode="python_plugin",
        entrypoint=record.previous_entrypoint,
        previous_renderer_family="",
        previous_entrypoint="",
        paper_proven=record.paper_proven,
        required_exports=record.required_exports,
        template_dir=record.template_dir,
        canonical_family_id=record.canonical_family_id,
        canonical_family_title=record.canonical_family_title,
        canonical_family_category=record.canonical_family_category,
        canonical_template_id=record.canonical_template_id,
        figure_archetype=record.figure_archetype,
        migration_status=record.migration_status,
        default_visible=record.default_visible,
        migrated_alias_template_ids=record.migrated_alias_template_ids,
        migration_reason=record.migration_reason,
    )
    try:
        return _render_python_template(previous_record, payload, output_root=paths.PYTHON_BASELINE_ROOT, suffix="python")
    except Exception as exc:
        return RenderedAsset(status="excluded", reason=f"legacy_python_baseline_render_failed: {type(exc).__name__}: {exc}")
