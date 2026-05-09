# Open Harness OS Architecture

这份文档回答一个长期架构问题：

`MedAutoScience` 现在是医学自动科研系统。未来如果希望让整套 harness 能兼容其他领域的论文生产与研究运行，这条线应如何理解？

本文给出的正式结论是：

- `MedAutoScience` 有能力成为开放 `Harness OS` 演化路线上的第一份成熟参考实现
- 但不应把今天的 `MedAutoScience` 直接等同于通用 `Harness OS`
- 正确方向是 `抽离内核`，不是 `完全重构重写`
- 长期应形成：
  - 上层：`OPL Gateway / federation`
  - 中层：可复用的 `Harness OS core`
  - 下层：各领域自己的 `domain pack`

## 一句话结论

`MedAutoScience` 可以兼容未来开放 `Harness OS` 的方向，但前提不是把医学语义原样推广到所有领域，而是把其中可复用的运行内核抽出来，同时把医学特化 contract、overlay、publication surface 与 delivery 规则保留为 `medical domain pack`。

## 当前定位

今天这个仓库的正式定位已经不是“医学脚本集合”，而是：

- 对外：`Research Ops` 的 `domain gateway`
- 对内：医学自动科研的 `Domain Harness OS`

这意味着它本来就有两层：

1. `gateway` 层
   - 负责稳定入口、公开 contract、审计边界、外部 handoff
2. `harness OS` 层
   - 负责 controller、runtime、eval、delivery 的长期运行链

这套定义与 `OPL` 顶层 federation 语言兼容：

```text
Human / Agent
  -> OPL Gateway
      -> Domain Gateway
          -> Domain Harness OS
              -> Runtime / Eval / Delivery
```

因此，未来的开放化方向，不应是否定 `MedAutoScience`，而应把它视为当前最成熟的 `Research Ops` domain reference implementation。

## 正式判断

### 1. 不需要完全重构

当前系统里已经有一批明显可复用的能力：

- `agent-first, human-auditable` 的运行模式
- workspace / study / quest 的长期状态模型
- authority artifact 的显式落盘与引用机制
- controller -> runtime -> eval -> delivery 的分层思路
- stop-loss、promotion、audit、resume、publication gate 这类治理语义
- worktree / runtime / integration 的工程纪律

这些并不是医学独占能力，而是可演化为通用 research harness 的基础层。

### 2. 也不能直接原样开放

当前代码和 contract 里仍然存在大量医学特化内容，例如：

- `medical_analysis_contract`
- `medical_reporting_contract`
- `journal_shortlist`
- `publication_gate`
- 临床 `study_archetype`
- `endpoint_type`
- `manuscript_family`
- Figure / Table publication surface
- 医学 overlay 与医学路线偏置

这说明今天的 `MedAutoScience` 仍然是“医学 domain system”，而不是“领域无关内核”。

### 3. 正确路径是抽离

长期正确方向不是：

- 把 `MedAutoScience` 直接改名为通用内核
- 或者把所有领域都硬塞进医学语义里

而是：

- 抽出 `Harness OS core`
- 保留 `MedAutoScience` 作为 `medical domain gateway + medical domain pack`
- 让新的其他领域在同一内核上挂接自己的 `domain pack`

## 建议的三层结构

### A. Federation Layer

这是 `OPL` 顶层负责的层。

职责：

- workstream discovery
- domain routing
- handoff payload
- federation audit
- 保证不会绕过 `domain gateway` 直达 harness

它不负责：

- 直接运行研究
- 直接持有某个具体领域的 truth
- 取代 domain gateway

### B. Harness OS Core

这是未来应抽离出来的通用内核。

它应只保留跨领域都成立的运行能力：

- `controller_charter`
  - 领域对象的 authority artifact 与 projection 机制
- `runtime`
  - quest / run / session / execution artifact 的稳定 contract
- `eval_hygiene`
  - verdict / gap / recommendation / escalation 的 typed artifact
- `delivery substrate`
  - 交付包、导出、审计、版本化与回写
- `gateway contract substrate`
  - workspace / profile / controller / adapter 的稳定入口约束
- `operational governance`
  - audit、resume、promotion、stop-loss、handoff、readability / readiness gates

这一层要刻意避免直接出现医学语义。

例如：

- 不出现 `medical_*`
- 不出现特定期刊、临床终点、医学 Figure/Table 语义
- 不把某个 domain 的 publication gate 直接写成 core gate

### C. Domain Pack

这一层承载各领域自己的语义与交付规则。

