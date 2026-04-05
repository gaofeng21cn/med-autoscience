# Research Foundry Medical Mainline

这份文档把 `Med Auto Science` 当前真正的主线固定下来。

它回答四个问题：

1. `Med Auto Science` 现在到底在做什么
2. `Research Foundry`、`domain gateway`、`domain harness OS` 三者是什么关系
3. 为什么论文交付仍然是顶层业务目标，但不再主导整个架构分层
4. 这条主线接下来应按什么顺序推进

## 一句话结论

`Med Auto Science` 当前应被理解为：

- `Research Foundry` 在医学场景上的首个成熟实现
- 对外承担医学 `Research Ops` 的 `domain gateway`
- 对内承担医学自动科研的 `domain harness OS`

而它的业务北极星始终不变：

- 把医学研究从数据资产稳定推进到可投稿论文

## 两层主线必须分开理解

### 1. 业务北极星

业务目标非常明确，而且不会改变：

- 形成值得继续投入的研究路线
- 形成完整证据链
- 形成稿件、图表、表格与投稿交付

所以：

- `display`
- `paper`
- `submission delivery`

都仍然是 `P0` 级能力。

### 2. 架构主线

为了让这些交付能力稳定存在，系统本体必须先收紧成：

- 对外稳定的 `domain gateway`
- 对内清晰的 `domain harness OS`
- 明确的 `controller / runtime / eval / delivery` authority boundary

因此：

- `display / paper delivery` 不是被降级
- 而是被放回 `delivery / publication plane` 的正确层级

它们依然决定平台有没有真实价值，但不再决定整个平台如何分层。

## 当前推荐的系统理解

推荐始终按下面这条链路理解：

```text
Human / Agent
  -> OPL Gateway
      -> Research Foundry
          -> Med Auto Science Domain Gateway
              -> Med Auto Science Domain Harness OS
                  -> Controller / Runtime / Eval / Delivery
```

这里的关键含义是：

- `OPL`
  - 负责顶层 federation 与 gateway language
- `Research Foundry`
  - 负责 `Research Ops` 的通用 framework 身份
- `Med Auto Science`
  - 负责医学场景的正式实现
- `Med DeepScientist`
  - 当前仍是最核心的 runtime substrate 之一
  - 但不等于整个 `Med Auto Science`

## Domain Gateway 与 Domain Harness OS 的分工

### Domain Gateway

`Med Auto Science` 作为 `domain gateway`，负责：

- 暴露正式入口
- 暴露稳定 contract
- 暴露 workspace / study / controller / adapter 的可审计控制面
- 阻止外部调用方直接绕过边界去碰内部 runtime

### Domain Harness OS

`Med Auto Science` 作为 `domain harness OS`，负责：

- 组织 controller、runtime、eval、delivery 为同一条长期运行链
- 持有 authority artifact、runtime artifact、verdict artifact 与 delivery artifact 的边界
- 维持研究推进、审核、停止、promotion、publication hygiene 与 submission delivery

未来 monorepo 内部的：

- `controller_charter`
- `runtime`
- `eval_hygiene`

都应被理解为这个 harness OS 的内部主模块。

与此同时，outer loop 不应被误解成第二个常驻 runtime。当前推荐形态是：

- `MedDeepScientist` 作为常驻 inner runtime
- `Med Auto Science` 作为 tick-driven outer controller

相关机制见：

- [Outer-Loop Wakeup And Decision Loop](./outer_loop_wakeup_and_decision_loop.md)

## 为什么 publication / display 仍然是主价值

这一点必须说清楚：

- `Med Auto Science` 最终不是为了“架构漂亮”
- 而是为了稳定产出医学论文

所以 publication / display 不是边缘能力，而是：

- `delivery plane`
- `publication plane`
- `paper-facing value plane`

它们仍然是平台对医学用户最直观、最关键的交付面。

只是它们应该建立在稳定底座上：

- `study charter`
- `startup projection`
- `runtime escalation`
- `publication eval`
- `medical reporting contract`
- `display template contract`

这些内部 contract 如果不先收紧，图表和稿件表面就会不断被局部问题牵着走。

## 主线与子线的正确关系

从今天开始，推荐把整个仓库的推进理解为：

### 顶层主线

`Research Foundry medical implementation / domain harness OS convergence`

### 主线下的正式子线

#### A. Authority Convergence

包括：

- `study charter artifact carrier`
- `startup projection`
- `runtime escalation record`
- `publication eval minimal schema`
- `charter-parameterized input contract`

#### B. Delivery / Publication Plane

包括：

- manuscript surface
- reporting contract
- publication gate
- submission companion
- graphical abstract / companion artifacts
- figure / table contract
- display template catalog

#### C. Real-Study Adoption

包括：

- 真实课题重绘
- 真实稿件重交付
- anchor paper closure
- 真实 paper-owned truth surface 对齐

### 这意味着什么

这意味着：

- `display / paper` 继续做
- 而且必须持续做
- 但它们作为 `delivery plane` 进入主线，而不是与系统本体竞争定义权

## 推荐 phase 顺序

### Phase 0. Program Truth Reset

目标：

- 把旧的 display program、monorepo program、当前 mainline 统一成同一个 north star
- 清掉过时 prompt、过时 CURRENT_PROGRAM 和 stale report 叙事

### Phase 1. Harness Authority Convergence

目标：

- 固定 `controller / runtime / eval / delivery` 的 authority boundary
- 先固定当前唯一活跃子线 `publication eval minimal schema`
- 在它之后按顺序继续：
  - `charter-parameterized input contract`
  - `delivery plane contract map`

### Phase 2. Delivery Plane Convergence

目标：

- 把 manuscript / reporting / submission / display 重新写成 harness OS 下的正式 delivery plane
- 明确哪些是 publication shell，哪些是 domain-specific contract

### Phase 3. Real-Study Relaunch

目标：

- 用新的 delivery plane 与 authority contract 重跑真实锚点课题
- 不再只追求“模板能画”，而是追求“study-owned paper surface 真正稳定”

### Phase 4. Monorepo Scaffold Gate

目标：

- 只有在前面 contract 收敛足够后，才考虑 monorepo scaffold 与 cutover
- scaffold 永远不是先手动作

## 当前 immediate next step

当前最自然的 immediate next step 不是重新讨论大而空的架构，而是：

1. 继续把 `publication eval minimal schema` 收紧成稳定 handoff surface
2. 在它之后继续：
   - `charter-parameterized input contract`
   - `delivery plane contract map`
   - `real-study relaunch`

## 非目标

当前主线不主张：

- 把 `Med Auto Science` 重新降级成“论文工具箱”
- 把 `display / paper` 误当成边缘能力
- 因为要 monorepo 就提前做大规模代码搬迁
- 因为要开放化就提前把医学语义抹平
- 把 `Research Foundry` 现在就做成新的物理主仓库

## 正式判断

因此，当前 `med-autoscience` 仓库的正式主线应写成：

> `Med Auto Science` is the medical implementation of `Research Foundry`, operating as a medical `domain gateway + domain harness OS`, with publication-grade paper delivery as the business north star.

对应中文可稳定表述为：

> `Med Auto Science` 是 `Research Foundry` 的医学实现；对外是医学 `Research Ops` 的 `domain gateway`，对内是医学自动科研的 `domain harness OS`；其业务北极星始终是把研究稳定推进到发表级论文交付。
