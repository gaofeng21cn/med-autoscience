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


def run_preflight(*, changed_files: list[str], repo_root: Path, input_mode: str = "files") -> PreflightResult:
    classification = dev_preflight_contract.classify_changed_files(changed_files)
    planned_commands = tuple(dev_preflight_contract.plan_commands_for_categories(classification.matched_categories))

    if classification.unclassified_changes:
        return PreflightResult(
            input_mode=input_mode,
            changed_files=tuple(changed_files),
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
        changed_files=tuple(changed_files),
        matched_categories=classification.matched_categories,
        unclassified_changes=classification.unclassified_changes,
        planned_commands=planned_commands,
        results=tuple(results),
        ok=ok,
    )