`MedAutoScience` 当前最成熟的就是 `medical domain pack`，它应继续持有：

- 医学 startup / reporting / analysis contract
- 医学 overlay
- 临床研究 archetype 与 route bias
- 期刊、报告规范、投稿 surface
- 医学论文 Figure / Table shell
- 医学审计与 publication-ready 质量门控
- 与 `MedDeepScientist` 的医学 research runtime glue

未来如果扩到其他领域，应新增独立的 domain pack，而不是污染 medical pack。

## 哪些东西应视为 Core 候选

下面这些对象，已经很接近 core 级抽象：

- `study_charter`
  - 本质上是 controller-owned authority artifact
- `startup_contract` 的 projection 机制
  - 本质上是 controller -> runtime handoff projection
- `runtime_escalation_record`
  - 本质上是 runtime-owned durable event artifact
- `status / decision / report / ref-only read model`
  - 本质上是运行态与审核态的投影问题
- workspace / study / quest 的层级组织
  - 本质上是长期运行对象模型

这些对象未来应逐步改写为 domain-neutral vocabulary，再由 domain pack 赋予具体语义。

## 哪些东西必须继续留在 Medical Domain Pack

下面这些东西不应被假装成“通用”：

- `medical_analysis_contract`
- `medical_reporting_contract`
- 期刊 shortlist 与投稿目标解析
- 临床终点、队列、纳排、paper framing
- publication display template catalog
- 医学 manuscript gate 与 terminology redline
- 医学 evidence package 与 route bias policy

这些对象的价值，恰恰来自医学专业性。

开放 `Harness OS` 的目标，不是把这部分磨平，而是把它们放在正确的层里。

## 对其他领域的兼容性判断

### 高兼容领域

对下面这类领域，兼容性通常较高：

- 生物信息 / 组学数据分析
- 公共卫生 / 流行病学
- 健康经济与结局研究
- 教育数据科学
- 产业研究 / 运营研究
- 计算社会科学中证据链和交付链较清晰的子方向

原因是它们通常也具备：

- 数据资产
- 研究对象模型
- 运行与评估链
- formal deliverable
- 人类审核与机器执行并存

### 低兼容领域

对下面这类领域，不能直接平移：

- 证明主导的理论工作
- 强依赖开放式人文解释的写作任务
- 没有稳定 artifact / verdict / delivery 边界的探索型任务

这些领域如果要接入，也需要自己的 domain pack，甚至需要不同的 eval / delivery contract。

## 对仓库未来演化的约束

### 近中期

`MedAutoScience` 仍应保持：

- `Research Ops` 的 domain gateway
- 医学 domain reference implementation
- 当前最成熟的 harness OS 参考面

不应为了“想开放”而提前抽空医学能力。

### 中长期

如果要真的走向开放 `Harness OS`，建议按下面顺序推进：

1. 冻结 vocabulary
   - 明确哪些词属于 core，哪些词属于 medical pack
2. 冻结 authority boundary
   - controller truth、runtime truth、eval truth、delivery truth 分层
3. 抽离 core contract
   - 先抽 artifact / projection / verdict / escalation / delivery substrate
4. 保留 medical pack
   - 不削弱医学 publication surface、overlay、gate
5. 用第二个非医学 domain 验证
   - 只有成功承接第二个 domain，才说明 core 真的成立

## 非目标

这份文档不主张：

- 把 `MedAutoScience` 直接改造成领域无关壳子
- 把 `OPL` 写成对 domain gateway 的替代
- 绕过 domain gateway 直达 harness
- 因为追求“通用”而弱化医学专业 contract
- 在没有第二个真实 domain 验证前，就宣称已经完成开放化

## 当前推荐口径

今后对内对外，推荐统一使用下面这条口径：

- `MedAutoScience` 是当前 active 的 `Research Ops` domain gateway 与 medical harness OS
- 它不是 `OPL` 的替代物，也不是通用 HarnessOS 的完成态
- 它是未来开放 `Harness OS` 路线上的第一份成熟参考实现
- 如果未来开放化，正确方向是 `Harness OS core + domain packs`，而不是把医学系统直接磨平成一个通用壳

## 结论

因此，关于“这一个东西是否可以成为一个开放的 HarnessOS”，正式结论是：

- 可以
- 但方式必须是 `抽离内核，保留领域包`
- `MedAutoScience` 继续承担 medical reference implementation 的角色
- 真正的开放 `Harness OS`，应在未来通过第二个 domain pack 验证，而不是只靠医学系统内部自我命名完成
