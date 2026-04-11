from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_manual_runtime_stabilization_doc_lists_stable_surfaces_and_external_blockers() -> None:
    content = _read("docs/program/manual_runtime_stabilization_checklist.md")

    required_terms = (
        "EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB",
        "doctor --profile <profile>",
        "med-deepscientist-upgrade-check --profile <profile> --refresh",
        "study-runtime-status --profile <profile> --study-id <study_id>",
        "ensure-study-runtime --profile <profile> --study-id <study_id>",
        "study-progress --profile <profile> --study-id <study_id>",
        "watch --quest-root <quest_root> --apply",
        "publication-gate --quest-root <quest_root> --apply",
        "sync-study-delivery --paper-root <study_root>/paper --stage submission_minimal",
        "study_runtime_status",
        "runtime_escalation_record.json",
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "last_launch_report.json",
        "MEDICAL_FORK_MANIFEST.json",
        "behavior_equivalence_gate.yaml",
        "waiting_for_user",
        "endpoint_provenance_note.md",
        "Methods",
        "display / paper figure asset packaging",
    )

    for term in required_terms:
        assert term in content


def test_manual_runtime_stabilization_doc_is_linked_from_runtime_entry_docs() -> None:
    doc_name = "manual_runtime_stabilization_checklist.md"

    docs_index = _read("docs/README.md")
    docs_index_zh = _read("docs/README.zh-CN.md")
    agent_runtime = _read("docs/runtime/agent_runtime_interface.md")
    external_gate = _read("docs/program/external_runtime_dependency_gate.md")

    assert doc_name in docs_index
    assert doc_name in docs_index_zh
    assert doc_name in agent_runtime
    assert doc_name in external_gate


def test_merge_gate_worktree_wording_matches_project_truth() -> None:
    root_agents = _read("AGENTS.md")
    merge_gates = _read("docs/program/merge_and_cutover_gates.md")

    assert "worktree" in root_agents
    assert ".worktrees/" in merge_gates
