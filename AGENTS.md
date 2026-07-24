# Med Auto Science

本仓是医学研究 domain agent；`contracts/opl_agent_package_manifest.json` 定义 `agent_id/package_id=mas`，`contracts/domain_descriptor.json` 与 `contracts/capability_map.json` 定义领域身份和能力边界。

- MAS 持有 study、publication、medical quality、artifact 和 owner receipt authority；OPL Framework 只持有通用 runtime、attempt lifecycle、transport 与 generated interfaces。
- `mas-scholar-skills` 是 MAS 的 required dependency；缺失或不可调用只阻断 MAS，不得 fail-open，也不得阻断无关 Package。
- `agent/primary_skill/SKILL.md` 是主路由，专业能力映射以 `contracts/capability_map.json` 为准；carrier mirror 不取得 MAS identity 或领域 authority。
- 当前事实以 contracts、源码、runtime artifacts 和验证输出为准；迁移目标与兼容说明留在 `README.md` 和 active plans。
- 默认验证运行 `scripts/verify.sh`；仅在任务需要完整重验证时使用其 full lane。

<!-- CODEGRAPH_START -->
## CodeGraph

- 本仓库使用本地 `.codegraph/` 索引；该目录不得纳入 Git。
- 定义、调用、影响范围和代码路径等结构检索优先使用 CodeGraph；字面文本检索使用 `rg`。
- 索引缺失或过期时运行 `codegraph init .` 或 `codegraph sync .`。
<!-- CODEGRAPH_END -->
