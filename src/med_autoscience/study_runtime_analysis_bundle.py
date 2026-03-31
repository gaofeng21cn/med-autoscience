from __future__ import annotations

import shutil
import subprocess
from typing import Any

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
    "dplyr",
    "readr",
    "tidyr",
    "patchwork",
    "survminer",
    "data.table",
)
DEFAULT_R_REPOSITORY = "https://cloud.r-project.org"


def _inspect_r_packages(*, packages: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:
    normalized_packages = tuple(DEFAULT_R_ANALYSIS_BUNDLE_PACKAGES if packages is None else packages)
    rscript = shutil.which("Rscript")
    if rscript is None:
        return {
            "ready": False,
            "packages": list(normalized_packages),
            "missing_packages": list(normalized_packages),
            "package_status": {package: False for package in normalized_packages},
            "rscript": None,
            "stdout": "",
            "stderr": "Rscript not found on PATH",
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
    install_script = (
        "args <- commandArgs(trailingOnly=TRUE); "
        f"options(repos = c(CRAN = '{DEFAULT_R_REPOSITORY}')); "
        "install.packages(args, quiet = TRUE)"
    )
    completed = subprocess.run(
        [str(before["rscript"]), "-e", install_script, *missing_packages],
        capture_output=True,
        text=True,
        check=False,
    )
    after = _inspect_r_packages(packages=packages)
    return {
        "action": "install_packages",
        "before": before,
        "after": after,
        "requested_packages": before["packages"],
        "missing_packages": missing_packages,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
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
