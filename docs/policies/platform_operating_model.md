# Platform Operating Model

`MedAutoScience` 默认按 `Agent-first, human-auditable` 的方式运行。

对外，它是 `Research Ops` 的 `domain gateway`。
对内，它是承载 controller、runtime、eval、delivery 的医学自动科研 `Domain Harness OS`。

这不是一句 README 口号，而是平台级操作约束：

- 人类主要负责提出研究任务、提供或更新数据、审核关键结果、做最终决策
- `Codex` 这类 Agent 主要负责读取 workspace 状态、调用平台 controller、协调 `MedDeepScientist` 与外挂工具、组织论文交付
- `MedAutoScience` 自身负责提供稳定、可验证、可审计的 gateway 接口，而不是要求人手工维护底层状态文件

在 `OPL` 联邦链路里，推荐始终按下面这条理解：

`Human / Agent -> OPL Gateway -> MedAutoScience domain gateway -> MedAutoScience Domain Harness OS -> runtime / eval / delivery surfaces`

这意味着：

- `OPL Gateway` 不替代 `MedAutoScience`
- `MedDeepScientist` 当前是 harness OS 中最重要的 runtime executor 之一，但不等于整个 harness OS
- future monorepo 的 `controller_charter / runtime / eval_hygiene` 应被理解为 harness OS 内部主模块，而不是对外 gateway 的替代品

更系统的定位说明见：[Domain Gateway And Harness OS](../domain_gateway_harness_os.md)

## Gateway 与 Harness OS 的分工

### Domain gateway 负责

- 暴露面向人类与 Agent 的正式 domain 入口
- 固定 workspace / profile / controller / overlay / adapter 的稳定接口
- 保持公开定位、entry contract、project-truth 与审计边界清晰
- 防止调用方绕过正式入口直接碰内部 runtime

### Domain harness OS 负责

- 持续执行、记录、治理和交付 domain work
- 承载 controller、runtime、eval、delivery 的长期运行链
- 持久化 authority artifact、评估结论、交付结果与回溯线索
- 让研究推进不是一次性脚本，而是可恢复、可审计、可持续的运行底座

## 角色分工

### 人类

- 给出高层目标，例如想做哪类医学论文、希望优先哪条临床主线
- 提供新数据、修订意见、期刊偏好和临床解释反馈
- 审阅图表、稿件和关键停止/继续决策

### Agent

- 读取 profile、workspace、study、runtime、portfolio 的当前状态
- 优先在高可塑性、易形成阳性证据包的研究路径中做选题与切换
- 调用 controller 和 overlay 完成数据治理、门控、交付同步与实验编排
- 在弱结果方向上尽快止损，而不是默认把整条线做完

### MedDeepScientist

- 作为底层自动科研执行引擎，负责 scout、idea、experiment、write、finalize 等任务推进
- 由 `MedAutoScience` 这个 domain gateway / harness OS 控制面注入医学特化 overlay、研究偏置和论文门控

### ToolUniverse 与公开数据侧挂

- 不是主控
- 只在功能分析、知识检索、通路/调控解释、公开数据扩展或证据加固时挂接

## 稳定操作面

平台默认希望 Agent 使用稳定的 gateway / controller 接口，而不是直接编辑状态文件。

当前正式操作面包括：

- profile
  - 定义 workspace、runtime、publication profile、overlay scope、研究偏置和默认 archetype
- formal-entry matrix
  - `CLI`：默认 formal entry
  - `MCP`：supported protocol layer
  - `controller`：internal control surface
- overlay
  - 把医学前验约束前移到 `MedDeepScientist` 的关键 stage
- portfolio / studies / runtime artifacts
  - 作为人类审核面和长期审计面

这些操作面属于 `MedAutoScience` 的 domain gateway 对外控制表面；它们驱动的 controller、runtime、eval、delivery 链条，则属于内部 harness OS 的运行表面。
当前 repo-tracked 产品主线按 `Auto-only` 理解；未来若要做 `Human-in-the-loop` 产品，应作为兼容 sibling 或 upper-layer product 复用同一 substrate，而不是把当前仓改成同仓双模。

对 workspace 的状态 mutation，默认遵循以下原则：

- 优先通过 controller 完成，而不是手工改 `registry.json`、`status.md`、临时脚本输出
- mutation 必须落盘，并可回溯到具体 payload、时间戳和刷新结果
- 人类审核应面向 report、summary、draft、final delivery，而不是底层中间状态

## 默认执行逻辑

一次标准的医学自动科研推进，默认按以下链路组织：

1. Agent 读取 profile，并对目标 workspace 执行 bootstrap / overlay 检查。
2. Agent 检查数据资产状态，包括私有版本、公开数据机会、startup readiness。
3. Agent 按研究偏置策略，优先选择高可塑性、易形成医学证据包的课题 archetype。
4. Agent 为当前 quest 安装或重覆写医学 overlay，把门控与写作约束前移到执行阶段。
5. `MedDeepScientist` 负责实验、写作和交付主链推进。
6. `MedAutoScience` 在关键节点执行 publication gate、data-asset gate、medical publication surface 等外层治理。
7. 若主线结果偏弱，Agent 应尽快止损、改题、补 sidecar 或切换路线，而不是继续空转。
8. 当证据面足够时，平台导出投稿包，并同步到 study 的正式交付路径。

## 研究路线偏置

平台默认不优先选择“一个固定临床假设先钉死，再赌阳性结果”的路线。

更推荐的，是以下这类可塑性更高、可通过 AI/统计/建模继续优化和扩展证据面的路线：

- 临床风险分层 / 分类器
- 数据驱动亚型重构
- 外部验证与模型更新
- 灰区分诊
- 公开数据与机制扩展 sidecar
- 基于通用大模型构造面向临床窄任务的专用智能体

是否采用某一类路线，不由底层引擎自由漂移决定，而由 profile、policy、overlay 和 controller 共同约束。

## 人类审核面

平台默认把以下内容视为人类审核优先面：

- `portfolio/data_assets/startup/latest_startup_data_readiness.json`
- `portfolio/data_assets/impact/latest_impact_report.json`
- `portfolio/data_assets/mutations/*.json`
- `runtime/quests/<quest>/reports/`、`summary.md`、`draft.md`
- `studies/<study-id>/.../final/` 下的正式交付物

这意味着：

- 人类不需要记住底层命令
- 人类也不需要手工维护 registry
- 人类主要看审计结果、证据包、图表和稿件

## 平台边界

`MedAutoScience` 不是完全脱离人类监督的黑箱自动化。

它的目标是：

- 让 Agent 成为主操作员
- 让平台状态更新更稳定
- 让医学论文生产更可控
- 让人类把时间放在研究判断、临床解释和投稿决策上
