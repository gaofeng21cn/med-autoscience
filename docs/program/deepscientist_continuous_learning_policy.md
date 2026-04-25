# DeepScientist Continuous Learning Policy

这份政策把 `MAS` 持续学习上游 `DeepScientist` 的方式规范下来。

它处理的是长期 owner 问题：即使 `MedDeepScientist` 未来被 `MAS` 完全吸收，`MAS` 仍然应持续观察、学习和选择性吸收 `DeepScientist` 的研究 workspace 方法论。

## 核心原则

`MAS` 学习 `DeepScientist`，学习的是可迁移的研究系统能力，而不是追随仓库形态、UI 外观或 provider 配置。

学习对象按 owner truth 固定为三类：

- behavior：长期研究如何保持连续、可接管、可恢复、可审计。
- contract：这些行为如何落到 `MAS` 的 study / runtime / publication / controller 合同。
- packet：每个研究阶段如何留下可接力的 objective、evidence、route outcome、resume point 和 failed-path 记录。

明确不学习三类内容作为 MAS 主线：

- provider：上游新增 provider、connector、账号配置、商业入口或 hosted 产品路径。
- UI：workspace、settings、copilot、modal、附件预览等产品界面形态。
- marketing：产品文案、商业化表述、demo 包装或非医学研究 owner surface。

长期学习对象固定为五类：

1. durable continuity spine：任务、文件、artifact、memory、branch、terminal 如何组成可恢复研究状态。
2. takeover / resume control surface：暂停、接管、继续、停止、消息排队和人工介入如何进入正式治理链。
3. inspectable workspace：Web、TUI、文件、Canvas、terminal 如何让用户看见研究过程并随时接管。
4. stage operational packets：scout、baseline、idea、analysis、write、finalize、decision 如何用 SOP 和模板稳定推进。
5. failed-path learning：失败路线、winning path、reproduction lesson 和 retry/refresh 机制如何沉淀到下一轮。

## Owner 边界

- `DeepScientist` 是持续学习对象和通用研究 workspace 方法来源。
- `MedDeepScientist` 是当前迁移期 backend、behavior oracle、upstream intake buffer 和 parity companion。
- `MAS` 是医学研究 owner，负责把上游 lesson 翻译成医学研究合同、质量账本、runtime governance、用户可见进度和投稿交付表面。

因此，任何吸收都必须落成 `MAS` 自己的 owner truth：

- 文档必须写清楚 lesson 映射到哪个 MAS owner 面。
- contract 必须使用 MAS 的 study / publication / controller 术语。
- 测试必须验证 MAS 表达，而不是只证明 upstream 有这个功能。
- MDS 被进一步吸收后，本政策仍继续生效，只是 intake buffer 从 fork checkout 转为 source-watch / parity fixture / upstream-reading workflow。

## Intake 节奏

每次 DeepScientist 学习 intake 先做方法层 triage，再决定是否进入代码层吸收。

当维护者说“学习一下 `DeepScientist` 的最新更新”“看看 `DeepScientist` 最近更新有什么值得吸收”或类似表达时，默认启动一轮执行型 learning-and-landing intake，而不是只读调研。具体触发语义、固定阅读入口、decision matrix、worktree 并行规则、验证门槛和完成定义见 [DeepScientist Latest-Update Learning Protocol](./deepscientist_latest_update_learning_protocol.md)。

### 方法层 triage

必须回答：

1. 这个变化强化了哪一类长期能力？
2. 它对应 MAS 的哪个 owner surface？
3. 需要代码吸收、文档规范、测试约束，还是只需保留观察记录？
4. 它是否会削弱 MAS 的医学质量 gate、publication gate 或 human gate？

### 代码层吸收

只有在下面条件同时满足时才吸收代码：

- 变化能被切成边界清晰的小 slice。
- slice 不要求 MAS 追随 upstream UI / provider / product 面。
- slice 可以通过 MAS 自己的 contract 或测试验证。
- slice 不把 MDS 重新抬升为医学质量 authority。

## 当前固定学习面

当前 `MAS` 把 DeepScientist lesson 固定映射到四条主线：

1. `controller_charter`：研究合同、route-back、human gate、decision record。
2. `runtime`：runtime_watch、outer-loop wakeup、takeover/resume/mailbox semantics。
3. `eval_hygiene`：evidence ledger、review ledger、publication_eval、submission blocker。
4. `workspace_projection`：study-progress、product-entry、artifact inventory、用户可见恢复点。

## 必须保留的审计痕迹

每轮 intake 至少留下一个 repo-tracked 记录，写明：

- upstream range 或 commit。
- 学到的 method lesson。
- MAS owner surface。
- absorption decision：`adopt_contract`、`adopt_template`、`adopt_code_slice`、`watch_only`、`reject`。
- 验证方式。

推荐入口：`docs/program/deepscientist_learning_intake_YYYY_MM_DD.md`。

## 禁止事项

- 不把 upstream 大包 merge 当成学习。
- 不把 provider、商业化入口、UI 文案更新当成 MAS 主线能力。
- 不把 provider / UI / marketing 变化升级成 MAS behavior、contract 或 packet。
- 不让上游 prompt 或 workflow 直接覆盖 MAS 医学研究合同。
- 不用 memory 替代 study-level durable truth。
- 不用 MDS fork 现状限制 MAS 的长期学习面。
