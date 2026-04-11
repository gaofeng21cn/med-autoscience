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
    assert "runtime_backend_interface_contract.md" in docs_index
    assert "runtime_backend_interface_contract.md" in docs_index_zh
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
    runtime_backend_contract = _read("docs/runtime/runtime_backend_interface_contract.md")
    runtime_contract = _read("docs/runtime/runtime_event_and_outer_loop_input_contract.md")
    runtime_cutover = _read("docs/runtime/runtime_core_convergence_and_controlled_cutover.md")
    workspace_knowledge = _read("docs/runtime/workspace_knowledge_and_literature_contract.md")

    assert "runtime native truth convergence" in priority_map
    assert "workspace knowledge and literature convergence" in priority_map
    assert "controlled cutover -> physical monorepo migration" in priority_map
    assert "先完成 `runtime native truth convergence`" in priority_map
    assert "再完成 `workspace knowledge and literature convergence`" in priority_map
    assert "当前剩余的 active tranche" in priority_map
    assert "P0：Runtime Native Truth 已完成" in priority_map
    assert "P1：Workspace Knowledge / Literature 已完成" in priority_map

    assert "quest-owned native runtime truth" in runtime_contract
    assert "study-owned outer-loop truth" in runtime_contract
    assert "runtime_event_ref" in runtime_contract
    assert "supervisor_tick_audit.status" in runtime_contract
    assert "不得再由 `study_runtime_status`" in runtime_contract

    assert "runtime backend interface" in runtime_backend_contract
    assert "runtime_backend_id" in runtime_backend_contract
    assert "runtime_engine_id" in runtime_backend_contract
    assert "如果 `execution.runtime_backend_id`" in runtime_backend_contract
    assert "Hermes" in runtime_backend_contract

    assert "cb73b3d21c404d424e57d7765b5a9a409060700a" in runtime_cutover
    assert "consumer-side cutover" in runtime_cutover
    assert "P2 controlled cutover -> physical monorepo migration" in runtime_cutover
    assert "Cross-repo parity gate" in runtime_cutover

    assert "portfolio/research_memory" in workspace_knowledge
    assert "canonical knowledge / literature truth" in workspace_knowledge
    assert "studies/<study_id>/artifacts/reference_context/latest.json" in workspace_knowledge
    assert "materialized working copy" in workspace_knowledge
    assert "workspace-first" in workspace_knowledge
    assert "`P1` 的正式完成态" in workspace_knowledge


def test_public_entry_docs_surface_current_p0_p1_done_and_p2_active() -> None:
    readme = _read("README.md")
    readme_zh = _read("README.zh-CN.md")
    docs_index = _read("docs/README.md")
    docs_index_zh = _read("docs/README.zh-CN.md")

    for doc in [readme, readme_zh, docs_index, docs_index_zh]:
        assert "P0 runtime native truth" in doc
        assert "P1 workspace canonical literature / knowledge truth" in doc
        assert "P2 controlled cutover -> physical monorepo migration" in doc

    assert "external runtime gate still exists" in readme
    assert "external runtime gate 仍然存在" in readme_zh
    assert "part of the blocker package" in docs_index
    assert "属于 blocker package" in docs_index_zh
