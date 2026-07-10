# Med Auto Science 集成参考：Generated Product Surface 与 OPL Handoff

Owner: `MedAutoScience`
Purpose: `Support MAS integration and OPL handoff understanding.`
State: `support_reference`
Machine boundary: Human-readable integration reference only; callable and generated-surface truth remains in `agent/`, contracts, schemas, source, tests, OPL handoff contracts, and read-model output.

## 1. 当前结论

MAS 不再维护 repo-local product-entry builder、status/workbench shell、CLI parser 或 MCP transport。产品入口载荷由 OPL 从 MAS pack 编译/托管，再 dispatch 到 MAS domain handler target。

当前 machine-readable 输入是：

- `contracts/action_catalog.json`：22 个 action id、handler target、schema 与 authority boundary；
- `contracts/generated_surface_handoff.json`：generated surface owner 与 forbidden writes；
- `contracts/domain_descriptor.json`、`contracts/pack_compiler_input.json`：package/compiler input；
- `agent/`：MAS stage、skill、prompt、knowledge 和 quality-gate semantics。

普通 action 的 handler target 统一为：

```text
med_autoscience.domain_entry:MedAutoScienceDomainEntry.dispatch#<action_id>
```

`product-entry-status`、`workspace-cockpit`、`product-entry-manifest`、`progress-projection`、`build-product-entry` 和旧 `medautosci product build-entry` 不是当前 MAS action id，也不是 repo-local executable truth。它们只能作为 OPL generated/hosted surface identity、retired migration identity 或 provenance 出现。

## 2. 两条集成路径

- Direct MAS app skill：
  `User/Agent -> MAS primary skill -> OPL generated action surface -> MAS domain handler`

- OPL stage handoff：
  `User/Agent -> OPL stage runtime -> StageRun/receipt/projection -> MAS handoff envelope -> MAS domain handler`

两条路径共享相同的 action id、input/output schema、study semantics、authority boundary 和 return surface。它们不共享第二套 CLI/MCP implementation。

## 3. Owner split

- OPL 持有 generated CLI/MCP/Skill/product/status/workbench、stage attempt、queue/wakeup、retry/dead-letter、generic lifecycle 和 operator projection。
- MAS 持有医学 study truth、source readiness、publication quality、artifact/package authority、memory accept/reject、owner receipt、typed blocker 和最小 authority functions。
- OPL generated surface 必须 dispatch 到 catalog 声明的 MAS handler target，且不得写 `publication_eval`、`controller_decisions`、memory body、source body、artifact authority 或 `current_package`。

`MedDeepScientist` 只保留为 source provenance、historical fixture、explicit archive import、backend audit、upstream intake 或 parity oracle reference；`Hermes-Agent` 只可指外部 runtime 项目/服务、显式 proof lane 或历史 provenance。

## 4. Handoff envelope

`OPL -> MAS` 最小 envelope 继续包含：

- `target_domain_id`
- `task_intent`
- `entry_mode`
- `workspace_locator`
- `domain_authority_handoff_contract`
- `managed_runtime_contract`
- `return_surface_contract`
- `domain_entry_contract`
- `user_interaction_contract`

医学研究域按 action schema 补充 `profile_ref`、`study_id`、`journal_target`、`evidence_boundary` 等字段。字段是否 required 以 `contracts/action_catalog.json` 和 input schema 为准，不从本文复制成第二真相源。

## 5. 当前入口读法

- `submit_study_task`：durable study task intake；
- `launch_study`：提交 MAS launch handoff，由 OPL hydrate；
- `study_progress` / `study_state_matrix` / `paper_mission`：refs-only readback；
- `domain_handler_export`：向 OPL 导出 MAS-owned projection 与 pending typed tasks；
- `domain_handler_dispatch`：消费 OPL typed task；不得生成 runtime queue row、provider attempt、owner receipt 或 publication verdict。

其他医学 action 直接读取 catalog。catalog 中不存在的旧命令不得通过文档恢复。

## 6. Ready 边界

Generated interface parity、schema valid、handler resolution 和 OPL scaffold validation只证明结构/dispatch currentness。它们不证明 runtime live、paper progress、publication-ready、artifact mutation authority、owner acceptance 或 production ready。

真实 readiness 继续要求相应 live readback、artifact、owner receipt、quality gate receipt、typed blocker、human gate 或 route-back evidence。
