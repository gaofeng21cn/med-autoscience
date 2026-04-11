# Research Foundry Positioning

这份文档用来冻结一套新的公开口径：

- `OPL / One Person Lab`
- `Research Foundry`
- `Med Auto Science`

它的目标是回答两个问题：

1. 这三层到底分别是什么？
2. 当前 `med-autoscience` 这个 GitHub repo 之后应该如何演化，而不打断现有主线开发？

## 一句话定义

推荐的长期品牌与架构层级是：

- `OPL / One Person Lab`
  - 顶层 lab federation 与 gateway 语言
- `Research Foundry`
  - 面向 `Research Ops` 的通用 framework
- `Med Auto Science`
  - `Research Foundry` 上第一个成熟的 medical domain implementation

也就是说：

`Med Auto Science` 不再承担“同时既是医学产品、又是通用框架本体”的双重身份。

## 为什么需要这一层新命名

当前 `MedAutoScience` 这个名字有一个自然优势：

- 医学场景非常明确
- 专业性强
- 与你当前最成熟的落地场景完全对齐

但它也带来一个长期问题：

- 名字天然把系统锁在“医学”上
- 不利于把 `Research Ops` 主链本身抽象成更通用的 framework
- 未来要承接非医学 research domain 时，叙事会变拧巴

如果继续让 `Med Auto Science` 既代表医学产品、又代表通用框架，后续会出现三个问题：

1. 对外产品边界不清
2. 对内架构抽象不清
3. 新 domain 无法自然进入同一层叙事

因此，更合理的做法是：

- 在 `OPL` 与 `Med Auto Science` 之间，补上一层新的 `Research Ops Framework` 名称
- 当前推荐这个名字是：
  - `Research Foundry`

## 三层关系

### 1. OPL / One Person Lab

`OPL` 是顶层 federation，不是某个具体 domain runtime，也不是具体一个产品 family。

它负责：

- federation model
- gateway language
- cross-domain routing
- shared foundation expectations

它不负责：

- 直接替代 domain gateway
- 直接成为所有 domain 的单体 runtime

### 2. Research Foundry

`Research Foundry` 是面向 `Research Ops` 的通用 framework。

它负责的是：

- 研究资产与证据组织
- authority artifact 与 runtime artifact 的长期运行语言
- 研究 claim / argument / story 的形成
- formal deliverable families 的投影与 contract

它不是某一个具体领域的实现，也不是某一个单独交付格式。

### 3. Med Auto Science

`Med Auto Science` 是当前最成熟的 medical domain implementation。

它负责：

- medical domain gateway
- medical domain contract
- medical publication / reporting / display / submission surfaces
- medical-specific overlay、route bias、publication gate 与 delivery logic

因此，`Med Auto Science` 的定位应从：

- “通用框架本体”

收紧为：

- “Research Foundry 在 medical domain 上的第一个成熟实现”

## Research Foundry 的边界

`Research Foundry` 当前不应被定义成“所有研究相关任务的大一统框架”。

第一版更准确的边界是：

- 它服务 `Research Ops`
- 它组织的是：
  - 资产
  - 证据
  - claim
  - story
  - formal deliverables

### 它直接覆盖的 formal deliverable families

从概念上，它可以承接至少下面三类 family：

- `paper`
- `grant_proposal`
- `deck`

这里的关键不是文件格式，而是：

- 同一批研究资产
- 经过不同 audience / objective framing
- 投影成不同正式交付面

### 这三类 family 的共同上层

它们共享的是：

- research truth
- evidence package
- story formation
- audience-specific framing
- delivery contract

因此：

- `paper` 不是 framework 本体
- `grant proposal` 不是 framework 本体
- `deck` 也不是 framework 本体

它们都只是 `Research Foundry` 里的 delivery family。

## 为什么现在不应把 RedCube AI 直接并进来

你当前想做的，是把 `Med Auto Science` 泛化成 `Research Ops` 的一个通用 framework，而不是立刻把整个 `OPL` 的所有 harness 合成一个大系统。

所以当前不建议：

- 立刻做一个统一吞掉 `Med Auto Science + RedCube AI` 的总 runtime

当前更合理的理解是：

- `Research Foundry`
  - 先解决 `Research Ops` 的通用 framework 问题
- `RedCube AI`
  - 继续作为独立的 `Presentation Ops` domain system
  - 同时未来可以成为 `deck` family 的强执行器 / 强视觉交付器

也就是说：

- 在概念上，`deck` 可以属于 `Research Foundry` 的 delivery family
- 但在实现上，完全可以由 `RedCube AI` 这类 sibling domain system 强力承接

