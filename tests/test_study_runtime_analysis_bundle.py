from __future__ import annotations

import importlib
import subprocess
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


def test_complexheatmap_is_classified_as_bioconductor_package() -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")

    channels = module._split_r_packages_by_repository(["pROC", "ComplexHeatmap"])

    assert channels["cran"] == ["pROC"]
    assert channels["bioconductor"] == ["ComplexHeatmap"]


def test_ensure_r_analysis_bundle_installs_cran_then_bioconductor_when_needed(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")
    before_state = {
        "ready": False,
        "packages": ["pROC", "ComplexHeatmap"],
        "missing_packages": ["pROC", "ComplexHeatmap"],
        "package_status": {"pROC": False, "ComplexHeatmap": False},
        "rscript": "/usr/bin/Rscript",
        "stdout": "",
        "stderr": "",
    }
    after_state = {
        "ready": True,
        "packages": ["pROC", "ComplexHeatmap"],
        "missing_packages": [],
        "package_status": {"pROC": True, "ComplexHeatmap": True},
        "rscript": "/usr/bin/Rscript",
        "stdout": "",
        "stderr": "",
    }

    class Inspector:
        def __init__(self) -> None:
            self.calls = 0

        def __call__(self, *, packages=None):
            self.calls += 1
            return before_state if self.calls == 1 else after_state

    inspector = Inspector()
    monkeypatch.setattr(module, "_inspect_r_packages", inspector)
    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(list(args))
        return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = module.ensure_r_analysis_bundle(packages=["pROC", "ComplexHeatmap"])

    assert [step["repository"] for step in result["install_steps"]] == ["CRAN", "Bioconductor"]
    assert calls[0][:3] == ["/usr/bin/Rscript", "-e", calls[0][2]]
    assert "install.packages(args, quiet = TRUE)" in calls[0][2]
    assert calls[0][3:] == ["pROC"]
    assert calls[1][:3] == ["/usr/bin/Rscript", "-e", calls[1][2]]
    assert "BiocManager" in calls[1][2]
    assert calls[1][3:] == ["ComplexHeatmap"]
    assert result["after"]["ready"] is True


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

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = module._inspect_r_packages(packages=["pROC"])

    assert result["ready"] is True
    assert result["rscript"] == str(explicit_rscript)
    assert result["missing_packages"] == []
    assert result["package_status"] == {"pROC": True}


def test_ensure_study_runtime_analysis_bundle_repairs_current_runtime(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")
    before_state = {
        "ready": False,
        "python": {"ready": False, "interpreter": "/tmp/workspace/.venv/bin/python3"},
        "r": {"ready": True, "rscript": "/usr/bin/Rscript"},
    }
    after_state = {
        "ready": True,
        "python": {"ready": True, "interpreter": "/tmp/workspace/.venv/bin/python3"},
        "r": {"ready": True, "rscript": "/usr/bin/Rscript"},
    }

    class Inspector:
        def __init__(self) -> None:
            self.calls = 0

        def __call__(self):
            self.calls += 1
            return before_state if self.calls == 1 else after_state

    inspector = Inspector()
    monkeypatch.setattr(module, "inspect_study_runtime_analysis_bundle", inspector)

    python_result = {"action": "uv_pip_install", "after": after_state["python"]}
    r_result = {"action": "already_ready", "after": after_state["r"]}
    monkeypatch.setattr(module, "ensure_python_environment_contract", lambda **kwargs: python_result)
    monkeypatch.setattr(module, "ensure_r_analysis_bundle", lambda: r_result)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("current runtime repair should not spawn a repo Python delegate")
        ),
    )

    result = module.ensure_study_runtime_analysis_bundle()

    assert result["action"] == "ensure_bundle"
    assert result["before"] == before_state
    assert result["after"] == after_state
    assert result["python"] == python_result
    assert result["r"] == r_result
    assert result["ready"] is True
