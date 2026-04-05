from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess

from med_autoscience import dev_preflight_contract


@dataclass(frozen=True)
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str

    def to_dict(self) -> dict[str, object]:
        return {
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


@dataclass(frozen=True)
class PreflightResult:
    input_mode: str
    changed_files: tuple[str, ...]
    matched_categories: tuple[str, ...]
    unclassified_changes: tuple[str, ...]
    planned_commands: tuple[str, ...]
    results: tuple[CommandResult, ...]
    ok: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "input_mode": self.input_mode,
            "changed_files": list(self.changed_files),
            "matched_categories": list(self.matched_categories),
            "unclassified_changes": list(self.unclassified_changes),
            "planned_commands": list(self.planned_commands),
            "results": [item.to_dict() for item in self.results],
            "ok": self.ok,
        }


def render_preflight_text(result: PreflightResult) -> str:
    lines = [
        f"input_mode: {result.input_mode}",
        f"ok: {'true' if result.ok else 'false'}",
        "changed_files:",
    ]
    lines.extend(f"  - {item}" for item in result.changed_files)
    lines.append("matched_categories:")
    lines.extend(f"  - {item}" for item in result.matched_categories)
    lines.append("unclassified_changes:")
    lines.extend(f"  - {item}" for item in result.unclassified_changes)
    lines.append("planned_commands:")
    lines.extend(f"  - {item}" for item in result.planned_commands)
    if result.results:
        lines.append("results:")
        for item in result.results:
            lines.append(f"  - command: {item.command}")
            lines.append(f"    returncode: {item.returncode}")
    return "\n".join(lines) + "\n"


def _normalize_changed_files(changed_files: list[str]) -> list[str]:
    normalized: list[str] = []
    for changed_file in changed_files:
        normalized_path = dev_preflight_contract._normalize_changed_file(str(changed_file))
        if not normalized_path or normalized_path in normalized:
            continue
        normalized.append(normalized_path)
    return normalized


def _git_diff_name_only(*, repo_root: Path, diff_args: list[str]) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--relative", *diff_args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "git diff failed")
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def collect_changed_files(
    *,
    repo_root: Path,
    files: list[str] | None = None,
    staged: bool = False,
    base_ref: str | None = None,
) -> list[str]:
    selected_modes = int(bool(files)) + int(bool(staged)) + int(bool(base_ref))
    if selected_modes != 1:
        raise ValueError("specify exactly one of files, staged, or base_ref")

    if files:
        return _normalize_changed_files(list(files))
    if staged:
        return _normalize_changed_files(_git_diff_name_only(repo_root=repo_root, diff_args=["--cached"]))
    return _normalize_changed_files(_git_diff_name_only(repo_root=repo_root, diff_args=[f"{base_ref}...HEAD"]))


def run_preflight(*, changed_files: list[str], repo_root: Path, input_mode: str = "files") -> PreflightResult:
    normalized_changed_files = _normalize_changed_files(changed_files)
    classification = dev_preflight_contract.classify_changed_files(normalized_changed_files)
    planned_commands = tuple(dev_preflight_contract.plan_commands_for_categories(classification.matched_categories))

    if classification.unclassified_changes:
        return PreflightResult(
            input_mode=input_mode,
            changed_files=tuple(normalized_changed_files),
            matched_categories=classification.matched_categories,
            unclassified_changes=classification.unclassified_changes,
            planned_commands=(),
            results=(),
            ok=False,
        )

    results: list[CommandResult] = []
    ok = True
    for command in planned_commands:
        completed = subprocess.run(
            shlex.split(command),
            cwd=repo_root,
            text=True,
            capture_output=True,
        )
        command_result = CommandResult(
            command=command,
            returncode=int(completed.returncode),
            stdout=str(completed.stdout),
            stderr=str(completed.stderr),
        )
        results.append(command_result)
        if completed.returncode != 0:
            ok = False

    return PreflightResult(
        input_mode=input_mode,
        changed_files=tuple(normalized_changed_files),
        matched_categories=classification.matched_categories,
        unclassified_changes=classification.unclassified_changes,
        planned_commands=planned_commands,
        results=tuple(results),
        ok=ok,
    )
