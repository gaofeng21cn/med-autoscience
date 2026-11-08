# 当前验证边界

本文区分源码事实与必须现场读取的状态，不保存发布版本、handler 计数、历史 receipt 或论文进展快照。

## 源码可证明的事实

MAS 使用 `agent/` 声明研究阶段、专业知识与质量要求；公开动作和内部 authority bindings 分别由 `contracts/action_catalog.json`、`contracts/domain_handler_registry.json` 持有。具体组件与职责见 [架构](./architecture.md)。

验证入口是 `scripts/verify.sh`；`full` 额外读取 OPL source-hygiene。测试通过只覆盖本次源码和所用 Framework 环境，不证明安装或线上运行状态。

## 需要现场证明的状态

| 结论 | 必须读取的证据 |
| --- | --- |
| Package 已安装且可用 | OPL Package 聚合状态、实际 carrier readback、ScholarSkills 所需能力可调用性 |
| Runtime 正常 | 同一 workspace/study 的 StageRun、Attempt、provider 与恢复结果 |
| 论文取得进展 | canonical artifact 的语义变化、MAS owner receipt、明确 route-back、human gate 或 typed blocker |
| 质量与投稿要求满足 | 当前独立 reviewer/auditor receipt、六域 review currentness、publication owner verdict 与当前 generation 产物 |
| 投稿或部署完成 | 对应外部系统或部署目标的正式回执 |

旧版本 validator qualification receipt 仅说明其冻结 artifact 的验证，不定义当前普通 Package readiness。Exact hash 一致不认证 issuer 身份；host 输入必须有 Framework managed authority-attempt 与 owner-ledger provenance。

开放验收条件见 [证据差距](./active/mas-ideal-state-gap-plan.md)。本页不推断任何具体 study、已安装版本或生产实例的当前状态。
