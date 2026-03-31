from __future__ import annotations

import importlib
from types import SimpleNamespace


def test_inspect_bundle_combines_python_and_r_states(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")

    monkeypatch.setattr(
        module,
        "inspect_python_environment_contract",
        lambda **kwargs: {"ready": True, "missing_requirements": [], "requirements": ["matplotlib>=3.9"]},
    )
    monkeypatch.setattr(
        module,
        "_inspect_r_packages",
        lambda **kwargs: {"ready": False, "missing_packages": ["survival"], "packages": ["survival"]},
    )

    result = module.inspect_study_runtime_analysis_bundle()

    assert result["ready"] is False
    assert result["python"]["ready"] is True
    assert result["r"]["ready"] is False


def test_ensure_bundle_installs_python_and_r(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")
    states = iter(
        [
            {
                "ready": False,
                "python": {"ready": False, "missing_requirements": ["matplotlib>=3.9"]},
                "r": {"ready": False, "missing_packages": ["survival"]},
            },
            {
                "ready": True,
                "python": {"ready": True, "missing_requirements": []},
                "r": {"ready": True, "missing_packages": []},
            },
        ]
    )

    monkeypatch.setattr(module, "inspect_study_runtime_analysis_bundle", lambda: next(states))
    monkeypatch.setattr(
        module,
        "ensure_python_environment_contract",
        lambda **kwargs: {"action": "uv_pip_install", "after": {"ready": True}},
    )
    monkeypatch.setattr(
        module,
        "ensure_r_analysis_bundle",
        lambda **kwargs: {"action": "install_packages", "after": {"ready": True}},
    )

    result = module.ensure_study_runtime_analysis_bundle()

    assert result["action"] == "ensure_bundle"
    assert result["ready"] is True
    assert result["python"]["action"] == "uv_pip_install"
    assert result["r"]["action"] == "install_packages"


def test_ensure_r_bundle_reports_missing_rscript(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")

    monkeypatch.setattr(
        module,
        "_inspect_r_packages",
        lambda **kwargs: {
            "ready": False,
            "packages": ["survival"],
            "missing_packages": ["survival"],
            "package_status": {"survival": False},
            "rscript": None,
            "stdout": "",
            "stderr": "Rscript not found on PATH",
        },
    )

    result = module.ensure_r_analysis_bundle()

    assert result["action"] == "rscript_required"
    assert result["exit_code"] is None
    assert "Rscript not found" in result["stderr"]
