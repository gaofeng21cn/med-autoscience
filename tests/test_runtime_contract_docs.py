from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_public_and_internal_runtime_contract_docs_freeze_handle_and_surface_semantics() -> None:
    readme = _read("README.md")
    readme_zh = _read("README.zh-CN.md")
    root_agents = _read("AGENTS.md")
    positioning = _read("docs/references/domain-harness-os-positioning.md")
    runtime_interface = _read("docs/runtime/agent_runtime_interface.md")
    runtime_contract = _read("docs/runtime/runtime_handle_and_durable_surface_contract.md")

    for doc in [readme, root_agents, positioning, runtime_interface, runtime_contract]:
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
    assert "project_repair_priority_map.md" in docs_index
    assert "project_repair_priority_map.md" in docs_index_zh
    assert "runtime_core_convergence_and_controlled_cutover.md" in docs_index
    assert "runtime_core_convergence_and_controlled_cutover.md" in docs_index_zh
    assert "runtime_core_convergence_and_controlled_cutover_implementation_plan.md" in docs_index
    assert "runtime_core_convergence_and_controlled_cutover_implementation_plan.md" in docs_index_zh
    assert "workspace_knowledge_and_literature_contract.md" in docs_index
    assert "workspace_knowledge_and_literature_contract.md" in docs_index_zh
    assert "workspace_knowledge_and_literature_implementation_plan.md" in docs_index
    assert "workspace_knowledge_and_literature_implementation_plan.md" in docs_index_zh


def test_monorepo_longrun_goal_stays_explicit_but_postponed_behind_runtime_gates() -> None:
    root_agents = _read("AGENTS.md")
    runtime_interface = _read("docs/runtime/agent_runtime_interface.md")
    positioning = _read("docs/references/research_foundry_positioning.md")

    for doc in [root_agents, runtime_interface, positioning]:
        assert "monorepo / runtime core ingest / controlled cutover" in doc

    assert "external runtime gate" in root_agents
    assert "external runtime gate" in runtime_interface
    assert "controller_charter" in runtime_interface
    assert "eval_hygiene" in runtime_interface
    assert "physical migration" in runtime_interface
    assert "cross-repo refactor" in runtime_interface

    assert "contract convergence" in positioning
    assert "behavior convergence" in positioning
    assert "domain-internal 长线" in positioning
    assert "不是放弃 monorepo" in positioning


def test_project_repair_docs_freeze_priority_order_and_workspace_literature_boundary() -> None:
    priority_map = _read("docs/program/project_repair_priority_map.md")
    runtime_cutover = _read("docs/runtime/runtime_core_convergence_and_controlled_cutover.md")
    workspace_knowledge = _read("docs/runtime/workspace_knowledge_and_literature_contract.md")

    assert "runtime native truth convergence" in priority_map
    assert "workspace knowledge and literature convergence" in priority_map
    assert "controlled monorepo cutover" in priority_map
    assert "先完成 `runtime native truth convergence`" in priority_map
    assert "再完成 `workspace knowledge and literature convergence`" in priority_map
    assert "最后进入 `controlled monorepo cutover`" in priority_map

    assert "runtime_event" in runtime_cutover
    assert "runtime core 原生输出" in runtime_cutover
    assert "MAS 改为纯消费者" in runtime_cutover
    assert "EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB" in runtime_cutover
    assert "scaffold boundary" in runtime_cutover
    assert "launch_report" in runtime_cutover
    assert "runtime_watch" in runtime_cutover

    assert "portfolio/research_memory" in workspace_knowledge
    assert "canonical literature registry" in workspace_knowledge
    assert "studies/<study_id>/artifacts/reference_context/latest.json" in workspace_knowledge
    assert "quest hydration" in workspace_knowledge
    assert "materialized working copy" in workspace_knowledge
    assert "journal_shortlist_evidence" in workspace_knowledge
    assert "venue_intelligence" in workspace_knowledge


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
