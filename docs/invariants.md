# 不可变约束

Owner: `MedAutoScience`
Purpose: `project_invariants`
State: `active_current_truth`
Machine boundary: 本文是人读约束；机器事实以 contracts、source、runtime durable surfaces、artifact 与 owner receipts 为准。

## 身份与 owner

- canonical id 是 `mas`；repo/package/plugin locator 不改变 domain identity。
- MAS 是 `Declarative Medical Research Pack + minimal authority functions`；OPL 持有 generated/hosted platform surfaces。
- OPL 不得写 MAS study truth、quality/publication verdict、canonical artifact body、memory body 或 owner receipt。
- MAS 不得重新拥有 generic runtime、queue、attempt ledger、StateIndex、lifecycle/storage、observability、installer、CLI/MCP transport 或 workbench shell。

## Pack 与 generated surfaces

- `agent/` 是 canonical rich pack source；plugin carrier mirror 是分发要求，不是重复实现。
- action catalog 当前包含 22 个 action。普通 interface 从 catalog/schema 生成，不在 MAS 新增手写 parser、JSON-RPC glue 或 duplicate descriptor。
- MAS domain entry 只实现 handler targets 与医学 authority result，不变成 platform facade。
- Foundry 系列 policy 归唯一 OPL Framework；MAS 只保留 canonical refs、policy fingerprint、domain delta 与 false-authority envelope，不复制 policy body，也不安装 Framework policy carrier。
- 环境依赖在 `contracts/runtime_environment_requirements.json` 声明；prepare/run 归 OPL。MAS 可保留 `mas_provisioning_allowed=false` 的只读环境检查/投影，但不在 import、workspace 或 installer 中安装、修复环境，也不授权 ready。

## Authority

- 默认 next-action authority 只有 `StageOutcome -> NextActionEnvelope`。
- OPL transport/readback 只有传输权；同 identity 的 MAS owner consumption 才能解释 domain result。
- AI-first quality gate 必须消费独立 reviewer/auditor invocation 与 receipt；executor 不得自审并关闭质量门。
- publication、submission、artifact mutation、memory accept/reject 与 source readiness 必须由对应 MAS owner surface裁决。
- refs-only projection、schema、validator、test、workbench 可见性和 inventory presence 都不等于 authority verdict。

## 退役与兼容

- 已被 OPL 或标准工具替代的 MAS-local wrapper、facade、installer、workspace initializer、runtime shell 和旧 next-action producer 直接退役；不新增 compatibility shim、alias 或聚合测试。
- 旧 provider admission、current work unit、PaperRecovery 与 domain-action request 只允许 tombstone/provenance/no-resurrection guard，不得恢复 current caller。
- MDS/DeepScientist 只作 provenance、explicit archive import、backend audit、upstream learning 与 parity oracle。
- Hermes-Agent 只作显式非默认 executor/proof lane；不宣称与 Codex CLI 行为或质量等价。

## Durable truth

- study、publication、runtime 与 display 真相归 stable runtime/controller/contract/generated artifact surface；docs 只解释和导航。
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
