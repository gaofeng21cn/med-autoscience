# MAS 知识与记忆

MAS 使用 [OPL 长期知识生命周期](https://github.com/gaofeng21cn/one-person-lab/blob/main/contracts/opl-framework/durable-knowledge-lifecycle-contract.json)。正文用 Markdown，目录只保存身份、适用阶段、来源、审阅日期和取代关系。

通用研究方法、投稿套路和审稿经验由 agent/knowledge/ 持有，统一登记到 contracts/durable_knowledge_catalog.json。研究组偏好和跨研究经验进入工作区 shared/memory/；一个研究的设计选择、失败路径与决策进入该项目 memory/；当前队列、期刊要求、投稿状态等时点事实进入该项目 state/。后三层分别使用 OPL 的 opl_durable_knowledge_catalog.json，不维护 MAS 私有索引或种子应用器。

阶段执行通过 OPL 召回适用且未过期的知识，并将正文及哈希绑定到同一轮生成、评审和返修。MAS 负责判断知识与当前临床问题、队列、终点和证据是否匹配；召回命中不能替代医学证据或投稿判断。直接使用 Skill 时同样先调用 OPL 召回，再读取被选中的正文。

研究套路正文见 [Publication Strategy Library](../../agent/knowledge/publication_strategy_library.md)。稳定经验与当前期刊规定分开维护；声称某杂志当前偏好前须核对作者指南或注明有时间范围的观察来源。

新经验先记录来源、失败条件、适用范围和目标层。MAS 或项目 owner 接受后才登记为 active；从单一研究推广到通用知识需要独立审阅和去除私人内容。已被取代的知识保留取代关系，退出召回。研究原始证据、质量裁定与投稿回执仍归各自已有事实源。
