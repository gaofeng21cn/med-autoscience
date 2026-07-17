# 不可变约束

Owner: `MedAutoScience`
Purpose: `project_invariants`
State: `active_current_truth`
Machine boundary: 本文是人读约束；机器事实以 contracts、source、runtime durable surfaces、artifact 与 owner receipts 为准。

## 身份与 owner

- canonical agent/package id 是 `mas`；machine `domain_id` / `target_domain_id` 是 `medautoscience`；repo/package/plugin locator 是 `med-autoscience`。
- MAS 是 `Declarative Medical Research Pack + minimal registry-bound authority functions`；OPL 持有 generated/hosted platform surfaces。
- OPL 不得写 MAS study truth、quality/publication verdict、canonical artifact body、memory body 或 owner receipt。
- MAS 不得重新拥有 generic runtime、queue、attempt ledger、StateIndex、lifecycle/storage、observability、installer、CLI/MCP transport 或 workbench shell。
- MAS 只输出 typed runtime request / route handoff并消费 OPL host 注入的 canonical payload；不得解析 OPL binary、spawn CLI、主动 probe runtime 或把缺失 host receipt 解释为 submission success。

## Pack 与 generated surfaces

- `agent/` 是 canonical rich pack source；plugin carrier mirror 是分发要求，不是重复实现。
- V2 action catalog 当前包含六个公开 Stage action，以及 candidate admission、paper mission 两个无用户 surface 的内部 authority actions。closed handler registry 另绑定 self-evolution closeout。普通 interface 从 catalog/schema 生成，不在 MAS 新增手写 parser、JSON-RPC glue 或 duplicate descriptor。
- V2 generated/default interface 只绑定 Stage manifest 与 closed handler registry。旧 `domain_entry` 及其 status/read-model/queue caller 已物理退役，不得以 compatibility、diagnostic 或 test fixture 名义恢复为 active source。
- Foundry 系列 policy 归唯一 OPL Framework；MAS 只保留 canonical refs、policy fingerprint、domain delta 与 false-authority envelope，不复制 policy body，也不安装 Framework policy carrier。
- 环境依赖在 `contracts/runtime_environment_requirements.json` 声明；prepare/run 归 OPL。MAS 可保留 `mas_provisioning_allowed=false` 的只读环境检查/投影，但不在 import、workspace 或 installer 中安装、修复环境，也不授权 ready。
- `mas-scholar-skills` 是 MAS 硬依赖。核心 package、ABI 或任一必需 export 缺失/不兼容时必须 `operational_ready=false`，不得静默降级；安装、激活、修复、更新、锁定、回滚和依赖卸载保护统一归 `opl packages`。可选 named-specialty Skill 不进入该 readiness floor。

## Authority

- 领域 route 语义只由 decisive Codex Attempt 决定；OPL StageRun controller 只校验并物化 transition。Formal Review StageRun 的 producer/repairer/`same_stage_repair_required` reviewer 不得获得终局 route authority；primary-only StageRun 的 producer可以成为 decisive Attempt；`cross_stage_route_back_before_budget_exhaustion` reviewer/re-reviewer 只在最窄 canonical owner 是另一个 declared Stage 时成为终局 decisive Attempt。
- OPL transport/readback 只有传输权；同 identity 的 MAS owner consumption 才能解释 domain result。
- AI-first quality gate 必须消费独立 reviewer/auditor invocation 与 receipt；executor 不得自审并关闭质量门。
- publication、submission、artifact mutation、memory accept/reject 与 source readiness 必须由对应 MAS owner surface裁决。
- refs-only projection、schema、validator、test、workbench 可见性和 inventory presence 都不等于 authority verdict。

## Stage prompt 与专业顺序

- Stage 主提示词只承载本 Stage 的目标、好结果、关键专业依赖、authority 边界与 handoff 语义；专业方法细节归 `agent/skills/`、ScholarSkills 与 quality gate，工具能力归 affordance catalog。
- Codex 可自主选择工具、迭代、替代和安全并行，但不得颠倒会破坏 claim/estimand、source 或 failed-path provenance、fresh review/artifact proof、owner/human authority 或不可逆动作安全性的依赖顺序。
- 新外部 Skill 只用于明确或已证明的能力缺口；sync 前必须检查 identity、provenance、permissions、data/credential scope 与 compatibility。已安装且已检查的兼容 Skill 可直接复用，不要求重复固定搜索流程。
- 可消费 delta 在质量预算耗尽时以 `completed_with_quality_debt` 前进；成功物化的 no-output/failure diagnostic 本身可作为进展 artifact，字面上仍无任何可消费 artifact 时则硬停止。quality debt 阻断 quality/publication/export/submission-ready claim，不阻断普通 Stage transition。只有 executor unavailable、真实 authority/safety/identity/currentness/credential/irreversible/human decision 或零可消费 artifact 才成为硬 blocker。

## 退役与兼容

- 已被 OPL 或标准工具替代的 MAS-local wrapper、facade、installer、workspace initializer、runtime shell 和旧 next-action producer 直接退役；不新增 compatibility shim、alias 或聚合测试。
- 旧 provider admission、current work unit、PaperRecovery 与 domain-action request 只允许 tombstone/provenance/no-resurrection guard，不得恢复 current caller。
- MDS/DeepScientist 只作 provenance、explicit archive import、backend audit、upstream learning 与 parity oracle。
- Hermes-Agent 只作显式非默认 executor/proof lane；不宣称与 Codex CLI 行为或质量等价。

## Durable truth

- study/publication/display domain truth 归 MAS declarative policy、authority result 与 canonical artifact；runtime/transition truth 归 OPL durable surface；docs 只解释和导航。
- SQLite/index/read model 是可重建投影，不得替代 canonical files、owner receipts 或 artifact authority。
- status/workbench 只能读取 body-free refs、receipts、blockers 与 diagnostics，不得授权执行或变更 artifact。
- workspace 不依赖 MAS checkout 内 `.venv`；环境由 OPL substrate 和标准 package tooling 准备。

## External learning

- 外部框架默认是 pattern source/provenance。只有进入 MAS owner surface 或 OPL callable/generated surface并有 allowed/forbidden authority evidence，才可写成 landed。
- Scientific Capability Registry 与 advisory workers 是 refs-only/fail-open support，不是 admission layer、第二 route table、quality owner、artifact authority 或 publication gate。

## Evidence

- repo/source/control-plane 完成由 diff、contract/schema、focused tests 与 no-active-caller proof 支持。
- live/runtime/readiness claim 必须有 fresh OPL readback、MAS owner receipt、stable typed blocker、human gate、independent reviewer/auditor receipt或真实 artifact semantic delta。
- docs、tests、descriptor ready、queue empty、projection clean、candidate package 和 dry-run 不得升级为 paper progress、publication ready、runtime ready、domain ready 或 production ready。
- Live evidence 可以后置，但后置不能被解释为已经 ready，也不能反向恢复已退役的 MAS private platform。

## 工程约束

- 删除优先；不为已退役系统再建审计、投影和专测体系。
- 保持 source/test 文件职责清晰；超过 1500 行是拆分信号。
- 测试使用 pytest 原生递归收集，不恢复 wildcard aggregate/re-export plumbing。
- Python packaging 信任标准安装/OPL workspace override，不在 import 时改写 `sys.path`、`__path__` 或 `sys.modules`。
