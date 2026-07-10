from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from med_autoscience.display_pack_gallery_catalog import (
    TABLE_PREVIEW_GALLERY_TEMPLATE_IDS,
    gallery_display_records,
    gallery_visual_records,
    read_template_records,
    table_preview_gallery_records,
)
from med_autoscience.display_pack_gallery import paths
from med_autoscience.display_pack_gallery.assets import RenderedAsset, _clean_assets, _strip_trailing_whitespace, write_json
from med_autoscience.display_pack_gallery.html import _render_html
from med_autoscience.display_pack_gallery.manifest import build_manifest
from med_autoscience.display_pack_gallery.lidocaineq_parity_audit import (
    write_lidocaineq_visual_parity_audit,
)
from med_autoscience.display_pack_gallery.payloads import _load_python_payload_fixtures, _load_seed_r_payloads, _python_display_payload
from med_autoscience.display_pack_gallery.pdf import _export_pdf
from med_autoscience.display_pack_gallery.quality import build_quality_audit_markdown
from med_autoscience.display_pack_gallery.reference_writer import _write_reference
from med_autoscience.display_pack_gallery.rendering import (
    _existing_python_template_asset,
    _existing_r_template_asset,
    _render_python_template,
    _render_r_gallery_preview,
    _render_r_template,
)
from med_autoscience.display_pack_gallery.status_writer import build_gallery_status_markdown
from med_autoscience.display_template_catalog import render_display_template_catalog_markdown


def _is_dependency_environment_error(exc: Exception) -> bool:
    message = str(exc)
    return (
        "dependency run-context" in message
        or "OPL prepare" in message
        or "OPL doctor" in message
        or "managed R library" in message
        or "requires OPL-prepared" in message
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
        help="Write an on-demand template catalog snapshot into docs. Gallery review artifacts are owned by ScholarSkills.",
    )
    parser.add_argument(
        "--force-render",
        action="store_true",
        help="Ignore cached figure assets, clean the asset directory, and re-render every visible template.",
    )
    parser.add_argument(
        "--package-only",
        action="store_true",
        help="Do not invoke renderers; rebuild HTML/PDF/local gallery markdown outputs from existing gallery assets only.",
    )
    return parser.parse_args(argv)


