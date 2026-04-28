from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs" / "program" / "integration_harness_activation_package.md"


def _doc_text() -> str:
    return DOC.read_text(encoding="utf-8")


def test_integration_harness_activation_package_preserves_absorbed_blocker_status() -> None:
    text = _doc_text()

    assert "EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB" in text
    assert "`end-to-end study harness` 已开启的声明" in text
    assert "`runtime cutover` 已放行的声明" in text
    assert "`behavior-equivalence` 已通过的声明" in text
    assert "对 `med-deepscientist` 写入、cross-repo write、external workspace writer widening 的授权" in text


def test_integration_harness_activation_package_keeps_repo_native_proof_surface_explicit() -> None:
    text = _doc_text()

    for proof_surface in (
        "tests/test_runtime_watch.py",
        "tests/test_study_delivery_sync.py",
        "tests/test_publication_gate.py",
        "tests/test_integration_harness_activation_package.py",
        "tests/test_dev_preflight_contract.py",
        "tests/test_dev_preflight.py",
    ):
        assert proof_surface in text

    for chain_surface in (
        "study_runtime_status / ensure_study_runtime",
        "launch_report",
        "runtime_escalation_record",
        "publication_eval",
        "study_outer_loop_tick",
        "study_decision_record",
        "runtime_watch",
        "publication_gate",
        "study_delivery_sync",
    ):
        assert chain_surface in text
