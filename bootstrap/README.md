# MAS Bootstrap

Owner: `MedAutoScience`
Purpose: `bootstrap_boundary`
State: `current_reference`
Machine boundary: 本文解释 package/environment handoff。可执行真相归 OPL installer/environment substrate、MAS contracts 与 generated interfaces。

## 结论

MAS 不再提供 repo-local workspace initializer、editable import bootstrap、Python/R environment builder、Codex plugin installer 或 runtime healthcheck。OPL Package lifecycle 从 Release Set 或显式 manifest/registry 选择 MAS，可默认随包物化 `mas-scholar-skills` 作为可选专业增强，并分别持有 package lock、receipt、scope activation、更新、修复与回滚。Provider 缺失或不兼容只形成 diagnostic / quality debt，不阻断 MAS lifecycle，也不形成原子依赖闭包或卸载保护。环境 owner 仍是 OPL Base，依赖环境、uv cache 与 bytecode 全部位于 source checkout 外。

当前 bootstrap 是两部分：

1. MAS 声明 domain pack、actions、schemas 与环境 requirements。
2. OPL 发现 package，生成 interfaces，并准备 hosted runtime/environment。

## Package discovery

OPL 读取：

- `contracts/domain_descriptor.json`
- `contracts/pack_compiler_input.json`
- `contracts/action_catalog.json`
- `contracts/generated_surface_handoff.json`
- `agent/`

canonical domain id 是 `mas`。`med-autoscience` 仅作为 repo/package/plugin locator。

用户与 operator 只使用 OPL Package lifecycle：

```bash
opl packages install mas --json
opl packages update mas --json
opl packages status --package-id mas --json
opl packages repair mas --json
```

workspace / quest 的 Skill materialization 通过 `--scope workspace|quest` 与对应 target 参数按目标 package 独立执行。只有 `required=true` 的 hard runtime dependency 进入 closure transaction；`mas-scholar-skills` 作为 optional Provider 独立物化，失败只记录 diagnostic。`status` 读取各 package 的 lock、projection、migration 与 lifecycle receipt；`repair` 只对 root package 及其 hard dependency closure 的当前字节和 scope materialization fail-closed，不得把 optional Provider 问题提升为 MAS repair failure。上述命令都不写 MAS domain truth、不生成 owner receipt，也不授权 domain 或 production ready。

## Python packaging

依赖通过标准 packaging/`uv sync` 或 OPL workspace override 安装。MAS import 不改写 `sys.path`、package `__path__` 或 `sys.modules`，也不尝试在 import 时发现 sibling checkout。

## Runtime environment

MAS 的环境声明在 `contracts/runtime_environment_requirements.json`。当前 `analysis-display` profile 包含 R 与 Bioconductor requirement；环境 owner 是 OPL Framework。

标准 handoff：

```bash
opl env prepare \
  --domain mas \
  --profile analysis-display \
  --platform <platform> \
  --requirement-profile contracts/runtime_environment_requirements.json \
  --artifact-root <artifact_root> \
  --apply \
  --json

opl env run \
  --domain mas \
  --profile analysis-display \
  --artifact-root <artifact_root> \
  -- <command>
```

Requirement profile 或 prepare success 不等于 MAS domain ready、paper progress、visual quality 或 production ready。

## Generated interfaces

CLI、MCP、Skill、product-entry、status 与 workbench 由 OPL 从 action catalog/schema 生成或托管。MAS 不提供第二套 installer、parser、JSON-RPC transport 或 hosted shell。

Direct Codex 使用 repo-tracked primary skill；plugin 分发使用受控 carrier mirror。两者 currentness 由 capability map/carrier projection contract 约束，不由 bootstrap 脚本复制。

## Workspace boundary

Study workspace lifecycle、locator、StateIndex、retention/restore 与 hosted workbench 归 OPL。MAS domain handlers 可以读取受权 refs并写 MAS-owned truth/receipt surface，但不得创建通用 workspace/platform authority。

## 验收

- OPL 能解析 descriptor、pack、7-action V2 catalog 与 schemas；
- OPL 能解析 runtime requirement profile；
- MAS import 不依赖 checkout path mutation；
- generated interfaces 不依赖 repo-local installer/workspace initializer；
- runtime/paper/readiness claim 仍由 fresh live/readback/owner evidence 证明。

## 相关入口

- [Project](../docs/project.md)
- [Architecture](../docs/architecture.md)
- [Contracts](../contracts/README.md)
- [Runtime boundary](../docs/runtime/contracts/runtime_boundary.md)
