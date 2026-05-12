# Contracts Root

`contracts/` is the repo root for machine-readable governance contracts.

Keep structured payloads here when other agents, CLIs, tests, or runtime entry
surfaces must consume the contract directly. Narrative design notes belong under
`docs/`; retired runtime explanations belong under `docs/history/`.

MAS is published as a medical research Foundry Agent and an OPL-compatible
package built on OPL Framework. Machine-readable product positioning lives in
the product-entry manifest, while this directory keeps the contract families
that let OPL discover, index, and validate MAS package metadata without owning
MAS medical research truth, quality verdicts, runtime owner surfaces, artifact
authority, or publication authority.

Current contract families:

- `contracts/modules/`: module boundary contracts for controller, runtime, and eval hygiene ownership.
- `contracts/opl-framework/`: OPL Framework projection, compatible-package, and helper-consumption contracts.
- `contracts/schemas/`: JSON schemas for stable product-entry surfaces.

This README is the index exception for humans and agents. It must not become a
second source of truth for contract fields.

## 中文

`contracts/` 是仓库根部的机器可读 governance contract 入口。

需要被 agent、CLI、测试或 runtime 入口直接消费的结构化 payload 放在这里。叙述性设计说明进入
`docs/`；已退休的 runtime 边界说明进入 `docs/history/`。

MAS 对外发布为医学研究 Foundry Agent，也是 built on OPL Framework 的
OPL-compatible package。机器可读产品定位由 product-entry manifest 持有；本目录只保存
OPL 发现、索引和验证 MAS package metadata 所需的 contract 家族，不让 OPL 持有 MAS 的
medical research truth、quality verdict、runtime owner surface、artifact authority 或
publication authority。

当前 contract 家族：

- `contracts/modules/`：controller、runtime、eval hygiene ownership 的模块边界 contract。
- `contracts/opl-framework/`：OPL Framework projection、compatible-package 与 helper-consumption contract。
- `contracts/schemas/`：稳定 product-entry surface 的 JSON schema。

本 README 只是给人和 agent 的索引例外，不承载 contract 字段真相。
