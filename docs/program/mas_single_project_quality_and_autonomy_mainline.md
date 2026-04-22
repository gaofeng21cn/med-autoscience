# MAS Single-Project Quality And Autonomy Mainline

这份文档把“医学论文质量优化 + 长时间全自动驾驶优化”的主体正式收口到 `MedAutoScience` 单项目主线。

它回答六个问题：

1. 为什么优化主体放在 `MAS`
2. `MDS` 在迁移期只保留什么角色
3. 医学论文质量优化在单项目目标下会怎么变化
4. 长时间全自动驾驶优化在单项目目标下会怎么变化
5. 这条主线按阶段如何落地
6. 这条主线完成到什么程度才算过线

## 核心判断

从现在开始，新增的“论文质量 + 全自动驾驶”优化主投入统一服务 `MAS` 单项目主线；方向锁定之后，普通科研推进、论文质量判断、reviewer concern 排序、证据充分性判断与 `bounded_analysis` 一类有限补充分析推进默认由 `MAS` 自主完成；human gate 收口到重大边界与最终投稿前审计；`MDS` 收敛为迁移期 research backend、行为等价 oracle、上游 intake buffer。

## 当前 tranche

当前 active tranche 已经固定，不再讨论主方向本身，而是把主线压成一套可验收的 `MAS` truth：

1. **质量闭环结构化**
   让 `study_charter`、`paper evidence ledger`、`review ledger` 形成同一条质量总合同与执行记录，覆盖方向锁定后的普通科研推进、论文质量裁决、`bounded_analysis` 边界、reviewer concern 处理与 submission hygiene。
2. **用户可见真相投影**
   让 `study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json` 形成同一条用户可见、维护可审计的 truth projection，能够解释当前阶段、关键证据、阻塞、下一步、恢复点和 human gate 原因。
3. **proof / soak 口径收紧**
   让 proof 直接围绕真实 study 的长期自治、质量裁决与前台 truth 是否一致展开；让 soak 直接围绕长时间运行、停滞恢复、有限补充分析自动收口、投稿前审计前的持续推进是否成立展开。

这意味着当前 tranche 的判断标准已经从“是否还有双边 owner”切换为“`MAS` 是否已经形成单一 owner truth，`MDS` 是否只剩迁移期 oracle / backend / intake buffer 角色”。

当前 repo-side 已经开始把这件事压成可读、可测的具体 truth：

- 质量闭环不再只写成泛化 blocker，而是要求说清当前是同线质量修复还是 `bounded_analysis`，以及为什么要回到该现有主线。
- 当 `publication_eval/latest.json` 已经把当前 blocked route 收口成 `bounded_analysis`，且 `publication_gate` 只剩 scientific-anchor 冻结、paper-facing surface repair、display/export refresh、submission-minimal replay 或 stale delivery replay 这类可确定修复项时，`study_outer_loop` 会把这条同线 route-back 前推成一次 `run_gate_clearing_batch`，先清当前 gate，再把 study 送回同一条托管主线。
- 用户可见面不再把质量修复、有限补充分析、runtime recovery、human gate 混成同一种“待确认”，而是要求投影出不同 owner 语义。
- 这条 gate-clearing batch 同时服务三个目标：对质量面，它并行清掉当前论文线里可确定修复的稿面/锚点/交付阻塞；对自治面，它把“先清 gate 再继续”保留在 controller-owned continuation 链里；对 single-project 边界，它继续只写 `publication_eval`、`controller_decisions`、`artifacts/controller/gate_clearing_batch/latest.json` 与 gate replay 这组既有 `MAS` durable surface。
- program 口径不再把 `MDS` 当作长期并行 owner，而是把它固定在 oracle / backend / intake buffer 三个迁移期角色里。

这个 tranche 的 repo-side 落点也需要说清楚：

- 当前 tranche 落的是 `MAS` 单项目 owner truth、程序边界、用户可见 boundary 和对应 mainline/docs 口径。
- 当前 tranche 不把 `physical monorepo absorb`、跨仓 `runtime core ingest`、更成熟的 hosted direct product entry 当作验收项。
- 当前 tranche 允许继续保留 `MDS`，但保留的理由只能是 controlled research backend、行为等价 oracle、上游 intake buffer。

## 当前 tranche 的主张

当前 tranche 有四条必须同时成立的主张：

