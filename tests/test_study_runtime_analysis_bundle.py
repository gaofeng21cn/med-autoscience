from __future__ import annotations

import importlib
import json
import subprocess
from types import SimpleNamespace

import pytest


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


def test_ensure_study_runtime_analysis_bundle_delegates_to_repo_managed_runtime(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")
    before_state = {
        "ready": False,
        "python": {"ready": False, "interpreter": "/tmp/external/bin/python"},
        "r": {"ready": True, "rscript": "/usr/bin/Rscript"},
    }
    delegated_payload = {
        "action": "ensure_bundle",
        "before": {"ready": False},
        "after": {"ready": True},
        "python": {"action": "uv_pip_install"},
        "r": {"action": "already_ready"},
        "ready": True,
    }
    recorded: dict[str, object] = {}

    monkeypatch.setattr(module, "inspect_study_runtime_analysis_bundle", lambda: before_state)
    monkeypatch.setattr(module, "_running_under_managed_runtime", lambda: False, raising=False)
    monkeypatch.setattr(
        module,
        "_managed_runtime_python_executable",
        lambda: "/tmp/repo/.venv/bin/python",
        raising=False,
    )
    monkeypatch.setattr(module, "_managed_runtime_repo_root", lambda: module.Path("/tmp/repo"), raising=False)

    def fail_local_install(**kwargs):
        raise AssertionError("should delegate to repo-managed runtime instead of using local interpreter")

    monkeypatch.setattr(module, "ensure_python_environment_contract", fail_local_install)

    def fake_run(args, **kwargs):
        recorded["args"] = args
        recorded["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout=json.dumps(delegated_payload), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = module.ensure_study_runtime_analysis_bundle()

    assert result["action"] == "delegate_to_managed_runtime"
    assert result["before"] == before_state
    assert result["after"] == delegated_payload["after"]
    assert result["ready"] is True
    assert result["delegated_result"] == delegated_payload
    assert result["managed_runtime"]["python"] == "/tmp/repo/.venv/bin/python"
    assert recorded["args"] == [
        "/tmp/repo/.venv/bin/python",
        "-m",
        "med_autoscience.cli",
        "ensure-study-runtime-analysis-bundle",
    ]
    assert recorded["kwargs"]["cwd"] == module.Path("/tmp/repo")
    assert str(module.Path("/tmp/repo") / "src") in recorded["kwargs"]["env"]["PYTHONPATH"]


def test_ensure_study_runtime_analysis_bundle_surfaces_delegate_failure(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")
    before_state = {
        "ready": False,
        "python": {"ready": False, "interpreter": "/tmp/external/bin/python"},
        "r": {"ready": True, "rscript": "/usr/bin/Rscript"},
    }

    monkeypatch.setattr(module, "inspect_study_runtime_analysis_bundle", lambda: before_state)
    monkeypatch.setattr(module, "_running_under_managed_runtime", lambda: False, raising=False)
    monkeypatch.setattr(
        module,
        "_managed_runtime_python_executable",
        lambda: "/tmp/repo/.venv/bin/python",
        raising=False,
    )
    monkeypatch.setattr(module, "_managed_runtime_repo_root", lambda: module.Path("/tmp/repo"), raising=False)
    monkeypatch.setattr(
        module,
        "ensure_python_environment_contract",
        lambda **kwargs: pytest.fail("should delegate to repo-managed runtime"),
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=17, stdout="", stderr="managed runtime failed"),
    )

    result = module.ensure_study_runtime_analysis_bundle()

    assert result["action"] == "delegate_to_managed_runtime"
    assert result["ready"] is False
    assert result["before"] == before_state
    assert result["after"] == before_state
    assert result["delegated_result"] is None
    assert result["managed_runtime"]["exit_code"] == 17
    assert result["managed_runtime"]["stderr"] == "managed runtime failed"
