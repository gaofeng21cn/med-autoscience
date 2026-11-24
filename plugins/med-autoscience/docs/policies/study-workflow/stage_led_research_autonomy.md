# 医学研究阶段自治、人机分工与 Frontier 边界

Owner: `MedAutoScience`
Purpose: `stage_autonomy_operating_model_and_frontier_ssot`
State: `active_policy`
Machine boundary: 可执行阶段、独立审阅角色、transition 规则、workspace artifacts 与 owner receipts 由 [Stage / Route / Handoff](../../runtime/stage_route_handoff_standard.md) 及对应机器合同持有。

## 人机操作分工

- **研究者**：提供临床问题、数据使用权限、研究目标与反馈，并决定临床解释、结论采用、伦理边界与最终投稿；优先查看当前 manuscript、分析结果、证据与审阅意见、交付 manifest 及明确的 human gate，不手工维护底层 registry。
- **Codex（默认 concrete executor）**：在 MAS Stage 目标、数据权限和医学约束内读取证据、比较路线、调用专业能力与 ToolUniverse（仅按需挂接）产生分析和稿件；选择说明 clinical relevance、source/data fit、可检验性、预期证据收益、成本、已否定路线和停止条件（不靠预设分数、固定分析清单或 [策略记忆库](../../../agent/knowledge/publication_strategy_library.md) 选择获胜路线）。
- **独立 Reviewer / Auditor**：读取当前冻结输入并作质量判断（[AI-First 质量边界](../quality/ai_first_quality_boundary.md)）。
- **OPL Framework & MAS Owner**：OPL 持有唤醒、队列、恢复、独立 Attempt/session、审批运输与只读工作台；MAS 持有医学研究 domain authority、source readiness、quality/publication verdict、artifact/memory accept/reject 与 owner receipt。通用运行成功不改变论文业务状态，也不替研究者作临床或投稿决定；MDS/DeepScientist 仅作历史来源与对照参考（[来源记录](../../references/med-deepscientist/source_provenance.json)）。

## 研究判断、证据纪律与止损

- 非 ML 研究可探索临床问题、人群/表型、数据能回答的问题、文献缺口、endpoint 与 claim 强度；ML/AI 研究须先明确 clinical bottleneck、医学先验、数据划分、评价和可改模型范围，避免只追逐 benchmark 分数。
- 优先选择高可塑性、可继续优化证据面的研究路线；每次分析保留 source、code、parameter、result、claim 与失败路径的关联。阴性、弱效应、相反或不稳定结果必须完整保留并在弱结果方向尽快止损（降级 claim、调整路线或停止 hypothesis），不以无限补分析或包装制造阳性叙事。
- 当前证据不足时选择诊断/补证、降级主张、回到最早缺陷 owner、换题或请求 human gate。涉及人群、endpoint、数据权限、临床解释和不可逆动作的变更必须重新取得相应 authority；可消费产物在质量预算耗尽时携质量债交接，真正的权限、安全、身份、来源、不可逆动作或人类决定边界保持阻断（见 [质量循环](../../runtime/progress_first_quality_loop.md)）。

## Bounded Analysis Frontier 候选板规则

`bounded_analysis` 不能变成无限分析扩张。每次补充分析必须回指当前 study charter、claim/evidence map、source refs、reviewer concern 或 controller route-back reason。Stage 内可维护 `research_frontier_board`（可物化为 `<study_root>/artifacts/stage_outputs/<stage>/research_frontier_board.json`），仅作为 Stage-local 比较和审计面（记录 `candidate_id`、`route_meaning`=`explore|exploit|fusion|debug|stop`、`target_claim_or_concern`、`expected_evidence_gain`、`cost_and_risk`、`clinical_interpretability`、`decision` 与 `decision_reason`），不创建 Stage 外 Frontier Plane，也不能自行放行扩大 primary claim、重定义人群/endpoint、引入新数据权限边界或授权 quality/publication/artifact/`current_package` 更新。

- **Plateau 止损规则**：新分析只重复已有结论、结果改善无法转化为临床解释或 reviewer concern closure、分析需突破 study charter/数据权限边界，或 claim 需靠 post-hoc 叙事维持时，必须考虑 `stop` 或 route-back。
- **Closeout 与记忆连续性**：每次结束须在 artifacts/closeout 留下 accepted/rejected candidates、selected path 或 stop reason、failed paths、consumed/produced refs、reviewer concern closure status、next route（decisive Attempt 选择的 canonical Stage）及下一 owner 所需证据，不能只存在于聊天。跨论文可复用经验须形成 proposal 经 MAS memory owner 接受，当前论文结果留在 evidence/review/trajectory（见 [策略记忆政策](./publication_route_memory_policy.md)）。
