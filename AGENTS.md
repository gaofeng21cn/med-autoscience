# Med Auto Science

本仓是 OPL 的医学研究 domain agent，也是 `OPL Package(kind=agent)`；canonical agent/package id 为 `mas`，machine `domain_id` / `target_domain_id` 与 domain-owned Stage manifest owner 为 `medautoscience`。`med-autoscience` 只作为 repo/package/plugin/carrier locator。

- MAS 持有 study、publication、medical quality、artifact 和 owner receipt authority。
- OPL Framework 持有通用 runtime、attempt lifecycle、workspace/artifact transport 与 generated interfaces。
- Package identity、capabilities、required/optional dependency identity、business work item 与 typed view 语义必须保持 executor-neutral；当前默认 executor 是 Codex，但 Codex Plugin 只是 carrier projection，不是 MAS identity、完整 Package bytes 或 domain authority。
- `mas-scholar-skills` 是 MAS 的 required hard dependency：普通组合只检查其 identity 已存在且所需能力可调用；缺失或不可调用只阻断 MAS，不得降级为 optional，也不得阻断无关 Package。
- MAS owner 独立发布完整 Package bytes 到自身 GHCR `latest-stable`；普通 readiness 不以跨包版本范围、ABI、lock、payload、digest、原子 closure、共享 Release Set 或跨包求解为门。Exact ref/digest 仅用于单次 release artifact 与完整性证明。
- `agent/primary_skill/SKILL.md` 是 rich primary skill；plugin carrier mirror 的关系以 `contracts/capability_map.json` 为准。现有 contracts/validators 仍可能保留旧 package 字段，迁移完成前不得把人读目标边界声称为已实现。
- 当前事实以 contracts、源码、runtime artifacts 和验证输出为准。

默认验证入口：`scripts/verify.sh`。

<!-- CODEGRAPH_START -->
## CodeGraph

- 本仓库使用本地 `.codegraph/` 索引；该目录不得纳入 Git。
- 定义、调用、影响范围和代码路径等结构检索优先使用 CodeGraph；字面文本检索使用 `rg`。
- 索引缺失或过期时运行 `codegraph init .` 或 `codegraph sync .`。
<!-- CODEGRAPH_END -->
