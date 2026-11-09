# MAS 知识与记忆

MAS 遵循 [OPL 知识来源与记忆政策](https://github.com/gaofeng21cn/one-person-lab/blob/main/docs/policies/knowledge-source-and-memory-policy.md)及其[生命周期合同](https://github.com/gaofeng21cn/one-person-lab/blob/main/contracts/opl-framework/durable-knowledge-lifecycle-contract.json)。知识正文归用户、团队或对应业务主题，MAS 按研究任务使用；Framework 保存来源绑定、版本、运行快照与回执。Markdown 是可编辑正文，机器元数据不进入正文。

归属与内容性质分开：产品知识包括通用研究方法和投稿策略，正文在 `agent/knowledge/`，登记到 `contracts/durable_knowledge_catalog.json`；用户或团队知识包括协作偏好和研究政策；主题知识包括跨 Study 的病种经验；项目知识包括一个 Study 的研究设计、失败路径与决策。各范围都可以有方法、政策、时点现状和决策记录，不能根据目录或文件日期推断其有效性。

团队已经使用 Obsidian 或其他 Markdown 资料库时，个人和主题知识继续在原处维护，通过 Framework 的来源绑定直接读取已接受版本。课题设计、数据、文献与论文正文可以留在项目目录；允许混合来源。没有独立资料库时，使用工作区 `shared/memory/` 和项目 `memory/`、`state/` 等既有目录作为正文来源。一个知识对象只有一个当前主源，不要求先复制一套 Markdown 投影，也不建立 MAS 私有索引、同步服务或种子应用器。

阶段执行通过 OPL 选择权限允许、适用且未过期的知识，直接从来源冻结正文及哈希；同一轮生成、评审和返修读取同一快照。直接使用 Skill 时先 `opl knowledge prepare`，再以返回的 binding 调用 `opl knowledge read-context`，不在角色间重新读取可变原文。MAS 负责判断知识与当前临床问题、队列、终点和证据是否匹配；召回命中不能替代医学证据或投稿判断。

用户直接编辑原文后，按已有维护授权复核变更并接受新版本，不让用户手工维护哈希。来源失效、权限撤回或与已接受版本不一致时，相关条目退出当前使用；可选的病种经验缺失不阻断独立研究工作，研究设计、必要来源和关键政策缺失则阻断依赖它们的判断。派生摘要随来源版本和授权变化重审，历史快照不延续被撤回的读取或行动权限。

研究套路正文见 [Publication Strategy Library](../../agent/knowledge/publication_strategy_library.md)。稳定经验与当前期刊规定分开维护；声称某杂志当前偏好前须核对作者指南或注明有时间范围的观察来源。

新经验先记录来源、失败条件、适用范围、内容性质和唯一写回目标。项目经验、病种主题经验、团队政策和可分发的产品方法分别由对应 owner 接受；单一研究结果不会自动升级为通用规则。Framework 可执行已接受提案的版本核验与机械写入，MAS 或知识 owner 保留语义判断。并发源文变化须先协调，不能覆盖新编辑。已被取代的知识保留取代关系，退出召回。研究原始证据、质量裁定与投稿回执仍归各自已有事实源。

业务工作区里的研究数据、论文正文与已接受决策不是运行缓存。`memory/portfolio/data_assets/` 由数据资产合同定义为可重建治理投影，不能据其路径推定它是可编辑长期知识主源。Framework 状态目录保存执行快照与恢复信息；清理运行记录不得连带删除知识正文或研究成果。
