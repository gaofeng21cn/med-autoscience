from .shared import *
from .authority import *
from .markdown_surface import *
from .post_materialization_sync import replay_post_submission_minimal_sync
from .profile_builders import *

def create_submission_minimal_package(
    *,
    paper_root: Path,
    publication_profile: str,
    citation_style: str | None = "auto",
) -> dict[str, Any]:
    paper_root = paper_root.resolve()
    workspace_root = workspace_root_from_paper_root(paper_root)
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
    compile_report_path = resolve_relpath(
        workspace_root,
        resolve_bundle_input_path(
            bundle_manifest=bundle_manifest,
            key="compile_report_path",
        ),
    )
    figure_catalog_path = resolve_relpath(
        workspace_root,
        resolve_bundle_input_path(
            bundle_manifest=bundle_manifest,
            key="figure_catalog_path",
            fallback="paper/figures/figure_catalog.json",
        ),
    )
    table_catalog_path = resolve_relpath(
        workspace_root,
        resolve_bundle_input_path(
            bundle_manifest=bundle_manifest,
            key="table_catalog_path",
            fallback="paper/tables/table_catalog.json",
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
    compiled_pdf_path = resolve_compiled_pdf_path(
        workspace_root=workspace_root,
        bundle_manifest=bundle_manifest,
        compile_report=compile_report,
        excluded_roots=excluded_compiled_source_roots,
    )

    if not compiled_markdown_path.exists():
        raise FileNotFoundError(f"missing compiled markdown: {compiled_markdown_path}")
    if not compiled_pdf_path.exists():
        raise FileNotFoundError(f"missing compiled pdf: {compiled_pdf_path}")

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

        source_markdown_path = compiled_markdown_path
        supplementary_source_markdown_path: Path | None = None
        supplementary_output_docx_path: Path | None = None
        source_markdown_alias_path: Path | None = None

        if resolved_publication_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
            source_markdown_path = build_general_medical_submission_markdown(
                compiled_markdown_path=compiled_markdown_path,
                submission_root=staging_submission_root,
                compiled_markdown_text=compiled_markdown_text,
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
            if (
                not source_markdown_alias_path.exists()
                and source_markdown_alias_path.resolve() != source_markdown_path.resolve()
            ):
                shutil.copy2(source_markdown_path, source_markdown_alias_path)

        figure_entries: list[dict[str, Any]] = []
        figure_naming_map: dict[str, str] = {}
        for entry in figure_catalog.get("figures", []):
            export_paths = resolve_figure_source_paths(entry)
            if not export_paths:
                continue
            existing_export_paths = filter_existing_source_paths(
                workspace_root=workspace_root,
                paper_root=paper_root,
                source_paths=export_paths,
            )
            if existing_export_paths:
                export_paths = existing_export_paths
            missing_paths = find_missing_source_paths(
                workspace_root=workspace_root,
                paper_root=paper_root,
                source_paths=export_paths,
            )
            if missing_paths:
                if is_planned_catalog_entry(entry):
                    continue
                missing_paths_text = ", ".join(str(path) for path in missing_paths)
                raise FileNotFoundError(
                    f"missing submission asset(s) for figure `{entry.get('figure_id')}`: {missing_paths_text}"
                )
            basename = build_figure_basename(str(entry["figure_id"]))
            output_paths = copy_with_renamed_targets(
                workspace_root=workspace_root,
                paper_root=paper_root,
                source_paths=export_paths,
                output_dir=figures_output_dir,
                basename=basename,
            )
            figure_naming_map[str(entry["figure_id"])] = basename
            pack_id = _resolve_pack_id(entry, id_field="template_id")
            figure_entry = {
                "figure_id": entry["figure_id"],
                "template_id": entry.get("template_id"),
                "pack_id": pack_id,
                "renderer_family": entry.get("renderer_family"),
                "paper_role": entry.get("paper_role"),
                "input_schema_id": entry.get("input_schema_id"),
                "qc_profile": entry.get("qc_profile"),
                "qc_result": entry.get("qc_result"),
                "source_paths": export_paths,
                "output_paths": output_paths,
            }
            _attach_pack_provenance(
                figure_entry,
                pack_id=pack_id,
                pack_summary_by_id=pack_summary_by_id,
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
            )
            table_naming_map[str(entry["table_id"])] = basename
            pack_id = _resolve_pack_id(entry, id_field="table_shell_id")
            table_entry = {
                "table_id": entry["table_id"],
                "table_shell_id": entry.get("table_shell_id"),
                "pack_id": pack_id,
                "paper_role": entry.get("paper_role"),
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

        export_docx(
            compiled_markdown_path=source_markdown_path,
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
        references_manifest = materialize_submission_references(
            paper_root=paper_root,
            submission_root=staging_submission_root,
            workspace_root=workspace_root,
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
        source_contract = build_submission_minimal_source_contract(
            paper_root=paper_root,
            workspace_root=workspace_root,
            compile_report_path=compile_report_path,
            compiled_markdown_path=compiled_markdown_path,
            figure_catalog_path=figure_catalog_path,
            table_catalog_path=table_catalog_path,
            figure_catalog=figure_catalog,
            table_catalog=table_catalog,
            pack_lock_path=pack_lock_path,
        )
        source_markdown_metadata, _ = split_front_matter(source_markdown_path.read_text(encoding="utf-8"))
        manifest: dict[str, Any] = {
            "schema_version": 1,
            "generated_at": utc_now(),
            "publication_profile": resolved_publication_profile,
            "citation_style": profile_config.citation_style,
            "output_root": relpath_from_workspace(target_submission_root, workspace_root),
            "manuscript": {
                "source_markdown_path": relpath_from_workspace(
                    remap_staging_path_to_target(
                        path=source_markdown_path,
                        staging_root=staging_submission_root,
                        target_root=target_submission_root,
                    ),
                    workspace_root,
                ),
                "pdf_path": relpath_from_workspace(target_submission_root / "paper.pdf", workspace_root),
                "docx_path": relpath_from_workspace(target_submission_root / "manuscript.docx", workspace_root),
                "csl_path": str(profile_config.csl_path.resolve()),
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
                            workspace_root=workspace_root,
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
                            workspace_root=workspace_root,
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
        }
        if references_manifest is not None:
            manifest["references"] = {
                **references_manifest,
                "output_path": remap_staging_relpath_to_target(
                    relpath=str(references_manifest["output_path"]),
                    workspace_root=workspace_root,
                    staging_root=staging_submission_root,
                    target_root=target_submission_root,
                ),
            }
        if source_markdown_alias_path is not None:
            manifest["manuscript"]["source_markdown_alias_path"] = relpath_from_workspace(
                remap_staging_path_to_target(
                    path=source_markdown_alias_path,
                    staging_root=staging_submission_root,
                    target_root=target_submission_root,
                ),
                workspace_root,
            )
        if pack_lock_path is not None:
            manifest["display_pack_lock_path"] = relpath_from_workspace(pack_lock_path, workspace_root)
            manifest["enabled_display_packs"] = list(pack_summary_by_id.values())
        if pruned_legacy_paths:
            manifest["pruned_legacy_paths"] = pruned_legacy_paths
        if requested_publication_profile != resolved_publication_profile:
            manifest["requested_publication_profile"] = requested_publication_profile
        if profile_config.reference_doc_path is not None:
            journal_target = {
                "reference_doc_path": str(profile_config.reference_doc_path.resolve()),
            }
            if profile_config.journal_name is not None:
                journal_target["journal_name"] = profile_config.journal_name
            if profile_config.journal_family is not None:
                journal_target["journal_family"] = profile_config.journal_family
            if profile_config.reference_style_family is not None:
                journal_target["reference_style_family"] = profile_config.reference_style_family
            manifest["journal_target"] = journal_target
        if supplementary_source_markdown_path is not None and supplementary_output_docx_path is not None:
            manifest["supplementary_material"] = {
                "source_markdown_path": relpath_from_workspace(
                    remap_staging_path_to_target(
                        path=supplementary_source_markdown_path,
                        staging_root=staging_submission_root,
                        target_root=target_submission_root,
                    ),
                    workspace_root,
                ),
                "docx_path": relpath_from_workspace(
                    remap_staging_path_to_target(
                        path=supplementary_output_docx_path,
                        staging_root=staging_submission_root,
                        target_root=target_submission_root,
                    ),
                    workspace_root,
                ),
                "reference_doc_path": str(profile_config.supplementary_reference_doc_path.resolve()),
            }

        write_text(
            readme_path,
            build_submission_minimal_readme(publication_profile=resolved_publication_profile),
        )
        manifest["readme_path"] = relpath_from_workspace(target_submission_root / "README.md", workspace_root)
        submission_manifest_path = staging_submission_root / "submission_manifest.json"
        dump_json(submission_manifest_path, manifest)
        replace_directory_atomically(
            staging_root=staging_submission_root,
            target_root=target_submission_root,
        )
    except Exception:
        shutil.rmtree(staging_submission_root, ignore_errors=True)
        raise

    submission_manifest_path = target_submission_root / "submission_manifest.json"
    archived_surface_roots = materialize_archived_reference_only_submission_surface_manifests(
        paper_root,
        active_manifest_path=submission_manifest_path,
    )
    if archived_surface_roots:
        manifest["archived_reference_only_submission_surface_roots"] = [
            relpath_from_workspace(surface_root, workspace_root) for surface_root in archived_surface_roots
        ]
        dump_json(submission_manifest_path, manifest)
    delivery_sync_result: dict[str, Any] | None = None
    post_materialization_sync_result: dict[str, Any] | None = None
    if study_delivery_sync.can_sync_study_delivery(paper_root=paper_root):
        delivery_sync_result = study_delivery_sync.sync_study_delivery(
            paper_root=paper_root,
            stage="submission_minimal",
            publication_profile=resolved_publication_profile,
        )
        post_materialization_sync_result = replay_post_submission_minimal_sync(paper_root=paper_root)
    if delivery_sync_result is not None or post_materialization_sync_result is not None:
        result = dict(manifest)
        if delivery_sync_result is not None:
            result["delivery_sync"] = delivery_sync_result
        if post_materialization_sync_result is not None:
            result["post_materialization_sync"] = post_materialization_sync_result
        return result
    return manifest


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