1. 方向锁定后，普通科研推进、质量判断与有限补充分析默认由 `MAS` 自主完成。
2. human gate 只保留重大边界、外部授权与最终投稿审计，不再承担日常质量裁决。
3. `MDS` 的存在只能解释为迁移期 oracle / backend / intake buffer，不再解释为长期双 owner、双治理面或双入口产品。
4. 用户看到的进度、阻塞、证据与下一步，必须直接来自 `MAS` 的 durable truth，而不是额外的人肉解释层。

围绕这四条主张，当前 tranche 还额外带一条收口纪律：

- 当前 tranche 的完成信号是 repo-tracked truth 闭合，不是 `physical monorepo absorb` 已启动；物理吸收和更大结构调整继续留在 post-gate phase。

## 1. 为什么优化主体在 MAS

`MAS` 已经承担医学研究的正式入口、study authority、workspace authority、证据推进、进度投影和人工决策点，因此它天然适合成为质量与自治能力的 owner。

把优化主体放在 `MAS` 有五个直接收益：

1. 医学论文质量可以前移到研究启动处统一定义。研究问题、终点、证据边界、目标期刊、发表口径、局限性约束都能在同一条主线上冻结。
2. 全自动驾驶可以由同一个控制面治理。启动、暂停、恢复、人工确认、升级、收口都能挂在同一套 study truth 上。
3. 质量门和自治门可以共用一份 durable truth。study charter 持有质量总合同，研究设计、主实验、有限补充分析、写作、评审、交付沿着同一份执行账本推进。
4. 用户认知会更稳定。对内对外都围绕 `MAS` 理解当前主线，维护面、产品面、program 面保持一致。
5. 单项目投入的复用率更高。医学研究方法、发表 hygiene、自治治理、workspace 可见性都能沉淀成平台能力，直接服务长期主线。

因此，这条优化主线的 owner 判断固定为：

- `controller_charter`：负责研究启动合同、study charter 质量总合同、journal/reporting/evidence contract、human gate 边界
- `runtime`：负责长时间自治、运行治理、恢复链路、study truth 投影
- `eval_hygiene`：负责 baseline、analysis、paper evidence ledger、review ledger、submission hygiene，并把执行结果持续回写到 charter contract

## 2. MDS 在迁移期只保留什么角色

`MDS` 的迁移期角色收敛为三类：

1. **受控 research backend**
   承担当前仍在运行中的 inner research execution 与存量 study 兼容面。
2. **行为等价 oracle**
   作为迁移过程中的对照线，帮助 `MAS` 判断关键研究行为、长期运行语义和 durable surface 是否守住等价性。
3. **上游 intake buffer**
   承接来自 `DeepScientist` / `MDS` 线的有价值更新，经过审计、对照、验证后再决定是否吸收进 `MAS`。

围绕这三类角色，新增优化投入采用同一条原则：

- 新的 owner、主文档、主验证口径、主维护判断都放在 `MAS`
- `MDS` 负责迁移期对照、存量兼容和 intake 缓冲

这也意味着三条负面边界同样要固定下来：

- 不再把 `MDS` 写成独立产品入口。
- 不再把 `MDS` 写成长期质量治理面或自治治理面。
- 不再把 `MDS` 的保留解释成“单项目主线尚未成立”，而只解释成迁移期能力守恒与等价 proof 需要。

从主线视角看，这会带来三条立刻生效的优化取向：

- 强化研究启动合同、统一证据账本、reviewer-first 这些论文质量主动作
- 强化单一 study authority、study 级可见性、恢复与人工接手治理这些自治主动作
- 把 `MDS` 独立入口、独立质量治理、独立自治治理收敛到迁移期 companion lane

## 3. 医学论文质量优化在单项目目标下怎么变化

单项目目标下，论文质量优化的重点会从“把稿件写得更像论文”提升为“让研究从启动开始就沿着发表级标准推进”。

### 3.1 研究设计前移到 controller_charter

最有价值的投入是把医学研究设计前移到 study 启动时冻结，并由 study charter 统一承载质量总合同：

- 研究问题和临床场景
- 终点与评价口径
- 数据边界和纳排逻辑
- 外部验证与稳健性目标
- 目标期刊与写作口径
- 局限性边界和过度主张约束

这样做的价值是让后面的 baseline、experiment、analysis、write、finalize 都围绕同一份医学发表合同推进；后续的 evidence ledger 和 review ledger 负责把这份合同翻译成持续执行、持续验收的 durable record。

### 3.2 study charter 承载质量总合同，ledger 承载执行

单项目目标下，`MAS` 先在 study charter 冻结质量总合同，再让 ledger 体系承载执行。

这份合同至少覆盖：

