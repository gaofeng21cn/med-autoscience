# Domain Gateway And Harness OS

这份文档把 `MedAutoScience` 当前更准确的定位固定下来：

- 对外：它是 `Research Ops` 的 `domain gateway`
- 对内：它是承载医学自动科研控制、执行、治理与交付的 `Domain Harness OS`

这不是一句宣传口号，而是后续架构、monorepo 迁移、runtime 边界与公开文档都必须遵守的定位约束。

## 一句话定义

`MedAutoScience` 是 `OPL` 体系下 `Research Ops` 的正式 domain gateway；它对外暴露稳定入口、领域合同与可审计控制面，对内由一个 `Domain Harness OS` 驱动，把 controller、runtime、eval、delivery 组织成同一条医学研究运行链。

## 在 OPL 联邦里的位置

在 `OPL` 的顶层语义里，推荐始终按下面这条链路理解：

```text
Human / Agent
  -> OPL Gateway
      -> MedAutoScience Domain Gateway
          -> MedAutoScience Domain Harness OS
              -> Runtime / Eval / Delivery Surfaces
```

这里的关键边界是：

- `OPL Gateway` 负责顶层路由语义与跨 domain 联邦语言
- `MedAutoScience` 负责 `Research Ops` 这个 domain 的正式入口与运行底座
- `MedDeepScientist` 当前是 `MedAutoScience` harness OS 中最核心的 runtime executor 之一，但不等于整个 harness OS

## Domain Gateway 负责什么

作为 `Research Ops` domain gateway，`MedAutoScience` 负责：

- 提供人类与 Agent 可稳定调用的正式入口
- 把研究任务路由到正确的 domain control surface，而不是让调用方直接碰 runtime 内部
- 暴露可验证、可审计、可持续演化的 workspace / profile / controller / overlay / adapter 合同
- 把领域级 authority 保持在 controller-facing truth surfaces，而不是散落到临时脚本或聊天上下文
- 让外部系统通过公开 contract 理解“这个 domain 能承接什么、如何进入、如何复核结果”

当前这个 gateway 角色，主要通过这些表面体现：

- workspace / study / portfolio 结构
- profile 与 policy
- formal-entry matrix：
  - `CLI` 作为默认 formal entry
  - `MCP` 作为 supported protocol layer
  - `controller` 作为 internal control surface
- adapter 入口
- project-truth contract 与公开技术文档

## Domain Harness OS 负责什么

作为 `Domain Harness OS`，`MedAutoScience` 负责：

- 执行 domain work，而不是只做文档路由
- 持久化关键状态、authority artifact、评估结论与交付结果
- 维护 controller -> runtime -> eval -> delivery 的稳定控制链
- 在研究推进中执行 gate、stop-loss、promotion、publication hygiene 与 submission delivery
- 让医学研究不是“一次性任务跑完”，而是“可审计、可恢复、可持续推进”的长期操作系统

从长期目标看，future monorepo 内部的一等模块：

- `controller_charter`
- `runtime`
- `eval_hygiene`

都属于这个 harness OS 的内部主模块，而不是对外 domain gateway 的替代物。

## 为什么一定要同时保留这两层

如果只强调 `gateway`，平台会退化成：

- 一个薄路由层
- 只会把任务转发下去
- 对长期 authority、runtime、eval、delivery 没有正式控制

如果只强调 `harness OS`，平台又容易退化成：

- 一个内部 runtime 容器
- 对外边界模糊
- 让调用方绕过 domain gateway 直接碰内部执行面

正确做法是同时保留：

- `domain gateway`
  - 解决正式入口、公开定位、稳定接口、可审计 handoff
- `Domain Harness OS`
  - 解决执行、记录、治理、评估、交付的长期运行能力

## 对 monorepo 迁移的约束

这一定义直接约束了当前 monorepo 方向：

- monorepo 目标是把 `MedAutoScience` 内部的 harness OS 收敛得更清晰
- 不是把 `MedAutoScience` 重新降级成只剩一个 gateway 壳
- 也不是把 gateway 角色吞进 runtime，最后只剩执行内核

因此，当前推荐的 monorepo 三模块：

- `controller_charter`
- `runtime`
- `eval_hygiene`

应被理解为 `Domain Harness OS` 的内部主模块。

与此同时，仓库级别仍然要保留：

- `Research Ops` domain gateway 的公开定位
- 面向 Agent 与人类协作者的稳定入口
- project-truth / docs / controller surfaces 这些可审计外层表面

## 对 authority 的直接影响

这套定位要求 authority 不再混叠：

- `controller_charter`
  - 持有 study charter 等 controller-owned authority object
- `runtime`
  - 持有 quest execution truth、session truth、artifact execution truth
- `eval_hygiene`
  - 持有 verdict / gap / recommendation 这类评估判据
- `domain gateway`
  - 暴露这些能力的正式入口与边界，但不把所有内部 truth 压成一个模糊大对象

例如：

- `study_charter` 属于 controller authority，而不是 runtime authority
- `startup_contract` 应是 runtime-facing projection，而不是 study authority root
- publication eval 应产生 verdict，而不是反向重写 controller truth

## 当前阶段的推荐理解

在今天这个仓库的实际状态下，更准确的理解是：

- `MedAutoScience`
  - 已经是正式的 `Research Ops` domain gateway
  - 正在把内部能力收敛成更清晰的 `Domain Harness OS`
  - 当前 repo-tracked 产品主线按 `Auto-only` 理解
- `MedDeepScientist`
  - 当前仍是最核心的 runtime execution substrate
  - 但未来会被更系统地收进 `MedAutoScience` harness OS 的 monorepo 拓扑中

如果未来要做高判断密度的 `Human-in-the-loop` 产品，更合理的形态是建立在这些稳定 contract 与执行模块之上的 sibling 或 upper-layer product，而不是把当前仓改造成同仓双模。

所以当前主线不是“再造一个新系统”，而是：

- 保持 gateway 角色稳定
- 把 harness OS 的 controller / runtime / eval 分层收紧
- 在 contract-first 的前提下逐步完成 monorepo 收敛

## 非目标

这份定位文档不主张：

- 把 `OPL` 写成对 `MedAutoScience` 的替代
- 把 `MedDeepScientist` 直接写成整个 `MedAutoScience`
- 因为要 monorepo 就把 gateway / harness OS / runtime 三层压成一层
- 因为强调 harness OS 就弱化公开入口、project-truth 与可审计对外表面
