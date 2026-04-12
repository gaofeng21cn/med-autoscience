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

    for doc in [readme, readme_zh, positioning, runtime_interface, runtime_contract]:
        assert "Codex-default host-agent runtime" in doc

    for doc in [positioning, runtime_interface, runtime_contract]:
        assert "Hermes" in doc
        assert "MedDeepScientist" in doc
        assert "controlled research backend" in doc
        assert "runtime_binding.yaml" in doc

    for doc in [runtime_interface, runtime_contract]:
        assert "research_backend_id" in doc
        assert "research_engine_id" in doc

    assert "research-foundry-medical-mainline" in readme
    assert "managed runtime handle" in readme
    assert "live daemon run handle" in readme
    assert "repo-side outer-runtime seam" in readme
    assert "not a landed upstream `Hermes-Agent` runtime" in readme
    assert "standalone host replacement continues through that gate" in readme
    assert "physician-friendly updates" in readme

    assert "research-foundry-medical-mainline" in readme_zh
    assert "受控 research backend quest 正式运行句柄" in readme_zh
    assert "live daemon run" in readme_zh
    assert "本地 operator handoff surface" in readme_zh
    assert "repo-side 外层 runtime seam" in readme_zh
    assert "不等于上游 `Hermes-Agent` runtime 已经落地" in readme_zh
    assert "独立上游 `Hermes-Agent` host 对 backend engine 的完整替代" in readme_zh
    assert "医生/PI 能读的人话进度" in readme_zh


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
    assert "hermes_backend_continuation_board.md" in docs_index
    assert "hermes_backend_continuation_board.md" in docs_index_zh
    assert "hermes_backend_activation_package.md" in docs_index
    assert "hermes_backend_activation_package.md" in docs_index_zh
    assert "med_deepscientist_deconstruction_map.md" in docs_index
    assert "med_deepscientist_deconstruction_map.md" in docs_index_zh


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
    hermes_board = _read("docs/program/hermes_backend_continuation_board.md")
    hermes_activation = _read("docs/program/hermes_backend_activation_package.md")
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
    assert "callable" in runtime_backend_contract

    for doc in [hermes_board, hermes_activation]:
        assert "Hermes" in doc
        assert "outer runtime substrate owner" in doc
        assert "external" in doc
        assert "blocker" in doc

    assert "promotion invariants" in hermes_board
    assert "excluded scope" in hermes_board
    assert "runtime_binding.yaml" in hermes_activation
    assert "runtime_backend_id = hermes" in hermes_activation

    assert "上游 `Hermes-Agent` 目标 + repo-side outer-runtime seam" in runtime_cutover
    assert "repo-side outer-runtime seam" in runtime_cutover
    assert "仓内已落地独立 Hermes-Agent host" in runtime_cutover
    assert "P2 controlled cutover -> physical monorepo migration" in runtime_cutover
    assert "deconstruction map" in runtime_cutover
    assert "physical migration" in runtime_cutover

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

    assert "The external runtime gate now sits as a concrete external blocker inside `P2`" in readme
    assert "external runtime gate 仍然存在" in readme_zh
    assert "part of the blocker package" in docs_index
    assert "属于 blocker package" in docs_index_zh


def test_hermes_backend_docs_are_linked_from_mainline_execution_and_runtime_entry_docs() -> None:
    mainline = _read("docs/program/research_foundry_medical_mainline.md")
    execution_map = _read("docs/program/research_foundry_medical_execution_map.md")
    activation = _read("docs/program/integration_harness_activation_package.md")
    runtime_interface = _read("docs/runtime/agent_runtime_interface.md")

    for doc in [mainline, execution_map, activation, runtime_interface]:
        assert "hermes_backend_continuation_board.md" in doc
        assert "hermes_backend_activation_package.md" in doc
        assert "med_deepscientist_deconstruction_map.md" in doc


def test_study_runtime_orchestration_doc_tracks_generic_managed_runtime_transport_contract() -> None:
    orchestration = _read("docs/runtime/study_runtime_orchestration.md")

    assert "managed_runtime_transport" in orchestration
    assert "managed_runtime_backend" in orchestration
    assert "med_deepscientist_transport" in orchestration
    assert "兼容别名" in orchestration
    assert "daemon 调用绑定收口为独立内部层" in orchestration