- 研究问题与临床场景
- 核心 claim、可接受证据强度与发表口径
- 主分析与有限补充分析的边界
- reviewer concern、局限性与 submission hygiene 约束

围绕这份合同，ledger 的 owner 分工保持清晰：

- `paper evidence ledger` 记录 claim 与 evidence 的覆盖关系、主结果与补充分析的兑现情况
- `review ledger` 记录 reviewer concern、稿件风险、补充动作与当前缺口

这样可以把“质量标准是什么”和“质量标准执行到哪里了”长期放在同一条 `MAS` 主线上解释。

### 3.3 证据账本升级为 MAS 统一主账本

论文质量最关键的提升，是让 `MAS` 统一持有：

- claim 和 evidence 的对应关系
- 主结果和补充分析的覆盖关系
- reviewer concern 和补充动作的映射关系
- 当前稿件离投稿级还有哪些缺口

这会让论文质量判断从“阶段性局部判断”升级为“全链统一判断”。

### 3.4 reviewer-first 提前成为 program 常规动作

单项目目标下，reviewer-first 适合在两个时点固定执行：

1. 选定主方向后，先看 novelty、clinical relevance、证据要求、比较基线是否成立
2. 主结果出来后，再看 claim 强度、补充实验、临床解释、局限性、稿件结构是否成立

这样可以更早发现高代价返工点，让研究线围绕投稿标准持续收敛。

### 3.5 医学发表 hygiene 升级为平台能力

结构化摘要、外部验证、校准、临床效用、局限性、补充材料、投稿 bundle 这些能力，适合在 `MAS` 里沉淀成长期能力。

这条变化的含义很明确：

- 论文质量提升将主要表现为 `MAS` 对研究全过程的发表级约束更强
- 写作本身继续重要，真正拉开差距的是前置研究设计、统一证据账本和更强的 review/hygiene

### 3.6 方向锁定后的质量判断默认自治

前期质量优化的关键边界，是把“方向选择”与“方向锁定后的质量推进”分清楚。

初始方向锁定属于 human gate。方向锁定之后，`MAS` 默认自主完成普通科研与论文质量判断，包括：

- baseline 是否足够支撑当前 claim
- 主分析、补充分析、稳健性分析的优先级
- `bounded_analysis` 一类有限补充分析是否应自动推进、何时收口、何时回写 ledger
- reviewer concern 是否已经被 evidence ledger 覆盖
- 当前稿件是否具备继续写作、继续补实验、进入审阅或进入投稿包准备的条件
- 论文主张、局限性和临床解释是否匹配现有证据

human gate 收窄到少数重大边界：

- 初始研究方向锁定
- 重大研究转向
- 止损与研究终止
- 外部凭据、账户、秘密和授权
- 作者、伦理、基金、利益冲突、数据可用性、声明等投稿客观信息
- 最终投稿前审计

这个边界让 `MAS` 的质量自治从“能表达待确认点”升级为“默认持有质量裁决权”。它也为 `MDS` 迁移提供明确验收面：`MDS` 继续作为对照线证明关键研究行为和质量判断保持等价，`MAS` 逐步接管 owner、charter contract、ledger 和前台解释面。

## 4. 长时间全自动驾驶优化在单项目目标下怎么变化

单项目目标下，自治能力优化的重点会从“某个 runtime 很能跑”提升为“整个 study lifecycle 在同一控制面上可长期治理、可恢复、可接手，并能自动推进有限补充分析与质量收口动作”。

### 4.1 单一 authority 变成首要目标

长时间自治首先要求 `MAS` 成为唯一的 study authority：

- 什么时候启动
- 什么情况下暂停
- 什么情况下继续跑
- 哪些少数边界触发人类 gate
- 什么情况下收口、升级、归档

这会让自治能力从局部 runtime 能力升级为研究平台能力。

### 4.2 study 级可见性成为自治基础设施

用户和 controller 都需要持续看到：

- 当前阶段
- 最近证据
- 当前阻塞
- 监管 freshness
- 下一个动作
- 恢复点和人工接手点

这类可见性直接决定长跑稳定性，也决定“无人干预”是否还能保持可信。

### 4.3 恢复、自愈、接手走统一链路

进程中断、外部依赖漂移、研究卡住、等待人工输入、证据门未过线，都应由 `MAS` 统一判断和处理。

这里的优化重点会变成：

- 恢复语义清晰
- 自愈动作可审计
- 人工接手点明确
- 每次干预都有 durable decision record

### 4.4 预算治理成为长期自治的放大器

