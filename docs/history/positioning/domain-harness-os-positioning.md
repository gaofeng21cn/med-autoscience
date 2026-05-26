# Unified Harness Engineering Substrate 下的 Domain Harness OS 定位

Owner: `MedAutoScience`
Purpose: `historical_positioning_reference`
State: `history_only_superseded`
Machine boundary: 本文只保存 2026-05-08 前后的旧内部定位语汇。当前 MAS 不是 generic framework/runtime owner；当前 owner 边界以 [MAS 理想目标态](../../references/positioning/mas_ideal_state.md)、[MAS 理想目标态差距与完善计划](../../active/mas-ideal-state-gap-plan.md)、核心五件套和 durable runtime/controller surfaces 为准。

Superseded reading note: 本文中的 `Unified Harness Engineering Substrate`、`Domain Harness OS`、`MAS Runtime OS`、local scheduler 默认链路和 MDS 迁移链路，均不得作为当前 active truth、默认 runtime topology、generic framework owner 或兼容接口保留理由。当前口径是 OPL 持有通用 stage-led framework/runtime primitive，MAS 持有 medical research domain truth 与 domain package 薄程序面。

## 文档目的

这份文档用于统一内部口径：`Med Auto Science` 不是一个独立新造的公共基础框架，而是运行在共享 `Unified Harness Engineering Substrate` 上的医学 `Research Ops` `Domain Harness OS`。
当前状态说明（2026-05-08）：本文保留为内部 harness/substrate 边界参考。当前公开第一身份是独立 medical research domain agent 与单一 MAS app skill；`Domain Harness OS` 词汇只用于内部执行、治理与兼容边界。文中涉及 MDS 的旧执行链路均按 historical / migration reference 理解，不能作为当前默认 runtime dependency。

## 1) 在 Unified Harness Engineering Substrate 中的位置

本节是 2026-05-08 口径的历史图示；今天不能据此把 `MAS Runtime OS` 读成 MAS 自有默认 runtime / scheduler owner。当前默认 hosted autonomous runtime 归 OPL/Temporal，MAS 保留医学 domain truth、authority refs、owner receipts、typed blockers 和必要 authority functions。

可按下面这条链路理解：

`User / Agent -> MAS app skill / MedAutoScience domain-agent entry -> MAS Runtime OS / Artifact OS / Quality OS -> runtime / eval / delivery surfaces`

其中：

- `Unified Harness Engineering Substrate` 提供跨域共享的工程约束与运行基础
- `Med Auto Science` 负责医学领域合同、研究推进与交付治理
- `MAS Runtime OS` 在本文历史语境中曾指 controller-facing runtime contract；当前不能作为 MAS 默认 runtime owner 读取
- `MedDeepScientist` 只保留 frozen source archive、historical fixture 和 explicit legacy diagnostic / provenance reference，不承担默认执行面

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

## 4) 历史默认 runtime 形态

下列形态是本文写作时的历史 closeout 口径，已经被当前 `OPL/Temporal hosted autonomous runtime + MAS domain authority refs` 口径取代，不能作为今天的默认 runtime topology、scheduler owner 或兼容保留理由：

- `MedAutoScience` = 唯一研究入口与 domain-agent entry
- `MAS Runtime OS` = 历史 controller-facing runtime owner / substrate 语汇
- `MAS supervision scheduler contract` = 历史外层监管调度 owner 语汇；默认 local scheduler / tick script 不能作为当前 MAS generic scheduler 或 worker residency owner 复活
- `MedDeepScientist` = frozen source archive、historical fixture、explicit legacy diagnostic / provenance reference
- 旧 `Codex-default host-agent runtime` = 本机外部 caller / 历史对照面；当前 stage 内第一公民 executor 是 `Codex CLI`，hosted runtime owner 是 OPL/Temporal

在该历史形态下：

- formal-entry matrix 固定为：
  - `default_formal_entry = CLI`
  - `supported_protocol_layer = MCP`
  - `internal_controller_surface = controller`
- 当时 repo-tracked 产品主线按 `Auto-only` 理解；future `Human-in-the-loop` 产品应作为 sibling 或 upper-layer product 复用同一 substrate
- 当时外层监管通过 `scheduler adapter -> MAS Runtime OS` 的受控 tick 完成；该 local scheduler / MAS Runtime OS 链路今天只能作为历史 closeout provenance 读取
- `Med Auto Science` 当时作为 `Domain Harness OS` 被描述为控制面、合同面和审计面 owner；今天该语汇不能替代 MAS 标准 OPL Agent owner 边界
- `MedDeepScientist` 不作为执行面或系统本体

## 5) 历史 execution handle contract

本文当时的主线至少要区分四层身份；今天若要判断 execution handle / attempt / stage identity，必须回到当前 contracts、runtime/controller surfaces 和 OPL provider attempt refs：

- `program_id`
  - 当前 `research-foundry-medical-mainline` 的 control-plane / report-routing 指针
- `study_id`
  - 医学 study 的持久聚合根身份
- `quest_id`
  - MAS managed quest 的正式运行句柄
- `active_run_id`
  - 当时 MAS runtime run / supervision tick / execution receipt 的细粒度执行句柄

这四者不能互相替代，尤其不能把 `active_run_id` 或 `quest_id` 倒灌成上层 study / control-plane 身份。

## 6) 历史 durable surface contract

本文当时列出以下 canonical durable surface。今天的 durable surface 以当前 `contracts/`、runtime/controller surfaces、真实 workspace artifact、owner receipts 和 active docs 为准；下列路径只作为历史 provenance 和迁移线索读取：

- `runtime_binding.yaml`
- `study_runtime_status`
- `runtime_watch`
- `studies/<study_id>/artifacts/publication_eval/latest.json`
- `runtime/quests/<quest_id>/artifacts/reports/escalation/runtime_escalation_record.json`
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
- 不因为未来托管形态而稀释当时医学 `Domain Harness OS` 的职责；今天该说法必须折回 MAS 标准 OPL Agent owner 边界
- external `Hermes` runtime repo / workspace / daemon truth 未清除前，不把 repo-side contract 冻结误写成 external cutover 完成
