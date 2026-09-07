# 文献与研究知识的归属

本文只解释知识的作用域、采用与写回；不声明私有 hydration/knowledge builder 已实现。

| 作用域 | 内容与权限 |
| --- | --- |
| MAS repo | Markdown 策略记忆与医学知识；辅助推理，不作为某篇论文证据 |
| Disease workspace | 经 MAS 接受的共享文献、来源、病种经验与复用线索 |
| Study | 当前研究选定 reference context、evidence/review ledger、claim 与失败路径 |
| StageAttempt | 显式 consumed refs、当前工作副本、closeout 与 writeback proposal |
| OPL projection | body-free locator、receipt、currentness 与执行关联，不拥有医学正文 |

Workspace 布局和 memory locator 以当前 profile、`contracts/memory_descriptor.json` 和 workspace artifact 为准。不能从 quest-local cache 反推出共享来源，也不能把空 working set 解释为所有文献缺失。

文献采用必须绑定来源身份、当前内容与所支撑 claim；provider API success、引用次数、ranking、cache hit 和记忆摘要都不是医学 acceptance。source retrieval 由 OPL Connect 托管，专业检索和审阅方法归 ScholarSkills，source/claim 判断归 MAS。

Stage 输出应标明 consumed evidence、当前研究结果、可复用 lesson proposal 与未解决引用缺口。proposal 不直接写共享真相；接受、拒绝、替换和 provenance 由 MAS memory owner 记录。详见 [策略记忆政策](../../policies/study-workflow/publication_route_memory_policy.md)。

当前接口从 `agent/` 与 contracts 发现；旧 `build_hydration_payload`、stage-entry builder、memory router 与私有 literature runtime 不再作为文档承诺的 API。
