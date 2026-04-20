# 当前状态

**更新时间：2026-04-20**

## 当前角色

- `Med Auto Science` 是面向专病研究的医学研究工作台，负责研究问题进入、工作区语境、证据推进、人话进度和论文相关文件交付。
- 仓库首页负责用户入口；`CLI`、`MCP`、`controller` 负责操作与自动化入口。
- `OPL` 是上层整合入口；`Med Auto Science` 也可以直接使用。
- 上游 `Hermes-Agent` 指外部运行时目标与监管责任方；当前受控研究后端继续是 `MedDeepScientist`。

## 当前推荐使用方式

- 用户视角：给出病种、数据、目标问题和期望论文结果，在同一个工作区里持续推进研究。
- 研究推进视角：围绕同一条课题线管理问题定义、证据补足、进度反馈和文件交付。
- 命令行操作视角：当前最小操作路径仍是 `product-frontdesk`、`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress` 这一组接口。

## 当前执行与监管模型

- 当前仓库跟踪主线继续按 `Auto-only` 理解。
- 默认执行仍继承本机 `Codex` 配置；仓库侧监管继续围绕外部运行时目标做状态检查和恢复判断。
- 方向锁定后的普通科研推进、论文质量判断与 `bounded_analysis` 一类有限补充分析默认由 `MAS` 自主完成。
- `MDS` 侧的 `publishability_gate_mode` 与 base skill 本地附加层清理继续服务 authority 去重；通用研究阶段纪律继续沿 `DeepScientist` / `MDS` base skill 维护，医学质量、医学稿件规则、submission hygiene 与 `publication gate` blocker 继续由 `MAS` 的 study charter、overlay、ledger、controller surface 承担。
- human gate 收口到方向重置、重大 claim 边界变化和投稿前最终审计。
- 关键持久表面继续围绕 `study_charter`、`evidence_ledger`、`review_ledger`、`study_runtime_status`、`runtime_watch`、`publication_eval/latest.json`、`controller_decisions/latest.json`。
- 关键身份继续围绕 `program_id`、`study_id`、`quest_id`、`active_run_id`；用户面优先呈现 `study_id`、任务摘要、阻塞和下一步。

## 当前边界

- `Med Auto Science` 负责研究入口、工作区权威语义、证据推进和论文交付。
- 研究者与课题负责人继续负责方向设定、重大边界变化和投稿前审计。
- 期刊投稿和外部系统交互继续由人工监督。
- `OPL` 集成、`product-entry manifest`、`handoff envelope` 和其他机器可读桥接继续留在集成层与参考层阅读。

## 当前维护重点

1. 保持 `README*` 与 `docs/README*` 继续面向医生、课题负责人和潜在使用者。
2. 保持 `docs/project.md`、`docs/status.md`、`docs/architecture.md` 对齐同一套产品边界、执行回路和 owner 层级。
3. 保持 `product-frontdesk`、`workspace-cockpit`、`submit-study-task`、`launch-study`、`study-progress` 作为 MAS 的核心可执行回路，同时保持 `CLI`、`MCP`、`controller` 作为正式操作与自动化入口。
4. 保持 `Hermes-Agent` 作为外部长期在线网关的 readiness 检查，并把维护者细节继续留在 reference / program 层。
5. 把“医学论文质量 + 长时间全自动驾驶优化”正式收口到 `MAS` 单项目主线，由 `controller_charter / runtime / eval_hygiene` 共同承担 owner；`MDS` 迁移期角色继续收敛为 research backend、行为等价 oracle、上游 intake buffer。
6. 把 study charter 升级为质量总合同入口；`paper evidence ledger` 与 `review ledger` 作为该合同的执行与审阅记录，统一承载主结果、`bounded_analysis`、reviewer concern 与 submission hygiene 的落地状态。
7. 把“持续学习 `DeepScientist` 方法论”收口为 `MAS` 的长期 program lane：维护者先读 [MedDeepScientist Method Learning Disciplines](./program/med_deepscientist_method_learning_disciplines.md)、[MedDeepScientist Continuous Learning Plan](./program/med_deepscientist_continuous_learning_plan.md) 和 [MedDeepScientist Upstream Source Provenance](./program/med_deepscientist_upstream_source_provenance.md)，先区分“upstream learned common research discipline”和“MAS-own governance / medical-quality surfaces”，再决定哪些 lesson 进入 `controller_charter`、`runtime`、`eval_hygiene` owner 面，哪些继续留在 `MDS` 的 oracle / intake / parity companion 面。
