import argparse
import inspect
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..shared_base import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    _attach_pack_provenance,
    _build_display_pack_summary_by_id,
    _load_display_pack_lock_payload,
    _resolve_pack_id,
    build_figure_basename,
    build_front_matter_placeholders,
    build_submission_minimal_readme,
    build_table_basename,
    copy_with_renamed_targets,
    create_staging_output_root,
    delivery_label_root_from_paper_root,
    dump_json,
    find_missing_source_paths,
    is_frontiers_family_harvard_profile,
    is_planned_catalog_entry,
    load_json,
    materialize_and_validate_submission_references,
    materialize_archived_reference_only_submission_surface_manifests,
    prune_legacy_paper_surface_exports,
    relpath_from_workspace,
    remap_staging_path_to_target,
    remap_staging_relpath_to_target,
    replace_directory_atomically,
    resolve_bundle_input_path,
    resolve_compile_report_path,
    resolve_compiled_markdown_path,
    resolve_compiled_pdf_path,
    resolve_output_root,
    resolve_publication_profile_config,
    resolve_relpath,
    resolve_submission_compiled_source_excluded_roots,
    resolve_table_source_paths,
    split_front_matter,
    utc_now,
    workspace_root_from_paper_root,
    write_text,
)
from ..authority import (
    _authority_blocking_artifact_refs,
    _authority_gate_fingerprint,
    _authority_handshake_fields,
    _resolve_authority_contract_markdown_path,
    describe_submission_minimal_authority,
)
from ..authority_note import (
    attach_submission_source_authority_note_qc,
    write_submission_source_authority_note,
)
from ..markdown_surface import (
    MANUSCRIPT_SHAPED_AUXILIARY_TOP_LEVEL_HEADINGS,
    MARKDOWN_IMAGE_LINE_PATTERN,
    _build_catalog_figure_heading,
    _ensure_submission_image_width,
    _first_image_alt_text,
    _iter_figure_semantics_items,
    _natural_figure_sort_key,
    _select_submission_markdown_figure_source,
    _sorted_figure_catalog_entries,
    _submission_markdown_figure_relpath,
    _submission_markdown_image_line,
    build_catalog_backed_figure_blocks,
    build_catalog_backed_main_figures,
    build_catalog_backed_submission_figure_image_map,
    build_figure_legend_blocks,
    build_frontiers_required_sections,
    build_submission_figure_blocks,
    build_table_blocks,
    canonicalize_manuscript_major_heading,
    collect_duplicate_manuscript_major_sections,
    collect_internal_instruction_hits,
    contains_internal_instruction_text,
    count_main_text_figures_in_catalog,
    extract_block_between_markers,
    extract_image_lines,
    extract_main_figure_blocks,
    extract_markdown_block,
    extract_optional_block_between_markers,
    extract_optional_markdown_block,
    figure_id_aliases,
    first_nonempty_block,
    first_nonempty_named_block,
    is_markdown_image_line,
    load_figure_semantics_map,
    merge_legend_with_figure_semantics,
    normalize_materialized_figure_heading,
    normalize_submission_figure_alt_text,
    normalize_submission_figure_heading,
    parse_figure_blocks,
    parse_figure_id_from_heading,
    parse_manuscript_shaped_draft,
    rewrite_image_paths,
    rewrite_submission_surface_image_lines,
    sort_main_figure_blocks,
    strip_image_lines,
)
from ..post_materialization_sync import replay_post_submission_minimal_sync
from ..markdown_surface_qc import build_submission_manuscript_surface_qc
from .supplementary_material import (
    build_combined_review_markdown,
    build_combined_supplementary_markdown,
    build_supplementary_figures_markdown,
    build_supplementary_tables_markdown,
    build_supplementary_tables_pdf,
    build_supplementary_tables_workbook,
    materialize_submission_figure_entry,
    supplementary_material_payload,
    write_combined_review_pdf,
    write_pdf_bundle,
)
from ..profile_builders import (
    _extract_canonical_manuscript_section,
    _extract_named_markdown_section,
    _matches_named_markdown_heading,
    _remove_canonical_manuscript_section,
    build_frontiers_manuscript_markdown,
    build_frontiers_supplementary_markdown,
    build_general_medical_inline_supplementary_section_markdown,
    build_general_medical_submission_markdown,
    should_build_general_medical_submission_markdown,
)
from ..source_contract import build_submission_minimal_source_contract
from ..source_hydration import (
    _filter_nested_figure_catalog_to_canonical_main_figures,
    hydrate_submission_package_sources_from_current_body,
)
from ..export_renderers import default_pdf_rendering_profile, export_docx, export_pdf
from .delivery_layout import (
    apply_controller_authorized_delivery_layout,
    write_submission_lineage_reproducibility_bundle,
    write_submission_reproducibility_documents,
)
from med_autoscience.controllers import paper_authority_delivery_guard
from med_autoscience.controllers.submission_package_layout import (
    build_package_layout_block,
    audit_path,
    submission_manifest_path as layout_submission_manifest_path,
)


