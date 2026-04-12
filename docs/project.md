# 项目概览

`Med Auto Science` 是共享 `Unified Harness Engineering Substrate` 之上的医学 `Research Ops` gateway 与 `Domain Harness OS`。仓库关注的是 gateway、controller、overlay、adapter 以及可审计的 durable surface，不把执行面 `MedDeepScientist` 当作本仓库本体。

## 当前运行形态

- 旧 `Codex-default host-agent runtime` 只保留为迁移期对照面与 regression oracle，不再是长期产品方向
- formal-entry matrix：默认正式入口 `CLI`、支持协议层 `MCP`、内部控制面 `controller`
- 主线理解：repo-tracked 产品主线按 `Auto-only` 理解
- 当前 repo-tracked 基线：`MedAutoScience` 作为唯一研究入口与 research gateway，`MedDeepScientist` 作为 controlled research backend；上游 `Hermes-Agent` 仍是目标外层 substrate，而当前仓内已落下 repo-side seam / real adapter
- 当前入口真相：`CLI / MCP` 已经构成稳定的 `agent entry`；repo-tracked 轻量医学 `product-entry shell`（`workspace-cockpit` / `submit-study-task` / `launch-study`）已落地，其中 `workspace-cockpit` 现已承担当前用户 inbox，直接聚合 repo 主线快照、attention queue 与启动/下任务/看进度命令回路，并通过 `study-progress` 投影当前任务摘要、监管 freshness 与人话进度；但成熟的 direct user-facing `product entry` 仍未落地
- 当前协作真相：`Hermes-Agent` 负责长期在线 runtime substrate / orchestration，`MedAutoScience` 负责研究入口与 outer-loop authority，`MedDeepScientist` 继续承载当前 research execution brain；这不要求现在就把 backend 内部依赖的 `Codex + skills` 全部替成 `Hermes`

## 目标

- 把医学研究的关键决策与运行状态沉到可审计的 repo-tracked contract 与 durable surface。
- 通过 `policy -> controller -> overlay -> adapter` 主链路表达能力，减少旁路。
- 把 controller / outer-loop / transport / durable surface 全链收紧到 backend-generic contract，避免继续把 `MedDeepScientist` 视作默认不可替代 runtime truth。
- 维护稳定的 runtime contract 与 delivery surface，确保可验证、可迭代。
- 把研究推进收口成一串通往 SCI-ready 投稿态的 fail-closed gate，而不是依赖一次长对话或单个 backend 自行兜底。
- 在 runtime gate 清除后，补齐可直接进入、也可被 `OPL` handoff 调起的 lightweight medical `product entry`。

## 目标中的 Hermes-Agent 与当前 seam

目标态里，不应把 `MedAutoScience` 理解成“把旧 `MedDeepScientist` 换个名字套起来”，而应理解为：

- `MedAutoScience` 负责研究入口、study/workspace authority、研究治理与 publication judgment。
- 上游 `Hermes-Agent` 负责 outer runtime substrate、managed runtime handle 与 backend-generic execution contract。
- `MedDeepScientist` 负责当前仍需保留的 inner research execution。

因此系统追求的不是“保证必然发表”，而是把研究推进变成可审计的阶段性收敛过程：

- 先明确问题、边界、journal 和 evidence package
- 再进入 managed runtime
- 再通过 publication gate、completion sync 和 delivery plane 持续逼近 SCI-ready 投稿态

当前还要补上一条诚实边界：

- 当前仓内的 `Hermes` 首先只是 repo-side outer substrate seam，不等于宿主机已经预装独立 `Hermes-Agent` runtime。
- 如果宿主机尚无 external `Hermes-Agent`，当前 repo-side adapter 会 fail-closed；当前能复用的是 outer-loop contract、durable surface、watch / supervision / progress semantics，而底层 quest execution 仍经由 controlled backend contract 落到 `MedDeepScientist`。
- 因而这条主线相对旧形态不是逻辑降级，而是先把外环监管、研究治理、人话进度汇报收成独立 authority，再把剩余 engine-level 能力逐步解构出去。

## 非目标

- 不把项目级 `.codex/`、`.omx/` 或其他临时 handoff surface 当作权威真相。
- 不在 external runtime gate 未解除时推动物理迁移或跨仓大重构。
- 不以临时补丁或后处理补救方式替代严谨 contract 设计。
- 不把 display / paper-facing asset packaging 独立线混入当前 runtime / gateway / architecture 主线迁移。
