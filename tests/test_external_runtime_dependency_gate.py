from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_external_runtime_dependency_gate_doc_lists_required_surfaces_and_blockers() -> None:
    content = _read("docs/program/external_runtime_dependency_gate.md")

    required_terms = (
        "EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB",
        "MEDICAL_FORK_MANIFEST.json",
        "behavior_equivalence_gate.yaml",
        "doctor",
        "hermes-runtime-check",
        "backend-upgrade-check",
        "inspect_workspace_contracts",
        "inspect_hermes_runtime_contract",
        "inspect_behavior_equivalence_gate",
        "study ensure-runtime",
        "waiting_for_user",
        "endpoint_provenance_note.md",
        "Methods",
    )

    for term in required_terms:
        assert term in content


def test_external_runtime_dependency_gate_is_linked_from_mainline_entry_docs() -> None:
    doc_name = "external_runtime_dependency_gate.md"

    mainline = _read("docs/program/research_foundry_medical_mainline.md")
    execution_map = _read("docs/program/research_foundry_medical_execution_map.md")
    activation = _read("docs/program/integration_harness_activation_package.md")
    merge_gates = _read("docs/program/merge_and_cutover_gates.md")
    agent_runtime = _read("docs/runtime/agent_runtime_interface.md")

    assert doc_name in mainline
    assert doc_name in execution_map
    assert doc_name in activation
    assert doc_name in merge_gates
    assert doc_name in agent_runtime


def test_external_runtime_dependency_gate_keeps_repo_side_and_external_evidence_distinct() -> None:
    content = _read("docs/program/external_runtime_dependency_gate.md")

    assert "Repo-side canonical evidence surface" in content
    assert "当前仍然必须由 external surface 提供的证据" in content
    assert "repo 内不再需要伪造新的 same-repo tranche" in content
