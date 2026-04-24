from .shared import *

def describe_submission_minimal_authority(
    *,
    paper_root: Path,
    publication_profile: str = GENERAL_MEDICAL_JOURNAL_PROFILE,
) -> dict[str, Any]:
    resolved_paper_root = paper_root.expanduser().resolve()
    workspace_root = workspace_root_from_paper_root(resolved_paper_root)
    normalized_publication_profile = normalize_publication_profile(publication_profile)
    submission_root = resolve_output_root(
        paper_root=resolved_paper_root,
        publication_profile=normalized_publication_profile,
    )
    submission_manifest_path = submission_root / "submission_manifest.json"
    if not submission_manifest_path.exists():
        return {
            "applicable": True,
            "status": "missing",
            "stale_reason": "submission_manifest_missing",
            "submission_root": str(submission_root),
            "submission_manifest_path": None,
            "source_signature": None,
            "recorded_source_signature": None,
            "missing_source_paths": [],
        }

    try:
        submission_manifest = load_json(submission_manifest_path)
    except json.JSONDecodeError:
        return {
            "applicable": True,
            "status": "invalid",
            "stale_reason": "submission_manifest_invalid",
            "submission_root": str(submission_root),
            "submission_manifest_path": str(submission_manifest_path),
            "source_signature": None,
            "recorded_source_signature": None,
            "missing_source_paths": [],
        }
    if not isinstance(submission_manifest, dict):
        return {
            "applicable": True,
            "status": "invalid",
            "stale_reason": "submission_manifest_invalid",
            "submission_root": str(submission_root),
            "submission_manifest_path": str(submission_manifest_path),
            "source_signature": None,
            "recorded_source_signature": None,
            "missing_source_paths": [],
        }

    bundle_manifest_path = resolved_paper_root / "paper_bundle_manifest.json"
    try:
        bundle_manifest = load_json(bundle_manifest_path)
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
        excluded_compiled_source_roots = resolve_submission_compiled_source_excluded_roots(
            paper_root=resolved_paper_root,
            workspace_root=workspace_root,
            submission_root=submission_root,
            bundle_manifest=bundle_manifest,
            compile_report=compile_report,
        )
        compiled_markdown_path = resolve_compiled_markdown_path(
            workspace_root=workspace_root,
            bundle_manifest=bundle_manifest,
            compile_report=compile_report,
            excluded_roots=excluded_compiled_source_roots,
        )
        pack_lock_payload = _load_display_pack_lock_payload(paper_root=resolved_paper_root)
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return {
            "applicable": True,
            "status": "stale_source_missing",
            "stale_reason": "submission_source_inputs_missing",
            "submission_root": str(submission_root),
            "submission_manifest_path": str(submission_manifest_path),
            "source_signature": None,
            "recorded_source_signature": None,
            "missing_source_paths": [],
        }

    source_contract = build_submission_minimal_source_contract(
        paper_root=resolved_paper_root,
        workspace_root=workspace_root,
        compile_report_path=compile_report_path,
        compiled_markdown_path=compiled_markdown_path,
        figure_catalog_path=figure_catalog_path,
        table_catalog_path=table_catalog_path,
        figure_catalog=figure_catalog if isinstance(figure_catalog, dict) else {},
        table_catalog=table_catalog if isinstance(table_catalog, dict) else {},
        pack_lock_path=pack_lock_payload[0] if pack_lock_payload is not None else None,
    )
    recorded_contract = (
        dict(submission_manifest.get("source_contract") or {})
        if isinstance(submission_manifest.get("source_contract"), dict)
        else {}
    )
    recorded_source_signature = _first_nonempty_string(
        submission_manifest.get("source_signature"),
        recorded_contract.get("source_signature"),
    )
    if source_contract["missing_source_paths"]:
        status = "stale_source_missing"
        stale_reason = "submission_source_inputs_missing"
    elif recorded_source_signature:
        status = "current" if recorded_source_signature == source_contract["source_signature"] else "stale_source_changed"
        stale_reason = None if status == "current" else "submission_source_signature_mismatch"
    else:
        manifest_mtime_ns = submission_manifest_path.stat().st_mtime_ns
        status = (
            "current"
            if manifest_mtime_ns >= int(source_contract["latest_source_mtime_ns"])
            else "stale_source_changed"
        )
        stale_reason = None if status == "current" else "submission_source_newer_than_manifest"
    return {
        "applicable": True,
        "status": status,
        "stale_reason": stale_reason,
        "submission_root": str(submission_root),
        "submission_manifest_path": str(submission_manifest_path),
        "source_signature": source_contract["source_signature"],
        "recorded_source_signature": recorded_source_signature,
        "missing_source_paths": list(source_contract["missing_source_paths"]),
        "latest_source_mtime_ns": int(source_contract["latest_source_mtime_ns"]),
    }


