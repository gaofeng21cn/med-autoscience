from __future__ import annotations

import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


PREFERRED_LINE_LIMIT = 1000
CLEAR_VIOLATION_LINE_LIMIT = 1500
DEFAULT_BASELINE = {
    "src/med_autoscience/controllers/runtime_watch.py": 1499,
    "src/med_autoscience/cli.py": 1475,
    "src/med_autoscience/controllers/study_outer_loop.py": 1410,
    "src/med_autoscience/controllers/gate_clearing_batch.py": 1363,
    "src/med_autoscience/controllers/study_runtime_execution.py": 1346,
    "src/med_autoscience/controllers/mainline_status.py": 1301,
    "src/med_autoscience/controllers/product_entry_parts/workspace_surfaces.py": 1292,
    "tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py": 1289,
    "tests/product_entry_cases/repo_shell_and_handoff_templates.py": 1265,
    "src/med_autoscience/controllers/workspace_init.py": 1186,
    "tests/product_entry_cases/frontdoor_preflight_and_task_submission.py": 1180,
    "src/med_autoscience/controllers/study_progress_parts/projection.py": 1155,
    "src/med_autoscience/runtime_transport/med_deepscientist.py": 1146,
    "src/med_autoscience/controllers/product_entry_parts/manifest_surfaces.py": 1122,
    "src/med_autoscience/controllers/time_to_event_direct_migration.py": 1094,
    "tests/study_progress_cases/markdown_and_followthrough_projection.py": 1075,
    "src/med_autoscience/controllers/product_entry_parts/shared_base.py": 1020,
}
CODE_EXTENSIONS = frozenset(
    {
        ".py",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".mts",
        ".cts",
        ".sh",
        ".bash",
        ".zsh",
        ".rs",
        ".go",
    }
)
IGNORED_PARTS = frozenset({"node_modules", "dist", "build", "coverage", ".venv", "__pycache__"})
IGNORED_SUFFIXES = (".min.js",)
MECHANICAL_SPLIT_NAME = re.compile(r"^(?:part|chunk|split)[_-]?\d+$", re.IGNORECASE)


@dataclass(frozen=True)
class BoundaryFinding:
    path: str
    kind: str
    severity: str
    message: str
    recommendation: str
    line_count: int | None = None
    limit: int | None = None
    baseline: int | None = None

    @property
    def is_blocking(self) -> bool:
        return self.severity == "violation"


@dataclass(frozen=True)
class BoundaryFitnessReport:
    findings: tuple[BoundaryFinding, ...]

    @property
    def blocking_findings(self) -> tuple[BoundaryFinding, ...]:
        return tuple(finding for finding in self.findings if finding.is_blocking)

    @property
    def oversized_findings(self) -> tuple[BoundaryFinding, ...]:
        return tuple(finding for finding in self.findings if finding.kind == "oversized_file")

    @property
    def mechanical_split_findings(self) -> tuple[BoundaryFinding, ...]:
        return tuple(finding for finding in self.findings if finding.kind == "mechanical_split_residue")


def audit_boundary_fitness(
    repo_root: Path | str,
    *,
    tracked_files: Sequence[str] | None = None,
    baseline: Mapping[str, int] | None = None,
) -> BoundaryFitnessReport:
    root = Path(repo_root)
    tracked = tuple(_tracked_files(root) if tracked_files is None else tracked_files)
    locked_baseline = _normalize_baseline(DEFAULT_BASELINE if baseline is None else baseline)
    findings: list[BoundaryFinding] = []

    for relative_path in tracked:
        normalized_path = _normalize_relative_path(relative_path)
        if not is_code_file(normalized_path):
            continue
        absolute_path = root / normalized_path
        if not absolute_path.is_file():
            continue
        if has_mechanical_split_name(normalized_path):
            findings.append(_mechanical_split_finding(normalized_path))
        line_count = count_lines(absolute_path)
        if line_count > PREFERRED_LINE_LIMIT:
            findings.append(
                _oversized_file_finding(
                    relative_path=normalized_path,
                    line_count=line_count,
                    baseline=locked_baseline.get(normalized_path),
                )
            )

    for relative_path in sorted(locked_baseline):
        if not (root / relative_path).exists():
            findings.append(
                BoundaryFinding(
                    path=relative_path,
                    kind="stale_boundary_baseline",
                    severity="violation",
                    message="stale boundary baseline entry points to a missing file",
                    recommendation="Remove the stale baseline entry after the file is deleted, renamed, or absorbed.",
                )
            )

    return BoundaryFitnessReport(findings=tuple(sorted(findings, key=_finding_sort_key)))


