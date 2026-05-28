from __future__ import annotations

import ast
import importlib
import subprocess
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta


def _boundary_fitness_module():
    return importlib.import_module("med_autoscience.controllers.boundary_fitness")


def _write_python_lines(path: Path, line_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"VALUE_{index} = {index}" for index in range(line_count)) + "\n", encoding="utf-8")


def test_audit_reports_preferred_boundary_advisories_and_clear_violations(tmp_path: Path) -> None:
    module = _boundary_fitness_module()
    advisory_path = Path("src/med_autoscience/controllers/large_controller.py")
    violation_path = Path("src/med_autoscience/controllers/overgrown_controller.py")
    _write_python_lines(tmp_path / advisory_path, 1001)
    _write_python_lines(tmp_path / violation_path, 1501)

    report = module.audit_boundary_fitness(
        tmp_path,
        tracked_files=(advisory_path.as_posix(), violation_path.as_posix()),
        baseline={advisory_path.as_posix(): 1001, violation_path.as_posix(): 1501},
    )

    oversized = {finding.path: finding for finding in report.oversized_findings}
    assert oversized[advisory_path.as_posix()].severity == "advisory"
    assert oversized[advisory_path.as_posix()].limit == module.PREFERRED_LINE_LIMIT
    assert oversized[violation_path.as_posix()].severity == "violation"
    assert oversized[violation_path.as_posix()].limit == module.CLEAR_VIOLATION_LINE_LIMIT
    assert oversized[violation_path.as_posix()] in report.blocking_findings
    assert "natural responsibility boundary" in oversized[violation_path.as_posix()].recommendation


def test_audit_blocks_new_or_growing_files_over_preferred_boundary(tmp_path: Path) -> None:
    module = _boundary_fitness_module()
    new_path = Path("src/med_autoscience/controllers/new_runtime_surface.py")
    growing_path = Path("src/med_autoscience/controllers/current_runtime_surface.py")
    _write_python_lines(tmp_path / new_path, 1001)
    _write_python_lines(tmp_path / growing_path, 1002)

    report = module.audit_boundary_fitness(
        tmp_path,
        tracked_files=(new_path.as_posix(), growing_path.as_posix()),
        baseline={growing_path.as_posix(): 1001},
    )

    blocking_by_path = {finding.path: finding for finding in report.blocking_findings}
    assert "without a reviewed boundary baseline" in blocking_by_path[new_path.as_posix()].message
    assert "exceeds locked boundary baseline" in blocking_by_path[growing_path.as_posix()].message


def test_audit_detects_mechanical_split_residue_without_flagging_semantic_parts(tmp_path: Path) -> None:
    module = _boundary_fitness_module()
    mechanical_path = Path("src/med_autoscience/controllers/domain_health_diagnostic_parts/chunk_01.py")
    semantic_path = Path("src/med_autoscience/controllers/product_entry_parts/shared.py")
    _write_python_lines(tmp_path / mechanical_path, 3)
    _write_python_lines(tmp_path / semantic_path, 3)

    report = module.audit_boundary_fitness(
        tmp_path,
        tracked_files=(mechanical_path.as_posix(), semantic_path.as_posix()),
        baseline={},
    )

    mechanical_paths = {finding.path for finding in report.mechanical_split_findings}
    assert mechanical_paths == {mechanical_path.as_posix()}
    assert report.mechanical_split_findings[0].severity == "violation"
    assert "numbered part/chunk/split files" in report.mechanical_split_findings[0].recommendation


