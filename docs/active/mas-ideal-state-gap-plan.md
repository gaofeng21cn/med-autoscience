# MAS 开放证据差距

本文只持有尚需实际验收的差距。产品目标见 [理想态](../references/positioning/mas_ideal_state.md)，实现职责见 [架构](../architecture.md)，当前状态的读取方法见 [状态](../status.md)。

## 当前需证明的结果

| 验收对象 | 需要的证据 | Owner |
| --- | --- | --- |
| 持久运行与恢复 | 同一 identity 的 StageRun/Attempt、重启恢复、retry/dead-letter 与持续运行 readback | OPL runtime |
| 真实论文推进 | canonical artifact delta、MAS owner receipt、route-back、stable blocker 或 human gate | MAS study |
| 独立审阅与发表判断 | 当前 artifact/source/rubric 绑定、独立 session、六域 currentness 与 publication verdict | MAS quality/publication |
| 已安装专业能力 | 实际 carrier、required ScholarSkills presence/callability，以及 selected build 要求的具体 validator 符号 | Package/carrier 与 ScholarSkills |
| 当前修订交付 | revision intake 被当前 generation 消费、完整 submission tree 的 receipt 与当前 manifest | MAS publication + OPL artifact transport |
| 生产无越权写入 | 真实 owner/provenance、受权写集和目标侧 readback | 各运行与领域 owner |

这些是验收条件，不是声称所有实例均有故障的任务表。重新立项时须补充当前目标、可复现缺口、负责人及关闭条件；没有新鲜实例证据，不复制旧 DM002/DM003 状态或历史 worklist。

闭合项退出本计划；证据留在其运行账本、产物、owner receipt 或提交中。稳定约束折回对应 policy/contract 说明，不追加完成清单或下一轮 Agent 提示词。
