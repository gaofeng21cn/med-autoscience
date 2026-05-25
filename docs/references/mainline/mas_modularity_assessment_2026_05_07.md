# MAS Modularity Assessment 2026-05-07

Status: `architecture fitness wave landed; hub role hardening landed`
Date: `2026-05-08`
Owner: `MedAutoScience`
Purpose: `Preserve MAS mainline architecture and quality reference analysis.`
State: `support_reference`
Machine boundary: Human-readable reference only; current architecture and quality truth remains in source, contracts, tests, diagnostics, active gap plan, and verification receipts.

## 结论

MAS 当前已经从“文件被迫切小”推进到“主要 owner 与 projection 边界可识别”的阶段。本评估后续触发的一轮 architecture fitness wave 已经落地到 `main`：原先的 `exec(compile(...))` 拼接、nested `_parts`、near-limit part、oversized runtime execution facade 和 `study_progress_parts/shared_base.py` 大桶都已收口到自然子域，boundary fitness 现在是 `0 blocking / 0 advisory`。

按架构质量判断，MAS 已满足继续推进真实 product/runtime 工作的结构门槛：依赖方向干净、主要 truth owner 已固定、public surface 与内部实现边界基本分离。

但它还没有达到理想意义上的高聚合、低耦合。当前更准确的判断是：

- `低耦合方向性` 已经较好：Sentrux DSM 显示 `above_diagonal=0`，没有发现依赖逆流；boundary fitness 没有 blocking 或 advisory finding。
- `高聚合` 处于中等偏好：自然子域已经大量形成，已确认的机械结构债已清掉；剩余风险主要来自少数高 fan-in/fan-out hub 随功能增长继续膨胀。
- `边界明确性` 明显优于上一轮：Runtime Control、Progress Projection、Delivery Sync、Product Entry、Publication/Delivery、Display/MCP 都有 owner 子域；后续风险主要来自少数中心 projection/entry/read-model 模块继续增长。

因此，后续不需要再开一条“全仓大重构”主线。更合适的做法是把结构治理变成每条功能 lane 的 architecture fitness budget：每次动到高风险模块，就顺手把该模块内的自然边界压实；不为了指标单独拆行为稳定的模块。

2026-05-08 的 hub role hardening 已把这条判断落成 repo guard：Runtime Supervisor、Product Cockpit、MCP Adapter 和 Display Validation 不再按文件数量继续拆，而是固定成 authority / read-model / adapter / materializer 四类角色。`module_boundary_audit` 与 `architecture_owner_boundary` 现在会 fail-closed 检查非 authority hub 是否声明 authority、控制 runtime/publication 或写 truth surface。下一步 portfolio 队列仍保持 workspace layout 去 MDS/DS 化、profile/entry compatibility retirement、MDS no-history physical absorb。

## Fresh Evidence

本评估基于当前 `main` 的 fresh read：

2026-05-08 复核：模块化治理后的关键结构信号没有漂移。Sentrux fresh scan 仍为 `quality_signal=6076`，DSM `above_diagonal=0`、`propagation_cost=63`；`.sentrux/rules.toml` 尚未定义额外架构规则，因此当前 hard gate 继续以 repo guard、boundary fitness、line budget 和 DSM 方向性为准。

| signal | current value | interpretation |
| --- | ---: | --- |
| Sentrux `quality_signal` | `6076` after wave; assessment baseline was `6156` | 本轮结构拆分降低了 Sentrux 单点分数，但 DSM 与 boundary fitness 均未退化；后续以 `above_diagonal=0` 和 boundary fitness 为硬门槛，quality drift 需要结合 diff 解释。 |
| Sentrux DSM `above_diagonal` | `0` | 依赖方向干净，没有发现跨层逆向依赖。 |
| Sentrux `propagation_cost` | `63` | 变更传播面仍偏大，说明 hub 模块仍多。 |
| Sentrux root causes | acyclicity `10000`; redundancy `8431`; depth `5000`; modularity `4688`; equality `4188` | 没有循环是优势；模块均衡性和模块化仍是短板。 |
| Boundary fitness | `0 blocking`, `0 advisory` | 原评估的 `31 advisory` 已通过 architecture fitness wave 清零。 |
| Line budget | pass | 当前 repo guard 可运行，触碰过的 near-limit part 已降到 preferred range。 |
| Mechanical split residue | no tracked `part_*` / `chunk_*` / `split_*` source file | 没有明显编号式机械拆分回流。 |
| Direct test-gap heuristic | low direct ratio | 许多行为通过 public/facade tests 覆盖，后续高风险子域应补更贴近 natural boundary 的 focused tests。 |
| 30-day churn | `product_entry`、`study_progress`、`cli`、`study_runtime_decision`、`domain_health_diagnostic`、display surfaces 最高 | 热点与 public entry / projection / display mainline 高度重合，说明结构风险集中在真实维护面。 |

