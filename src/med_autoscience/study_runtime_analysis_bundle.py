from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any

from med_autoscience.python_environment_contract import (
    CURATED_PYTHON_ANALYSIS_BUNDLE_REQUIREMENTS,
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
BIOCONDUCTOR_R_ANALYSIS_BUNDLE_PACKAGES = ("ComplexHeatmap",)
ANALYSIS_PROVISIONING_BLOCKER = {
    "status": "opl_runtime_environment_bioconductor_source_supported",
    "owner": "one-person-lab",
    "owner_surface": "opl env prepare",
    "blocked_requirement": "ComplexHeatmap",
    "contract_ref": "contracts/opl-framework/runtime-environment-substrate-contract.json",
    "owner_release_ref": "one-person-lab@19abf74e79227e0f4924ab1588ecf3a3eb18d613",
    "effect": "read_only",
    "mas_provisioning_allowed": False,
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
        if separator:
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


def inspect_analysis_bundle() -> dict[str, Any]:
    python = inspect_python_environment_contract(requirements=CURATED_PYTHON_ANALYSIS_BUNDLE_REQUIREMENTS)
    r = _inspect_r_packages()
    return {
        "ready": python["ready"] and r["ready"],
        "python": python,
        "r": r,
        "r_package_sources": {
            package: (
                "bioconductor" if package in BIOCONDUCTOR_R_ANALYSIS_BUNDLE_PACKAGES else "cran"
            )
            for package in DEFAULT_R_ANALYSIS_BUNDLE_PACKAGES
        },
        "provisioning": dict(ANALYSIS_PROVISIONING_BLOCKER),
    }


__all__ = [
    "ANALYSIS_PROVISIONING_BLOCKER",
    "BIOCONDUCTOR_R_ANALYSIS_BUNDLE_PACKAGES",
    "DEFAULT_R_ANALYSIS_BUNDLE_PACKAGES",
    "inspect_analysis_bundle",
]