def _render_records(
    records: list,
    *,
    force_render: bool,
    package_only: bool,
) -> tuple[dict[str, RenderedAsset], dict[str, RenderedAsset]]:
    seed_r_payloads = _load_seed_r_payloads(records, pack_root=paths.PACK_ROOT)
    fixture_payloads = _load_python_payload_fixtures()
    rendered: dict[str, RenderedAsset] = {}
    visible_template_ids = {record.template_id for record in gallery_visual_records(records)}
    for record in records:
        if record.template_id not in visible_template_ids and record.template_id not in TABLE_PREVIEW_GALLERY_TEMPLATE_IDS:
            rendered[record.template_id] = RenderedAsset(
                status="not_default",
                reason="hidden_from_default_gallery_or_non_visual_inventory",
            )
            continue
        if record.renderer_family == "r_ggplot2":
            try:
                if package_only:
                    rendered[record.template_id] = _existing_r_template_asset(
                        record,
                        cache_status="package_only",
                    )
                else:
                    rendered[record.template_id] = _render_r_template(
                        record,
                        seed_r_payloads,
                        force_render=force_render,
                    )
            except Exception as exc:
                if record.template_id == "cohort_flow_figure":
                    if _is_dependency_environment_error(exc):
                        raise
                    rendered[record.template_id] = RenderedAsset(
                        status="not_rendered",
                        reason=f"{type(exc).__name__}: {exc}",
                    )
                    continue
                raise
        elif record.kind == "illustration_shell" and record.renderer_family == "python":
            try:
                payload = _python_display_payload(record, fixture_payloads)
                if package_only:
                    rendered[record.template_id] = _existing_python_template_asset(
                        record,
                        output_root=paths.ASSET_ROOT,
                        suffix="design",
                        cache_status="package_only",
                    )
                else:
                    rendered[record.template_id] = _render_python_template(
                        record,
                        payload,
                        output_root=paths.ASSET_ROOT,
                        suffix="design",
                        force_render=force_render,
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
        elif record.template_id in TABLE_PREVIEW_GALLERY_TEMPLATE_IDS:
            if package_only:
                rendered[record.template_id] = _existing_r_template_asset(
                    record,
                    cache_status="package_only",
                )
            else:
                rendered[record.template_id] = _render_r_gallery_preview(
                    record,
                    seed_r_payloads,
                    force_render=force_render,
                )
        else:
            rendered[record.template_id] = RenderedAsset(status="not_visual", reason="table_shell_or_non_visual_template")
    return rendered, {}


def _render_cache_summary(rendered: dict[str, RenderedAsset]) -> dict[str, int]:
    rendered_assets = [asset for asset in rendered.values() if asset.status == "rendered"]
    return {
        "cache_hit": sum(1 for asset in rendered_assets if asset.render_cache_status == "hit"),
        "cache_miss": sum(1 for asset in rendered_assets if asset.render_cache_status == "miss"),
        "package_only": sum(1 for asset in rendered_assets if asset.render_cache_status == "package_only"),
        "cache_untracked": sum(1 for asset in rendered_assets if not asset.render_cache_status),
    }


def _prepare_asset_root(*, force_render: bool, package_only: bool) -> dict[str, object]:
    if force_render:
        _clean_assets()
        return {"status": "cleaned_for_force_render", "copied_file_count": 0}
    paths.ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    if package_only:
        return {
            "status": "use_existing_output_asset_root",
            "source_asset_root": str(paths.ASSET_ROOT),
            "target_asset_root": str(paths.ASSET_ROOT),
            "copied_file_count": 0,
        }
    return {"status": "reuse_output_asset_root", "copied_file_count": 0}


def _package_only_required_assets(records: list) -> list[Path]:
    required: list[Path] = []
    visible_records = gallery_visual_records(records)
    for record in visible_records:
        suffix = ".design" if record.kind == "illustration_shell" and record.renderer_family == "python" else ""
        required.extend(
            [
                paths.ASSET_ROOT / f"{record.template_id}{suffix}.payload.json",
                paths.ASSET_ROOT / f"{record.template_id}{suffix}.png",
                paths.ASSET_ROOT / f"{record.template_id}{suffix}.layout.json",
            ]
        )
        if record.renderer_family == "r_ggplot2":
            required.append(paths.ASSET_ROOT / f"{record.template_id}.pdf")
        if record.kind == "illustration_shell" and record.renderer_family == "python":
            required.append(paths.ASSET_ROOT / f"{record.template_id}.design.svg")
    return required


def _assert_package_only_assets_ready(records: list) -> None:
    missing = [path for path in _package_only_required_assets(records) if not path.is_file()]
    if missing:
        preview = ", ".join(str(path) for path in missing[:12])
        remaining = len(missing) - min(len(missing), 12)
        suffix = f"; and {remaining} more" if remaining else ""
        raise RuntimeError(
            "package-only gallery build requires existing rendered gallery assets. "
            f"Missing {len(missing)} required files: {preview}{suffix}. "
            "Run the normal gallery build after OPL dependency prepare, or restore the local output gallery assets."
        )


def _publish_template_catalog() -> None:
    paths.DOCS_TEMPLATE_CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    paths.DOCS_TEMPLATE_CATALOG_PATH.write_text(
        render_display_template_catalog_markdown(),
        encoding="utf-8",
    )
    _strip_trailing_whitespace(paths.DOCS_TEMPLATE_CATALOG_PATH)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.force_render and args.package_only:
        raise ValueError("--force-render and --package-only cannot be used together")
    paths.configure_output_paths(args.output_root)
    paths.HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not args.package_only and shutil.which("Rscript") is None:
        raise RuntimeError("Rscript is required to rebuild the gallery")

    records = read_template_records(paths.PACK_ROOT, paths.TEMPLATE_ROOT)
    asset_reuse = _prepare_asset_root(
        force_render=bool(args.force_render),
        package_only=bool(args.package_only),
    )
    if args.package_only:
        _assert_package_only_assets_ready(records)
    rendered, baseline_rendered = _render_records(
        records,
        force_render=args.force_render,
        package_only=args.package_only,
    )

    paths.HTML_PATH.write_text(_render_html(records, rendered, baseline_rendered), encoding="utf-8")
    _strip_trailing_whitespace(paths.HTML_PATH)
    _write_reference(records, rendered, baseline_rendered, reference_path=paths.REFERENCE_PATH)
    _strip_trailing_whitespace(paths.REFERENCE_PATH)

    manifest = build_manifest(
        records=records,
        rendered=rendered,
        baseline_rendered=baseline_rendered,
        publish_docs=args.publish_docs,
        render_cache_summary=_render_cache_summary(rendered),
        force_render=bool(args.force_render),
        package_only=bool(args.package_only),
    )
    manifest["lidocaineq_visual_parity_audit_path"] = str(paths.LIDOCAINEQ_PARITY_AUDIT_PATH)
    manifest["lidocaineq_visual_parity_audit_json_path"] = str(paths.LIDOCAINEQ_PARITY_AUDIT_JSON_PATH)
    manifest["lidocaineq_visual_parity_contact_sheet_path"] = str(paths.LIDOCAINEQ_PARITY_CONTACT_SHEET_PATH)
    manifest["asset_reuse"] = asset_reuse
    parity_audit = write_lidocaineq_visual_parity_audit(manifest)
    manifest["lidocaineq_visual_parity_audit"] = {
        "schema_version": parity_audit["schema_version"],
        "source_project": parity_audit["source_project"],
        "reference_root": parity_audit["reference_root"],
        "reference_template_count": parity_audit["reference_template_count"],
        "status_counts": parity_audit["status_counts"],
        "contact_sheet_path": paths.repo_relative_path(paths.LIDOCAINEQ_PARITY_CONTACT_SHEET_PATH),
        "markdown_path": paths.repo_relative_path(paths.LIDOCAINEQ_PARITY_AUDIT_PATH),
        "json_path": paths.repo_relative_path(paths.LIDOCAINEQ_PARITY_AUDIT_JSON_PATH),
    }
    write_json(paths.MANIFEST_PATH, manifest)
    paths.QUALITY_AUDIT_PATH.write_text(
        build_quality_audit_markdown(manifest["quality_audit"]),
        encoding="utf-8",
    )
    _strip_trailing_whitespace(paths.QUALITY_AUDIT_PATH)
    paths.STATUS_PATH.write_text(
        build_gallery_status_markdown(manifest),
        encoding="utf-8",
    )
    _strip_trailing_whitespace(paths.STATUS_PATH)
    _export_pdf()
    if args.publish_docs:
        _publish_template_catalog()

    visible_records = gallery_display_records(records)
    visible_visual_records = gallery_visual_records(records)
    table_preview_records = table_preview_gallery_records(records)
    print(
        json.dumps(
            {
                "status": "rendered",
                "active_templates": len(visible_records),
                "gallery_visual_templates": len(visible_visual_records),
                "migration_inventory_templates": len(records),
                "design_gallery_templates": manifest["design_gallery_template_count"],
                "table_preview_gallery_templates": len(table_preview_records),
                "non_visual_canonical_templates": manifest["non_visual_canonical_template_count"],
                "rendered_image_templates": manifest["rendered_image_template_count"],
                "internal_rendered_image_templates": manifest["internal_rendered_image_template_count"],
                "lidocaineq_reference_template_count": manifest["lidocaineq_reference_coverage"]["reference_template_count"],
                "lidocaineq_covered_reference_template_count": manifest["lidocaineq_reference_coverage"]["covered_reference_template_count"],
                "lidocaineq_reference_coverage_complete": manifest["lidocaineq_reference_coverage"]["coverage_complete"],
                "lidocaineq_missing_or_downgraded_reference_template_ids": manifest["lidocaineq_reference_coverage"]["missing_or_downgraded_reference_template_ids"],
                "lidocaineq_replacement_template_count": manifest["lidocaineq_reference_coverage"]["replacement_template_count"],
                "lidocaineq_do_not_restore_legacy_alias_count": manifest["lidocaineq_reference_coverage"]["do_not_restore_legacy_alias_count"],
                "quality_overall_status": manifest["quality_audit"]["overall_status"],
                "publication_ready_claim_authorized": manifest["quality_audit"]["publication_ready_claim_authorized"],
                "render_cache_summary": manifest["render_cache_summary"],
                "asset_reuse": manifest["asset_reuse"],
                "force_render": manifest["force_render"],
                "package_only": manifest["package_only"],
                "html_path": str(paths.HTML_PATH),
                "pdf_path": str(paths.PDF_PATH),
                "quality_audit_path": str(paths.QUALITY_AUDIT_PATH),
                "lidocaineq_visual_parity_audit_path": str(paths.LIDOCAINEQ_PARITY_AUDIT_PATH),
                "lidocaineq_visual_parity_audit_json_path": str(paths.LIDOCAINEQ_PARITY_AUDIT_JSON_PATH),
                "lidocaineq_visual_parity_contact_sheet_path": str(paths.LIDOCAINEQ_PARITY_CONTACT_SHEET_PATH),
                "status_path": str(paths.STATUS_PATH),
                "docs_template_catalog_path": str(paths.DOCS_TEMPLATE_CATALOG_PATH) if args.publish_docs else "",
                "docs_gallery_review_package_owner": "ScholarSkills" if args.publish_docs else "",
                "manifest_path": str(paths.MANIFEST_PATH),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0