def test_audit_reports_boundary_governance_advisories_without_blocking(tmp_path: Path) -> None:
    module = _boundary_fitness_module()
    nested_path = Path(
        "src/med_autoscience/controllers/study_runtime_decision_parts/runtime_events_parts/human_gates.py"
    )
    shared_base_path = Path("src/med_autoscience/controllers/product_entry_parts/shared_base.py")
    near_limit_path = Path("src/med_autoscience/controllers/study_progress_parts/projection.py")
    exec_compile_path = Path("src/med_autoscience/controllers/study_runtime_decision.py")
    _write_python_lines(tmp_path / nested_path, 3)
    _write_python_lines(tmp_path / shared_base_path, module.SHARED_BASE_BUCKET_LINE_LIMIT)
    _write_python_lines(tmp_path / near_limit_path, module.PART_NEAR_LINE_LIMIT)
    (tmp_path / exec_compile_path).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / exec_compile_path).write_text(
        "from pathlib import Path\n"
        "for _chunk_path in (Path(__file__),):\n"
        "    exec(compile(_chunk_path.read_text(encoding=\"utf-8\"), str(_chunk_path), \"exec\"), globals())\n",
        encoding="utf-8",
    )

    report = module.audit_boundary_fitness(
        tmp_path,
        tracked_files=(
            nested_path.as_posix(),
            shared_base_path.as_posix(),
            near_limit_path.as_posix(),
            exec_compile_path.as_posix(),
        ),
        baseline={},
    )

    advisory_by_kind = {finding.kind: finding for finding in report.advisory_findings}
    assert advisory_by_kind["nested_parts_directory"].path == nested_path.as_posix()
    assert advisory_by_kind["shared_base_bucket"].line_count == module.SHARED_BASE_BUCKET_LINE_LIMIT
    assert advisory_by_kind["part_near_line_limit"].line_count == module.PART_NEAR_LINE_LIMIT
    assert advisory_by_kind["exec_compile_concatenation"].path == exec_compile_path.as_posix()
    assert report.blocking_findings == ()


def test_current_repo_boundary_guard_has_no_blocking_findings() -> None:
    module = _boundary_fitness_module()
    repo_root = Path(__file__).resolve().parents[1]

    report = module.audit_boundary_fitness(repo_root)

    assert report.blocking_findings == ()
    for finding in report.oversized_findings:
        assert finding.severity == "advisory"


def test_submission_minimal_shared_facade_is_physically_retired() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    retired_facade = repo_root / "src/med_autoscience/controllers/submission_minimal_parts/shared.py"

    assert not retired_facade.exists()
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "src/med_autoscience/controllers/submission_minimal.py",
            "src/med_autoscience/controllers/submission_minimal_parts",
        ],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("med_autoscience.controllers.submission_minimal_parts.shared")

    offenders = []
    for relative_path in result.stdout.splitlines():
        candidate = repo_root / relative_path
        if not candidate.exists():
            continue
        tree = ast.parse(candidate.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                if any(
                    alias.name == "med_autoscience.controllers.submission_minimal_parts.shared"
                    for alias in node.names
                ):
                    offenders.append(relative_path)
                    break
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module == "shared" and node.level == 1:
                offenders.append(relative_path)
                break
            if node.module == "med_autoscience.controllers.submission_minimal_parts.shared":
                offenders.append(relative_path)
                break
            if node.module is None and node.level == 1 and any(alias.name == "shared" for alias in node.names):
                offenders.append(relative_path)
                break

    assert offenders == []


def test_program_boundary_map_prioritizes_natural_mas_mds_boundaries() -> None:
    module = _boundary_fitness_module()
    gate_path = "src/med_autoscience/controllers/gate_clearing_batch.py"
    runtime_path = "src/med_autoscience/opl_runtime_contract.py"
    observability_path = "src/med_autoscience/controllers/study_cycle_profiler.py"

    boundary_map = module.build_program_boundary_map(
        tracked_files=(gate_path, runtime_path, observability_path),
        findings=(
            module.BoundaryFinding(
                path=gate_path,
                kind="oversized_file",
                severity="violation",
                message="too large",
                recommendation="split by deterministic repair and gate replay responsibilities",
                line_count=1600,
                limit=1500,
            ),
            module.BoundaryFinding(
                path=runtime_path,
                kind="oversized_file",
                severity="advisory",
                message="large OPL provider handoff adapter",
                recommendation="keep MAS runtime transport limited to refs-only DomainIntent handoff",
                line_count=1146,
                limit=1000,
            ),
        ),
    )

    priorities = boundary_map["priorities"]
    assert priorities[0]["boundary_id"] == "paper_quality_gate"
    assert priorities[0]["priority"] == "now"
    assert "deterministic repair" in priorities[0]["recommended_split_direction"]
    assert {item["boundary_id"] for item in priorities} >= {
        "paper_quality_gate",
        "opl_stage_runtime_handoff",
        "observability_delivery_metrics",
    }
    split_text = " ".join(item["recommended_split_direction"].lower() for item in priorities)
    assert "chunk" not in split_text
    assert "part_" not in split_text
    assert "numbered" not in split_text
