# MAS Stage / Route / Handoff 标准

Owner: `MedAutoScience`
Purpose: `stage_route_handoff_and_outcome_standard`
State: `active_current_truth`
Machine boundary: 机器真相归 `agent/stages/manifest.json`、`agent/stages/stage_route_contract.yaml`、`contracts/action_catalog.json`、`contracts/stage_run_kernel_profile.json`、`contracts/stage_quality_cycle_policy.json`、`contracts/mas-paper-study-stage-pack.json` 与 OPL StageRun/Attempt contracts。

## 六个 canonical Stage 与合同来源

1. `direction_and_route_selection`
2. `baseline_and_evidence_setup`
3. `bounded_analysis_campaign`
4. `manuscript_authoring`
5. `review_and_quality_gate`
6. `finalize_and_publication_handoff`

- `agent/stages/manifest.json` 定义六个 canonical Stage 与 prompt/knowledge/policy；`contracts/action_catalog.json` 将公开 action 绑定至 manifest（旧短 route id 不作 public action alias）；`agent/stages/stage_route_contract.yaml` 持有研究 route 语义、evidence obligations 与 progress-first policy；`contracts/mas-paper-study-stage-pack.json` 持有论文物理 artifact 阶段（非另一套运行路由）。已退役的 route/transition surface 不形成第二 Stage graph（见 [约束](../invariants.md#退役与兼容)）。

## Authority Split 与 Progress-First Outcome

- `semantic_route_decision_owner=decisive_codex_attempt`
- `stage_transition_materialization_owner=opl_stage_run_controller`

Primary-only StageRun 的 producer 是 decisive Attempt。Formal Review StageRun 只有终局 reviewer / re-reviewer 是 decisive Attempt；在这种 StageRun 内 producer、repairer 始终只能给 recommendation。仍有 repair budget 且缺陷可在当前 Stage 修复时，`repair_required` reviewer 也只给 recommendation；若最窄 canonical owner 是另一个 declared Stage，则 reviewer / re-reviewer 可提前以 `repair_required + route_back` 终结当前 StageRun（预算耗尽前唯一允许的终局 `repair_required` 路由）。预算耗尽且 artifact 可消费时，终局 reviewer / re-reviewer 给 route decision，controller 以 `completed_with_quality_debt` 物化。

每个 stage attempt 必须形成可接力 outcome，至少绑定 `program_id`、`study_id`、`quest_id`、`active_run_id`、stage/attempt identity、outcome kind、owner 与 required output、evidence/artifact refs 及 receipt/blocker/human-gate ref 与 forbidden-write boundary（默认下一步只从 `Codex CLI selected stage -> nonbinding route context` 产生；不得从旧 provider/current-work-unit projection 拼接下一步）：

| 结果类型 | 是否算 domain progress |
| --- | --- |
| canonical paper/evidence/artifact semantic delta | 是，需 owner receipt |
| stable typed blocker with owner route / human gate with resume contract | 是，合法可接力停点或阻断 |
| independent reviewer/auditor receipt | 是，按 verdict/route-back 解释 |
| projection / StateIndex / workbench repair（无领域产物）、queue empty、attempt/provider completed、docs/tests pass | 否 |

OPL controller 只验证角色资格、declared target、identity、lineage 与 exact hashes，然后记录 transition；MAS authority function 只处理 host 注入的医学 owner boundary，不启动 runtime、不写 session、不物化 transition。

## 独立质量循环

产生开放领域判断或 canonical bytes 的前四个 Stage 启用 formal Review；producer 同线程的写后检查仅是 `in_thread_refinement`。reviewer、repairer 与 re-reviewer 均使用新 Attempt/session，输入只有 exact artifact/source/rubric 和必要 lineage refs，不继承 producer conversation。

默认最多三轮 `repairer + re_reviewer`，provider/dispatch retry 和协议补全不占语义修复预算。Attempt 的 outcome 仅为 `pass`、`repair_required`、`quality_debt`、`blocked` 或 `human_gate`；Framework receipt 才将后两者映射为 `hard_stop`。

`review_and_quality_gate` 是独立 cross-Stage Meta Review，不递归创建 Review，也不在 reviewer 会话内修改稿件。`finalize_and_publication_handoff` 是 primary-only 机械 inspection packaging，不签 quality/export/publication/ready；二者各自的 producer 是 decisive Attempt，但 Handoff 的 route 权不扩张交付 authority。内容缺陷回到最早 owner Stage，变化后重新完成受影响 Stage Review 和 Meta Review；`strategy_retrospective` 只提供非权威方法学习，不替代上述 Review。

## Handoff 与 Stop Conditions

Handoff 是 body-free refs 与 evidence 的交接，不是 MAS 私有 queue 或 runner。Handoff 的 `publication_generation` 绑定 exact package bytes、`submission/STATUS.json`、`artifacts/publication_eval/latest.json`、`control/next_action.json` 与 projection manifest；MAS owner receipt 只有在这些成员与六域 review currentness 属于同一 generation 时，才输出 `artifact_projection_transport` authorization。Framework `opl_pack_materialize_artifact_projection` 在 sibling staging 校验完整树后整树切换 `submission/`，transport 成功不生成或提升领域 verdict。

普通质量缺口在预算耗尽且 artifact 可消费时进入 `completed_with_quality_debt`，关闭对应 quality/ready claim 但继续推进；只有真实 authority/safety/identity/currentness/credential/irreversible/human gate，或在 diagnostic 尝试后仍无任何可消费 artifact，才是 hard stop（成功物化的 no-output/failure diagnostic 本身可作为可消费进展 artifact）。Stage 仅在 owner receipt 确认 terminal outcome、stable typed blocker 已绑定 owner route、human gate 已有明确 resume input、independent reviewer route-back 已记录或 stop-loss 获 MAS owner 明确授权时合法停止。

## 相关入口与验证

详见 [Runtime 边界](./runtime_boundary.md)、[质量循环](./progress_first_quality_loop.md)、[约束](../invariants.md) 与 [开放计划](../active/mas-ideal-state-gap-plan.md)。运行 `scripts/verify.sh full` 并在冻结 Framework 读取单仓 interfaces/conformance/default-callers/residue/source-closure；结构绿不替代真实 StageRun、Review receipt、owner result 或 paper artifact evidence。
