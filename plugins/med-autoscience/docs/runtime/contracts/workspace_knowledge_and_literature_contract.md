# 文献与研究知识的归属

本文解释知识与研究证据的作用域、采用与写回。通用来源解析和冻结由 Framework 持有，MAS 不维护私有 hydration/knowledge builder。

| 作用域 | 内容与权限 |
| --- | --- |
| 产品知识 | MAS repo 的通用方法与医学知识；辅助推理，不作为某篇论文证据 |
| 用户或团队知识 | 团队政策、协作偏好，使用用户已有知识库或工作目录中的唯一正文 |
| 病种主题知识 | 经接受的病种经验与复用线索，可服务多个获授权 Study，不绑定某一次运行 |
| Study 项目知识 | 当前研究设计、选定 reference context、evidence/review ledger、claim 与失败路径 |
| StageAttempt | 显式 consumed refs、当前工作副本、closeout 与 writeback proposal |
| OPL 控制与执行记录 | 来源绑定、body-free locator、冻结快照、receipt、currentness 与执行关联，不拥有医学语义 |

`contracts/durable_knowledge_catalog.json` 只登记可分发的产品知识。用户、主题和项目正文的来源、权限、已接受版本由 Profile/Workspace 的 Framework 来源登记与绑定持有；不得把私人路径放进产品包。Obsidian 与普通工作目录使用同一来源模型，不强制中间全文投影，知识身份不随路径变化。文献原件、队列数据和研究结果保留在真实证据来源；知识摘要不是它们的替代品。不能从 quest-local cache 反推出共享来源，也不能把空 working set 解释为所有文献缺失。

文献采用必须绑定来源身份、当前内容与所支撑 claim；provider API success、引用次数、ranking、cache hit 和记忆摘要都不是医学 acceptance。source retrieval 由 OPL Connect 托管，专业检索和审阅方法归 ScholarSkills，source/claim 判断归 MAS。

Stage 输出应标明 consumed evidence、知识 identity/scope/content kind/version、当前研究结果、可复用 lesson proposal 与未解决引用缺口。proposal 不直接写共享真相；接受、拒绝、替换和 provenance 由相应知识 owner 记录。来源漂移、过期、撤回和并发修改由通用机制核验；研究语义与必须证据缺口由 MAS 判断。详见 [知识政策](../../policies/domain_memory_markdown_first_policy.md)和[策略记忆政策](../../policies/study-workflow/publication_route_memory_policy.md)。

当前接口从 `agent/` 与 contracts 发现；旧 `build_hydration_payload`、stage-entry builder、memory router 与私有 literature runtime 不再作为文档承诺的 API。