def _journal_target_payload(profile_config: Any) -> dict[str, str] | None:
    if profile_config.reference_doc_path is None:
        return None
    journal_target = {
        "reference_doc_path": str(profile_config.reference_doc_path.resolve()),
    }
    optional_fields = (
        ("journal_name", profile_config.journal_name),
        ("journal_family", profile_config.journal_family),
        ("reference_style_family", profile_config.reference_style_family),
    )
    for key, value in optional_fields:
        if value is not None:
            journal_target[key] = value
    return journal_target


_SUBMISSION_AUDIT_MATERIALIZATION_BLOCKERS = frozenset(
    {
        "authority_snapshot_missing",
        "dispatch_gate_blocked",
        "submission_authority_or_human_gate_closeout_required",
    }
)


def _can_materialize_submission_audit_package(gate: Mapping[str, Any]) -> bool:
    if bool(gate.get("authorized")):
        return True
    if bool(gate.get("projection_only")):
        return False
    blockers = {
        str(reason or "").strip()
        for reason in gate.get("blocking_reasons") or []
        if str(reason or "").strip()
    }
    return bool(blockers) and blockers.issubset(_SUBMISSION_AUDIT_MATERIALIZATION_BLOCKERS)


def create_submission_minimal_package(
    *,
    paper_root: Path,
    publication_profile: str,
    citation_style: str | None = "auto",
    authority_route_context: Mapping[str, Any] | None = None,
    route_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from med_autoscience.controllers.authority_write_route import (
        attach_write_route_gate,
        blocked_authority_write_payload,
        resolve_authority_write_route_context,
    )
    from med_autoscience.controllers.authority_write_route_context import with_study_authority_route_context

    paper_root = paper_root.resolve()
    study_root = paper_authority_delivery_guard.study_root_for_paper_delivery(paper_root=paper_root)
    provided_route_context = authority_route_context or route_context
    write_route_context = with_study_authority_route_context(
        study_root=study_root,
        context=dict(provided_route_context) if provided_route_context is not None else None,
    )
    resolved_route_context, authority_route_gate = resolve_authority_write_route_context(
        action="submission_materialize",
        context=write_route_context,
        default_paths=[paper_root / "submission_minimal", paper_root / "references.bib"],
    )
    if not _can_materialize_submission_audit_package(authority_route_gate):
        return blocked_authority_write_payload(
            gate=authority_route_gate,
            paper_root=str(paper_root),
        )
    workspace_root = workspace_root_from_paper_root(paper_root)
    label_root = delivery_label_root_from_paper_root(paper_root)
    clean_migration_blocker = paper_authority_delivery_guard.pending_clean_migration_blocker(
        study_root=study_root,
    )
    if clean_migration_blocker is not None:
        return {
            **clean_migration_blocker,
            "paper_root": str(paper_root),
            "authority_route_gate": authority_route_gate,
        }
    requested_publication_profile = str(publication_profile or "").strip()
    profile_config = resolve_publication_profile_config(
        publication_profile=requested_publication_profile,
        citation_style=citation_style,
    )
    resolved_publication_profile = profile_config.publication_profile
    target_submission_root = resolve_output_root(
        paper_root=paper_root,
        publication_profile=resolved_publication_profile,
    )

    bundle_manifest = load_json(paper_root / "paper_bundle_manifest.json")
    source_hydration_result = hydrate_submission_package_sources_from_current_body(
        paper_root=paper_root,
        bundle_manifest=bundle_manifest,
    )
    compile_report_path = resolve_compile_report_path(
        workspace_root=workspace_root,
        paper_root=paper_root,
        bundle_manifest=bundle_manifest,
    )
    figure_catalog_path = resolve_relpath(
        workspace_root,
        resolve_bundle_input_path(
            bundle_manifest=bundle_manifest,
            key="figure_catalog_path",
            default_path="paper/figures/figure_catalog.json",
        ),
    )
    filtered_direct_figure_catalog_path = _filter_nested_figure_catalog_to_canonical_main_figures(
        source_root=paper_root,
        paper_root=paper_root,
    )
    if filtered_direct_figure_catalog_path is not None:
        figure_catalog_path = filtered_direct_figure_catalog_path
    table_catalog_path = resolve_relpath(
        workspace_root,
        resolve_bundle_input_path(
            bundle_manifest=bundle_manifest,
            key="table_catalog_path",
            default_path="paper/tables/table_catalog.json",
        ),
    )

    compile_report = load_json(compile_report_path)
    figure_catalog = load_json(figure_catalog_path)
    table_catalog = load_json(table_catalog_path)
    pack_lock_payload = _load_display_pack_lock_payload(paper_root=paper_root)
    pack_lock_path, pack_summary_by_id = (
        pack_lock_payload[0],
        _build_display_pack_summary_by_id(pack_lock_payload[1]),
    ) if pack_lock_payload is not None else (None, {})
    excluded_compiled_source_roots = resolve_submission_compiled_source_excluded_roots(
        paper_root=paper_root,
        workspace_root=workspace_root,
        submission_root=target_submission_root,
        bundle_manifest=bundle_manifest,
        compile_report=compile_report,
    )

    compiled_markdown_path = resolve_compiled_markdown_path(
        workspace_root=workspace_root,
        bundle_manifest=bundle_manifest,
        compile_report=compile_report,
        excluded_roots=excluded_compiled_source_roots,
    )
    input_compiled_pdf_path = resolve_compiled_pdf_path(
        workspace_root=workspace_root,
        bundle_manifest=bundle_manifest,
        compile_report=compile_report,
        excluded_roots=excluded_compiled_source_roots,
        required=False,
    )

    if not compiled_markdown_path.exists():
        raise FileNotFoundError(f"missing compiled markdown: {compiled_markdown_path}")

    compiled_markdown_text = compiled_markdown_path.read_text(encoding="utf-8")
    preserved_compiled_markdown_rel: Path | None = None
    try:
        preserved_compiled_markdown_rel = compiled_markdown_path.relative_to(target_submission_root)
    except ValueError:
        preserved_compiled_markdown_rel = None

    staging_submission_root = create_staging_output_root(target_root=target_submission_root)
    figures_output_dir = staging_submission_root / "figures"
    tables_output_dir = staging_submission_root / "tables"
    try:
        if preserved_compiled_markdown_rel is not None:
            write_text(staging_submission_root / preserved_compiled_markdown_rel, compiled_markdown_text)
        readme_path = staging_submission_root / "README.md"
        output_docx_path = staging_submission_root / "manuscript.docx"
        output_pdf_path = staging_submission_root / "paper.pdf"
        compiled_pdf_path = output_pdf_path

        source_markdown_path = compiled_markdown_path
        docx_source_markdown_path: Path | None = None
        supplementary_source_markdown_path: Path | None = None
        supplementary_output_docx_path: Path | None = None
        supplementary_output_pdf_path: Path | None = None
        supplementary_tables_markdown_path: Path | None = None
        supplementary_figures_markdown_path: Path | None = None
        supplementary_material_fallback_path: Path | None = None
        supplementary_tables_workbook_path: Path | None = None
        supplementary_tables_pdf_path: Path | None = None
        combined_review_source_markdown_path: Path | None = None
        combined_review_docx_source_markdown_path: Path | None = None
        combined_review_docx_path: Path | None = None
        combined_review_pdf_path: Path | None = None
        source_markdown_alias_path: Path | None = None

        if resolved_publication_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
            source_markdown_path = build_general_medical_submission_markdown(
                compiled_markdown_path=compiled_markdown_path,
                submission_root=staging_submission_root,
                compiled_markdown_text=compiled_markdown_text,
            )
            docx_source_markdown_path = build_general_medical_submission_markdown(
                compiled_markdown_path=compiled_markdown_path,
                submission_root=staging_submission_root,
                compiled_markdown_text=compiled_markdown_text,
                output_name="manuscript_submission_docx.md",
                allow_landscape_latex_for_tables=False,
            )
        elif is_frontiers_family_harvard_profile(resolved_publication_profile):
            source_markdown_path = build_frontiers_manuscript_markdown(
                compiled_markdown_path=compiled_markdown_path,
                submission_root=staging_submission_root,
                compiled_markdown_text=compiled_markdown_text,
            )
            supplementary_source_markdown_path = build_frontiers_supplementary_markdown(
                compiled_markdown_path=compiled_markdown_path,
                submission_root=staging_submission_root,
                compiled_markdown_text=compiled_markdown_text,
            )
            supplementary_output_docx_path = staging_submission_root / str(profile_config.supplementary_docx_name)
        if source_markdown_path.name != "manuscript_source.md":
            source_markdown_alias_path = staging_submission_root / "manuscript_source.md"
            if source_markdown_alias_path.resolve() != source_markdown_path.resolve():
                write_submission_source_authority_note(
                    output_path=source_markdown_alias_path,
                    source_markdown_path=source_markdown_path,
                    compiled_markdown_path=compiled_markdown_path,
                    staging_root=staging_submission_root,
                    target_root=target_submission_root,
                    label_root=label_root,
                )
        source_contract_markdown_path = compiled_markdown_path
        if source_markdown_alias_path is not None:
            source_markdown_alias_target_path = remap_staging_path_to_target(
                path=source_markdown_alias_path,
                staging_root=staging_submission_root,
                target_root=target_submission_root,
            )
            if compiled_markdown_path.resolve() == source_markdown_alias_target_path.resolve():
                source_contract_markdown_path = source_markdown_path

        figure_entries: list[dict[str, Any]] = []
        figure_naming_map: dict[str, str] = {}
        seen_figure_ids: set[str] = set()
        for entry in figure_catalog.get("figures", []):
            paper_role = str(entry.get("paper_role") or "").strip().lower()
            display_role = str(entry.get("display_role") or "").strip().lower()
            if paper_role == "supplementary" and display_role.startswith("deferred_"):
                continue
            figure_entry = materialize_submission_figure_entry(
                entry=entry,
                paper_root=paper_root,
                workspace_root=workspace_root,
                label_root=label_root,
                figures_output_dir=figures_output_dir,
                pack_summary_by_id=pack_summary_by_id,
            )
            if figure_entry is None:
                continue
            figure_naming_map[str(figure_entry["figure_id"])] = build_figure_basename(
                str(figure_entry["figure_id"])
            )
            figure_entries.append(figure_entry)
            seen_figure_ids.add(str(figure_entry["figure_id"]))
        for entry in figure_catalog.get("deferred_figures", []):
            figure_id = str(entry.get("figure_id") or "").strip()
            if not figure_id or figure_id in seen_figure_ids:
                continue
            figure_entry = materialize_submission_figure_entry(
                entry=entry,
                paper_root=paper_root,
                workspace_root=workspace_root,
                label_root=label_root,
                figures_output_dir=figures_output_dir,
                pack_summary_by_id=pack_summary_by_id,
            )
            if figure_entry is None:
                continue
            figure_naming_map[str(figure_entry["figure_id"])] = build_figure_basename(
                str(figure_entry["figure_id"])
            )
            figure_entries.append(figure_entry)

        table_entries: list[dict[str, Any]] = []
        table_naming_map: dict[str, str] = {}
        for entry in table_catalog.get("tables", []):
            asset_paths = resolve_table_source_paths(entry)
            if not asset_paths:
                continue
            missing_paths = find_missing_source_paths(
                workspace_root=workspace_root,
                paper_root=paper_root,
                source_paths=asset_paths,
            )
            if missing_paths:
                if is_planned_catalog_entry(entry):
                    continue
                missing_paths_text = ", ".join(str(path) for path in missing_paths)
                raise FileNotFoundError(
                    f"missing submission asset(s) for table `{entry.get('table_id')}`: {missing_paths_text}"
                )
            basename = build_table_basename(str(entry["table_id"]))
            output_paths = copy_with_renamed_targets(
                workspace_root=workspace_root,
                paper_root=paper_root,
                source_paths=asset_paths,
                output_dir=tables_output_dir,
                basename=basename,
                label_root=label_root,
            )
            table_naming_map[str(entry["table_id"])] = basename
            pack_id = _resolve_pack_id(entry, id_field="table_shell_id")
            table_entry = {
                "table_id": entry["table_id"],
                "table_shell_id": entry.get("table_shell_id"),
                "pack_id": pack_id,
                "paper_role": entry.get("paper_role"),
                "title": entry.get("title"),
                "caption": entry.get("caption"),
                "input_schema_id": entry.get("input_schema_id"),
                "qc_profile": entry.get("qc_profile"),
                "qc_result": entry.get("qc_result"),
                "source_paths": asset_paths,
                "output_paths": output_paths,
            }
            _attach_pack_provenance(
                table_entry,
                pack_id=pack_id,
                pack_summary_by_id=pack_summary_by_id,
            )
            table_entries.append(table_entry)

        if resolved_publication_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
            inline_supplementary_fallback_used = False
            supplementary_tables_markdown_path = build_general_medical_inline_supplementary_section_markdown(
                compiled_markdown_path=compiled_markdown_path,
                submission_root=staging_submission_root,
                section_heading="Supplementary Tables",
                output_name="supplementary_tables.md",
                intro_text=(
                    "This file contains supplementary tables preserved from the canonical manuscript source."
                ),
                compiled_markdown_text=compiled_markdown_text,
            )
            inline_supplementary_fallback_used = supplementary_tables_markdown_path is not None
            if supplementary_tables_markdown_path is None:
                supplementary_tables_markdown_path = build_supplementary_tables_markdown(
                    table_entries=table_entries,
                    submission_root=staging_submission_root,
                    label_root=label_root,
                )
            supplementary_figures_markdown_path = build_supplementary_figures_markdown(
                figure_entries=figure_entries,
                submission_root=staging_submission_root,
                label_root=label_root,
            )
            if supplementary_figures_markdown_path is None:
                supplementary_figures_markdown_path = build_general_medical_inline_supplementary_section_markdown(
                    compiled_markdown_path=compiled_markdown_path,
                    submission_root=staging_submission_root,
                    section_heading="Supplementary Figures",
                    output_name="supplementary_figures.md",
                    intro_text=(
                        "This file contains supplementary figures preserved from the canonical manuscript source."
                    ),
                    compiled_markdown_text=compiled_markdown_text,
                )
                inline_supplementary_fallback_used = (
                    inline_supplementary_fallback_used or supplementary_figures_markdown_path is not None
                )
            if supplementary_tables_markdown_path is None and supplementary_figures_markdown_path is None:
                supplementary_material_fallback_path = build_general_medical_inline_supplementary_section_markdown(
                    compiled_markdown_path=compiled_markdown_path,
                    submission_root=staging_submission_root,
                    section_heading="Supplementary Material",
                    output_name="supplementary_material.md",
                    intro_text=(
                        "This file contains supplementary material preserved from the canonical manuscript source."
                    ),
                    compiled_markdown_text=compiled_markdown_text,
                )
            supplementary_tables_workbook_path = build_supplementary_tables_workbook(
                supplementary_tables_markdown_path=supplementary_tables_markdown_path,
                submission_root=staging_submission_root,
            )
            supplementary_tables_pdf_path = build_supplementary_tables_pdf(
                supplementary_tables_markdown_path=supplementary_tables_markdown_path,
                submission_root=staging_submission_root,
            )
            supplementary_source_markdown_path = build_combined_supplementary_markdown(
                supplementary_markdown_paths=[
                    path
                    for path in (
                        supplementary_tables_markdown_path,
                        supplementary_figures_markdown_path,
                        supplementary_material_fallback_path,
                    )
                    if path is not None
                ],
                submission_root=staging_submission_root,
                force_combined_output=(
                    inline_supplementary_fallback_used
                    or supplementary_tables_markdown_path is not None
                ),
            )
            if supplementary_source_markdown_path is not None:
                supplementary_output_pdf_path = staging_submission_root / f"{supplementary_source_markdown_path.stem}.pdf"
                combined_review_source_markdown_path = build_combined_review_markdown(
                    manuscript_markdown_path=source_markdown_path,
                    supplementary_markdown_path=supplementary_source_markdown_path,
                    submission_root=staging_submission_root,
                )
                combined_review_docx_source_markdown_path = build_combined_review_markdown(
                    manuscript_markdown_path=docx_source_markdown_path or source_markdown_path,
                    supplementary_markdown_path=supplementary_source_markdown_path,
                    submission_root=staging_submission_root,
                    output_name="manuscript_with_supplementary_docx.md",
                )
                combined_review_docx_path = staging_submission_root / "manuscript_with_supplementary.docx"
                combined_review_pdf_path = staging_submission_root / "paper_with_supplementary.pdf"

        references_manifest, references_source_path, references_coverage = materialize_and_validate_submission_references(
            paper_root=paper_root,
            submission_root=staging_submission_root,
            workspace_root=workspace_root,
            label_root=label_root,
            source_markdown_path=source_markdown_path,
        )

        export_docx(
            compiled_markdown_path=docx_source_markdown_path or source_markdown_path,
            paper_root=paper_root,
            output_docx_path=output_docx_path,
            csl_path=profile_config.csl_path,
            reference_doc_path=profile_config.reference_doc_path,
        )
        export_pdf(
            compiled_markdown_path=source_markdown_path,
            paper_root=paper_root,
            output_pdf_path=output_pdf_path,
            csl_path=profile_config.csl_path,
        )
        if supplementary_source_markdown_path is not None and supplementary_output_docx_path is not None:
            export_docx(
                compiled_markdown_path=supplementary_source_markdown_path,
                paper_root=paper_root,
                output_docx_path=supplementary_output_docx_path,
                csl_path=profile_config.csl_path,
                reference_doc_path=profile_config.supplementary_reference_doc_path,
            )
        if supplementary_source_markdown_path is not None and supplementary_output_pdf_path is not None:
            supplementary_pdf_component_paths: list[Path] = []
            if supplementary_tables_pdf_path is not None:
                supplementary_pdf_component_paths.append(supplementary_tables_pdf_path)
                if supplementary_figures_markdown_path is not None:
                    supplementary_figures_pdf_path = staging_submission_root / "supplementary_figures.pdf"
                    export_pdf(
                        compiled_markdown_path=supplementary_figures_markdown_path,
                        paper_root=paper_root,
                        output_pdf_path=supplementary_figures_pdf_path,
                        csl_path=profile_config.csl_path,
                    )
                    supplementary_pdf_component_paths.append(supplementary_figures_pdf_path)
                if supplementary_material_fallback_path is not None:
                    supplementary_fallback_pdf_path = staging_submission_root / "supplementary_material_fallback.pdf"
                    export_pdf(
                        compiled_markdown_path=supplementary_material_fallback_path,
                        paper_root=paper_root,
                        output_pdf_path=supplementary_fallback_pdf_path,
                        csl_path=profile_config.csl_path,
                    )
                    supplementary_pdf_component_paths.append(supplementary_fallback_pdf_path)
                write_pdf_bundle(
                    source_pdf_paths=supplementary_pdf_component_paths,
                    output_pdf_path=supplementary_output_pdf_path,
                )
            else:
                export_pdf(
                    compiled_markdown_path=supplementary_source_markdown_path,
                    paper_root=paper_root,
                    output_pdf_path=supplementary_output_pdf_path,
                    csl_path=profile_config.csl_path,
                )
        if combined_review_source_markdown_path is not None and combined_review_docx_path is not None:
            export_docx(
                compiled_markdown_path=combined_review_docx_source_markdown_path or combined_review_source_markdown_path,
                paper_root=paper_root,
                output_docx_path=combined_review_docx_path,
                csl_path=profile_config.csl_path,
                reference_doc_path=profile_config.reference_doc_path,
            )
        if supplementary_output_pdf_path is not None and combined_review_pdf_path is not None:
            write_combined_review_pdf(
                manuscript_pdf_path=output_pdf_path,
                supplementary_pdf_path=supplementary_output_pdf_path,
                output_pdf_path=combined_review_pdf_path,
            )
        pruned_legacy_paths = prune_legacy_paper_surface_exports(
            paper_root=paper_root,
            figure_catalog=figure_catalog,
            table_catalog=table_catalog,
        )
        manuscript_surface_qc = build_submission_manuscript_surface_qc(
            publication_profile=resolved_publication_profile,
            source_markdown_path=source_markdown_path,
            docx_path=output_docx_path,
            pdf_path=output_pdf_path,
            expected_main_figure_count=count_main_text_figures_in_catalog(figure_catalog),
        )
        manuscript_surface_qc = attach_submission_source_authority_note_qc(
            manuscript_surface_qc,
            authority_note_path=source_markdown_alias_path,
        )
        source_contract = build_submission_minimal_source_contract(
            paper_root=paper_root,
            workspace_root=workspace_root,
            compile_report_path=compile_report_path,
            compiled_markdown_path=source_contract_markdown_path,
            figure_catalog_path=figure_catalog_path,
            table_catalog_path=table_catalog_path,
            figure_catalog=figure_catalog,
            table_catalog=table_catalog,
            pack_lock_path=pack_lock_path,
            references_source_path=references_source_path,
        )
        source_markdown_metadata, _ = split_front_matter(source_markdown_path.read_text(encoding="utf-8"))
        manifest: dict[str, Any] = {
            "schema_version": 1,
            "generated_at": utc_now(),
            "publication_profile": resolved_publication_profile,
            "citation_style": profile_config.citation_style,
            "output_root": relpath_from_workspace(target_submission_root, label_root),
            "delivery_layout": build_package_layout_block(
                package_root=target_submission_root,
                workspace_root=label_root,
                package_role="controller_authorized_package_source",
                source_package_root=target_submission_root,
                legacy_input_status="v2_generated",
            ),
            "manuscript": {
                "source_markdown_path": relpath_from_workspace(
                    remap_staging_path_to_target(
                        path=source_markdown_path,
                        staging_root=staging_submission_root,
                        target_root=target_submission_root,
                    ),
                    label_root,
                ),
                "pdf_path": relpath_from_workspace(target_submission_root / "paper.pdf", label_root),
                "docx_path": relpath_from_workspace(target_submission_root / "manuscript.docx", label_root),
                "csl_path": str(profile_config.csl_path.resolve()),
                "pdf_rendering": default_pdf_rendering_profile(),
                "surface_qc": manuscript_surface_qc,
            },
            "naming_map": {
                "figures": figure_naming_map,
                "tables": table_naming_map,
            },
            "figures": [
                {
                    **entry,
                    "output_paths": [
                        remap_staging_relpath_to_target(
                            relpath=path,
                            workspace_root=label_root,
                            staging_root=staging_submission_root,
                            target_root=target_submission_root,
                        )
                        for path in entry["output_paths"]
                    ],
                }
                for entry in figure_entries
            ],
            "tables": [
                {
                    **entry,
                    "output_paths": [
                        remap_staging_relpath_to_target(
                            relpath=path,
                            workspace_root=label_root,
                            staging_root=staging_submission_root,
                            target_root=target_submission_root,
                        )
                        for path in entry["output_paths"]
                    ],
                }
                for entry in table_entries
            ],
            "front_matter_placeholders": build_front_matter_placeholders(
                metadata=source_markdown_metadata,
            ),
            "source_signature": source_contract["source_signature"],
            "source_contract": source_contract,
            "source_hydration": source_hydration_result,
        }
        if input_compiled_pdf_path.exists():
            manifest["input_compiled_pdf_path"] = relpath_from_workspace(input_compiled_pdf_path, label_root)
        else:
            manifest["input_compiled_pdf_path"] = None
            manifest["input_compiled_pdf_status"] = "not_required_rebuilt_from_submission_source"
        if references_manifest is not None:
            manifest["references"] = {
                **references_manifest,
                "output_path": remap_staging_relpath_to_target(
                    relpath=str(references_manifest["output_path"]),
                    workspace_root=label_root,
                    staging_root=staging_submission_root,
                    target_root=target_submission_root,
                ),
                "coverage": references_coverage,
            }
        if source_markdown_alias_path is not None:
            manifest["manuscript"]["source_markdown_alias_path"] = relpath_from_workspace(
                remap_staging_path_to_target(
                    path=source_markdown_alias_path,
                    staging_root=staging_submission_root,
                    target_root=target_submission_root,
                ),
                label_root,
            )
            manifest["manuscript"]["source_markdown_alias_role"] = "authority_note"
        if pack_lock_path is not None:
            manifest["display_pack_lock_path"] = relpath_from_workspace(pack_lock_path, label_root)
            manifest["enabled_display_packs"] = list(pack_summary_by_id.values())
            publication_figure_quality_refs = pack_lock_payload[1].get("publication_figure_quality_refs")
            if publication_figure_quality_refs is not None:
                if not isinstance(publication_figure_quality_refs, dict):
                    raise ValueError("display_pack_lock.json publication_figure_quality_refs must be an object")
                manifest["publication_figure_quality_refs"] = publication_figure_quality_refs
        if pruned_legacy_paths:
            manifest["pruned_legacy_paths"] = pruned_legacy_paths
        if requested_publication_profile != resolved_publication_profile:
            manifest["requested_publication_profile"] = requested_publication_profile
        journal_target = _journal_target_payload(profile_config)
        if journal_target is not None:
            manifest["journal_target"] = journal_target
        supplementary_material = supplementary_material_payload(
            supplementary_source_markdown_path=supplementary_source_markdown_path,
            supplementary_output_docx_path=supplementary_output_docx_path,
            supplementary_output_pdf_path=supplementary_output_pdf_path,
            supplementary_tables_workbook_path=supplementary_tables_workbook_path,
            supplementary_tables_pdf_path=supplementary_tables_pdf_path,
            combined_review_docx_path=combined_review_docx_path,
            combined_review_pdf_path=combined_review_pdf_path,
            profile_config=profile_config,
            staging_submission_root=staging_submission_root,
            target_submission_root=target_submission_root,
            workspace_root=label_root,
        )
        if supplementary_material is not None:
            manifest["supplementary_material"] = supplementary_material

        manifest["authority_route_gate"] = authority_route_gate
        if not bool(authority_route_gate.get("authorized")):
            manifest["submission_materialization_status"] = {
                "package_role": "audit_source_package",
                "can_submit": False,
                "quality_gate_status": "blocked",
                "known_blockers": list(authority_route_gate.get("blocking_reasons") or []),
            }
        write_text(
            readme_path,
            build_submission_minimal_readme(publication_profile=resolved_publication_profile),
        )
        manifest["readme_path"] = relpath_from_workspace(target_submission_root / "README.md", label_root)
        submission_manifest_path = layout_submission_manifest_path(staging_submission_root)
        dump_json(submission_manifest_path, manifest)
        evidence_ledger_source = paper_root / "evidence_ledger.json"
        if evidence_ledger_source.exists():
            shutil.copy2(evidence_ledger_source, audit_path(staging_submission_root, "evidence_ledger"))
        replace_directory_atomically(
            staging_root=staging_submission_root,
            target_root=target_submission_root,
        )
    except Exception:
        shutil.rmtree(staging_submission_root, ignore_errors=True)
        raise

    submission_manifest_path = layout_submission_manifest_path(target_submission_root)
    post_replace_contract_markdown_path = remap_staging_path_to_target(
        path=source_contract_markdown_path,
        staging_root=staging_submission_root,
        target_root=target_submission_root,
    )
    refreshed_source_contract = build_submission_minimal_source_contract(
        paper_root=paper_root,
        workspace_root=workspace_root,
        compile_report_path=compile_report_path,
        compiled_markdown_path=post_replace_contract_markdown_path,
        figure_catalog_path=figure_catalog_path,
        table_catalog_path=table_catalog_path,
        figure_catalog=figure_catalog,
        table_catalog=table_catalog,
        pack_lock_path=pack_lock_path,
    )
    apply_controller_authorized_delivery_layout(
        manifest=manifest,
        target_submission_root=target_submission_root,
        workspace_root=label_root,
        source_contract=refreshed_source_contract,
    )
    dump_json(submission_manifest_path, manifest)
    write_submission_reproducibility_documents(
        target_submission_root=target_submission_root,
        source_contract=refreshed_source_contract,
    )
    write_submission_lineage_reproducibility_bundle(
        target_submission_root=target_submission_root,
        source_contract=refreshed_source_contract,
    )
    archived_surface_roots = materialize_archived_reference_only_submission_surface_manifests(
        paper_root,
        active_manifest_path=submission_manifest_path,
    )
    if archived_surface_roots:
        manifest["archived_reference_only_submission_surface_roots"] = [
            relpath_from_workspace(surface_root, label_root) for surface_root in archived_surface_roots
        ]
        dump_json(submission_manifest_path, manifest)
    from med_autoscience.controllers import study_delivery_sync

    delivery_sync_result: dict[str, Any] | None = None
    post_materialization_sync_result: dict[str, Any] | None = None
    if study_delivery_sync.can_sync_study_delivery(paper_root=paper_root):
        delivery_sync_result = _sync_study_delivery_with_route_context(
            paper_root=paper_root,
            stage="submission_minimal",
            publication_profile=resolved_publication_profile,
            authority_route_context=resolved_route_context,
        )
        post_materialization_sync_result = replay_post_submission_minimal_sync(
            paper_root=paper_root,
            publication_profile=resolved_publication_profile,
            authority_route_context=resolved_route_context,
        )
        refreshed_source_contract = build_submission_minimal_source_contract(
            paper_root=paper_root,
            workspace_root=workspace_root,
            compile_report_path=compile_report_path,
            compiled_markdown_path=post_replace_contract_markdown_path,
            figure_catalog_path=figure_catalog_path,
            table_catalog_path=table_catalog_path,
            figure_catalog=figure_catalog,
            table_catalog=table_catalog,
            pack_lock_path=pack_lock_path,
        )
        apply_controller_authorized_delivery_layout(
            manifest=manifest,
            target_submission_root=target_submission_root,
            workspace_root=label_root,
            source_contract=refreshed_source_contract,
        )
        dump_json(submission_manifest_path, manifest)
        write_submission_reproducibility_documents(
            target_submission_root=target_submission_root,
            source_contract=refreshed_source_contract,
        )
        write_submission_lineage_reproducibility_bundle(
            target_submission_root=target_submission_root,
            source_contract=refreshed_source_contract,
        )
    if delivery_sync_result is not None or post_materialization_sync_result is not None:
        result = dict(manifest)
        if delivery_sync_result is not None:
            result["delivery_sync"] = delivery_sync_result
        if post_materialization_sync_result is not None:
            result["post_materialization_sync"] = post_materialization_sync_result
        return attach_write_route_gate(result, authority_route_gate)
    return attach_write_route_gate(manifest, authority_route_gate)


def _sync_study_delivery_with_route_context(
    *,
    paper_root: Path,
    stage: str,
    publication_profile: str,
    authority_route_context: Mapping[str, Any],
) -> dict[str, Any]:
    from med_autoscience.controllers import study_delivery_sync

    signature = inspect.signature(study_delivery_sync.sync_study_delivery)
    if "authority_route_context" in signature.parameters:
        return study_delivery_sync.sync_study_delivery(
            paper_root=paper_root,
            stage=stage,
            publication_profile=publication_profile,
            authority_route_context=authority_route_context,
        )
    return study_delivery_sync.sync_study_delivery(
        paper_root=paper_root,
        stage=stage,
        publication_profile=publication_profile,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a submission-minimal manuscript package.")
    parser.add_argument("--paper-root", type=Path, required=True)
    parser.add_argument("--publication-profile", default="general_medical_journal")
    parser.add_argument("--citation-style", default="auto")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    create_submission_minimal_package(
        paper_root=args.paper_root,
        publication_profile=args.publication_profile,
        citation_style=args.citation_style,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
