from __future__ import annotations

import importlib


def test_default_r_analysis_bundle_includes_publication_ready_packages() -> None:
    module = importlib.import_module("med_autoscience.study_runtime_analysis_bundle")

    packages = set(module.DEFAULT_R_ANALYSIS_BUNDLE_PACKAGES)

    assert {
        "ggplot2",
        "patchwork",
        "ggrepel",
        "ggsci",
        "cowplot",
        "pROC",
        "precrec",
        "dcurves",
        "ggsurvfit",
        "forestploter",
        "ComplexHeatmap",
        "circlize",
    }.issubset(packages)