单项目之后，自治系统最值得提升的是“把算力、时间、证据收益、投稿价值放在同一套排序里”。  
这样系统才能更稳地决定先跑主结果、先补 `bounded_analysis`、先写稿、还是先进入重大边界审计。

### 4.5 MDS 作为影子对照线保留到等价 proof 过线

迁移期里，`MDS` 继续承担对照线价值：帮助 `MAS` 识别哪些自治行为已经成熟，哪些地方还需要 soak proof 和行为等价验证。

这里的关键约束也需要写死：`MDS` 只保留 oracle、受控 backend、upstream intake buffer 三个迁移期用途。当前 tranche 的 proof 目标是证明 `MAS` 已经能独立持有 owner judgment，而不是把 `MDS` 长期保留成第二个 owner。

## 5. 按阶段怎么落地

### Phase 1：冻结主判断

目标：

- 正式写清“优化主体在 `MAS`”
- 正式写清 `MDS` 迁移期角色
- 正式写清这条主线由 `controller_charter / runtime / eval_hygiene` 三块 owner 共同推进

交付：

- 主线文档
- `status` 可见入口
- program 层 owner 判断

### Phase 2：先把质量门和治理门上收到 MAS

目标：

- 第一刀先落 `human gate boundary policy`：明确方向锁定后的普通科研、论文质量裁决与 `bounded_analysis` 推进由 `MAS` 自主完成；human gate 只覆盖重大边界、投稿客观信息和最终投稿前审计
- 第二步建设 `study charter quality contract`：让研究问题、claim、证据强度、有限补充分析边界、submission hygiene 统一冻结在 study charter
- 第三步建设 `evidence ledger`：让 claim、analysis、figure、supplement、limitation 与投稿缺口统一落在 `MAS` durable truth 上，作为 charter contract 的执行记录
- 第四步建设 `review ledger`：让 novelty、clinical relevance、reviewer concern、补充动作和稿件风险持续可读，作为 charter contract 的审阅记录
- 第五步打通 `runtime watch -> outer-loop wakeup`：让监管信号、进度停滞、恢复动作和下一步自治裁决进入同一条 outer-loop 决策链

这个阶段里，`MDS` 继续承接迁移期 research backend 角色，`MAS` 开始成为质量和自治两条主线的实际 owner。

当前 tranche 就处在这个阶段的收口段，验收重点不再是“有没有列出更多结构”，而是下面三件事是否已经接上同一条主线：

- quality loop 已经结构化：study charter 质量总合同、evidence ledger、review ledger 可以解释同一条稿件推进线
- user-visible truth 已经投影：当前阶段、关键证据、阻塞、下一步、恢复点可以从 `MAS` durable surface 直接读出
- human gate 已经收窄：方向锁定后的日常质量裁决与 `bounded_analysis` 推进不再依赖 `MDS` 或人工兜底解释

这里还要额外卡住一条 phase 边界：

- 当前 Phase 2 收口的是 repo-tracked single-project truth，不是 post-gate `physical monorepo absorb`；只要 external/runtime/workspace gate 还没清完，就不能把物理吸收当成当前 tranche 的自然延长。

### Phase 2 当前 tranche 的最小验收口径

这个 tranche 过线至少要求：

1. `MAS` 文档已经明确把方向锁定后的普通科研推进、论文质量裁决与 `bounded_analysis` 推进写成默认自治。
2. `MAS` 文档已经明确把用户可见 truth projection 写成 durable surface 责任，而不是额外口头说明。
3. `MDS` 在同一套文档里只能被解释为 oracle / backend / intake buffer，不能再出现长期双 owner 含义。
4. 质量总合同、执行账本、前台 truth 三层之间的 owner 与关系已经能在 `MAS` program truth 里闭合。
5. 当质量闭环要求 route-back 时，`MAS` 可以把“回到哪条现有主线、该主线当前关键问题是什么、为什么这是最窄修复路径”解释成 repo-tracked truth。
6. `mainline` / `status` / program truth 已经能明确区分“当前 tranche 正在收什么”和“post-gate 才能启动的 physical monorepo / runtime core ingest”。
7. 当同线 route-back 只剩 controller 可确定修复的 batch work 时，`MAS` 已经能把它写成 `run_gate_clearing_batch` 这类 controller-owned continuation step，而不是再为这一步单独扩出新的 owner 面。

### Phase 3：做单项目等价 proof

目标：

- 让 `MAS` 的质量判断和自治判断在真实 study 上稳定成立
- 用对照线确认关键 durable surface、研究推进语义和恢复语义已经可持续复用

重点：

