# 项目概览

`Med Auto Science` 是共享 `Unified Harness Engineering Substrate` 之上的医学 `Research Ops` gateway 与 `Domain Harness OS`。仓库关注的是 gateway、controller、overlay、adapter 以及可审计的 durable surface，不把执行面 `MedDeepScientist` 当作本仓库本体。

## 当前运行形态

- 旧 `Codex-default host-agent runtime` 只保留为迁移期对照面与 regression oracle，不再是长期产品方向
- formal-entry matrix：默认正式入口 `CLI`、支持协议层 `MCP`、内部控制面 `controller`
- 主线理解：repo-tracked 产品主线按 `Auto-only` 理解
- 当前 repo-tracked runtime topology：`MedAutoScience` 作为唯一研究入口与 research gateway，`Hermes` 作为外层 runtime substrate owner，`MedDeepScientist` 作为 controlled research backend

## 目标

- 把医学研究的关键决策与运行状态沉到可审计的 repo-tracked contract 与 durable surface。
- 通过 `policy -> controller -> overlay -> adapter` 主链路表达能力，减少旁路。
- 把 controller / outer-loop / transport / durable surface 全链收紧到 backend-generic contract，避免继续把 `MedDeepScientist` 视作默认不可替代 runtime truth。
- 维护稳定的 runtime contract 与 delivery surface，确保可验证、可迭代。

## 非目标

- 不把项目级 `.codex/`、`.omx/` 或其他临时 handoff surface 当作权威真相。
- 不在 external runtime gate 未解除时推动物理迁移或跨仓大重构。
- 不以临时补丁或后处理补救方式替代严谨 contract 设计。
- 不把 display / paper-facing asset packaging 独立线混入当前 runtime / gateway / architecture 主线迁移。