def test_runtime_mainline_docs_freeze_hermes_topology_and_display_exclusion() -> None:
    mainline = _read("docs/program/research_foundry_medical_mainline.md")
    execution_map = _read("docs/program/research_foundry_medical_execution_map.md")
    merge_gates = _read("docs/program/merge_and_cutover_gates.md")
    external_gate = _read("docs/program/external_runtime_dependency_gate.md")

    for doc in [mainline, execution_map, merge_gates, external_gate]:
        assert "Hermes" in doc
        assert "MedDeepScientist" in doc
        assert "EXTERNAL_RUNTIME_DEPENDENCY_BLOCKED_AFTER_ABSORB" in doc

    for doc in [mainline, execution_map, merge_gates]:
        assert "display" in doc

    assert "outer runtime substrate owner" in mainline
    assert "outer runtime substrate owner" in execution_map
    assert "runtime cutover gate" in merge_gates
    assert "external `Hermes` runtime" in external_gate


def test_core_docs_explain_hermes_integrated_research_progression_without_overclaiming() -> None:
    architecture = _read("docs/architecture.md")
    project = _read("docs/project.md")
    runtime_interface = _read("docs/runtime/agent_runtime_interface.md")

    assert "问题定义 -> startup boundary -> repo-side outer-runtime seam -> publication gate -> study completion sync" in architecture
    assert "这套机制把研究推进拆成一串 fail-closed gate" in architecture
    assert "一步步逼近 SCI-ready 投稿态" in architecture
    assert "相对只依赖 `MedDeepScientist` 的版本，逻辑上不是降级" in architecture
    assert "outer-loop / inner-loop coordination" in architecture
    assert "supervisor_tick_audit" in architecture
    assert "managed_runtime_supervision_gap" in architecture
    assert "details projection" in architecture

    assert "SCI-ready 投稿态" in project
    assert "fail-closed gate" in project
    assert "当前仓内的 `Hermes` 首先只是 repo-side outer substrate seam" in project
    assert "宿主机尚无 external `Hermes-Agent`" in project

    assert "study charter / startup boundary / publication gate / completion sync" in runtime_interface
    assert "不是把判断继续藏在 inner runtime 里" in runtime_interface
    assert "repo-side real adapter" in runtime_interface
    assert "独立安装的 Hermes daemon" in runtime_interface


def test_entry_docs_freeze_lightweight_product_entry_and_opl_handoff_without_crossing_external_gate() -> None:
    readme = _read("README.md")
    readme_zh = _read("README.zh-CN.md")
    docs_index = _read("docs/README.md")
    docs_index_zh = _read("docs/README.zh-CN.md")
    project = _read("docs/project.md")
    architecture = _read("docs/architecture.md")
    status = _read("docs/status.md")
    handoff = _read("docs/references/lightweight_product_entry_and_opl_handoff.md")

    assert "`operator entry` and `agent entry`" in readme
    assert "`product entry`: not landed yet as a mature direct user-facing entry" in readme
    assert "`User -> Med Auto Science Product Entry -> Med Auto Science Gateway -> Hermes Kernel -> Med Auto Science Domain Harness OS`" in readme
    assert "`User -> OPL Product Entry -> OPL Gateway -> Hermes Kernel -> Domain Handoff -> Med Auto Science Product Entry / Med Auto Science Gateway`" in readme

    assert "`operator entry` 和 `agent entry`" in readme_zh
    assert "`product entry`：真正成熟的 direct user-facing 入口还没有落地" in readme_zh
    assert "`OPL -> Med Auto Science`" in architecture

    assert "operator entry" in docs_index
    assert "lightweight medical direct entry" in docs_index
    assert "references/lightweight_product_entry_and_opl_handoff.md" in docs_index
    assert "operator entry" in docs_index_zh
    assert "轻量医学 `product entry`" in docs_index_zh
    assert "references/lightweight_product_entry_and_opl_handoff.md" in docs_index_zh

    assert "lightweight medical `product entry`" in project
    assert "target_domain_id" in architecture
    assert "study_id" in architecture
    assert "journal_target" in architecture
    assert "evidence_boundary" in architecture
    assert "OPL -> Med Auto Science" in status

    assert "target_domain_id" in handoff
    assert "task_intent" in handoff
    assert "entry_mode" in handoff
    assert "workspace_locator" in handoff
    assert "runtime_session_contract" in handoff
    assert "return_surface_contract" in handoff
    assert "study_id" in handoff
    assert "journal_target" in handoff
    assert "evidence_boundary" in handoff
    assert "真实 external runtime gate" in handoff
    assert "不能把 repo-side seam 写成“上游 `Hermes-Agent` 已经完整接管”" in handoff
