# Contracts Root

`contracts/` is the repo root for machine-readable governance contracts.

Keep structured payloads here when other agents, CLIs, tests, or runtime entry
surfaces must consume the contract directly. Narrative design notes belong under
`docs/`; retired runtime explanations belong under `docs/history/`.

Current contract families:

- `contracts/modules/`: module boundary contracts for controller, runtime, and eval hygiene ownership.
- `contracts/opl-gateway/`: OPL family-level projection and helper-consumption contracts.
- `contracts/schemas/`: JSON schemas for stable product-entry surfaces.

This README is the index exception for humans and agents. It must not become a
second source of truth for contract fields.

## 中文

`contracts/` 是仓库根部的机器可读 governance contract 入口。

需要被 agent、CLI、测试或 runtime 入口直接消费的结构化 payload 放在这里。叙述性设计说明进入
`docs/`；已退休的 runtime 边界说明进入 `docs/history/`。

当前 contract 家族：

- `contracts/modules/`：controller、runtime、eval hygiene ownership 的模块边界 contract。
- `contracts/opl-gateway/`：OPL family-level projection 与 helper-consumption contract。
- `contracts/schemas/`：稳定 product-entry surface 的 JSON schema。

本 README 只是给人和 agent 的索引例外，不承载 contract 字段真相。
