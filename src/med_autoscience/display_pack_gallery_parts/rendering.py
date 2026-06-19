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
    _load_r_gallery_payload,
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
        raise RuntimeError("Python evidence templates are not retained in the current gallery")
    write_json(payload_path, render_payload)
    if record.kind == "illustration_shell":
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
