from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from med_autoscience import python_environment_contract
from med_autoscience.python_environment_contract import (
    CURATED_PYTHON_ANALYSIS_BUNDLE_REQUIREMENTS,
    ensure_python_environment_contract,
    inspect_python_environment_contract,
)


DEFAULT_R_ANALYSIS_BUNDLE_PACKAGES = (
    "survival",
    "cmprsk",
    "riskRegression",
    "timeROC",
    "rms",
    "ggplot2",
    "ggrepel",
    "ggsci",
    "jsonlite",
    "dplyr",
    "readr",
    "tidyr",
    "patchwork",
    "cowplot",
    "pROC",
    "precrec",
    "dcurves",
    "ggsurvfit",
    "forestploter",
    "ComplexHeatmap",
    "circlize",
    "survminer",
    "data.table",
)
DEFAULT_R_REPOSITORY = "https://cloud.r-project.org"
BIOCONDUCTOR_R_ANALYSIS_BUNDLE_PACKAGES = ("ComplexHeatmap",)


def _managed_runtime_repo_root() -> Path:
    return python_environment_contract.CHECKOUT_ROOT


def _running_under_managed_runtime() -> bool:
    return python_environment_contract._is_managed_runtime()


def _managed_runtime_prefix() -> Path:
    prefixes: list[Path] = []
    for prefix in (
        python_environment_contract.CHECKOUT_MANAGED_RUNTIME_PREFIX,
        python_environment_contract.MANAGED_RUNTIME_PREFIX,
    ):
        if prefix not in prefixes:
            prefixes.append(prefix)
    for prefix in prefixes:
        if prefix.exists():
            return prefix
    return prefixes[0]


