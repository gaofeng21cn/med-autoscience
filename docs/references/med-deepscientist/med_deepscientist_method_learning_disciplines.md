# MedDeepScientist Method Learning Disciplines

这份文档把 `MedAutoScience` 从 `MedDeepScientist` / `DeepScientist` 持续学习时应固定的研究行为纪律沉淀为 repo-tracked program truth。

它回答四个问题：

1. 这轮演进里最值得长期学习的优化是什么
2. 这些优化为什么对 `MAS` 的“长时间自治 + 高质量医学论文”主线有价值
3. `MAS` 应该按什么纪律去学，而不是把学习动作做成零散 intake
4. 哪些能力已经适合进入 `MAS` owner 面，哪些继续留在 `MDS` 迁移期 companion 面

## 1. 当前前提

这份学习纪律建立在当前固定边界之上：

- `MAS` 是唯一研究入口、study / workspace authority owner、医学论文质量 owner、长时间自治 owner。
- `MDS` 当前角色收敛为 controlled research backend、行为等价 oracle、上游 intake buffer。
- 学习目标是把高价值研究行为沉淀为 `MAS` 自己的合同、文档、测试与 durable surface。
- 学习动作服务 `MAS` 主线，不服务独立 `MDS` 日常运维面的继续膨胀。

## 2. 这轮最值得持续学习的五类优化

### 2.1 先冻结研究合同，再启动长期执行

这轮最有价值的优化，是把研究目标、证据边界、期刊口径、补充分析边界、人工 gate 提前冻结，而不是把这些判断留到运行中临时决定。

对 `MAS` 的启发很直接：

- `controller_charter` 要成为 study 启动时的总合同入口。
- `study charter` 要提前承载 claim、evidence、journal、risk、bounded analysis 边界。
- 长时间自治的前提是先把“研究往哪里收敛”定义清楚。

### 2.2 用单条研究主线贯通 baseline、experiment、analysis、write、finalize

`DeepScientist` 体系里最强的地方之一，是把研究推进理解为一条可持续接力的 program，而不是若干互相断开的工具调用。

对 `MAS` 的价值有三层：

- 论文质量提升来自整条研究主线的持续收敛。
- 自治稳定性来自跨阶段的 durable continuity。
- 维护成本下降来自 owner、文档、控制面和前台解释面都围绕同一条主线组织。

### 2.3 把研究过程沉到 durable surface，而不是只留在对话和临时运行态

这轮演进持续强化了任务、文件、分支、artifact、memory、decision 的落盘与可追溯性。对于医学研究域，这种优化直接决定了长时间自治是否可信。

对 `MAS` 的核心启发：

- `study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json` 这类 durable surface 要继续做厚。
- `paper evidence ledger` 与 `review ledger` 要成为质量治理的常驻主账本。
- 前台解释、人工接手、恢复和最终投稿审计都应读取 durable truth，而不是读取局部运行日志。

### 2.4 让 interrupt / resume / replan 成为正式研究治理动作

`DeepScientist` 的另一个高价值点，是把打断、续跑、改计划、切分任务、恢复现场做成正式能力。对医学研究主线来说，这类能力直接决定长期自治是否有韧性。

`MAS` 在这条线上要学到的不是某个具体交互形式，而是三条治理原则：

- 每次暂停、恢复、升级、人工接手都要有明确 decision record。
- 外环 controller 要能把进度停滞、证据不足、外部依赖缺失翻译成正式状态。
- bounded analysis、reviewer concern、submission hygiene 补动作要进入可审计的 outer-loop 决策链。

### 2.5 把“持续学习”本身变成受控 program

这轮最重要的方法论收获，是学习动作本身也需要 owner、阶段、入口和验收面。

对 `MAS` 来说，持续学习 `DeepScientist` 不是一次性吸收，也不是按 commit 追赶，而是一条长期 program：

- 从真实研究行为里抽象可复用纪律
- 把纪律翻译成 `MAS` 的合同和验证口径
- 在真实 study 上证明这些纪律带来更强的质量与自治
- 继续保留 `MDS` 作为 oracle 和 intake buffer，直到等价 proof 过线

## 3. 为什么这些优化对 MAS 有价值

## 3.1 它们服务 MAS 的真实目标函数

`MAS` 的目标函数已经固定为“长时间自治 + 高质量医学论文”。这要求系统同时做好四件事：

1. 研究方向一旦锁定，就能围绕明确 claim 和 evidence contract 持续推进。
2. 运行过程长、跨阶段、可恢复时，系统仍能维持稳定治理。
3. 论文质量判断、补充分析、reviewer concern 处理和 submission hygiene 可以沿同一条主线解释。
4. owner 边界、文档入口、验证口径和前台可见性保持一致。

