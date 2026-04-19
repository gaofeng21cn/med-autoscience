# 项目概览

`Med Auto Science` 是共享 `Unified Harness Engineering Substrate` 之上的医学 `Research Ops` gateway 与 `Domain Harness OS`。它负责研究入口、workspace authority、证据推进、进度投影与面向论文的交付面；仓库持续维护 gateway、controller、overlay、adapter 与可审计 durable surface，同时把当前 research execution backend 保持在 `MedDeepScientist`。

## 当前运行形态

- formal-entry matrix：默认正式入口 `CLI`、支持协议层 `MCP`、内部控制面 `controller`
- repo-tracked 主线继续按 `Auto-only` 理解
- 当前 repo-tracked 基线：`MedAutoScience` 作为唯一研究入口与 research gateway，`Hermes-Agent` 作为上游外部 managed runtime target 与 supervision owner，`MedDeepScientist` 作为 controlled research backend
- 当前入口真相：repo-tracked 用户回路收口为 `product-frontdesk -> workspace-cockpit -> submit-study-task -> launch-study -> study-progress`。`product-frontdesk` 承担 controller-owned frontdoor，`workspace-cockpit` 承担当前用户 inbox，`study-progress` 负责投影任务摘要、监管 freshness 与人话进度；`product-entry-manifest` 与 `build-product-entry` 负责把这层回路输出为 shared direct / `OPL` handoff envelope
- 当前协作真相：当前仓内持有 repo-side seam / real adapter，并把研究治理、runtime supervision 与 progress semantics 固定在 repo-tracked surface 上；真实 research execution 继续由受控 backend 承担
- 历史 `Codex-default host-agent runtime` 只保留为迁移期对照面与 regression oracle

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
- 当前允许推进 family shared modules / shared boundary refactor；`physical migration / monorepo absorb` 继续跟随 external runtime gate 与已冻结的维护记录推进。
- 不以临时补丁或后处理补救方式替代严谨 contract 设计。
- 不把 display / paper-facing asset packaging 独立线混入当前 runtime / gateway / architecture 主线迁移。
