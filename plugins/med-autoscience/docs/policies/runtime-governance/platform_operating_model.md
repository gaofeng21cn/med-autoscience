# 人与 Agent 的操作分工

本文只定义医学研究中的角色分工。接口与 runtime 关系见 [架构](../../architecture.md)，科研探索规则见 [阶段自治](../study-workflow/stage_led_research_autonomy.md)。

研究者提供临床问题、数据使用权限、目标与反馈，并决定结论采用、伦理边界与最终投稿。Codex 在 MAS Stage 中读取证据、比较路线、调用专业能力、产生分析和稿件；独立 reviewer/auditor 读取当前冻结输入并作质量判断。MAS owner 消费这些证据并作领域裁决。

OPL 持有托管执行、独立 Attempt/session、恢复、receipt 与只读工作台；通用运行成功不改变论文业务状态，也不替研究者作临床或投稿决定。

人类优先查看当前 manuscript、分析结果、证据与审阅意见、交付 manifest 以及明确的 human gate。机器状态从 JSON/contract 读取，不要求用户维护底层 registry。

阴性、弱效应或失败分析应完整保留并形成诚实的下一步判断。是否补证、降低主张、转向或停止，由当前医学证据和用户目标决定，不把追求阳性结果作为默认策略。
