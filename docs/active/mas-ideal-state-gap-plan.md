# MAS 理想目标态差距与完善计划

Owner: `MedAutoScience`
Purpose: `single_active_truth_plan`
State: `active_plan`
Machine boundary: 本文只持有当前结构摘要、开放差距、证据边界与下一轮 Agent prompt。机器事实归 `agent/`、`contracts/`、source、tests、OPL generated/readback surfaces、workspace artifacts 与 owner receipts。

## Ideal-State Reference

目标态以 [MAS 理想态](../references/positioning/mas_ideal_state.md) 为长期参考，并由
当前机器合同约束为：

> `Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal registry-bound authority functions`

canonical agent/package id 是 `mas`，machine domain id 是
`medautoscience`。OPL 持有通用 interface、runtime、transport、package lifecycle 与
projection；MAS 持有医学语义声明、专业能力依赖、独立 Review policy 和无法声明化的
最小 authority functions。

## Current State Summary

当前 audited source snapshot 的结构摘要如下：

| Theme | Current source evidence | Boundary |
| --- | --- | --- |
| Declarative pack | `agent/` 持有 primary skill、六个 Stage、prompts、knowledge 与 quality gates | pack 声明不等于 live StageRun |
| Action catalog | `contracts/action_catalog.json` 持有六个公开 Stage action 与两个无用户 surface 的内部 authority actions | public/generated surface currentness 仍归 OPL readback |
| Authority registry | `contracts/domain_handler_registry.json` 绑定 candidate admission、paper mission 与 self-evolution closeout 三个纯 handler | handler 只作领域裁决，不拥有 runtime、transport、session 或 transition |
| Source morphology | `src/med_autoscience/` 只保留 package init、三个 authority handlers、共享纯校验 helper 与 CSL assets | source closure 不等于 runtime、paper 或 publication ready |
| Package / ScholarSkills dependency | `contracts/opl_agent_package_manifest.json` 声明 MAS SemVer `0.2.19`、required dependency 范围 `>=0.2.12 <0.3.0` 和兼容 ABI/exports/modules；出版版式由 ScholarSkills 单一目录提供，MAS 只消费 selection ref | 缺失或不兼容使 MAS readiness fail-closed；exact closure、installed resolution、lock 与 activation 归 OPL package readback |

## Current-State vs Ideal-State Gaps

### Functional / Structural Gaps

State: `none_selected`

本轮未从 live contracts/source/tests 中选出新的 repo/source 结构差距。已关闭结构项
不继续作为完成清单保留在 active plan；如未来机器面重新出现 private runtime、重复
interface、第二 truth source 或越权 handler，应以新鲜 caller、owner、write-set 与
replacement evidence 重新立项。

### Test / Evidence Gaps

State: `partial_deferred`

以下 claim 必须由对应 owner surface fresh 证明，不能由本计划关闭：

| Claim | Required evidence |
| --- | --- |
| OPL runtime ready | same-identity StageRun/Attempt readback、provider running、restart/retry/dead-letter/long-soak |
| Paper progress | MAS owner receipt、stable typed blocker、human gate、route-back 或 paper/artifact semantic delta |
| Quality/publication ready | independent reviewer/auditor receipt、publication owner verdict 与 current artifact refs |
| Installed package current | `opl packages` authority readback，包括 resolved version、content lock、activation 与 lifecycle receipt |
| Submission/current package ready | submission authority、fresh manifest/package receipt 与 owner readback |
| Production ready | live runtime/readback 与 production no-forbidden-write proof |

## Next-Round Agent Prompt

下一轮可直接使用以下 autonomous baton：

```text
Objective: 从 MAS 理想态与当前 live repo truth 重新审计 Active Truth，只治理有
机器证据支持的开放差距，并保持 MAS domain authority 与 OPL platform authority 分离。

Write scope: docs/active/mas-ideal-state-gap-plan.md、受影响的 canonical/support docs，
以及关闭新证实差距所必需的 agent/contracts/src/tests；若存在其他 owner lane 的重叠
写集，只记录 blocker，不覆盖。

Non-goals: 不恢复 MAS-local runtime、CLI/MCP wrapper、queue、session store、StateIndex、
package installer、provider transport、workbench、retired entrypoint 或 duplicate facade；不把 docs、tests、
doctor、projection、candidate package、queue empty 或 dry-run 写成 runtime、paper、
publication、submission 或 production ready。

Live truth inputs: AGENTS.md；docs/references/positioning/mas_ideal_state.md；agent/；
contracts/action_catalog.json；contracts/domain_handler_registry.json；
contracts/opl_agent_package_manifest.json；src/med_autoscience/；tests/；scripts/verify.sh；
涉及运行或安装 currentness 时读取 fresh OPL StageRun/package/owner surfaces。

Required actions: 逐项比较理想态与机器面；将差距分类为 structural 或 evidence-only；
核对每个 current doc 的唯一语义 owner；删除 active docs 中的完成流水；只在 replacement
owner 与 no-active-caller evidence 成立时退役 stale surface；将仍开放项和下一 baton
写回本计划。

Verification commands: scripts/verify.sh；opl-doc-doctor doctor . --format json；
运行全仓 Markdown 相对链接扫描；git diff --check。涉及 OPL-owned runtime/package
claim 时另做对应 fresh readback，不从 repo checkout 反推。

Completion gate: 每个变更 claim 都有 machine/live evidence；本计划只含当前摘要、开放
差距和下一 baton；canonical docs 不再持有冲突的 handler/action/package 口径；相对
链接解析成功；repo-native 验证通过，或留下精确 owner/currentness/dependency blocker。

Foldback target: 稳定当前事实进入 docs/status.md、docs/architecture.md、
docs/invariants.md 或 docs/decisions.md；Stage/Review/route 边界进入对应 support doc；
历史过程只留 Git/docs/history；开放差距和下一 prompt 只留本文件。
```
