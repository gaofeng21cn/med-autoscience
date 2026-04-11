# Unified Harness Engineering Substrate 下的 Domain Harness OS 定位

## 文档目的

这份文档用于统一内部口径：`Med Auto Science` 不是一个独立新造的公共基础框架，而是运行在共享 `Unified Harness Engineering Substrate` 上的医学 `Research Ops` `Domain Harness OS`。

## 1) 在 Unified Harness Engineering Substrate 中的位置

可按下面这条链路理解：

`User / Agent -> OPL Gateway（可选）-> Unified Harness Engineering Substrate -> Med Auto Science（医学 Domain Harness OS）-> 受控 MedDeepScientist surface`

其中：

- `Unified Harness Engineering Substrate` 提供跨域共享的工程约束与运行基础
- `Med Auto Science` 负责医学领域合同、研究推进与交付治理
- `Hermes` 负责当前默认 outer runtime substrate owner 的 controller-facing contract
- `MedDeepScientist` 负责被调用的 controlled research backend execution surface，不承担 `Domain Harness OS` 的全部职责

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

当前 repo-tracked 默认 runtime 形态不是继续深化旧 `Codex-default host-agent runtime`，而是：

- `MedAutoScience` = 唯一研究入口与 domain gateway
- `Hermes` = 默认 outer runtime substrate owner
- `MedDeepScientist` = controlled research backend
- 旧 `Codex-default host-agent runtime` = 只保留为迁移期对照面与 regression oracle

在该形态下：

- formal-entry matrix 固定为：
  - `default_formal_entry = CLI`
  - `supported_protocol_layer = MCP`
  - `internal_controller_surface = controller`
- 当前 repo-tracked 产品主线按 `Auto-only` 理解；future `Human-in-the-loop` 产品应作为 sibling 或 upper-layer product 复用同一 substrate
- 运行推进通过 `Hermes -> MedDeepScientist` 的受控 surface 完成
- `Med Auto Science` 作为 `Domain Harness OS`，负责控制面、合同面和审计面
- `MedDeepScientist` 作为执行面，不被表述为系统本体

## 5) 当前 execution handle contract

当前主线至少要区分四层身份：

- `program_id`
  - 当前 `research-foundry-medical-mainline` 的 control-plane / report-routing 指针
- `study_id`
  - 医学 study 的持久聚合根身份
- `quest_id`
  - 受控 `MedDeepScientist` managed quest 的正式运行句柄
- `active_run_id`
  - 当前 live daemon run 的细粒度执行句柄

这四者不能互相替代，尤其不能把 `active_run_id` 或 `quest_id` 倒灌成上层 study / control-plane 身份。

## 6) 当前 durable surface contract

当前主线下，至少以下表面必须继续被理解为 canonical durable surface：

- `runtime_binding.yaml`
- `study_runtime_status`
- `runtime_watch`
- `studies/<study_id>/artifacts/publication_eval/latest.json`
- `ops/med-deepscientist/runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
- `studies/<study_id>/artifacts/controller_decisions/latest.json`
- `studies/<study_id>/artifacts/runtime/last_launch_report.json`

## 7) 未来 managed web runtime（同一底座）下的不变项

如果迁移到同一 `Unified Harness Engineering Substrate` 上的 managed web runtime，下列内容保持不变：

- 医学领域 contract 语义
- 关键 artifact schema
- 可审计决策链与 mutation 追踪要求
- `Med Auto Science` 与执行 surface 的边界定义

允许变化的部分：

- host 生命周期管理方式
- 调度与权限托管方式
- 运行入口的部署形态（本地/托管）

## 8) 边界声明

- 不把当前表述夸大为“已经形成独立公共代码框架”
- 不把 `MedDeepScientist` 等同为 `Med Auto Science` 本体
- 不因为未来托管形态而稀释当前医学 `Domain Harness OS` 的职责
- external `Hermes` runtime repo / workspace / daemon truth 未清除前，不把 repo-side contract 冻结误写成 external cutover 完成
