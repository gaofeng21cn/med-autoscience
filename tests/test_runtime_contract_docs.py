from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_public_and_internal_runtime_contract_docs_freeze_handle_and_surface_semantics() -> None:
    readme = _read("README.md")
    readme_zh = _read("README.zh-CN.md")
    project_truth = _read("contracts/project-truth/AGENTS.md")
    positioning = _read("docs/domain-harness-os-positioning.md")
    runtime_interface = _read("docs/agent_runtime_interface.md")
    runtime_contract = _read("docs/runtime_handle_and_durable_surface_contract.md")

    for doc in [readme, project_truth, positioning, runtime_interface, runtime_contract]:
        assert "Codex-default host-agent runtime" in doc
        assert "CLI" in doc
        assert "MCP" in doc
        assert "controller" in doc
        assert "Auto-only" in doc
        assert "program_id" in doc
        assert "study_id" in doc
        assert "quest_id" in doc
        assert "active_run_id" in doc
        assert "study_runtime_status" in doc
        assert "runtime_watch" in doc
        assert "publication_eval/latest.json" in doc
        assert "runtime_escalation_record.json" in doc
        assert "controller_decisions/latest.json" in doc

    assert "research-foundry-medical-mainline" in readme
    assert "managed runtime handle" in readme
    assert "live daemon run handle" in readme

    assert "research-foundry-medical-mainline" in readme_zh
    assert "managed quest" in readme_zh
    assert "live daemon run" in readme_zh
    assert "本地 operator handoff surface" in readme_zh


def test_docs_index_tracks_runtime_contract_doc_as_internal_operator_surface() -> None:
    docs_index = _read("docs/README.md")
    docs_index_zh = _read("docs/README.zh-CN.md")

    assert "runtime_handle_and_durable_surface_contract.md" in docs_index
    assert "runtime_handle_and_durable_surface_contract.md" in docs_index_zh
    assert "runtime_event_and_outer_loop_input_contract.md" in docs_index
    assert "runtime_event_and_outer_loop_input_contract.md" in docs_index_zh
    assert "runtime_event_and_outer_loop_input_implementation_plan.md" in docs_index
    assert "runtime_event_and_outer_loop_input_implementation_plan.md" in docs_index_zh


def test_monorepo_longrun_goal_stays_explicit_but_postponed_behind_runtime_gates() -> None:
    project_truth = _read("contracts/project-truth/AGENTS.md")
    runtime_interface = _read("docs/agent_runtime_interface.md")
    positioning = _read("docs/research_foundry_positioning.md")

    for doc in [project_truth, runtime_interface, positioning]:
        assert "monorepo / runtime core ingest / controlled cutover" in doc

    assert "external runtime gate" in project_truth
    assert "external runtime gate" in runtime_interface
    assert "controller_charter" in runtime_interface
    assert "eval_hygiene" in runtime_interface
    assert "physical migration" in runtime_interface
    assert "cross-repo refactor" in runtime_interface

    assert "contract convergence" in positioning
    assert "behavior convergence" in positioning
    assert "domain-internal 长线" in positioning
    assert "不是放弃 monorepo" in positioning


def test_public_entry_docs_surface_external_gate_stop_state() -> None:
    readme = _read("README.md")
    readme_zh = _read("README.zh-CN.md")
    docs_index = _read("docs/README.md")
    docs_index_zh = _read("docs/README.zh-CN.md")

    for doc in [readme, readme_zh, docs_index, docs_index_zh]:
        assert "EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB" in doc
        assert "external_runtime_dependency_gate.md" in doc

    assert "new in-repo architecture tranche" in readme
    assert "新的仓内架构 tranche" in readme_zh
    assert "open in-repo implementation baton" in docs_index
    assert "正在仓内继续实现的 active tranche" in docs_index_zh