- 真实 study soak
- 长时间运行场景
- 人工接手与恢复场景
- 论文证据链完整性场景

### Phase 3 proof / soak 预期

进入这个阶段后，proof 与 soak 口径固定为：

1. **质量闭环 proof**
   真实 study 上，study charter 的质量总合同可以持续约束 evidence / review ledger，并支撑方向锁定后的质量裁决与 `bounded_analysis` 自动收口；当 blocked route 只剩可确定修复项时，这个 proof 也应覆盖 `run_gate_clearing_batch` 是否真的把 scientific-anchor、paper-facing surface 与 delivery blocker 收回到同一条质量主线。
2. **truth projection proof**
   用户面、维护面、controller 面读取到的当前阶段、关键证据、阻塞、下一步和恢复点来自同一组 `MAS` durable surface，文档口径与运行口径一致；同线质量修复、`bounded_analysis`、runtime recovery、human gate 四类语义不会在前台混淆。到这一步，`autonomy_soak_status`、`quality_review_followthrough`、caller-facing `return_surface_contract`，以及 `publication_eval -> controller_decisions -> gate_clearing_batch record -> publication_gate replay` 这条 same-line continuation chain 都应进入同一套 truth projection。
3. **autonomy soak**
   真实 study 的长时间推进、停滞、恢复、有限补充分析追加、human gate 升级都能在长跑中保持稳定，不需要 `MDS` 作为第二个日常 owner 介入；`workspace-cockpit`、`product-frontdesk` 和外部 caller 都能直接读到最近一次自治续跑与其确认信号。对于 `run_gate_clearing_batch` 这类 continuation step，soak 看的是系统能否先完成这一批 controller-owned repair，再继续回到同一条 paper line，而不是把它升级成新的治理面。
4. **oracle proof**
   `MDS` 只用于证明行为等价、兼容存量 study 与吸收上游更新；proof 的通过结果应表现为 `MAS` owner 面更完整，而不是 `MDS` owner 面继续扩张。`run_gate_clearing_batch` 这类同线 continuation step 也只允许强化 `MAS` controller 的 owner truth，不允许把 `MDS` 重新解释成新的 quality/autonomy owner 面。

### Phase 4：让 MAS 成为默认维护面

目标：

- 日常开发、维护、排障、质量判断、自治治理都以 `MAS` 为默认入口
- `MDS` 收敛为迁移期对照与 intake 缓冲

这一步依然不是 `physical monorepo absorb`；它收的是默认维护面和 retained-now backend 边界。

### Phase 5：完成单项目收口

目标：

- 新增主投入全部按 `MAS` 主线组织
- 旧 study、旧 artifact、旧运行轨迹都能被稳定读取和解释
- `MDS` 迁移期角色进入低频维护

`physical monorepo absorb`、`runtime core ingest` 和更大平台结构调整只在这个 post-gate 区段讨论，而且前提是前四阶段的 owner truth、proof 与 retained-now 边界已经稳定。

## 6. 验收标准

这条主线过线时，至少满足下面八条：

1. 每个关键优化 cell 都有 `MAS` owner、program 文档、验证口径和真实 study 证据。
2. 医学论文质量判断可以沿着同一条 `MAS` 主线解释清楚：study charter 质量总合同、主结果、有限补充分析、review、submission hygiene 之间关系明确。
3. 长时间自治可以沿着同一条 `MAS` 主线解释清楚：启动、运行、阻塞、恢复、人工接手、收口之间关系明确。
4. 用户在 `MAS` 主线上能看到当前阶段、关键证据、阻塞、下一步和恢复点。
5. `MDS` 的角色可以稳定描述为迁移期 research backend、行为等价 oracle、上游 intake buffer。
6. 旧的 study / artifact / runtime 轨迹都能继续被读取、审计和解释。
7. 方向锁定后的普通科研推进、论文质量裁决与 `bounded_analysis` 推进默认由 `MAS` 自主完成；human gate 边界在文档、前台投影和 durable decision artifact 中保持一致。
8. proof / soak 的通过结论会强化 `MAS` 的单一 owner truth，不会重新打开 `MDS` 作为长期双 owner 的解释空间。

## 正式主张

因此，面向未来 monorepo 的“医学论文质量 + 长时间全自动驾驶”优化，当前就应该按 `MAS` 单项目主线落地；当前 tranche 应集中完成质量闭环结构化、用户可见真相投影与 proof / soak 口径收紧；`MDS` 迁移期继续服务能力守恒、等价验证和低风险吸收，不再保留长期双 owner 含义。
