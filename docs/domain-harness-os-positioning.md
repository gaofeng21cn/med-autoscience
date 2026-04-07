# Unified Harness Engineering Substrate 下的 Domain Harness OS 定位

## 文档目的

这份文档用于统一内部口径：`Med Auto Science` 不是一个独立新造的公共基础框架，而是运行在共享 `Unified Harness Engineering Substrate` 上的医学 `Research Ops` `Domain Harness OS`。

## 1) 在 Unified Harness Engineering Substrate 中的位置

可按下面这条链路理解：

`User / Agent -> OPL Gateway（可选）-> Unified Harness Engineering Substrate -> Med Auto Science（医学 Domain Harness OS）-> 受控 MedDeepScientist surface`

其中：

- `Unified Harness Engineering Substrate` 提供跨域共享的工程约束与运行基础
- `Med Auto Science` 负责医学领域合同、研究推进与交付治理
- `MedDeepScientist` 负责被调用的执行 surface，不承担 `Domain Harness OS` 的全部职责

## 2) 继承的统一约束（来自共享底座）

本项目继承并遵循以下共享约束：

- 主链路约束：能力表达优先走 `policy -> controller -> overlay -> adapter`
- contract-first：先定义稳定 contract，再扩展执行实现
- mutation 可审计：重要状态变化要有可追踪落盘，不允许只停留在会话中
- 错误显式化：不做静默纠偏，输入/状态不合法时必须报错并可追踪
- 迁移兼容：接口语义不能绑定单一 host 的临时执行习惯

## 3) 保留的 domain-specific contract（医学领域不抽空）

在继承统一底座的同时，以下医学合同保持由本仓库负责：

- 研究资产合同：变量定义、终点定义、纳排语义与数据可用范围
- 课题推进合同：从清洗/登记到分析/验证/证据组织/投稿交付的阶段约束
- 决策合同：继续/停止、改题、sidecar 补充的审计化决策面
- 交付合同：稿件、图表、补充材料、submission package 的一致性要求

## 4) 当前默认 runtime 形态

当前默认本地执行形态是 `Codex-default host-agent runtime`。

在该形态下：

- 运行推进通过受控 `MedDeepScientist` surface 完成
- `Med Auto Science` 作为 `Domain Harness OS`，负责控制面、合同面和审计面
- `MedDeepScientist` 作为执行面，不被表述为系统本体

## 5) 未来 managed web runtime（同一底座）下的不变项

如果迁移到同一 `Unified Harness Engineering Substrate` 上的 managed web runtime，下列内容保持不变：

- 医学领域 contract 语义
- 关键 artifact schema
- 可审计决策链与 mutation 追踪要求
- `Med Auto Science` 与执行 surface 的边界定义

允许变化的部分：

- host 生命周期管理方式
- 调度与权限托管方式
- 运行入口的部署形态（本地/托管）

## 6) 边界声明

- 不把当前表述夸大为“已经形成独立公共代码框架”
- 不把 `MedDeepScientist` 等同为 `Med Auto Science` 本体
- 不因为未来托管形态而稀释当前医学 `Domain Harness OS` 的职责
