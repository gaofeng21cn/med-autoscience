# Agent Runtime Interface

本文只说明 MAS 声明与 OPL host 的可调用边界。可执行来源是 `contracts/action_catalog.json`、`agent/stages/manifest.json` 和 `contracts/domain_handler_registry.json`。

## 公开与内部入口

公开执行由六个 canonical Stage action 承载：direction、baseline、analysis、manuscript、review、handoff 的完整 action id 以 catalog 为准。CLI/MCP/Skill/product spelling 由 OPL 生成；MAS 不维护另一份命令 parser 或 JSON-RPC transport。

当前 catalog 另含 study initialization、qualification work-item provisioning、study lifecycle reactivation、candidate admission、build-dependency currentness 和 paper mission 六个 host-only authority action。它们的用户 surfaces 为 null。Registry 另绑定 Agent Lab self-evolution closeout，完整 binding 以 registry 为准。

Handler 消费 host 提供的身份、exact refs、authority context 和当前证据，返回领域 result 或受限物化授权；不负责文件、网络、进程、session、runtime lifecycle 或 Stage transition。Host 执行受权物化必须回传 receipt，不能自造 MAS verdict。

## 调用与回读

Host 在创建 StageRun/Attempt 前解析 workspace/study identity，并执行 lifecycle admission。初始化与重新激活的规则分别归 `contracts/study_initialization_contract.json` 与 `contracts/study_lifecycle_reactivation_contract.json`。

Attempt 的 route/review 协议见 [Stage / Route / Handoff](../stage_route_handoff_standard.md)。OPL 负责持久执行、独立 session、receipt 物化和只读状态展示；MAS 负责医学语义与 owner consumption。

Package 使用 `opl packages` 公开生命周期入口。ScholarSkills 缺失或所需能力不可调用只阻断 MAS；具体 selected build 还须探测其 validator 符号，不能把 Package presence 当作函数级验证。

[验证入口](../../policies/repo-ops/repository_ci_preflight.md) 证明源码合同；真实进展需要 StageRun、independent Review、MAS owner result 与当前 artifact evidence。