def _managed_runtime_python_executable() -> str:
    prefix = _managed_runtime_prefix()
    candidates = (
        prefix / "bin" / "python",
        prefix / "bin" / "python3",
        prefix / "Scripts" / "python.exe",
        prefix / "Scripts" / "python",
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(candidates[0])


def _managed_runtime_environment(*, repo_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    source_root = str(repo_root / "src")
    current_pythonpath = env.get("PYTHONPATH", "").strip()
    if current_pythonpath:
        env["PYTHONPATH"] = os.pathsep.join((source_root, current_pythonpath))
    else:
        env["PYTHONPATH"] = source_root
    return env


def _delegate_analysis_bundle_to_managed_runtime(*, before: dict[str, Any]) -> dict[str, Any]:
    repo_root = _managed_runtime_repo_root()
    managed_python = _managed_runtime_python_executable()
    command = [
        managed_python,
        "-m",
        "med_autoscience.cli",
        "ensure-study-runtime-analysis-bundle",
    ]
    managed_runtime: dict[str, Any] = {
        "repo_root": str(repo_root),
        "python": managed_python,
        "command": command,
    }
    delegated_result: dict[str, Any] | None = None
    after: dict[str, Any] = before
    ready = False
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            env=_managed_runtime_environment(repo_root=repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        managed_runtime.update(
            {
                "exit_code": None,
                "stdout": "",
                "stderr": str(exc),
            }
        )
    else:
        managed_runtime.update(
            {
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
        if completed.returncode == 0:
            try:
                payload = json.loads(completed.stdout)
            except json.JSONDecodeError as exc:
                managed_runtime["stderr"] = (
                    f"{completed.stderr.rstrip()}\nInvalid managed-runtime JSON payload: {exc}".strip()
                )
            else:
                if isinstance(payload, dict):
                    delegated_result = payload
                    delegated_after = payload.get("after")
                    if isinstance(delegated_after, dict):
                        after = delegated_after
                    ready = payload.get("ready") is True
                else:
                    managed_runtime["stderr"] = (
                        f"{completed.stderr.rstrip()}\nManaged runtime returned a non-object JSON payload.".strip()
                    )
    result = {
        "action": "delegate_to_managed_runtime",
        "before": before,
        "after": after,
        "delegated_result": delegated_result,
        "managed_runtime": managed_runtime,
        "ready": ready,
    }
    if delegated_result is not None:
        if "python" in delegated_result:
            result["python"] = delegated_result["python"]
        if "r" in delegated_result:
            result["r"] = delegated_result["r"]
    return result


def _split_r_packages_by_repository(packages: tuple[str, ...] | list[str]) -> dict[str, list[str]]:
    bioconductor = [package for package in packages if package in BIOCONDUCTOR_R_ANALYSIS_BUNDLE_PACKAGES]
    cran = [package for package in packages if package not in BIOCONDUCTOR_R_ANALYSIS_BUNDLE_PACKAGES]
    return {
        "cran": cran,
        "bioconductor": bioconductor,
    }


def _resolve_rscript_executable() -> tuple[str | None, str | None]:
    configured_rscript = str(os.environ.get("MED_AUTOSCIENCE_RSCRIPT_BIN") or "").strip()
    if configured_rscript:
        if not os.path.isabs(configured_rscript):
            return None, f"MED_AUTOSCIENCE_RSCRIPT_BIN must be an absolute path: {configured_rscript}"
        if not os.access(configured_rscript, os.X_OK):
            return None, f"MED_AUTOSCIENCE_RSCRIPT_BIN is not executable: {configured_rscript}"
        return configured_rscript, None
    rscript = shutil.which("Rscript")
    if rscript is None:
        return None, "Rscript not found on PATH"
    return rscript, None


def _inspect_r_packages(*, packages: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
    normalized_packages = tuple(DEFAULT_R_ANALYSIS_BUNDLE_PACKAGES if packages is None else packages)
    rscript, rscript_error = _resolve_rscript_executable()
    if rscript is None:
        return {
            "ready": False,
            "packages": list(normalized_packages),
            "missing_packages": list(normalized_packages),
            "package_status": {package: False for package in normalized_packages},
            "rscript": None,
            "stdout": "",
            "stderr": rscript_error or "Rscript not found on PATH",
        }

    probe = (
        "args <- commandArgs(trailingOnly=TRUE); "
        "status <- vapply(args, requireNamespace, quietly=TRUE, FUN.VALUE=logical(1)); "
        "for (i in seq_along(args)) { "
        "cat(sprintf('%s=%s\\n', args[[i]], if (status[[i]]) '1' else '0')) "
        "}"
    )
    completed = subprocess.run(
        [rscript, "-e", probe, *normalized_packages],
        capture_output=True,
        text=True,
        check=False,
    )
    package_status: dict[str, bool] = {}
    for line in completed.stdout.splitlines():
        name, separator, value = line.partition("=")
        if not separator:
            continue
        package_status[name.strip()] = value.strip() == "1"
    for package in normalized_packages:
        package_status.setdefault(package, False)
    missing_packages = [package for package, ready in package_status.items() if not ready]
    return {
        "ready": completed.returncode == 0 and not missing_packages,
        "packages": list(normalized_packages),
        "missing_packages": missing_packages,
        "package_status": package_status,
        "rscript": rscript,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def ensure_r_analysis_bundle(*, packages: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
    before = _inspect_r_packages(packages=packages)
    if before["ready"]:
        return {"action": "already_ready", "before": before, "after": before}
    if before["rscript"] is None:
        return {
            "action": "rscript_required",
            "before": before,
            "after": before,
            "exit_code": None,
            "stdout": "",
            "stderr": before["stderr"],
        }

    missing_packages = [str(item) for item in before["missing_packages"]]
    package_channels = _split_r_packages_by_repository(missing_packages)
    install_steps: list[dict[str, Any]] = []
    combined_stdout: list[str] = []
    combined_stderr: list[str] = []
    exit_code = 0

    if package_channels["cran"]:
        cran_install_script = (
            "args <- commandArgs(trailingOnly=TRUE); "
            f"options(repos = c(CRAN = '{DEFAULT_R_REPOSITORY}')); "
            "install.packages(args, quiet = TRUE)"
        )
        cran_completed = subprocess.run(
            [str(before["rscript"]), "-e", cran_install_script, *package_channels["cran"]],
            capture_output=True,
            text=True,
            check=False,
        )
        install_steps.append(
            {
                "repository": "CRAN",
                "packages": list(package_channels["cran"]),
                "exit_code": cran_completed.returncode,
                "stdout": cran_completed.stdout,
                "stderr": cran_completed.stderr,
            }
        )
        if cran_completed.stdout:
            combined_stdout.append(cran_completed.stdout)
        if cran_completed.stderr:
            combined_stderr.append(cran_completed.stderr)
        if exit_code == 0 and cran_completed.returncode != 0:
            exit_code = cran_completed.returncode

    if package_channels["bioconductor"]:
        bioconductor_install_script = (
            "args <- commandArgs(trailingOnly=TRUE); "
            f"options(repos = c(CRAN = '{DEFAULT_R_REPOSITORY}')); "
            "if (!requireNamespace('BiocManager', quietly = TRUE)) install.packages('BiocManager', quiet = TRUE); "
            "suppressMessages(BiocManager::install(args, ask = FALSE, update = FALSE))"
        )
        bioconductor_completed = subprocess.run(
            [str(before["rscript"]), "-e", bioconductor_install_script, *package_channels["bioconductor"]],
            capture_output=True,
            text=True,
            check=False,
        )
        install_steps.append(
            {
                "repository": "Bioconductor",
                "packages": list(package_channels["bioconductor"]),
                "exit_code": bioconductor_completed.returncode,
                "stdout": bioconductor_completed.stdout,
                "stderr": bioconductor_completed.stderr,
            }
        )
        if bioconductor_completed.stdout:
            combined_stdout.append(bioconductor_completed.stdout)
        if bioconductor_completed.stderr:
            combined_stderr.append(bioconductor_completed.stderr)
        if exit_code == 0 and bioconductor_completed.returncode != 0:
            exit_code = bioconductor_completed.returncode

    after = _inspect_r_packages(packages=packages)
    return {
        "action": "install_packages",
        "before": before,
        "after": after,
        "requested_packages": before["packages"],
        "missing_packages": missing_packages,
        "install_steps": install_steps,
        "exit_code": exit_code,
        "stdout": "\n".join(item.rstrip() for item in combined_stdout if item).strip(),
        "stderr": "\n".join(item.rstrip() for item in combined_stderr if item).strip(),
    }


def inspect_study_runtime_analysis_bundle() -> dict[str, Any]:
    python = inspect_python_environment_contract(requirements=CURATED_PYTHON_ANALYSIS_BUNDLE_REQUIREMENTS)
    r = _inspect_r_packages()
    return {
        "ready": python["ready"] and r["ready"],
        "python": python,
        "r": r,
    }


def ensure_study_runtime_analysis_bundle() -> dict[str, Any]:
    before = inspect_study_runtime_analysis_bundle()
    if before["ready"]:
        return {"action": "already_ready", "before": before, "after": before, "ready": True}
    if not _running_under_managed_runtime():
        return _delegate_analysis_bundle_to_managed_runtime(before=before)

    python_result = ensure_python_environment_contract(requirements=CURATED_PYTHON_ANALYSIS_BUNDLE_REQUIREMENTS)
    r_result = ensure_r_analysis_bundle()
    after = inspect_study_runtime_analysis_bundle()
    return {
        "action": "ensure_bundle",
        "before": before,
        "after": after,
        "python": python_result,
        "r": r_result,
        "ready": after["ready"],
    }