上面五类优化正好分别补强这四件事，因此它们适合进入 `MAS` 主线。

## 3.2 它们降低 MAS 后续吸收成本

如果现在只把 `MDS` 当成执行黑盒，后面每吸收一项能力都要重复做一次 owner 重划、语义翻译和测试补课。先把行为纪律沉到 `MAS`，后续的物理吸收、合同吸收和 cutover proof 会更轻。

## 3.3 它们让医学研究判断更可审计

高质量医学论文依赖的不是一次性写作润色，而是整条研究链路上的判断质量。研究合同、evidence ledger、review ledger、runtime decision record 越完整，`MAS` 越能把“为什么继续、为什么补分析、为什么可以收口投稿”解释清楚。

## 4. MAS 持续学习时应遵守的纪律

### 4.1 先学行为，再学实现

每次从 `DeepScientist` 线吸收内容时，优先回答四个问题：

1. 它提升的是哪一类研究行为
2. 这类行为落在 `controller_charter`、`runtime`、`eval_hygiene` 中的哪个 owner
3. 它需要新增或收紧哪份 repo-tracked contract
4. 它的 proof surface 是文档、测试、真实 study 证据中的哪些

### 4.2 先把 lesson 写成 MAS truth，再考虑是否做物理吸收

一个 lesson 只有进入下面这些面，才算真正被 `MAS` 学到：

- `docs/project.md`、`docs/architecture.md`、`docs/status.md` 这一层的 owner 与入口说明
- `docs/program/`、`docs/runtime/` 这一层的 program truth 和 contract truth
- 对应的 `tests/*`、`make test-meta`、必要的 targeted regression
- 至少一个真实 study 或真实维护场景的验证证据

### 4.3 按 owner 面吸收，避免把 MDS 再写成默认 authority

凡是属于研究入口、study authority、外环治理、质量判断、长期维护入口的 lesson，都应优先进入 `MAS`。

继续留在 `MDS` 的内容主要有三类：

- 提高 oracle 置信度的对照能力
- 提高 upstream intake 审计质量的能力
- 为旧 quest / workspace / artifact 提供迁移期参考面的能力

### 4.4 学习动作也要受验证约束

只要一个 lesson 会改变 docs surface、runtime contract surface、quality gate surface 或 operator 判断，就必须补上对应验证。文档先行可以成立，文档漂移不成立。

## 5. 这条学习主线在 MAS 内部的 owner 映射

| 学习主题 | 主要 owner | 进入 MAS 后的主落点 | 典型 proof |
| --- | --- | --- | --- |
| 研究合同前置 | `controller_charter` | study charter、gate policy、status/program docs | contract docs、meta tests、真实 study charter |
| 单主线研究推进 | `controller_charter` + `eval_hygiene` | quest/study program、evidence/review ledger、delivery plane | docs、ledger tests、真实研究轨迹 |
| durable truth 与前台可见性 | `runtime` + `eval_hygiene` | `study_runtime_status`、`runtime_watch`、`publication_eval`、progress projection | runtime tests、meta tests、fresh runtime evidence |
| interrupt / resume / replan 治理 | `runtime` | supervision loop、outer-loop decision、controller decision record | runtime tests、真实恢复场景 |
| 持续学习 program | `controller_charter` + `runtime` + `eval_hygiene` | `docs/program/`、intake / parity / oracle gate、长期主线 status | docs、merge gate、parity proof |

## 6. 当前还应留给 MDS 的迁移期职责

在当前阶段，下面这些内容继续适合留在 `MDS` 迁移期 companion 面：

1. controlled research backend 的真实执行生态
2. behavior oracle 与 parity replay
3. upstream intake buffer 与差异审计
4. 旧 quest / workspace / artifact 的兼容读取参考面

这四类职责为 `MAS` 持续学习提供稳定参照，也保证学习动作有真实对照线。

## 7. 什么时候可以说 MAS 学会了一项方法论

一项来自 `DeepScientist` 线的方法论，只有同时满足下面五条时，才应视为已经被 `MAS` 学会：

1. 该能力的 owner 已经落在 `MAS` 的 `controller_charter`、`runtime` 或 `eval_hygiene` 之一。
2. 对应 repo-tracked 文档已经把边界、入口、语义和目标说清楚。
3. 至少有一条测试或 meta verification 在守住这项能力的 contract。
4. 至少有一类真实 study 或真实维护场景证明它改善了质量或自治。
5. `MDS` 仍可作为对照线说明等价性、兼容性或尚未吸收的剩余部分。

满足这五条之后，`MAS` 学到的是长期可维护的方法论资产。
