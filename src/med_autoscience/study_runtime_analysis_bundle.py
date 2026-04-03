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


def _split_r_packages_by_repository(packages: tuple[str, ...] | list[str]) -> dict[str, list[str]]:
    bioconductor = [package for package in packages if package in BIOCONDUCTOR_R_ANALYSIS_BUNDLE_PACKAGES]
    cran = [package for package in packages if package not in BIOCONDUCTOR_R_ANALYSIS_BUNDLE_PACKAGES]
    return {
        "cran": cran,
        "bioconductor": bioconductor,
    }


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
