from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace


def test_default_r_analysis_bundle_includes_publication_ready_packages() -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")

    packages = set(module.DEFAULT_R_ANALYSIS_BUNDLE_PACKAGES)

    assert {
        "ggplot2",
        "patchwork",
        "ggrepel",
        "ggsci",
        "jsonlite",
        "cowplot",
        "pROC",
        "precrec",
        "dcurves",
        "ggsurvfit",
        "forestploter",
        "ComplexHeatmap",
        "circlize",
    }.issubset(packages)
    assert module.BIOCONDUCTOR_R_ANALYSIS_BUNDLE_PACKAGES == ("ComplexHeatmap",)


def test_inspect_r_packages_honors_explicit_rscript_env_when_path_is_missing(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")
    explicit_rscript = tmp_path / "Rscript"
    explicit_rscript.write_text("#!/bin/sh\n", encoding="utf-8")
    explicit_rscript.chmod(0o755)

    monkeypatch.setenv("MED_AUTOSCIENCE_RSCRIPT_BIN", str(explicit_rscript))
    monkeypatch.setattr(module.shutil, "which", lambda executable: None)

    def fake_run(args, **kwargs):
        assert args[:2] == [str(explicit_rscript), "-e"]
        return SimpleNamespace(returncode=0, stdout="pROC=1\n", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module._inspect_r_packages(packages=["pROC"])

    assert result["ready"] is True
    assert result["rscript"] == str(explicit_rscript)
    assert result["missing_packages"] == []
    assert result["package_status"] == {"pROC": True}


def test_analysis_bundle_reports_opl_bioconductor_provisioning_owner(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")
    monkeypatch.setattr(
        module,
        "inspect_python_environment_contract",
        lambda **kwargs: {"ready": True},
    )
    monkeypatch.setattr(
        module,
        "_inspect_r_packages",
        lambda: {"ready": False, "missing_packages": ["ComplexHeatmap"]},
    )

    result = module.inspect_analysis_bundle()

    assert result["ready"] is False
    assert result["r_package_sources"]["pROC"] == "cran"
    assert result["r_package_sources"]["ComplexHeatmap"] == "bioconductor"
    assert result["provisioning"] == {
        "status": "opl_runtime_environment_bioconductor_source_supported",
        "owner": "one-person-lab",
        "owner_surface": "opl env prepare",
        "blocked_requirement": "ComplexHeatmap",
        "contract_ref": "contracts/opl-framework/runtime-environment-substrate-contract.json",
        "owner_release_ref": "one-person-lab@19abf74e79227e0f4924ab1588ecf3a3eb18d613",
        "effect": "read_only",
        "mas_provisioning_allowed": False,
    }


def test_analysis_bundle_surface_does_not_install_packages() -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert not hasattr(module, "ensure_analysis_bundle")
    assert not hasattr(module, "ensure_r_analysis_bundle")
    assert "install.packages" not in source
    assert "BiocManager" not in source
    assert "uv pip install" not in source