Sentrux `git_stats` 不能直接跑在 relative worktree extension 上；本次通过兼容 clone 读取 30 天演化信号。该演化信号只用于定位 hotspot，不作为完成性证明。

## Current Strong Boundaries

### Authority / Truth Boundary

`StudyTruthKernel`、`RuntimeHealthKernel`、`study_macro_state`、`owner_route`、AI reviewer-backed `publication_eval/latest.json`、`controller_decisions/latest.json` 和 canonical artifact proof 已经把核心 authority 分开。这个层次的边界是当前最重要的成果：entry projection、MCP、workspace cockpit、product-entry 和 OPL handoff 都只能消费 truth，不能重新解释下一步。

### Runtime Control Boundary

Runtime Control 现在围绕 `owner_route -> consumer latest -> executor dispatch -> rescan` 展开。supervisor scan、consume、execute-dispatch、platform repair、AI reviewer request 和 publication gate request 已有可区分 owner。它的结构价值在于把 runtime liveness、publication blocker、AI reviewer 队列和 artifact freshness 从一个 tick 里的混合判断拆成路由票据。

### Progress Projection Boundary

Progress Projection 已经把用户可见状态压到 `study_macro_state -> user_visible_projection`。CLI markdown、MCP compact/markdown、workspace cockpit、product-entry caller projection 不再各自拼当前阶段、下一步和 package state。该边界应被视为“行为 contract”，后续只允许扩展 read model，不应回到各入口自行判断。

### Artifact / Delivery Boundary

Delivery Sync 已从旧 helper/facade 大桶进入输入解析、delivery context、materialization、render/report 的 pipeline。Publication/delivery、submission_minimal 和 current_package projection 的 authority 边界比此前清楚：delivery mirror 不成为 edit source，package rebuild proof 才支撑交付判断。

### Runtime Lifecycle / Storage Boundary

SQLite runtime authority、runtime lifecycle ledger、restore-proof archive、quest Git retirement 和 workspace root Git retirement 已经把 runtime/state index 与 paper/publication/artifact truth 分离。这个边界降低了 `.ds` 小文件膨胀对源码和业务状态的污染。

## Remaining Coupling Hotspots

这些不是立即 blocker，但应作为后续开发时的优先关注点。

| area | evidence | risk | preferred handling |
| --- | --- | --- | --- |
| runtime execution / platform repair | runtime dispatch 与 platform repair 仍是高 fan-in control hub，但当前 boundary fitness 清零 | 新 controller action 容易继续堆到同一层 | 新 action 进入 action family / lifecycle / receipt 子域，保持 `owner_route -> consumer latest -> executor dispatch`。 |
| product-entry / workspace cockpit | cockpit read model、brief rendering、manifest projection 仍是高 churn entry surface | caller projection 易重新承担 authority 判断 | 只消费 progress/runtime/publication projection，新增 payload assembly 按 workspace cockpit 子域落点。 |
| study progress / MCP adapter | progress projection 是稳定核心，MCP 与 markdown 仍是高调用入口 | adapter 容易重新拼装用户状态 | `study_macro_state -> user_visible_projection` 继续是唯一状态链，MCP 只做 tool-result rendering。 |
| publication / delivery | delivery、publication gate、medical surface reporting 已拆成自然子域 | 产物 mirror 与 authority source 容易混用 | 真实入口和产物等价测试优先，delivery mirror 不成为 edit source。 |
| display materialization / layout QC | display family 是自然大域，registry/validator 仍高 churn | 新 display contract 容易形成规则大桶 | 按 display family / schema family / validation phase 分组，保留 public registry。 |
| `profiles` | import fan-in 约 `60` | 配置模型是必要 shared hub，但变更影响面大 | 把 profile schema 稳定化，新增读取逻辑走 read model / adapter，避免各 controller 直接解释 profile 细节。 |