def is_code_file(relative_path: str) -> bool:
    path = PurePosixPath(_normalize_relative_path(relative_path))
    if any(part in IGNORED_PARTS for part in path.parts):
        return False
    if path.as_posix().endswith(IGNORED_SUFFIXES):
        return False
    return path.suffix in CODE_EXTENSIONS


def count_lines(path: Path) -> int:
    content = path.read_text(encoding="utf-8")
    if not content:
        return 0
    return len(content.splitlines())


def has_mechanical_split_name(relative_path: str) -> bool:
    path = PurePosixPath(_normalize_relative_path(relative_path))
    for index, part in enumerate(path.parts):
        name = PurePosixPath(part).stem if index == len(path.parts) - 1 else part
        if MECHANICAL_SPLIT_NAME.fullmatch(name):
            return True
    return False


def _tracked_files(repo_root: Path) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return tuple(result.stdout.splitlines())


def _normalize_baseline(baseline: Mapping[str, int]) -> dict[str, int]:
    return {_normalize_relative_path(relative_path): line_count for relative_path, line_count in baseline.items()}


def _normalize_relative_path(relative_path: str) -> str:
    return relative_path.replace("\\", "/").removeprefix("./")


def _oversized_file_finding(
    *,
    relative_path: str,
    line_count: int,
    baseline: int | None,
) -> BoundaryFinding:
    if line_count > CLEAR_VIOLATION_LINE_LIMIT:
        return BoundaryFinding(
            path=relative_path,
            kind="oversized_file",
            severity="violation",
            line_count=line_count,
            limit=CLEAR_VIOLATION_LINE_LIMIT,
            baseline=baseline,
            message=(
                f"{line_count} lines exceeds the clear {CLEAR_VIOLATION_LINE_LIMIT}-line boundary violation limit"
            ),
            recommendation=natural_boundary_recommendation(relative_path),
        )
    if baseline is None:
        return BoundaryFinding(
            path=relative_path,
            kind="oversized_file",
            severity="violation",
            line_count=line_count,
            limit=PREFERRED_LINE_LIMIT,
            message=f"{line_count} lines exceeds the preferred boundary without a reviewed boundary baseline",
            recommendation=natural_boundary_recommendation(relative_path),
        )
    if line_count > baseline:
        return BoundaryFinding(
            path=relative_path,
            kind="oversized_file",
            severity="violation",
            line_count=line_count,
            limit=baseline,
            baseline=baseline,
            message=f"{line_count} lines exceeds locked boundary baseline {baseline}",
            recommendation=natural_boundary_recommendation(relative_path),
        )
    return BoundaryFinding(
        path=relative_path,
        kind="oversized_file",
        severity="advisory",
        line_count=line_count,
        limit=PREFERRED_LINE_LIMIT,
        baseline=baseline,
        message=f"{line_count} lines exceeds the preferred {PREFERRED_LINE_LIMIT}-line boundary",
        recommendation=natural_boundary_recommendation(relative_path),
    )


def _mechanical_split_finding(relative_path: str) -> BoundaryFinding:
    return BoundaryFinding(
        path=relative_path,
        kind="mechanical_split_residue",
        severity="violation",
        message="tracked code uses mechanical part/chunk/split numbering",
        recommendation=(
            "Rename or split by a natural responsibility boundary instead of numbered part/chunk/split files."
        ),
    )


def natural_boundary_recommendation(relative_path: str) -> str:
    path = PurePosixPath(relative_path)
    parts = path.parts
    stem = path.stem
    if "controllers" in parts:
        return (
            f"Prefer a thin controller entrypoint plus src/med_autoscience/controllers/{stem}_parts/ modules "
            "named by natural responsibility boundary."
        )
    if parts and parts[0] == "tests":
        return (
            f"Prefer behavior-focused tests/{stem}_cases/ modules named by natural responsibility boundary, "
            "with any top-level test file kept as a thin entrypoint."
        )
    if parts and parts[0] == "scripts":
        return (
            "Prefer a thin script wrapper around importable src/med_autoscience modules named by natural "
            "responsibility boundary."
        )
    return "Prefer focused modules named by natural responsibility boundary before adding more logic here."


def _finding_sort_key(finding: BoundaryFinding) -> tuple[int, str, int, str]:
    severity_rank = 0 if finding.severity == "violation" else 1
    return (severity_rank, finding.kind, -(finding.line_count or 0), finding.path)
