# DeepScientist Learning Intake 2026-04-25

本轮 intake 基于 fresh `git fetch upstream` 后的 `DeepScientist upstream/main`，观察范围为 `e539e2e..710792e`。

目标不是同步上游代码，而是把 DeepScientist 近期强化的“长期研究伙伴”能力翻译成 `MAS` 可维护的 owner truth。

## 上游变化摘要

近期上游变化集中在五组：

1. `artifact: add overwrite baseline refresh flow`
2. `daemon: prioritize new user messages over retry backoff`
3. `skills: refine idea, analysis, and write SOPs`
4. `feat: add idea draft template and attachment preview modal`
5. `ui: update workspace, settings, and copilot surfaces`

## MAS 吸收决策

| Upstream change | Lesson | Decision | MAS owner surface | 落地方式 |
| --- | --- | --- | --- | --- |
| `daemon: prioritize new user messages over retry backoff` | MDS retry priority | `adopt_code_slice` | runtime control surface | 新用户输入必须 preempt retry/backoff，进入 durable mailbox / takeover semantics，且不启动第二个 authority writer |
| `artifact: add overwrite baseline refresh flow` | baseline refresh | `adopt_contract` | runtime / eval_hygiene | 将 overwrite 约束为 medical baseline refresh record，要求 affected surfaces、verification refs 和 route decision |
| `skills: refine idea, analysis, and write SOPs` | stage operational packets / SOP | `adopt_template` | controller_charter / eval_hygiene | 医学化 stage packet 覆盖 idea objective contract / candidate board、analysis bounded campaign、write evidence-bound repair、finalize submission truth、decision route outcome |
| quest / artifact / memory continuity reinforcement | durable continuity spine | `adopt_contract` | runtime / workspace projection | 明确 artifact、memory、execution evidence 在 MAS 的职责分工 |
| workspace visibility and recovery affordances | inspectable workspace | `adopt_contract` | product-entry / study-progress | 将 workspace 可见性表达为 artifact inventory、恢复点和可接管状态 |
| failed-path and reproduction notes | failed-path learning | `adopt_contract` | portfolio memory / evidence-review | 失败路线和 reproduction lesson 进入 durable truth 或 reusable memory 的边界 |
| `feat: add idea draft template and attachment preview modal` | idea template shape and attachment visibility | `watch_only` | workspace projection | 只观察交互形态；MAS 不把 modal / product UI 当作 owner truth |
| `ui: update workspace, settings, and copilot surfaces` | UI / product shell | `watch_only` | none | 保留为可见性参考，不追随 upstream UI 包 |
| provider / connector / commercial entry changes | provider / connector surface | `reject` | none | 不吸收 provider 配置扩面、connector 入口或 marketing surface |

## 不吸收的内容

本轮不追随 upstream UI 大包、provider 配置扩面、商业化入口和产品文案变化。

这些变化可以作为 workspace interaction 参考，但不应改变 MAS 的医学研究 owner 边界。

## 验证口径

本轮落地必须满足：

- `docs/program/deepscientist_continuous_learning_policy.md` 固定长期学习政策。
- runtime 文档明确 takeover / resume / mailbox semantics。
- stage 模板文档明确医学研究阶段 packet 的 durable outputs。
- meta 测试锁住政策入口与本轮 intake 记录，避免后续学习主线漂移。
