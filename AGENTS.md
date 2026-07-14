# Med Auto Science

本仓是 OPL 的医学研究 domain agent，canonical id 为 `mas`。

- MAS 持有 study、publication、medical quality、artifact 和 owner receipt authority。
- OPL Framework 持有通用 runtime、attempt lifecycle、workspace/artifact transport 与 generated interfaces。
- `agent/primary_skill/SKILL.md` 是 rich primary skill；plugin carrier mirror 的关系以 `contracts/capability_map.json` 为准。
- 当前事实以 contracts、源码、runtime artifacts 和验证输出为准。

默认验证入口：`scripts/verify.sh`。

<!-- CODEGRAPH_START -->
## CodeGraph

- 本仓库使用本地 `.codegraph/` 索引；该目录不得纳入 Git。
- 定义、调用、影响范围和代码路径等结构检索优先使用 CodeGraph；字面文本检索使用 `rg`。
- 索引缺失或过期时运行 `codegraph init .` 或 `codegraph sync .`。
<!-- CODEGRAPH_END -->