这两件事不冲突。

## 对 Med Auto Science 仓库的正式影响

### 当前不建议立即做的事情

现在不建议立刻：

- 改 Python package 名
- 大规模改 import path
- 直接改 GitHub repo 名
- 把医学 contract 从现有仓库中硬拆出去

原因很简单：

- 当前还有活跃 repo-side mainline 在持续收口
- display / monorepo 仍处于 contract 收口期
- 过早做品牌级物理迁移，收益小于风险

### 当前建议先做的事情

当前应先做“口径迁移”，不是“物理迁移”。

也就是先把公开叙事改成：

- 仓库现在承载的是 `Med Auto Science`
- 它是 `Research Foundry` 的 medical implementation
- `Research Foundry` 是上层通用 `Research Ops Framework`

### 推荐的三阶段 repo 演化策略

#### Phase 1：Public Positioning Shift

只改公开叙事，不改 repo 物理身份。

包括：

- README wording
- docs wording
- GitHub about / description
- OPL linking language
- 对外介绍口径

在这一阶段，仓库仍然可以保持：

- repo slug: `med-autoscience`
- package: `med_autoscience`

#### Phase 2：Dual-Identity Repository

当 `Research Foundry` 的上层口径稳定后，可以让这个仓库进入双身份阶段：

- 对外显示名：`Med Auto Science`
- 对外介绍文案里明确写：
  - `Med Auto Science is the medical implementation of Research Foundry`

这一阶段仍然不要求立刻改 code package。

#### Phase 3：Framework / Implementation Separation

只有在下面条件满足时，才考虑真正分仓或重命名：

- `Research Foundry` 的 core contract 已有明确候选
- `core vs medical pack` 的 vocabulary 已冻结到足够稳定
- 至少出现第二个非医学实现候选

到那个时候，才值得决定是否：

- 新建 `research-foundry` repo
- 当前仓库继续保留为 `med-auto-science`
- 或者当前仓库反向上升为 framework repo，再把 medical pack 下沉

在这之前，不建议做物理级 repo 改造。

### 这不等于 monorepo 目标取消

这里需要把顺序讲清楚：

- 当前四仓统一 program 先做的是 contract convergence 与 behavior convergence
- `MedAutoScience` 自己的 `monorepo / runtime core ingest / controlled cutover` 仍然保留为 domain-internal 长线
- 前者解决的是跨仓共享 substrate contract 是否已经冻结
- 后者解决的是 `MedAutoScience` 单域内部 topology、runtime core 与 cutover 的物理整合

因此，当前不提前做 physical migration，不是放弃 monorepo，而是先把未来迁移必须依赖的边界和 contract 冻结干净。

## 对 GitHub repo 的具体建议

### 现在

当前建议：

- GitHub repo 先不改名
- 继续使用：
  - `gaofeng21cn/med-autoscience`
- 但显示文案逐步调整为：
  - `Med Auto Science`
  - `Medical implementation of Research Foundry`

### 接下来可以逐步改的公共表面

1. GitHub 仓库描述
   - 从“医学自动科研系统”改为更准确的两层口径
2. README 首页
   - 增加：
     - `OPL -> Research Foundry -> Med Auto Science`
3. OPL README 与 federation 文档
   - 把 `MedAutoScience` 的定位从“Research Ops 本体”改成：
     - `Research Ops` 当前 active 的 medical implementation
4. 文档内部术语
   - 逐步把无必要的“MedAutoScience = 通用框架”暗示移除

### 暂时不要改的公共表面

- repo slug
- Python import path
- CLI command 名
- 已存在的用户调用面
- 已被当前 repo-side mainline 依赖的 contract path

## 推荐公开口径

今后对外介绍时，推荐统一使用下面这条口径：

> `One Person Lab` 是顶层 federation。  
> `Research Foundry` 是面向 `Research Ops` 的通用 framework。  
> `Med Auto Science` 是 `Research Foundry` 在医学场景上的第一个成熟实现。

如果要再简短一点，可以用：

> `Med Auto Science` is the medical implementation of `Research Foundry` under `OPL`.

## 结论

因此，关于“现在的 Med Auto Science 这个 GitHub repo，后边应该怎么变化”，正式结论是：

- 先改定位，不急着改物理仓库身份
- 先把 `Research Foundry` 立成上层 framework 名
- 让当前仓库承担 `Med Auto Science` 这个 medical implementation 的角色
- 等 core 与 domain pack 的边界更稳定、且出现第二个实现候选后，再考虑 repo 级拆分或重命名
