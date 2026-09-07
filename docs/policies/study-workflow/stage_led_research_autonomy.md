# 医学研究阶段自治

本文只定义研究思考的自由度与证据纪律。可执行阶段、独立审阅角色和 transition 规则由 [Stage handoff](../../runtime/stage_route_handoff_standard.md) 与其机器合同持有。

## 研究判断

Codex 在当前 Stage 目标、用户意图、数据权限和医学约束内形成候选问题、分析与解释。声明给出目标、可用能力、证据要求和禁止动作；不通过预设分数、固定分析清单或记忆卡片选择获胜路线。

非 ML 研究可以探索临床问题、人群/表型、数据能回答的问题、文献缺口、endpoint 与 claim 强度。ML/AI 研究还须先明确 clinical bottleneck、医学先验、数据划分、评价和可改模型范围；算法创新不能只追逐 benchmark 分数。

选择需要说明 clinical relevance、source/data fit、可检验性、预期证据收益、成本、已否定路线和停止条件。研究路线经验见 [策略记忆库](./publication_route_memory_library.md)，它只提供参考。

## 证据与变化

每次分析保留 source、code、parameter、result、claim 与失败路径的关联。阴性、弱效应、相反或不可识别结果也是科学产物，不能隐藏、改写 primary endpoint 或以无限补分析制造阳性叙事。

当前证据不足时，选择有边界的诊断/补证、降低主张、回到最早缺陷 owner、换题或请求 human gate。涉及人群、endpoint、数据权限、临床解释和不可逆动作的变更必须重新取得相应 authority；普通质量不足不自动变成运行阻断。

可消费产物在质量预算耗尽时携质量债继续交接；真正的权限、安全、身份、来源、不可逆动作或人类决定边界保持阻断。具体规则见 [质量循环](../../runtime/control/progress_first_quality_loop.md)。

## 记忆与连续性

上下文来自当前 study artifacts、source/文献和 MAS 接受的领域记忆。每次 closeout 留下 consumed/produced refs、选择理由、failed paths、未解决问题及下一 owner 所需证据，不能只存在于聊天。

跨论文可复用经验先形成 proposal，经 MAS memory owner 接受或拒绝。当前论文结果留在 evidence/review/trajectory，不升级为通用经验或下一篇论文的证据。详见 [记忆政策](./publication_route_memory_policy.md)。

不存在 MAS 私有 research scorer、route orchestrator、outer loop 或 knowledge-plane materializer 的默认调用链。执行、恢复、独立 Attempt 与通用 projection 属于 OPL；医学判断与 artifact authority 属于 MAS。
