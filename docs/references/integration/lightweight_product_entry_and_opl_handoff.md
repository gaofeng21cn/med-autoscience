# Med Auto Science 集成参考：Generated Product Surface 与 OPL Handoff

Owner: `MedAutoScience`
Purpose: `Support MAS integration and OPL handoff understanding.`
State: `support_reference`
Machine boundary: Human-readable integration reference only; callable and generated-surface truth remains in `agent/`, contracts, schemas, source, tests, OPL handoff contracts, and read-model output.

## 1. 当前结论

MAS 不再维护 repo-local product-entry builder、status/workbench shell、CLI parser 或 MCP transport。产品入口由 OPL 从 MAS pack 编译/托管：公开调用绑定 canonical Stage，内部 authority 调用绑定 closed handler registry。

当前 machine-readable 输入是：

- `contracts/action_catalog.json`：六个公开 Stage action、一个内部 authority action、schema 与 authority boundary；
- `contracts/domain_handler_registry.json`：无用户 surface 的最小 authority callable binding；
- `contracts/generated_surface_handoff.json`：generated surface owner 与 forbidden writes；
- `contracts/domain_descriptor.json`、`contracts/pack_compiler_input.json`：package/compiler input；
- `agent/`：MAS stage、skill、prompt、knowledge 和 quality-gate semantics。

公开 action 的 execution binding 统一指向：

```text
agent/stages/manifest.json#<canonical_stage_id>
```

内部 `paper_mission_authority_evaluate` 只通过 `handler:mas.paper-mission-authority-evaluate` 解析到纯 callable。旧 `MedAutoScienceDomainEntry.dispatch` 不再是 V2 generated/default target；仍有 active caller 的源码属于待迁 residue。

`product-entry-status`、`workspace-cockpit`、`product-entry-manifest`、`progress-projection`、`build-product-entry` 和旧 `medautosci product build-entry` 不是当前 MAS action id，也不是 repo-local executable truth。它们只能作为 OPL generated/hosted surface identity、retired migration identity 或 provenance 出现。

## 2. 两条集成路径

- Direct MAS app skill：
  `User/Agent -> MAS primary skill -> OPL generated Stage action -> OPL Stage runtime -> MAS owner surface`

- OPL stage handoff：
  `User/Agent -> OPL stage runtime -> StageRun/receipt/projection -> MAS owner surface`

两条路径共享相同的 Stage action、input/output schema、study semantics、authority boundary 和 return surface。内部 authority callable 是 host-only binding，不形成第三条用户入口。它们不共享第二套 CLI/MCP implementation。

## 3. Owner split

- OPL 持有 generated CLI/MCP/Skill/product/status/workbench、stage attempt、queue/wakeup、retry/dead-letter、generic lifecycle 和 operator projection。
- MAS 持有医学 study truth、source readiness、publication quality、artifact/package authority、memory accept/reject、owner receipt、typed blocker 和最小 authority functions。
- OPL generated surface 必须按 catalog 的 Stage binding 执行；host-only authority 调用必须按 closed registry 解析，并原样提交 exact result。两者都不得越权写 `publication_eval`、`controller_decisions`、memory body、source body、artifact authority 或 `current_package`。

`MedDeepScientist` 只保留为 source provenance、historical fixture、explicit archive import、backend audit、upstream intake 或 parity oracle reference；`Hermes-Agent` 只可指外部 runtime 项目/服务、显式 proof lane 或历史 provenance。

## 4. Handoff envelope

公开 Stage action 的 payload 以 V2 closed schema 为准，包含 workspace/study identity、用户意图和 typed input/route/human-gate refs。内部 authority payload 则包含 host context、mission、medical evidence、independent review、repair 与 hard-gate records。字段是否 required 只以 catalog 和对应 V2 schema 为准，不从本文复制成第二真相源。

## 5. 当前入口读法

- `direction_and_route_selection`：选定当前最有价值的研究方向或 route-back；
- `baseline_and_evidence_setup`：建立研究基线、source/evidence 边界与缺口；
- `bounded_analysis_campaign`：执行有界分析与证据增量；
- `manuscript_authoring`：形成或修订可审阅稿件增量；
- `review_and_quality_gate`：独立 cross-Stage Meta Review 与 defect-owner route；
- `finalize_and_publication_handoff`：收口出版交付与外部 human gate；
- `paper_mission_authority_evaluate`：host-only authority callable，无 CLI/MCP/Skill/product surface。

V1 `submit_study_task`、`launch_study`、`study_progress`、`paper_mission`、`mainline_*` 与 `domain_handler_export/dispatch` 不再是 public/default action。遗留内部 caller 必须通过 source-closure 与 physical-retirement gate 迁移，不得通过文档恢复为用户命令。

## 6. Ready 边界

Generated interface parity、schema valid、handler resolution 和 OPL scaffold validation只证明结构/dispatch currentness。它们不证明 runtime live、paper progress、publication-ready、artifact mutation authority、owner acceptance 或 production ready。

真实 readiness 继续要求相应 live readback、artifact、owner receipt、quality gate receipt、typed blocker、human gate 或 route-back evidence。
