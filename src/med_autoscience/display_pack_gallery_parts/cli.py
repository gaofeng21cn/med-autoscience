from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from med_autoscience.display_pack_gallery_catalog import read_template_records, visual_gallery_records
from med_autoscience.display_pack_gallery_parts import paths
from med_autoscience.display_pack_gallery_parts.assets import RenderedAsset, _clean_assets, _strip_trailing_whitespace, write_json
from med_autoscience.display_pack_gallery_parts.html import _render_html
from med_autoscience.display_pack_gallery_parts.manifest import build_manifest
from med_autoscience.display_pack_gallery_parts.payloads import _load_python_payload_fixtures, _load_seed_r_payloads, _python_display_payload
from med_autoscience.display_pack_gallery_parts.pdf import _copy_docs_gallery, _export_pdf
from med_autoscience.display_pack_gallery_parts.quality import build_quality_audit_markdown
from med_autoscience.display_pack_gallery_parts.reference_writer import _write_reference
from med_autoscience.display_pack_gallery_parts.rendering import (
    _render_python_template,
    _render_r_template,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the local MAS display-pack gallery.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=paths.DEFAULT_OUTPUT_ROOT,
        help="Local gallery output root. Defaults to outputs/display-pack-gallery.",
    )
    parser.add_argument(
        "--publish-docs",
        action="store_true",
        help="Copy the gallery PDF, reference markdown, and quality audit into docs.",
    )
    return parser.parse_args(argv)


def _render_records(records: list) -> tuple[dict[str, RenderedAsset], dict[str, RenderedAsset]]:
    seed_r_payloads = _load_seed_r_payloads(records)
    fixture_payloads = _load_python_payload_fixtures()
    rendered: dict[str, RenderedAsset] = {}
    visible_template_ids = {record.template_id for record in visual_gallery_records(records)}
    for record in records:
        if record.template_id not in visible_template_ids:
            rendered[record.template_id] = RenderedAsset(
                status="not_default",
                reason="hidden_from_default_gallery_or_non_visual_inventory",
            )
            continue
        if record.renderer_family == "r_ggplot2":
            rendered[record.template_id] = _render_r_template(record, seed_r_payloads)
        elif record.kind == "illustration_shell" and record.renderer_family == "python":
            try:
                payload = _python_display_payload(record, fixture_payloads)
                rendered[record.template_id] = _render_python_template(
                    record,
                    payload,
                    output_root=paths.ASSET_ROOT,
                    suffix="python",
                )
            except Exception as exc:
                rendered[record.template_id] = RenderedAsset(
                    status="not_rendered",
                    reason=f"{type(exc).__name__}: {exc}",
                )
        elif record.kind == "evidence_figure" and record.renderer_family == "python":
            rendered[record.template_id] = RenderedAsset(
                status="policy_violation",
                reason="python_evidence_templates_are_not_retained_without_documented_advantage_proof",
            )
        else:
            rendered[record.template_id] = RenderedAsset(status="not_visual", reason="table_shell_or_non_visual_template")
    return rendered, {}


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    paths.configure_output_paths(args.output_root)
    if shutil.which("Rscript") is None:
        raise RuntimeError("Rscript is required to rebuild the gallery")

    records = read_template_records(paths.PACK_ROOT, paths.TEMPLATE_ROOT)
    _clean_assets()
    rendered, baseline_rendered = _render_records(records)

    paths.HTML_PATH.write_text(_render_html(records, rendered, baseline_rendered), encoding="utf-8")
    _strip_trailing_whitespace(paths.HTML_PATH)
    _write_reference(records, rendered, baseline_rendered, reference_path=paths.REFERENCE_PATH)
    _strip_trailing_whitespace(paths.REFERENCE_PATH)

    manifest = build_manifest(
        records=records,
        rendered=rendered,
        baseline_rendered=baseline_rendered,
        publish_docs=args.publish_docs,
    )
    write_json(paths.MANIFEST_PATH, manifest)
    paths.QUALITY_AUDIT_PATH.write_text(
        build_quality_audit_markdown(manifest["quality_audit"]),
        encoding="utf-8",
    )
    _strip_trailing_whitespace(paths.QUALITY_AUDIT_PATH)
    _export_pdf()
    if args.publish_docs:
        _copy_docs_gallery()

    visible_records = visual_gallery_records(records)
    print(
        json.dumps(
            {
                "status": "rendered",
                "active_templates": len(visible_records),
                "migration_inventory_templates": len(records),
                "non_visual_canonical_templates": manifest["non_visual_canonical_template_count"],
                "rendered_image_templates": manifest["rendered_image_template_count"],
                "internal_rendered_image_templates": manifest["internal_rendered_image_template_count"],
                "quality_overall_status": manifest["quality_audit"]["overall_status"],
                "publication_ready_claim_authorized": manifest["quality_audit"]["publication_ready_claim_authorized"],
                "html_path": str(paths.HTML_PATH),
                "pdf_path": str(paths.PDF_PATH),
                "quality_audit_path": str(paths.QUALITY_AUDIT_PATH),
                "docs_pdf_path": str(paths.DOCS_PDF_PATH) if args.publish_docs else "",
                "docs_reference_path": str(paths.DOCS_REFERENCE_PATH) if args.publish_docs else "",
                "docs_quality_audit_path": str(paths.DOCS_QUALITY_AUDIT_PATH) if args.publish_docs else "",
                "manifest_path": str(paths.MANIFEST_PATH),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0
