# Med Auto Science

本仓是医学研究 domain agent；`contracts/opl_agent_package_manifest.json` 定义 `agent_id/package_id=mas`，`contracts/domain_descriptor.json` 与 `contracts/capability_map.json` 定义领域身份和能力边界。

- MAS 持有 study、publication、medical quality、artifact 和 owner receipt authority；OPL Framework 只持有通用 runtime、attempt lifecycle、transport 与 generated interfaces。
- `mas-scholar-skills` 是 MAS 的 required dependency；缺失或不可调用只阻断 MAS，不得 fail-open，也不得阻断无关 Package。
- `agent/primary_skill/SKILL.md` 是主路由，专业能力映射以 `contracts/capability_map.json` 为准；carrier mirror 不取得 MAS identity 或领域 authority。
- 当前事实以 contracts、源码、runtime artifacts 和验证输出为准；README 负责使用入口，架构解释 owner 边界，开放差距只进入 active plan。
- 默认验证运行 `scripts/verify.sh`；仅在任务需要完整重验证时使用其 full lane。

## 文档生命周期

- 每份文档只拥有一个主题；先更新该主题现有 owner，再修正引用，不新增重复状态表、验收流水或永久兼容页。目录导航与详细规则见 `docs/docs_portfolio_consolidation.md`。
- 代码、合同、调用者或验证入口变化时，同步核对描述它们的文档。当前事实、未实现目标和历史来源分别表达；完成清单不继续留在 active plan。
- 过时模块、接口、测试和文档在真实调用者切换后直接退役。独特决策理由或上游来源才保留历史档案；普通执行记录与已被接替的说明由 Git 历史保存。
- 文档语义由人工/AI 根据实现判断；机器只检查链接、资源、schema、生成完整性及真实安全边界，不固定措辞、标题、段落或清单数量。

<!-- CODEGRAPH_START -->
## CodeGraph

- 本仓库使用本地 `.codegraph/` 索引；该目录不得纳入 Git。
- 定义、调用、影响范围和代码路径等结构检索优先使用 CodeGraph；字面文本检索使用 `rg`。
- 索引缺失或过期时运行 `codegraph init .` 或 `codegraph sync .`。
<!-- CODEGRAPH_END -->
