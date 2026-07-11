from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_EXECUTION_DIR = (
    REPO_ROOT
    / "src"
    / "med_autoscience"
    / "controllers"
    / "stage_outcome_authority"
    / "action_execution"
)
AUTHORITY_MODULE = ACTION_EXECUTION_DIR / "publication_handoff_stage_projection.py"
AUTHORITY_MODULE_REL = AUTHORITY_MODULE.relative_to(REPO_ROOT).as_posix()


def test_terminal_handoff_stage_projection_has_single_source_writer() -> None:
    offenders: list[str] = []
    for path in ACTION_EXECUTION_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(REPO_ROOT).as_posix()
        if path == AUTHORITY_MODULE:
            writer_names = {
                node.name for node in tree.body if isinstance(node, ast.FunctionDef)
            }
            assert "write_stage_current_projection" in writer_names
            assert "_write_json" in writer_names
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in {
                "_write_current_owner_delta",
                "_write_current_pointer",
                "write_stage_current_projection",
            }:
                offenders.append(f"{rel}:{node.lineno}: function {node.name}")
            if isinstance(node, ast.Name) and node.id in {
                "CURRENT_OWNER_DELTA_RELATIVE_PATH",
                "CURRENT_POINTER_RELATIVE_PATH",
            }:
                offenders.append(f"{rel}:{node.lineno}: direct {node.id}")

    assert offenders == []


def test_terminal_handoff_projection_paths_are_owned_by_authority_module() -> None:
    offenders: list[str] = []
    for path in ACTION_EXECUTION_DIR.glob("*.py"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel == AUTHORITY_MODULE_REL:
            continue
        source = path.read_text(encoding="utf-8")
        if "projection/current_owner_delta.json" in source:
            offenders.append(f"{rel}: direct terminal current owner delta path")
        if "08-publication_package_handoff/current.json" in source:
            offenders.append(f"{rel}: direct terminal current pointer path")

    assert offenders == []
