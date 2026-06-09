from __future__ import annotations

import ast
import importlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_EXECUTION_DIR = (
    REPO_ROOT
    / "src"
    / "med_autoscience"
    / "controllers"
    / "domain_owner_action_dispatch_parts"
    / "action_execution"
)
AUTHORITY_MODULE = ACTION_EXECUTION_DIR / "publication_handoff_stage_projection.py"
AUTHORITY_MODULE_REL = AUTHORITY_MODULE.relative_to(REPO_ROOT).as_posix()
MATERIALIZER_MODULE = (
    REPO_ROOT / "src" / "med_autoscience" / "controllers" / "stage_artifact_materializer.py"
)


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


def test_terminal_handoff_materializer_cannot_publish_owner_answer_projection() -> None:
    materializer = importlib.import_module(
        "med_autoscience.controllers.stage_artifact_materializer"
    )

    assert materializer._stage_artifact_projection_ref("08-publication_package_handoff") is None
    assert materializer._stage_artifact_projection_refs("08-publication_package_handoff") == []
    assert materializer._projection_authority("08-publication_package_handoff") == {
        "surface_kind": "stage_artifact_projection_authority",
        "stage_id": "08-publication_package_handoff",
        "materializer_can_write_current_owner_delta": False,
        "owner_answer_projection_required": True,
        "owner_answer_projection_ref": "projection/current_owner_delta.json",
        "owner_answer_projection_writer": "publication_handoff_stage_projection.py",
        "stage_run_current_authority": "opl_stage_transition_authority_only",
        "projection_role": "terminal_owner_answer_projection_required_not_materializer_publish",
        "can_publish_opl_current_owner_delta": False,
        "can_write_stage_current_pointer": False,
        "can_write_stage_run_terminal_state": False,
    }


def test_terminal_handoff_materializer_has_no_direct_projection_write() -> None:
    tree = ast.parse(MATERIALIZER_MODULE.read_text(encoding="utf-8"), filename=str(MATERIALIZER_MODULE))
    offenders: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "_write_json":
            continue
        if not node.args:
            continue
        path_expr = ast.dump(node.args[0])
        if "_PROJECTION_REF" in path_expr:
            offenders.append(f"{MATERIALIZER_MODULE.relative_to(REPO_ROOT).as_posix()}:{node.lineno}")

    assert offenders == []
