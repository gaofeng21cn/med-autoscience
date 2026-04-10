from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_activation_package_freezes_required_chain_and_artifacts() -> None:
    content = _read("docs/integration_harness_activation_package.md")

    required_terms = (
        "controller -> runtime -> eval -> delivery",
        "launch_report",
        "runtime_escalation_record",
        "publication_eval",
        "study_decision_record",
        "runtime_watch",
        "publication_gate",
        "study_delivery_sync",
        "end-to-end study harness",
        "behavior-equivalence",
        "med-deepscientist",
        "cross-repo write",
    )

    for term in required_terms:
        assert term in content


def test_activation_package_is_linked_from_current_repo_tracked_entry_docs() -> None:
    mainline = _read("docs/research_foundry_medical_mainline.md")
    execution_map = _read("docs/research_foundry_medical_execution_map.md")
    agent_runtime = _read("docs/agent_runtime_interface.md")

    assert "integration_harness_activation_package.md" in mainline
    assert "integration_harness_activation_package.md" in execution_map
    assert "integration_harness_activation_package.md" in agent_runtime


def test_merge_and_cutover_doc_keeps_cutover_gate_separate_from_activation_package() -> None:
    content = _read("docs/merge_and_cutover_gates.md")

    assert "integration harness activation package" in content
    assert "runtime cutover gate" in content
    assert "behavior equivalence gate" in content


def test_activation_and_cutover_closeout_docs_record_external_blocker_as_already_absorbed() -> None:
    activation = _read("docs/integration_harness_activation_package.md")
    merge_gates = _read("docs/merge_and_cutover_gates.md")

    assert "2026-04-10" in activation
    assert "absorbed closeout commit" in activation
    assert "70dc19fe4001b6eddda14e9b7a00e79a30d79ab1" in activation

    assert "external runtime dependency gate" in merge_gates
    assert "EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB" in merge_gates
    assert "未 absorb 的 same-repo tranche" in merge_gates
