# Repository Split Between Research Foundry And Med Auto Science

这份文档只回答一个长期仓库问题：

当 `Med Auto Science` 成熟到足以支撑第二个学科实现时，未来的

- `gaofeng21cn/research-foundry`
- `gaofeng21cn/med-autoscience`

之间到底是什么关系？

## 一句话结论

长期目标不是把 `med-autoscience` 直接改名成 `research-foundry`，再把医学实现反向拆出去。

长期目标是：

- 新建 `gaofeng21cn/research-foundry` 作为通用 `Research Ops framework` repo
- 保留 `gaofeng21cn/med-autoscience` 作为医学 domain implementation repo
- 由 `med-autoscience` 依赖 `research-foundry` 的通用内核，而不是被它替代

换句话说：

- `research-foundry` = 通用骨架
- `med-autoscience` = 医学实现

## 这不是什么关系

这两个 repo 未来不应被理解为：

- 简单改名关系
- 上下游临时过渡关系
- “先把医学仓库升级成通用仓库，再把医学代码迁出去”的反向拆分关系
- “`research-foundry` 抽走所有底层后，`med-autoscience` 只剩一层薄壳”的关系

更准确的理解是：

- `research-foundry` 持有跨学科通用的 `Research Ops` core
- `med-autoscience` 持有医学语义、医学合同、医学交付与医学运行 glue
- 两者通过清晰的依赖方向协作：
  - `med-autoscience` 依赖 `research-foundry`
  - `research-foundry` 不反向依赖 `med-autoscience`

## 为什么不应直接把 med-autoscience 改名

如果未来直接把当前仓库改名为 `research-foundry`，会出现四个问题：

1. 仓库历史天然带有明显的医学语义与医学主线，不适合作为通用 core 的起点表面
2. 第二个学科 implementation 会天然落在一个“前身是医学仓库”的 core 下面，边界不干净
3. 现有 GitHub 链接、包名、运行合同与外部认知会一起发生不必要扰动
4. 当前仍在推进的医学 display / monorepo 主线会被额外引入品牌级迁移成本

因此，正确方向是：

- 先从 `med-autoscience` 中抽离通用内核
- 再把这部分通用内核单列成 `research-foundry`
- 最后让 `med-autoscience` 正式建立在其上

## future research-foundry 应持有什么

`research-foundry` 应持有真正跨学科成立的对象，而不是“今天碰巧写在医学仓库里”的所有底层代码。

### 应优先上提的对象

- domain-neutral 的 authority artifact 语言
- controller-owned charter / compiled authority object
- controller -> runtime 的 startup projection substrate
- runtime-owned escalation / verdict / gap / recommendation artifact
- controller / runtime / eval / delivery 的边界 contract
- workspace / study / quest 这类长期对象模型中的通用层
- delivery family 的通用投影骨架
- gateway / harness 的通用入口约束

### 结合当前主线，最可能先上提的对象

- `study_charter`
- `startup_contract` 中可 domain-neutral 化的 projection 部分
- `runtime_escalation_record`
- monorepo 中 controller / runtime / eval 的 authority boundary

这些对象之所以适合上提，不是因为它们“底层”，而是因为它们已经显露出跨领域可复用的 contract 形态。

## 哪些东西必须继续留在 med-autoscience

`med-autoscience` 不应被抽空。它未来仍然应是一个厚实现 repo。

必须继续留在这里的，包括：

- 医学 startup / analysis / reporting contract
- 医学 overlay、route bias 与 publication gate
- 临床队列、纳排、终点、亚组、paper framing 等医学语义
- 医学 Figure / Table publication shell
- 医学 display template catalog 与 publication-ready 质量门控
- 医学 evidence package 与 manuscript terminology redline
- 与 `MedDeepScientist` 强耦合的医学运行 glue

这些内容的价值恰恰来自医学专业性，不应被伪装成“通用 core”。

## 触发单列 research-foundry 的条件

下面这些条件至少满足大部分时，才适合把 `research-foundry` 正式单列：

1. 已经出现第二个真实的非医学 implementation，而不只是概念上的 future domain
2. 已经有一批共享 contract 能在两个 domain 中原样复用，而不是靠名字相似
3. 共享 vocabulary 已经完成明显的 domain-neutral 化，不再依赖医学术语解释
4. 依赖方向已经能稳定表达为：
   - framework core -> domain implementation
5. `med-autoscience` 当前活跃主线不再处于高频 contract 重写期
6. 单列不会显著打断现有运行、测试、发布与 GitHub 公开面

如果上述条件还不满足，那么 `Research Foundry` 更适合继续作为上层框架身份露出，而不是立即变成新的物理主仓库。

## 推荐的三阶段迁移方式

### Phase 1：口径先行

先在公开面明确：

- `Med Auto Science` 是 `Research Foundry` 的医学实现
- `Research Foundry` 是上层 `Research Ops framework`

这一阶段不改 repo slug，不做大规模代码搬迁。

### Phase 2：抽离共享内核

在仍以 `med-autoscience` 为主战场的前提下：

- 识别真正通用的 contract / substrate
- 把它们改写成 domain-neutral vocabulary
- 收紧依赖方向
- 明确哪些对象以后必须从 core 暴露，哪些只能由 medical pack 持有

这一阶段的重点是收敛边界，不是追求“尽快新建 repo”。

### Phase 3：单列 research-foundry

当共享内核已经稳定，且第二个 domain 确实开始落地时：

- 新建 `gaofeng21cn/research-foundry`
- 把已经成熟的共享 core 迁入
- 由 `med-autoscience` 明确依赖 `research-foundry`
- 在 `OPL` 顶层与两个 domain repo 中同步公开入口

## GitHub 公开面应如何呈现

单列之后，公开表面应是：

- `one-person-lab`
  - 顶层 federation / gateway 入口
- `research-foundry`
  - 通用 `Research Ops framework`
- `med-autoscience`
  - `Research Foundry` 的医学实现

届时：

- `research-foundry` README 负责解释 core、shared contracts 与 implementation map
- `med-autoscience` README 负责解释医学 implementation、医学交付面与医学 runtime
- `one-person-lab` README 负责解释三者在联邦中的位置

## 明确的非目标

这条路线当前明确不做以下事情：

- 不把 `RedCube AI` 并入 `Research Foundry`
- 不把所有 `Presentation Ops` 语义强行塞进 `Research Ops core`
- 不把 `med-autoscience` 改写成“无领域颜色”的空壳
- 不为了抢先创建 `research-foundry` repo 而提前搬迁尚未冻结的 contract

## 最终判断

未来正确的结构应是：

```text
OPL / One Person Lab
  -> Research Foundry
      -> Med Auto Science
      -> Future Domain Implementation A
      -> Future Domain Implementation B
```

因此，`research-foundry` 与 `med-autoscience` 的关系不是“谁取代谁”，而是：

- 一个提供共享骨架
- 一个提供医学实现

未来确实会有一部分底层上提到 `research-foundry`，但只会上提已经证明为跨学科通用的那一层，不会把 `med-autoscience` 的医学专业面整体搬空。
