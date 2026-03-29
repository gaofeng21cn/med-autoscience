from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
from typing import Any

from med_autoscience.controllers import study_delivery_sync


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def relpath_from_workspace(path: Path, workspace_root: Path) -> str:
    return path.resolve().relative_to(workspace_root.resolve()).as_posix()


def workspace_root_from_paper_root(paper_root: Path) -> Path:
    return paper_root.resolve().parent


def resolve_relpath(workspace_root: Path, value: str) -> Path:
    return workspace_root / value


def default_ama_csl_path() -> Path:
    return Path(__file__).resolve().parents[1] / "styles" / "american-medical-association.csl"


def build_figure_basename(figure_id: str) -> str:
    if figure_id.startswith("FS"):
        return f"SupplementaryFigureS{figure_id[2:]}"
    if figure_id.startswith("F"):
        return f"Figure{figure_id[1:]}"
    return figure_id


def build_table_basename(table_id: str) -> str:
    if table_id.startswith("TA"):
        return f"AppendixTable{table_id[2:]}"
    if table_id.startswith("T"):
        return f"Table{table_id[1:]}"
    return table_id


def copy_with_renamed_targets(
    *,
    workspace_root: Path,
    source_paths: list[str],
    output_dir: Path,
    basename: str,
) -> list[str]:
    output_relpaths: list[str] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for source_rel in source_paths:
        source_path = resolve_relpath(workspace_root, source_rel)
        if not source_path.exists():
            raise FileNotFoundError(f"missing submission asset: {source_path}")
        suffix = source_path.suffix
        target_path = output_dir / f"{basename}{suffix}"
        shutil.copy2(source_path, target_path)
        output_relpaths.append(relpath_from_workspace(target_path, workspace_root))
    return output_relpaths


def export_docx(
    *,
    compiled_markdown_path: Path,
    paper_root: Path,
    output_docx_path: Path,
    csl_path: Path,
) -> None:
    output_docx_path.parent.mkdir(parents=True, exist_ok=True)
    resource_path = os.path.relpath(paper_root.resolve(), compiled_markdown_path.parent.resolve())
    subprocess.run(
        [
            "pandoc",
            compiled_markdown_path.name,
            "--citeproc",
            "--csl",
            str(csl_path.resolve()),
            "--resource-path",
            resource_path,
            "-o",
            os.path.relpath(output_docx_path.resolve(), compiled_markdown_path.parent.resolve()),
        ],
        cwd=compiled_markdown_path.parent,
        check=True,
    )


def create_submission_minimal_package(
    *,
    paper_root: Path,
    publication_profile: str,
    citation_style: str = "AMA",
) -> dict[str, Any]:
    paper_root = paper_root.resolve()
    workspace_root = workspace_root_from_paper_root(paper_root)
    submission_root = paper_root / "submission_minimal"
    figures_output_dir = submission_root / "figures"
    tables_output_dir = submission_root / "tables"
    csl_path = default_ama_csl_path()
    if citation_style != "AMA":
        raise ValueError(f"unsupported citation style: {citation_style}")
    if not csl_path.exists():
        raise FileNotFoundError(f"missing AMA CSL file: {csl_path}")

    bundle_manifest = load_json(paper_root / "paper_bundle_manifest.json")
    compile_report_path = resolve_relpath(workspace_root, bundle_manifest["bundle_inputs"]["compile_report_path"])
    figure_catalog_path = resolve_relpath(workspace_root, bundle_manifest["bundle_inputs"]["figure_catalog_path"])
    table_catalog_path = resolve_relpath(workspace_root, bundle_manifest["bundle_inputs"]["table_catalog_path"])

    compile_report = load_json(compile_report_path)
    figure_catalog = load_json(figure_catalog_path)
    table_catalog = load_json(table_catalog_path)

    compiled_markdown_path = resolve_relpath(workspace_root, compile_report["source_markdown"])
    compiled_pdf_path = resolve_relpath(workspace_root, compile_report["output_pdf"])

    if not compiled_markdown_path.exists():
        raise FileNotFoundError(f"missing compiled markdown: {compiled_markdown_path}")
    if not compiled_pdf_path.exists():
        raise FileNotFoundError(f"missing compiled pdf: {compiled_pdf_path}")

    submission_root.mkdir(parents=True, exist_ok=True)
    output_docx_path = submission_root / "manuscript.docx"
    output_pdf_path = submission_root / "paper.pdf"
    shutil.copy2(compiled_pdf_path, output_pdf_path)
    export_docx(
        compiled_markdown_path=compiled_markdown_path,
        paper_root=paper_root,
        output_docx_path=output_docx_path,
        csl_path=csl_path,
    )

    figure_entries: list[dict[str, Any]] = []
    figure_naming_map: dict[str, str] = {}
    for entry in figure_catalog.get("figures", []):
        export_paths = list(entry.get("export_paths") or [])
        if not export_paths:
            continue
        basename = build_figure_basename(str(entry["figure_id"]))
        output_paths = copy_with_renamed_targets(
            workspace_root=workspace_root,
            source_paths=export_paths,
            output_dir=figures_output_dir,
            basename=basename,
        )
        figure_naming_map[str(entry["figure_id"])] = basename
        figure_entries.append(
            {
                "figure_id": entry["figure_id"],
                "paper_role": entry.get("paper_role"),
                "source_paths": export_paths,
                "output_paths": output_paths,
            }
        )

    table_entries: list[dict[str, Any]] = []
    table_naming_map: dict[str, str] = {}
    for entry in table_catalog.get("tables", []):
        asset_paths = list(entry.get("asset_paths") or [])
        if not asset_paths:
            continue
        basename = build_table_basename(str(entry["table_id"]))
        output_paths = copy_with_renamed_targets(
            workspace_root=workspace_root,
            source_paths=asset_paths,
            output_dir=tables_output_dir,
            basename=basename,
        )
        table_naming_map[str(entry["table_id"])] = basename
        table_entries.append(
            {
                "table_id": entry["table_id"],
                "paper_role": entry.get("paper_role"),
                "source_paths": asset_paths,
                "output_paths": output_paths,
            }
        )

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "publication_profile": publication_profile,
        "citation_style": citation_style,
        "output_root": str(submission_root),
        "manuscript": {
            "source_markdown_path": relpath_from_workspace(compiled_markdown_path, workspace_root),
            "pdf_path": relpath_from_workspace(output_pdf_path, workspace_root),
            "docx_path": relpath_from_workspace(output_docx_path, workspace_root),
            "csl_path": str(csl_path.resolve()),
        },
        "naming_map": {
            "figures": figure_naming_map,
            "tables": table_naming_map,
        },
        "figures": figure_entries,
        "tables": table_entries,
    }
    dump_json(submission_root / "submission_manifest.json", manifest)
    if study_delivery_sync.can_sync_study_delivery(paper_root=paper_root):
        study_delivery_sync.sync_study_delivery(
            paper_root=paper_root,
            stage="submission_minimal",
        )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a submission-minimal manuscript package.")
    parser.add_argument("--paper-root", type=Path, required=True)
    parser.add_argument("--publication-profile", default="general_medical_journal")
    parser.add_argument("--citation-style", default="AMA")
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
