# Platform Operating Model

`MedAutoScience` 默认按 `Agent-first, human-auditable` 的方式运行。

对外，它是疾病研究与 manuscript-delivery 方向的独立 medical research domain agent。
对内，`Domain Harness OS` 只作为 controller、runtime、eval、delivery 的边界层与执行层语言保留；旧 `domain gateway` 语料只在历史/参考文档中解释。

这不是一句 README 口号，而是平台级操作约束：

- 人类主要负责提出研究任务、提供或更新数据、审核关键结果、做最终决策
- `Codex` 这类 Agent 主要负责读取 workspace 状态、调用平台 controller、协调 MAS Runtime OS / Progress Portal / Artifact OS / Quality OS 与外挂工具、组织论文交付
- `MedAutoScience` 自身负责提供稳定、可验证、可审计的 domain-agent entry 接口，而不是要求人手工维护底层状态文件

在 `OPL` 联邦链路里，推荐始终按下面这条理解：

`Human / Agent -> OPL stage-led framework or direct MAS skill -> MedAutoScience domain-agent entry -> MAS controller/runtime/quality/artifact surfaces`

这意味着：

- `OPL` 是完整智能体运行框架，可托管 stage attempt、queue、wakeup、retry/dead-letter、approval、projection 和 shared lifecycle/index 能力；它不替代 `MedAutoScience` 的医学研究 owner 身份。
- `Stage` 是一次大型任务步骤；`Codex CLI` 是 stage 内默认 concrete executor 和最小执行单元。
- OPL provider-backed stage runtime 是当前 generic runtime owner；`MAS Runtime OS` 只承担 MAS domain runtime adapter、owner receipt、typed blocker、event refs、guarded apply 与 diagnostic surface；`MedDeepScientist` 只保留 frozen source archive、historical fixture、explicit archive import reference、backend audit、upstream intake 和 parity oracle。
- OPL provider / Temporal 只能承载、唤醒、记录和派发 attempt；`hermes_agent` 只作为显式非默认 executor/proof lane，旧 Hermes provider 或 local scheduler 只作 history/provenance/dev/CI/offline diagnostic，不持有 MAS study truth、publication quality、artifact authority 或 current package。

旧定位说明已归档到 [Historical Framework Positioning](../../history/runtime/historical_framework_positioning.md)。当前 active 口径以独立 medical research domain agent 与 OPL stage-led framework 托管边界为准。

## Domain Agent 与 Harness OS 的分工

### Domain agent entry 负责

- 暴露面向人类与 Agent 的正式 domain 入口
- 固定 workspace / profile / controller / overlay / adapter 的稳定接口
- 保持公开定位、entry contract、核心 docs 与审计边界清晰
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

### OPL / Codex 执行层

- `OPL` 提供 stage-led runtime framework、provider abstraction、queue、signal/query、receipt 和跨 domain projection。
- `Codex CLI` 在 MAS stage 内承担默认具体执行：读取 stage packet、调用 MAS controller/工具、产出修复、分析、写作和验证结果。
- `MedDeepScientist` / `DeepScientist` 只作为历史来源、显式归档导入、backend audit、upstream intake 或 parity oracle；不再作为 MAS 默认执行层。

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
- stage / overlay
  - 把医学前验、stage packet、质量约束和 route-back 规则前移到 MAS stage
- portfolio / studies / runtime artifacts
  - 作为人类审核面和长期审计面

这些操作面属于 `MedAutoScience` 的 domain-agent 对外控制表面；它们驱动的 controller、runtime、eval、delivery 链条，则属于内部 execution/runtime surface。
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
5. `Codex CLI` 在 MAS stage packet 约束内执行实验、写作、修复和交付准备。
6. `MedAutoScience` 在关键节点执行 publication gate、data-asset gate、AI reviewer、medical publication surface 等治理。
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