## Cohesion / Coupling Judgment

### 高聚合

当前高聚合做得较好的区域：

- runtime lifecycle / storage：SQLite、ledger、restore proof、quest materializer 的职责集中。
- progress projection：用户可见状态与入口投影集中到一个 read model。
- delivery sync：交付 pipeline 开始围绕自然步骤组织。
- owner boundary：study truth、runtime health、quality judgement、artifact proof 和 observability 已明确分层。

当前高聚合不足的区域：

- product-entry / workspace cockpit 仍承担多种 caller projection 与 human brief 渲染。
- study progress 仍同时覆盖 runtime context、quality followthrough、markdown rendering 和 publication runtime。
- display materialization 仍是一个大能力族，内部规则很多但 public registry 边界较清楚。

### 低耦合

低耦合方向性很好，证据是 DSM 没有逆向边和循环。但变更传播成本仍偏高，原因是：

- public entry/projection 文件天然被多处调用；
- profiles、publication eval、study charter、submission layout 这类 shared contract 是必要中心；
- tests 仍大量通过 aggregate entrypoint 验证，直接子域测试覆盖不均。

这意味着 MAS 现在不是“耦合混乱”，而是“中心 contract 多、hub 风险高”。解决方式不是继续减少文件数量，而是让 hub 只保留 contract/read-model/adapter/materializer 角色，不再混入 owner 判断或重业务实现。本轮已把这个结论落实到四个高风险 hub：supervisor scan 只消费 canonical runtime facts / owner route 后生成 action projection，workspace cockpit 只消费 progress/runtime/publication compact projection，MCP 只做 tool registry / handler adapter / renderer，display validation 只返回 validation/materialization verdict。

## Program Impact

Runtime Control 与 Progress Projection 已经完成本阶段最关键的行为边界收口。后续 program queue 不应再把它们作为独立大重构主题反复打开，而应作为所有后续 lane 的前置 contract：

1. 新功能不得绕开 `study_macro_state` 和 `owner_route` 自行解释用户状态或下一步。
2. 新 runtime action 不得绕开 consumer latest / executor dispatch 直接写 paper 或 package。
3. 新 product-entry / MCP / OPL projection 不得创建第二套 progress 或 publication authority。
4. 新结构治理只能在 owner 子域内优化 importable module，不改变 durable payload shape。
5. 新增或修改中心 hub 时必须声明 `hub_role`，read-model / adapter 不得写 authority surface、绕过 `study_macro_state` / `owner_route` 做 owner 判断，materializer 必须有明确受控写入范围。

当前 portfolio 下一步仍应保持：workspace layout 去 MDS/DS 化、profile/entry compatibility retirement、MDS no-history physical absorb。模块化治理作为横向 fitness budget 随这些 lane 执行，不单独抢占产品队列。

## Recommended Fitness Budget

后续每条涉及 repo source 的 lane 至少执行以下结构预算：

- 不新增 tracked `part_*`、`chunk_*`、`split_*` 文件。
- 不新增 `exec(compile(...))` 拼接加载。
- 不新增接近 1000 行的新 part；已有 near-limit part 被触碰时，应优先自然拆分。
- 不让 `product_entry`、`study_progress`、`mcp_server`、`cli` 入口重新承载 authority 判断。
- `module_boundary_audit` 和 `architecture_owner_boundary` 的 hub role guard 必须保持 green；projection/read-model/adapter hub 的 authority drift 是 blocking。
- 触碰 Runtime Control 或 Progress Projection 时，必须有 focused public-surface tests 验证 payload shape 和行为等价。
- 触碰 high-churn hub 时，补一个贴近自然子域的 focused test，而不是只依赖顶层 aggregate test。

验证入口保持：

- `scripts/verify.sh structure`
- `make test-meta`
- 对应 public-surface focused tests
- `git diff --check`

Sentrux `quality_signal` 不需要每次单点提高，但不得在无解释情况下退化；DSM `above_diagonal` 必须保持 `0`。
