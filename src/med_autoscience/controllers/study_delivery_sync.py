from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SYNC_STAGES = ("submission_minimal", "finalize")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_flat_yaml_mapping(path: Path) -> dict[str, str]:
    payload: dict[str, str] = {}
    pattern = re.compile(r"^(?P<key>[A-Za-z0-9_]+)\s*:\s*(?P<value>.+?)\s*$")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if raw_line.startswith((" ", "\t")):
            raise ValueError(f"nested YAML is not supported in {path}")
        match = pattern.match(raw_line)
        if match is None:
            raise ValueError(f"unsupported YAML line in {path}: {raw_line}")
        value = match.group("value").strip().strip("'").strip('"')
        if not value:
            raise ValueError(f"empty YAML scalar in {path}: {raw_line}")
        payload[match.group("key")] = value
    return payload


def read_top_level_yaml_scalar(path: Path, key: str) -> str:
    payload = load_flat_yaml_mapping(path)
    try:
        return payload[key]
    except KeyError as exc:
        raise ValueError(f"missing top-level scalar `{key}` in {path}") from exc


def reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def resolve_worktree_root(paper_root: Path) -> Path:
    return paper_root.resolve().parent


def resolve_quest_root(paper_root: Path) -> Path:
    worktree_root = resolve_worktree_root(paper_root)
    if worktree_root.parent.name != "worktrees" or worktree_root.parent.parent.name != ".ds":
        raise ValueError(f"paper_root is not under a DeepScientist worktree layout: {paper_root}")
    return worktree_root.parents[2]


def resolve_study_root(paper_root: Path) -> tuple[str, Path]:
    worktree_root = resolve_worktree_root(paper_root)
    quest_root = resolve_quest_root(paper_root)
    quest_yaml_path = worktree_root / "quest.yaml"
    if not quest_yaml_path.exists():
        raise FileNotFoundError(f"missing worktree quest.yaml: {quest_yaml_path}")
    study_id = read_top_level_yaml_scalar(quest_yaml_path, "quest_id")
    workspace_root = quest_root.parents[4]
    study_root = workspace_root / "studies" / study_id
    if not (study_root / "study.yaml").exists():
        raise FileNotFoundError(f"unable to resolve studies root for `{study_id}` from {paper_root}")
    return study_id, study_root


def can_sync_study_delivery(*, paper_root: Path) -> bool:
    try:
        resolve_study_root(paper_root.resolve())
    except (FileNotFoundError, ValueError):
        return False
    return True


def copy_file(
    *,
    source: Path,
    target: Path,
    category: str,
    copied_files: list[dict[str, str]],
) -> None:
    if not source.exists():
        raise FileNotFoundError(f"missing delivery source: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    copied_files.append(
        {
            "category": category,
            "source_path": str(source.resolve()),
            "target_path": str(target.resolve()),
        }
    )


def copy_tree(
    *,
    source_root: Path,
    target_root: Path,
    category: str,
    copied_files: list[dict[str, str]],
) -> None:
    if not source_root.exists():
        raise FileNotFoundError(f"missing delivery source directory: {source_root}")
    for source in sorted(source_root.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(source_root)
        copy_file(
            source=source,
            target=target_root / relative,
            category=category,
            copied_files=copied_files,
        )


def sync_study_delivery(
    *,
    paper_root: Path,
    stage: str,
) -> dict[str, Any]:
    normalized_stage = str(stage or "").strip()
    if normalized_stage not in SYNC_STAGES:
        raise ValueError(f"unsupported sync stage: {stage}")

    paper_root = paper_root.resolve()
    worktree_root = resolve_worktree_root(paper_root)
    study_id, study_root = resolve_study_root(paper_root)
    manuscript_final_root = study_root / "manuscript" / "final"
    artifacts_final_root = study_root / "artifacts" / "final"

    reset_directory(manuscript_final_root)
    reset_directory(artifacts_final_root)

    copied_files: list[dict[str, str]] = []
    copy_file(
        source=paper_root / "submission_minimal" / "manuscript.docx",
        target=manuscript_final_root / "manuscript.docx",
        category="manuscript",
        copied_files=copied_files,
    )
    copy_file(
        source=paper_root / "submission_minimal" / "paper.pdf",
        target=manuscript_final_root / "paper.pdf",
        category="manuscript",
        copied_files=copied_files,
    )
    copy_file(
        source=paper_root / "submission_minimal" / "submission_manifest.json",
        target=manuscript_final_root / "submission_manifest.json",
        category="manifest",
        copied_files=copied_files,
    )
    copy_tree(
        source_root=paper_root / "submission_minimal" / "figures",
        target_root=artifacts_final_root / "figures",
        category="figures",
        copied_files=copied_files,
    )
    copy_tree(
        source_root=paper_root / "submission_minimal" / "tables",
        target_root=artifacts_final_root / "tables",
        category="tables",
        copied_files=copied_files,
    )

    if normalized_stage == "finalize":
        copy_file(
            source=worktree_root / "SUMMARY.md",
            target=manuscript_final_root / "SUMMARY.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=worktree_root / "status.md",
            target=manuscript_final_root / "status.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "final_claim_ledger.md",
            target=manuscript_final_root / "final_claim_ledger.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "finalize_resume_packet.md",
            target=manuscript_final_root / "finalize_resume_packet.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "paper_bundle_manifest.json",
            target=artifacts_final_root / "paper_bundle_manifest.json",
            category="manifest",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "build" / "compile_report.json",
            target=artifacts_final_root / "compile_report.json",
            category="manifest",
            copied_files=copied_files,
        )

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": normalized_stage,
        "study_id": study_id,
        "quest_id": study_id,
        "source": {
            "paper_root": str(paper_root),
            "worktree_root": str(worktree_root),
        },
        "targets": {
            "study_root": str(study_root),
            "manuscript_final_root": str(manuscript_final_root),
            "artifacts_final_root": str(artifacts_final_root),
        },
        "copied_files": copied_files,
    }
    dump_json(manuscript_final_root / "delivery_manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync finalized paper deliverables into the study shallow path.")
    parser.add_argument("--paper-root", type=Path, required=True)
    parser.add_argument("--stage", choices=SYNC_STAGES, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sync_study_delivery(
        paper_root=args.paper_root,
        stage=args.stage,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
